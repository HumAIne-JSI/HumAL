"""Unit tests for JWT authentication helpers."""
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt as pyjwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from app.config.config import SYSTEM_USER_ID
from app.core import dependencies
from app.core.dependencies import create_access_token, get_current_user
from app.persistence.duckdb import DuckDbPersistenceService


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield DuckDbPersistenceService(db_path=Path(tmpdir) / "test.duckdb")


@pytest.fixture
def patched_db(monkeypatch, temp_db):
    monkeypatch.setattr(dependencies, "duckdb_persistence_service", temp_db)
    return temp_db


class TestCreateAccessToken:
    def test_token_contains_expected_claims(self):
        token = create_access_token(user_id="user-123", username="alice")
        payload = pyjwt.decode(
            token,
            key=os.environ["JWT_SECRET_KEY"],
            algorithms=[os.environ["JWT_ALGORITHM"]],
        )
        assert payload["sub"] == "user-123"
        assert payload["username"] == "alice"
        assert "exp" in payload
        assert "iat" in payload

    def test_token_expires_in_future(self):
        token = create_access_token(user_id="user-123", username="alice")
        payload = pyjwt.decode(
            token,
            key=os.environ["JWT_SECRET_KEY"],
            algorithms=[os.environ["JWT_ALGORITHM"]],
        )
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp > datetime.now(timezone.utc)


class TestGetCurrentUser:
    def test_missing_credentials_returns_system_user(self):
        user = get_current_user(credentials=None)
        assert user["user_id"] == SYSTEM_USER_ID
        assert user["username"] == "system"

    def test_valid_token_returns_matching_user(self, patched_db):
        user_id = patched_db.upsert_user(username="alice", password="pwd")
        token = create_access_token(user_id=str(user_id), username="alice")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        user = get_current_user(credentials=credentials)
        assert str(user["user_id"]) == str(user_id)
        assert user["username"] == "alice"

    def test_invalid_token_raises_401(self):
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="not-a-valid-token"
        )
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials)
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        payload = {
            "sub": "user-123",
            "username": "alice",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        token = pyjwt.encode(
            payload,
            key=os.environ["JWT_SECRET_KEY"],
            algorithm=os.environ["JWT_ALGORITHM"],
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials)
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()

    def test_token_with_missing_sub_raises_401(self):
        payload = {"username": "alice"}
        token = pyjwt.encode(
            payload,
            key=os.environ["JWT_SECRET_KEY"],
            algorithm=os.environ["JWT_ALGORITHM"],
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials)
        assert exc_info.value.status_code == 401

    def test_valid_token_for_deleted_user_raises_401(self, patched_db):
        from app.persistence.duckdb.connection import connect

        user_id = patched_db.upsert_user(username="alice", password="pwd")
        token = create_access_token(user_id=str(user_id), username="alice")

        with connect(patched_db.db_path) as conn:
            conn.execute("DELETE FROM users WHERE user_id = ?", [str(user_id)])

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials)
        assert exc_info.value.status_code == 401
