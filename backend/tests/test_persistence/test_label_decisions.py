from __future__ import annotations

from app.persistence.duckdb.service import DuckDbPersistenceService


def test_upsert_label_decision_preserves_existing_fields(tmp_path):
    service = DuckDbPersistenceService(db_path=tmp_path / "test.db")

    service.upsert_label_decision(
        al_instance_id=0,
        ref="T001",
        label="Hardware",
        model_prediction="Network",
        latency_ms=120,
        explanation="Initial explanation",
        most_helpful_feature="title",
    )
    service.upsert_label_decision(
        al_instance_id=0,
        ref="T001",
        xai_result={"top_words": [["printer", 0.15]]},
        similar_tickets=[{"ref": "T002", "similarity": 0.91}],
    )

    row = service.get_label_decision(al_instance_id=0, ref="T001")

    assert row is not None
    assert row["label"] == "Hardware"
    assert row["model_prediction"] == "Network"
    assert row["latency_ms"] == 120
    assert row["explanation"] == "Initial explanation"
    assert row["most_helpful_feature"] == "title"
    assert row["xai_result"] == {"top_words": [["printer", 0.15]]}
    assert row["similar_tickets"] == [{"ref": "T002", "similarity": 0.91}]


def test_upsert_label_decision_updates_only_new_values(tmp_path):
    service = DuckDbPersistenceService(db_path=tmp_path / "test.db")

    service.upsert_label_decision(
        al_instance_id=0,
        ref="T002",
        label="Network",
        model_prediction="Hardware",
    )
    service.upsert_label_decision(
        al_instance_id=0,
        ref="T002",
        latency_ms=250,
        explanation="Updated during review",
    )

    row = service.get_label_decision(al_instance_id=0, ref="T002")

    assert row is not None
    assert row["label"] == "Network"
    assert row["model_prediction"] == "Hardware"
    assert row["latency_ms"] == 250
    assert row["explanation"] == "Updated during review"
    assert row["xai_result"] is None
    assert row["similar_tickets"] is None