from app.core.storage import ActiveLearningStorage
from app.data_models.active_learning_dm import Data
import pandas as pd
import joblib
from app.services.data_preprocessing import inference
from sentence_transformers import SentenceTransformer
from app.config.config import SENTENCE_TRANSFORMERS_CACHE_DIR, SENTENCE_TRANSFORMERS_MODEL, SENTENCE_TRANSFORMERS_LOCAL_ONLY
from typing import Optional
from app.persistence.local_artifacts import LocalArtifactsStore
from app.persistence.minio_storage import MinioService
from app.persistence.duckdb.service import DuckDbPersistenceService
from app.config.config import SYSTEM_USER_ID
import time

class InferenceService:
    def __init__(
            self, 
            storage: ActiveLearningStorage,
            local_artifacts_store: Optional[LocalArtifactsStore] = None,
            duckdb_service: Optional[DuckDbPersistenceService] = None,
            ):
        self.storage = storage
        self.sentence_model = SentenceTransformer(
            SENTENCE_TRANSFORMERS_MODEL,
            cache_folder=SENTENCE_TRANSFORMERS_CACHE_DIR,
            local_files_only=SENTENCE_TRANSFORMERS_LOCAL_ONLY
        )
        self.local_artifacts_store = local_artifacts_store
        self.duckdb_service = duckdb_service

    def _log_event(self, *, al_instance_id: int, action: str, latency_ms: int, payload: dict, user_id: str = SYSTEM_USER_ID,
                   actor_type: Optional[str] = None, agent: Optional[str] = None, object_id: Optional[str] = None,
                   duration_s: Optional[float] = None, correct: Optional[bool] = None, ai_suggested: Optional[str] = None) -> None:
        if self.duckdb_service is None:
            return

        self.duckdb_service.log_event(
            al_instance_id=al_instance_id,
            user_id=user_id,
            action=action,
            latency_ms=latency_ms,
            payload=payload,
            actor_type=actor_type,
            agent=agent,
            object_id=object_id,
            duration_s=duration_s,
            correct=correct,
            ai_suggested=ai_suggested,
        )

    # Logic for inference
    def infer(self, al_instance_id: int, X: Data | list[Data], model_id: int = 0, user_id: str = SYSTEM_USER_ID, refs: Optional[list[str]] = None):
        start_time = time.perf_counter()
        # Convert Data object(s) to pandas DataFrame
        if isinstance(X, list):
            data_dicts = [item.model_dump() for item in X]
        else:
            data_dicts = [X.model_dump()]

        X = pd.DataFrame(data_dicts)

        # Preprocess the data for inference
        X = inference(
            df=X,
            le=self.storage.dataset_dict[al_instance_id]['le'],
            oh=self.storage.dataset_dict[al_instance_id]['oh'],
            sentence_model=self.sentence_model
        )

        # Load the model
        model = self.local_artifacts_store.load_model(al_instance_id, model_id)

        # Load the label encoder
        le = self.storage.dataset_dict[al_instance_id]['le']

        # Make predictions
        predictions = model.predict(X)
        # Transform the predictions to the original labels
        predictions = le.inverse_transform(predictions)

        predictions_list = predictions.tolist()

        if refs is not None and self.duckdb_service is not None:
            assert len(refs) == len(predictions_list), (
                f"refs/predictions length mismatch: {len(refs)} vs {len(predictions_list)}"
            )
            for ref, pred in zip(refs, predictions_list):
                if ref is None:
                    continue
                self._log_event(
                    al_instance_id=al_instance_id,
                    action="predict",
                    latency_ms=int((time.perf_counter() - start_time) * 1000),
                    actor_type="ai",
                    agent="classifier_model",
                    object_id=str(ref),
                    payload={"prediction": pred},
                    user_id=user_id,
                )

        # Return the predictions
        return predictions_list

    def infer_proba(self, al_instance_id: int, X: Data | list[Data], model_id: int = 0, user_id: str = SYSTEM_USER_ID, refs: Optional[list[str]] = None):
        """Run probability inference for the provided samples.

        Args:
            al_instance_id: Active learning instance id.
            X: Input data instance(s).
            model_id: Model id to load.
            refs: Optional list of ticket refs (one per row of X) for per-ticket event logging.

        Returns:
            dict: Classes list and probability matrix.

        Raises:
            ValueError: If the loaded model does not support predict_proba.
        """
        start_time = time.perf_counter()
        # Convert Data object(s) to pandas DataFrame
        if isinstance(X, list):
            data_dicts = [item.model_dump() for item in X]
        else:
            data_dicts = [X.model_dump()]

        X = pd.DataFrame(data_dicts)

        # Preprocess the data for inference
        X = inference(
            df=X,
            le=self.storage.dataset_dict[al_instance_id]['le'],
            oh=self.storage.dataset_dict[al_instance_id]['oh'],
            sentence_model=self.sentence_model
        )

        # Load the model
        model = self.local_artifacts_store.load_model(al_instance_id, model_id)

        # Load the label encoder
        le = self.storage.dataset_dict[al_instance_id]['le']

        # Make probability predictions
        predict_proba = getattr(model, "predict_proba", None)
        if predict_proba is None:
            raise ValueError("Model does not support predict_proba")

        probabilities = predict_proba(X)
        probabilities = probabilities.tolist() if hasattr(probabilities, "tolist") else probabilities
        classes = le.classes_.tolist() if hasattr(le, "classes_") else []

        if refs is not None and self.duckdb_service is not None:
            assert len(refs) == len(probabilities), (
                f"refs/probabilities length mismatch: {len(refs)} vs {len(probabilities)}"
            )
            for ref, prob_row in zip(refs, probabilities):
                if ref is None:
                    continue
                self._log_event(
                    al_instance_id=al_instance_id,
                    action="predict",
                    latency_ms=int((time.perf_counter() - start_time) * 1000),
                    actor_type="ai",
                    agent="classifier_model",
                    object_id=str(ref),
                    payload={
                        "classes": classes,
                        "probabilities": prob_row,
                    },
                    user_id=user_id,
                )

        return {
            "classes": classes,
            "probabilities": probabilities
        }
        
