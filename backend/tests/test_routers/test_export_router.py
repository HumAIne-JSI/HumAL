"""Integration tests for the export endpoint."""
from __future__ import annotations

import io
import os
import tempfile
import zipfile
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


def _zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", "{}")
    buf.seek(0)
    return buf.getvalue()


class TestExportEndpoint:
    def test_export_success(self, client, auth_headers):
        alice_user_id = str(
            client.get("/users/me", headers=auth_headers["alice"]).json()["user_id"]
        )
        active_learning_router.al_service.storage.al_instances_dict = {
            1: {
                "user_id": alice_user_id,
                "model_name": "svm",
                "qs": "random",
                "classes": [0, 1],
            }
        }
        zip_bytes = _zip_bytes()
        buf = io.BytesIO(zip_bytes)
        active_learning_router.al_service.export_instance.return_value = (
            buf,
            "export_al_1_20260101T000000.zip",
        )

        response = client.get("/activelearning/1/export", headers=auth_headers["alice"])

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert "attachment" in response.headers["content-disposition"]
        assert "export_al_1_" in response.headers["content-disposition"]
        assert response.content == zip_bytes
        active_learning_router.al_service.export_instance.assert_called_once_with(1)

    def test_export_404_when_instance_missing(self, client, auth_headers):
        active_learning_router.al_service.storage.al_instances_dict = {}

        response = client.get("/activelearning/1/export", headers=auth_headers["alice"])

        assert response.status_code == 404

    def test_export_403_when_not_authorized(self, client, auth_headers):
        active_learning_router.al_service.storage.al_instances_dict = {
            1: {
                "user_id": "alice-uuid-not-bob",
                "model_name": "svm",
                "qs": "random",
                "classes": [0, 1],
            }
        }

        response = client.get("/activelearning/1/export", headers=auth_headers["bob"])

        assert response.status_code == 403

    def test_export_400_on_value_error(self, client, auth_headers):
        alice_user_id = str(
            client.get("/users/me", headers=auth_headers["alice"]).json()["user_id"]
        )
        active_learning_router.al_service.storage.al_instances_dict = {
            1: {
                "user_id": alice_user_id,
                "model_name": "svm",
                "qs": "random",
                "classes": [0, 1],
            }
        }
        active_learning_router.al_service.export_instance.side_effect = ValueError(
            "DuckDB persistence is not configured"
        )

        response = client.get("/activelearning/1/export", headers=auth_headers["alice"])

        assert response.status_code == 400
        assert "persistence is not configured" in response.json()["detail"]
