"""Integration tests for delegation endpoints."""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

import pytest
from fastapi.testclient import TestClient

from app.core import dependencies
from app.core.storage import ActiveLearningStorage
from app.main import app
from app.persistence.duckdb import DuckDbPersistenceService
from app.routers import active_learning_router, user_router


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield DuckDbPersistenceService(db_path=Path(tmpdir) / "test.duckdb")


@pytest.fixture
def client(temp_db, monkeypatch):
    monkeypatch.setattr(active_learning_router, "al_service", MagicMock())
    monkeypatch.setattr(user_router, "duckdb_service", temp_db)
    monkeypatch.setattr(dependencies, "duckdb_persistence_service", temp_db)

    class MockStartupService:
        def load_data_from_minio_into_duckdb(self):
            pass

    monkeypatch.setattr(dependencies, "startup_service", MockStartupService())

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client, temp_db):
    client.post("/users/register", json={"username": "alice", "password": "pwd"})
    client.post("/users/register", json={"username": "bob", "password": "pwd"})

    alice_login = client.post("/users/login", json={"username": "alice", "password": "pwd"}).json()
    bob_login = client.post("/users/login", json={"username": "bob", "password": "pwd"}).json()

    return {
        "alice": {"Authorization": f"Bearer {alice_login['access_token']}"},
        "bob": {"Authorization": f"Bearer {bob_login['access_token']}"},
    }


class TestDelegateEndpoint:
    def test_delegate_success(self, client, auth_headers):
        alice_user_id = str(client.get("/users/me", headers=auth_headers["alice"]).json()["user_id"])
        active_learning_router.al_service.storage.al_instances_dict[1] = {
            "user_id": alice_user_id,
            "model_name": "rf",
            "qs": "random",
            "classes": [0, 1],
        }
        active_learning_router.al_service.delegate_instance.return_value = {
            "username": "bob",
            "delegate_user_id": "bob-uuid",
            "granted_by": alice_user_id,
            "granted_at": "2026-06-15T10:00:00",
        }

        response = client.post(
            "/activelearning/1/delegate",
            json={"username": "bob"},
            headers=auth_headers["alice"],
        )
        assert response.status_code == 200
        assert response.json()["username"] == "bob"

    def test_delegate_rejects_non_owner(self, client, auth_headers):
        active_learning_router.al_service.storage.al_instances_dict[1] = {
            "user_id": "alice-uuid",
            "model_name": "rf",
            "qs": "random",
            "classes": [0, 1],
        }
        active_learning_router.al_service.delegate_instance.side_effect = ValueError(
            "Only the instance owner can delegate access"
        )

        response = client.post(
            "/activelearning/1/delegate",
            json={"username": "bob"},
            headers=auth_headers["bob"],
        )
        assert response.status_code == 400
        assert "Only the instance owner" in response.json()["detail"]

    def test_delegate_rejects_nonexistent_user(self, client, auth_headers):
        alice_user_id = str(client.get("/users/me", headers=auth_headers["alice"]).json()["user_id"])
        active_learning_router.al_service.storage.al_instances_dict[1] = {
            "user_id": alice_user_id,
            "model_name": "rf",
            "qs": "random",
            "classes": [0, 1],
        }
        active_learning_router.al_service.delegate_instance.side_effect = ValueError(
            "User 'nonexistent' not found"
        )

        response = client.post(
            "/activelearning/1/delegate",
            json={"username": "nonexistent"},
            headers=auth_headers["alice"],
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]


class TestRevokeEndpoint:
    def test_revoke_success(self, client, auth_headers):
        alice_user_id = str(client.get("/users/me", headers=auth_headers["alice"]).json()["user_id"])
        active_learning_router.al_service.storage.al_instances_dict[1] = {
            "user_id": alice_user_id,
            "model_name": "rf",
            "qs": "random",
            "classes": [0, 1],
        }
        active_learning_router.al_service.revoke_delegation.return_value = None

        response = client.delete(
            "/activelearning/1/delegate/bob",
            headers=auth_headers["alice"],
        )
        assert response.status_code == 200
        assert "Delegation revoked" in response.json()["message"]

    def test_revoke_rejects_non_owner(self, client, auth_headers):
        active_learning_router.al_service.storage.al_instances_dict[1] = {
            "user_id": "alice-uuid",
            "model_name": "rf",
            "qs": "random",
            "classes": [0, 1],
        }
        active_learning_router.al_service.revoke_delegation.side_effect = ValueError(
            "Only the instance owner can revoke delegation"
        )

        response = client.delete(
            "/activelearning/1/delegate/bob",
            headers=auth_headers["bob"],
        )
        assert response.status_code == 400
        assert "Only the instance owner" in response.json()["detail"]


class TestListDelegatesEndpoint:
    def test_list_success(self, client, auth_headers):
        alice_user_id = str(client.get("/users/me", headers=auth_headers["alice"]).json()["user_id"])
        active_learning_router.al_service.storage.al_instances_dict[1] = {
            "user_id": alice_user_id,
            "model_name": "rf",
            "qs": "random",
            "classes": [0, 1],
        }
        active_learning_router.al_service.get_delegates.return_value = [
            {"username": "bob", "delegate_user_id": "bob-uuid", "granted_by": alice_user_id, "granted_at": "2026-06-15T10:00:00"}
        ]

        response = client.get(
            "/activelearning/1/delegates",
            headers=auth_headers["alice"],
        )
        assert response.status_code == 200
        assert len(response.json()["delegates"]) == 1
        assert response.json()["delegates"][0]["username"] == "bob"

    def test_list_rejects_non_owner(self, client, auth_headers):
        active_learning_router.al_service.storage.al_instances_dict[1] = {
            "user_id": "alice-uuid",
            "model_name": "rf",
            "qs": "random",
            "classes": [0, 1],
        }
        active_learning_router.al_service.get_delegates.side_effect = ValueError(
            "Only the instance owner can view delegates"
        )

        response = client.get(
            "/activelearning/1/delegates",
            headers=auth_headers["bob"],
        )
        assert response.status_code == 400
        assert "Only the instance owner" in response.json()["detail"]


class TestInstanceListingWithDelegation:
    def test_instances_includes_delegated(self, client, auth_headers, temp_db):
        alice_user_id = str(client.get("/users/me", headers=auth_headers["alice"]).json()["user_id"])
        bob_user_id = str(client.get("/users/me", headers=auth_headers["bob"]).json()["user_id"])

        mock_storage = MagicMock()
        mock_storage.al_instances_dict = {
            1: {"user_id": alice_user_id, "model_name": "rf", "qs": "random", "classes": [0, 1]},
            2: {"user_id": alice_user_id, "model_name": "rf", "qs": "random", "classes": [0, 1]},
        }
        active_learning_router.al_service.storage = mock_storage

        temp_db.delegate_instance(al_instance_id=2, delegate_user_id=bob_user_id, granted_by=alice_user_id)

        response = client.get("/activelearning/instances", headers=auth_headers["bob"])
        assert response.status_code == 200
        instances = response.json()["instances"]
        assert "2" in instances or 2 in instances
