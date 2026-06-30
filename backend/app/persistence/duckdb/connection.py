from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

import duckdb


DEFAULT_DB_PATH = Path("storage/db/humal.duckdb")

_MAX_LOCK_RETRIES = 10
_LOCK_RETRY_BACKOFF_SECONDS = 1.0

_LOCK_ERROR_MARKERS = (
    "being used by another process",
    "already in use",
    "could not set lock",
    "could not lock",
    "database is locked",
)

logger = logging.getLogger(__name__)


def resolve_db_path(db_path: Optional[str | Path]) -> Path:
    if db_path is None:
        return Path(os.getenv("DUCKDB_PATH", DEFAULT_DB_PATH))
    return Path(db_path)


def is_lock_contention_error(exc: Exception) -> bool:
    """Return True if *exc* indicates DuckDB lock contention (another process holds the file)."""
    if not isinstance(exc, duckdb.IOException):
        return False
    message = str(exc).lower()
    return any(marker in message for marker in _LOCK_ERROR_MARKERS)


def _connect_with_retries(path: str) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection, retrying on lock contention with bounded backoff."""
    last_exc: Optional[duckdb.IOException] = None
    for attempt in range(_MAX_LOCK_RETRIES + 1):
        try:
            return duckdb.connect(path)
        except duckdb.IOException as exc:
            if not is_lock_contention_error(exc):
                raise
            last_exc = exc
            if attempt < _MAX_LOCK_RETRIES:
                logger.warning(
                    "DuckDB lock contention on %s (attempt %d/%d), retrying in %ss...",
                    path,
                    attempt + 1,
                    _MAX_LOCK_RETRIES + 1,
                    _LOCK_RETRY_BACKOFF_SECONDS,
                )
                time.sleep(_LOCK_RETRY_BACKOFF_SECONDS)
    assert last_exc is not None  # pragma: no cover - only reached when retries exhausted
    raise last_exc


@contextmanager
def connect(db_path: Optional[str | Path] = None) -> Iterator[duckdb.DuckDBPyConnection]:
    path = resolve_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = _connect_with_retries(str(path))
    try:
        yield conn
    finally:
        conn.close()
