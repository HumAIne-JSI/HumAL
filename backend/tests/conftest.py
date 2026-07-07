"""Shared fixtures and setup for all tests."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

# --- Temp storage root: keeps DuckDB / model artifacts out of backend/storage/ ---
_TEST_STORAGE_ROOT = Path(tempfile.mkdtemp(prefix="humal_test_storage_"))
_TEST_DB_PATH = _TEST_STORAGE_ROOT / "db" / "humal.duckdb"

# IMPORTANT: set ALL env vars required by module-level code BEFORE any import
# that transitively loads app.config (which evaluates os.getenv at import time).
# In particular app.config.config is reached via app.persistence.duckdb.service.
_ST_CACHE = str(Path(__file__).resolve().parent.parent / "sentence_transformers_cache")
os.environ.setdefault("DUCKDB_PATH", str(_TEST_DB_PATH))
os.environ.setdefault("MODELS_DIR", str(_TEST_STORAGE_ROOT / "models"))
os.environ.setdefault("ENCODERS_DIR", str(_TEST_STORAGE_ROOT / "encoders"))
os.environ.setdefault("USE_RABBITMQ", "0")
os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("SENTENCE_TRANSFORMERS_CACHE_DIR", _ST_CACHE)
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Keep the connection module's DEFAULT_DB_PATH in sync with DUCKDB_PATH so the
# resolve_db_path(None) fallback returns the same value that tests import.
import app.persistence.duckdb.connection as _duckdb_conn
_duckdb_conn.DEFAULT_DB_PATH = _TEST_DB_PATH

# Prevent MinioClient from attempting network calls during module-level import.
import app.core.minio_client
if not isinstance(app.core.minio_client.MinioClient, MagicMock):
    _minio_patcher = patch.object(app.core.minio_client, "MinioClient", autospec=False)
    _minio_patcher.start()

# --- Mock SentenceTransformer so tests run fully offline (no model download) ---
# `.encode()` must return a 2-D ndarray whose row count matches the input list
# length (dispatch_team and inference build feature matrices from it).
_st_mock = MagicMock()

def _fake_encode(sentences, show_progress_bar=False, **kwargs):
    return np.zeros((len(sentences), 8), dtype=float)

_st_mock.return_value.encode.side_effect = _fake_encode

import app.services.data_preprocessing
import app.services.inference_svc
import app.services.xai_svc
for _mod in (app.services.data_preprocessing, app.services.inference_svc, app.services.xai_svc):
    if not isinstance(getattr(_mod, "SentenceTransformer", None), MagicMock):
        setattr(_mod, "SentenceTransformer", _st_mock)

# --- Mock spacy.load so XaiService._get_spacy_nlp doesn't need en_core_web_sm ---
try:
    import spacy  # noqa: F401  (offline-safe: importing the package never loads a model)
    if not isinstance(getattr(spacy, "load", None), MagicMock):
        spacy.load = MagicMock()
except ImportError:
    pass
