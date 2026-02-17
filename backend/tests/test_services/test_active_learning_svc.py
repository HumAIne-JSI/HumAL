"""Tests for ActiveLearningService persistence loading."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from skactiveml.utils import MISSING_LABEL

from app.core.storage import ActiveLearningStorage
from app.persistence.duckdb import DuckDbPersistenceService
from app.persistence.local_artifacts import LocalArtifactsStore
from app.services.active_learning_svc import ActiveLearningService


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
                "train_data_path": "data/train.csv",
                "test_data_path": "data/test.csv",
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
                "train_data_path": "data/train.csv",
                "test_data_path": "data/test.csv",
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
                "train_data_path": "data/train.csv",
                "test_data_path": "data/test.csv",
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
                "train_data_path": "data/train.csv",
                "test_data_path": "data/test.csv",
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

    def test_load_from_persistence_missing_data_paths(self, storage, mock_duckdb_service, mock_local_artifacts):
        """Test that it skips instances when data paths are missing."""
        instances = {
            1: {
                "model_name": "svm",
                "qs": "uncertainty sampling entropy",
                "classes": ["A", "B"],
            }
        }
        mock_duckdb_service.get_all_instances.return_value = instances
        
        service = ActiveLearningService(
            storage,
            duckdb_service=mock_duckdb_service,
            local_artifacts_store=mock_local_artifacts,
        )
        
        # Should skip instance 1 (missing data paths)
        assert 1 not in storage.al_instances_dict
        assert 1 not in storage.dataset_dict

    def test_load_from_persistence_full_success(self, storage, mock_duckdb_service, mock_local_artifacts):
        """Test successful loading of a complete instance."""
        instances = {
            1: {
                "model_name": "svm",
                "qs": "uncertainty sampling entropy",
                "classes": ["A", "B", "C"],
                "train_data_path": "data/train.csv",
                "test_data_path": "data/test.csv",
            }
        }
        mock_duckdb_service.get_all_instances.return_value = instances
        
        # Mock encoders with transform that encodes labels
        le_mock = MagicMock()
        oh_mock = MagicMock()
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
        
        # Verify data paths are stored
        assert storage.dataset_dict[1]["train_data_path"] == "data/train.csv"
        assert storage.dataset_dict[1]["test_data_path"] == "data/test.csv"
        
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
                "train_data_path": "data/train.csv",
                "test_data_path": "data/test.csv",
            }
        }
        mock_duckdb_service.get_all_instances.return_value = instances
        
        le_mock = MagicMock()
        oh_mock = MagicMock()
        le_mock.transform = MagicMock(side_effect=lambda x: np.array([0 if val == "A" else 1 for val in x]))
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
                "train_data_path": "data/train.csv",
                "test_data_path": "data/test.csv",
            },
            2: {
                "model_name": "random forest",
                "qs": "uncertainty sampling margin sampling",
                "classes": ["X", "Y"],
                "train_data_path": "data/train2.csv",
                "test_data_path": "data/test2.csv",
            },
        }
        mock_duckdb_service.get_all_instances.return_value = instances
        
        le_mock = MagicMock()
        oh_mock = MagicMock()
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
