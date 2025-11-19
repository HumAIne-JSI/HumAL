from fastapi import APIRouter, HTTPException
from app.core.dependencies import get_inference_service
from app.data_models.active_learning_dm import Data

router = APIRouter(prefix="/activelearning", tags=["inference"])
inference_service = get_inference_service()

@router.post("/{al_instance_id}/infer")
def infer(al_instance_id: int, data: Data):
    # check if the instance id is valid
    if al_instance_id not in inference_service.storage.al_instances_dict:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # check if the model is trained
    if al_instance_id not in inference_service.storage.model_paths_dict:
        raise HTTPException(status_code=404, detail="Model not trained yet, please train the model first")
    return inference_service.infer(al_instance_id, data)