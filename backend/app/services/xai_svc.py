from app.core.storage import ActiveLearningStorage
from app.services.inference_svc import InferenceService
from lime.lime_text import LimeTextExplainer
from app.services.data_preprocessing import inference
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.data_models.active_learning_dm import Data
from sentence_transformers import SentenceTransformer

class XaiService:
    def __init__(self, storage: ActiveLearningStorage, inference_service: InferenceService):
        self.storage = storage
        self.inference_service = inference_service
        self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")

    def explain_lime(self, al_instance_id: int, tickets: list[Data], model_id: int = 0):
        """
        This function returns a Lime explanation for the texts.
        """
        le = self.storage.dataset_dict[al_instance_id]['le']
        lime_explainer = LimeTextExplainer(class_names = le.classes_)
        lime_explanation_outputs = []

        for ticket in tickets:
            try:
                def _predict_probabilities_wrapper(texts):
                    return self._predict_probabilities(al_instance_id=al_instance_id, texts=texts, ticket=ticket, model_id=model_id)

                # Predict the class of the ticket

                pred_class_idx = le.transform(self.inference_service.infer(al_instance_id=al_instance_id, X=ticket, model_id=model_id))[0]
                
                # Extract the text of the ticket (Title + Description)
                text = (ticket.title_anon or "") + " " + (ticket.description_anon or "")

                # Explain instance for the predicted class
                lime_explanation = lime_explainer.explain_instance(
                    text,
                    _predict_probabilities_wrapper,
                    num_features=10,
                    num_samples=1000,
                    labels=(pred_class_idx,) # Explain only the predicted class index
                )
                # Extract (word, weight) pairs
                lime_explanation_outputs.append({
                    "top_words": [(w, float(s)) for w, s in lime_explanation.as_list(label=pred_class_idx)],
                    "error": None
                })
            except Exception as e:
                lime_explanation_outputs.append({
                    "top_words": [],
                    "error": f"LIME error: {str(e)}"
                })
        
        return lime_explanation_outputs

    def find_nearest_by_ticket(self, al_instance_id: int, ticket: Data, model_id: int = 0):
        """
        This function finds the nearest already labeled ticket to the given ticket.
        """
        target_embedding = 
            
        similarities = cosine_similarity(target_embedding, X_labeled.values)
    
        nearest_neighbor_idx_in_labeled = np.argmax(similarities[0])
    
        # --- Retrieve neighbor info ---
        neighbor_internal_idx = labeled_indices_internal[nearest_neighbor_idx_in_labeled]
        neighbor_original_ref_id = index_dict_train[neighbor_internal_idx]
    
        # Retrieve neighbor's true label (float)
        y_labeled_encoded_array = y_labeled_encoded.to_numpy()
        neighbor_true_label_encoded_float = y_labeled_encoded_array[nearest_neighbor_idx_in_labeled]
    
        # --- FIX: Convert float label to integer ---
        # Add check for NaN or other non-finite values if MISSING_LABEL could be NaN
        if np.isfinite(neighbor_true_label_encoded_float):
            neighbor_true_label_encoded_int = int(neighbor_true_label_encoded_float) # Cast to int
        else:
            # Handle case where the nearest neighbor somehow has MISSING_LABEL
            # This shouldn't happen if we indexed y_labeled_encoded correctly, but safety check
            print(f"Warning: Nearest neighbor {neighbor_original_ref_id} has non-finite label value: {neighbor_true_label_encoded_float}")
            neighbor_true_label_encoded_int = -1 # Or some indicator value
    
        # Check if the integer index is valid for the LabelEncoder classes
        if 0 <= neighbor_true_label_encoded_int < len(le.classes_):
            # Convert the integer encoded label back to text
            neighbor_true_label_text = le.inverse_transform([neighbor_true_label_encoded_int])[0]
        else:
            neighbor_true_label_text = "[Invalid Label Index]"
        # --- END FIX ---
    
        similar_example_info = {
            "neighbor_id": neighbor_original_ref_id,
            "true_label": neighbor_true_label_text,
            "similarity_score": float(similarities[0, nearest_neighbor_idx_in_labeled]),
            "error": None
        }
    
        return similar_example_info


    def _predict_probabilities(self, al_instance_id, texts, ticket, model_id: int = 0):
        """
        This function predicts the probabilities of the texts.
        It adds other features to the texts and then predicts the probabilities.
        """

        model_path = self.storage.model_paths_dict[al_instance_id][model_id]
        model = joblib.load(model_path)
        
        le = self.storage.dataset_dict[al_instance_id]['le']
        oh = self.storage.dataset_dict[al_instance_id]['oh']
        
        tickets = self._create_ticket(texts, ticket)
        texts = inference(tickets, le, oh, self.sentence_model)
        
        probabilities = model.predict_proba(texts)
        return probabilities

    def _create_ticket(self, texts, ticket):
        """
        This function creates a ticket from the text and other ticket data.
        """
        tickets = pd.DataFrame({
            'title_anon': texts,
            'description_anon': ["" for _ in range(len(texts))],
            'service_subcategory_name': [ticket.service_subcategory_name for _ in range(len(texts))],
            'service_name': [ticket.service_name for _ in range(len(texts))]
        })
        return tickets