"""
HumAL API Client for fetching analytics data.
"""

import os
from typing import Optional
import httpx

from humal_analytics.models import (
    SessionLog,
    SessionSummary,
    AnalyticsOverview,
    LabelingMetrics,
    ModelPerformanceMetrics,
    ALEffectivenessMetrics,
    ClassDistributionMetrics,
    SessionComparison,
    LegacyLogsFile,
)


class HumALClient:
    """Client for interacting with HumAL Analytics API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the HumAL API client.
        
        Args:
            base_url: HumAL backend URL. Defaults to HUMAL_API_URL env var or localhost:8000
            timeout: Request timeout in seconds
        """
        self.base_url = (
            base_url or 
            os.getenv("HUMAL_API_URL", "http://localhost:8000")
        ).rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
    
    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make a GET request to the API."""
        url = f"{self.base_url}{endpoint}"
        response = self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def _post(self, endpoint: str, data: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        """Make a POST request to the API."""
        url = f"{self.base_url}{endpoint}"
        response = self._client.post(url, json=data, params=params)
        response.raise_for_status()
        return response.json()
    
    def check_connection(self) -> bool:
        """Check if the backend is reachable."""
        try:
            self._get("/config/availability")
            return True
        except Exception:
            return False
    
    # ==================== Analytics Endpoints ====================
    
    def get_overview(self) -> AnalyticsOverview:
        """Get aggregated analytics across all sessions."""
        data = self._get("/analytics/overview")
        return AnalyticsOverview(**data)
    
    def list_sessions(self) -> list[SessionSummary]:
        """List all sessions with summary statistics."""
        data = self._get("/analytics/sessions")
        return [SessionSummary(**s) for s in data.get("sessions", [])]
    
    def get_session_summary(self, instance_id: int) -> SessionSummary:
        """Get summary statistics for a specific session."""
        data = self._get(f"/analytics/sessions/{instance_id}")
        return SessionSummary(**data)
    
    def get_session_decisions(self, instance_id: int) -> SessionLog:
        """Get the full decision log for a session."""
        data = self._get(f"/analytics/sessions/{instance_id}/decisions")
        return SessionLog(**data)
    
    def get_labeling_metrics(self, instance_id: int) -> LabelingMetrics:
        """Get detailed labeling efficiency metrics."""
        data = self._get(f"/analytics/sessions/{instance_id}/labeling")
        return LabelingMetrics(**data)
    
    def get_model_performance(self, instance_id: int) -> ModelPerformanceMetrics:
        """Get model performance trend metrics."""
        data = self._get(f"/analytics/sessions/{instance_id}/performance")
        return ModelPerformanceMetrics(**data)
    
    def get_al_effectiveness(self, instance_id: int) -> ALEffectivenessMetrics:
        """Get AL strategy effectiveness metrics."""
        data = self._get(f"/analytics/sessions/{instance_id}/effectiveness")
        return ALEffectivenessMetrics(**data)
    
    def get_class_distribution(self, instance_id: int) -> ClassDistributionMetrics:
        """Get class distribution metrics."""
        data = self._get(f"/analytics/sessions/{instance_id}/distribution")
        return ClassDistributionMetrics(**data)
    
    def export_session(self, instance_id: int) -> dict:
        """Export session data in standard JSON format."""
        return self._get(f"/analytics/sessions/{instance_id}/export")
    
    def compare_sessions(self, instance_ids: list[int]) -> SessionComparison:
        """Compare multiple sessions side by side."""
        params = {"instance_ids": instance_ids}
        data = self._post("/analytics/compare", params=params)
        return SessionComparison(**data)
    
    def export_bulk(
        self,
        instance_ids: Optional[list[int]] = None,
        include_decisions: bool = True,
        include_metrics: bool = True
    ) -> dict:
        """Export multiple sessions in bulk."""
        data = {
            "instance_ids": instance_ids or [],
            "include_decisions": include_decisions,
            "include_metrics": include_metrics
        }
        return self._post("/analytics/export-bulk", data=data)
    
    # ==================== Active Learning Endpoints ====================
    
    def get_instances(self) -> dict:
        """Get all active learning instances with metrics."""
        return self._get("/activelearning/instances")
    
    def get_instance_info(self, instance_id: int) -> dict:
        """Get metrics for a specific instance."""
        return self._get(f"/activelearning/{instance_id}/info")
    
    # ==================== File Loading ====================
    
    @staticmethod
    def load_from_file(filepath: str) -> LegacyLogsFile:
        """
        Load session data from a JSON file (legacy format).
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Parsed log data
        """
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        return LegacyLogsFile(**data)
    
    @staticmethod
    def load_env_file(filepath: str) -> dict:
        """
        Load environment/simulation spec from a JSON file.
        
        Args:
            filepath: Path to environment JSON file
            
        Returns:
            Parsed environment data
        """
        import json
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncHumALClient:
    """Async client for interacting with HumAL Analytics API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = (
            base_url or 
            os.getenv("HUMAL_API_URL", "http://localhost:8000")
        ).rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def _post(self, endpoint: str, data: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        response = await self._client.post(url, json=data, params=params)
        response.raise_for_status()
        return response.json()
    
    async def check_connection(self) -> bool:
        try:
            await self._get("/config/availability")
            return True
        except Exception:
            return False
    
    async def get_overview(self) -> AnalyticsOverview:
        data = await self._get("/analytics/overview")
        return AnalyticsOverview(**data)
    
    async def list_sessions(self) -> list[SessionSummary]:
        data = await self._get("/analytics/sessions")
        return [SessionSummary(**s) for s in data.get("sessions", [])]
    
    async def get_session_summary(self, instance_id: int) -> SessionSummary:
        data = await self._get(f"/analytics/sessions/{instance_id}")
        return SessionSummary(**data)
    
    async def get_model_performance(self, instance_id: int) -> ModelPerformanceMetrics:
        data = await self._get(f"/analytics/sessions/{instance_id}/performance")
        return ModelPerformanceMetrics(**data)
    
    async def close(self):
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
