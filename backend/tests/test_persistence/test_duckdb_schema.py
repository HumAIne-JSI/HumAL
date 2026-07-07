"""Tests for DuckDB schema initialization."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest

from app.persistence.duckdb.connection import connect
from app.persistence.duckdb.schema import init_database, SCHEMA_VERSION


@pytest.fixture
def temp_db():
    """Create a temporary database for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        yield db_path


class TestInitDatabase:
    def test_creates_all_tables(self, temp_db):
        init_database(temp_db)
        
        with connect(temp_db) as conn:
            # Query information schema to verify tables exist
            tables = conn.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'main'
                ORDER BY table_name
                """
            ).fetchall()
            
            table_names = [row[0] for row in tables]
            
            assert "al_instances" in table_names
            assert "users" in table_names
            assert "tickets" in table_names
            assert "labels" in table_names
            assert "metrics" in table_names
            assert "model_paths" in table_names

    def test_creates_al_instance_id_sequence(self, temp_db):
        init_database(temp_db)

        with connect(temp_db) as conn:
            row = conn.execute("SELECT nextval('al_instance_id_seq')").fetchone()

        assert row is not None
        assert int(row[0]) == 1

    def test_al_instances_schema(self, temp_db):
        init_database(temp_db)
        
        with connect(temp_db) as conn:
            columns = conn.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'al_instances'
                ORDER BY ordinal_position
                """
            ).fetchall()
            
            col_dict = {col[0]: col[1] for col in columns}
            
            assert "al_instance_id" in col_dict
            assert "model_name" in col_dict
            assert "query_strategy" in col_dict
            assert "classes" in col_dict
            assert "created_at" in col_dict

    def test_users_schema(self, temp_db):
        init_database(temp_db)
        
        with connect(temp_db) as conn:
            columns = conn.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
                """
            ).fetchall()
            
            col_dict = {col[0]: col[1] for col in columns}
            
            assert "user_id" in col_dict
            assert "username" in col_dict
            assert "password" in col_dict
            assert "created_at" in col_dict

    def test_tickets_schema(self, temp_db):
        init_database(temp_db)
        
        with connect(temp_db) as conn:
            columns = conn.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'tickets'
                ORDER BY ordinal_position
                """
            ).fetchall()
            
            col_dict = {col[0]: col[1] for col in columns}
            
            assert "ref" in col_dict
            assert "split" in col_dict
            assert "title_anon" in col_dict
            assert "dataset_timestamp" in col_dict

    def test_labels_schema_with_foreign_keys(self, temp_db):
        init_database(temp_db)
        
        with connect(temp_db) as conn:
            columns = conn.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'labels'
                ORDER BY ordinal_position
                """
            ).fetchall()
            
            col_dict = {col[0]: col[1] for col in columns}
            
            assert "al_instance_id" in col_dict
            assert "user_id" in col_dict
            assert "ref" in col_dict
            assert "label" in col_dict
            assert "labeled_at" in col_dict

    def test_metrics_schema(self, temp_db):
        init_database(temp_db)
        
        with connect(temp_db) as conn:
            columns = conn.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'metrics'
                ORDER BY ordinal_position
                """
            ).fetchall()
            
            col_dict = {col[0]: col[1] for col in columns}
            
            assert "al_instance_id" in col_dict
            assert "iteration_id" in col_dict
            assert "f1_score" in col_dict
            assert "mean_entropy" in col_dict
            assert "num_labeled" in col_dict
            assert "accuracy" in col_dict
            assert "precision_macro" in col_dict
            assert "precision_weighted" in col_dict
            assert "recall_macro" in col_dict
            assert "recall_weighted" in col_dict
            assert "f1_per_class" in col_dict
            assert "confusion_matrix" in col_dict
            assert "roc_auc_ovr_macro" in col_dict
            assert "created_at" in col_dict

    def test_model_paths_schema(self, temp_db):
        init_database(temp_db)
        
        with connect(temp_db) as conn:
            columns = conn.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'model_paths'
                ORDER BY ordinal_position
                """
            ).fetchall()
            
            col_dict = {col[0]: col[1] for col in columns}
            
            assert "al_instance_id" in col_dict
            assert "model_id" in col_dict
            assert "path_to_model" in col_dict
            assert "created_at" in col_dict

    def test_users_schema_excludes_api_key(self, temp_db):
        init_database(temp_db)
        
        with connect(temp_db) as conn:
            columns = conn.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
                """
            ).fetchall()
            
            col_dict = {col[0]: col[1] for col in columns}
            
            assert "api_key" not in col_dict

    def test_al_instances_schema_includes_user_id(self, temp_db):
        init_database(temp_db)
        
        with connect(temp_db) as conn:
            columns = conn.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'al_instances'
                ORDER BY ordinal_position
                """
            ).fetchall()
            
            col_dict = {col[0]: col[1] for col in columns}
            
            assert "user_id" in col_dict

    def test_xai_jobs_schema_includes_user_id(self, temp_db):
        init_database(temp_db)
        
        with connect(temp_db) as conn:
            columns = conn.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'xai_jobs'
                ORDER BY ordinal_position
                """
            ).fetchall()
            
            col_dict = {col[0]: col[1] for col in columns}
            
            assert "user_id" in col_dict

    def test_idempotent_initialization(self, temp_db):
        """Test that running init_database multiple times doesn't error."""
        init_database(temp_db)
        init_database(temp_db)
        init_database(temp_db)
        
        with connect(temp_db) as conn:
            tables = conn.execute(
                """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'main'
                """
            ).fetchone()
            
            # Should still have the same tables, no duplicates
            assert tables[0] >= 6

    def test_al_events_schema_includes_haic_columns(self, temp_db):
        init_database(temp_db)
        with connect(temp_db) as conn:
            columns = conn.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'al_events'
                ORDER BY ordinal_position
                """
            ).fetchall()
            col_names = {col[0] for col in columns}
            assert "actor_type" in col_names
            assert "agent" in col_names
            assert "object_id" in col_names
            assert "duration_s" in col_names
            assert "correct" in col_names
            assert "ai_suggested" in col_names


class TestSchemaVersioning:
    """Tests for the schema version mechanism."""

    def test_schema_meta_table_created_with_current_version(self, temp_db):
        """After init, _schema_meta exists and stores SCHEMA_VERSION."""
        init_database(temp_db)
        with connect(temp_db) as conn:
            row = conn.execute(
                "SELECT version FROM _schema_meta LIMIT 1"
            ).fetchone()
            assert row is not None
            assert row[0] == SCHEMA_VERSION

    def test_version_match_skips_rebuild(self, temp_db):
        """When the stored version matches, init_database does not rebuild."""
        init_database(temp_db)

        # Insert a user that would survive a no-rebuild but be lost on rebuild
        with connect(temp_db) as conn:
            conn.execute(
                "INSERT INTO users (user_id, username, password) "
                "VALUES ('11111111-1111-1111-1111-111111111111'::UUID, 'survivor', 'pwd')"
            )

        # Re-init — version matches, should skip
        init_database(temp_db)

        with connect(temp_db) as conn:
            row = conn.execute(
                "SELECT username FROM users "
                "WHERE user_id = '11111111-1111-1111-1111-111111111111'::UUID"
            ).fetchone()
            assert row is not None
            assert row[0] == "survivor"

    def test_version_mismatch_rebuilds_and_drops_data(self, temp_db):
        """When the stored version mismatches, init_database rebuilds and drops all data."""
        init_database(temp_db)

        # Insert data
        with connect(temp_db) as conn:
            conn.execute(
                "INSERT INTO users (user_id, username, password) "
                "VALUES ('11111111-1111-1111-1111-111111111111'::UUID, 'doomed', 'pwd')"
            )

        # Force a version mismatch
        with connect(temp_db) as conn:
            conn.execute("UPDATE _schema_meta SET version = 0")

        # Re-init — should detect mismatch and rebuild
        init_database(temp_db)

        with connect(temp_db) as conn:
            # Data should be gone
            row = conn.execute(
                "SELECT username FROM users "
                "WHERE user_id = '11111111-1111-1111-1111-111111111111'::UUID"
            ).fetchone()
            assert row is None
            # Version should be updated to current
            row = conn.execute(
                "SELECT version FROM _schema_meta LIMIT 1"
            ).fetchone()
            assert row[0] == SCHEMA_VERSION

    def test_old_db_without_schema_meta_triggers_rebuild(self, temp_db):
        """A DB created before versioning (no _schema_meta) gets rebuilt on init."""
        # Simulate an old DB: create tables directly without _schema_meta
        from app.persistence.duckdb.schema import _create_tables, _create_indexes

        with connect(temp_db) as conn:
            _create_tables(conn)
            _create_indexes(conn)

        # Verify _schema_meta does not exist yet
        with connect(temp_db) as conn:
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_name = '_schema_meta'"
            ).fetchall()
            assert len(tables) == 0

        # init_database should detect missing _schema_meta and rebuild
        init_database(temp_db)

        with connect(temp_db) as conn:
            row = conn.execute(
                "SELECT version FROM _schema_meta LIMIT 1"
            ).fetchone()
            assert row is not None
            assert row[0] == SCHEMA_VERSION


class TestInitDatabaseLockContention:
    """Tests for lock-contention graceful skip in init_database."""

    def test_init_database_skips_on_lock_contention(self, monkeypatch, tmp_path):
        """init_database returns without raising when DuckDB is locked by another process."""
        from app.persistence.duckdb import connection as conn_module

        # Make retries instant so the test is fast
        monkeypatch.setattr(conn_module, "_LOCK_RETRY_BACKOFF_SECONDS", 0.0)
        monkeypatch.setattr(conn_module, "_MAX_LOCK_RETRIES", 1)

        lock_error = duckdb.IOException(
            "IO Error: Cannot open file: The process cannot access the file "
            "because it is being used by another process."
        )

        def _always_raise_lock(path):
            raise lock_error

        monkeypatch.setattr(duckdb, "connect", _always_raise_lock)

        db_path = tmp_path / "test.duckdb"

        # Should not raise — graceful skip
        init_database(db_path)

        # DB file should not have been created (connect never succeeded)
        assert not db_path.exists()

    def test_init_database_raises_on_non_lock_io_error(self, monkeypatch, tmp_path):
        """init_database re-raises non-lock IOException (e.g. disk full)."""
        from app.persistence.duckdb import connection as conn_module

        monkeypatch.setattr(conn_module, "_LOCK_RETRY_BACKOFF_SECONDS", 0.0)

        non_lock_error = duckdb.IOException("IO Error: Disk full")

        def _always_raise_disk_full(path):
            raise non_lock_error

        monkeypatch.setattr(duckdb, "connect", _always_raise_disk_full)

        db_path = tmp_path / "test.duckdb"

        with pytest.raises(duckdb.IOException):
            init_database(db_path)
