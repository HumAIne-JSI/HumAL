from app.core.storage import ActiveLearningStorage
from app.data_models.active_learning_dm import InferenceRequest, InferenceResponse
import pandas as pd
import joblib
from app.services.data_preprocessing import inference
from sentence_transformers import SentenceTransformer
from typing import Optional
from app.persistence.local_artifacts import LocalArtifactsStore
from backend.app.config.config import DEFAULT_MODEL_ID

class InferenceService:
    def __init__(
            self, 
            storage: ActiveLearningStorage,
            local_artifacts_store: Optional[LocalArtifactsStore] = None
            ):
        self.storage = storage
        self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.local_artifacts_store = local_artifacts_store

    def infer(self, al_instance_id: int, X: list[InferenceRequest], model_id: int = DEFAULT_MODEL_ID) -> list[InferenceResponse]:
        """Perform inference for a given active learning instance and input data."""

        # convert the list of InferenceRequest objects to a dataframe. Use id as the index.
        X = pd.DataFrame([request.fields for request in X], index=[request.id for request in X])

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
        
