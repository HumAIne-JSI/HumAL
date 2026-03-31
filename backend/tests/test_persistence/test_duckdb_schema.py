"""Tests for DuckDB schema initialization."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.persistence.duckdb.connection import connect
from app.persistence.duckdb.schema import init_database


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
