"""Tests for ActiveLearningService persistence loading."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import LabelEncoder
from skactiveml.utils import MISSING_LABEL

from app.core.storage import ActiveLearningStorage
from app.persistence.duckdb import DuckDbPersistenceService
from app.persistence.local_artifacts import LocalArtifactsStore
from app.persistence.minio_storage import MinioService
from app.services.active_learning_svc import ActiveLearningService
from app.data_models.active_learning_dm import LabelInfo, LabelRequest, NewInstance


@pytest.fixture
def storage():
    """Create a fresh storage instance."""
    return ActiveLearningStorage()


@pytest.fixture
def mock_duckdb_service():
    """Create a mock DuckDB persistence service."""
    return MagicMock(spec=DuckDbPersistenceService)


@pytest.fixture
def mock_local_artifacts():
    """Create a mock local artifacts store."""
    return MagicMock(spec=LocalArtifactsStore)


class _FakeLabelEncoder:
    classes_ = np.array(["Team A", "Team B", np.nan], dtype=object)

    def transform(self, values):
        encoded = []
        for value in values:
            if pd.isna(value):
                encoded.append(2)
            elif value == "Team A":
                encoded.append(0)
            elif value == "Team B":
                encoded.append(1)
            else:
                raise ValueError(f"Unknown label: {value}")
        return np.array(encoded)

    def inverse_transform(self, values):
        decoded = []
        for value in values:
            if value == 0:
                decoded.append("Team A")
            elif value == 1:
                decoded.append("Team B")
            else:
                decoded.append(np.nan)
        return np.array(decoded, dtype=object)


class _DummyClassifier:
    def predict_proba(self, X):
        return np.array([[0.7, 0.3] for _ in range(len(X))])

    def predict(self, X):
        return np.array([index % 2 for index in range(len(X))])


def _build_create_instance_service(storage, mock_duckdb_service, mock_local_artifacts):
    mock_duckdb_service.get_all_instances.return_value = {}
    mock_local_artifacts.save_model.return_value = "models/1/model_0.joblib"
    mock_local_artifacts.load_model.return_value = _DummyClassifier()

    return ActiveLearningService(
        storage,
        duckdb_service=mock_duckdb_service,
        local_artifacts_store=mock_local_artifacts,
    )


class TestGetInstanceInfo:
    def test_get_instance_info_combines_storage_duckdb_and_minio(self, storage, mock_duckdb_service):
        """Test that instance info includes metrics, creation time, and train dataset names."""
        storage.results_dict[7] = {
            "mean_entropies": [0.42],
            "f1_scores": [0.91],
            "num_labeled": [12],
        }

        mock_duckdb_service.load_al_instance.return_value = {
            "created_at": "2026-05-01T12:34:56",
        }

        mock_minio_service = MagicMock()
        mock_minio_service.return_data_names.return_value = [
            "datasets/train/User_Request_last_team_ANON_20240101T120000.xlsx",
            "datasets/train/User_Request_last_team_ANON_20240115T090000.xlsx",
        ]

        service = ActiveLearningService(
            storage,
            duckdb_service=mock_duckdb_service,
            minio_service=mock_minio_service,
        )

        info = service.get_instance_info(7)

        assert info["mean_entropies"] == [0.42]
        assert info["f1_scores"] == [0.91]
        assert info["num_labeled"] == [12]
        assert info["created_at"] == "2026-05-01T12:34:56"
        assert info["train_datasets_minio"] == [
            "datasets/train/User_Request_last_team_ANON_20240101T120000.xlsx",
            "datasets/train/User_Request_last_team_ANON_20240115T090000.xlsx",
        ]
        mock_duckdb_service.load_al_instance.assert_called_once_with(7)
        mock_minio_service.return_data_names.assert_called_once_with("train")


class TestCreateInstance:
    def test_create_instance_rejects_fewer_than_50_labeled_rows(self, storage, mock_duckdb_service, mock_local_artifacts, monkeypatch):
        empty_value = _FakeLabelEncoder().transform([np.nan])[0]

        def fake_dispatch_team(duckdb_service, test_set=False, le=None, oh=None, classes=None):
            if not test_set:
                refs = [f"T{i:03d}" for i in range(50)]
                x_train = pd.DataFrame([[i, i + 1] for i in range(50)], index=refs)
                y_train = pd.Series([0] * 49 + [empty_value], index=refs)
                return x_train, y_train, _FakeLabelEncoder(), MagicMock()

            x_test = pd.DataFrame([[1, 2]], index=["S001"])
            y_test = pd.Series(["Team A"], index=["S001"])
            return x_test, y_test, _FakeLabelEncoder(), MagicMock()

        monkeypatch.setattr("app.services.active_learning_svc.dispatch_team", fake_dispatch_team)
        service = _build_create_instance_service(storage, mock_duckdb_service, mock_local_artifacts)

        new_instance = NewInstance(
            model_name="svm",
            qs_strategy="random sampling",
            class_list=["Team A", "Team B"],
        )

        with pytest.raises(ValueError, match="at least 50 labeled instances"):
            service.create_instance(new_instance)

        assert storage.al_instances_dict == {}
        assert storage.dataset_dict == {}
        assert storage.model_paths_dict == {}
        assert storage.results_dict == {}
        mock_duckdb_service.save_al_instance.assert_not_called()
        mock_local_artifacts.save_model.assert_not_called()

    def test_create_instance_trains_and_populates_metrics(self, storage, mock_duckdb_service, mock_local_artifacts, monkeypatch):
        def fake_dispatch_team(duckdb_service, test_set=False, le=None, oh=None, classes=None):
            if not test_set:
                refs = [f"T{i:03d}" for i in range(50)]
                x_train = pd.DataFrame([[i, i + 1] for i in range(50)], index=refs)
                y_train = pd.Series([0 if i % 2 == 0 else 1 for i in range(50)], index=refs)
                return x_train, y_train, _FakeLabelEncoder(), MagicMock()

            x_test = pd.DataFrame([[1, 2], [3, 4]], index=["S001", "S002"])
            y_test = pd.Series(["Team A", "Team B"], index=["S001", "S002"])
            return x_test, y_test, _FakeLabelEncoder(), MagicMock()

        monkeypatch.setattr("app.services.active_learning_svc.dispatch_team", fake_dispatch_team)
        service = _build_create_instance_service(storage, mock_duckdb_service, mock_local_artifacts)

        new_instance = NewInstance(
            model_name="svm",
            qs_strategy="random sampling",
            class_list=["Team A", "Team B"],
        )

        instance_id = service.create_instance(new_instance)

        assert instance_id == 1
        assert instance_id in storage.al_instances_dict
        assert instance_id in storage.dataset_dict
        assert instance_id in storage.model_paths_dict
        assert instance_id in storage.results_dict
        assert storage.model_paths_dict[instance_id][0] == "models/1/model_0.joblib"
        assert len(storage.results_dict[instance_id]["mean_entropies"]) == 1
        assert len(storage.results_dict[instance_id]["f1_scores"]) == 1
        assert len(storage.results_dict[instance_id]["num_labeled"]) == 1
        mock_duckdb_service.save_al_instance.assert_called_once()
        mock_duckdb_service.save_model_path.assert_called_once()
        mock_duckdb_service.save_metrics.assert_called_once()
        mock_local_artifacts.save_model.assert_called_once()
        mock_local_artifacts.load_model.assert_called_once_with(instance_id, 0)

    def test_create_instance_stores_user_id(self, storage, mock_duckdb_service, mock_local_artifacts, monkeypatch):
        custom_user_id = "11111111-1111-1111-1111-111111111111"

        def fake_dispatch_team(duckdb_service, test_set=False, le=None, oh=None, classes=None):
            if not test_set:
                refs = [f"T{i:03d}" for i in range(50)]
                x_train = pd.DataFrame([[i, i + 1] for i in range(50)], index=refs)
                y_train = pd.Series([0 if i % 2 == 0 else 1 for i in range(50)], index=refs)
                return x_train, y_train, _FakeLabelEncoder(), MagicMock()

            x_test = pd.DataFrame([[1, 2], [3, 4]], index=["S001", "S002"])
            y_test = pd.Series(["Team A", "Team B"], index=["S001", "S002"])
            return x_test, y_test, _FakeLabelEncoder(), MagicMock()

        monkeypatch.setattr("app.services.active_learning_svc.dispatch_team", fake_dispatch_team)
        service = _build_create_instance_service(storage, mock_duckdb_service, mock_local_artifacts)

        new_instance = NewInstance(
            model_name="svm",
            qs_strategy="random sampling",
            class_list=["Team A", "Team B"],
        )

        instance_id = service.create_instance(new_instance, user_id=custom_user_id)

        assert storage.al_instances_dict[instance_id]["user_id"] == custom_user_id
        mock_duckdb_service.save_al_instance.assert_called_once()
        assert mock_duckdb_service.save_al_instance.call_args.kwargs["user_id"] == custom_user_id

    def test_create_instance_ignores_optional_data_paths(self, storage, mock_duckdb_service, mock_local_artifacts, monkeypatch):
        """Deprecated train_data_path / test_data_path are accepted but ignored."""
        def fake_dispatch_team(duckdb_service, test_set=False, le=None, oh=None, classes=None):
            if not test_set:
                refs = [f"T{i:03d}" for i in range(50)]
                x_train = pd.DataFrame([[i, i + 1] for i in range(50)], index=refs)
                y_train = pd.Series([0 if i % 2 == 0 else 1 for i in range(50)], index=refs)
                return x_train, y_train, _FakeLabelEncoder(), MagicMock()

            x_test = pd.DataFrame([[1, 2], [3, 4]], index=["S001", "S002"])
            y_test = pd.Series(["Team A", "Team B"], index=["S001", "S002"])
            return x_test, y_test, _FakeLabelEncoder(), MagicMock()

        monkeypatch.setattr("app.services.active_learning_svc.dispatch_team", fake_dispatch_team)
        service = _build_create_instance_service(storage, mock_duckdb_service, mock_local_artifacts)

        new_instance = NewInstance(
            model_name="svm",
            qs_strategy="random sampling",
            class_list=["Team A", "Team B"],
            train_data_path="legacy-train.csv",
            test_data_path="legacy-test.csv",
        )

        instance_id = service.create_instance(new_instance)

        assert instance_id == 1
        assert "train_data_path" not in storage.dataset_dict[instance_id]
        assert "test_data_path" not in storage.dataset_dict[instance_id]
        mock_duckdb_service.save_al_instance.assert_called_once()


class TestLabelInstanceLogging:
    def test_label_instance_logs_and_triggers_export(self, storage):
        duckdb_service = MagicMock(spec=DuckDbPersistenceService)
        local_artifacts = MagicMock(spec=LocalArtifactsStore)
        minio_service = MagicMock()
        benchmarking_service = MagicMock()

        storage.al_instances_dict[1] = {
            "model_name": "svm",
            "qs": "random sampling",
            "classes": [0, 1],
        }
        le_mock = MagicMock()
        le_mock.classes_ = np.array(["Team A", "Team B"], dtype=object)
        le_mock.transform.return_value = np.array([0])
        storage.dataset_dict[1] = {
            "y_train": pd.Series([np.nan], index=["T001"]),
            "le": le_mock,
            "oh": MagicMock(),
            "X_train": pd.DataFrame(),
            "X_test": pd.DataFrame(),
        }

        service = ActiveLearningService(
            storage,
            duckdb_service=duckdb_service,
            local_artifacts_store=local_artifacts,
            minio_service=minio_service,
            benchmarking_service=benchmarking_service,
        )

        service.label_instance(1, LabelRequest(query_idx=["T001"], labels=["Team A"]))

        duckdb_service.save_labels.assert_called_once()
        assert duckdb_service.save_labels.call_args.kwargs["labels_dict"] == {"T001": "Team A"}
        minio_service.save_labels.assert_called_once()

    def test_label_instance_rejects_unknown_labels(self, storage):
        duckdb_service = MagicMock(spec=DuckDbPersistenceService)

        storage.al_instances_dict[1] = {
            "model_name": "svm",
            "qs": "random sampling",
            "classes": [0, 1],
        }
        le_mock = MagicMock()
        le_mock.classes_ = np.array(["Team A", "Team B"], dtype=object)
        storage.dataset_dict[1] = {
            "y_train": pd.Series([np.nan], index=["T001"]),
            "le": le_mock,
            "oh": MagicMock(),
            "X_train": pd.DataFrame(),
            "X_test": pd.DataFrame(),
        }

        service = ActiveLearningService(
            storage,
            duckdb_service=duckdb_service,
            local_artifacts_store=MagicMock(spec=LocalArtifactsStore),
        )

        with pytest.raises(ValueError, match="Unknown labels"):
            service.label_instance(1, LabelRequest(query_idx=["T001"], labels=["team_a"]))

    def test_label_with_info_logs_events_and_exports_once(self, storage):
        duckdb_service = MagicMock(spec=DuckDbPersistenceService)
        local_artifacts = MagicMock(spec=LocalArtifactsStore)
        minio_service = MagicMock()
        benchmarking_service = MagicMock()

        storage.al_instances_dict[1] = {
            "model_name": "svm",
            "qs": "random sampling",
            "classes": [0, 1],
        }
        label_encoder = LabelEncoder().fit(["Hardware", "Network"])
        storage.dataset_dict[1] = {
            "y_train": pd.Series([np.nan, np.nan], index=["T001", "T002"]),
            "le": label_encoder,
            "oh": MagicMock(),
            "X_train": pd.DataFrame(),
            "X_test": pd.DataFrame(),
        }

        service = ActiveLearningService(
            storage,
            duckdb_service=duckdb_service,
            local_artifacts_store=local_artifacts,
            minio_service=minio_service,
            benchmarking_service=benchmarking_service,
        )

        response = service.label_with_info(
            1,
            [
                LabelInfo(
                    ticket_id="T001",
                    label="Network",
                    model_prediction=None,
                    start_time=pd.Timestamp("2026-05-20T10:00:00"),
                    end_time=pd.Timestamp("2026-05-20T10:00:02"),
                    most_helpful_feature="lime",
                ),
                LabelInfo(
                    ticket_id="T002",
                    label="Hardware",
                    model_prediction="Network",
                    start_time=pd.Timestamp("2026-05-20T10:01:00"),
                    end_time=pd.Timestamp("2026-05-20T10:01:03"),
                ),
            ],
        )

        assert response == {"message": "Labels updated"}
        duckdb_service.save_labels.assert_called_once()
        assert duckdb_service.save_labels.call_args.kwargs["labels_dict"] == {"T001": "Network", "T002": "Hardware"}
        assert [call.kwargs["action"] for call in duckdb_service.log_event.call_args_list] == ["confirm_label", "override_label"]
        assert duckdb_service.upsert_label_decision.call_count == 2

        first_call = duckdb_service.upsert_label_decision.call_args_list[0].kwargs
        assert first_call["ref"] == "T001"
        assert first_call["label"] == "Network"
        assert first_call["labeled_at"] == pd.Timestamp("2026-05-20T10:00:02")
        assert first_call["model_prediction"] is None
        assert first_call["latency_ms"] == 2000
        assert first_call["most_helpful_feature"] == "lime"

        second_call = duckdb_service.upsert_label_decision.call_args_list[1].kwargs
        assert second_call["ref"] == "T002"
        assert second_call["label"] == "Hardware"
        assert second_call["labeled_at"] == pd.Timestamp("2026-05-20T10:01:03")
        assert second_call["model_prediction"] == "Network"
        assert second_call["latency_ms"] == 3000
        assert second_call["most_helpful_feature"] is None
        benchmarking_service.export_if_needed.assert_called_once_with(1, user_id='00000000-0000-0000-0000-000000000000')
        minio_service.save_labels.assert_called_once()

    def test_label_instance_uses_user_id(self, storage):
        duckdb_service = MagicMock(spec=DuckDbPersistenceService)
        local_artifacts = MagicMock(spec=LocalArtifactsStore)
        minio_service = MagicMock()
        custom_user_id = "22222222-2222-2222-2222-222222222222"

        le_mock = MagicMock()
        le_mock.classes_ = np.array(["Team A", "Team B"], dtype=object)
        le_mock.transform.return_value = np.array([0])

        storage.al_instances_dict[1] = {
            "model_name": "svm",
            "qs": "random sampling",
            "classes": [0, 1],
        }
        storage.dataset_dict[1] = {
            "y_train": pd.Series([np.nan], index=["T001"]),
            "le": le_mock,
            "oh": MagicMock(),
            "X_train": pd.DataFrame(),
            "X_test": pd.DataFrame(),
        }

        service = ActiveLearningService(
            storage,
            duckdb_service=duckdb_service,
            local_artifacts_store=local_artifacts,
            minio_service=minio_service,
        )

        service.label_instance(1, LabelRequest(query_idx=["T001"], labels=["Team A"]), user_id=custom_user_id)

        duckdb_service.save_labels.assert_called_once()
        assert duckdb_service.save_labels.call_args.kwargs["user_id"] == custom_user_id


class TestLoadFromPersistence:
    def test_load_from_persistence_empty_instances(self, storage, mock_duckdb_service, mock_local_artifacts):
        """Test that it gracefully handles empty instances."""
        mock_duckdb_service.get_all_instances.return_value = {}
        
        service = ActiveLearningService(
            storage,
            duckdb_service=mock_duckdb_service,
            local_artifacts_store=mock_local_artifacts,
        )
        
        # Should not crash and dictionaries should remain empty
        assert len(storage.al_instances_dict) == 0
        assert len(storage.dataset_dict) == 0

    def test_load_from_persistence_missing_encoders(self, storage, mock_duckdb_service, mock_local_artifacts):
        """Test that it skips instances when encoders are missing."""
        instances = {
            1: {
                "model_name": "svm",
                "qs": "uncertainty sampling entropy",
                "classes": ["A", "B"],
            }
        }
        mock_duckdb_service.get_all_instances.return_value = instances
        mock_local_artifacts.load_encoders.side_effect = FileNotFoundError("Encoders not found")
        
        service = ActiveLearningService(
            storage,
            duckdb_service=mock_duckdb_service,
            local_artifacts_store=mock_local_artifacts,
        )
        
        # Should skip instance 1
        assert 1 not in storage.al_instances_dict
        assert 1 not in storage.dataset_dict

    def test_load_from_persistence_missing_vectorized_dataset(self, storage, mock_duckdb_service, mock_local_artifacts):
        """Test that it skips instances when vectorized datasets are missing."""
        instances = {
            1: {
                "model_name": "svm",
                "qs": "uncertainty sampling entropy",
                "classes": ["A", "B"],
            }
        }
        mock_duckdb_service.get_all_instances.return_value = instances
        
        le_mock = MagicMock()
        oh_mock = MagicMock()
        mock_local_artifacts.load_encoders.return_value = (le_mock, oh_mock)
        mock_local_artifacts.load_vectorized_dataset.side_effect = FileNotFoundError("Dataset not found")
        
        service = ActiveLearningService(
            storage,
            duckdb_service=mock_duckdb_service,
            local_artifacts_store=mock_local_artifacts,
        )
        
        # Should skip instance 1
        assert 1 not in storage.al_instances_dict

    def test_load_from_persistence_invalid_model(self, storage, mock_duckdb_service, mock_local_artifacts):
        """Test that it skips instances with invalid model names."""
        instances = {
            1: {
                "model_name": "InvalidModel",
                "qs": "entropy",
                "classes": ["A", "B"],
            }
        }
        mock_duckdb_service.get_all_instances.return_value = instances
        
        service = ActiveLearningService(
            storage,
            duckdb_service=mock_duckdb_service,
            local_artifacts_store=mock_local_artifacts,
        )
        
        # Should skip instance 1 (model not in model_dict)
        assert 1 not in storage.al_instances_dict

    def test_load_from_persistence_invalid_qs(self, storage, mock_duckdb_service, mock_local_artifacts):
        """Test that it skips instances with invalid query strategies."""
        instances = {
            1: {
                "model_name": "svm",
                "qs": "invalid_strategy",
                "classes": ["A", "B"],
            }
        }
        mock_duckdb_service.get_all_instances.return_value = instances
        
        service = ActiveLearningService(
            storage,
            duckdb_service=mock_duckdb_service,
            local_artifacts_store=mock_local_artifacts,
        )
        
        # Should skip instance 1 (qs not in qs_dict)
        assert 1 not in storage.al_instances_dict

    def test_load_from_persistence_full_success(self, storage, mock_duckdb_service, mock_local_artifacts):
        """Test successful loading of a complete instance."""
        instances = {
            1: {
                "model_name": "svm",
                "qs": "uncertainty sampling entropy",
                "classes": ["A", "B", "C"],
            }
        }
        mock_duckdb_service.get_all_instances.return_value = instances
        
        # Mock encoders with transform that encodes labels
        le_mock = MagicMock()
        oh_mock = MagicMock()
        le_mock.classes_ = np.array(["A", "B", "C"], dtype=object)
        le_mock.transform = MagicMock(side_effect=lambda x: np.array([0 if val == "A" else 1 if val == "B" else 2 for val in x]))
        mock_local_artifacts.load_encoders.return_value = (le_mock, oh_mock)
        
        # Mock vectorized datasets
        X_train = pd.DataFrame(
            [[1, 2], [3, 4], [5, 6]],
            index=["T001", "T002", "T003"],
            columns=["feat1", "feat2"],
        )
        X_test = pd.DataFrame(
            [[7, 8]],
            index=["T004"],
            columns=["feat1", "feat2"],
        )
        mock_local_artifacts.load_vectorized_dataset.side_effect = [X_train, X_test]
        
        # Mock labels (original string labels from DB)
        y_train_labels = pd.Series(
            ["A", "B", "A"],
            index=["T001", "T002", "T003"],
        )
        y_test_labels = pd.Series([], dtype=object)
        mock_duckdb_service.load_labels.side_effect = [y_train_labels, y_test_labels]
        
        # Mock metrics
        mock_duckdb_service.load_all_metrics.return_value = [
            {"iteration_id": 1, "f1_score": 0.75, "mean_entropy": 0.5, "num_labeled": 2},
            {"iteration_id": 2, "f1_score": 0.85, "mean_entropy": 0.3, "num_labeled": 3},
        ]
        
        # Mock model paths
        mock_duckdb_service.load_model_paths.return_value = {1: "models/1/model_1.joblib"}
        
        service = ActiveLearningService(
            storage,
            duckdb_service=mock_duckdb_service,
            local_artifacts_store=mock_local_artifacts,
        )
        
        # Verify instance was loaded
        assert 1 in storage.al_instances_dict
        assert storage.al_instances_dict[1]["model_name"] == "svm"
        assert storage.al_instances_dict[1]["qs"] == "uncertainty sampling entropy"
        
        # Verify dataset was loaded
        assert 1 in storage.dataset_dict
        assert len(storage.dataset_dict[1]["X_train"]) == 3
        assert len(storage.dataset_dict[1]["X_test"]) == 1
        
        # Verify labels were encoded and aligned
        assert list(storage.dataset_dict[1]["y_train"].index) == ["T001", "T002", "T003"]
        assert storage.dataset_dict[1]["y_train"].loc["T001"] == 0  # "A" encoded as 0
        assert storage.dataset_dict[1]["y_train"].loc["T002"] == 1  # "B" encoded as 1
        
        # Verify metrics were loaded
        assert 1 in storage.results_dict
        assert len(storage.results_dict[1]["f1_scores"]) == 2
        assert storage.results_dict[1]["f1_scores"][0] == 0.75
        
        # Verify model paths were loaded
        assert 1 in storage.model_paths_dict
        assert storage.model_paths_dict[1][1] == "models/1/model_1.joblib"

    def test_load_from_persistence_labels_alignment(self, storage, mock_duckdb_service, mock_local_artifacts):
        """Test that labels are properly aligned to X_train/X_test indices."""
        instances = {
            1: {
                "model_name": "svm",
                "qs": "uncertainty sampling entropy",
                "classes": ["A", "B"],
            }
        }
        mock_duckdb_service.get_all_instances.return_value = instances
        
        le_mock = MagicMock()
        oh_mock = MagicMock()
        le_mock.classes_ = np.array(["A", "B"], dtype=object)

        def encode_labels(values):
            return np.array([
                0 if val == "A" else 1 if val == "B" else 2
                for val in values
            ])

        le_mock.transform = MagicMock(side_effect=encode_labels)
        mock_local_artifacts.load_encoders.return_value = (le_mock, oh_mock)
        
        # Mock datasets with specific indices
        X_train = pd.DataFrame(
            [[1, 2], [3, 4], [5, 6], [7, 8]],
            index=["T001", "T002", "T003", "T004"],
            columns=["feat1", "feat2"],
        )
        X_test = pd.DataFrame(
            [[9, 10]],
            index=["T005"],
            columns=["feat1", "feat2"],
        )
        mock_local_artifacts.load_vectorized_dataset.side_effect = [X_train, X_test]
        
        # Mock partial labels (missing T004)
        y_train_labels = pd.Series(
            ["A", "B", "A"],
            index=["T001", "T002", "T003"],
        )
        y_test_labels = pd.Series([], dtype=object)
        mock_duckdb_service.load_labels.side_effect = [y_train_labels, y_test_labels]
        
        mock_duckdb_service.load_all_metrics.return_value = []
        mock_duckdb_service.load_model_paths.return_value = {}
        
        service = ActiveLearningService(
            storage,
            duckdb_service=mock_duckdb_service,
            local_artifacts_store=mock_local_artifacts,
        )
        
        y_train = storage.dataset_dict[1]["y_train"]
        y_test = storage.dataset_dict[1]["y_test"]
        
        # Should have encoded labels for T001, T002, T003
        assert y_train.loc["T001"] == 0  # "A" encoded as 0
        assert y_train.loc["T002"] == 1  # "B" encoded as 1
        assert y_train.loc["T003"] == 0  # "A" encoded as 0
        
        # T004 should be filled with MISSING_LABEL (from fill_missing parameter)
        assert pd.isna(y_train.loc["T004"])
        
        # Test set should be filled with np.nan (from fill_missing parameter)
        assert len(y_test) == 1
        assert pd.isna(y_test.loc["T005"])

    def test_load_from_persistence_multiple_instances(self, storage, mock_duckdb_service, mock_local_artifacts):
        """Test loading multiple instances."""
        instances = {
            1: {
                "model_name": "svm",
                "qs": "uncertainty sampling entropy",
                "classes": ["A", "B"],
            },
            2: {
                "model_name": "random forest",
                "qs": "uncertainty sampling margin sampling",
                "classes": ["X", "Y"],
            },
        }
        mock_duckdb_service.get_all_instances.return_value = instances
        
        le_mock = MagicMock()
        oh_mock = MagicMock()
        le_mock.classes_ = np.array(["A", "B"], dtype=object)
        le_mock.transform = MagicMock(side_effect=lambda x: np.array([0 if val == "A" else 1 for val in x]))
        mock_local_artifacts.load_encoders.return_value = (le_mock, oh_mock)
        
        X_train = pd.DataFrame([[1, 2]], index=["T001"], columns=["feat1", "feat2"])
        X_test = pd.DataFrame([[3, 4]], index=["T002"], columns=["feat1", "feat2"])
        mock_local_artifacts.load_vectorized_dataset.side_effect = [
            X_train, X_test,  # For instance 1
            X_train, X_test,  # For instance 2
        ]
        
        y_labels = pd.Series(["A"], index=["T001"])
        mock_duckdb_service.load_labels.side_effect = [
            y_labels, pd.Series([], dtype=object),  # For instance 1
            y_labels, pd.Series([], dtype=object),  # For instance 2
        ]
        
        mock_duckdb_service.load_all_metrics.return_value = []
        mock_duckdb_service.load_model_paths.return_value = {}
        
        service = ActiveLearningService(
            storage,
            duckdb_service=mock_duckdb_service,
            local_artifacts_store=mock_local_artifacts,
        )
        
        # Both instances should be loaded
        assert 1 in storage.al_instances_dict
        assert 2 in storage.al_instances_dict
        assert 1 in storage.dataset_dict
        assert 2 in storage.dataset_dict


class TestDelegation:
    @pytest.fixture
    def storage(self):
        return ActiveLearningStorage()

    @pytest.fixture
    def mock_duckdb_service(self):
        return MagicMock(spec=DuckDbPersistenceService)

    @pytest.fixture
    def mock_local_artifacts(self):
        return MagicMock(spec=LocalArtifactsStore)

    @pytest.fixture
    def mock_minio_service(self):
        return MagicMock(spec=MinioService)

    def _build_service(self, storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service):
        mock_duckdb_service.get_all_instances.return_value = {}
        return ActiveLearningService(
            storage,
            duckdb_service=mock_duckdb_service,
            local_artifacts_store=mock_local_artifacts,
            minio_service=mock_minio_service,
        )

    def test_delegate_rejects_nonexistent_instance(self, storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service):
        service = self._build_service(storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service)
        with pytest.raises(ValueError, match="Instance 999 not found"):
            service.delegate_instance(al_instance_id=999, delegate_username="bob", owner_user_id="owner-uuid")

    def test_delegate_rejects_non_owner(self, storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service):
        storage.al_instances_dict[1] = {"user_id": "alice-uuid", "model_name": "rf", "qs": "random", "classes": [0, 1]}
        service = self._build_service(storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service)
        with pytest.raises(ValueError, match="Only the instance owner"):
            service.delegate_instance(al_instance_id=1, delegate_username="bob", owner_user_id="mallory-uuid")

    def test_delegate_rejects_nonexistent_user(self, storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service):
        storage.al_instances_dict[1] = {"user_id": "alice-uuid", "model_name": "rf", "qs": "random", "classes": [0, 1]}
        mock_duckdb_service.get_user_by_username.return_value = None
        service = self._build_service(storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service)
        with pytest.raises(ValueError, match="User 'nonexistent' not found"):
            service.delegate_instance(al_instance_id=1, delegate_username="nonexistent", owner_user_id="alice-uuid")

    def test_delegate_rejects_self_delegation(self, storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service):
        storage.al_instances_dict[1] = {"user_id": "alice-uuid", "model_name": "rf", "qs": "random", "classes": [0, 1]}
        mock_duckdb_service.get_user_by_username.return_value = {"user_id": "alice-uuid", "username": "alice"}
        service = self._build_service(storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service)
        with pytest.raises(ValueError, match="Cannot delegate to yourself"):
            service.delegate_instance(al_instance_id=1, delegate_username="alice", owner_user_id="alice-uuid")

    def test_delegate_success(self, storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service):
        storage.al_instances_dict[1] = {"user_id": "alice-uuid", "model_name": "rf", "qs": "random", "classes": [0, 1]}
        mock_duckdb_service.get_user_by_username.return_value = {"user_id": "bob-uuid", "username": "bob"}
        mock_duckdb_service.get_delegates_for_instance.return_value = [
            {"delegate_user_id": "bob-uuid", "username": "bob", "granted_by": "alice-uuid", "granted_at": datetime.now()}
        ]
        service = self._build_service(storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service)
        result = service.delegate_instance(al_instance_id=1, delegate_username="bob", owner_user_id="alice-uuid")
        assert result["username"] == "bob"
        mock_duckdb_service.delegate_instance.assert_called_once()
        mock_duckdb_service.log_event.assert_called_once()

    def test_revoke_rejects_non_owner(self, storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service):
        storage.al_instances_dict[1] = {"user_id": "alice-uuid", "model_name": "rf", "qs": "random", "classes": [0, 1]}
        service = self._build_service(storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service)
        with pytest.raises(ValueError, match="Only the instance owner"):
            service.revoke_delegation(al_instance_id=1, delegate_username="bob", owner_user_id="mallory-uuid")

    def test_revoke_success(self, storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service):
        storage.al_instances_dict[1] = {"user_id": "alice-uuid", "model_name": "rf", "qs": "random", "classes": [0, 1]}
        mock_duckdb_service.get_user_by_username.return_value = {"user_id": "bob-uuid", "username": "bob"}
        service = self._build_service(storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service)
        service.revoke_delegation(al_instance_id=1, delegate_username="bob", owner_user_id="alice-uuid")
        mock_duckdb_service.revoke_delegation.assert_called_once()
        mock_duckdb_service.log_event.assert_called_once()

    def test_get_delegates_rejects_non_owner(self, storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service):
        storage.al_instances_dict[1] = {"user_id": "alice-uuid", "model_name": "rf", "qs": "random", "classes": [0, 1]}
        service = self._build_service(storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service)
        with pytest.raises(ValueError, match="Only the instance owner"):
            service.get_delegates(al_instance_id=1, owner_user_id="mallory-uuid")

    def test_get_delegates_success(self, storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service):
        storage.al_instances_dict[1] = {"user_id": "alice-uuid", "model_name": "rf", "qs": "random", "classes": [0, 1]}
        mock_duckdb_service.get_delegates_for_instance.return_value = [
            {"delegate_user_id": "bob-uuid", "username": "bob", "granted_by": "alice-uuid", "granted_at": datetime.now()}
        ]
        service = self._build_service(storage, mock_duckdb_service, mock_local_artifacts, mock_minio_service)
        delegates = service.get_delegates(al_instance_id=1, owner_user_id="alice-uuid")
        assert len(delegates) == 1
        assert delegates[0]["username"] == "bob"
