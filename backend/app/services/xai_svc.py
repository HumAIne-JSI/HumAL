from app.core.storage import ActiveLearningStorage
from app.services.inference_svc import InferenceService
from lime.lime_text import LimeTextExplainer
from app.services.data_preprocessing import inference
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from skactiveml.utils import MISSING_LABEL
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

        Returns:
            - nearest_ticket_ref: str
            - nearest_ticket_label: str
            - similarity_score: float
        """
        target_embedding = inference(
            df=pd.DataFrame([ticket.model_dump()]), 
            le=self.storage.dataset_dict[al_instance_id]['le'], 
            oh=self.storage.dataset_dict[al_instance_id]['oh'], 
            sentence_model=self.sentence_model).values

        # Extract the train data that is already labeled
        X_train = self.storage.dataset_dict[al_instance_id]['X_train']
        y_train = self.storage.dataset_dict[al_instance_id]['y_train']
        labeled_mask = y_train.notna() # Check if the label is not missing
        X_labeled = X_train[labeled_mask]

        # Extract the indices of the labeled tickets
        X_labeled_indices = np.where(labeled_mask)[0]
            
        # Get the most similar ticket
        similarities = cosine_similarity(target_embedding, X_labeled.values)
        nearest_ticket_idx = np.argmax(similarities[0])

        # Convert the index to the X_train index
        nearest_ticket_idx_X_train = X_labeled_indices[nearest_ticket_idx]

        # Convert the index to the original reference id (Ref)
        nearest_ticket_ref = self.storage.dataset_dict[al_instance_id]['X_train'].index[nearest_ticket_idx_X_train]

        # Retrieve nearest ticket's true label
        le = self.storage.dataset_dict[al_instance_id]['le']
        nearest_ticket_label = le.inverse_transform([int(y_train[nearest_ticket_idx_X_train])])[0]

        return {
            "nearest_ticket_ref": nearest_ticket_ref,
            "nearest_ticket_label": nearest_ticket_label,
            "similarity_score": float(similarities[0, nearest_ticket_idx])
        }

    def find_nearest_by_query_idx(self, al_instance_id: int, indices: list[int], model_id: int = 0):
        """
        This function finds the nearest already labeled tickets to the tickets given by the indices.

        Returns:
            - nearest_ticket_refs: list[str]
            - nearest_ticket_labels: list[str]
            - similarity_score: list[float]
        """
        # Indices are Ref values; select rows directly
        target_embeddings = self.storage.dataset_dict[al_instance_id]['X_train'].loc[indices].values

        # Extract the train data that is already labeled
        X_train = self.storage.dataset_dict[al_instance_id]['X_train']
        y_train = self.storage.dataset_dict[al_instance_id]['y_train']
        labeled_mask = y_train.notna() # Check if the label is not missing
        X_labeled = X_train[labeled_mask]

        # Extract the indices of the labeled tickets
        X_labeled_indices = np.where(labeled_mask)[0]
            
        # Get the most similar tickets
        similarities = cosine_similarity(target_embeddings, X_labeled.values)
        nearest_ticket_idxs = np.argmax(similarities, axis=1)

        # Convert the indices to the X_train indices
        nearest_ticket_idxs_X_train = X_labeled_indices[nearest_ticket_idxs]

        # Convert the indices to the original reference ids (Ref)
        nearest_ticket_refs = list(self.storage.dataset_dict[al_instance_id]['X_train'].index[nearest_ticket_idxs_X_train])

        # Retrieve nearest tickets' true labels
        le = self.storage.dataset_dict[al_instance_id]['le']
        nearest_ticket_labels = le.inverse_transform([int(y_train[idx]) for idx in nearest_ticket_idxs_X_train]).tolist()
        similarity_scores = [similarities[i, nearest_ticket_idxs[i]] for i in range(len(nearest_ticket_idxs))]

        return {
            "nearest_ticket_ref": nearest_ticket_refs,
            "nearest_ticket_label": nearest_ticket_labels,
            "similarity_score": similarity_scores
        }


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