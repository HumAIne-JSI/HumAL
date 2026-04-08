from app.core.storage import ActiveLearningStorage
from app.services.inference_svc import InferenceService
from app.services.ticket_vectorizer_svc import TicketVectorizerService
from lime.lime_text import LimeTextExplainer
from app.services.data_preprocessing import inference
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from skactiveml.utils import MISSING_LABEL
from app.data_models.active_learning_dm import Data
from sentence_transformers import SentenceTransformer
from typing import Optional, Dict, Any
from app.persistence.local_artifacts import LocalArtifactsStore
from app.persistence.duckdb.service import DuckDbPersistenceService
from app.persistence.minio_storage import MinioService
from app.core.rabbitmq_client import RabbitMQClient
import uuid
import app.config.config as config
import os

class XaiService:
    def __init__(
            self, 
            storage: ActiveLearningStorage, 
            inference_service: InferenceService,
            local_artifacts_store: Optional[LocalArtifactsStore] = None,
            minio_service: Optional[MinioService] = None,
            duckdb_service: Optional[DuckDbPersistenceService] = None,
            rabbitmq_client: Optional[RabbitMQClient] = None,
            ticket_vectorizer_service: Optional[TicketVectorizerService] = None
            ):
        self.storage = storage
        self.inference_service = inference_service
        self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.local_artifacts_store = local_artifacts_store
        self.minio_service = minio_service
        self.duckdb_service = duckdb_service
        self.rabbitmq_client = rabbitmq_client
        self.ticket_vectorizer_service = ticket_vectorizer_service

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
        nearest_ticket_label = le.inverse_transform([int(y_train[nearest_ticket_ref])])[0]

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
        nearest_ticket_labels = le.inverse_transform([int(y_train[idx]) for idx in nearest_ticket_refs]).tolist()
        similarity_scores = [similarities[i, nearest_ticket_idxs[i]] for i in range(len(nearest_ticket_idxs))]

        return {
            "nearest_ticket_ref": nearest_ticket_refs,
            "nearest_ticket_label": nearest_ticket_labels,
            "similarity_score": similarity_scores
        }

    async def create_xai_request(self, al_instance_id: int, ticket_data: Data, model_id: int, ticket_ref: Optional[str] = None):
        """Saves the ticket and vectorizer to MinIO.
           If ticket_ref is provided, it uses the ticket_ref as the object name in MinIO,
           otherwise, the minio method generates a sha256 hash.
           It then generates a job_id and saves the XAI request information to the database for tracking."""
        if self.minio_service is None or self.duckdb_service is None:
            raise RuntimeError("XAI request dependencies are not configured")

        ticket_storage_info = self.minio_service.save_ticket_for_xai(
            al_instance_id=al_instance_id,
            X=ticket_data,
            ticket_ref=ticket_ref,
        )

        # Create and save the ticket vectorizer
        vectorizer_path = None
        if self.ticket_vectorizer_service is not None:
            one_hot_encoder = self.storage.dataset_dict[al_instance_id]['oh']
            vectorizer = self.ticket_vectorizer_service.create_vectorizer(
                one_hot_encoder=one_hot_encoder,
            )
            vectorizer_storage_info = self.ticket_vectorizer_service.save_vectorizer(
                al_instance_id=al_instance_id,
                vectorizer=vectorizer,
            )
            vectorizer_path = vectorizer_storage_info["object"]

        job_id = uuid.uuid4()
        
        # Payload for DuckDB (follows schema column names)
        xai_job_duckdb_args = {
            "al_instance_id": al_instance_id,
            "job_id": job_id,
            "model_id": model_id,
            "ticket_ref_or_sha": ticket_storage_info["ticket_sha"],
            "request_ticket_location": ticket_storage_info["object"],
            "request_model_location": config.model_location(al_instance_id, model_id),
            "request_preprocessor_location": vectorizer_path,
            "request_raw_tickets_locations": self.minio_service.return_data_names(config.TEST_SPLIT),
        }

        # Format the payload for RabbitMQ (artifacts nesting; job_id to string; friendly names)
        xai_job_payload = {
            "version": os.getenv("MESSAGE_VERSION", "0.1"),
            "job_id": str(job_id),
            "al_instance_id": al_instance_id,
            "model_id": model_id,
            "ticket_sha": ticket_storage_info["ticket_sha"],
            "artifacts": {
                "ticket": ticket_storage_info["object"],
                "model": config.model_location(al_instance_id, model_id),
                "preprocessor": vectorizer_path,
                "raw_tickets": self.minio_service.return_data_names(config.TEST_SPLIT),
            }
        }

        # Publish the message to RabbitMQ for asynchronous processing
        if self.rabbitmq_client is not None and os.getenv("USE_RABBITMQ", "0") == "1":
            task_queue = os.getenv("TASK_QUEUE")
            if not task_queue:
                raise RuntimeError("TASK_QUEUE is not configured")
            publish_payload = {**xai_job_payload}
            await self.rabbitmq_client.publish(queue_name=task_queue, message=publish_payload)

        self.duckdb_service.create_xai_job(**xai_job_duckdb_args)


        return job_id

    def get_xai_job(self, job_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Retrieve XAI job details by job_id."""
        if self.duckdb_service is None:
            raise RuntimeError("DuckDB service is not configured")
        return self.duckdb_service.get_xai_job(job_id)
    

    async def update_xai_job(self, data: Dict[str, Any]):
        """Update XAI job details in the database.
           This method is called by the worker after processing the XAI request."""
        if self.duckdb_service is None:
            raise RuntimeError("DuckDB service is not configured")
        
        if not {"job_id", "status"}.issubset(data.keys()):
            raise ValueError("Invalid data format for updating XAI job")
        else:
            job_id = data["job_id"]
            if isinstance(job_id, str):
                job_id = uuid.UUID(job_id)
            
            if data["status"] == "completed" and ("result_location" not in data or "result_file_names" not in data):
                raise ValueError("Missing result_location or result_file_names for completed XAI job")

            self.duckdb_service.update_xai_job_status(job_id=job_id,
                                                      status=data["status"],
                                                      result_location=data.get("result_location"),
                                                      result_file_names=data.get("result_file_names"))
        


    def _predict_probabilities(self, al_instance_id, texts, ticket, model_id: int = 0):
        """
        This function predicts the probabilities of the texts.
        It adds other features to the texts and then predicts the probabilities.
        """

        # Load the model
        model = self.local_artifacts_store.load_model(al_instance_id, model_id)
        
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