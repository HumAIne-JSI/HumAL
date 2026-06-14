import time

from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.dependencies import get_inference_service, get_duckdb_persistence_service, get_current_user
from app.data_models.active_learning_dm import Data, InferProbaResponse
from app.config.config import SYSTEM_USER_ID

router = APIRouter(prefix="/activelearning", tags=["inference"])
inference_service = get_inference_service()
duckdb_service = get_duckdb_persistence_service()


def _require_instance_owner(al_instance_id: int, current_user: dict):
    instance = inference_service.storage.al_instances_dict.get(al_instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    if instance.get("user_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this instance")


@router.post("/{al_instance_id}/infer")
def infer(al_instance_id: int, data: Data | list[Data], ref: str | None = Query(None), current_user: dict = Depends(get_current_user)):
    request_start = time.perf_counter()
    _require_instance_owner(al_instance_id, current_user)
    
    # check if the model is trained
    if al_instance_id not in inference_service.storage.model_paths_dict:
        raise HTTPException(status_code=404, detail="Model not trained yet, please train the model first")

    if duckdb_service is not None:
        duckdb_service.log_event(
            al_instance_id=al_instance_id,
            user_id=current_user["user_id"],
            action="request_prediction",
            latency_ms=int((time.perf_counter() - request_start) * 1000),
            payload={
                "request_size": len(data) if isinstance(data, list) else 1,
                **({"ref": ref} if ref is not None else {}),
            },
        )
    return inference_service.infer(al_instance_id, data, user_id=current_user["user_id"])

@router.post("/{al_instance_id}/infer_proba", response_model=InferProbaResponse)
def infer_proba(al_instance_id: int, data: Data | list[Data], ref: str | None = Query(None), current_user: dict = Depends(get_current_user)):
    """Return class probabilities for inference requests.

    Args:
        al_instance_id: Active learning instance id.
        data: Input data instance(s).

    Returns:
        InferProbaResponse: Classes list and probability matrix.

    Raises:
        HTTPException: When the instance or model is missing, or model lacks predict_proba.
    """
    request_start = time.perf_counter()
    _require_instance_owner(al_instance_id, current_user)

    # check if the model is trained
    if al_instance_id not in inference_service.storage.model_paths_dict:
        raise HTTPException(status_code=404, detail="Model not trained yet, please train the model first")

    if duckdb_service is not None:
        duckdb_service.log_event(
            al_instance_id=al_instance_id,
            user_id=current_user["user_id"],
            action="request_prediction",
            latency_ms=int((time.perf_counter() - request_start) * 1000),
            payload={
                "request_size": len(data) if isinstance(data, list) else 1,
                **({"ref": ref} if ref is not None else {}),
            },
        )

    try:
        return inference_service.infer_proba(al_instance_id, data, user_id=current_user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc