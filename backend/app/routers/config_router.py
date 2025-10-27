from fastapi import APIRouter
from app.core.dependencies import get_config_service
from typing import List

router = APIRouter(prefix="/config", tags=["configuration"])
config_service = get_config_service()

@router.get("/models")
def get_available_models():
    """
    Get all available machine learning model names.
    
    Returns:
        Dictionary containing model names
    """
    return config_service.get_available_models()

@router.get("/query-strategies")
def get_available_query_strategies():
    """
    Get all available query strategy names.
    
    Returns:
        Dictionary containing query strategy names
    """
    return config_service.get_available_query_strategies()
