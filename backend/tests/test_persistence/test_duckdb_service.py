"""Tests for DuckDB persistence service."""
from __future__ import annotations

import tempfile
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from app.persistence.duckdb import DuckDbPersistenceService


@pytest.fixture
def temp_db():
    """Create a temporary database for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        yield db_path


@pytest.fixture
def service(temp_db):
    """Create a fresh service instance for each test."""
    return DuckDbPersistenceService(db_path=temp_db)


class TestUsers:
    def test_upsert_user_with_auto_generated_id(self, service):
        user_id = service.upsert_user(username="alice", password="hash123")
        
        assert isinstance(user_id, uuid.UUID)
        
        user = service.get_user(user_id=user_id)
        assert user["username"] == "alice"
        assert user["password"] == "hash123"
        assert "created_at" in user

    def test_upsert_user_with_provided_id(self, service):
        custom_id = uuid.uuid4()
        user_id = service.upsert_user(user_id=custom_id, username="bob", password="pwd")
        
        assert user_id == custom_id
        
        user = service.get_user(user_id=custom_id)
        assert user["username"] == "bob"

    def test_upsert_user_replaces_existing(self, service):
        user_id = service.upsert_user(username="charlie", password="old")
        service.upsert_user(user_id=user_id, username="charlie", password="new")
        
        user = service.get_user(user_id=user_id)
        assert user["password"] == "new"

    def test_get_user_nonexistent(self, service):
        result = service.get_user(user_id=uuid.uuid4())
        assert result is None

    def test_get_user_by_username(self, service):
        service.upsert_user(username="dave", password="secret")
        
        user = service.get_user_by_username(username="dave")
        assert user is not None
        assert user["username"] == "dave"
        assert user["password"] == "secret"

    def test_get_user_by_username_nonexistent(self, service):
        result = service.get_user_by_username(username="nobody")
        assert result is None

    def test_get_user_does_not_include_api_key(self, service):
        user_id = service.upsert_user(username="nokey", password="pwd")
        user = service.get_user(user_id=user_id)
        assert "api_key" not in user

    def test_get_user_by_username_does_not_include_api_key(self, service):
        service.upsert_user(username="nokey2", password="pwd")
        user = service.get_user_by_username(username="nokey2")
        assert user is not None
        assert "api_key" not in user

    def test_upsert_user_rejects_api_key_argument(self, service):
        with pytest.raises(TypeError):
            service.upsert_user(username="legacy", password="pwd", api_key="should-fail")


class TestALInstances:
    def test_save_and_load_instance(self, service):
        data = {
            "model_name": "SVC",
            "qs": "entropy",
            "classes": [1, 2, 3]
        }
        service.save_al_instance(1, data)
        
        loaded = service.load_al_instance(1)
        
        assert loaded["model_name"] == "SVC"
        assert loaded["qs"] == "entropy"
        assert loaded["classes"] == [1, 2, 3]

    def test_load_nonexistent_instance(self, service):
        result = service.load_al_instance(999)
        assert result is None

    def test_get_all_instances(self, service):
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        service.save_al_instance(2, {"model_name": "M2", "qs": "qs2", "classes": []})
        service.save_al_instance(3, {"model_name": "M3", "qs": "qs3", "classes": []})
        
        instances = service.get_all_instances()
        
        assert len(instances) == 4
        assert 0 in instances
        assert 1 in instances
        assert 2 in instances
        assert 3 in instances
        assert instances[0]["model_name"] == "default_model"
        assert instances[1]["model_name"] == "M1"
        assert instances[2]["model_name"] == "M2"

    def test_save_al_instance_with_user_id(self, service):
        user_id = service.upsert_user(username="owner", password="pwd")
        data = {"model_name": "SVC", "qs": "entropy", "classes": [1, 2]}
        service.save_al_instance(1, data, user_id=user_id)
        
        loaded = service.load_al_instance(1)
        assert loaded["user_id"] == str(user_id)

    def test_get_all_instances_filters_by_user_id(self, service):
        user_a = service.upsert_user(username="user_a", password="pwd")
        user_b = service.upsert_user(username="user_b", password="pwd")
        
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []}, user_id=user_a)
        service.save_al_instance(2, {"model_name": "M2", "qs": "qs2", "classes": []}, user_id=user_b)
        service.save_al_instance(3, {"model_name": "M3", "qs": "qs3", "classes": []}, user_id=user_a)
        
        instances_a = service.get_all_instances(user_id=user_a)
        assert 1 in instances_a
        assert 3 in instances_a
        assert 2 not in instances_a
        
        instances_b = service.get_all_instances(user_id=user_b)
        assert 2 in instances_b
        assert 1 not in instances_b

    def test_get_all_instances_empty(self, service):
        instances = service.get_all_instances()
        assert instances == {
            0: {
                "model_name": "default_model",
                "qs": "default_query_strategy",
                "classes": [1, 2],
                "user_id": "00000000-0000-0000-0000-000000000000",
            }
        }


class TestTickets:
    def test_upsert_tickets_df_basic(self, service):
        df = pd.DataFrame({
            "Ref": ["T001", "T002", "T003"],
            "Title_anon": ["Issue 1", "Issue 2", "Issue 3"]
        })
        
        count = service.upsert_tickets_df(df, split="train")
        
        assert count == 3
        
        loaded = service.load_tickets("train")
        assert len(loaded) == 3
        assert "T001" in loaded["Ref"].values
        assert "T002" in loaded["Ref"].values

    def test_upsert_tickets_df_with_all_columns(self, service):
        df = pd.DataFrame({
            "Ref": ["T100"],
            "Service subcategory->Name": ["Hardware"],
            "Service->Name": ["Network"],
            "Request Type": ["Incident"],
            "Last team ID->Name": ["IT Support"],
            "Title_anon": ["Network down"],
            "Description_anon": ["Cannot connect"],
            "Public_log_anon": ["Investigating"]
        })
        
        count = service.upsert_tickets_df(df, split="test", dataset_timestamp="2026-01-29")
        
        assert count == 1
        
        loaded = service.load_tickets("test")
        assert len(loaded) == 1
        assert loaded.iloc[0]["Ref"] == "T100"
        assert loaded.iloc[0]["Service subcategory->Name"] == "Hardware"
        assert loaded.iloc[0]["split"] == "test"

    def test_upsert_tickets_empty_df(self, service):
        df = pd.DataFrame()
        count = service.upsert_tickets_df(df, split="train")
        assert count == 0

    def test_upsert_tickets_missing_ref_column(self, service):
        df = pd.DataFrame({"Title_anon": ["Issue"]})
        
        with pytest.raises(ValueError, match="must contain 'Ref' column"):
            service.upsert_tickets_df(df, split="train")

    def test_load_tickets_train(self, service):
        df_train = pd.DataFrame({"Ref": ["T1", "T2"]})
        df_test = pd.DataFrame({"Ref": ["T3", "T4"]})
        
        service.upsert_tickets_df(df_train, split="train")
        service.upsert_tickets_df(df_test, split="test")
        
        train_tickets = service.load_tickets("train")
        
        assert len(train_tickets) == 2
        assert "T1" in train_tickets["Ref"].values
        assert "T3" not in train_tickets["Ref"].values

    def test_load_tickets_test(self, service):
        df_train = pd.DataFrame({"Ref": ["T1"]})
        df_test = pd.DataFrame({"Ref": ["T3"]})
        
        service.upsert_tickets_df(df_train, split="train")
        service.upsert_tickets_df(df_test, split="test")
        
        test_tickets = service.load_tickets("test")
        
        assert len(test_tickets) == 1
        assert "T3" in test_tickets["Ref"].values

    def test_load_tickets_invalid_split(self, service):
        with pytest.raises(ValueError, match="must be 'train' or 'test'"):
            service.load_tickets("invalid")


class TestLabels:
    def test_save_and_load_labels(self, service):
        # Create dependencies first (required by foreign keys)
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        user_id = service.upsert_user(username="labeler", password="pwd")
        service.upsert_tickets_df(pd.DataFrame({"Ref": ["T001", "T002", "T003"]}), split="train")
        
        labels = {
            "T001": "ClassA",
            "T002": "ClassB",
            "T003": "ClassA"
        }
        
        count = service.save_labels(1, user_id, labels, split="train")
        
        assert count == 3
        
        loaded = service.load_labels(1, user_id, split="train")
        
        assert loaded["T001"] == "ClassA"
        assert loaded["T002"] == "ClassB"
        assert loaded["T003"] == "ClassA"

    def test_save_labels_skips_null(self, service):
        # Create dependencies first (required by foreign keys)
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        user_id = service.upsert_user(username="labeler2", password="pwd")
        service.upsert_tickets_df(pd.DataFrame({"Ref": ["T001", "T002", "T003", "T004"]}), split="train")
        
        labels = {
            "T001": "ClassA",
            "T002": pd.NA,
            "T003": None,
            "T004": "ClassB"
        }
        
        count = service.save_labels(1, user_id, labels, split="train")
        
        assert count == 2  # Only T001 and T004
        
        loaded = service.load_labels(1, user_id, split="train")
        assert len(loaded) == 2
        assert "T002" not in loaded.index

    def test_save_labels_empty_dict(self, service):
        user_id = service.upsert_user(username="labeler3", password="pwd")
        count = service.save_labels(1, user_id, {}, split="train")
        assert count == 0

    def test_load_labels_nonexistent(self, service):
        user_id = service.upsert_user(username="labeler4", password="pwd")
        loaded = service.load_labels(999, user_id, split="train")
        
        assert len(loaded) == 0
        assert isinstance(loaded, pd.Series)

    def test_save_labels_replaces_existing(self, service):
        # Create dependencies first (required by foreign keys)
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        user_id = service.upsert_user(username="labeler5", password="pwd")
        service.upsert_tickets_df(pd.DataFrame({"Ref": ["T001"]}), split="train")
        
        service.save_labels(1, user_id, {"T001": "OldClass"}, split="train")
        service.save_labels(1, user_id, {"T001": "NewClass"}, split="train")
        
        loaded = service.load_labels(1, user_id, split="train")
        assert loaded["T001"] == "NewClass"

    def test_labels_isolated_by_user(self, service):
        # Create dependencies first (required by foreign keys)
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        user1 = service.upsert_user(username="user1", password="pwd")
        user2 = service.upsert_user(username="user2", password="pwd")
        service.upsert_tickets_df(pd.DataFrame({"Ref": ["T001"]}), split="train")
        
        service.save_labels(1, user1, {"T001": "User1Class"}, split="train")
        service.save_labels(1, user2, {"T001": "User2Class"}, split="train")
        
        loaded1 = service.load_labels(1, user1, split="train")
        loaded2 = service.load_labels(1, user2, split="train")
        
        assert loaded1["T001"] == "User1Class"
        assert loaded2["T001"] == "User2Class"

    def test_labels_majority_label_wins(self, service):
        labels_df = pd.DataFrame(
            {
                "ref": ["T001", "T001", "T001"],
                "label": ["ClassA", "ClassA", "ClassB"],
                "labeled_at": [
                    pd.Timestamp("2026-02-10 10:00:00"),
                    pd.Timestamp("2026-02-10 11:00:00"),
                    pd.Timestamp("2026-02-10 12:00:00"),
                ],
            }
        )

        resolved = service._keep_majority_or_latest_label(labels_df)

        assert resolved.loc[resolved["ref"] == "T001", "label"].iloc[0] == "ClassA"

    def test_labels_latest_majority_breaks_tie(self, service):
        labels_df = pd.DataFrame(
            {
                "ref": ["T002", "T002", "T002", "T002"],
                "label": ["ClassA", "ClassB", "ClassA", "ClassB"],
                "labeled_at": [
                    pd.Timestamp("2026-02-10 09:00:00"),
                    pd.Timestamp("2026-02-10 10:00:00"),
                    pd.Timestamp("2026-02-10 11:00:00"),
                    pd.Timestamp("2026-02-10 12:00:00"),
                ],
            }
        )

        resolved = service._keep_majority_or_latest_label(labels_df)

        assert resolved.loc[resolved["ref"] == "T002", "label"].iloc[0] == "ClassB"


class TestEvents:
    def test_log_and_read_events(self, service):
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        service.upsert_user(username="user", password="pwd")

        service.log_event(
            al_instance_id=1,
            user_id="00000000-0000-0000-0000-000000000000",
            action="confirm_label",
            latency_ms=250,
            payload={"ticket_id": "T1"},
        )
        service.log_event(
            al_instance_id=1,
            user_id="00000000-0000-0000-0000-000000000000",
            action="benchmark_export",
            latency_ms=15,
            payload={"minio_path": "benchmarking/1/events_1.json"},
        )

        events = service.get_al_events(1)
        assert len(events) == 2
        assert events[0]["action"] == "confirm_label"
        assert events[0]["payload"]["ticket_id"] == "T1"

        filtered = service.get_al_events(1, actions=["benchmark_export"])
        assert len(filtered) == 1
        assert filtered[0]["action"] == "benchmark_export"

        last_export = service.get_last_benchmark_export(1)
        assert last_export is not None

    def test_log_event_serializes_datetime_payload(self, service):
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        service.upsert_user(username="user", password="pwd")

        exported_at = datetime(2026, 1, 1, 10, 30, 0)
        service.log_event(
            al_instance_id=1,
            user_id="00000000-0000-0000-0000-000000000000",
            action="benchmark_export",
            payload={"exported_at": exported_at},
        )

        events = service.get_al_events(1)
        assert events[0]["payload"]["exported_at"] == exported_at.isoformat()

    def test_count_label_events_since(self, service):
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        service.log_event(al_instance_id=1, user_id="00000000-0000-0000-0000-000000000000", action="confirm_label")
        service.log_event(al_instance_id=1, user_id="00000000-0000-0000-0000-000000000000", action="override_label")
        service.log_event(al_instance_id=1, user_id="00000000-0000-0000-0000-000000000000", action="predict")

        assert service.count_label_events_since(1, None) == 2


class TestModelPaths:
    def test_save_and_load_model_paths(self, service):
        # Create AL instance first (required by foreign key)
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        
        service.save_model_path(1, 1, "storage/models/1/model_1.joblib")
        service.save_model_path(1, 2, "storage/models/1/model_2.joblib")
        service.save_model_path(1, 3, "storage/models/1/model_3.joblib")
        
        paths = service.load_model_paths(1)
        
        assert len(paths) == 3
        assert paths[1] == "storage/models/1/model_1.joblib"
        assert paths[2] == "storage/models/1/model_2.joblib"
        assert paths[3] == "storage/models/1/model_3.joblib"

    def test_load_model_paths_empty(self, service):
        paths = service.load_model_paths(999)
        assert paths == {}

    def test_save_model_path_replaces(self, service):
        # Create AL instance first (required by foreign key)
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        
        service.save_model_path(1, 1, "old/path.joblib")
        service.save_model_path(1, 1, "new/path.joblib")
        
        paths = service.load_model_paths(1)
        assert paths[1] == "new/path.joblib"


class TestMetrics:
    def test_save_and_load_metrics(self, service):
        # Create AL instance first (required by foreign key)
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        
        iteration_id = service.save_metrics(1, f1_score=0.85, mean_entropy=0.42, num_labeled=100)
        
        assert iteration_id == 1
        
        metrics = service.load_metrics(1)
        
        assert metrics["iteration_id"] == 1
        assert metrics["f1_score"] == 0.85
        assert metrics["mean_entropy"] == 0.42
        assert metrics["num_labeled"] == 100

    def test_save_metrics_partial(self, service):
        # Create AL instance first (required by foreign key)
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        
        iteration_id = service.save_metrics(1, f1_score=0.75)
        
        assert iteration_id == 1
        
        metrics = service.load_metrics(1)
        
        assert metrics["iteration_id"] == 1
        assert metrics["f1_score"] == 0.75
        assert metrics["mean_entropy"] is None
        assert metrics["num_labeled"] is None

    def test_load_metrics_nonexistent(self, service):
        metrics = service.load_metrics(999)
        
        assert metrics["iteration_id"] is None
        assert metrics["f1_score"] is None
        assert metrics["mean_entropy"] is None
        assert metrics["num_labeled"] is None

    def test_save_metrics_replaces(self, service):
        # Create AL instance first (required by foreign key)
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        
        iter1 = service.save_metrics(1, f1_score=0.5)
        iter2 = service.save_metrics(1, f1_score=0.9, mean_entropy=0.3)
        
        assert iter1 == 1
        assert iter2 == 2
        
        metrics = service.load_metrics(1)
        
        assert metrics["iteration_id"] == 2
        assert metrics["f1_score"] == 0.9
        assert metrics["mean_entropy"] == 0.3

    def test_save_metrics_with_explicit_iteration_id(self, service):
        # Create AL instance first (required by foreign key)
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        
        # Save with explicit iteration_id
        iter_id = service.save_metrics(1, iteration_id=5, f1_score=0.8)
        
        assert iter_id == 5
        
        # Next auto iteration should be 6
        next_iter = service.save_metrics(1, f1_score=0.85)
        
        assert next_iter == 6
        
        # Can load specific iteration
        metrics_5 = service.load_metrics(1, iteration_id=5)
        assert metrics_5["iteration_id"] == 5
        assert metrics_5["f1_score"] == 0.8
        
        # Default loads latest (iteration 6)
        metrics_latest = service.load_metrics(1)
        assert metrics_latest["iteration_id"] == 6
        assert metrics_latest["f1_score"] == 0.85

    def test_load_all_metrics(self, service):
        # Create AL instance first (required by foreign key)
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        
        # Save multiple iterations
        service.save_metrics(1, f1_score=0.5, num_labeled=10)
        service.save_metrics(1, f1_score=0.7, num_labeled=20)
        service.save_metrics(1, f1_score=0.85, num_labeled=30)
        
        all_metrics = service.load_all_metrics(1)
        
        assert len(all_metrics) == 3
        assert all_metrics[0]["iteration_id"] == 1
        assert all_metrics[0]["f1_score"] == 0.5
        assert all_metrics[0]["num_labeled"] == 10
        
        assert all_metrics[1]["iteration_id"] == 2
        assert all_metrics[1]["f1_score"] == 0.7
        
        assert all_metrics[2]["iteration_id"] == 3
        assert all_metrics[2]["f1_score"] == 0.85


class TestDeletion:
    def test_delete_instance_cascade(self, service):
        # Create user first
        user_id = service.upsert_user(username="test_user", password="hash")
        
        # Setup AL instance
        service.save_al_instance(1, {"model_name": "SVC", "qs": "entropy", "classes": []})
        
        # Add tickets (required by foreign key in labels)
        service.upsert_tickets_df(pd.DataFrame({"Ref": ["T001"]}), split="train")
        
        # Add related data
        service.save_metrics(1, f1_score=0.85)
        service.save_model_path(1, 1, "path/to/model.joblib")
        service.save_labels(1, user_id, {"T001": "ClassA"}, split="train")
        
        # Delete instance
        service.delete_instance(1)
        
        # Verify all related data is gone
        assert service.load_al_instance(1) is None
        assert service.load_metrics(1)["f1_score"] is None
        assert service.load_model_paths(1) == {}
        assert len(service.load_labels(1, user_id, split="train")) == 0

    def test_delete_nonexistent_instance(self, service):
        # Should not raise an error
        service.delete_instance(999)

    def test_delete_preserves_other_instances(self, service):
        service.save_al_instance(1, {"model_name": "M1", "qs": "qs1", "classes": []})
        service.save_al_instance(2, {"model_name": "M2", "qs": "qs2", "classes": []})
        
        service.delete_instance(1)
        
        assert service.load_al_instance(1) is None
        assert service.load_al_instance(2) is not None


class TestIntegration:
    def test_full_workflow(self, service):
        """Test a complete AL workflow."""
        # Create user
        user_id = service.upsert_user(username="analyst", password="hashed")
        
        # Upload tickets
        tickets_df = pd.DataFrame({
            "Ref": ["T1", "T2", "T3"],
            "Title_anon": ["Issue A", "Issue B", "Issue C"]
        })
        service.upsert_tickets_df(tickets_df, split="train")
        
        # Create AL instance
        service.save_al_instance(1, {
            "model_name": "SVC",
            "qs": "entropy",
            "classes": [1, 2]
        })
        
        # Label some tickets
        service.save_labels(1, user_id, {"T1": "A", "T2": "B"}, split="train")
        
        # Save model paths
        service.save_model_path(1, 1, "models/1/model_1.joblib")
        
        # Save metrics
        service.save_metrics(1, f1_score=0.72, num_labeled=2)
        
        # Verify everything
        user = service.get_user(user_id=user_id)
        assert user["username"] == "analyst"
        
        tickets = service.load_tickets("train")
        assert len(tickets) == 3
        
        instance = service.load_al_instance(1)
        assert instance["model_name"] == "SVC"
        
        labels = service.load_labels(1, user_id, split="train")
        assert len(labels) == 2
        
        paths = service.load_model_paths(1)
        assert 1 in paths
        
        metrics = service.load_metrics(1)
        assert metrics["f1_score"] == 0.72


class TestXAIJobs:
    def test_create_xai_job_with_user_id(self, service):
        # Create prerequisites
        user_id = service.upsert_user(username="xai_user", password="pwd")
        service.save_al_instance(1, {"model_name": "SVC", "qs": "entropy", "classes": []}, user_id=user_id)
        service.upsert_tickets_df(pd.DataFrame({"Ref": ["T001"]}), split="train")
        
        job_id = uuid.uuid4()
        service.create_xai_job(
            al_instance_id=1,
            job_id=job_id,
            model_id=0,
            ticket_ref_or_sha="sha123",
            request_ticket_location="tickets/T001",
            request_model_location="models/1/0",
            request_preprocessor_location=None,
            request_one_hot_encoder_location=None,
            request_raw_tickets_locations=["raw_tickets/test"],
            user_id=user_id,
        )
        
        job = service.get_xai_job(job_id)
        assert job is not None
        assert job["user_id"] == str(user_id)
        assert job["al_instance_id"] == 1
