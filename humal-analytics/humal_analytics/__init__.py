"""
HumAL Analytics - Analytics tool for HumAL Active Learning sessions.
"""

from humal_analytics.client import HumALClient
from humal_analytics.models import (
    SessionLog,
    SessionSummary,
    AnalyticsOverview,
    LabelingMetrics,
    ModelPerformanceMetrics,
    ALEffectivenessMetrics,
    ClassDistributionMetrics,
    SessionComparison,
)
from humal_analytics.metrics import MetricsCalculator
from humal_analytics.charts import ChartBuilder

__version__ = "0.1.0"
__all__ = [
    "HumALClient",
    "MetricsCalculator",
    "ChartBuilder",
    "SessionLog",
    "SessionSummary",
    "AnalyticsOverview",
    "LabelingMetrics",
    "ModelPerformanceMetrics",
    "ALEffectivenessMetrics",
    "ClassDistributionMetrics",
    "SessionComparison",
]
