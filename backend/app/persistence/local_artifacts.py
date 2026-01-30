from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Tuple

import joblib

# Top-level constants
MODELS_BASE_DIR = Path("storage/models")
ENCODERS_BASE_DIR = Path("storage/encoders")
LABEL_ENCODER_FILENAME = "label_encoder.joblib"
ONEHOT_ENCODER_FILENAME = "onehot_encoder.joblib"


@dataclass(frozen=True)
class LocalArtifactsStore:
    models_dir: Path = MODELS_BASE_DIR
    encoders_dir: Path = ENCODERS_BASE_DIR

    def __post_init__(self) -> None:
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.encoders_dir.mkdir(parents=True, exist_ok=True)

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

        joblib.dump(model, model_dir / f"{model_id}.joblib")

    def load_model(self, al_instance_id: int, model_id: int) -> Any:
        model_path = self.models_dir / str(al_instance_id) / f"{model_id}.joblib"
        return joblib.load(model_path)

    def delete_instance_artifacts(self, al_instance_id: int) -> None:
        # Delete encoders
        encoder_dir = self.encoders_dir / str(al_instance_id)
        if encoder_dir.exists():
            for child in encoder_dir.iterdir():
                if child.is_file():
                    child.unlink()
            try:
                encoder_dir.rmdir()
            except OSError:
                pass

        # Delete models
        model_dir = self.models_dir / str(al_instance_id)
        if model_dir.exists():
            for child in model_dir.rglob("*"):
                if child.is_file():
                    child.unlink()
            for child in sorted(model_dir.rglob("*"), reverse=True):
                if child.is_dir():
                    try:
                        child.rmdir()
                    except OSError:
                        pass
            try:
                model_dir.rmdir()
            except OSError:
                pass
