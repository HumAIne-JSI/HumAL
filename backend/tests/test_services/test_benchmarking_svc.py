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
            "user_id": "user-1",
            "action": "confirm_label",
            "latency_ms": 123,
            "payload": {"ticket_id": "T1"},
        },
        {
            "timestamp": datetime(2026, 1, 1, 10, 2, 0),
            "user_id": "user-1",
            "action": "override_label",
            "latency_ms": 456,
            "payload": {"ticket_id": "T2"},
        },
    ]
    duckdb_service.get_last_benchmark_export.return_value = last_export
    duckdb_service.count_label_events_since.return_value = 10
    duckdb_service.get_al_events.return_value = events
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
    duckdb_service.log_event.assert_called_once()
    assert duckdb_service.log_event.call_args.kwargs["action"] == "benchmark_export"
    assert duckdb_service.log_event.call_args.kwargs["payload"]["label_count"] == 10