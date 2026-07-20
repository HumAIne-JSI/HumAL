from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from app.services.benchmarking_svc import BenchmarkingService


def test_export_if_needed_skips_below_threshold():
    duckdb_service = MagicMock()
    minio_service = MagicMock()
    duckdb_service.get_last_benchmark_export.return_value = None
    duckdb_service.count_label_events_since.return_value = 3

    service = BenchmarkingService(duckdb_service, minio_service)

    result = service.export_if_needed(1, label_threshold=10)

    assert result is None
    minio_service.save_benchmark_events.assert_not_called()
    duckdb_service.log_event.assert_not_called()


def test_export_if_needed_exports_and_logs_marker():
    duckdb_service = MagicMock()
    minio_service = MagicMock()
    last_export = datetime(2026, 1, 1, 10, 0, 0)
    events = [
        {
            "timestamp": datetime(2026, 1, 1, 10, 1, 0),
            "user_id": "00000000-0000-0000-0000-000000000000",
            "action": "select_batch",
            "latency_ms": 98,
            "payload": {"batch_id": 123, "ids": ["T1"]},
            "actor_type": "ai",
            "agent": "al_model",
            "object_id": "T1",
            "duration_s": None,
            "correct": None,
            "ai_suggested": None,
        },
        {
            "timestamp": datetime(2026, 1, 1, 10, 2, 0),
            "user_id": "00000000-0000-0000-0000-000000000000",
            "action": "confirm_label",
            "latency_ms": 500,
            "payload": {"ticket_id": "T1", "new_label": "Team A", "model_prediction": "Team A"},
            "actor_type": "human",
            "agent": "system",
            "object_id": "T1",
            "duration_s": 5.0,
            "correct": True,
            "ai_suggested": "Team A",
        },
        {
            "timestamp": datetime(2026, 1, 1, 10, 0, 30),
            "user_id": "00000000-0000-0000-0000-000000000000",
            "action": "request_batch",
            "latency_ms": 50,
            "payload": {"batch_size": 1, "strategy": "random", "pool_size": 100},
            "actor_type": "system",
            "agent": "orchestrator",
            "object_id": "pool_main",
            "duration_s": None,
            "correct": None,
            "ai_suggested": None,
        },
    ]
    duckdb_service.get_last_benchmark_export.return_value = last_export
    duckdb_service.count_label_events_since.return_value = 10
    duckdb_service.get_al_events.return_value = events
    duckdb_service.load_al_instance.return_value = {
        "model_name": "random forest",
        "user_id": "00000000-0000-0000-0000-000000000000",
    }
    duckdb_service.get_user.return_value = {"username": "alice"}
    minio_service.save_benchmark_events.return_value = {
        "bucket": "smart-finance-results",
        "object": "benchmarking/1/events_deadbeef.json",
    }

    service = BenchmarkingService(duckdb_service, minio_service)

    result = service.export_if_needed(1, label_threshold=10)

    assert result == {
        "bucket": "smart-finance-results",
        "object": "benchmarking/1/events_deadbeef.json",
    }
    minio_service.save_benchmark_events.assert_called_once()

    artifact = minio_service.save_benchmark_events.call_args.kwargs["payload"]
    assert artifact["artifact_schema"] == "haic.decisions_artifact.v1"
    assert artifact["schema_version"] == "haic.decisions.v1"
    assert "session_id" in artifact
    assert artifact["meta"]["ai_system"]["model_name"] == "random forest"
    assert artifact["meta"]["human"]["actor_id"] == "alice"
    assert len(artifact["decisions"]) == 2  # select_batch + confirm_label
    assert len(artifact["events"]) == 1      # request_batch

    duckdb_service.log_event.assert_called_once()
    assert duckdb_service.log_event.call_args.kwargs["action"] == "benchmark_export"
    assert duckdb_service.log_event.call_args.kwargs["payload"]["label_count"] == 10
    assert duckdb_service.log_event.call_args.kwargs["actor_type"] == "system"
    assert duckdb_service.log_event.call_args.kwargs["agent"] == "orchestrator"