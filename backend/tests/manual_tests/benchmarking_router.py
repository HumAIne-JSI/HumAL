from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sklearn.preprocessing import LabelEncoder
from pydantic import ValidationError

from app.core.storage import ActiveLearningStorage
from app.data_models.active_learning_dm import LabelInfo, LabelRequest
from app.routers import active_learning_router
from app.services.active_learning_svc import ActiveLearningService


def _build_service():
    storage = ActiveLearningStorage()
    storage.al_instances_dict[7] = {
        "model_name": "svm",
        "qs": "random sampling",
        "classes": [0, 1],
    }

    label_encoder = LabelEncoder().fit(["Hardware", "Network"])
    storage.dataset_dict[7] = {
        "y_train": pd.Series([np.nan, np.nan], index=["T-1", "T-2"]),
        "le": label_encoder,
        "oh": MagicMock(),
        "X_train": pd.DataFrame(index=["T-1", "T-2"]),
        "X_test": pd.DataFrame(index=["T-3"]),
    }

    duckdb_service = MagicMock()
    minio_service = MagicMock()
    benchmarking_service = MagicMock()
    service = ActiveLearningService(
        storage,
        duckdb_service=duckdb_service,
        minio_service=minio_service,
        benchmarking_service=benchmarking_service,
    )
    return service, storage, duckdb_service, minio_service, benchmarking_service


def _build_app(service):
    active_learning_router.al_service = service
    app = FastAPI()
    app.include_router(active_learning_router.router)
    return app


def test_label_with_info_endpoint_accepts_list_and_triggers_export():
    service, storage, duckdb_service, minio_service, benchmarking_service = _build_service()
    app = _build_app(service)
    client = TestClient(app)

    response = client.post(
        "/activelearning/7/label-with-info",
        json=[
            {
                "ticket_id": "T-1",
                "label": "Network",
                "model_prediction": None,
                "start_time": "2026-05-20T10:00:00Z",
                "end_time": "2026-05-20T10:00:02Z",
                "explanation": "Matched the ticket description",
                "most_helpful_feature": "title",
            },
            {
                "ticket_id": "T-2",
                "label": "Hardware",
                "model_prediction": "Network",
                "start_time": "2026-05-20T10:01:00Z",
                "end_time": "2026-05-20T10:01:03Z",
                "explanation": None,
                "most_helpful_feature": None,
            },
        ],
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Labels updated"}
    duckdb_service.save_labels.assert_called_once()
    assert duckdb_service.save_labels.call_args.kwargs["labels_dict"] == {"T-1": "Network", "T-2": "Hardware"}
    assert [call.kwargs["action"] for call in duckdb_service.log_event.call_args_list] == ["confirm_label", "override_label"]
    benchmarking_service.export_if_needed.assert_called_once_with(7)
    minio_service.save_labels.assert_called_once()
    assert storage.dataset_dict[7]["y_train"].loc["T-1"] == 1
    assert storage.dataset_dict[7]["y_train"].loc["T-2"] == 0


def test_label_with_info_endpoint_rejects_invalid_payload(monkeypatch: pytest.MonkeyPatch):
    service, _, _, _, _ = _build_service()
    monkeypatch.setattr(active_learning_router, "al_service", service)

    with pytest.raises(HTTPException) as exc_info:
        active_learning_router.label_with_info(
            7,
            [
                {
                    "ticket_id": "",
                    "label": "Network",
                    "model_prediction": "Network",
                    "start_time": "2026-05-20T10:00:00Z",
                    "end_time": "2026-05-20T10:00:01Z",
                }
            ],
        )

    assert exc_info.value.status_code == 400


def test_label_with_info_endpoint_rejects_reversed_times(monkeypatch: pytest.MonkeyPatch):
    service, _, _, _, _ = _build_service()
    monkeypatch.setattr(active_learning_router, "al_service", service)

    with pytest.raises(HTTPException) as exc_info:
        active_learning_router.label_with_info(
            7,
            [
                {
                    "ticket_id": "T-1",
                    "label": "Network",
                    "model_prediction": "Network",
                    "start_time": "2026-05-20T10:00:02Z",
                    "end_time": "2026-05-20T10:00:00Z",
                }
            ],
        )

    assert exc_info.value.status_code == 400


def test_label_info_validator_rejects_empty_ticket_id():
    with pytest.raises(ValidationError):
        LabelInfo(
            ticket_id="   ",
            label="Network",
            model_prediction="Network",
            start_time=datetime(2026, 5, 20, 10, 0, 0),
            end_time=datetime(2026, 5, 20, 10, 0, 1),
        )


def test_label_route_keeps_existing_payload_shape(monkeypatch: pytest.MonkeyPatch):
    service, _, duckdb_service, _, _ = _build_service()
    monkeypatch.setattr(active_learning_router, "al_service", service)
    service.update_model = MagicMock()
    service.calculate_metrics = MagicMock()

    app = _build_app(service)
    client = TestClient(app)

    response = client.put(
        "/activelearning/7/label",
        json={"query_idx": ["T-1"], "labels": ["Network"]},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Labels updated"}
    duckdb_service.save_labels.assert_called_once()
    service.update_model.assert_called_once_with(7)
    service.calculate_metrics.assert_called_once_with(7)


def test_new_instance_endpoint_returns_400_for_insufficient_labels(monkeypatch: pytest.MonkeyPatch):
    service = MagicMock(spec=ActiveLearningService)
    service.create_instance.side_effect = ValueError(
        "Initial dataset must contain at least 50 labeled instances to create an AL instance."
    )
    monkeypatch.setattr(active_learning_router, "al_service", service)

    app = _build_app(service)
    client = TestClient(app)

    response = client.post(
        "/activelearning/new",
        json={
            "model_name": "svm",
            "qs_strategy": "random sampling",
            "class_list": ["Team A", "Team B"],
            "train_data_path": "train.csv",
            "test_data_path": "test.csv",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Initial dataset must contain at least 50 labeled instances to create an AL instance."
    }