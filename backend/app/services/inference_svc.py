from app.core.storage import ActiveLearningStorage
from app.data_models.active_learning_dm import Data
import pandas as pd
import joblib
from app.services.data_preprocessing import inference
from sentence_transformers import SentenceTransformer

class InferenceService:
    def __init__(self, storage: ActiveLearningStorage):
        self.storage = storage
        self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Logic for inference
    def infer(self, al_instance_id: int, X: Data, model_id: int = 0):
        # Convert Data object to pandas DataFrame with an index
        data_dict = X.model_dump()
        
        # Wrap the dictionary in a list to create a single row DataFrame
        X = pd.DataFrame([data_dict])

        # Preprocess the data for inference
        X = inference(
            df=X, 
            le=self.storage.dataset_dict[al_instance_id]['le'], 
            oh=self.storage.dataset_dict[al_instance_id]['oh'],
            sentence_model=self.sentence_model
        )
        
        # Load the model
        model_path = self.storage.model_paths_dict[al_instance_id][model_id]
        model = joblib.load(model_path)
        # Load the label encoder
        le = self.storage.dataset_dict[al_instance_id]['le']

        # Make predictions
        predictions = model.predict(X)
        # Transform the predictions to the original labels
        predictions = le.inverse_transform(predictions)

        # Return the predictions
        return predictions.tolist()
        
