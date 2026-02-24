"""Tests for StartupService data loading from MinIO into DuckDB."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, call

import pandas as pd
import pytest

from app.config.config import (
    GROUND_TRUTH_AL_INSTANCE_ID,
    SYSTEM_USER_ID,
    TEAM_NAME,
    TEST_SPLIT,
    TRAIN_SPLIT,
)
from app.persistence.duckdb.service import DuckDbPersistenceService
from app.persistence.minio_storage import MinioService
from app.services.startup_svc import StartupService


TS1 = datetime(2026, 1, 24, 12, 30, 0)
TS2 = datetime(2026, 1, 26, 12, 30, 0)


def _train_df(rows: list[tuple[str, str | None]]) -> pd.DataFrame:
    return pd.DataFrame({"Ref": [r[0] for r in rows], TEAM_NAME: [r[1] for r in rows]})


def _test_df(rows: list[tuple[str, str | None]]) -> pd.DataFrame:
    return pd.DataFrame({"Ref": [r[0] for r in rows], TEAM_NAME: [r[1] for r in rows]})


@pytest.fixture
def mock_duckdb_service() -> MagicMock:
    return MagicMock(spec=DuckDbPersistenceService)


@pytest.fixture
def mock_minio_service() -> MagicMock:
    return MagicMock(spec=MinioService)


@pytest.fixture
def startup_service(mock_duckdb_service: MagicMock, mock_minio_service: MagicMock) -> StartupService:
    return StartupService(duckdb_service=mock_duckdb_service, minio_service=mock_minio_service)


def test_empty_duckdb_loads_both_datasets_for_train_and_test(
    startup_service: StartupService,
    mock_duckdb_service: MagicMock,
    mock_minio_service: MagicMock,
):
    train_ts1_df = _train_df([("T001", "TeamA"), ("T002", None)])
    train_ts2_df = _train_df([("T003", "TeamB")])
    test_ts1_df = _test_df([("S001", "TeamA"), ("S002", None)])
    test_ts2_df = _test_df([("S003", "TeamC")])

    mock_duckdb_service.get_latest_dataset_timestamp.side_effect = [None, None]
    mock_minio_service.load_data.side_effect = [
        {TS1: train_ts1_df, TS2: train_ts2_df},
        {TS1: test_ts1_df, TS2: test_ts2_df},
    ]

    startup_service.load_data_from_minio_into_duckdb()

    assert mock_minio_service.load_data.call_args_list == [
        call(split=TRAIN_SPLIT),
        call(split=TEST_SPLIT),
    ]

    # 2 train + 2 test upserts
    assert mock_duckdb_service.upsert_tickets_df.call_count == 4


def test_existing_first_dataset_loads_only_second(
    startup_service: StartupService,
    mock_duckdb_service: MagicMock,
    mock_minio_service: MagicMock,
):
    train_ts2_df = _train_df([("T100", "TeamX")])
    test_ts2_df = _test_df([("S100", "TeamY")])

    mock_duckdb_service.get_latest_dataset_timestamp.side_effect = [TS1, TS1]
    mock_minio_service.load_data.side_effect = [
        {TS2: train_ts2_df},
        {TS2: test_ts2_df},
    ]

    startup_service.load_data_from_minio_into_duckdb()

    assert mock_minio_service.load_data.call_args_list == [
        call(split=TRAIN_SPLIT, latest_dataset_timestamp=TS1),
        call(split=TEST_SPLIT, latest_dataset_timestamp=TS1),
    ]

    assert mock_duckdb_service.upsert_tickets_df.call_count == 2
    upsert_calls = mock_duckdb_service.upsert_tickets_df.call_args_list
    assert upsert_calls[0].kwargs["dataset_timestamp"] == TS2
    assert upsert_calls[1].kwargs["dataset_timestamp"] == TS2


def test_existing_latest_dataset_loads_none(
    startup_service: StartupService,
    mock_duckdb_service: MagicMock,
    mock_minio_service: MagicMock,
):
    mock_duckdb_service.get_latest_dataset_timestamp.side_effect = [TS2, TS2]
    mock_minio_service.load_data.side_effect = [None, None]

    startup_service.load_data_from_minio_into_duckdb()

    mock_duckdb_service.upsert_tickets_df.assert_not_called()
    mock_duckdb_service.save_labels.assert_not_called()


def test_groundtruth_labels_loaded_for_train_split(
    startup_service: StartupService,
    mock_duckdb_service: MagicMock,
    mock_minio_service: MagicMock,
):
    # Train has one labeled and one unlabeled row -> only labeled should be saved
    train_df = _train_df([("T201", "TeamA"), ("T202", None)])

    mock_duckdb_service.get_latest_dataset_timestamp.side_effect = [None, TS2]
    mock_minio_service.load_data.side_effect = [
        {TS1: train_df},
        None,
    ]

    startup_service.load_data_from_minio_into_duckdb()

    label_calls = [c for c in mock_duckdb_service.save_labels.call_args_list if c.kwargs["split"] == TRAIN_SPLIT]
    assert len(label_calls) == 1

    labels_dict = label_calls[0].kwargs["labels_dict"]
    assert labels_dict == {"T201": "TeamA"}
    assert label_calls[0].kwargs["al_instance_id"] == GROUND_TRUTH_AL_INSTANCE_ID
    assert label_calls[0].kwargs["user_id"] == SYSTEM_USER_ID


def test_labels_loaded_for_test_split(
    startup_service: StartupService,
    mock_duckdb_service: MagicMock,
    mock_minio_service: MagicMock,
):
    # Test labels are required; unlabeled test rows should be filtered out before save_labels
    test_df = _test_df([("S301", "TeamB"), ("S302", None), ("S303", "TeamC")])

    mock_duckdb_service.get_latest_dataset_timestamp.side_effect = [TS2, None]
    mock_minio_service.load_data.side_effect = [
        None,
        {TS1: test_df},
    ]

    startup_service.load_data_from_minio_into_duckdb()

    label_calls = [c for c in mock_duckdb_service.save_labels.call_args_list if c.kwargs["split"] == TEST_SPLIT]
    assert len(label_calls) == 1

    labels_dict = label_calls[0].kwargs["labels_dict"]
    assert labels_dict == {"S301": "TeamB", "S303": "TeamC"}
    assert label_calls[0].kwargs["al_instance_id"] == GROUND_TRUTH_AL_INSTANCE_ID
    assert label_calls[0].kwargs["user_id"] == SYSTEM_USER_ID


def test_test_split_upsert_filters_out_unlabeled_rows(
    startup_service: StartupService,
    mock_duckdb_service: MagicMock,
    mock_minio_service: MagicMock,
):
    # Optional beneficial test: verify unlabeled test tickets are not upserted
    mixed_test_df = _test_df([("S401", None), ("S402", "TeamX")])

    mock_duckdb_service.get_latest_dataset_timestamp.side_effect = [TS2, None]
    mock_minio_service.load_data.side_effect = [
        None,
        {TS1: mixed_test_df},
    ]

    startup_service.load_data_from_minio_into_duckdb()

    test_upsert_calls = [
        c for c in mock_duckdb_service.upsert_tickets_df.call_args_list if c.kwargs["split"] == TEST_SPLIT
    ]
    assert len(test_upsert_calls) == 1
    upsert_df = test_upsert_calls[0].kwargs["tickets_df"]
    assert upsert_df["Ref"].tolist() == ["S402"]
