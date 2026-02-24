"""Tests for data preprocessing service functions."""
from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from app.config.config import TEST_SPLIT, TRAIN_SPLIT
from app.services import data_preprocessing as dp


class DummySparseMatrix:
    def __init__(self, array: np.ndarray):
        self._array = array

    def toarray(self) -> np.ndarray:
        return self._array


class FakeLabelEncoder:
    def __init__(self):
        self.fitted_classes = None

    def fit(self, classes):
        self.fitted_classes = list(classes)
        return self

    def transform(self, values):
        mapping = {"Team A": 0, "Team B": 1}
        return np.array([mapping.get(v, -1) for v in values])


class FakeOneHotEncoder:
    def __init__(self, handle_unknown=None):
        self.handle_unknown = handle_unknown

    def fit_transform(self, values):
        rows = len(values)
        arr = np.zeros((rows, 2))
        if rows > 0:
            arr[:, 0] = 1
        return DummySparseMatrix(arr)

    def transform(self, values):
        rows = len(values)
        arr = np.zeros((rows, 2))
        if rows > 0:
            arr[:, 1] = 1
        return DummySparseMatrix(arr)


@pytest.fixture
def mock_duckdb_service() -> MagicMock:
    return MagicMock()


def test_dispatch_team_train_set_preprocesses_and_encodes(monkeypatch, mock_duckdb_service: MagicMock):
    monkeypatch.setattr(dp, "LabelEncoder", FakeLabelEncoder)
    monkeypatch.setattr(dp, "OneHotEncoder", FakeOneHotEncoder)

    mock_sentence_model = MagicMock()
    mock_sentence_model.encode.return_value = [[0.1, 0.2]]
    mock_sentence_transformer_class = MagicMock(return_value=mock_sentence_model)
    monkeypatch.setattr(dp, "SentenceTransformer", mock_sentence_transformer_class)

    mock_duckdb_service.load_tickets.return_value = pd.DataFrame(
        {
            "Ref": ["R1", "R2", "R3"],
            "Last team ID->Name": [None, "Changed", None],
            "Title_anon": ["Title 1", "Title 2", None],
            "Description_anon": [" Desc 1", " Desc 2", " Desc 3"],
            "Service subcategory->Name": ["Sub A", "Sub B", "Sub C"],
            "Service->Name": ["Srv A", "Srv B", "Srv C"],
            "Team->Name": ["Team A", "Team B", "Team A"],
        }
    )

    X, y_true, le, oh = dp.dispatch_team(
        duckdb_service=mock_duckdb_service,
        test_set=False,
        classes=["Team A", "Team B"],
    )

    mock_duckdb_service.load_tickets.assert_called_once_with(split=TRAIN_SPLIT)
    assert list(X.index) == ["R1"]
    assert list(y_true.index) == ["R1"]
    assert y_true.iloc[0] == 0
    assert all(isinstance(col, str) for col in X.columns)
    assert isinstance(le, FakeLabelEncoder)
    assert isinstance(oh, FakeOneHotEncoder)


def test_dispatch_team_test_set_uses_transform_and_keeps_string_labels(monkeypatch, mock_duckdb_service: MagicMock):
    mock_sentence_model = MagicMock()
    mock_sentence_model.encode.return_value = [[0.3, 0.4]]
    mock_sentence_transformer_class = MagicMock(return_value=mock_sentence_model)
    monkeypatch.setattr(dp, "SentenceTransformer", mock_sentence_transformer_class)

    provided_le = MagicMock()
    provided_oh = MagicMock()
    provided_oh.transform.return_value = DummySparseMatrix(np.array([[0.0, 1.0]]))

    mock_duckdb_service.load_tickets.return_value = pd.DataFrame(
        {
            "Ref": ["T1", "T2"],
            "Last team ID->Name": [None, None],
            "Title_anon": ["Hello", "Missing Team"],
            "Description_anon": [" World", " Value"],
            "Service subcategory->Name": ["Sub A", "Sub B"],
            "Service->Name": ["Srv A", "Srv B"],
            "Team->Name": ["Team B", None],
        }
    )

    X, y_true, le, oh = dp.dispatch_team(
        duckdb_service=mock_duckdb_service,
        test_set=True,
        le=provided_le,
        oh=provided_oh,
    )

    mock_duckdb_service.load_tickets.assert_called_once_with(split=TEST_SPLIT)
    provided_oh.transform.assert_called_once()
    assert list(X.index) == ["T1"]
    assert y_true.tolist() == ["Team B"]
    assert le is provided_le
    assert oh is provided_oh


def test_dispatch_team_raises_when_no_data(mock_duckdb_service: MagicMock):
    mock_duckdb_service.load_tickets.return_value = pd.DataFrame()

    with pytest.raises(ValueError, match="No data found for the specified split"):
        dp.dispatch_team(duckdb_service=mock_duckdb_service)


def test_inference_builds_combined_features():
    input_df = pd.DataFrame(
        {
            "title_anon": ["Issue", "Request"],
            "description_anon": [" details", " info"],
            "service_subcategory_name": ["Sub A", "Sub B"],
            "service_name": ["Srv A", "Srv B"],
        }
    )

    mock_sentence_model = MagicMock()
    mock_sentence_model.encode.return_value = [[1.0, 2.0], [3.0, 4.0]]

    mock_oh = MagicMock()
    mock_oh.transform.return_value = DummySparseMatrix(np.array([[1.0, 0.0], [0.0, 1.0]]))

    X = dp.inference(
        df=input_df,
        le=MagicMock(),
        oh=mock_oh,
        sentence_model=mock_sentence_model,
    )

    assert X.shape == (2, 4)
    assert all(isinstance(col, str) for col in X.columns)

    transformed_df = mock_oh.transform.call_args.args[0]
    assert list(transformed_df.columns) == ["Service subcategory->Name", "Service->Name"]
