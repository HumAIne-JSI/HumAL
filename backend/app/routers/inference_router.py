import time

from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.dependencies import get_inference_service, get_duckdb_persistence_service, get_current_user, require_instance_access
from app.data_models.active_learning_dm import Data, InferProbaResponse
from app.config.config import SYSTEM_USER_ID

router = APIRouter(prefix="/activelearning", tags=["inference"])
inference_service = get_inference_service()
duckdb_service = get_duckdb_persistence_service()


@router.post("/{al_instance_id}/infer")
def infer(al_instance_id: int, data: Data | list[Data], ref: str | None = Query(None), current_user: dict = Depends(get_current_user)):
    request_start = time.perf_counter()
    require_instance_access(al_instance_id, current_user, inference_service.storage)
    
    # check if the model is trained
    if al_instance_id not in inference_service.storage.model_paths_dict:
        raise HTTPException(status_code=404, detail="Model not trained yet, please train the model first")

    if duckdb_service is not None:
        duckdb_service.log_event(
            al_instance_id=al_instance_id,
            user_id=current_user["user_id"],
            action="request_prediction",
            latency_ms=int((time.perf_counter() - request_start) * 1000),
            actor_type="system",
            agent="orchestrator",
            object_id=ref,
            payload={
                "request_size": len(data) if isinstance(data, list) else 1,
                **({"ref": ref} if ref is not None else {}),
            },
        )
    return inference_service.infer(al_instance_id, data, user_id=current_user["user_id"], ref=ref)

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
    require_instance_access(al_instance_id, current_user, inference_service.storage)

    # check if the model is trained
    if al_instance_id not in inference_service.storage.model_paths_dict:
        raise HTTPException(status_code=404, detail="Model not trained yet, please train the model first")

    if duckdb_service is not None:
        duckdb_service.log_event(
            al_instance_id=al_instance_id,
            user_id=current_user["user_id"],
            action="request_prediction",
            latency_ms=int((time.perf_counter() - request_start) * 1000),
            actor_type="system",
            agent="orchestrator",
            object_id=ref,
            payload={
                "request_size": len(data) if isinstance(data, list) else 1,
                **({"ref": ref} if ref is not None else {}),
            },
        )

    try:
        return inference_service.infer_proba(al_instance_id, data, user_id=current_user["user_id"], ref=ref)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc