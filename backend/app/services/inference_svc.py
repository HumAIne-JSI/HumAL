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

class InferenceService:
    def __init__(
            self, 
            storage: ActiveLearningStorage,
            local_artifacts_store: Optional[LocalArtifactsStore] = None
            ):
        self.storage = storage
        self.sentence_model = SentenceTransformer(
            SENTENCE_TRANSFORMERS_MODEL,
            cache_folder=SENTENCE_TRANSFORMERS_CACHE_DIR,
            local_files_only=SENTENCE_TRANSFORMERS_LOCAL_ONLY
        )
        self.local_artifacts_store = local_artifacts_store

    # Logic for inference
    def infer(self, al_instance_id: int, X: Data | list[Data], model_id: int = 0):
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

        # Return the predictions
        return predictions.tolist()

    def infer_proba(self, al_instance_id: int, X: Data | list[Data], model_id: int = 0):
        """Run probability inference for the provided samples.

        Args:
            al_instance_id: Active learning instance id.
            X: Input data instance(s).
            model_id: Model id to load.

        Returns:
            dict: Classes list and probability matrix.

        Raises:
            ValueError: If the loaded model does not support predict_proba.
        """
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

        return {
            "classes": classes,
            "probabilities": probabilities
        }
        
