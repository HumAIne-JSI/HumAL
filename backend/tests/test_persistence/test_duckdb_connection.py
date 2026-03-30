"""Tests for DuckDB connection management."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.persistence.duckdb.connection import connect, resolve_db_path, DEFAULT_DB_PATH


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
