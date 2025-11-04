# app/core/dependencies.py
from fastapi import Depends
from app.core.storage import ActiveLearningStorage
from app.services.active_learning_svc import ActiveLearningService
from app.services.inference_svc import InferenceService
from app.services.config_svc import ConfigService
from app.services.data_service import DataService
from app.services.xai_svc import XaiService
from app.services.resolution_svc import ResolutionService
import os

# Create instances
storage = ActiveLearningStorage()
al_service = ActiveLearningService(storage)
inference_service = InferenceService(storage)
config_service = ConfigService()
data_service = DataService(storage)
xai_service = XaiService(storage, inference_service)

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

def get_xai_service():
    return xai_service
    
# Lazy-loaded resolution service (heavy models)
_resolution_service_instance = None

def get_resolution_service() -> ResolutionService:
    """Get or create resolution service instance (lazy-loaded due to heavy ML models)"""
    global _resolution_service_instance
    if _resolution_service_instance is None:
        _resolution_service_instance = ResolutionService(
            knowledge_base_path=os.getenv(
                "KNOWLEDGE_BASE_PATH",
                "backend/data/tickets_large_first_reply_label.csv"
            ),
            ticket_classifier_path=os.getenv(
                "TICKET_CLASSIFIER_PATH",
                "./ticket_classifier_model"
            ),
            team_classifier_path=os.getenv(
                "TEAM_CLASSIFIER_PATH",
                "./perfect_team_classifier"
            )
        )
    return _resolution_service_instance