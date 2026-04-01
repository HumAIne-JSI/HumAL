from fastapi import APIRouter, HTTPException
from app.core.dependencies import get_inference_service, get_duckdb_persistence_service
from app.data_models.active_learning_dm import InferenceRequest, InferenceResponse
from app.config.config import DEFAULT_MODEL_ID

router = APIRouter(prefix="/activelearning", tags=["inference"])
inference_service = get_inference_service()
duckdb_persistence_service = get_duckdb_persistence_service()

@router.post("/{al_instance_id}/infer", response_model= list[InferenceResponse])
def infer(al_instance_id: int, data: list[InferenceRequest], model_id : int = DEFAULT_MODEL_ID) -> list[InferenceResponse]:
    # check if the instance id is valid
    if al_instance_id not in inference_service.storage.al_instances_dict:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # check if the model is trained
    models = duckdb_persistence_service.load_models(al_instance_id)
    if not models:
        raise HTTPException(status_code=404, detail="Model not trained yet, please train the model first")
    return inference_service.infer(al_instance_id, data, model_id)