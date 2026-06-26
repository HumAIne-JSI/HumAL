from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse

from pydantic import ValidationError

from app.core import dependencies
from app.core.dependencies import get_al_service, get_current_user, require_instance_access
from app.data_models.active_learning_dm import (
    DelegateRequest,
    LabelInfo,
    LabelRequest,
    NewInstance,
)

router = APIRouter(prefix="/activelearning", tags=["active_learning"])
al_service = get_al_service()


@router.post("/new")
def activelearning_init(new_instance: NewInstance, current_user: dict = Depends(get_current_user)):
    try:
        instance_id = al_service.create_instance(new_instance, user_id=current_user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"instance_id": instance_id}

@router.get("/{al_instance_id}/next")
def next_instance(al_instance_id: int, batch_size: int = 1, current_user: dict = Depends(get_current_user)):
    require_instance_access(al_instance_id, current_user, al_service.storage)
    
    # Get the next instances
    next_instances = al_service.get_next_instances(al_instance_id, batch_size, user_id=current_user["user_id"])
    return {"query_idx": next_instances}

@router.put("/{al_instance_id}/label")
def label_instance(al_instance_id: int, label_request: LabelRequest, current_user: dict = Depends(get_current_user)):
    require_instance_access(al_instance_id, current_user, al_service.storage)
    try:
        al_service.label_instance(al_instance_id, label_request, user_id=current_user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    al_service.update_model(al_instance_id, user_id=current_user["user_id"])
    al_service.calculate_metrics(al_instance_id, user_id=current_user["user_id"])
    return {"message": "Labels updated"}


def _coerce_label_info_items(label_info):
    if isinstance(label_info, dict) and "label_info" in label_info:
        label_info = label_info["label_info"]

    if not isinstance(label_info, list):
        raise HTTPException(status_code=400, detail="label_info must be a list of objects")

    coerced_items = []
    for item in label_info:
        try:
            coerced_items.append(item if isinstance(item, LabelInfo) else LabelInfo(**item))
        except (TypeError, ValidationError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return coerced_items


@router.post("/{al_instance_id}/label-with-info")
def label_with_info(al_instance_id: int, label_info: list[LabelInfo] = Body(...), current_user: dict = Depends(get_current_user)):
    require_instance_access(al_instance_id, current_user, al_service.storage)

    try:
        coerced_items = _coerce_label_info_items(label_info)
        result = al_service.label_with_info(al_instance_id, coerced_items, user_id=current_user["user_id"], username=current_user["username"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    al_service.update_model(al_instance_id, user_id=current_user["user_id"])
    al_service.calculate_metrics(al_instance_id, user_id=current_user["user_id"])
    return result

@router.get("/{al_instance_id}/info")
def get_info(al_instance_id: int, current_user: dict = Depends(get_current_user)):
    require_instance_access(al_instance_id, current_user, al_service.storage)
    return al_service.get_instance_info(al_instance_id)

@router.post("/{al_instance_id}/save")
def save_model(al_instance_id: int, current_user: dict = Depends(get_current_user)):
    require_instance_access(al_instance_id, current_user, al_service.storage)

    model_id = al_service.save_model(al_instance_id, user_id=current_user["user_id"])
    return {"model_id": model_id}

@router.get("/instances")
def get_instances(current_user: dict = Depends(get_current_user)):
    """Get all AL instances owned by or delegated to the current user."""
    user_id = current_user["user_id"]
    
    owned_instances = {
        k: v for k, v in al_service.storage.al_instances_dict.items()
        if v.get("user_id") == user_id
    }
    
    delegated_ids = dependencies.duckdb_persistence_service.get_delegated_instance_ids(
        user_id=user_id
    )
    delegated_instances = {
        k: v for k, v in al_service.storage.al_instances_dict.items()
        if k in delegated_ids
    }
    
    all_instances = {**owned_instances, **delegated_instances}
    return {"instances": all_instances}

@router.delete("/{al_instance_id}")
def delete_instance(al_instance_id: int, current_user: dict = Depends(get_current_user)):
    require_instance_access(al_instance_id, current_user, al_service.storage)
    
    al_service.delete_instance(al_instance_id)
    return {"message": "Instance deleted"}

@router.post("/{al_instance_id}/delegate")
def delegate_instance(
    al_instance_id: int,
    request: DelegateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Delegate an AL instance to another user. Only the instance owner can delegate."""
    try:
        delegate_info = al_service.delegate_instance(
            al_instance_id=al_instance_id,
            delegate_username=request.username,
            owner_user_id=current_user["user_id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return delegate_info


@router.delete("/{al_instance_id}/delegate/{username}")
def revoke_delegation(
    al_instance_id: int,
    username: str,
    current_user: dict = Depends(get_current_user),
):
    """Revoke a user's delegated access. Only the instance owner can revoke."""
    try:
        al_service.revoke_delegation(
            al_instance_id=al_instance_id,
            delegate_username=username,
            owner_user_id=current_user["user_id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": f"Delegation revoked for user '{username}'"}


@router.get("/{al_instance_id}/delegates")
def list_delegates(
    al_instance_id: int,
    current_user: dict = Depends(get_current_user),
):
    """List all users delegated access to an instance. Only the owner can view."""
    try:
        delegates = al_service.get_delegates(
            al_instance_id=al_instance_id,
            owner_user_id=current_user["user_id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"delegates": delegates}


@router.get("/{al_instance_id}/export")
def export_instance(al_instance_id: int, current_user: dict = Depends(get_current_user)):
    """Export all DuckDB data for an AL instance as a downloadable ZIP of JSON files.

    Returns an ``application/zip`` download named ``export_al_<id>_<timestamp>.zip``
    containing a ``manifest.json`` and one ``duckdb/<table>.json`` per table.
    """
    require_instance_access(al_instance_id, current_user, al_service.storage)
    try:
        buffer, filename = al_service.export_instance(al_instance_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )