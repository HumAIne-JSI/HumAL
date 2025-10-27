# app/core/dependencies.py
from fastapi import Depends
from app.core.storage import ActiveLearningStorage
from app.services.active_learning_svc import ActiveLearningService
from app.services.inference_svc import InferenceService
from app.services.config_svc import ConfigService
from app.services.data_service import DataService
from app.services.xai_svc import XaiService

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