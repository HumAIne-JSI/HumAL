import time
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from app.core.dependencies import (
    get_inference_service,
    get_duckdb_persistence_service,
    get_data_service,
    get_current_user,
    require_instance_access,
)
from app.data_models.active_learning_dm import Data, InferProbaResponse
from app.config.config import SYSTEM_USER_ID

router = APIRouter(prefix="/activelearning", tags=["inference"])
inference_service = get_inference_service()
duckdb_service = get_duckdb_persistence_service()
data_service = get_data_service()


def _resolve_tickets_by_refs(al_instance_id: int, query_idx: list[str]) -> list[Data]:
    """Resolve ticket refs into Data objects via the data service.

    Raises HTTPException(404) if any ref is missing.
    """
    tickets: list[Data] = []
    for idx in query_idx:
        ticket_response = data_service.get_tickets([idx])
        if ticket_response is None or not ticket_response.get("tickets"):
            raise HTTPException(status_code=404, detail=f"Ticket {idx} not found")
        ticket = ticket_response["tickets"][0]
        tickets.append(Data(
            title_anon=ticket["Title_anon"],
            description_anon=ticket["Description_anon"],
            service_name=ticket["Service->Name"],
            service_subcategory_name=ticket["Service subcategory->Name"],
        ))
    return tickets


@router.post("/{al_instance_id}/infer")
def infer(
    al_instance_id: int,
    data: Data | list[Data] = Body(None),
    query_idx: Optional[list[str]] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    request_start = time.perf_counter()
    require_instance_access(al_instance_id, current_user, inference_service.storage)

    if al_instance_id not in inference_service.storage.model_paths_dict:
        raise HTTPException(status_code=404, detail="Model not trained yet, please train the model first")

    if (data is None) == (query_idx is None):
        raise HTTPException(status_code=400, detail="Provide exactly one of data or query_idx")

    if query_idx is not None:
        refs = list(query_idx)
        if duckdb_service is not None:
            duckdb_service.log_event(
                al_instance_id=al_instance_id,
                user_id=current_user["user_id"],
                action="request_prediction",
                latency_ms=int((time.perf_counter() - request_start) * 1000),
                actor_type="system",
                agent="orchestrator",
                object_id=None,
                payload={
                    "request_size": len(refs),
                    "ticket_ids": refs,
                },
            )
        resolved = _resolve_tickets_by_refs(al_instance_id, refs)
        return inference_service.infer(al_instance_id, resolved, user_id=current_user["user_id"], refs=refs)

    return inference_service.infer(al_instance_id, data, user_id=current_user["user_id"])


@router.post("/{al_instance_id}/infer_proba", response_model=InferProbaResponse)
def infer_proba(
    al_instance_id: int,
    data: Data | list[Data] = Body(None),
    query_idx: Optional[list[str]] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Return class probabilities for inference requests.

    Args:
        al_instance_id: Active learning instance id.
        data: Ad-hoc input data instance(s). Not logged.
        query_idx: Ticket references to resolve and predict + log per ticket.

    Returns:
        InferProbaResponse: Classes list and probability matrix.

    Raises:
        HTTPException: When the instance/model is missing, model lacks predict_proba,
            or both/neither of data and query_idx are provided.
    """
    request_start = time.perf_counter()
    require_instance_access(al_instance_id, current_user, inference_service.storage)

    if al_instance_id not in inference_service.storage.model_paths_dict:
        raise HTTPException(status_code=404, detail="Model not trained yet, please train the model first")

    if (data is None) == (query_idx is None):
        raise HTTPException(status_code=400, detail="Provide exactly one of data or query_idx")

    try:
        if query_idx is not None:
            refs = list(query_idx)
            if duckdb_service is not None:
                duckdb_service.log_event(
                    al_instance_id=al_instance_id,
                    user_id=current_user["user_id"],
                    action="request_prediction",
                    latency_ms=int((time.perf_counter() - request_start) * 1000),
                    actor_type="system",
                    agent="orchestrator",
                    object_id=None,
                    payload={
                        "request_size": len(refs),
                        "ticket_ids": refs,
                    },
                )
            resolved = _resolve_tickets_by_refs(al_instance_id, refs)
            return inference_service.infer_proba(al_instance_id, resolved, user_id=current_user["user_id"], refs=refs)
        return inference_service.infer_proba(al_instance_id, data, user_id=current_user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc