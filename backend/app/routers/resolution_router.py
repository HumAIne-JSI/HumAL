"""Router for ticket resolution endpoints"""
from fastapi import APIRouter, HTTPException
from app.core.dependencies import get_resolution_service
from app.data_models.resolution_dm import (
    ResolutionRequest, 
    ResolutionResponse,
    EmbeddingsRebuildResponse,
    FeedbackRequest,
    FeedbackResponse
)

router = APIRouter(prefix="/resolution", tags=["resolution"])

@router.post("/process", response_model=ResolutionResponse)
def process_ticket_resolution(request: ResolutionRequest):
    """
    Generate first-reply response for IT support ticket.
    Uses RAG + GPT to generate contextually appropriate responses.
    """
    try:
        resolution_service = get_resolution_service()
        return resolution_service.process_new_ticket(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/feedback", response_model=FeedbackResponse)
def save_ticket_feedback(request: FeedbackRequest):
    """
    Save resolved ticket for continuous improvement.
    Adds single embedding to FAISS index without full rebuild.
    """
    try:
        resolution_service = get_resolution_service()
        result = resolution_service.save_resolved_ticket_with_feedback(
            ticket_title=request.ticket_title,
            ticket_description=request.ticket_description,
            edited_response=request.edited_response,
            predicted_team=request.predicted_team,
            predicted_classification=request.predicted_classification,
            service_name=request.service_name,
            service_subcategory=request.service_subcategory
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return FeedbackResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/rebuild-embeddings", response_model=EmbeddingsRebuildResponse)
def force_rebuild_embeddings():
    """Force full rebuild of embeddings cache (slow, prefer /feedback)"""
    try:
        resolution_service = get_resolution_service()
        result = resolution_service.rebuild_embeddings()
        return EmbeddingsRebuildResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Uncomment if implementing health checks in the future
#@router.get("/health")
#def health_check():
#    """Check if resolution service is ready"""
#    resolution_service = get_resolution_service()
#    return {
#        "status": "healthy",
#        "rag_cached": resolution_service._rag_cache.get("rag") is not None,
#        "kb_size": len(resolution_service._rag_cache.get("df", [])) if resolution_service._rag_cache.get("df") is not None else 0
#    }