"""Integration tests for the user router."""
import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from fastapi.testclient import TestClient

from app.core.dependencies import get_startup_service
from app.main import app
from app.persistence.duckdb import DuckDbPersistenceService
from app.routers import user_router


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield DuckDbPersistenceService(db_path=Path(tmpdir) / "test.duckdb")


@pytest.fixture
def client(temp_db, monkeypatch):
    monkeypatch.setattr(user_router, "duckdb_service", temp_db)
    from app.core import dependencies
    monkeypatch.setattr(dependencies, "duckdb_persistence_service", temp_db)

    class MockStartupService:
        def load_data_from_minio_into_duckdb(self):
            pass

    monkeypatch.setattr(dependencies, "startup_service", MockStartupService())

    with TestClient(app) as test_client:
        yield test_client


class TestRegister:
    def test_register_returns_user_without_api_key(self, client):
        response = client.post(
            "/users/register", json={"username": "alice", "password": "pwd"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "alice"
        assert "user_id" in data
        assert "api_key" not in data

    def test_register_duplicate_username_returns_409(self, client):
        client.post("/users/register", json={"username": "alice", "password": "pwd"})
        response = client.post(
            "/users/register", json={"username": "alice", "password": "other"}
        )
        assert response.status_code == 409


class TestLogin:
    def test_login_success(self, client):
        client.post("/users/register", json={"username": "alice", "password": "pwd"})
        response = client.post(
            "/users/login", json={"username": "alice", "password": "pwd"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        client.post("/users/register", json={"username": "alice", "password": "pwd"})
        response = client.post(
            "/users/login", json={"username": "alice", "password": "wrong"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/users/login", json={"username": "nobody", "password": "pwd"}
        )
        assert response.status_code == 401


class TestMe:
    def test_me_without_token_returns_system_user(self, client):
        response = client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "system"
        assert data["user_id"] == "00000000-0000-0000-0000-000000000000"

    def test_me_with_valid_token_returns_user(self, client):
        client.post("/users/register", json={"username": "alice", "password": "pwd"})
        login_response = client.post(
            "/users/login", json={"username": "alice", "password": "pwd"}
        )
        token = login_response.json()["access_token"]
        response = client.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["username"] == "alice"

    def test_me_with_invalid_token_returns_401(self, client):
        response = client.get(
            "/users/me", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
