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
from collections.abc import Sequence
from app.persistence.local_artifacts import LocalArtifactsStore
from app.persistence.duckdb.service import DuckDbPersistenceService
from app.persistence.minio_storage import MinioService
from app.core.rabbitmq_client import RabbitMQClient
import uuid
import app.config.config as config
import os
import logging
import time
import re
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
        self._spacy_nlp = None
        self.local_artifacts_store = local_artifacts_store
        self.minio_service = minio_service
        self.duckdb_service = duckdb_service
        self.rabbitmq_client = rabbitmq_client
        self.ticket_vectorizer_service = ticket_vectorizer_service

    def _get_spacy_nlp(self):
        """Load and cache the configured SpaCy pipeline on first use.

        Returns:
            The loaded SpaCy language pipeline.

        Raises:
            ValueError: If SpaCy is not installed or the configured model is missing.
        """
        if self._spacy_nlp is not None:
            return self._spacy_nlp

        try:
            import spacy  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ValueError("SpaCy is not installed") from exc

        try:
            nlp = spacy.load(config.SPACY_MODEL_NAME)
        except OSError as exc:
            raise ValueError(f"SpaCy model '{config.SPACY_MODEL_NAME}' is not installed") from exc

        if "sentencizer" not in nlp.pipe_names and "parser" not in nlp.pipe_names:
            try:
                nlp.add_pipe("sentencizer")
            except ValueError:
                pass

        self._spacy_nlp = nlp
        return nlp

    def _ticket_text(self, ticket: Data) -> str:
        """Build the canonical plain-text representation used for sentence scoring.

        Args:
            ticket: The ticket data to stringify.

        Returns:
            A single normalized text string.
        """
        parts = [ticket.title_anon, ticket.description_anon]
        return " ".join(part.strip() for part in parts if isinstance(part, str) and part.strip()).strip()

    def _encode_text_embedding(self, text: str) -> np.ndarray:
        """Encode a text string into a 2D embedding array.

        Args:
            text: The text to embed.

        Returns:
            A 2D numpy array suitable for cosine similarity.
        """
        embedding = np.asarray(self.sentence_model.encode([text or ""]))
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        return embedding

    def _extract_keywords(self, doc) -> set[str]:
        """Extract keyword candidates from a SpaCy doc.

        Args:
            doc: The SpaCy document.

        Returns:
            A set of normalized keyword strings.
        """
        keywords: set[str] = set()

        try:
            chunks = [chunk.text for chunk in doc.noun_chunks]
        except Exception:
            chunks = []

        source_terms = chunks if chunks else [token.text for token in doc if getattr(token, "is_alpha", False) and not getattr(token, "is_stop", False)]
        for term in source_terms:
            normalized = term.lower().strip()
            if normalized:
                keywords.update(part for part in re.findall(r"\b\w+\b", normalized) if len(part) > 2)

        return keywords

    def _extract_entities(self, doc) -> set[str]:
        """Extract normalized named entities from a SpaCy doc.

        Args:
            doc: The SpaCy document.

        Returns:
            A set of entity strings.
        """
        return {ent.text.lower().strip() for ent in getattr(doc, "ents", []) if ent.text and ent.text.strip()}

    def _sentence_score_components(
        self,
        *,
        sentence: str,
        original_text_embedding: np.ndarray,
        original_doc,
    ) -> tuple[float, dict[str, float]]:
        """Compute the weighted sentence score and component scores.

        Args:
            sentence: Candidate sentence text.
            original_text_embedding: The cached embedding for the source ticket text.
            original_doc: The SpaCy doc for the source ticket text.

        Returns:
            A tuple of overall score and component score dictionary.
        """
        nlp = self._get_spacy_nlp()
        sentence_doc = nlp(sentence)
        sentence_embedding = self._encode_text_embedding(sentence)

        embedding_similarity = float(cosine_similarity(original_text_embedding, sentence_embedding)[0, 0])

        original_keywords = self._extract_keywords(original_doc)
        sentence_keywords = self._extract_keywords(sentence_doc)
        keyword_overlap = float(len(original_keywords & sentence_keywords) / max(len(sentence_keywords), 1))

        original_entities = self._extract_entities(original_doc)
        sentence_entities = self._extract_entities(sentence_doc)
        entity_overlap = float(len(original_entities & sentence_entities) / max(len(sentence_entities), 1))

        score = 0.7 * embedding_similarity + 0.2 * keyword_overlap + 0.1 * entity_overlap
        return score, {
            "embedding_similarity": embedding_similarity,
            "keyword_overlap": keyword_overlap,
            "entity_overlap": entity_overlap,
        }

    def _best_sentence_from_text(self, text: str, original_text_embedding: np.ndarray) -> tuple[Optional[str], float, Optional[dict[str, float]]]:
        """Select the best scoring sentence from a piece of text.

        Newlines (``\\n``) are treated as sentence boundaries so that multi-line
        descriptions yield meaningful short candidates.  The full text is then
        cleaned of newlines for keyword and entity extraction to avoid confusing
        SpaCy's tokenization and NER.

        Args:
            text: Candidate ticket text.
            original_text_embedding: Cached embedding of the source ticket text.

        Returns:
            The best sentence, its score, and the component score breakdown.
        """
        normalized_text = (text or "").strip()
        if not normalized_text:
            return None, 0.0, None

        nlp = self._get_spacy_nlp()

        # Split on newlines first so each paragraph is processed independently.
        # SpaCy does not treat \n as a sentence boundary, so without this step
        # multi-line descriptions are lumped into one giant sentence.
        all_sentences: list[str] = []
        for paragraph in normalized_text.split("\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            doc = nlp(paragraph)
            for sent in doc.sents:
                sent_text = sent.text.strip()
                if sent_text:
                    all_sentences.append(sent_text)

        if not all_sentences:
            return None, 0.0, None

        # Build a single doc from the full text for keyword/entity extraction.
        # Replace \n with space so SpaCy tokenization and NER are not confused
        # by embedded newline characters.
        clean_text = normalized_text.replace("\n", " ")
        original_doc = nlp(clean_text)

        best_sentence = None
        best_score = 0.0
        best_components = None

        for sentence in all_sentences:
            score, components = self._sentence_score_components(
                sentence=sentence,
                original_text_embedding=original_text_embedding,
                original_doc=original_doc,
            )
            if best_sentence is None or score > best_score:
                best_sentence = sentence
                best_score = float(score)
                best_components = components

        return best_sentence, float(best_score), best_components

    def _sanitize_neighbor_for_storage(self, neighbor: Dict[str, Any]) -> Dict[str, Any]:
        """Strip large or recursive fields from a neighbor payload before persistence.

        Args:
            neighbor: The neighbor payload to sanitize.

        Returns:
            A JSON-serializable dictionary safe for label_decisions.similar_tickets.
        """
        excluded_keys = {"xai_result", "similar_tickets"}
        return {key: value for key, value in neighbor.items() if key not in excluded_keys}

    def _load_ticket_lookup(self, refs: list[str]) -> Dict[str, Dict[str, Any]]:
        """Load ticket metadata for a list of refs and index it by ref string.

        Args:
            refs: Ticket references to fetch.

        Returns:
            A dictionary keyed by ref string.
        """
        if self.duckdb_service is None or not refs:
            return {}

        refs_df = self.duckdb_service.load_tickets_by_ref(refs)
        if refs_df is None or refs_df.empty:
            return {}

        lookup: Dict[str, Dict[str, Any]] = {}
        for _, row in refs_df.iterrows():
            lookup[str(row["Ref"])] = {str(key): value for key, value in row.to_dict().items()}
        return lookup

    def _get_predicted_classes(self, al_instance_id: int, ticket: Data, top_k: int, model_id: int = 0) -> list[Any]:
        """Return the top predicted classes for a ticket.

        Args:
            al_instance_id: Active learning instance identifier.
            ticket: Ticket to classify.
            top_k: Maximum number of classes to return.
            model_id: Model identifier.

        Returns:
            Ordered class labels selected from the model probabilities.
        """
        if self.inference_service is None:
            raise ValueError("Inference service is not configured")

        res = self.inference_service.infer_proba(al_instance_id, ticket, model_id)
        probabilities = res["probabilities"][0]
        classes = res["classes"]
        top_k = min(top_k, len(classes))
        sorted_class_idx = np.argsort(probabilities)[::-1][:top_k]
        return [classes[idx] for idx in sorted_class_idx]

    def _build_predicted_class_neighbors(
        self,
        *,
        al_instance_id: int,
        target_embedding: np.ndarray,
        original_text_embedding: np.ndarray,
        original_text: str,
        top_k: int,
        ticket: Data,
        model_id: int = 0,
    ) -> list[Dict[str, Any]]:
        """Build one nearest neighbor per predicted class.

        Args:
            al_instance_id: Active learning instance identifier.
            target_embedding: Vectorized representation used for nearest-neighbor search.
            original_text_embedding: Cached embedding for sentence scoring.
            original_text: Source ticket text.
            top_k: Maximum number of predicted classes to consider.
            ticket: Source ticket data.
            model_id: Model identifier.

        Returns:
            A list of neighbor dictionaries.
        """
        predicted_classes = self._get_predicted_classes(al_instance_id, ticket, top_k, model_id)
        if not predicted_classes:
            return []

        X_train = self.storage.dataset_dict[al_instance_id]["X_train"]
        y_train = self.storage.dataset_dict[al_instance_id]["y_train"]
        le = self.storage.dataset_dict[al_instance_id]["le"]

        labeled_mask = y_train.notna()
        X_labeled = X_train[labeled_mask]
        if X_labeled.empty:
            return []

        X_labeled_indices = np.where(labeled_mask)[0]
        similarities = cosine_similarity(target_embedding, X_labeled.values)[0]
        sorted_sim_indices = np.argsort(similarities)[::-1]

        matched_neighbors: list[Dict[str, Any]] = []
        matched_classes: set[Any] = set()
        for idx in sorted_sim_indices:
            real_idx_X_train = X_labeled_indices[idx]
            nearest_ticket_ref = str(X_train.index[real_idx_X_train])
            label_idx = int(y_train[nearest_ticket_ref])
            nearest_ticket_label = le.inverse_transform([label_idx])[0]

            if nearest_ticket_label in predicted_classes and nearest_ticket_label not in matched_classes:
                matched_classes.add(nearest_ticket_label)
                matched_neighbors.append(
                    {
                        "ref": nearest_ticket_ref,
                        "label": str(nearest_ticket_label),
                        "similarity": float(similarities[idx]),
                    }
                )
                if len(matched_classes) >= len(predicted_classes):
                    break

        ticket_lookup = self._load_ticket_lookup([neighbor["ref"] for neighbor in matched_neighbors])
        results: list[Dict[str, Any]] = []
        for neighbor in matched_neighbors:
            ticket_row = ticket_lookup.get(neighbor["ref"], {})
            title = ticket_row.get("Title_anon") or None
            description = ticket_row.get("Description_anon") or None
            sentence_text = description or ""
            best_sentence, best_sentence_score, sentence_score_components = self._best_sentence_from_text(
                sentence_text,
                original_text_embedding,
            )
            results.append(
                {
                    **neighbor,
                    "title": title,
                    "description": description,
                    "best_sentence": best_sentence,
                    "best_sentence_score": best_sentence_score,
                    "sentence_score_components": sentence_score_components,
                }
            )

        return results

    def _build_historical_neighbors(
        self,
        *,
        al_instance_id: int,
        target_embedding: np.ndarray,
        original_text_embedding: np.ndarray,
        top_k: int = 2,
    ) -> list[Dict[str, Any]]:
        """Build nearest neighbors from previously saved label decisions.

        Args:
            al_instance_id: Active learning instance identifier.
            target_embedding: Vectorized representation used for nearest-neighbor search.
            original_text_embedding: Cached embedding for sentence scoring.

        Returns:
            A list of neighbor dictionaries with historical metadata attached.

        Raises:
            ValueError: If the DuckDB service is unavailable.
        """
        if self.duckdb_service is None:
            raise ValueError("DuckDB service is not configured")

        X_train = self.storage.dataset_dict[al_instance_id]["X_train"]
        y_train = self.storage.dataset_dict[al_instance_id]["y_train"]
        le = self.storage.dataset_dict[al_instance_id]["le"]

        candidates = self.duckdb_service.load_label_decisions_with_xai(al_instance_id=al_instance_id)
        if not candidates:
            return []

        valid_candidates: list[Dict[str, Any]] = []
        skipped_refs: list[str] = []
        for candidate in candidates:
            ref = str(candidate["ref"])
            if ref not in X_train.index:
                skipped_refs.append(ref)
                continue
            valid_candidates.append(candidate)

        if skipped_refs:
            logger.debug("Skipping label_decision refs not found in X_train: %s", skipped_refs)

        if not valid_candidates:
            return []

        candidate_refs = [str(candidate["ref"]) for candidate in valid_candidates]
        candidate_embeddings = X_train.loc[candidate_refs].values
        similarities = cosine_similarity(target_embedding, candidate_embeddings)[0]
        sorted_indices = np.argsort(similarities)[::-1]
        num_neighbors = min(top_k, len(valid_candidates), len(sorted_indices))

        ticket_lookup = self._load_ticket_lookup(candidate_refs)
        results: list[Dict[str, Any]] = []
        for sorted_position in range(num_neighbors):
            candidate = valid_candidates[int(sorted_indices[sorted_position])]
            ref = str(candidate["ref"])
            ticket_row = ticket_lookup.get(ref, {})
            title = ticket_row.get("Title_anon") or None
            description = ticket_row.get("Description_anon") or None
            sentence_text = description or ""
            best_sentence, best_sentence_score, sentence_score_components = self._best_sentence_from_text(
                sentence_text,
                original_text_embedding,
            )

            label_value = candidate.get("label")
            if label_value is None and ref in y_train.index and pd.notna(y_train[ref]):
                label_idx = int(y_train[ref])
                label_value = le.inverse_transform([label_idx])[0]

            results.append(
                {
                    "ref": ref,
                    "label": None if label_value is None else str(label_value),
                    "similarity": float(similarities[int(sorted_indices[sorted_position])]),
                    "title": title,
                    "description": description,
                    "best_sentence": best_sentence,
                    "best_sentence_score": best_sentence_score,
                    "sentence_score_components": sentence_score_components,
                    "xai_result": candidate.get("xai_result"),
                    "similar_tickets": candidate.get("similar_tickets"),
                    "model_prediction": candidate.get("model_prediction"),
                    "explanation": candidate.get("explanation"),
                    "most_helpful_feature": candidate.get("most_helpful_feature"),
                }
            )

        return results

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

    def find_nearest(self, al_instance_id: int, ticket: Data, top_k: int = 1, model_id: int = 0):
        start_time = time.perf_counter()
        original_text = self._ticket_text(ticket)
        target_embedding = inference(
            df=pd.DataFrame([ticket.model_dump()]), 
            le=self.storage.dataset_dict[al_instance_id]['le'], 
            oh=self.storage.dataset_dict[al_instance_id]['oh'], 
            sentence_model=self.sentence_model
        ).values
        original_text_embedding = self._encode_text_embedding(original_text)

        predicted_class_neighbors = self._build_predicted_class_neighbors(
            al_instance_id=al_instance_id,
            target_embedding=target_embedding,
            original_text_embedding=original_text_embedding,
            original_text=original_text,
            top_k=top_k,
            ticket=ticket,
            model_id=model_id,
        )
        historical_neighbors = self._build_historical_neighbors(
            al_instance_id=al_instance_id,
            target_embedding=target_embedding,
            original_text_embedding=original_text_embedding,
            top_k=top_k,
        )

        if self.duckdb_service is not None:
            self.duckdb_service.log_event(
                al_instance_id=al_instance_id,
                user_id=SYSTEM_USER_ID,
                action="similar_tickets",
                latency_ms=int((time.perf_counter() - start_time) * 1000),
                payload={
                    "ticket_id": None,
                    "predicted_class_neighbor_ids": [item["ref"] for item in predicted_class_neighbors],
                    "predicted_class_similarities": [item["similarity"] for item in predicted_class_neighbors],
                    "historical_neighbor_ids": [item["ref"] for item in historical_neighbors],
                    "historical_similarities": [item["similarity"] for item in historical_neighbors],
                    "top_k": top_k,
                },
            )

            ticket_ref = getattr(ticket, "ref", None)
            if ticket_ref and (predicted_class_neighbors or historical_neighbors):
                sanitized_results = {
                    "predicted_class_neighbors": [self._sanitize_neighbor_for_storage(item) for item in predicted_class_neighbors],
                    "historical_neighbors": [self._sanitize_neighbor_for_storage(item) for item in historical_neighbors],
                }
                self.duckdb_service.upsert_label_decision(
                    al_instance_id=al_instance_id,
                    ref=str(ticket_ref),
                    similar_tickets=sanitized_results,
                )

        return {
            "predicted_class_neighbors": predicted_class_neighbors,
            "historical_neighbors": historical_neighbors,
        }

    def find_nearest_by_idx(self, al_instance_id: int, index: str, top_k: int = 2, model_id: int = 0):
        start_time = time.perf_counter()
        if self.duckdb_service is None:
            raise ValueError("DuckDB service is not configured")

        target_embedding = self.storage.dataset_dict[al_instance_id]['X_train'].loc[[index]].values
        
        query_df = self.duckdb_service.load_tickets_by_ref([index])
        if query_df is not None and not query_df.empty:
            row = query_df.iloc[0]
            input_title = row['Title_anon'] if pd.notna(row['Title_anon']) else ""
            input_description = row['Description_anon'] if pd.notna(row['Description_anon']) else ""
            s_name = row['Service->Name'] if pd.notna(row['Service->Name']) else None
            s_sub = row['Service subcategory->Name'] if pd.notna(row['Service subcategory->Name']) else None
        else:
            input_title, input_description, s_name, s_sub = "", "", None, None

        ticket_obj = Data(
            title_anon=input_title,
            description_anon=input_description,
            service_name=s_name,
            service_subcategory_name=s_sub
        )
        original_text = self._ticket_text(ticket_obj)
        original_text_embedding = self._encode_text_embedding(original_text)
        predicted_class_neighbors = self._build_predicted_class_neighbors(
            al_instance_id=al_instance_id,
            target_embedding=target_embedding,
            original_text_embedding=original_text_embedding,
            original_text=original_text,
            top_k=top_k,
            ticket=ticket_obj,
            model_id=model_id,
        )
        historical_neighbors = self._build_historical_neighbors(
            al_instance_id=al_instance_id,
            target_embedding=target_embedding,
            original_text_embedding=original_text_embedding,
            top_k=top_k,
        )

        if self.duckdb_service is not None:
            self.duckdb_service.log_event(
                al_instance_id=al_instance_id,
                user_id=SYSTEM_USER_ID,
                action="similar_tickets",
                latency_ms=int((time.perf_counter() - start_time) * 1000),
                payload={
                    "ticket_id": str(index),
                    "predicted_class_neighbor_ids": [item["ref"] for item in predicted_class_neighbors],
                    "predicted_class_similarities": [item["similarity"] for item in predicted_class_neighbors],
                    "historical_neighbor_ids": [item["ref"] for item in historical_neighbors],
                    "historical_similarities": [item["similarity"] for item in historical_neighbors],
                    "top_k": top_k,
                },
            )

            if predicted_class_neighbors or historical_neighbors:
                sanitized_results = {
                    "predicted_class_neighbors": [self._sanitize_neighbor_for_storage(item) for item in predicted_class_neighbors],
                    "historical_neighbors": [self._sanitize_neighbor_for_storage(item) for item in historical_neighbors],
                }
                self.duckdb_service.upsert_label_decision(
                    al_instance_id=al_instance_id, 
                    ref=str(index),
                    similar_tickets=sanitized_results,
                )

        return {
            "predicted_class_neighbors": predicted_class_neighbors,
            "historical_neighbors": historical_neighbors,
        }

    def _compute_nearest(self, al_instance_id: int, target_embedding, top_k: int, distinct_classes: bool, target_classes: Optional[set[Any]] = None, input_title: str = "", input_description: str = ""):
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
        results = []
        for ref, label, similarity in raw_matches:
            results.append({
                "ref": ref,
                "label": label,
                "similarity": float(similarity),
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

    def find_nearest_by_query_idx(self, al_instance_id: int, indices: Sequence[str | int], model_id: int = 0):
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

        if self.local_artifacts_store is None:
            raise ValueError("Local artifacts store is not configured")

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