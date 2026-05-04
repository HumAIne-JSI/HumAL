from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Tuple
import logging

import joblib

logger = logging.getLogger(__name__)

# Top-level constants
MODELS_BASE_DIR = Path("storage/models")
ENCODERS_BASE_DIR = Path("storage/encoders")
LABEL_ENCODER_FILENAME = "label_encoder.joblib"
ONEHOT_ENCODER_FILENAME = "onehot_encoder.joblib"
VECTORIZED_DATA_BASE_DIR = Path("storage/vectorized_data")


@dataclass(frozen=True)
class LocalArtifactsStore:
    models_dir: Path = MODELS_BASE_DIR
    encoders_dir: Path = ENCODERS_BASE_DIR
    vectorized_data_dir: Path = VECTORIZED_DATA_BASE_DIR
    def __post_init__(self) -> None:
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.encoders_dir.mkdir(parents=True, exist_ok=True)
        self.vectorized_data_dir.mkdir(parents=True, exist_ok=True)

    def save_encoders(self, al_instance_id: int, label_encoder: Any, one_hot_encoder: Any) -> None:
        encoder_dir = self.encoders_dir / str(al_instance_id)
        encoder_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(label_encoder, encoder_dir / LABEL_ENCODER_FILENAME)
        joblib.dump(one_hot_encoder, encoder_dir / ONEHOT_ENCODER_FILENAME)

    def load_encoders(self, al_instance_id: int) -> Tuple[Any, Any]:
        encoder_dir = self.encoders_dir / str(al_instance_id)

        label_encoder = joblib.load(encoder_dir / LABEL_ENCODER_FILENAME)
        one_hot_encoder = joblib.load(encoder_dir / ONEHOT_ENCODER_FILENAME)

        return label_encoder, one_hot_encoder

    def save_model(self, al_instance_id: int, model_id: int, model: Any) -> None:
        model_dir = self.models_dir / str(al_instance_id)
        model_dir.mkdir(parents=True, exist_ok=True)

        model_path = model_dir / f"{model_id}.joblib"

        joblib.dump(model, model_path)

        return str(model_path)

    def load_model(self, al_instance_id: int, model_id: int) -> Any:
        model_path = self.models_dir / str(al_instance_id) / f"{model_id}.joblib"
        return joblib.load(model_path)

    def save_vectorized_dataset(self, al_instance_id: int, X: Any, split: str) -> None:
        """Save vectorized features for a given split ('train' or 'test')."""
        if split not in ("train", "test"):
            raise ValueError("split must be 'train' or 'test'")
        
        data_dir = self.vectorized_data_dir / str(al_instance_id)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(X, data_dir / f"X_{split}.joblib")

    def load_vectorized_dataset(self, al_instance_id: int, split: str) -> Any:
        """Load vectorized features for a given split ('train' or 'test')."""
        if split not in ("train", "test"):
            raise ValueError("split must be 'train' or 'test'")
        
        data_dir = self.vectorized_data_dir / str(al_instance_id)
        data_path = data_dir / f"X_{split}.joblib"
        
        return joblib.load(data_path)

    def delete_instance_artifacts(self, al_instance_id: int) -> None:
        """Delete all artifacts for an instance. Continues even if some files are missing."""
        logger.info(f"Starting deletion of artifacts for instance {al_instance_id}")
        
        deleted_count = 0
        failed_count = 0
        
        # Delete encoders
        encoder_dir = self.encoders_dir / str(al_instance_id)
        if encoder_dir.exists():
            logger.debug(f"Deleting encoder directory: {encoder_dir}")
            for child in encoder_dir.iterdir():
                if child.is_file():
                    try:
                        child.unlink()
                        logger.debug(f"Deleted encoder file: {child}")
                        deleted_count += 1
                    except OSError as e:
                        logger.warning(f"Failed to delete encoder file {child}: {e}")
                        failed_count += 1
            try:
                encoder_dir.rmdir()
                logger.debug(f"Deleted encoder directory: {encoder_dir}")
                deleted_count += 1
            except OSError as e:
                logger.warning(f"Failed to delete encoder directory {encoder_dir}: {e}")
                failed_count += 1

        # Delete models
        model_dir = self.models_dir / str(al_instance_id)
        if model_dir.exists():
            logger.debug(f"Deleting model directory: {model_dir}")
            for child in model_dir.rglob("*"):
                if child.is_file():
                    try:
                        child.unlink()
                        logger.debug(f"Deleted model file: {child}")
                        deleted_count += 1
                    except OSError as e:
                        logger.warning(f"Failed to delete model file {child}: {e}")
                        failed_count += 1
            for child in sorted(model_dir.rglob("*"), reverse=True):
                if child.is_dir():
                    try:
                        child.rmdir()
                        logger.debug(f"Deleted model subdirectory: {child}")
                        deleted_count += 1
                    except OSError as e:
                        logger.warning(f"Failed to delete model subdirectory {child}: {e}")
                        failed_count += 1
            try:
                model_dir.rmdir()
                logger.debug(f"Deleted model directory: {model_dir}")
                deleted_count += 1
            except OSError as e:
                logger.warning(f"Failed to delete model directory {model_dir}: {e}")
                failed_count += 1

        # Delete vectorized data
        data_dir = self.vectorized_data_dir / str(al_instance_id)
        if data_dir.exists():
            logger.debug(f"Deleting vectorized data directory: {data_dir}")
            for child in data_dir.iterdir():
                if child.is_file():
                    try:
                        child.unlink()
                        logger.debug(f"Deleted vectorized data file: {child}")
                        deleted_count += 1
                    except OSError as e:
                        logger.warning(f"Failed to delete vectorized data file {child}: {e}")
                        failed_count += 1
            try:
                data_dir.rmdir()
                logger.debug(f"Deleted vectorized data directory: {data_dir}")
                deleted_count += 1
            except OSError as e:
                logger.warning(f"Failed to delete vectorized data directory {data_dir}: {e}")
                failed_count += 1
        
        logger.info(f"Completed deletion of artifacts for instance {al_instance_id}: {deleted_count} deleted, {failed_count} failed")