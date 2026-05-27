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
from app.config.config import SENTENCE_TRANSFORMERS_CACHE_DIR, SENTENCE_TRANSFORMERS_MODEL, SENTENCE_TRANSFORMERS_LOCAL_ONLY
from typing import Optional, Dict, Any
from app.persistence.local_artifacts import LocalArtifactsStore
from app.persistence.duckdb.service import DuckDbPersistenceService
from app.persistence.minio_storage import MinioService
from app.core.rabbitmq_client import RabbitMQClient
import uuid
import app.config.config as config
import os
import logging
import time
from app.config.config import SYSTEM_USER_ID

logger = logging.getLogger(__name__)

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
        self.sentence_model = SentenceTransformer(
            SENTENCE_TRANSFORMERS_MODEL,
            cache_folder=SENTENCE_TRANSFORMERS_CACHE_DIR,
            local_files_only=SENTENCE_TRANSFORMERS_LOCAL_ONLY
        )
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

    def find_nearest(self, al_instance_id: int, ticket: Data, top_k: int = 1, distinct_classes: bool = True, model_id: int = 0):
        start_time = time.perf_counter()
        target_embedding = inference(
            df=pd.DataFrame([ticket.model_dump()]), 
            le=self.storage.dataset_dict[al_instance_id]['le'], 
            oh=self.storage.dataset_dict[al_instance_id]['oh'], 
            sentence_model=self.sentence_model
        ).values
        
        target_classes = None
        input_title = ticket.title_anon or ""
        input_description = ticket.description_anon or ""
        
        if distinct_classes:
            try:
                res = self.inference_service.infer_proba(al_instance_id, ticket, model_id)
                probs = res["probabilities"][0]
                classes = res["classes"]
                sorted_class_idx = np.argsort(probs)[::-1]
                target_classes = {classes[i] for i in sorted_class_idx[:top_k]}
            except ValueError:
                # Fallback to standard infer
                preds = self.inference_service.infer(al_instance_id, ticket, model_id)
                target_classes = set(preds)

        results = self._compute_nearest(al_instance_id, target_embedding, top_k, distinct_classes, target_classes, input_title, input_description)

        if self.duckdb_service is not None:
            self.duckdb_service.log_event(
                al_instance_id=al_instance_id,
                user_id=SYSTEM_USER_ID,
                action="similar_tickets",
                latency_ms=int((time.perf_counter() - start_time) * 1000),
                payload={
                    "ticket_id": None,
                    "similar_ids": [item["ref"] for item in results],
                    "similarities": [item["similarity"] for item in results],
                    "top_k": top_k,
                },
            )

            ticket_ref = getattr(ticket, "ref", None)
            if ticket_ref and results:
                sanitized_results = [
                    {key: value for key, value in item.items() if key not in {"title", "description"}}
                    for item in results
                ]
                self.duckdb_service.upsert_label_decision(
                    al_instance_id=al_instance_id,
                    ref=str(ticket_ref),
                    similar_tickets=sanitized_results,
                )

        return results

    def find_nearest_by_idx(self, al_instance_id: int, index: str, top_k: int = 2, distinct_classes: bool = True, model_id: int = 0):
        start_time = time.perf_counter()
        target_embedding = self.storage.dataset_dict[al_instance_id]['X_train'].loc[[index]].values
        
        target_classes = None
        
        query_df = self.duckdb_service.load_tickets_by_ref([index])
        if query_df is not None and not query_df.empty:
            row = query_df.iloc[0]
            input_title = row['Title_anon'] if pd.notna(row['Title_anon']) else ""
            input_description = row['Description_anon'] if pd.notna(row['Description_anon']) else ""
            s_name = row['Service->Name'] if pd.notna(row['Service->Name']) else None
            s_sub = row['Service subcategory->Name'] if pd.notna(row['Service subcategory->Name']) else None
        else:
            input_title, input_description, s_name, s_sub = "", "", None, None

        if distinct_classes:
            ticket_obj = Data(
                title_anon=input_title,
                description_anon=input_description,
                service_name=s_name,
                service_subcategory_name=s_sub
            )
            
            try:
                res = self.inference_service.infer_proba(al_instance_id, ticket_obj, model_id)
                probs = res["probabilities"][0]
                classes = res["classes"]
                sorted_class_idx = np.argsort(probs)[::-1]
                target_classes = {classes[i] for i in sorted_class_idx[:top_k]}
            except ValueError:
                preds = self.inference_service.infer(al_instance_id, ticket_obj, model_id)
                target_classes = set(preds)

        results = self._compute_nearest(al_instance_id, target_embedding, top_k, distinct_classes, target_classes, input_title, input_description)

        if self.duckdb_service is not None:
            self.duckdb_service.log_event(
                al_instance_id=al_instance_id,
                user_id=SYSTEM_USER_ID,
                action="similar_tickets",
                latency_ms=int((time.perf_counter() - start_time) * 1000),
                payload={
                    "ticket_id": str(index),
                    "similar_ids": [item["ref"] for item in results],
                    "similarities": [item["similarity"] for item in results],
                    "top_k": top_k,
                },
            )

            if results:
                sanitized_results = [
                    {key: value for key, value in item.items() if key not in {"title", "description"}}
                    for item in results
                ]
                self.duckdb_service.upsert_label_decision(
                    al_instance_id=al_instance_id, 
                    ref=str(index),
                    similar_tickets=sanitized_results,
                )

        return results

    def _compute_nearest(self, al_instance_id: int, target_embedding, top_k: int, distinct_classes: bool, target_classes: set = None, input_title: str = "", input_description: str = ""):
        import re
        X_train = self.storage.dataset_dict[al_instance_id]['X_train']
        y_train = self.storage.dataset_dict[al_instance_id]['y_train']
        le = self.storage.dataset_dict[al_instance_id]['le']
        
        labeled_mask = y_train.notna()
        X_labeled = X_train[labeled_mask]
        X_labeled_indices = np.where(labeled_mask)[0]
        
        similarities = cosine_similarity(target_embedding, X_labeled.values)[0]
        sorted_sim_indices = np.argsort(similarities)[::-1]
        
        raw_matches = []
        
        if distinct_classes and target_classes is not None:
            classes_found = set()
            
            for idx in sorted_sim_indices:
                if len(classes_found) >= len(target_classes):
                    break
                    
                real_idx_X_train = X_labeled_indices[idx]
                nearest_ticket_ref = X_train.index[real_idx_X_train]
                label_idx = int(y_train[nearest_ticket_ref])
                nearest_ticket_label = le.inverse_transform([label_idx])[0]
                
                if nearest_ticket_label in target_classes and nearest_ticket_label not in classes_found:
                    classes_found.add(nearest_ticket_label)
                    raw_matches.append((str(nearest_ticket_ref), nearest_ticket_label, similarities[idx]))
        else:
            for idx in sorted_sim_indices:
                if len(raw_matches) >= top_k:
                    break
                    
                real_idx_X_train = X_labeled_indices[idx]
                nearest_ticket_ref = X_train.index[real_idx_X_train]
                label_idx = int(y_train[nearest_ticket_ref])
                nearest_ticket_label = le.inverse_transform([label_idx])[0]
                
                raw_matches.append((str(nearest_ticket_ref), nearest_ticket_label, similarities[idx]))
        
        # Load the raw ticket data from duckdb
        refs = [m[0] for m in raw_matches]
        refs_df = self.duckdb_service.load_tickets_by_ref(refs) if refs else None

        input_text = f"{input_title} {input_description}".lower()
        input_words = set(re.findall(r'\b\w{4,}\b', input_text))

        results = []
        for ref, label, similarity in raw_matches:
            title, description = None, None
            
            if refs_df is not None and not refs_df.empty:
                # Match the ref string types properly
                row_matches = refs_df[refs_df['Ref'] == ref]
                if not row_matches.empty:
                    row = row_matches.iloc[0]
                    title = row['Title_anon'] if pd.notna(row['Title_anon']) else None
                    description = row['Description_anon'] if pd.notna(row['Description_anon']) else None
            
            neighbor_text = f"{title or ''} {description or ''}".lower()
            neighbor_words = set(re.findall(r'\b\w{4,}\b', neighbor_text))
            
            overlapping_terms = list(input_words.intersection(neighbor_words))
            reason = None
            if overlapping_terms:
                reason = f"Shares {', '.join(overlapping_terms)} with the current ticket."
                
            results.append({
                "ref": ref,
                "label": label,
                "similarity": float(similarity),
                "title": title,
                "description": description,
                "reason": reason,
                "overlapping_terms": overlapping_terms
            })
            
        return results

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
            vectorizer = self.ticket_vectorizer_service.create_vectorizer()
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
            "request_one_hot_encoder_location": config.encoder_location(al_instance_id, "one_hot"),
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
                "one_hot_encoder": config.encoder_location(al_instance_id, "one_hot"),
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
        logger.info(f"Received XAI job update message: {data}")
        
        if self.duckdb_service is None:
            logger.error("DuckDB service is not configured")
            raise RuntimeError("DuckDB service is not configured")
        
        if not {"job_id", "status"}.issubset(data.keys()):
            logger.error(f"Invalid data format - missing required fields. Data: {data}")
            raise ValueError("Invalid data format for updating XAI job")
        else:
            job_id = data["job_id"]
            if isinstance(job_id, str):
                try:
                    job_id = uuid.UUID(job_id)
                except ValueError as e:
                    logger.error(f"Failed to parse job_id '{job_id}' as UUID: {e}")
                    raise
            
            if data["status"] == "completed" and ("result_location" not in data or "result_file_names" not in data):
                logger.error(f"Status is 'completed' but missing result_location or result_file_names. Data: {data}")
                raise ValueError("Missing result_location or result_file_names for completed XAI job")

            logger.info(f"Updating XAI job {job_id} with status={data['status']}")
            self.duckdb_service.update_xai_job_status(job_id=job_id,
                                                      status=data["status"],
                                                      result_location=data.get("result_location"),
                                                      result_file_names=data.get("result_file_names"))
            logger.info(f"Successfully updated XAI job {job_id}")

            if data["status"] == "completed":
                job_info = self.duckdb_service.get_xai_job(job_id)
                ticket_ids = []
                top_features = []
                errors = None

                if job_info and job_info.get("ticket_ref_or_sha"):
                    ticket_ids = [job_info["ticket_ref_or_sha"]]

                if job_info and job_info.get("result_location") and job_info.get("result_file_names") and self.minio_service is not None:
                    try:
                        result_payload = self.minio_service.load_xai_results(
                            result_location=job_info["result_location"],
                            files=job_info["result_file_names"],
                        )
                        for value in result_payload.values():
                            if isinstance(value, list):
                                for item in value:
                                    if isinstance(item, dict) and item.get("top_words"):
                                        top_features.append(item["top_words"][:10])
                                        if item.get("error"):
                                            errors = (errors or []) + [item["error"]]
                            elif isinstance(value, dict) and value.get("top_words"):
                                top_features.append(value["top_words"][:10])
                                if value.get("error"):
                                    errors = (errors or []) + [value["error"]]
                    except Exception as exc:
                        errors = (errors or []) + [str(exc)]

                latency_ms = None
                if job_info and job_info.get("created_at") and job_info.get("finished_at"):
                    latency_ms = int((job_info["finished_at"] - job_info["created_at"]).total_seconds() * 1000)

                if job_info is not None:
                    self.duckdb_service.log_event(
                        al_instance_id=job_info["al_instance_id"],
                        user_id=SYSTEM_USER_ID,
                        action="lime",
                        latency_ms=latency_ms,
                        payload={
                            "ticket_ids": ticket_ids,
                            "top_features": top_features,
                            "errors": errors,
                        },
                    )
        
        


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