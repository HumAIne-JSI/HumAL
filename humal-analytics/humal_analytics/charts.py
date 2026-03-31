"""
Plotly chart builders for HumAL Analytics.
"""

from typing import Optional, Union
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from humal_analytics.client import HumALClient
from humal_analytics.models import (
    SessionSummary,
    ModelPerformanceMetrics,
    LabelingMetrics,
    ClassDistributionMetrics,
    SessionComparison,
    AnalyticsOverview,
)


# Color palette
COLORS = {
    "primary": "#6366f1",      # Indigo
    "secondary": "#8b5cf6",    # Purple
    "success": "#22c55e",      # Green
    "warning": "#f59e0b",      # Amber
    "danger": "#ef4444",       # Red
    "info": "#06b6d4",         # Cyan
    "muted": "#64748b",        # Slate
    "background": "#0f172a",   # Dark slate
}

STRATEGY_COLORS = {
    "entropy": "#6366f1",
    "uncertainty sampling": "#8b5cf6",
    "random sampling": "#64748b",
    "query by committee": "#06b6d4",
    "expected model change": "#22c55e",
    "value of information": "#f59e0b",
}


class ChartBuilder:
    """Build Plotly charts for HumAL analytics."""
    
    def __init__(self, client: Optional[HumALClient] = None):
        """
        Initialize chart builder.
        
        Args:
            client: Optional HumALClient for fetching data
        """
        self.client = client
    
    def plot_f1_trend(
        self,
        f1_scores: Optional[list[float]] = None,
        num_labeled: Optional[list[int]] = None,
        instance_id: Optional[int] = None,
        title: str = "F1 Score Trend",
        show_confidence: bool = True,
    ) -> go.Figure:
        """
        Plot F1 score trend over iterations.
        
        Args:
            f1_scores: List of F1 scores (or fetch via instance_id)
            num_labeled: List of label counts for x-axis
            instance_id: Instance ID to fetch data from API
            title: Chart title
            show_confidence: Show confidence band
            
        Returns:
            Plotly Figure
        """
        if instance_id and self.client:
            perf = self.client.get_model_performance(instance_id)
            f1_scores = perf.f1_scores
            num_labeled = perf.num_labeled
        
        if not f1_scores:
            return self._empty_chart("No F1 data available")
        
        x = num_labeled if num_labeled else list(range(1, len(f1_scores) + 1))
        x_label = "Labeled Samples" if num_labeled else "Iteration"
        
        fig = go.Figure()
        
        # Main line
        fig.add_trace(go.Scatter(
            x=x,
            y=f1_scores,
            mode='lines+markers',
            name='F1 Score',
            line=dict(color=COLORS["primary"], width=3),
            marker=dict(size=8),
        ))
        
        # Confidence band (smoothed)
        if show_confidence and len(f1_scores) > 3:
            # Simple rolling std for confidence
            window = min(3, len(f1_scores) // 2)
            rolling_std = pd.Series(f1_scores).rolling(window, min_periods=1).std()
            upper = np.array(f1_scores) + rolling_std.fillna(0).values
            lower = np.array(f1_scores) - rolling_std.fillna(0).values
            
            fig.add_trace(go.Scatter(
                x=list(x) + list(x)[::-1],
                y=list(upper) + list(lower)[::-1],
                fill='toself',
                fillcolor='rgba(99, 102, 241, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                name='Confidence',
            ))
        
        # Target line
        fig.add_hline(y=0.8, line_dash="dash", line_color=COLORS["success"],
                      annotation_text="Target (0.8)")
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title="F1 Score (Macro)",
            template="plotly_dark",
            yaxis=dict(range=[0, 1]),
        )
        
        return fig
    
    def plot_learning_curve(
        self,
        sessions: list[dict],
        title: str = "Learning Curves Comparison",
    ) -> go.Figure:
        """
        Plot learning curves for multiple sessions.
        
        Args:
            sessions: List of dicts with 'name', 'f1_scores', 'num_labeled'
            title: Chart title
            
        Returns:
            Plotly Figure
        """
        fig = go.Figure()
        
        colors = list(STRATEGY_COLORS.values())
        
        for i, session in enumerate(sessions):
            name = session.get('name', f"Session {i+1}")
            f1_scores = session.get('f1_scores', [])
            num_labeled = session.get('num_labeled', list(range(len(f1_scores))))
            strategy = session.get('strategy', 'unknown')
            
            color = STRATEGY_COLORS.get(strategy, colors[i % len(colors)])
            
            fig.add_trace(go.Scatter(
                x=num_labeled,
                y=f1_scores,
                mode='lines+markers',
                name=name,
                line=dict(color=color, width=2),
                marker=dict(size=6),
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Labeled Samples",
            yaxis_title="F1 Score (Macro)",
            template="plotly_dark",
            yaxis=dict(range=[0, 1]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        
        return fig
    
    def plot_entropy_trend(
        self,
        mean_entropies: Optional[list[float]] = None,
        instance_id: Optional[int] = None,
        title: str = "Model Uncertainty Over Time",
    ) -> go.Figure:
        """
        Plot mean entropy trend (lower is better = more confident).
        """
        if instance_id and self.client:
            perf = self.client.get_model_performance(instance_id)
            mean_entropies = perf.mean_entropies
        
        if not mean_entropies:
            return self._empty_chart("No entropy data available")
        
        x = list(range(1, len(mean_entropies) + 1))
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=x,
            y=mean_entropies,
            mode='lines+markers',
            name='Mean Entropy',
            fill='tozeroy',
            line=dict(color=COLORS["warning"], width=2),
            fillcolor='rgba(245, 158, 11, 0.2)',
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Iteration",
            yaxis_title="Mean Entropy",
            template="plotly_dark",
        )
        
        return fig
    
    def plot_labeling_duration_distribution(
        self,
        durations: Optional[list[float]] = None,
        instance_id: Optional[int] = None,
        title: str = "Labeling Duration Distribution",
    ) -> go.Figure:
        """
        Plot histogram of labeling durations.
        """
        if instance_id and self.client:
            # Would need to extract from decisions
            pass
        
        if not durations:
            return self._empty_chart("No duration data available")
        
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=durations,
            nbinsx=20,
            name='Duration',
            marker_color=COLORS["info"],
        ))
        
        # Add mean line
        mean_dur = np.mean(durations)
        fig.add_vline(x=mean_dur, line_dash="dash", line_color=COLORS["danger"],
                      annotation_text=f"Mean: {mean_dur:.1f}s")
        
        fig.update_layout(
            title=title,
            xaxis_title="Duration (seconds)",
            yaxis_title="Frequency",
            template="plotly_dark",
        )
        
        return fig
    
    def plot_labeling_timeline(
        self,
        decisions: list[dict],
        title: str = "Labeling Timeline",
    ) -> go.Figure:
        """
        Plot Gantt-style timeline of labeling events.
        """
        # Extract label events with timing
        events = []
        for d in decisions:
            if d.get('actor_type') == 'human' and d.get('duration_s'):
                events.append({
                    'id': d.get('interaction_id', 'unknown'),
                    'start': d.get('t', 0) - d.get('duration_s', 0),
                    'end': d.get('t', 0),
                    'duration': d.get('duration_s'),
                    'label': d.get('payload', {}).get('label', 'unknown'),
                })
        
        if not events:
            return self._empty_chart("No labeling events found")
        
        df = pd.DataFrame(events)
        
        fig = px.timeline(
            df,
            x_start='start',
            x_end='end',
            y='id',
            color='label',
            title=title,
            template="plotly_dark",
        )
        
        fig.update_layout(
            xaxis_title="Time (seconds)",
            yaxis_title="Ticket ID",
        )
        
        return fig
    
    def plot_class_distribution(
        self,
        class_counts: Optional[dict[str, int]] = None,
        instance_id: Optional[int] = None,
        title: str = "Class Distribution",
        chart_type: str = "pie",  # "pie", "bar", "sunburst"
    ) -> go.Figure:
        """
        Plot class distribution.
        """
        if instance_id and self.client:
            dist = self.client.get_class_distribution(instance_id)
            class_counts = dist.class_counts
        
        if not class_counts:
            return self._empty_chart("No class data available")
        
        labels = list(class_counts.keys())
        values = list(class_counts.values())
        
        if chart_type == "pie":
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=list(STRATEGY_COLORS.values())[:len(labels)],
            )])
        elif chart_type == "bar":
            fig = go.Figure(data=[go.Bar(
                x=labels,
                y=values,
                marker_color=COLORS["primary"],
            )])
            fig.update_layout(
                xaxis_title="Class",
                yaxis_title="Count",
            )
        else:
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
        
        fig.update_layout(
            title=title,
            template="plotly_dark",
        )
        
        return fig
    
    def plot_strategy_comparison(
        self,
        strategy_data: dict[str, dict],
        metric: str = "avg_final_f1",
        title: str = "Strategy Performance Comparison",
    ) -> go.Figure:
        """
        Plot bar chart comparing strategy performance.
        
        Args:
            strategy_data: Dict of strategy -> metrics dict
            metric: Which metric to compare
            title: Chart title
        """
        strategies = list(strategy_data.keys())
        values = [strategy_data[s].get(metric, 0) or 0 for s in strategies]
        colors = [STRATEGY_COLORS.get(s, COLORS["muted"]) for s in strategies]
        
        fig = go.Figure(data=[go.Bar(
            x=strategies,
            y=values,
            marker_color=colors,
            text=[f"{v:.3f}" for v in values],
            textposition='outside',
        )])
        
        fig.update_layout(
            title=title,
            xaxis_title="Strategy",
            yaxis_title=metric.replace("_", " ").title(),
            template="plotly_dark",
        )
        
        return fig
    
    def plot_overview_cards(
        self,
        overview: AnalyticsOverview,
    ) -> go.Figure:
        """
        Create indicator cards for overview metrics.
        """
        fig = make_subplots(
            rows=2, cols=3,
            specs=[[{"type": "indicator"}] * 3] * 2,
            subplot_titles=[
                "Total Sessions", "Total Labels", "Avg F1 Score",
                "Best F1", "Avg Labels/Session", "Iterations"
            ],
        )
        
        metrics = [
            (overview.total_sessions, None, ""),
            (overview.total_labels, None, ""),
            (overview.avg_f1_score, None, ""),
            (overview.best_f1_score, None, ""),
            (overview.avg_labels_per_session, None, ""),
            (overview.total_iterations, None, ""),
        ]
        
        positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)]
        
        for (value, delta, suffix), (row, col) in zip(metrics, positions):
            fig.add_trace(go.Indicator(
                mode="number",
                value=value or 0,
                number={"suffix": suffix, "font": {"size": 40}},
            ), row=row, col=col)
        
        fig.update_layout(
            template="plotly_dark",
            height=400,
        )
        
        return fig
    
    def plot_session_comparison(
        self,
        comparison: SessionComparison,
        title: str = "Session Comparison",
    ) -> go.Figure:
        """
        Plot multi-session F1 comparison.
        """
        fig = go.Figure()
        
        colors = list(STRATEGY_COLORS.values())
        
        for i, instance_id in enumerate(comparison.instance_ids):
            f1_scores = comparison.f1_scores.get(instance_id, [])
            num_labeled = comparison.num_labeled.get(instance_id, list(range(len(f1_scores))))
            strategy = comparison.strategies.get(instance_id, "unknown")
            
            color = STRATEGY_COLORS.get(strategy, colors[i % len(colors)])
            
            fig.add_trace(go.Scatter(
                x=num_labeled,
                y=f1_scores,
                mode='lines+markers',
                name=f"Instance {instance_id} ({strategy})",
                line=dict(color=color, width=2),
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Labeled Samples",
            yaxis_title="F1 Score",
            template="plotly_dark",
            yaxis=dict(range=[0, 1]),
        )
        
        return fig
    
    def plot_batch_utilities(
        self,
        batch_utilities: list[list[float]],
        title: str = "Batch Selection Utilities",
    ) -> go.Figure:
        """
        Plot heatmap of batch selection utility scores over iterations.
        """
        if not batch_utilities:
            return self._empty_chart("No utility data available")
        
        # Pad to equal lengths
        max_len = max(len(b) for b in batch_utilities)
        padded = [b + [None] * (max_len - len(b)) for b in batch_utilities]
        
        fig = go.Figure(data=go.Heatmap(
            z=padded,
            colorscale='Viridis',
            colorbar_title="Utility",
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Batch Position",
            yaxis_title="Iteration",
            template="plotly_dark",
        )
        
        return fig
    
    def plot_dual_axis(
        self,
        f1_scores: list[float],
        mean_entropies: list[float],
        title: str = "F1 Score vs Uncertainty",
    ) -> go.Figure:
        """
        Plot F1 and entropy on dual y-axes.
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        x = list(range(1, len(f1_scores) + 1))
        
        fig.add_trace(
            go.Scatter(x=x, y=f1_scores, name="F1 Score",
                      line=dict(color=COLORS["primary"], width=3)),
            secondary_y=False,
        )
        
        fig.add_trace(
            go.Scatter(x=x, y=mean_entropies, name="Mean Entropy",
                      line=dict(color=COLORS["warning"], width=2, dash="dot")),
            secondary_y=True,
        )
        
        fig.update_layout(
            title=title,
            template="plotly_dark",
        )
        fig.update_xaxes(title_text="Iteration")
        fig.update_yaxes(title_text="F1 Score", secondary_y=False, range=[0, 1])
        fig.update_yaxes(title_text="Mean Entropy", secondary_y=True)
        
        return fig
    
    def _empty_chart(self, message: str) -> go.Figure:
        """Create an empty chart with a message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color=COLORS["muted"]),
        )
        fig.update_layout(
            template="plotly_dark",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig


def quick_plot(data: Union[dict, list], chart_type: str = "auto") -> go.Figure:
    """
    Quick helper to plot data without instantiating ChartBuilder.
    
    Args:
        data: Dict with 'f1_scores', 'num_labeled', etc. or list of values
        chart_type: "f1", "entropy", "comparison", or "auto"
    """
    builder = ChartBuilder()
    
    if isinstance(data, list):
        return builder.plot_f1_trend(f1_scores=data)
    
    if chart_type == "auto":
        if "f1_scores" in data:
            chart_type = "f1"
        elif "mean_entropies" in data:
            chart_type = "entropy"
        elif "class_counts" in data:
            chart_type = "distribution"
    
    if chart_type == "f1":
        return builder.plot_f1_trend(
            f1_scores=data.get("f1_scores"),
            num_labeled=data.get("num_labeled"),
        )
    elif chart_type == "entropy":
        return builder.plot_entropy_trend(mean_entropies=data.get("mean_entropies"))
    elif chart_type == "distribution":
        return builder.plot_class_distribution(class_counts=data.get("class_counts"))
    else:
        return builder._empty_chart("Unknown chart type")
