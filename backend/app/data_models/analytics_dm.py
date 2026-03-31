from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class ActorType(str, Enum):
    SYSTEM = "system"
    AI = "ai"
    HUMAN = "human"


class Decision(BaseModel):
    """Single decision/event in an active learning session."""
    t: float = Field(..., description="Timestamp in seconds from session start")
    actor_type: ActorType
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    interaction_id: Optional[str] = None
    latency_ms: Optional[float] = None
    duration_s: Optional[float] = None


class SessionMeta(BaseModel):
    """Metadata for an active learning session."""
    task_parameters: dict[str, Any] = Field(default_factory=dict)


class SessionLog(BaseModel):
    """Complete decision log for an active learning session."""
    sim_id: str
    session_id: str
    pilot_tag: Optional[str] = None
    user_id: Optional[str] = None
    app_version: Optional[str] = None
    ai_model_version: Optional[str] = None
    meta: SessionMeta = Field(default_factory=SessionMeta)
    decisions: list[Decision] = Field(default_factory=list)


class SessionSummary(BaseModel):
    """Aggregated summary statistics for a session."""
    session_id: str
    instance_id: int
    model_name: str
    qs_strategy: str
    
    # Labeling metrics
    total_labeled: int = 0
    labeling_iterations: int = 0
    avg_labeling_duration_s: Optional[float] = None
    
    # Model performance
    latest_f1: Optional[float] = None
    f1_improvement: Optional[float] = None  # From first to last iteration
    latest_accuracy: Optional[float] = None
    
    # AL effectiveness
    latest_mean_entropy: Optional[float] = None
    entropy_reduction: Optional[float] = None  # From first to last
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


class LabelingMetrics(BaseModel):
    """Detailed labeling efficiency metrics."""
    total_labels: int
    labels_per_iteration: list[int]
    avg_duration_per_label_s: Optional[float] = None
    min_duration_s: Optional[float] = None
    max_duration_s: Optional[float] = None
    throughput_per_hour: Optional[float] = None


class ModelPerformanceMetrics(BaseModel):
    """Model performance trend metrics."""
    f1_scores: list[float]
    mean_entropies: list[float]
    num_labeled: list[int]
    f1_trend: Optional[str] = None  # "improving", "stable", "declining"
    convergence_iteration: Optional[int] = None


class ALEffectivenessMetrics(BaseModel):
    """Active learning strategy effectiveness metrics."""
    strategy: str
    uncertainty_reduction_rate: Optional[float] = None
    samples_to_target_f1: Optional[int] = None
    efficiency_score: Optional[float] = None  # Normalized metric


class ClassDistributionMetrics(BaseModel):
    """Class distribution and balance metrics."""
    class_counts: dict[str, int]
    class_percentages: dict[str, float]
    imbalance_ratio: Optional[float] = None
    majority_class: Optional[str] = None
    minority_class: Optional[str] = None


class AnalyticsOverview(BaseModel):
    """Aggregated analytics across all sessions."""
    total_sessions: int
    total_instances: int
    total_labels: int
    total_iterations: int
    
    # Averages across sessions
    avg_f1_score: Optional[float] = None
    avg_labels_per_session: Optional[float] = None
    avg_labeling_duration_s: Optional[float] = None
    
    # Best performers
    best_f1_instance_id: Optional[int] = None
    best_f1_score: Optional[float] = None
    most_efficient_strategy: Optional[str] = None
    
    # Strategy breakdown
    strategy_performance: dict[str, float] = Field(default_factory=dict)


class SessionComparison(BaseModel):
    """Side-by-side comparison of multiple sessions."""
    session_ids: list[str]
    instance_ids: list[int]
    
    # Comparative metrics
    f1_scores: dict[int, list[float]]
    num_labeled: dict[int, list[int]]
    strategies: dict[int, str]
    
    # Rankings
    f1_ranking: list[int]  # Instance IDs ordered by final F1
    efficiency_ranking: list[int]  # Instance IDs ordered by labels-to-F1 ratio


class ExportRequest(BaseModel):
    """Request model for exporting session data."""
    instance_ids: list[int] = Field(default_factory=list)
    include_decisions: bool = True
    include_metrics: bool = True
    format: str = "json"  # "json" or "csv"
