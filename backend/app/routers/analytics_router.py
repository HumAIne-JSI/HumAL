from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.core.dependencies import get_analytics_service
from app.data_models.analytics_dm import (
    SessionLog, SessionSummary, AnalyticsOverview,
    LabelingMetrics, ModelPerformanceMetrics, ALEffectivenessMetrics,
    ClassDistributionMetrics, SessionComparison, ExportRequest
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
analytics_service = get_analytics_service()


@router.get("/overview", response_model=AnalyticsOverview)
def get_overview():
    """Get aggregated analytics across all sessions."""
    return analytics_service.get_overview()


@router.get("/sessions")
def list_sessions():
    """List all sessions with summary statistics."""
    summaries = []
    for instance_id in analytics_service.storage.al_instances_dict.keys():
        summary = analytics_service.get_session_summary(instance_id)
        if summary:
            summaries.append(summary)
    return {"sessions": summaries}


@router.get("/sessions/{instance_id}", response_model=SessionSummary)
def get_session_summary(instance_id: int):
    """Get summary statistics for a specific session."""
    summary = analytics_service.get_session_summary(instance_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    return summary


@router.get("/sessions/{instance_id}/decisions", response_model=SessionLog)
def get_session_decisions(instance_id: int):
    """Get the full decision log for a session."""
    log = analytics_service.get_session_log(instance_id)
    if not log:
        raise HTTPException(status_code=404, detail="Session not found")
    return log


@router.get("/sessions/{instance_id}/labeling", response_model=LabelingMetrics)
def get_labeling_metrics(instance_id: int):
    """Get detailed labeling efficiency metrics for a session."""
    metrics = analytics_service.get_labeling_metrics(instance_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Session not found or no labeling data")
    return metrics


@router.get("/sessions/{instance_id}/performance", response_model=ModelPerformanceMetrics)
def get_model_performance(instance_id: int):
    """Get model performance trend metrics for a session."""
    metrics = analytics_service.get_model_performance(instance_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Session not found or no performance data")
    return metrics


@router.get("/sessions/{instance_id}/effectiveness", response_model=ALEffectivenessMetrics)
def get_al_effectiveness(instance_id: int):
    """Get active learning strategy effectiveness metrics."""
    metrics = analytics_service.get_al_effectiveness(instance_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Session not found")
    return metrics


@router.get("/sessions/{instance_id}/distribution", response_model=ClassDistributionMetrics)
def get_class_distribution(instance_id: int):
    """Get class distribution metrics for labeled data."""
    metrics = analytics_service.get_class_distribution(instance_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Session not found or no labeled data")
    return metrics


@router.get("/sessions/{instance_id}/export")
def export_session(instance_id: int):
    """Export session data in standard JSON format."""
    data = analytics_service.export_session(instance_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data


@router.post("/compare", response_model=SessionComparison)
def compare_sessions(instance_ids: list[int] = Query(..., description="Instance IDs to compare")):
    """Compare multiple sessions side by side."""
    if len(instance_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 instance IDs required for comparison")
    
    # Validate all instance IDs exist
    valid_ids = [
        i for i in instance_ids 
        if i in analytics_service.storage.al_instances_dict
    ]
    
    if len(valid_ids) < 2:
        raise HTTPException(status_code=404, detail="Not enough valid sessions found")
    
    return analytics_service.compare_sessions(valid_ids)


@router.post("/export-bulk")
def export_bulk(request: ExportRequest):
    """Export multiple sessions in bulk."""
    results = []
    
    instance_ids = request.instance_ids
    if not instance_ids:
        # Export all if no IDs specified
        instance_ids = list(analytics_service.storage.al_instances_dict.keys())
    
    for instance_id in instance_ids:
        session_data = {}
        
        if request.include_decisions:
            log = analytics_service.get_session_log(instance_id)
            if log:
                session_data["decisions"] = log.model_dump()
        
        if request.include_metrics:
            summary = analytics_service.get_session_summary(instance_id)
            if summary:
                session_data["summary"] = summary.model_dump()
            
            performance = analytics_service.get_model_performance(instance_id)
            if performance:
                session_data["performance"] = performance.model_dump()
            
            labeling = analytics_service.get_labeling_metrics(instance_id)
            if labeling:
                session_data["labeling"] = labeling.model_dump()
        
        if session_data:
            session_data["instance_id"] = instance_id
            results.append(session_data)
    
    return {"exports": results, "count": len(results)}
