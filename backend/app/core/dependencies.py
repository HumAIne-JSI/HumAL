# app/core/dependencies.py
from fastapi import Depends
from app.core.storage import ActiveLearningStorage
from app.services.active_learning_svc import ActiveLearningService
from app.services.inference_svc import InferenceService
from app.services.config_svc import ConfigService
from app.services.data_service import DataService
from app.services.xai_svc import XaiService
from app.services.ticket_vectorizer_svc import TicketVectorizerService
from app.persistence.duckdb import DuckDbPersistenceService
from app.persistence.local_artifacts import LocalArtifactsStore
from app.persistence import MinioService
from app.services.startup_svc import StartupService
from app.core.minio_client import MinioClient
from app.core.rabbitmq_client import RabbitMQClient
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
inference_service = InferenceService(storage, local_artifacts_store)
config_service = ConfigService()
data_service = DataService(duckdb_service=duckdb_persistence_service)
ticket_vectorizer_service = TicketVectorizerService(minio_service=minio_service)
xai_service = XaiService(
    storage,
    inference_service,
    local_artifacts_store,
    minio_service=minio_service,
    duckdb_service=duckdb_persistence_service,
    rabbitmq_client=rabbitmq_client if os.getenv("USE_RABBITMQ", "0") == "1" else None,
    ticket_vectorizer_service=ticket_vectorizer_service
)
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
