from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import duckdb

from .connection import connect, is_lock_contention_error


SCHEMA_VERSION = 1

logger = logging.getLogger(__name__)


def init_database(db_path: Optional[str | Path] = None) -> None:
    """Create or rebuild the DuckDB schema when the version is out of date.

    Compares the version stored in the ``_schema_meta`` table against
    ``SCHEMA_VERSION``. On mismatch (or a fresh database) all tables are
    dropped and recreated — no data is preserved. On DuckDB lock contention
    (e.g. a concurrent pod during a rolling update) the call logs a warning
    and returns without raising, so startup is not blocked.
    """
    try:
        with connect(db_path) as conn:
            current_version = _read_schema_version(conn)
            if current_version == SCHEMA_VERSION:
                return
            logger.info(
                "Schema version mismatch (db=%s, code=%s) — rebuilding all tables.",
                current_version,
                SCHEMA_VERSION,
            )
            _drop_all_tables(conn)
            _create_tables(conn)
            _create_indexes(conn)
            _populate_default_users(conn)
            _populate_default_al_instance(conn)
            _write_schema_version(conn)
    except duckdb.IOException as exc:
        if is_lock_contention_error(exc):
            logger.warning(
                "DuckDB lock contention during schema init — skipping. "
                "Another process likely holds the file open. Details: %s",
                exc,
            )
            return
        raise


def _read_schema_version(conn: duckdb.DuckDBPyConnection) -> Optional[int]:
    """Return the schema version stored in the database, or None if not set."""
    try:
        row = conn.execute("SELECT version FROM _schema_meta LIMIT 1").fetchone()
        return int(row[0]) if row else None
    except duckdb.CatalogException:
        return None


def _write_schema_version(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the _schema_meta table and store the current SCHEMA_VERSION."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _schema_meta (
            version INTEGER NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute("INSERT INTO _schema_meta (version) VALUES (?)", [SCHEMA_VERSION])


def _drop_all_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Drop all known tables in FK-respecting order (children first)."""
    tables_in_drop_order = [
        "labels",
        "label_decisions",
        "metrics",
        "model_paths",
        "al_events",
        "xai_jobs",
        "instance_delegations",
        "tickets",
        "al_instances",
        "users",
        "_schema_meta",
    ]
    for table_name in tables_in_drop_order:
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")


def _create_tables(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS al_instances (
            al_instance_id INTEGER PRIMARY KEY,
            model_name VARCHAR,
            query_strategy VARCHAR,
            classes INTEGER[],
            user_id UUID DEFAULT '00000000-0000-0000-0000-000000000000'::UUID NOT NULL,
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
        CREATE TABLE IF NOT EXISTS tickets (
            ref VARCHAR PRIMARY KEY,
            service_subcategory_name VARCHAR,
            service_name VARCHAR,
            request_type VARCHAR,
            last_team_id_name VARCHAR,
            title_anon VARCHAR,
            description_anon VARCHAR,
            public_log_anon VARCHAR,
            split VARCHAR NOT NULL CHECK (split IN ('train', 'test')),
            dataset_timestamp TIMESTAMP
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
        CREATE TABLE IF NOT EXISTS label_decisions (
            al_instance_id INTEGER NOT NULL,
            ref VARCHAR NOT NULL,
            user_id UUID,
            label VARCHAR,
            labeled_at TIMESTAMP,
            model_prediction VARCHAR,
            latency_ms INTEGER,
            most_helpful_feature VARCHAR,
            xai_result JSON,
            similar_tickets JSON,
            PRIMARY KEY (al_instance_id, ref),
            FOREIGN KEY (al_instance_id) REFERENCES al_instances(al_instance_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
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
        CREATE TABLE IF NOT EXISTS model_paths (
            al_instance_id INTEGER NOT NULL,
            model_id INTEGER NOT NULL,
            path_to_model VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (al_instance_id, model_id),
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
            actor_type VARCHAR,
            agent VARCHAR,
            object_id VARCHAR,
            duration_s DOUBLE,
            correct BOOLEAN,
            ai_suggested VARCHAR,
            FOREIGN KEY (al_instance_id) REFERENCES al_instances(al_instance_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )

    conn.execute(
        """ 
        CREATE TABLE IF NOT EXISTS xai_jobs (
            job_id UUID PRIMARY KEY,
            al_instance_id INTEGER NOT NULL,
            user_id UUID,
            model_id INTEGER NOT NULL,
            ticket_ref_or_sha VARCHAR NOT NULL,
            status VARCHAR NOT NULL CHECK (status IN ('queued','processing','completed','failed')),
            request_ticket_location VARCHAR NOT NULL,
            request_model_location VARCHAR NOT NULL,
            request_preprocessor_location VARCHAR,
            request_one_hot_encoder_location VARCHAR,
            request_raw_tickets_locations VARCHAR[] NOT NULL,
            result_location VARCHAR,
            result_file_names VARCHAR[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            FOREIGN KEY (al_instance_id) REFERENCES al_instances(al_instance_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS instance_delegations (
            al_instance_id INTEGER NOT NULL,
            delegate_user_id UUID NOT NULL,
            granted_by UUID NOT NULL,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (al_instance_id, delegate_user_id)
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
        CREATE INDEX IF NOT EXISTS idx_label_decisions_instance_ref
        ON label_decisions(al_instance_id, ref)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_label_decisions_user
        ON label_decisions(user_id)
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
        CREATE INDEX IF NOT EXISTS idx_model_paths_instance
        ON model_paths(al_instance_id)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tickets_split
        ON tickets(split)
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
        CREATE INDEX IF NOT EXISTS idx_xai_jobs_instance
        ON xai_jobs(al_instance_id)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_instance_delegations_delegate
        ON instance_delegations(delegate_user_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_instance_delegations_instance
        ON instance_delegations(al_instance_id)
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
        INSERT INTO al_instances (al_instance_id, model_name, query_strategy, classes, user_id, created_at)
        VALUES (
            0,
            'default_model',
            'default_query_strategy',
            ARRAY[1, 2],
            '00000000-0000-0000-0000-000000000000'::UUID,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT DO NOTHING
        """
    )
