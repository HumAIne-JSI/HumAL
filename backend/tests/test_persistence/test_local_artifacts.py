"""Tests for local artifacts storage."""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.svm import SVC

from app.persistence.local_artifacts import LocalArtifactsStore


@pytest.fixture
def temp_storage():
    """Create temporary storage directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        store = LocalArtifactsStore(
            models_dir=base / "models",
            encoders_dir=base / "encoders"
        )
        yield store


class TestDirectoryCreation:
    def test_creates_directories_on_init(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            models_dir = base / "custom_models"
            encoders_dir = base / "custom_encoders"
            
            store = LocalArtifactsStore(
                models_dir=models_dir,
                encoders_dir=encoders_dir
            )
            
            assert models_dir.exists()
            assert encoders_dir.exists()

    def test_handles_existing_directories(self, temp_storage):
        # Should not error even if directories exist
        assert temp_storage.models_dir.exists()
        assert temp_storage.encoders_dir.exists()


class TestEncoders:
    def test_save_and_load_label_encoder(self, temp_storage):
        # Create and fit encoder
        label_enc = LabelEncoder()
        label_enc.fit(["ClassA", "ClassB", "ClassC"])
        
        onehot_enc = OneHotEncoder(sparse_output=False)
        onehot_enc.fit([[1], [2], [3]])
        
        # Save
        temp_storage.save_encoders(1, label_enc, onehot_enc)
        
        # Load
        loaded_label, loaded_onehot = temp_storage.load_encoders(1)
        
        # Verify label encoder
        assert list(loaded_label.classes_) == ["ClassA", "ClassB", "ClassC"]
        assert loaded_label.transform(["ClassA"])[0] == 0
        assert loaded_label.transform(["ClassB"])[0] == 1

    def test_save_and_load_onehot_encoder(self, temp_storage):
        label_enc = LabelEncoder()
        label_enc.fit(["A"])
        
        onehot_enc = OneHotEncoder(sparse_output=False)
        onehot_enc.fit([[1], [2], [3], [4]])
        
        temp_storage.save_encoders(2, label_enc, onehot_enc)
        
        _, loaded_onehot = temp_storage.load_encoders(2)
        
        # Verify onehot encoder
        assert loaded_onehot.n_features_in_ == 1
        transformed = loaded_onehot.transform([[1]])
        assert transformed.shape == (1, 4)

    def test_save_encoders_creates_instance_directory(self, temp_storage):
        label_enc = LabelEncoder()
        onehot_enc = OneHotEncoder()
        
        temp_storage.save_encoders(5, label_enc, onehot_enc)
        
        encoder_dir = temp_storage.encoders_dir / "5"
        assert encoder_dir.exists()
        assert (encoder_dir / "label_encoder.joblib").exists()
        assert (encoder_dir / "onehot_encoder.joblib").exists()

    def test_load_encoders_nonexistent_raises(self, temp_storage):
        with pytest.raises(FileNotFoundError):
            temp_storage.load_encoders(999)

    def test_save_encoders_replaces_existing(self, temp_storage):
        # First save
        label_enc1 = LabelEncoder()
        label_enc1.fit(["A", "B"])
        onehot_enc1 = OneHotEncoder()
        
        temp_storage.save_encoders(1, label_enc1, onehot_enc1)
        
        # Second save with different encoder
        label_enc2 = LabelEncoder()
        label_enc2.fit(["X", "Y", "Z"])
        onehot_enc2 = OneHotEncoder()
        
        temp_storage.save_encoders(1, label_enc2, onehot_enc2)
        
        # Load and verify it's the second one
        loaded_label, _ = temp_storage.load_encoders(1)
        assert list(loaded_label.classes_) == ["X", "Y", "Z"]


class TestModels:
    def test_save_and_load_svc_model(self, temp_storage):
        # Create and train model
        model = SVC(kernel="rbf", C=1.0)
        X = [[1, 2], [3, 4], [5, 6], [7, 8]]
        y = [0, 1, 0, 1]
        model.fit(X, y)
        
        # Save
        temp_storage.save_model(al_instance_id=1, model_id=1, model=model)
        
        # Load
        loaded = temp_storage.load_model(al_instance_id=1, model_id=1)
        
        # Verify
        assert isinstance(loaded, SVC)
        assert loaded.kernel == "rbf"
        assert loaded.C == 1.0
        
        # Test prediction works
        predictions = loaded.predict(X)
        assert len(predictions) == 4

    def test_save_and_load_random_forest(self, temp_storage):
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])
        model.fit(X, y)
        
        temp_storage.save_model(2, 5, model)
        
        loaded = temp_storage.load_model(2, 5)
        
        assert isinstance(loaded, RandomForestClassifier)
        assert loaded.n_estimators == 10
        assert loaded.predict([[1, 2]])[0] in [0, 1]

    def test_save_and_load_logistic_regression(self, temp_storage):
        model = LogisticRegression()
        X = [[1, 2], [3, 4], [5, 6], [7, 8]]
        y = [0, 1, 0, 1]
        model.fit(X, y)
        
        temp_storage.save_model(3, 2, model)
        
        loaded = temp_storage.load_model(3, 2)
        
        assert isinstance(loaded, LogisticRegression)
        predictions = loaded.predict(X)
        assert len(predictions) == 4

    def test_save_model_creates_directory(self, temp_storage):
        model = SVC()
        model.fit([[1, 2], [3, 4]], [0, 1])
        
        temp_storage.save_model(10, 1, model)
        
        model_dir = temp_storage.models_dir / "10"
        assert model_dir.exists()
        assert (model_dir / "1.joblib").exists()

    def test_save_multiple_models_same_instance(self, temp_storage):
        model1 = SVC()
        model2 = LogisticRegression()
        model3 = RandomForestClassifier(n_estimators=5)
        
        X = [[1, 2], [3, 4]]
        y = [0, 1]
        
        model1.fit(X, y)
        model2.fit(X, y)
        model3.fit(X, y)
        
        temp_storage.save_model(1, 1, model1)
        temp_storage.save_model(1, 2, model2)
        temp_storage.save_model(1, 3, model3)
        
        loaded1 = temp_storage.load_model(1, 1)
        loaded2 = temp_storage.load_model(1, 2)
        loaded3 = temp_storage.load_model(1, 3)
        
        assert isinstance(loaded1, SVC)
        assert isinstance(loaded2, LogisticRegression)
        assert isinstance(loaded3, RandomForestClassifier)

    def test_load_model_nonexistent_raises(self, temp_storage):
        with pytest.raises(FileNotFoundError):
            temp_storage.load_model(999, 1)

    def test_save_model_replaces_existing(self, temp_storage):
        model1 = SVC(C=1.0)
        model1.fit([[1, 2], [3, 4]], [0, 1])
        temp_storage.save_model(1, 1, model1)
        
        model2 = SVC(C=10.0)
        model2.fit([[5, 6], [7, 8]], [0, 1])
        temp_storage.save_model(1, 1, model2)
        
        loaded = temp_storage.load_model(1, 1)
        assert loaded.C == 10.0


class TestDeletion:
    def test_delete_instance_artifacts_removes_encoders(self, temp_storage):
        label_enc = LabelEncoder()
        onehot_enc = OneHotEncoder()
        
        temp_storage.save_encoders(1, label_enc, onehot_enc)
        
        encoder_dir = temp_storage.encoders_dir / "1"
        assert encoder_dir.exists()
        
        temp_storage.delete_instance_artifacts(1)
        
        assert not encoder_dir.exists()

    def test_delete_instance_artifacts_removes_models(self, temp_storage):
        model = SVC()
        model.fit([[1, 2], [3, 4]], [0, 1])
        
        temp_storage.save_model(1, 1, model)
        temp_storage.save_model(1, 2, model)
        
        model_dir = temp_storage.models_dir / "1"
        assert model_dir.exists()
        
        temp_storage.delete_instance_artifacts(1)
        
        assert not model_dir.exists()

    def test_delete_instance_artifacts_removes_both(self, temp_storage):
        # Add encoders
        label_enc = LabelEncoder()
        onehot_enc = OneHotEncoder()
        temp_storage.save_encoders(5, label_enc, onehot_enc)
        
        # Add models
        model = LogisticRegression()
        model.fit([[1, 2], [3, 4]], [0, 1])
        temp_storage.save_model(5, 1, model)
        
        temp_storage.delete_instance_artifacts(5)
        
        assert not (temp_storage.encoders_dir / "5").exists()
        assert not (temp_storage.models_dir / "5").exists()

    def test_delete_nonexistent_instance_no_error(self, temp_storage):
        # Should not raise an error
        temp_storage.delete_instance_artifacts(999)

    def test_delete_preserves_other_instances(self, temp_storage):
        # Create artifacts for instance 1
        label_enc1 = LabelEncoder()
        onehot_enc1 = OneHotEncoder()
        temp_storage.save_encoders(1, label_enc1, onehot_enc1)
        
        model1 = SVC()
        model1.fit([[1, 2], [3, 4]], [0, 1])
        temp_storage.save_model(1, 1, model1)
        
        # Create artifacts for instance 2
        label_enc2 = LabelEncoder()
        onehot_enc2 = OneHotEncoder()
        temp_storage.save_encoders(2, label_enc2, onehot_enc2)
        
        model2 = SVC()
        model2.fit([[5, 6], [7, 8]], [0, 1])
        temp_storage.save_model(2, 1, model2)
        
        # Delete instance 1
        temp_storage.delete_instance_artifacts(1)
        
        # Verify instance 1 is gone
        assert not (temp_storage.encoders_dir / "1").exists()
        assert not (temp_storage.models_dir / "1").exists()
        
        # Verify instance 2 still exists
        assert (temp_storage.encoders_dir / "2").exists()
        assert (temp_storage.models_dir / "2").exists()
        
        # Verify instance 2 data is intact
        loaded_label, _ = temp_storage.load_encoders(2)
        loaded_model = temp_storage.load_model(2, 1)
        assert loaded_label is not None
        assert loaded_model is not None


class TestEdgeCases:
    def test_save_model_with_nested_subdirectories(self, temp_storage):
        """Test that nested directories in models are handled."""
        model = SVC()
        model.fit([[1, 2], [3, 4]], [0, 1])
        
        # Even though we just save with instance_id and model_id,
        # the structure should work
        temp_storage.save_model(100, 50, model)
        
        assert temp_storage.load_model(100, 50) is not None

    def test_multiple_instances_isolated(self, temp_storage):
        """Test that different AL instances are properly isolated."""
        model1 = SVC(C=1.0)
        model2 = SVC(C=2.0)
        model1.fit([[1, 2], [3, 4]], [0, 1])
        model2.fit([[5, 6], [7, 8]], [0, 1])
        
        temp_storage.save_model(1, 1, model1)
        temp_storage.save_model(2, 1, model2)
        
        loaded1 = temp_storage.load_model(1, 1)
        loaded2 = temp_storage.load_model(2, 1)
        
        assert loaded1.C == 1.0
        assert loaded2.C == 2.0

    def test_encoder_directory_structure(self, temp_storage):
        """Verify the directory structure created for encoders."""
        label_enc = LabelEncoder()
        onehot_enc = OneHotEncoder()
        
        temp_storage.save_encoders(42, label_enc, onehot_enc)
        
        encoder_dir = temp_storage.encoders_dir / "42"
        assert encoder_dir.is_dir()
        assert (encoder_dir / "label_encoder.joblib").is_file()
        assert (encoder_dir / "onehot_encoder.joblib").is_file()

    def test_model_directory_structure(self, temp_storage):
        """Verify the directory structure created for models."""
        model = SVC()
        model.fit([[1, 2], [3, 4]], [0, 1])
        
        temp_storage.save_model(42, 7, model)
        
        model_dir = temp_storage.models_dir / "42"
        assert model_dir.is_dir()
        assert (model_dir / "7.joblib").is_file()
