"""Integration tests for the /infer and /infer_proba endpoints.

Covers the mutually-exclusive data/query_idx contract:
- body path: ad-hoc data, no logging
- query_idx path: refs resolved via data service, request_prediction logged once,
  service called with refs list for per-ticket predict events
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

import pytest
from fastapi.testclient import TestClient

from app.config.config import SYSTEM_USER_ID
from app.core import dependencies
from app.core.dependencies import create_access_token
from app.core.storage import ActiveLearningStorage
from app.main import app
from app.persistence.duckdb import DuckDbPersistenceService
from app.routers import inference_router, user_router


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield DuckDbPersistenceService(db_path=Path(tmpdir) / "test.duckdb")


@pytest.fixture
def client(temp_db, monkeypatch):
    # Insert al_instance row 1 so the FK on al_events passes
    temp_db.save_al_instance(
        al_instance_id=1,
        instance_data={"model_name": "rf", "qs": "random", "classes": [0, 1]},
        user_id=SYSTEM_USER_ID,
    )

    fake_inference = MagicMock()
    fake_inference.storage = ActiveLearningStorage()
    fake_inference.storage.model_paths_dict = {1: "/some/model/path"}
    fake_inference.storage.al_instances_dict = {1: {"user_id": SYSTEM_USER_ID}}

    fake_data = MagicMock()
    fake_data.get_tickets.return_value = {
        "tickets": [
            {
                "Title_anon": "Title 1",
                "Description_anon": "Desc 1",
                "Service->Name": "Service A",
                "Service subcategory->Name": "Subcat A",
            },
            {
                "Title_anon": "Title 2",
                "Description_anon": "Desc 2",
                "Service->Name": "Service B",
                "Service subcategory->Name": "Subcat B",
            },
        ]
    }

    monkeypatch.setattr(inference_router, "inference_service", fake_inference)
    monkeypatch.setattr(inference_router, "data_service", fake_data)
    monkeypatch.setattr(inference_router, "duckdb_service", temp_db)
    monkeypatch.setattr(user_router, "duckdb_service", temp_db)
    monkeypatch.setattr(dependencies, "duckdb_persistence_service", temp_db)
    monkeypatch.setattr(dependencies, "inference_service", fake_inference)
    monkeypatch.setattr(dependencies, "data_service", fake_data)

    class MockStartupService:
        def load_data_from_minio_into_duckdb(self):
            pass

    monkeypatch.setattr(dependencies, "startup_service", MockStartupService())

    with TestClient(app) as test_client:
        yield test_client


def _sample_data():
    return {
        "title_anon": "Hello",
        "description_anon": "World",
    }


class TestInferBodyPath:
    def test_body_path_no_logging(self, client):
        fake_inf = inference_router.inference_service
        fake_inf.infer.return_value = ["Team A"]

        response = client.post("/activelearning/1/infer", json=_sample_data())

        assert response.status_code == 200
        assert response.json() == ["Team A"]
        # infer called without refs (body path = unlogged)
        call_kwargs = fake_inf.infer.call_args.kwargs
        assert "refs" not in call_kwargs
        # No request_prediction event logged on the body path
        events = _get_events(inference_router.duckdb_service, "request_prediction")
        assert events == []

    def test_body_path_batch_no_logging(self, client):
        fake_inf = inference_router.inference_service
        fake_inf.infer.return_value = ["Team A", "Team B"]

        response = client.post(
            "/activelearning/1/infer", json=[_sample_data(), _sample_data()]
        )

        assert response.status_code == 200
        assert response.json() == ["Team A", "Team B"]
        events = _get_events(inference_router.duckdb_service, "request_prediction")
        assert events == []


class TestInferQueryIdxPath:
    def test_query_idx_calls_service_with_refs(self, client):
        fake_inf = inference_router.inference_service
        fake_inf.infer.return_value = ["Team A", "Team B"]

        response = client.post(
            "/activelearning/1/infer?query_idx=R-1&query_idx=R-2"
        )

        assert response.status_code == 200
        assert response.json() == ["Team A", "Team B"]
        call_kwargs = fake_inf.infer.call_args.kwargs
        assert call_kwargs.get("refs") == ["R-1", "R-2"]

    def test_query_idx_emits_request_prediction_event(self, client):
        fake_inf = inference_router.inference_service
        fake_inf.infer.return_value = ["Team A", "Team B"]

        response = client.post(
            "/activelearning/1/infer?query_idx=R-1&query_idx=R-2"
        )

        assert response.status_code == 200
        events = _get_events(inference_router.duckdb_service, "request_prediction")
        assert len(events) == 1
        ev = events[0]
        assert ev["action"] == "request_prediction"
        assert ev["actor_type"] == "system"
        assert ev["agent"] == "orchestrator"
        assert ev["object_id"] is None
        assert ev["payload"]["request_size"] == 2
        assert ev["payload"]["ticket_ids"] == ["R-1", "R-2"]

    def test_query_idx_missing_ticket_returns_404(self, client):
        inference_router.data_service.get_tickets.return_value = None

        response = client.post("/activelearning/1/infer?query_idx=R-9")

        assert response.status_code == 404
        assert "R-9" in response.json()["detail"]

    def test_query_idx_empty_tickets_returns_404(self, client):
        inference_router.data_service.get_tickets.return_value = {"tickets": []}

        response = client.post("/activelearning/1/infer?query_idx=R-9")

        assert response.status_code == 404
        assert "R-9" in response.json()["detail"]


class TestInferMutualExclusivity:
    def test_both_data_and_query_idx_returns_400(self, client):
        response = client.post(
            "/activelearning/1/infer?query_idx=R-1", json=_sample_data()
        )

        assert response.status_code == 400
        assert "exactly one" in response.json()["detail"]
        # No inference, no logging
        inference_router.inference_service.infer.assert_not_called()
        events = _get_events(inference_router.duckdb_service, "request_prediction")
        assert events == []

    def test_neither_data_nor_query_idx_returns_400(self, client):
        response = client.post("/activelearning/1/infer")

        assert response.status_code == 400
        assert "exactly one" in response.json()["detail"]


class TestInferModelNotTrained:
    def test_model_not_trained_returns_404(self, client):
        inference_router.inference_service.storage.model_paths_dict = {}

        response = client.post(
            "/activelearning/1/infer?query_idx=R-1"
        )

        assert response.status_code == 404
        assert "Model not trained" in response.json()["detail"]
        # No request_prediction logged (training check precedes logging)
        events = _get_events(inference_router.duckdb_service, "request_prediction")
        assert events == []


class TestInferProbaBodyPath:
    def test_body_path_no_logging(self, client):
        fake_inf = inference_router.inference_service
        fake_inf.infer_proba.return_value = {
            "classes": ["Team A", "Team B"],
            "probabilities": [[0.7, 0.3]],
        }

        response = client.post("/activelearning/1/infer_proba", json=_sample_data())

        assert response.status_code == 200
        body = response.json()
        assert body["classes"] == ["Team A", "Team B"]
        call_kwargs = fake_inf.infer_proba.call_args.kwargs
        assert "refs" not in call_kwargs
        events = _get_events(inference_router.duckdb_service, "request_prediction")
        assert events == []


class TestInferProbaQueryIdxPath:
    def test_query_idx_emits_request_prediction_event(self, client):
        fake_inf = inference_router.inference_service
        fake_inf.infer_proba.return_value = {
            "classes": ["Team A", "Team B"],
            "probabilities": [[0.7, 0.3], [0.1, 0.9]],
        }

        response = client.post(
            "/activelearning/1/infer_proba?query_idx=R-1&query_idx=R-2"
        )

        assert response.status_code == 200
        call_kwargs = fake_inf.infer_proba.call_args.kwargs
        assert call_kwargs.get("refs") == ["R-1", "R-2"]
        events = _get_events(inference_router.duckdb_service, "request_prediction")
        assert len(events) == 1
        ev = events[0]
        assert ev["action"] == "request_prediction"
        assert ev["actor_type"] == "system"
        assert ev["agent"] == "orchestrator"
        assert ev["object_id"] is None
        assert ev["payload"]["request_size"] == 2
        assert ev["payload"]["ticket_ids"] == ["R-1", "R-2"]

    def test_query_idx_missing_ticket_returns_404(self, client):
        inference_router.data_service.get_tickets.return_value = None

        response = client.post("/activelearning/1/infer_proba?query_idx=R-9")

        assert response.status_code == 404
        assert "R-9" in response.json()["detail"]


class TestInferProbaMutualExclusivity:
    def test_both_data_and_query_idx_returns_400(self, client):
        response = client.post(
            "/activelearning/1/infer_proba?query_idx=R-1", json=_sample_data()
        )

        assert response.status_code == 400
        assert "exactly one" in response.json()["detail"]

    def test_neither_data_nor_query_idx_returns_400(self, client):
        response = client.post("/activelearning/1/infer_proba")

        assert response.status_code == 400
        assert "exactly one" in response.json()["detail"]


class TestInferProbaValueError:
    def test_value_error_returns_400(self, client):
        fake_inf = inference_router.inference_service
        fake_inf.infer_proba.side_effect = ValueError("Model does not support predict_proba")

        response = client.post("/activelearning/1/infer_proba", json=_sample_data())

        assert response.status_code == 400
        assert "predict_proba" in response.json()["detail"]


def _get_events(duckdb_svc, action):
    """Helper: fetch all al_events rows with a given action from the real DuckDB svc."""
    rows = duckdb_svc.get_al_events(al_instance_id=1, actions=[action], limit=100)
    return rows


@pytest.fixture
def client_non_system_owner(temp_db, monkeypatch):
    """Fixture: instance 1 owned by a real registered user 'alice' (not SYSTEM_USER_ID).

    Yields (test_client, alice_id_str) so tests can mint alice's JWT.
    With no token, get_current_user returns SYSTEM_USER_ID, which is neither alice
    nor a delegate -> 403 on the query_idx path; data path skips the access check.
    """
    alice_id = temp_db.upsert_user(username="alice", password="pwd")
    alice_id_str = str(alice_id)
    temp_db.save_al_instance(
        al_instance_id=1,
        instance_data={"model_name": "rf", "qs": "random", "classes": [0, 1]},
        user_id=alice_id_str,
    )

    fake_inference = MagicMock()
    fake_inference.storage = ActiveLearningStorage()
    fake_inference.storage.model_paths_dict = {1: "/some/model/path"}
    fake_inference.storage.al_instances_dict = {1: {"user_id": alice_id_str}}

    fake_data = MagicMock()
    fake_data.get_tickets.return_value = {
        "tickets": [
            {
                "Title_anon": "Title 1",
                "Description_anon": "Desc 1",
                "Service->Name": "Service A",
                "Service subcategory->Name": "Subcat A",
            },
            {
                "Title_anon": "Title 2",
                "Description_anon": "Desc 2",
                "Service->Name": "Service B",
                "Service subcategory->Name": "Subcat B",
            },
        ]
    }

    monkeypatch.setattr(inference_router, "inference_service", fake_inference)
    monkeypatch.setattr(inference_router, "data_service", fake_data)
    monkeypatch.setattr(inference_router, "duckdb_service", temp_db)
    monkeypatch.setattr(user_router, "duckdb_service", temp_db)
    monkeypatch.setattr(dependencies, "duckdb_persistence_service", temp_db)
    monkeypatch.setattr(dependencies, "inference_service", fake_inference)
    monkeypatch.setattr(dependencies, "data_service", fake_data)

    class MockStartupService:
        def load_data_from_minio_into_duckdb(self):
            pass

    monkeypatch.setattr(dependencies, "startup_service", MockStartupService())

    with TestClient(app) as test_client:
        yield test_client, alice_id_str


class TestInferConditionalAuth:
    def test_data_path_succeeds_without_token_when_not_owner(self, client_non_system_owner):
        # data body path skips the ownership gate; no token, instance not owned by system user
        client, _ = client_non_system_owner
        fake_inf = inference_router.inference_service
        fake_inf.infer.return_value = ["Team A"]

        response = client.post("/activelearning/1/infer", json=_sample_data())

        assert response.status_code == 200
        assert response.json() == ["Team A"]

    def test_query_idx_returns_403_without_token_when_not_owner(self, client_non_system_owner):
        # query_idx path still enforces ownership; system user is not owner/delegate
        client, _ = client_non_system_owner

        response = client.post("/activelearning/1/infer?query_idx=R-1&query_idx=R-2")

        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
        # access check runs BEFORE request_prediction logging -> no event written
        events = _get_events(inference_router.duckdb_service, "request_prediction")
        assert events == []

    def test_query_idx_with_owner_token_succeeds_and_logs_as_user(self, client_non_system_owner):
        # authenticated owner: 200, and request_prediction attributed to alice's user_id
        client, alice_id_str = client_non_system_owner
        fake_inf = inference_router.inference_service
        fake_inf.infer.return_value = ["Team A", "Team B"]
        token = create_access_token(user_id=alice_id_str, username="alice")

        response = client.post(
            "/activelearning/1/infer?query_idx=R-1&query_idx=R-2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json() == ["Team A", "Team B"]
        events = _get_events(inference_router.duckdb_service, "request_prediction")
        assert len(events) == 1
        assert events[0]["user_id"] == alice_id_str


class TestInferProbaConditionalAuth:
    def test_data_path_succeeds_without_token_when_not_owner(self, client_non_system_owner):
        client, _ = client_non_system_owner
        fake_inf = inference_router.inference_service
        fake_inf.infer_proba.return_value = {
            "classes": ["Team A", "Team B"],
            "probabilities": [[0.7, 0.3]],
        }

        response = client.post("/activelearning/1/infer_proba", json=_sample_data())

        assert response.status_code == 200
        assert response.json()["classes"] == ["Team A", "Team B"]

    def test_query_idx_returns_403_without_token_when_not_owner(self, client_non_system_owner):
        client, _ = client_non_system_owner

        response = client.post("/activelearning/1/infer_proba?query_idx=R-1&query_idx=R-2")

        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
        events = _get_events(inference_router.duckdb_service, "request_prediction")
        assert events == []

    def test_query_idx_with_owner_token_succeeds_and_logs_as_user(self, client_non_system_owner):
        client, alice_id_str = client_non_system_owner
        fake_inf = inference_router.inference_service
        fake_inf.infer_proba.return_value = {
            "classes": ["Team A", "Team B"],
            "probabilities": [[0.7, 0.3], [0.1, 0.9]],
        }
        token = create_access_token(user_id=alice_id_str, username="alice")

        response = client.post(
            "/activelearning/1/infer_proba?query_idx=R-1&query_idx=R-2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        events = _get_events(inference_router.duckdb_service, "request_prediction")
        assert len(events) == 1
        assert events[0]["user_id"] == alice_id_str
