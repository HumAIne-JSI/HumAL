from fastapi import APIRouter, HTTPException
from app.core.dependencies import get_data_service

router = APIRouter(prefix="/data", tags=["data"])
data_service = get_data_service()

@router.post("/tickets")
def get_tickets(indices: list[str]):
    """
    Get tickets by their indices.

    Returns:
        Dictionary containing tickets
    """

    return data_service.get_tickets(indices=indices)

@router.get("/teams")
def get_teams():
    """
    Get teams from the dataset. 

    Returns:
        Dictionary containing teams
    """

    return data_service.get_teams()

@router.get("/categories")
def get_categories():
    """
    Get categories from the dataset.
    
    Returns:
        Dictionary containing categories
    """

    return data_service.get_categories()

@router.get("/subcategories")
def get_subcategories():
    """
    Get subcategories from the dataset.
    
    Returns:
        Dictionary containing subcategories
    """

    return data_service.get_subcategories()
