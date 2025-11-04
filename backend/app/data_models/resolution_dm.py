from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any

class ResolutionRequest(BaseModel):
    """Request model for ticket resolution"""
    ticket_title: Optional[str] = Field(None, description="Title of the ticket")
    ticket_description: Optional[str] = Field(None, description="Description of the ticket")
    service_category: Optional[str] = Field(None, description="Service category if available")
    service_subcategory: Optional[str] = Field(None, description="Service subcategory if available")
    top_k: int = Field(5, ge=1, le=20, description="Number of similar tickets to retrieve")
    force_rebuild: bool = Field(False, description="Force rebuild of embeddings cache")
    
    @model_validator(mode='after')
    def check_at_least_one_field(self):
        """Ensure at least title or description is provided"""
        if not self.ticket_title and not self.ticket_description:
            raise ValueError("At least one of 'ticket_title' or 'ticket_description' must be provided")
        return self


class ResolutionResponse(BaseModel):
    """Response model for ticket resolution"""
    classification: str = Field(..., description="Classified ticket type (e.g., vpn_request, onboarding)")
    predicted_team: str = Field(..., description="Team assigned to handle the ticket")
    team_confidence: float = Field(..., description="Confidence score for team prediction")
    response: str = Field(..., description="Generated first reply to the ticket")
    similar_replies: List[Dict[str, Any]] = Field(..., description="Similar historical tickets")
    retrieval_k: int = Field(..., description="Number of similar tickets retrieved")

class EmbeddingsRebuildResponse(BaseModel):
    """Response for embeddings rebuild operation"""
    rebuilt: bool
    records: int
    embedding_dim: Optional[int]
    cache_file: Optional[str]
    cache_saved: bool


class FeedbackRequest(BaseModel):
    """Request for saving user-approved ticket resolution"""
    ticket_title: str = Field(..., description="Original ticket title")
    ticket_description: str = Field(..., description="Original ticket description")
    edited_response: str = Field(..., description="User-approved/edited response")
    predicted_team: Optional[str] = Field(None, description="Team assignment")
    predicted_classification: Optional[str] = Field(None, description="Ticket type")
    service_name: Optional[str] = Field(None, description="Service category")
    service_subcategory: Optional[str] = Field(None, description="Service subcategory")

class FeedbackResponse(BaseModel):
    """Response after saving feedback"""
    success: bool
    message: str
    ticket_ref: Optional[str]
    new_kb_size: Optional[int]
    embedding_added_incrementally: bool
    embedding_invalidated: bool