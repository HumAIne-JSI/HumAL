from fastapi import APIRouter, HTTPException, Query, Body
from app.core.dependencies import get_xai_service, get_data_service
from app.data_models.active_learning_dm import Data
import pandas as pd
from typing import Optional

router = APIRouter(prefix="/xai", tags=["xai"])
xai_service = get_xai_service()
data_service = get_data_service()

@router.post("/{al_instance_id}/explain_lime")
def explain_lime(
    al_instance_id: int, 
    ticket_data: Optional[Data] = Body(None), 
    query_idx: Optional[list[str]] = Query(None), 
    model_id: int = Query(0)
    ):
    # check if the instance id is valid
    if al_instance_id not in xai_service.storage.al_instances_dict:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # check if the model is trained
    if al_instance_id not in xai_service.storage.model_paths_dict:
        raise HTTPException(status_code=404, detail="Model not trained yet, please train the model first")

    tickets = []

    # require exactly one source
    if (ticket_data is None) == (query_idx is None):
        raise HTTPException(status_code=400, detail="Provide exactly one of ticket_data or query_idx")

    if ticket_data is not None:
        tickets.append(ticket_data)
    else:
        for idx in query_idx:
            ticket = data_service.get_tickets(al_instance_id, [idx])['tickets'][0]
            ticket_data_obj = Data(
                title_anon = ticket['Title_anon'],
                description_anon = ticket['Description_anon'],
                service_name = ticket['Service->Name'],
                service_subcategory_name = ticket['Service subcategory->Name']
            )
            tickets.append(ticket_data_obj)
   
    # explain the ticket_data
    return xai_service.explain_lime(al_instance_id, tickets, model_id)

@router.post("/{al_instance_id}/nearest_ticket")
def find_nearest_ticket(
    al_instance_id: int, 
    ticket_data: Optional[Data] = Body(None), 
    query_idx: Optional[list[str]] = Query(None), 
    model_id: int = Query(0)
    ):
    # check if the instance id is valid
    if al_instance_id not in xai_service.storage.al_instances_dict:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # check if the model is trained
    if al_instance_id not in xai_service.storage.model_paths_dict:
        raise HTTPException(status_code=404, detail="Model not trained yet, please train the model first")
    
    
    # require exactly one source
    if (ticket_data is None) == (query_idx is None):
        raise HTTPException(status_code=400, detail="Provide exactly one of ticket_data or query_idx")
    
    if ticket_data is not None:
        return xai_service.find_nearest_by_ticket(al_instance_id, ticket_data, model_id)
    else:
        return xai_service.find_nearest_by_query_idx(al_instance_id, query_idx, model_id)
    