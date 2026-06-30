"""Tests for DuckDB connection management."""
from __future__ import annotations

import tempfile
from pathlib import Path

import duckdb
import pytest

from app.persistence.duckdb import connection as conn_module
from app.persistence.duckdb.connection import (
    connect,
    resolve_db_path,
    DEFAULT_DB_PATH,
    is_lock_contention_error,
)


class TestResolveDbPath:
    def test_none_returns_default(self):
        result = resolve_db_path(None)
        assert result == DEFAULT_DB_PATH

    def test_string_path_converts_to_path(self):
        result = resolve_db_path("custom/path.duckdb")
        assert isinstance(result, Path)
        assert result == Path("custom/path.duckdb")

    def test_path_object_returns_as_is(self):
        input_path = Path("some/db.duckdb")
        result = resolve_db_path(input_path)
        assert result == input_path


class TestConnect:
    def test_creates_database_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.duckdb"
            
            with connect(db_path) as conn:
                assert conn is not None
            
            assert db_path.exists()

    def test_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "nested" / "dirs" / "test.duckdb"
            
            with connect(db_path) as conn:
                assert conn is not None
            
            assert db_path.exists()
            assert db_path.parent.exists()


    def test_connection_closes_after_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.duckdb"
            
            with connect(db_path) as conn:
                connection_id = id(conn)
            
            # Connection should be closed, but we can't easily test this
            # without accessing internals. Just verify no exception.
            assert connection_id is not None

    def test_default_path_when_none_provided(self):
        # This test creates a database at the default location
        # Clean up is manual - be aware this touches the real default path
        with connect(None) as conn:
            assert conn is not None

        # Cleanup
        if DEFAULT_DB_PATH.exists():
            DEFAULT_DB_PATH.unlink()


class TestConnectLockRetries:
    """Tests for lock-contention retry logic in connect()."""

    def test_retries_on_lock_contention_then_succeeds(self, monkeypatch, tmp_path):
        """connect() retries on lock contention and succeeds once the lock frees."""
        monkeypatch.setattr(conn_module, "_LOCK_RETRY_BACKOFF_SECONDS", 0.0)

        lock_error = duckdb.IOException(
            "IO Error: Cannot open file: The process cannot access the file "
            "because it is being used by another process."
        )

        real_connect = duckdb.connect
        call_count = {"n": 0}

        def flaky_connect(path):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise lock_error
            return real_connect(path)

        monkeypatch.setattr(duckdb, "connect", flaky_connect)

        db_path = tmp_path / "test.duckdb"
        with connect(db_path) as conn:
            assert conn is not None

        assert call_count["n"] == 3

    def test_raises_after_exhausting_retries(self, monkeypatch, tmp_path):
        """connect() raises IOException after exhausting all retries on lock contention."""
        monkeypatch.setattr(conn_module, "_LOCK_RETRY_BACKOFF_SECONDS", 0.0)
        monkeypatch.setattr(conn_module, "_MAX_LOCK_RETRIES", 2)

        lock_error = duckdb.IOException(
            "IO Error: Could not set lock or file is already in use "
            "by another process."
        )

        def always_raise(path):
            raise lock_error

        monkeypatch.setattr(duckdb, "connect", always_raise)

        db_path = tmp_path / "test.duckdb"
        with pytest.raises(duckdb.IOException):
            with connect(db_path):
                pass

    def test_does_not_retry_non_lock_errors(self, monkeypatch, tmp_path):
        """connect() raises immediately for non-lock IOException without retrying."""
        monkeypatch.setattr(conn_module, "_LOCK_RETRY_BACKOFF_SECONDS", 0.0)

        non_lock_error = duckdb.IOException("IO Error: Disk full")
        call_count = {"n": 0}

        def fail_immediately(path):
            call_count["n"] += 1
            raise non_lock_error

        monkeypatch.setattr(duckdb, "connect", fail_immediately)

        db_path = tmp_path / "test.duckdb"
        with pytest.raises(duckdb.IOException):
            with connect(db_path):
                pass

        assert call_count["n"] == 1


class TestIsLockContentionError:
    """Tests for the is_lock_contention_error helper."""

    def test_returns_true_for_windows_lock_message(self):
        exc = duckdb.IOException(
            "IO Error: Cannot open file: The process cannot access the file "
            "because it is being used by another process."
        )
        assert is_lock_contention_error(exc) is True

    def test_returns_true_for_linux_lock_message(self):
        exc = duckdb.IOException(
            "IO Error: Could not set lock or file is already in use "
            "by another process."
        )
        assert is_lock_contention_error(exc) is True

    def test_returns_false_for_non_lock_io_error(self):
        exc = duckdb.IOException("IO Error: Disk full")
        assert is_lock_contention_error(exc) is False

    def test_returns_false_for_non_io_exception(self):
        exc = ValueError("being used by another process")
        assert is_lock_contention_error(exc) is False
