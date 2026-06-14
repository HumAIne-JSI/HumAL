from fastapi import APIRouter, Body, Depends, HTTPException

from pydantic import ValidationError

from app.core.dependencies import get_al_service, get_current_user
from app.data_models.active_learning_dm import LabelInfo, LabelRequest, NewInstance

router = APIRouter(prefix="/activelearning", tags=["active_learning"])
al_service = get_al_service()


def _require_instance_owner(al_instance_id: int, current_user: dict):
    instance = al_service.storage.al_instances_dict.get(al_instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    if instance.get("user_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this instance")


@router.post("/new")
def activelearning_init(new_instance: NewInstance, current_user: dict = Depends(get_current_user)):
    try:
        instance_id = al_service.create_instance(new_instance, user_id=current_user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"instance_id": instance_id}

@router.get("/{al_instance_id}/next")
def next_instance(al_instance_id: int, batch_size: int = 1, current_user: dict = Depends(get_current_user)):
    _require_instance_owner(al_instance_id, current_user)
    
    # Get the next instances
    next_instances = al_service.get_next_instances(al_instance_id, batch_size, user_id=current_user["user_id"])
    return {"query_idx": next_instances}

@router.put("/{al_instance_id}/label")
def label_instance(al_instance_id: int, label_request: LabelRequest, current_user: dict = Depends(get_current_user)):
    _require_instance_owner(al_instance_id, current_user)
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
    _require_instance_owner(al_instance_id, current_user)

    try:
        coerced_items = _coerce_label_info_items(label_info)
        result = al_service.label_with_info(al_instance_id, coerced_items, user_id=current_user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    al_service.update_model(al_instance_id, user_id=current_user["user_id"])
    al_service.calculate_metrics(al_instance_id, user_id=current_user["user_id"])
    return result

@router.get("/{al_instance_id}/info")
def get_info(al_instance_id: int, current_user: dict = Depends(get_current_user)):
    _require_instance_owner(al_instance_id, current_user)
    return al_service.get_instance_info(al_instance_id)

@router.post("/{al_instance_id}/save")
def save_model(al_instance_id: int, current_user: dict = Depends(get_current_user)):
    _require_instance_owner(al_instance_id, current_user)

    model_id = al_service.save_model(al_instance_id, user_id=current_user["user_id"])
    return {"model_id": model_id}

@router.get("/instances")
def get_instances(current_user: dict = Depends(get_current_user)):
    instances = {
        k: v for k, v in al_service.storage.al_instances_dict.items()
        if v.get("user_id") == current_user["user_id"]
    }
    return {"instances": instances}

@router.delete("/{al_instance_id}")
def delete_instance(al_instance_id: int, current_user: dict = Depends(get_current_user)):
    _require_instance_owner(al_instance_id, current_user)
    
    al_service.delete_instance(al_instance_id)
    return {"message": "Instance deleted"}