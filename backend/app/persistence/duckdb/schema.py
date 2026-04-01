from __future__ import annotations

from pathlib import Path
from typing import Optional

import duckdb

from .connection import connect


def init_database(db_path: Optional[str | Path] = None) -> None:
    """Create/upgrade tables needed by HumAL persistence."""
    with connect(db_path) as conn:
        _create_tables(conn)
        _create_indexes(conn)
        _populate_default_users(conn)
        _populate_default_al_instance(conn)


def _create_tables(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS al_instances (
            al_instance_id INTEGER PRIMARY KEY,
            model_name VARCHAR,
            query_strategy VARCHAR,
            classes INTEGER[],
            minio_prefix VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY,
            username VARCHAR UNIQUE,
            password VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS labels (
            al_instance_id INTEGER NOT NULL,
            user_id UUID NOT NULL,
            ref VARCHAR NOT NULL,
            label VARCHAR,
            split VARCHAR NOT NULL CHECK (split IN ('train', 'test')),
            labeled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (al_instance_id, ref, user_id),
            FOREIGN KEY (al_instance_id) REFERENCES al_instances(al_instance_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (ref) REFERENCES tickets(ref)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS models (
            model_id INTEGER NOT NULL,
            al_instance_id INTEGER NOT NULL,
            metrics JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (model_id, al_instance_id),
            FOREIGN KEY (al_instance_id) REFERENCES al_instances(al_instance_id)
        )
        """
    )


    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS metrics (
            al_instance_id INTEGER NOT NULL,
            iteration_id INTEGER NOT NULL,
            f1_score DOUBLE,
            mean_entropy DOUBLE,
            num_labeled INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (al_instance_id, iteration_id),
            FOREIGN KEY (al_instance_id) REFERENCES al_instances(al_instance_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS al_events (
            al_instance_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id UUID,
            action VARCHAR,
            latency_ms INTEGER,
            payload JSON,
            FOREIGN KEY (al_instance_id) REFERENCES al_instances(al_instance_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dataset_configs (
            al_instance_id INTEGER PRIMARY KEY,
            dataset_name VARCHAR NOT NULL,
            version VARCHAR NOT NULL,
            dataset_format VARCHAR NOT NULL,
            id_field VARCHAR NOT NULL,
            splits JSON NOT NULL,
            fields JSON NOT NULL,
            task JSON NOT NULL,
            features JSON NOT NULL,
            preprocessing JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (al_instance_id) REFERENCES al_instances(al_instance_id)
        )
        """
    )


def _create_indexes(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_labels_instance_ref
        ON labels(al_instance_id, ref)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_metrics_instance
        ON metrics(al_instance_id)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_models_instance
        ON models(al_instance_id)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_al_events_instance
        ON al_events(al_instance_id)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_dataset_configs_name
        ON dataset_configs(dataset_name)
        """
    )


def _populate_default_users(conn: duckdb.DuckDBPyConnection) -> None:
    """Insert default system user for deployments without user authentication."""
    conn.execute(
        """
        INSERT INTO users (user_id, username, password, created_at)
        VALUES (
            '00000000-0000-0000-0000-000000000000'::UUID,
            'system',
            NULL,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT DO NOTHING
        """
    )

def _populate_default_al_instance(conn: duckdb.DuckDBPyConnection) -> None:
    """Insert default AL instance for deployments without multiple AL instances."""
    conn.execute(
        """
        INSERT INTO al_instances (al_instance_id, model_name, query_strategy, classes, train_data_path, test_data_path, created_at)
        VALUES (
            0,
            'default_model',
            'default_query_strategy',
            ARRAY[1, 2],
            NULL,
            NULL,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT DO NOTHING
        """
    )
