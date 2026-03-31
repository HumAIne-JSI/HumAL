"""
Metrics calculators for HumAL Analytics.
Provides statistical analysis and derived metrics from session data.
"""

from typing import Optional
import numpy as np
from scipy import stats

from humal_analytics.models import (
    SessionLog,
    SessionSummary,
    LabelingMetrics,
    ModelPerformanceMetrics,
    ALEffectivenessMetrics,
    ClassDistributionMetrics,
    LegacySessionLog,
    LegacyLogsFile,
)


class MetricsCalculator:
    """Calculate derived metrics from session data."""
    
    @staticmethod
    def calculate_labeling_stats(decisions: list) -> dict:
        """
        Calculate labeling statistics from decision log.
        
        Returns:
            Dict with duration stats, throughput, etc.
        """
        # Extract labeling events
        label_events = [
            d for d in decisions 
            if hasattr(d, 'actor_type') and d.actor_type in ('human', 'HUMAN')
            and hasattr(d, 'duration_s') and d.duration_s is not None
        ]
        
        if not label_events:
            return {
                "count": 0,
                "avg_duration_s": None,
                "std_duration_s": None,
                "min_duration_s": None,
                "max_duration_s": None,
                "median_duration_s": None,
                "throughput_per_hour": None,
                "p95_duration_s": None,
            }
        
        durations = [e.duration_s for e in label_events]
        
        avg_duration = np.mean(durations)
        throughput = 3600.0 / avg_duration if avg_duration > 0 else None
        
        return {
            "count": len(label_events),
            "avg_duration_s": avg_duration,
            "std_duration_s": np.std(durations),
            "min_duration_s": np.min(durations),
            "max_duration_s": np.max(durations),
            "median_duration_s": np.median(durations),
            "throughput_per_hour": throughput,
            "p95_duration_s": np.percentile(durations, 95),
        }
    
    @staticmethod
    def calculate_f1_trend(f1_scores: list[float]) -> dict:
        """
        Analyze F1 score trend over iterations.
        
        Returns:
            Dict with trend direction, slope, R², etc.
        """
        if len(f1_scores) < 2:
            return {
                "trend": "insufficient_data",
                "slope": None,
                "r_squared": None,
                "improvement": None,
                "convergence_iteration": None,
            }
        
        x = np.arange(len(f1_scores))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, f1_scores)
        
        # Determine trend
        if slope > 0.01:
            trend = "improving"
        elif slope < -0.01:
            trend = "declining"
        else:
            trend = "stable"
        
        # Find convergence (where improvement < 1% for 3 consecutive)
        convergence = None
        for i in range(2, len(f1_scores)):
            if all(abs(f1_scores[j] - f1_scores[j-1]) < 0.01 for j in range(max(1, i-2), i+1)):
                convergence = i - 2
                break
        
        return {
            "trend": trend,
            "slope": slope,
            "r_squared": r_value ** 2,
            "improvement": f1_scores[-1] - f1_scores[0] if f1_scores else None,
            "convergence_iteration": convergence,
            "final_f1": f1_scores[-1] if f1_scores else None,
            "initial_f1": f1_scores[0] if f1_scores else None,
        }
    
    @staticmethod
    def calculate_entropy_reduction(mean_entropies: list[float]) -> dict:
        """
        Analyze model uncertainty reduction over iterations.
        
        Returns:
            Dict with reduction rate, total reduction, etc.
        """
        if len(mean_entropies) < 2:
            return {
                "total_reduction": None,
                "reduction_rate": None,
                "reduction_percentage": None,
                "initial_entropy": None,
                "final_entropy": None,
            }
        
        initial = mean_entropies[0]
        final = mean_entropies[-1]
        total_reduction = initial - final
        
        return {
            "total_reduction": total_reduction,
            "reduction_rate": total_reduction / len(mean_entropies),
            "reduction_percentage": (total_reduction / initial * 100) if initial > 0 else None,
            "initial_entropy": initial,
            "final_entropy": final,
        }
    
    @staticmethod
    def calculate_efficiency_score(
        f1_scores: list[float],
        num_labeled: list[int]
    ) -> dict:
        """
        Calculate AL efficiency (performance gain per label).
        
        Returns:
            Dict with efficiency score, labels needed for targets, etc.
        """
        if not f1_scores or not num_labeled:
            return {
                "efficiency_score": None,
                "labels_to_70_f1": None,
                "labels_to_80_f1": None,
                "labels_to_90_f1": None,
                "f1_per_100_labels": None,
            }
        
        f1_gain = f1_scores[-1] - f1_scores[0] if len(f1_scores) > 1 else 0
        total_labels = num_labeled[-1] if num_labeled else 0
        
        # Efficiency: F1 gain per label (scaled)
        efficiency = (f1_gain / total_labels * 100) if total_labels > 0 else None
        
        # Find labels needed for target F1 scores
        targets = {0.7: None, 0.8: None, 0.9: None}
        for target in targets:
            for f1, labels in zip(f1_scores, num_labeled):
                if f1 >= target:
                    targets[target] = labels
                    break
        
        # F1 gain per 100 labels
        f1_per_100 = (f1_gain / total_labels * 100) if total_labels > 0 else None
        
        return {
            "efficiency_score": efficiency,
            "labels_to_70_f1": targets[0.7],
            "labels_to_80_f1": targets[0.8],
            "labels_to_90_f1": targets[0.9],
            "f1_per_100_labels": f1_per_100,
        }
    
    @staticmethod
    def calculate_class_balance(class_counts: dict[str, int]) -> dict:
        """
        Analyze class distribution balance.
        
        Returns:
            Dict with imbalance metrics, entropy, etc.
        """
        if not class_counts:
            return {
                "imbalance_ratio": None,
                "gini_coefficient": None,
                "distribution_entropy": None,
                "majority_class": None,
                "minority_class": None,
            }
        
        counts = list(class_counts.values())
        total = sum(counts)
        
        if total == 0:
            return {
                "imbalance_ratio": None,
                "gini_coefficient": None,
                "distribution_entropy": None,
                "majority_class": None,
                "minority_class": None,
            }
        
        # Imbalance ratio
        max_count = max(counts)
        min_count = min(counts)
        imbalance = max_count / min_count if min_count > 0 else float('inf')
        
        # Distribution entropy (normalized)
        probs = np.array(counts) / total
        dist_entropy = stats.entropy(probs) / np.log(len(counts)) if len(counts) > 1 else 0
        
        # Gini coefficient
        sorted_counts = np.sort(counts)
        n = len(sorted_counts)
        cumulative = np.cumsum(sorted_counts)
        gini = (n + 1 - 2 * np.sum(cumulative) / cumulative[-1]) / n if n > 0 else 0
        
        # Majority/minority classes
        majority = max(class_counts, key=class_counts.get)
        minority = min(class_counts, key=class_counts.get)
        
        return {
            "imbalance_ratio": imbalance,
            "gini_coefficient": gini,
            "distribution_entropy": dist_entropy,
            "majority_class": majority,
            "minority_class": minority,
        }
    
    @staticmethod
    def compare_strategies(sessions: list[dict]) -> dict:
        """
        Compare performance across different AL strategies.
        
        Args:
            sessions: List of session dicts with 'strategy' and 'f1_scores'
            
        Returns:
            Dict with strategy rankings and statistics
        """
        strategy_results = {}
        
        for session in sessions:
            strategy = session.get('strategy', 'unknown')
            f1_scores = session.get('f1_scores', [])
            
            if strategy not in strategy_results:
                strategy_results[strategy] = {
                    "final_f1_scores": [],
                    "improvements": [],
                    "session_count": 0,
                }
            
            if f1_scores:
                strategy_results[strategy]["final_f1_scores"].append(f1_scores[-1])
                if len(f1_scores) > 1:
                    strategy_results[strategy]["improvements"].append(
                        f1_scores[-1] - f1_scores[0]
                    )
                strategy_results[strategy]["session_count"] += 1
        
        # Calculate summary stats per strategy
        summary = {}
        for strategy, data in strategy_results.items():
            final_scores = data["final_f1_scores"]
            improvements = data["improvements"]
            
            summary[strategy] = {
                "session_count": data["session_count"],
                "avg_final_f1": np.mean(final_scores) if final_scores else None,
                "std_final_f1": np.std(final_scores) if final_scores else None,
                "avg_improvement": np.mean(improvements) if improvements else None,
                "best_f1": max(final_scores) if final_scores else None,
            }
        
        # Rank strategies by avg F1
        ranking = sorted(
            summary.keys(),
            key=lambda s: summary[s]["avg_final_f1"] or 0,
            reverse=True
        )
        
        return {
            "strategies": summary,
            "ranking": ranking,
            "best_strategy": ranking[0] if ranking else None,
        }
    
    @staticmethod
    def calculate_learning_curve_area(
        f1_scores: list[float],
        num_labeled: list[int]
    ) -> float:
        """
        Calculate area under the learning curve (AUC-LC).
        Higher is better - indicates faster learning.
        
        Returns:
            AUC-LC value (normalized 0-1)
        """
        if len(f1_scores) < 2 or len(num_labeled) < 2:
            return 0.0
        
        # Normalize x-axis to [0, 1]
        max_labels = max(num_labeled)
        if max_labels == 0:
            return 0.0
        
        x_norm = np.array(num_labeled) / max_labels
        
        # Calculate AUC using trapezoidal rule
        auc = np.trapz(f1_scores, x_norm)
        
        return auc
    
    @staticmethod
    def parse_legacy_log(log_file: LegacyLogsFile) -> list[dict]:
        """
        Parse legacy JSON log format into metrics-ready dicts.
        
        Returns:
            List of session dicts with extracted metrics
        """
        sessions = []
        
        for log in log_file.logs:
            session_data = {
                "session_id": log.session_id,
                "sim_id": log.sim_id,
                "user_id": log.user_id,
                "app_version": log.app_version,
                "ai_model_version": log.ai_model_version,
                "decisions": [],
                "metrics": {
                    "f1_scores": [],
                    "labeling_durations": [],
                    "strategies": [],
                    "batch_utilities": [],
                },
            }
            
            for decision in log.decisions:
                session_data["decisions"].append({
                    "t": decision.t,
                    "actor_type": decision.actor_type,
                    "action": decision.action,
                    "payload": decision.payload,
                    "duration_s": decision.duration_s,
                    "latency_ms": decision.latency_ms,
                })
                
                # Extract specific metrics
                if decision.action == "model_update_finished":
                    metrics = decision.payload.get("metrics", {})
                    if "f1_macro" in metrics:
                        session_data["metrics"]["f1_scores"].append(metrics["f1_macro"])
                
                if decision.action == "label_received" and decision.duration_s:
                    session_data["metrics"]["labeling_durations"].append(decision.duration_s)
                
                if decision.action == "al_query_issued":
                    strategy = decision.payload.get("strategy")
                    if strategy:
                        session_data["metrics"]["strategies"].append(strategy)
                
                if decision.action == "al_candidates":
                    utilities = decision.payload.get("utilities", [])
                    if utilities:
                        session_data["metrics"]["batch_utilities"].append(utilities)
            
            sessions.append(session_data)
        
        return sessions
