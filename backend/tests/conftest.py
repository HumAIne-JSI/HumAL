"""Shared fixtures and setup for all tests."""
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Set env vars required by module-level code in app.core.dependencies before
# any app modules are imported.
_ST_CACHE = str(Path(__file__).resolve().parent.parent / "sentence_transformers_cache")
os.environ.setdefault("USE_RABBITMQ", "0")
os.environ.setdefault("SENTENCE_TRANSFORMERS_CACHE_DIR", _ST_CACHE)
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Prevent MinioClient from attempting network calls during module-level import.
import app.core.minio_client
if not isinstance(app.core.minio_client.MinioClient, MagicMock):
    _minio_patcher = patch.object(app.core.minio_client, "MinioClient", autospec=False)
    _minio_patcher.start()
