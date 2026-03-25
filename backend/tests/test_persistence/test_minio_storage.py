"""Tests for MinioService object-key namespacing via MINIO_PREFIX."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.core.minio_client import MinioClient
from app.persistence.minio_storage import DATA_BUCKET, MODELS_BUCKET, MinioService


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock(spec=MinioClient)


def test_save_model_uses_minio_prefix(monkeypatch: pytest.MonkeyPatch, mock_client: MagicMock):
    monkeypatch.setenv("MINIO_PREFIX", "test")

    svc = MinioService(mock_client)
    svc.save_model(al_instance_id=7, model_version=3, model={"ok": True})

    mock_client.upload_file_bytes.assert_called_once()
    bucket_name, object_name, model_bytes = mock_client.upload_file_bytes.call_args.args

    assert bucket_name == MODELS_BUCKET
    assert object_name == "test/models/7/3.joblib"
    assert isinstance(model_bytes, bytes)


def test_load_data_uses_prefixed_dataset_path(monkeypatch: pytest.MonkeyPatch, mock_client: MagicMock):
    monkeypatch.setenv("MINIO_PREFIX", "qa")

    object_name = "qa/datasets/train/User Request_last_team_ANON_20260124T123000.xlsx"
    mock_client.list_objects.return_value = {"matches": [object_name]}
    mock_client.download_object.return_value = b"xlsx-bytes"

    expected_df = pd.DataFrame({"Ref": ["R-1"]})
    with patch("app.persistence.minio_storage.pd.read_excel", return_value=expected_df):
        svc = MinioService(mock_client)
        result = svc.load_data(split="train")

    mock_client.list_objects.assert_called_once_with(
        DATA_BUCKET,
        prefix="qa/datasets/train/",
        filter_type="exact",
    )
    mock_client.download_object.assert_called_once_with(DATA_BUCKET, object_name)

    assert result is not None
    assert list(result.keys()) == [datetime(2026, 1, 24, 12, 30, 0)]
    assert result[datetime(2026, 1, 24, 12, 30, 0)].equals(expected_df)


def test_delete_instance_objects_uses_prefixed_paths_and_buckets(
    monkeypatch: pytest.MonkeyPatch,
    mock_client: MagicMock,
):
    monkeypatch.setenv("MINIO_PREFIX", "sandbox")

    mock_client.list_objects.side_effect = [
        {"matches": ["sandbox/models/11/1.joblib"]},
        {"matches": ["sandbox/encoders/11/label_encoder.joblib"]},
        {"matches": ["sandbox/vectorized_tickets/11/1_train.joblib"]},
        {"matches": ["sandbox/labels/11/1_train.joblib"]},
    ]

    svc = MinioService(mock_client)
    svc.delete_instance_objects(11)

    assert mock_client.list_objects.call_args_list == [
        ((MODELS_BUCKET,), {"prefix": "sandbox/models/11/", "filter_type": "exact"}),
        ((MODELS_BUCKET,), {"prefix": "sandbox/encoders/11/", "filter_type": "exact"}),
        ((DATA_BUCKET,), {"prefix": "sandbox/vectorized_tickets/11/", "filter_type": "exact"}),
        ((DATA_BUCKET,), {"prefix": "sandbox/labels/11/", "filter_type": "exact"}),
    ]

    assert mock_client.delete_object.call_args_list == [
        ((MODELS_BUCKET, "sandbox/models/11/1.joblib"), {}),
        ((MODELS_BUCKET, "sandbox/encoders/11/label_encoder.joblib"), {}),
        ((DATA_BUCKET, "sandbox/vectorized_tickets/11/1_train.joblib"), {}),
        ((DATA_BUCKET, "sandbox/labels/11/1_train.joblib"), {}),
    ]


def test_lowercase_minio_prefix_env_is_supported(
    monkeypatch: pytest.MonkeyPatch,
    mock_client: MagicMock,
):
    monkeypatch.delenv("MINIO_PREFIX", raising=False)
    monkeypatch.setenv("minio_prefix", "dev")

    svc = MinioService(mock_client)
    svc.save_label_encoder(al_instance_id=5, encoder={"enc": True})

    mock_client.upload_file_bytes.assert_called_once()
    bucket_name, object_name, _ = mock_client.upload_file_bytes.call_args.args

    assert bucket_name == MODELS_BUCKET
    assert object_name == "dev/encoders/5/label_encoder.joblib"
