"""Build a haic.decisions_artifact.v1 artifact from raw AL events."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config.config import (
    APP_NAME,
    APP_VERSION,
    AI_MODEL_TYPE,
    HUMAN_EXPERTISE,
    HUMAN_ROLE,
    PILOT_TAG,
    TASK_DOMAIN,
    TASK_NAME,
    TASK_UNIT_OF_WORK,
)

ARTIFACT_SCHEMA = "haic.decisions_artifact.v1"
SCHEMA_VERSION = "haic.decisions.v1"


def _format_t(dt: Optional[datetime]) -> Optional[str]:
    """Format a datetime as ISO 8601 with Z suffix."""
    if dt is None:
        return None
    iso = dt.isoformat()
    if iso.endswith("+00:00"):
        iso = iso[:-6] + "Z"
    elif not iso.endswith("Z"):
        iso = iso + "Z"
    return iso


def build_decisions_artifact(
    events: List[Dict[str, Any]],
    *,
    al_instance_id: int,
    model_name: Optional[str] = None,
    creator_username: Optional[str] = None,
) -> Dict[str, Any]:
    """Transform raw AL events into a haic.decisions_artifact.v1 artifact.

    Args:
        events: Raw event dicts from get_al_events, sorted by timestamp ASC.
            Each dict must contain: timestamp, user_id, action, latency_ms,
            payload, actor_type, agent, object_id, duration_s, correct,
            ai_suggested.
        al_instance_id: The AL instance ID for this session.
        model_name: Model name from al_instances table (for meta.ai_system).
        creator_username: Username of the instance creator (for meta.human.actor_id).

    Returns:
        A dict with artifact_schema, schema_version, session_id, meta,
        decisions (human+ai events), and events (system events).
    """
    first_ts = events[0]["timestamp"]
    last_ts = events[-1]["timestamp"]
    session_id = f"st_session_{first_ts.strftime('%Y%m%dT%H%M%S')}"

    decisions: List[Dict[str, Any]] = []
    system_events: List[Dict[str, Any]] = []

    for seq, event in enumerate(events):
        action = event["action"]
        if action == "benchmark_export":
            continue

        actor_type = event.get("actor_type") or "system"
        ai_suggested_val = event.get("ai_suggested")

        payload = dict(event.get("payload") or {})
        if event.get("user_id") is not None:
            payload["user_id"] = event["user_id"]

        entry: Dict[str, Any] = {
            "seq": seq,
            "t": _format_t(event["timestamp"]),
            "agent": event.get("agent"),
            "actor_type": actor_type,
            "action": action,
            "object_id": event.get("object_id"),
            "latency_ms": event.get("latency_ms"),
            "duration_s": event.get("duration_s"),
            "correct": event.get("correct"),
            "interaction_id": f"{session_id}_{seq:03d}",
            "session_id": session_id,
        }
        if ai_suggested_val is not None:
            entry["ai_suggested"] = ai_suggested_val
        entry["payload"] = payload

        if actor_type == "system":
            system_events.append(entry)
        else:
            decisions.append(entry)

    meta = {
        "pilot_tag": PILOT_TAG,
        "application": {"name": APP_NAME, "version": APP_VERSION},
        "ai_system": {"model_name": model_name, "model_type": AI_MODEL_TYPE},
        "task": {
            "name": TASK_NAME,
            "domain": TASK_DOMAIN,
            "unit_of_work": TASK_UNIT_OF_WORK,
        },
        "human": {
            "actor_id": creator_username,
            "role": HUMAN_ROLE,
            "expertise": HUMAN_EXPERTISE,
        },
        "timestamps": {
            "start_time": _format_t(first_ts),
            "end_time": _format_t(last_ts),
        },
    }

    return {
        "artifact_schema": ARTIFACT_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "meta": meta,
        "decisions": decisions,
        "events": system_events,
    }
