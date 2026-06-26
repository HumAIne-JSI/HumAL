"""Tests for ActiveLearningService.export_instance."""
from __future__ import annotations

import io
import json
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from app.core.storage import ActiveLearningStorage
from app.persistence.duckdb import DuckDbPersistenceService
from app.services.active_learning_svc import ActiveLearningService


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield DuckDbPersistenceService(db_path=Path(tmpdir) / "test.duckdb")


def _populate(db, instance_id=1):
    owner = db.upsert_user(username="alice", password="secret")
    db.save_al_instance(
        instance_id,
        {"model_name": "svm", "qs": "random sampling", "classes": [0, 1]},
        user_id=owner,
    )
    db.upsert_tickets_df(
        pd.DataFrame({"Ref": ["T001", "T002"], "Title_anon": ["a", "b"]}),
        split="train",
    )
    db.save_labels(instance_id, owner, {"T001": "A"}, split="train")
    db.save_labels(0, owner, {"T001": "GT-A"}, split="train")
    db.save_metrics(instance_id, f1_score=0.5, num_labeled=1)
    db.save_model_path(instance_id, 0, "storage/models/1/0.joblib")
    db.log_event(
        al_instance_id=instance_id,
        user_id=str(owner),
        action="confirm_label",
        payload={"k": "v"},
    )
    return owner


class TestExportInstance:
    def test_returns_zip_buffer_and_filename(self, temp_db):
        _populate(temp_db)
        service = ActiveLearningService(ActiveLearningStorage(), duckdb_service=temp_db)

        buffer, filename = service.export_instance(1)

        assert isinstance(buffer, io.BytesIO)
        assert filename.startswith("export_al_1_")
        assert filename.endswith(".zip")

    def test_zip_contains_manifest_and_one_json_per_table(self, temp_db):
        _populate(temp_db)
        service = ActiveLearningService(ActiveLearningStorage(), duckdb_service=temp_db)

        buffer, _ = service.export_instance(1)

        with zipfile.ZipFile(buffer) as zf:
            names = zf.namelist()
            assert "manifest.json" in names
            for table in (
                "al_instances",
                "metrics",
                "model_paths",
                "al_events",
                "labels",
                "ground_truth_labels",
                "label_decisions",
                "xai_jobs",
                "instance_delegations",
                "tickets",
                "users",
            ):
                assert f"duckdb/{table}.json" in names

            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["schema_version"] == 1
            assert manifest["al_instance_id"] == 1
            assert "exported_at" in manifest
            assert manifest["tables"]["al_instances"] == 1
            assert manifest["tables"]["ground_truth_labels"] == 1

            events = json.loads(zf.read("duckdb/al_events.json"))
            assert events[0]["payload"] == {"k": "v"}

            users = json.loads(zf.read("duckdb/users.json"))
            assert users[0]["password"] is None

            ground_truth = json.loads(zf.read("duckdb/ground_truth_labels.json"))
            assert ground_truth[0]["label"] == "GT-A"
            assert ground_truth[0]["al_instance_id"] == 0

    def test_export_without_persistence_raises(self):
        service = ActiveLearningService(ActiveLearningStorage())

        with pytest.raises(ValueError, match="persistence is not configured"):
            service.export_instance(1)

    def test_export_empty_instance_still_valid_zip(self, temp_db):
        service = ActiveLearningService(ActiveLearningStorage(), duckdb_service=temp_db)

        buffer, _ = service.export_instance(999)

        with zipfile.ZipFile(buffer) as zf:
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["tables"]["al_instances"] == 0
            assert manifest["tables"]["ground_truth_labels"] == 0
            assert json.loads(zf.read("duckdb/labels.json")) == []
            assert json.loads(zf.read("duckdb/ground_truth_labels.json")) == []
