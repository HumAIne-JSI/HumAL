# app/core/dependencies.py
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.storage import ActiveLearningStorage
from app.services.active_learning_svc import ActiveLearningService
from app.services.inference_svc import InferenceService
from app.services.config_svc import ConfigService
from app.services.data_service import DataService
from app.services.benchmarking_svc import BenchmarkingService
from app.services.xai_svc import XaiService
from app.services.ticket_vectorizer_svc import TicketVectorizerService
from app.persistence.duckdb import DuckDbPersistenceService
from app.persistence.local_artifacts import LocalArtifactsStore
from app.persistence import MinioService
from app.services.startup_svc import StartupService
from app.core.minio_client import MinioClient
from app.core.rabbitmq_client import RabbitMQClient
from app.config.config import SYSTEM_USER_ID, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from pathlib import Path
import os

# Create instances
storage = ActiveLearningStorage()
duckdb_persistence_service = DuckDbPersistenceService(
    db_path=os.getenv("DUCKDB_PATH", "storage/db/humal.duckdb")
)
local_artifacts_store = LocalArtifactsStore(
    models_dir=Path(os.getenv("MODELS_DIR", "storage/models")),
    encoders_dir=Path(os.getenv("ENCODERS_DIR", "storage/encoders"))
)
minio_client = MinioClient()
minio_service = MinioService(client=minio_client)
if os.getenv("USE_RABBITMQ", "0") == "1":
    rabbitmq_client = RabbitMQClient(url=os.getenv("RABBIT_URL", ""))
al_service = ActiveLearningService(storage, duckdb_persistence_service, local_artifacts_store, minio_service)
inference_service = InferenceService(storage, local_artifacts_store, duckdb_persistence_service)
config_service = ConfigService()
data_service = DataService(duckdb_service=duckdb_persistence_service)
ticket_vectorizer_service = TicketVectorizerService(minio_service=minio_service)
benchmarking_service = BenchmarkingService(duckdb_persistence_service, minio_service)
xai_service = XaiService(
    storage,
    inference_service,
    local_artifacts_store,
    minio_service=minio_service,
    duckdb_service=duckdb_persistence_service,
    rabbitmq_client=rabbitmq_client if os.getenv("USE_RABBITMQ", "0") == "1" else None,
    ticket_vectorizer_service=ticket_vectorizer_service
)
al_service.benchmarking_service = benchmarking_service
startup_service = StartupService(
    duckdb_service=duckdb_persistence_service,
    minio_service=minio_service,
)


# Dependency functions
def get_storage():
    return storage

def get_al_service():
    return al_service

def get_inference_service():
    return inference_service

def get_config_service():
    return config_service

def get_data_service():
    return data_service

def get_ticket_vectorizer_service():
    return ticket_vectorizer_service

def get_benchmarking_service() -> BenchmarkingService:
    return benchmarking_service

def get_xai_service():
    return xai_service

def get_duckdb_persistence_service() -> DuckDbPersistenceService:
    return duckdb_persistence_service

def get_local_artifacts_store() -> LocalArtifactsStore:
    return local_artifacts_store

def get_startup_service() -> StartupService:
    return startup_service

def get_rabbitmq_client() -> RabbitMQClient:
    if os.getenv("USE_RABBITMQ", "0") == "1":
        return rabbitmq_client
    return None


security = HTTPBearer(auto_error=False)


def create_access_token(*, user_id: str, username: str) -> str:
    """Create a JWT access token for the given user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    Resolve the Authorization: Bearer <token> header to a user dict.
    If the header is missing, return the system user.
    """
    if credentials is None:
        return {
            "user_id": SYSTEM_USER_ID,
            "username": "system",
        }

    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token") from None

    user_id = payload.get("sub")
    username = payload.get("username")
    if user_id is None or username is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = duckdb_persistence_service.get_user(user_id=user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
