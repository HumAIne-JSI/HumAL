from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Optional

from app.config.config import SYSTEM_USER_ID
from app.persistence.duckdb.service import DuckDbPersistenceService
from app.persistence.minio_storage import MinioService


class BenchmarkingService:
    def __init__(self, duckdb_service: DuckDbPersistenceService, minio_service: MinioService):
        self.duckdb_service = duckdb_service
        self.minio_service = minio_service

    def export_if_needed(self, al_instance_id: int, label_threshold: int = 10, user_id: str = SYSTEM_USER_ID) -> Optional[Dict[str, str]]:
        last_export_ts = self.duckdb_service.get_last_benchmark_export(al_instance_id)
        label_count = self.duckdb_service.count_label_events_since(al_instance_id, last_export_ts)

        if label_count < label_threshold:
            return None

        events = self.duckdb_service.get_al_events(al_instance_id, since_timestamp=last_export_ts)
        if not events:
            return None

        from_timestamp = last_export_ts if last_export_ts is not None else events[0]["timestamp"]
        to_timestamp = events[-1]["timestamp"]
        exported_at = datetime.now()
        export_id = exported_at.strftime("%Y%m%dT%H%M%S%f")

        payload = {
            "al_instance_id": al_instance_id,
            "from_timestamp": from_timestamp,
            "to_timestamp": to_timestamp,
            "exported_at": exported_at,
            "events": events,
        }

        start = time.perf_counter()
        storage_info = self.minio_service.save_benchmark_events(
            al_instance_id=al_instance_id,
            export_id=export_id,
            payload=payload,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        self.duckdb_service.log_event(
            al_instance_id=al_instance_id,
            user_id=user_id,
            action="benchmark_export",
            latency_ms=latency_ms,
            payload={
                "minio_path": storage_info["object"],
                "label_count": label_count,
                "from_timestamp": from_timestamp,
                "to_timestamp": to_timestamp,
            },
        )

        return storage_info