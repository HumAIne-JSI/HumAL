from datetime import datetime
from typing import Optional
import numpy as np

from app.core.storage import ActiveLearningStorage
from app.data_models.analytics_dm import (
    Decision, SessionLog, SessionSummary, SessionMeta,
    LabelingMetrics, ModelPerformanceMetrics, ALEffectivenessMetrics,
    ClassDistributionMetrics, AnalyticsOverview, SessionComparison,
    ActorType
)


class AnalyticsService:
    def __init__(self, storage: ActiveLearningStorage):
        self.storage = storage
        # Store decision logs per instance (extended logging)
        self.decision_logs: dict[int, list[Decision]] = {}
        # Store labeling timestamps for duration calculations
        self.labeling_timestamps: dict[int, list[dict]] = {}
    
    def record_decision(
        self,
        instance_id: int,
        actor_type: ActorType,
        action: str,
        payload: dict,
        interaction_id: Optional[str] = None,
        latency_ms: Optional[float] = None,
        duration_s: Optional[float] = None
    ):
        """Record a decision event for analytics."""
        if instance_id not in self.decision_logs:
            self.decision_logs[instance_id] = []
            self.labeling_timestamps[instance_id] = []
        
        # Calculate timestamp relative to first decision
        if self.decision_logs[instance_id]:
            t = (datetime.now() - self._get_session_start(instance_id)).total_seconds()
        else:
            t = 0.0
        
        decision = Decision(
            t=t,
            actor_type=actor_type,
            action=action,
            payload=payload,
            interaction_id=interaction_id,
            latency_ms=latency_ms,
            duration_s=duration_s
        )
        self.decision_logs[instance_id].append(decision)
        
        # Track labeling durations separately
        if actor_type == ActorType.HUMAN and duration_s is not None:
            self.labeling_timestamps[instance_id].append({
                "timestamp": datetime.now(),
                "duration_s": duration_s,
                "interaction_id": interaction_id
            })
    
    def _get_session_start(self, instance_id: int) -> datetime:
        """Get the start time of a session."""
        if instance_id in self.decision_logs and self.decision_logs[instance_id]:
            # Estimate from first decision
            first = self.decision_logs[instance_id][0]
            return datetime.now()  # Simplified; in production, store actual start time
        return datetime.now()
    
    def get_session_log(self, instance_id: int) -> Optional[SessionLog]:
        """Get the full decision log for a session."""
        if instance_id not in self.storage.al_instances_dict:
            return None
        
        instance_data = self.storage.al_instances_dict[instance_id]
        decisions = self.decision_logs.get(instance_id, [])
        
        # Generate synthetic decisions from results if no explicit log exists
        if not decisions:
            decisions = self._generate_decisions_from_results(instance_id)
        
        return SessionLog(
            sim_id=f"humal_session_{instance_id}",
            session_id=f"session_{instance_id}",
            pilot_tag="humal",
            app_version="1.0.0",
            ai_model_version=instance_data.get('model_name', 'unknown'),
            meta=SessionMeta(task_parameters={
                "qs_strategy": instance_data.get('qs'),
                "model_name": instance_data.get('model_name')
            }),
            decisions=decisions
        )
    
    def _generate_decisions_from_results(self, instance_id: int) -> list[Decision]:
        """Generate decision log from existing results_dict data."""
        decisions = []
        
        if instance_id not in self.storage.results_dict:
            return decisions
        
        results = self.storage.results_dict[instance_id]
        instance_data = self.storage.al_instances_dict.get(instance_id, {})
        
        # Pool initialization
        decisions.append(Decision(
            t=0.0,
            actor_type=ActorType.SYSTEM,
            action="session_started",
            payload={
                "model_name": instance_data.get('model_name'),
                "qs_strategy": instance_data.get('qs')
            }
        ))
        
        f1_scores = results.get('f1_scores', [])
        num_labeled = results.get('num_labeled', [])
        mean_entropies = results.get('mean_entropies', [])
        
        # Generate decisions for each iteration
        for i, (f1, labeled, entropy_val) in enumerate(zip(f1_scores, num_labeled, mean_entropies)):
            t_base = (i + 1) * 10.0  # Approximate timing
            
            # AL query
            decisions.append(Decision(
                t=t_base,
                actor_type=ActorType.AI,
                action="al_query_issued",
                payload={"iteration": i + 1, "strategy": instance_data.get('qs')}
            ))
            
            # Labels received (aggregated)
            labels_this_iter = labeled - (num_labeled[i-1] if i > 0 else 0)
            decisions.append(Decision(
                t=t_base + 1.0,
                actor_type=ActorType.HUMAN,
                action="labels_received",
                payload={"count": labels_this_iter, "total": labeled}
            ))
            
            # Model update
            decisions.append(Decision(
                t=t_base + 2.0,
                actor_type=ActorType.AI,
                action="model_update_finished",
                payload={
                    "metrics": {
                        "f1_macro": f1,
                        "mean_entropy": entropy_val
                    }
                }
            ))
        
        return decisions
    
    def get_session_summary(self, instance_id: int) -> Optional[SessionSummary]:
        """Get aggregated summary for a session."""
        if instance_id not in self.storage.al_instances_dict:
            return None
        
        instance_data = self.storage.al_instances_dict[instance_id]
        results = self.storage.results_dict.get(instance_id, {})
        
        f1_scores = results.get('f1_scores', [])
        num_labeled = results.get('num_labeled', [])
        mean_entropies = results.get('mean_entropies', [])
        
        # Calculate labeling durations
        labeling_data = self.labeling_timestamps.get(instance_id, [])
        avg_duration = None
        if labeling_data:
            durations = [d['duration_s'] for d in labeling_data if d['duration_s']]
            avg_duration = np.mean(durations) if durations else None
        
        return SessionSummary(
            session_id=f"session_{instance_id}",
            instance_id=instance_id,
            model_name=instance_data.get('model_name', 'unknown'),
            qs_strategy=instance_data.get('qs', 'unknown'),
            total_labeled=num_labeled[-1] if num_labeled else 0,
            labeling_iterations=len(f1_scores),
            avg_labeling_duration_s=avg_duration,
            latest_f1=f1_scores[-1] if f1_scores else None,
            f1_improvement=(f1_scores[-1] - f1_scores[0]) if len(f1_scores) > 1 else None,
            latest_mean_entropy=mean_entropies[-1] if mean_entropies else None,
            entropy_reduction=(mean_entropies[0] - mean_entropies[-1]) if len(mean_entropies) > 1 else None
        )
    
    def get_labeling_metrics(self, instance_id: int) -> Optional[LabelingMetrics]:
        """Get detailed labeling efficiency metrics."""
        if instance_id not in self.storage.results_dict:
            return None
        
        results = self.storage.results_dict[instance_id]
        num_labeled = results.get('num_labeled', [])
        
        # Calculate labels per iteration
        labels_per_iter = []
        for i, total in enumerate(num_labeled):
            prev = num_labeled[i-1] if i > 0 else 0
            labels_per_iter.append(total - prev)
        
        # Get duration stats
        labeling_data = self.labeling_timestamps.get(instance_id, [])
        durations = [d['duration_s'] for d in labeling_data if d.get('duration_s')]
        
        total_labels = num_labeled[-1] if num_labeled else 0
        avg_duration = np.mean(durations) if durations else None
        
        # Calculate throughput (labels per hour)
        throughput = None
        if avg_duration and avg_duration > 0:
            throughput = 3600.0 / avg_duration
        
        return LabelingMetrics(
            total_labels=total_labels,
            labels_per_iteration=labels_per_iter,
            avg_duration_per_label_s=avg_duration,
            min_duration_s=min(durations) if durations else None,
            max_duration_s=max(durations) if durations else None,
            throughput_per_hour=throughput
        )
    
    def get_model_performance(self, instance_id: int) -> Optional[ModelPerformanceMetrics]:
        """Get model performance trend metrics."""
        if instance_id not in self.storage.results_dict:
            return None
        
        results = self.storage.results_dict[instance_id]
        f1_scores = results.get('f1_scores', [])
        mean_entropies = results.get('mean_entropies', [])
        num_labeled = results.get('num_labeled', [])
        
        # Determine trend
        trend = None
        if len(f1_scores) >= 3:
            recent_avg = np.mean(f1_scores[-3:])
            early_avg = np.mean(f1_scores[:3])
            if recent_avg > early_avg + 0.02:
                trend = "improving"
            elif recent_avg < early_avg - 0.02:
                trend = "declining"
            else:
                trend = "stable"
        
        # Find convergence (where improvement < 1% for 3 consecutive iterations)
        convergence = None
        for i in range(2, len(f1_scores)):
            if all(abs(f1_scores[j] - f1_scores[j-1]) < 0.01 for j in range(i-1, i+1)):
                convergence = i
                break
        
        return ModelPerformanceMetrics(
            f1_scores=f1_scores,
            mean_entropies=mean_entropies,
            num_labeled=num_labeled,
            f1_trend=trend,
            convergence_iteration=convergence
        )
    
    def get_al_effectiveness(self, instance_id: int) -> Optional[ALEffectivenessMetrics]:
        """Get AL strategy effectiveness metrics."""
        if instance_id not in self.storage.al_instances_dict:
            return None
        
        instance_data = self.storage.al_instances_dict[instance_id]
        results = self.storage.results_dict.get(instance_id, {})
        
        mean_entropies = results.get('mean_entropies', [])
        f1_scores = results.get('f1_scores', [])
        num_labeled = results.get('num_labeled', [])
        
        # Calculate uncertainty reduction rate
        reduction_rate = None
        if len(mean_entropies) >= 2:
            reduction_rate = (mean_entropies[0] - mean_entropies[-1]) / len(mean_entropies)
        
        # Calculate samples needed to reach 0.7 F1 (or target)
        target_f1 = 0.7
        samples_to_target = None
        for i, (f1, labels) in enumerate(zip(f1_scores, num_labeled)):
            if f1 >= target_f1:
                samples_to_target = labels
                break
        
        # Efficiency score: F1 improvement per label
        efficiency = None
        if f1_scores and num_labeled and num_labeled[-1] > 0:
            f1_gain = f1_scores[-1] - (f1_scores[0] if f1_scores else 0)
            efficiency = f1_gain / num_labeled[-1] * 100  # Scaled
        
        return ALEffectivenessMetrics(
            strategy=instance_data.get('qs', 'unknown'),
            uncertainty_reduction_rate=reduction_rate,
            samples_to_target_f1=samples_to_target,
            efficiency_score=efficiency
        )
    
    def get_class_distribution(self, instance_id: int) -> Optional[ClassDistributionMetrics]:
        """Get class distribution metrics from labeled data."""
        if instance_id not in self.storage.dataset_dict:
            return None
        
        dataset = self.storage.dataset_dict[instance_id]
        y_train = dataset.get('y_train')
        le = dataset.get('le')
        
        if y_train is None:
            return None
        
        # Count labeled instances per class
        from skactiveml.utils import MISSING_LABEL
        labeled_mask = y_train != MISSING_LABEL
        labeled_y = y_train[labeled_mask]
        
        # Get class counts
        class_counts = {}
        class_percentages = {}
        total = len(labeled_y)
        
        if total > 0 and le is not None:
            unique, counts = np.unique(labeled_y, return_counts=True)
            for val, count in zip(unique, counts):
                try:
                    class_name = str(le.inverse_transform([int(val)])[0])
                    class_counts[class_name] = int(count)
                    class_percentages[class_name] = count / total
                except Exception:
                    class_counts[str(val)] = int(count)
                    class_percentages[str(val)] = count / total
        
        # Calculate imbalance ratio
        imbalance = None
        majority = None
        minority = None
        if class_counts:
            max_count = max(class_counts.values())
            min_count = min(class_counts.values())
            if min_count > 0:
                imbalance = max_count / min_count
            majority = max(class_counts, key=class_counts.get)
            minority = min(class_counts, key=class_counts.get)
        
        return ClassDistributionMetrics(
            class_counts=class_counts,
            class_percentages=class_percentages,
            imbalance_ratio=imbalance,
            majority_class=majority,
            minority_class=minority
        )
    
    def get_overview(self) -> AnalyticsOverview:
        """Get aggregated analytics across all sessions."""
        total_sessions = len(self.storage.al_instances_dict)
        total_labels = 0
        total_iterations = 0
        all_f1_scores = []
        strategy_f1s: dict[str, list[float]] = {}
        best_f1 = 0.0
        best_f1_instance = None
        
        for instance_id, results in self.storage.results_dict.items():
            f1_scores = results.get('f1_scores', [])
            num_labeled = results.get('num_labeled', [])
            
            if num_labeled:
                total_labels += num_labeled[-1]
            total_iterations += len(f1_scores)
            
            if f1_scores:
                all_f1_scores.extend(f1_scores)
                latest_f1 = f1_scores[-1]
                if latest_f1 > best_f1:
                    best_f1 = latest_f1
                    best_f1_instance = instance_id
                
                # Track by strategy
                instance_data = self.storage.al_instances_dict.get(instance_id, {})
                strategy = instance_data.get('qs', 'unknown')
                if strategy not in strategy_f1s:
                    strategy_f1s[strategy] = []
                strategy_f1s[strategy].append(latest_f1)
        
        # Calculate averages
        avg_f1 = np.mean(all_f1_scores) if all_f1_scores else None
        avg_labels = total_labels / total_sessions if total_sessions > 0 else None
        
        # Determine best strategy
        strategy_performance = {s: np.mean(scores) for s, scores in strategy_f1s.items()}
        best_strategy = max(strategy_performance, key=strategy_performance.get) if strategy_performance else None
        
        # Calculate avg labeling duration
        all_durations = []
        for timestamps in self.labeling_timestamps.values():
            all_durations.extend([t['duration_s'] for t in timestamps if t.get('duration_s')])
        avg_duration = np.mean(all_durations) if all_durations else None
        
        return AnalyticsOverview(
            total_sessions=total_sessions,
            total_instances=total_sessions,
            total_labels=total_labels,
            total_iterations=total_iterations,
            avg_f1_score=avg_f1,
            avg_labels_per_session=avg_labels,
            avg_labeling_duration_s=avg_duration,
            best_f1_instance_id=best_f1_instance,
            best_f1_score=best_f1 if best_f1 > 0 else None,
            most_efficient_strategy=best_strategy,
            strategy_performance=strategy_performance
        )
    
    def compare_sessions(self, instance_ids: list[int]) -> SessionComparison:
        """Compare multiple sessions side by side."""
        f1_dict = {}
        num_labeled_dict = {}
        strategies_dict = {}
        
        for instance_id in instance_ids:
            if instance_id in self.storage.results_dict:
                results = self.storage.results_dict[instance_id]
                f1_dict[instance_id] = results.get('f1_scores', [])
                num_labeled_dict[instance_id] = results.get('num_labeled', [])
            
            if instance_id in self.storage.al_instances_dict:
                instance_data = self.storage.al_instances_dict[instance_id]
                strategies_dict[instance_id] = instance_data.get('qs', 'unknown')
        
        # Rank by final F1
        f1_ranking = sorted(
            instance_ids,
            key=lambda x: f1_dict.get(x, [0])[-1] if f1_dict.get(x) else 0,
            reverse=True
        )
        
        # Rank by efficiency (F1 per label)
        def efficiency(x):
            f1s = f1_dict.get(x, [])
            labels = num_labeled_dict.get(x, [])
            if f1s and labels and labels[-1] > 0:
                return f1s[-1] / labels[-1]
            return 0
        
        efficiency_ranking = sorted(instance_ids, key=efficiency, reverse=True)
        
        return SessionComparison(
            session_ids=[f"session_{i}" for i in instance_ids],
            instance_ids=instance_ids,
            f1_scores=f1_dict,
            num_labeled=num_labeled_dict,
            strategies=strategies_dict,
            f1_ranking=f1_ranking,
            efficiency_ranking=efficiency_ranking
        )
    
    def export_session(self, instance_id: int) -> Optional[dict]:
        """Export session data in the standard JSON format."""
        session_log = self.get_session_log(instance_id)
        if not session_log:
            return None
        
        return {
            "logs": [session_log.model_dump()]
        }
