from __future__ import annotations

import pytest

from app.persistence.duckdb.service import DuckDbPersistenceService


def test_upsert_label_decision_persists_signals_and_derived_skip(tmp_path):
    service = DuckDbPersistenceService(db_path=tmp_path / "test.db")

    service.upsert_label_decision(
        al_instance_id=0,
        ref="T001",
        label="Team A",
        is_tired=True,
        is_difficult=False,
        i_dont_know=True,
    )

    ld = service.get_label_decision(al_instance_id=0, ref="T001")
    assert ld is not None
    assert ld["is_tired"] is True
    assert ld["is_difficult"] is False
    assert ld["i_dont_know"] is True
    assert ld["skipped_for_training"] is True
    assert ld["label"] == "Team A"


@pytest.mark.parametrize("idk_val,expected_skip", [
    (True, True),
    (False, False),
    (None, False),
])
def test_skipped_for_training_derived_from_i_dont_know(tmp_path, idk_val, expected_skip):
    service = DuckDbPersistenceService(db_path=tmp_path / "test.db")

    kwargs = {"al_instance_id": 0, "ref": "T001", "label": "Team A"}
    if idk_val is not None:
        kwargs["i_dont_know"] = idk_val

    service.upsert_label_decision(**kwargs)

    ld = service.get_label_decision(al_instance_id=0, ref="T001")
    assert ld["skipped_for_training"] is expected_skip


def test_load_skipped_refs_returns_only_idk_true(tmp_path):
    service = DuckDbPersistenceService(db_path=tmp_path / "test.db")

    service.upsert_label_decision(al_instance_id=0, ref="S001", label="A", i_dont_know=True)
    service.upsert_label_decision(al_instance_id=0, ref="S002", label="B", i_dont_know=False)
    service.upsert_label_decision(al_instance_id=0, ref="S003", label="C")  # i_dont_know=None

    skipped = service.load_skipped_refs(al_instance_id=0)
    assert skipped == ["S001"]


def test_upsert_preserves_signals_on_partial_update(tmp_path):
    service = DuckDbPersistenceService(db_path=tmp_path / "test.db")

    # First upsert with i_dont_know=True
    service.upsert_label_decision(
        al_instance_id=0, ref="T001", label="A", i_dont_know=True,
    )

    # Second upsert with only xai_result (no signals passed)
    service.upsert_label_decision(
        al_instance_id=0, ref="T001", xai_result={"top_words": [["printer", 0.15]]},
    )

    ld = service.get_label_decision(al_instance_id=0, ref="T001")
    assert ld["i_dont_know"] is True
    assert ld["skipped_for_training"] is True
    assert ld["xai_result"] == {"top_words": [["printer", 0.15]]}


def test_get_label_decision_includes_new_columns(tmp_path):
    service = DuckDbPersistenceService(db_path=tmp_path / "test.db")

    service.upsert_label_decision(
        al_instance_id=0, ref="T001", label="A",
        is_tired=True, is_difficult=True, i_dont_know=False,
    )

    ld = service.get_label_decision(al_instance_id=0, ref="T001")
    for key in ("is_tired", "is_difficult", "i_dont_know", "skipped_for_training"):
        assert key in ld, f"Key {key} missing from get_label_decision result"


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