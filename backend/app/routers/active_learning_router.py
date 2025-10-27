from fastapi import APIRouter, HTTPException
from app.core.dependencies import get_al_service
from app.data_models.active_learning_dm import NewInstance, LabelRequest

router = APIRouter(prefix="/activelearning", tags=["active_learning"])
al_service = get_al_service()


@router.post("/new")
def activelearning_init(new_instance: NewInstance):
    instance_id = al_service.create_instance(new_instance)
    return {"instance_id": instance_id}

@router.get("/{al_instance_id}/next")
def next_instance(al_instance_id: int, batch_size: int = 1):                                                                                                                                                                                                                                                                                                                                                                                                                                      
    # check if the instance id is valid
    if al_instance_id not in al_service.storage.al_instances_dict:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Get the next instances
    next_instances = al_service.get_next_instances(al_instance_id, batch_size)
    return {"query_idx": next_instances}

@router.put("/{al_instance_id}/label")
def label_instance(al_instance_id: int, label_request: LabelRequest):
    al_service.label_instance(al_instance_id, label_request)
    al_service.update_model(al_instance_id)
    al_service.calculate_metrics(al_instance_id)
    return {"message": "Labels updated"}

@router.get("/{al_instance_id}/info")
def get_info(al_instance_id: int):
    if al_instance_id not in al_service.storage.results_dict:
        raise HTTPException(status_code=404, detail="Instance not found")
    return al_service.storage.results_dict[al_instance_id]

@router.post("/{al_instance_id}/save")
def save_model(al_instance_id: int):
    if al_instance_id not in al_service.storage.results_dict:
        raise HTTPException(status_code=404, detail="Instance not found")

    model_id = al_service.save_model(al_instance_id)
    return {"model_id": model_id}

@router.get("/instances")
def get_instances():
    return {"instances": al_service.storage.al_instances_dict}

@router.delete("/{al_instance_id}")
def delete_instance(al_instance_id: int):
    if al_instance_id not in al_service.storage.al_instances_dict:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    al_service.delete_instance(al_instance_id)
    return {"message": "Instance deleted"}
