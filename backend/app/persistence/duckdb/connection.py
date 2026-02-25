from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
from typing import Iterator, Optional

import duckdb


DEFAULT_DB_PATH = "storage/db/humal.duckdb"


def resolve_db_path(db_path: Optional[str | Path]) -> Path:
    if db_path is None:
        return Path(os.getenv("DUCKDB_PATH", DEFAULT_DB_PATH))
    return Path(db_path)


@contextmanager
def connect(db_path: Optional[str | Path] = None) -> Iterator[duckdb.DuckDBPyConnection]:
    path = resolve_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(path)) as conn:
        yield conn
