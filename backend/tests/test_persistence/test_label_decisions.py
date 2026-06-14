from __future__ import annotations

from app.persistence.duckdb.service import DuckDbPersistenceService


def test_load_label_decisions_with_xai_filters_non_empty(tmp_path):
    service = DuckDbPersistenceService(db_path=tmp_path / "test.db")

    service.upsert_label_decision(
        al_instance_id=0,
        ref="T001",
        label="Team A",
        xai_result={"top_words": [["printer", 0.15]]},
    )
    service.upsert_label_decision(
        al_instance_id=0,
        ref="T002",
        label="Team B",
        similar_tickets=[{"ref": "T003", "similarity": 0.91}],
    )
    service.upsert_label_decision(
        al_instance_id=0,
        ref="T003",
        label="Team A",
        xai_result={},
    )
    service.upsert_label_decision(
        al_instance_id=0,
        ref="T004",
        label="Team B",
        similar_tickets=[],
    )
    service.upsert_label_decision(
        al_instance_id=0,
        ref="T005",
    )
    service.upsert_label_decision(
        al_instance_id=0,
        ref="T006",
        xai_result={"top_words": [["vpn", 0.2]]},
    )

    rows = service.load_label_decisions_with_xai(al_instance_id=0)

    assert {row["ref"] for row in rows} == {"T001", "T002"}


def test_load_label_decisions_with_xai_deserializes_json(tmp_path):
    service = DuckDbPersistenceService(db_path=tmp_path / "test.db")

    service.upsert_label_decision(
        al_instance_id=0,
        ref="T010",
        label="Team A",
        xai_result={"top_words": [["printer", 0.15]]},
        similar_tickets=[{"ref": "T011", "similarity": 0.91}],
    )

    rows = service.load_label_decisions_with_xai(al_instance_id=0)

    assert len(rows) == 1
    assert isinstance(rows[0]["xai_result"], dict)
    assert isinstance(rows[0]["similar_tickets"], list)


def test_load_label_decisions_with_xai_returns_metadata_fields(tmp_path):
    service = DuckDbPersistenceService(db_path=tmp_path / "test.db")

    service.upsert_label_decision(
        al_instance_id=0,
        ref="T020",
        label="Team A",
        model_prediction="Team A",
        most_helpful_feature="lime",
        xai_result={"top_words": [["printer", 0.15]]},
    )

    rows = service.load_label_decisions_with_xai(al_instance_id=0)

    assert len(rows) == 1
    row = rows[0]
    assert row["label"] == "Team A"
    assert row["model_prediction"] == "Team A"
    assert row["most_helpful_feature"] == "lime"
    assert {"model_prediction", "most_helpful_feature"}.issubset(row.keys())


def test_load_label_decisions_with_xai_excludes_unlabeled(tmp_path):
    service = DuckDbPersistenceService(db_path=tmp_path / "test.db")

    service.upsert_label_decision(al_instance_id=0, ref="L001", label="Team A", xai_result={"a": 1})
    service.upsert_label_decision(al_instance_id=0, ref="U001", xai_result={"a": 1})

    rows = service.load_label_decisions_with_xai(al_instance_id=0)

    assert [r["ref"] for r in rows] == ["L001"]