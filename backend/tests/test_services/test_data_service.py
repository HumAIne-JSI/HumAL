"""Tests for DataService."""
from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from app.config.config import TEAM_NAME, TRAIN_SPLIT
from app.persistence.duckdb.service import DuckDbPersistenceService
from app.services.data_service import DataService


@pytest.fixture
def mock_duckdb_service() -> MagicMock:
    return MagicMock(spec=DuckDbPersistenceService)


@pytest.fixture
def data_service(mock_duckdb_service: MagicMock) -> DataService:
    return DataService(duckdb_service=mock_duckdb_service)


def test_get_tickets_returns_empty_when_no_data(
    data_service: DataService,
    mock_duckdb_service: MagicMock,
):
    mock_duckdb_service.load_tickets_by_ref.return_value = pd.DataFrame()

    result = data_service.get_tickets(indices=["T1", "T2"])

    assert result == {"tickets": []}
    mock_duckdb_service.load_tickets_by_ref.assert_called_once_with(ref_list=["T1", "T2"])


def test_get_tickets_replaces_nan_and_excludes_internal_columns(
    data_service: DataService,
    mock_duckdb_service: MagicMock,
):
    mock_duckdb_service.load_tickets_by_ref.return_value = pd.DataFrame(
        {
            "Ref": ["T1"],
            "Summary": [np.nan],
            "split": ["train"],
            "dataset_timestamp": ["2026-01-01T00:00:00"],
        }
    )

    result = data_service.get_tickets(indices=["T1"])

    assert result == {"tickets": [{"Ref": "T1", "Summary": None}]}


def test_get_teams_returns_empty_when_no_data(
    data_service: DataService,
    mock_duckdb_service: MagicMock,
):
    mock_duckdb_service.load_tickets.return_value = None

    result = data_service.get_teams()

    assert result == {"teams": []}
    mock_duckdb_service.load_tickets.assert_called_once_with(split=TRAIN_SPLIT)


def test_get_teams_returns_unique_non_null_values(
    data_service: DataService,
    mock_duckdb_service: MagicMock,
):
    mock_duckdb_service.load_tickets.return_value = pd.DataFrame(
        {
            TEAM_NAME: ["Team A", "Team B", None, "Team A"],
        }
    )

    result = data_service.get_teams()

    assert result == {"teams": ["Team A", "Team B"]}


def test_get_categories_returns_empty_when_no_data(
    data_service: DataService,
    mock_duckdb_service: MagicMock,
):
    mock_duckdb_service.load_tickets.return_value = pd.DataFrame()

    result = data_service.get_categories()

    assert result == {"categories": []}
    mock_duckdb_service.load_tickets.assert_called_once_with(split=TRAIN_SPLIT)


def test_get_categories_returns_unique_non_null_values(
    data_service: DataService,
    mock_duckdb_service: MagicMock,
):
    mock_duckdb_service.load_tickets.return_value = pd.DataFrame(
        {
            "Service->Name": ["Hardware", "Software", None, "Hardware"],
        }
    )

    result = data_service.get_categories()

    assert result == {"categories": ["Hardware", "Software"]}


def test_get_subcategories_returns_empty_when_no_data(
    data_service: DataService,
    mock_duckdb_service: MagicMock,
):
    mock_duckdb_service.load_tickets.return_value = pd.DataFrame()

    result = data_service.get_subcategories()

    assert result == {"subcategories": []}
    mock_duckdb_service.load_tickets.assert_called_once_with(split=TRAIN_SPLIT)


def test_get_subcategories_returns_unique_non_null_values(
    data_service: DataService,
    mock_duckdb_service: MagicMock,
):
    mock_duckdb_service.load_tickets.return_value = pd.DataFrame(
        {
            "Service subcategory->Name": ["Laptop", "Monitor", None, "Laptop"],
        }
    )

    result = data_service.get_subcategories()

    assert result == {"subcategories": ["Laptop", "Monitor"]}
