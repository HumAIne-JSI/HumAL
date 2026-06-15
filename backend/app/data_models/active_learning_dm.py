from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, root_validator, validator

MostHelpfulFeature = Literal[
    "lime",
    "predicted_class_neighbors",
    "historical_neighbors",
    "model_prediction",
]

# Deprecated request fields remain accepted for backward compatibility but are unused.
class NewInstance(BaseModel):
    model_name: str
    qs_strategy: str
    class_list: list[int | str | None]
    train_data_path: str | None = None
    test_data_path: str | None = None

# Data model for the label request
class LabelRequest(BaseModel):
    query_idx: list[int | str]
    labels: list[str | int | None]


class LabelInfo(BaseModel):
    ticket_id: str
    label: str
    model_prediction: Optional[str] = None
    start_time: datetime
    end_time: datetime
    most_helpful_feature: Optional[MostHelpfulFeature] = None

    @validator("ticket_id", "label")
    def _ensure_non_empty_string(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must be a non-empty string")
        return value

    @root_validator(skip_on_failure=True)
    def _validate_time_order(cls, values):
        start_time = values.get("start_time")
        end_time = values.get("end_time")

        if start_time is not None and end_time is not None and end_time < start_time:
            raise ValueError("end_time must be greater than or equal to start_time")

        return values


class BenchmarkLabelEventRequest(BaseModel):
    ticket_id: str
    action: Literal["confirm_label", "override_label"]
    new_label: str
    duration_s: float
    original_prediction: Optional[str] = None
    user_id: Optional[str] = None

# Data model for the inference instance input
class Data(BaseModel):
    service_subcategory_name: Optional[str] = None
    team_name: Optional[str] = None
    service_name: Optional[str] = None
    last_team_id_name: Optional[str] = None
    title_anon: Optional[str] = None
    description_anon: Optional[str] = None
    public_log_anon: Optional[str] = None

# Response model for probability inference
class InferProbaResponse(BaseModel):
    classes: list[str | int | None]
    probabilities: list[list[float]]

# Data model for the nearest neighbor ticket
class Neighbor(BaseModel):
    ref: str
    label: Optional[str] = None
    similarity: float
    title: Optional[str] = None
    description: Optional[str] = None
    best_sentence: Optional[str] = None
    best_sentence_score: Optional[float] = None
    sentence_score_components: Optional[dict[str, float]] = None
    xai_result: Optional[Any] = None
    similar_tickets: Optional[Any] = None
    model_prediction: Optional[str] = None
    most_helpful_feature: Optional[MostHelpfulFeature] = None

# Response model for nearest neighbor query
class NearestTicketResponse(BaseModel):
    query_idx: Optional[str] = None
    predicted_class_neighbors: list[Neighbor] = Field(default_factory=list)
    historical_neighbors: list[Neighbor] = Field(default_factory=list)


class UserRegisterRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: str
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DelegateRequest(BaseModel):
    """Request body for delegating an instance to another user."""
    username: str


class DelegateResponse(BaseModel):
    """Response for a single delegate."""
    username: str
    delegate_user_id: str
    granted_by: str
    granted_at: datetime


class DelegateListResponse(BaseModel):
    """Response for listing all delegates of an instance."""
    delegates: list[DelegateResponse]
