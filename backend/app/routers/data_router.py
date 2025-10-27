from fastapi import APIRouter, HTTPException
from app.core.dependencies import get_data_service

router = APIRouter(prefix="/data", tags=["data"])
data_service = get_data_service()

@router.post("/{al_instance_id}/tickets")
def get_tickets(al_instance_id: int, indices: list[str], train_data_path: str = None):
    """
    Get tickets by their indices.

    Returns:
        Dictionary containing tickets
    """
    # check if the instance id is 0
    # if it is, check if the train_data_path is provided
    # if the instance id is not 0, check if it is valid
    if al_instance_id == 0:
        if train_data_path is None:
            raise HTTPException(status_code=400, detail="Train data path is required if no instance id is provided")

    elif al_instance_id not in data_service.storage.al_instances_dict:
        raise HTTPException(status_code=404, detail="Instance not found")

    return data_service.get_tickets(al_instance_id, indices, train_data_path)

@router.get("/{al_instance_id}/teams")
def get_teams(al_instance_id: int, train_data_path: str = None):
    """
    Get teams from the dataset.
    If al_instance_id is 0, the train_data_path is required.    

    Returns:
        Dictionary containing teams
    """
    # check if the instance id is 0
    # if it is, check if the train_data_path is provided
    # if the instance id is not 0, check if it is valid
    if al_instance_id == 0:
        if train_data_path is None:
            raise HTTPException(status_code=400, detail="Train data path is required if no instance id is provided")

    elif al_instance_id not in data_service.storage.al_instances_dict:
        raise HTTPException(status_code=404, detail="Instance not found")

    return data_service.get_teams(al_instance_id, train_data_path)

@router.get("/{al_instance_id}/categories")
def get_categories(al_instance_id: int, train_data_path: str = None):
    """
    Get categories from the dataset.
    
    Returns:
        Dictionary containing categories
    """
    # check if the instance id is 0
    # if it is, check if the train_data_path is provided
    # if the instance id is not 0, check if it is valid
    if al_instance_id == 0:
        if train_data_path is None:
            raise HTTPException(status_code=400, detail="Train data path is required if no instance id is provided")

    elif al_instance_id not in data_service.storage.al_instances_dict:
        raise HTTPException(status_code=404, detail="Instance not found")

    return data_service.get_categories(al_instance_id, train_data_path)

@router.get("/{al_instance_id}/subcategories")
def get_subcategories(al_instance_id: int, train_data_path: str = None):
    """
    Get subcategories from the dataset.
    
    Returns:
        Dictionary containing subcategories
    """
    # check if the instance id is 0
    # if it is, check if the train_data_path is provided
    # if the instance id is not 0, check if it is valid
    if al_instance_id == 0:
        if train_data_path is None:
            raise HTTPException(status_code=400, detail="Train data path is required if no instance id is provided")

    elif al_instance_id not in data_service.storage.al_instances_dict:
        raise HTTPException(status_code=404, detail="Instance not found")

    return data_service.get_subcategories(al_instance_id, train_data_path)
