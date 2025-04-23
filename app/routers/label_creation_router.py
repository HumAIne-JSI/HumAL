from fastapi import APIRouter
from app.services.data_preprocessing import resolution_label_creation

router = APIRouter(prefix="/activelearning")

@router.post("/resolution_label_creation")
def create_resolution_labels(data_path: str, output_data_path: str, labels: bool = False, test_set: bool = False):
    return {"data_path": resolution_label_creation(data_path, output_data_path, labels, test_set)}
