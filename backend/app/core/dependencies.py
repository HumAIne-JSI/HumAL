# app/core/dependencies.py
from fastapi import Depends
from app.core.storage import ActiveLearningStorage
from app.services.active_learning_svc import ActiveLearningService
from app.services.inference_svc import InferenceService

# Create instances
storage = ActiveLearningStorage()
al_service = ActiveLearningService(storage)
inference_service = InferenceService(storage)

# Dependency functions
def get_storage():
    return storage

def get_al_service():
    return al_service

def get_inference_service():
    return inference_service