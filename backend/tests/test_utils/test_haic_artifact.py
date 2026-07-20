"""Tests for the HAIC artifact builder."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from app.utils.haic_artifact import build_decisions_artifact


def _sample_events() -> List[Dict[str, Any]]:
    return [
        {
            "timestamp": datetime(2026, 5, 20, 15, 7, 2, 343974),
            "user_id": "00000000-0000-0000-0000-000000000000",
            "action": "request_batch",
            "latency_ms": 0,
            "payload": {"batch_size": 1, "pool_size": 966, "strategy": "random sampling"},
            "actor_type": "system",
            "agent": "orchestrator",
            "object_id": "pool_main",
            "duration_s": None,
            "correct": None,
            "ai_suggested": None,
        },
        {
            "timestamp": datetime(2026, 5, 20, 15, 7, 2, 460341),
            "user_id": "00000000-0000-0000-0000-000000000000",
            "action": "select_batch",
            "latency_ms": 98,
            "payload": {"batch_id": 1779282422401, "ids": ["R-535527"], "uncertainties": None},
            "actor_type": "ai",
            "agent": "al_model",
            "object_id": "R-535527",
            "duration_s": None,
            "correct": None,
            "ai_suggested": None,
        },
        {
            "timestamp": datetime(2026, 5, 20, 15, 7, 15, 785937),
            "user_id": "00000000-0000-0000-0000-000000000000",
            "action": "confirm_label",
            "latency_ms": 500,
            "payload": {"ticket_id": "R-535527", "new_label": "(GI-UX) Group", "model_prediction": "(GI-UX) Group"},
            "actor_type": "human",
            "agent": "labeler_01",
            "object_id": "R-535527",
            "duration_s": 6.3,
            "correct": True,
            "ai_suggested": "(GI-UX) Group",
        },
    ]


def test_build_artifact_splits_decisions_and_system_events():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    assert len(artifact["decisions"]) == 2
    assert len(artifact["events"]) == 1
    assert {d["action"] for d in artifact["decisions"]} == {"select_batch", "confirm_label"}
    assert artifact["events"][0]["action"] == "request_batch"


def test_build_artifact_assigns_global_sequential_seq():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    all_entries = sorted(
        artifact["decisions"] + artifact["events"],
        key=lambda e: e["seq"],
    )
    for i, entry in enumerate(all_entries):
        assert entry["seq"] == i


def test_build_artifact_generates_session_id_from_first_timestamp():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    assert artifact["session_id"] == "st_session_20260520T150702"


def test_build_artifact_sets_interaction_id_to_object_id():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    for entry in artifact["decisions"] + artifact["events"]:
        assert entry["interaction_id"] == entry["object_id"]


def test_build_artifact_uses_timestamp_field():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    for entry in artifact["decisions"] + artifact["events"]:
        assert "t" not in entry
        assert entry["timestamp"] is not None
        assert entry["timestamp"].endswith("Z")


def test_build_artifact_promotes_object_id_to_top_level():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    for entry in artifact["decisions"]:
        assert entry["object_id"] is not None
    # verify object_id is not buried in payload
    for entry in artifact["decisions"]:
        payload = entry["payload"]
        assert "object_id" not in payload


def test_build_artifact_includes_duration_s_and_correct():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    for entry in artifact["decisions"] + artifact["events"]:
        assert "duration_s" in entry
        assert "correct" in entry


def test_build_artifact_includes_ai_suggested_only_when_not_none():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    for entry in artifact["events"]:
        assert "ai_suggested" not in entry  # request_batch has ai_suggested=None

    decisions_by_action = {d["action"]: d for d in artifact["decisions"]}
    assert "ai_suggested" not in decisions_by_action["select_batch"]
    assert decisions_by_action["confirm_label"]["ai_suggested"] == "(GI-UX) Group"


def test_build_artifact_moves_user_id_into_payload():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    for entry in artifact["decisions"] + artifact["events"]:
        assert "user_id" not in entry
        assert entry["payload"]["user_id"] is not None


def test_build_artifact_excludes_benchmark_export_events():
    events = _sample_events() + [
        {
            "timestamp": datetime(2026, 5, 20, 16, 0, 0),
            "user_id": "00000000-0000-0000-0000-000000000000",
            "action": "benchmark_export",
            "latency_ms": 15,
            "payload": {"minio_path": "benchmarking/1/events_1.json", "label_count": 10},
            "actor_type": "system",
            "agent": "orchestrator",
            "object_id": None,
            "duration_s": None,
            "correct": None,
            "ai_suggested": None,
        },
    ]
    artifact = build_decisions_artifact(
        events, al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    all_actions = [e["action"] for e in artifact["decisions"] + artifact["events"]]
    assert "benchmark_export" not in all_actions


def test_build_artifact_builds_meta_block():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    meta = artifact["meta"]
    assert meta["al_instance_id"] == 1
    assert meta["pilot_tag"] == "smart_ticketing"
    assert meta["application"]["name"] == "Smart Ticketing AL Platform"
    assert meta["application"]["version"] == "1.0.0"
    assert meta["ai_system"]["model_name"] == "random forest"
    assert meta["ai_system"]["model_type"] == "classifier"
    assert meta["task"]["name"] == "active_learning_ticket_triage"
    assert meta["task"]["domain"] == "customer_support"
    assert meta["task"]["unit_of_work"] == "ticket"
    assert meta["human"]["actor_id"] == "labeler_01"
    assert meta["human"]["role"] == "labeler"
    assert meta["human"]["expertise"] == "domain_expert"


def test_build_artifact_uses_db_lookup_values_for_meta():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="svm", creator_username="alice"
    )
    assert artifact["meta"]["ai_system"]["model_name"] == "svm"
    assert artifact["meta"]["human"]["actor_id"] == "alice"


def test_build_artifact_defaults_null_actor_type_to_system():
    events = _sample_events()
    events[0]["actor_type"] = None
    artifact = build_decisions_artifact(
        events, al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    # request_batch with actor_type=None should go to events array
    assert any(e["action"] == "request_batch" for e in artifact["events"])


def test_build_artifact_formats_timestamps_with_z_suffix():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    for entry in artifact["decisions"] + artifact["events"]:
        assert entry["timestamp"].endswith("Z"), f"timestamp field {entry['timestamp']} does not end with Z"
    assert artifact["meta"]["timestamps"]["start_time"].endswith("Z")
    assert artifact["meta"]["timestamps"]["end_time"].endswith("Z")


def test_build_artifact_top_level_envelope():
    artifact = build_decisions_artifact(
        _sample_events(), al_instance_id=1, model_name="random forest", creator_username="labeler_01"
    )
    assert artifact["artifact_schema"] == "haic.decisions_artifact.v1"
    assert artifact["schema_version"] == "haic.decisions.v1"
    assert artifact["session_id"] is not None
