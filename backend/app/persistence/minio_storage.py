"""
High-level model operations backed by MinIO.
"""
from datetime import datetime
from io import BytesIO
import logging
import os
import re
from typing import Any, Dict, Optional
import joblib
import cloudpickle
import pandas as pd
from app.core.minio_client import MinioClient
from app.data_models.active_learning_dm import Data
import hashlib, json, unicodedata
import humal_vectorizer

logger = logging.getLogger(__name__)

# MinIO bucket names
MODELS_BUCKET = "smart-finance-models"
DATA_BUCKET = "smart-finance-data"
RESULTS_BUCKET = "smart-finance-results"
SHA_FIELDS = ["service_subcategory_name", "service_name", "title_anon", "description_anon", "public_log_anon"]

class MinioService:
    def __init__(self, client: MinioClient):
        self.client = client
        self.minio_prefix = self._get_minio_prefix()
        logger.info(f"Initialized MinioService with prefix: {self.minio_prefix or '(none)'}")

    def save_model(
        self,
        *,
        al_instance_id: int,
        model_version: int,
        model: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Upload a model (as Python object) and optionally attach metadata."""
        object_name = self._with_prefix(f"models/{al_instance_id}/{model_version}.joblib")
        logger.info(f"Saving model to MinIO: instance={al_instance_id}, version={model_version}, object={object_name}")
        try:
            model_bytes = self._to_joblib(model)
            logger.debug(f"Model serialized to {len(model_bytes)} bytes")
            self.client.upload_file_bytes(MODELS_BUCKET, object_name, model_bytes)

            metadata_result = None
            if metadata:
                logger.debug(f"Updating model metadata: {metadata}")
                metadata_result = self.client.update_metadata(MODELS_BUCKET, object_name, metadata)

            logger.info(f"Model saved successfully: {MODELS_BUCKET}/{object_name}")
            return {
                "bucket": MODELS_BUCKET,
                "object": object_name,
                "metadata": metadata_result if metadata_result is not None else metadata,
            }
        except Exception as e:
            logger.error(f"Failed to save model {al_instance_id}/{model_version}: {e}", exc_info=True)
            raise

    def load_model(
        self,
        *,
        al_instance_id: int,
        model_version: int,
    ):
        """Download and deserialize a model from MinIO."""
        object_name = self._with_prefix(f"models/{al_instance_id}/{model_version}.joblib")
        logger.info(f"Loading model from MinIO: instance={al_instance_id}, version={model_version}")
        try:
            downloaded = self.client.download_object(MODELS_BUCKET, object_name)
            logger.debug(f"Downloaded {len(downloaded)} bytes")
            model = joblib.load(BytesIO(downloaded))
            logger.info(f"Model loaded successfully: {MODELS_BUCKET}/{object_name}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model {al_instance_id}/{model_version}: {e}", exc_info=True)
            raise

    def load_metadata(
        self,
        *,
        al_instance_id: int,
        model_version: int,
    ) -> Dict[str, Any]:
        """Fetch object metadata for a stored model."""
        object_name = self._with_prefix(f"models/{al_instance_id}/{model_version}.joblib")
        logger.debug(f"Loading model metadata: instance={al_instance_id}, version={model_version}")
        try:
            metadata = self.client.get_metadata(MODELS_BUCKET, object_name)
            logger.debug(f"Model metadata loaded: {metadata}")
            return metadata
        except Exception as e:
            logger.error(f"Failed to load metadata for model {al_instance_id}/{model_version}: {e}", exc_info=True)
            raise

    def save_label_encoder(
        self,
        *,
        al_instance_id: int,
        encoder: Any,
    ):
        """Upload a label encoder (as Python object)."""
        object_name = self._with_prefix(f"encoders/{al_instance_id}/label_encoder.joblib")
        logger.info(f"Saving label encoder to MinIO: instance={al_instance_id}, object={object_name}")
        try:
            encoder_bytes = self._to_joblib(encoder)
            logger.debug(f"Label encoder serialized to {len(encoder_bytes)} bytes")
            self.client.upload_file_bytes(MODELS_BUCKET, object_name, encoder_bytes)
            logger.info(f"Label encoder saved successfully")
            return {"bucket": MODELS_BUCKET, "object": object_name}
        except Exception as e:
            logger.error(f"Failed to save label encoder for instance {al_instance_id}: {e}", exc_info=True)
            raise

    def load_label_encoder(
        self,
        *,
        al_instance_id: int,
    ):
        """Download and deserialize a label encoder from MinIO."""
        object_name = self._with_prefix(f"encoders/{al_instance_id}/label_encoder.joblib")
        logger.info(f"Loading label encoder from MinIO: instance={al_instance_id}")
        try:
            downloaded = self.client.download_object(MODELS_BUCKET, object_name)
            logger.debug(f"Downloaded {len(downloaded)} bytes")
            encoder = joblib.load(BytesIO(downloaded))
            logger.info(f"Label encoder loaded successfully")
            return encoder
        except Exception as e:
            logger.error(f"Failed to load label encoder for instance {al_instance_id}: {e}", exc_info=True)
            raise

    def save_one_hot_encoder(
        self,
        *,
        al_instance_id: int,
        encoder: Any,
    ):
        """Upload a one-hot encoder (as Python object)."""
        object_name = self._with_prefix(f"encoders/{al_instance_id}/one_hot_encoder.joblib")
        logger.info(f"Saving one-hot encoder to MinIO: instance={al_instance_id}, object={object_name}")
        try:
            encoder_bytes = self._to_joblib(encoder)
            logger.debug(f"One-hot encoder serialized to {len(encoder_bytes)} bytes")
            self.client.upload_file_bytes(MODELS_BUCKET, object_name, encoder_bytes)
            logger.info(f"One-hot encoder saved successfully")
            return {"bucket": MODELS_BUCKET, "object": object_name}
        except Exception as e:
            logger.error(f"Failed to save one-hot encoder for instance {al_instance_id}: {e}", exc_info=True)
            raise

    def load_one_hot_encoder(
        self,
        *,
        al_instance_id: int,
    ):
        """Download and deserialize a one-hot encoder from MinIO."""
        object_name = self._with_prefix(f"encoders/{al_instance_id}/one_hot_encoder.joblib")
        logger.info(f"Loading one-hot encoder from MinIO: instance={al_instance_id}")
        try:
            downloaded = self.client.download_object(MODELS_BUCKET, object_name)
            logger.debug(f"Downloaded {len(downloaded)} bytes")
            encoder = joblib.load(BytesIO(downloaded))
            logger.info(f"One-hot encoder loaded successfully")
            return encoder
        except Exception as e:
            logger.error(f"Failed to load one-hot encoder for instance {al_instance_id}: {e}", exc_info=True)
            raise

    def load_data(self, split: str, latest_dataset_timestamp: datetime=datetime.min) -> Optional[Dict[datetime, pd.DataFrame]]:
        """Load all newer tickets, newer than `latest_dataset_timestamp` from MinIO.

        The method checks for objects named:
        `datasets/{split}/User Request_last_team_ANON_{timestamp}.xlsx`

        The timestamp is of the format `%Y%m%dT%H%M%S`, e.g. `20240101T120000`.
        All datasets with `timestamp` greater than `latest_dataset_timestamp`,
        are downloaded and returned as a dictionary of DataFrames.

        Returns None if no newer dataset is available.
        """
        logger.info(f"Loading datasets from MinIO: split={split}, newer_than={latest_dataset_timestamp}")
        
        # Construct the prefix
        prefix = f"datasets/{split}/"
        # Find all of the datasets in the bucket (of the given split)
        try:
            listing = self.client.list_objects(DATA_BUCKET, prefix=prefix, filter_type="exact")
            
            if not listing or not listing.get("matches"):
                logger.info(f"No datasets found for split={split}")
                return None

            pattern = re.compile(rf"^{re.escape(prefix)}User Request_last_team_ANON_(\d{{8}}T\d{{6}})\.xlsx$")
            new_tickets = {}

            for name in listing["matches"]:
                m = pattern.match(str(name))
                if not m: 
                    continue
                # Extract timestamp from filename
                ts = m.group(1)
                # Convert to datetime for comparison
                try:
                    ts_dt = datetime.strptime(ts, "%Y%m%dT%H%M%S")
                except ValueError:
                    logger.warning(f"Failed to parse timestamp from {name}")
                    continue

                if ts_dt > latest_dataset_timestamp:
                    logger.debug(f"Downloading dataset: {name}")
                    downloaded = self.client.download_object(DATA_BUCKET, str(name))
                    df = pd.read_excel(BytesIO(downloaded))
                    logger.debug(f"Loaded dataset {name}: {len(df)} rows, {len(df.columns)} columns")
                    new_tickets[ts_dt] = df

            if new_tickets:
                logger.info(f"Successfully loaded {len(new_tickets)} newer datasets for split={split}")
                return new_tickets

            logger.info(f"No newer datasets found for split={split}")
            return None
        except Exception as e:
            logger.error(f"Failed to load datasets for split={split}: {e}", exc_info=True)
            raise
    
    def return_data_names(self, split: str):
        """Return the names of the datasets available in MinIO for a given split."""
        logger.debug(f"Listing dataset names for split={split}")
        try:
            prefix = f"datasets/{split}/"
            listing = self.client.list_objects(DATA_BUCKET, prefix=prefix, filter_type="exact")
            
            if not listing or not listing.get("matches"):
                logger.debug(f"No datasets found for split={split}")
                return []

            pattern = re.compile(rf"^{re.escape(prefix)}User Request_last_team_ANON_(\d{{8}}T\d{{6}})\.xlsx$")
            dataset_names = []

            for name in listing["matches"]:
                m = pattern.match(str(name))
                if m:
                    dataset_names.append(str(name))

            logger.debug(f"Found {len(dataset_names)} datasets for split={split}")
            return dataset_names
        except Exception as e:
            logger.error(f"Failed to list dataset names for split={split}: {e}", exc_info=True)
            raise

    def save_vectorized_tickets(
        self,
        *,
        al_instance_id: int,
        tickets_version: int,
        split: str,
        df: pd.DataFrame,
    ):
        """Upload vectorized tickets as joblib format."""
        object_name = self._with_prefix(f"vectorized_tickets/{al_instance_id}/{tickets_version}_{split}.joblib")
        logger.info(f"Saving vectorized tickets to MinIO: instance={al_instance_id}, version={tickets_version}, split={split}, shape={df.shape}")
        try:
            tickets_bytes = self._to_joblib(df)
            logger.debug(f"Vectorized tickets serialized to {len(tickets_bytes)} bytes")
            self.client.upload_file_bytes(DATA_BUCKET, object_name, tickets_bytes)
            logger.info(f"Vectorized tickets saved successfully")
            return {"bucket": DATA_BUCKET, "object": object_name}
        except Exception as e:
            logger.error(f"Failed to save vectorized tickets for instance {al_instance_id}/{tickets_version}/{split}: {e}", exc_info=True)
            raise

    def load_vectorized_tickets(
        self,
        *,
        al_instance_id: int,
        tickets_version: int,
        split: str,
    ) -> pd.DataFrame:
        """Download and deserialize vectorized tickets from MinIO."""
        object_name = self._with_prefix(f"vectorized_tickets/{al_instance_id}/{tickets_version}_{split}.joblib")
        logger.info(f"Loading vectorized tickets from MinIO: instance={al_instance_id}, version={tickets_version}, split={split}")
        try:
            downloaded = self.client.download_object(DATA_BUCKET, object_name)
            logger.debug(f"Downloaded {len(downloaded)} bytes")
            df = joblib.load(BytesIO(downloaded))
            logger.info(f"Vectorized tickets loaded successfully: shape={df.shape}")
            return df
        except Exception as e:
            logger.error(f"Failed to load vectorized tickets for instance {al_instance_id}/{tickets_version}/{split}: {e}", exc_info=True)
            raise
    
    def save_labels(
        self,
        *,
        al_instance_id: int,
        labels_version: int,
        split: str,
        df: pd.Series,
    ):
        """Upload labels as joblib format."""
        object_name = self._with_prefix(f"labels/{al_instance_id}/{labels_version}_{split}.joblib")
        logger.info(f"Saving labels to MinIO: instance={al_instance_id}, version={labels_version}, split={split}, count={len(df)}")
        try:
            labels_bytes = self._to_joblib(df)
            logger.debug(f"Labels serialized to {len(labels_bytes)} bytes")
            self.client.upload_file_bytes(DATA_BUCKET, object_name, labels_bytes)
            logger.info(f"Labels saved successfully")
            return {"bucket": DATA_BUCKET, "object": object_name}
        except Exception as e:
            logger.error(f"Failed to save labels for instance {al_instance_id}/{labels_version}/{split}: {e}", exc_info=True)
            raise

    def load_labels(
        self,
        *,
        al_instance_id: int,
        labels_version: int,
        split: str,
    ) -> pd.Series:
        """Download and deserialize labels from MinIO."""
        object_name = self._with_prefix(f"labels/{al_instance_id}/{labels_version}_{split}.joblib")
        logger.info(f"Loading labels from MinIO: instance={al_instance_id}, version={labels_version}, split={split}")
        try:
            downloaded = self.client.download_object(DATA_BUCKET, object_name)
            logger.debug(f"Downloaded {len(downloaded)} bytes")
            labels = joblib.load(BytesIO(downloaded))
            logger.info(f"Labels loaded successfully: count={len(labels)}")
            return labels
        except Exception as e:
            logger.error(f"Failed to load labels for instance {al_instance_id}/{labels_version}/{split}: {e}", exc_info=True)
            raise

    def save_ticket_vectorizer(
        self,
        *,
        al_instance_id: int,
        vectorizer,
    ):
        """
        Upload a TicketVectorizer as a portable cloudpickle file.
        
        Registers the humal_vectorizer module to serialize the TicketVectorizer class as bytecode.
        Safe because SentenceTransformer is imported inside _get_sentence_model() (not at module level),
        so cloudpickle won't include environment-specific module paths in the serialization.
        
        External machines only need: cloudpickle, pandas, scikit-learn, sentence-transformers
        
        IMPORTANT: The vectorizer must have one_hot_encoder=None before calling this method.
        The encoder is saved separately via save_one_hot_encoder().
        
        Raises:
            RuntimeError: If vectorizer.one_hot_encoder is not None
        """
        if vectorizer.one_hot_encoder is not None:
            raise RuntimeError(
                "Cannot save vectorizer with one_hot_encoder attached. "
                "Set vectorizer.one_hot_encoder = None before saving. "
                "The encoder will be saved separately via save_one_hot_encoder()."
            )
        
        logger.info(f"Saving ticket vectorizer to MinIO: instance={al_instance_id}")
        try:
            # Register humal_vectorizer module to be serialized as bytecode
            cloudpickle.register_pickle_by_value(humal_vectorizer)
            
            object_name = self._with_prefix(f"vectorizers/{al_instance_id}/ticket_vectorizer.pkl")
            vectorizer_bytes = self._to_cloudpickle(vectorizer)
            logger.debug(f"Vectorizer serialized to {len(vectorizer_bytes)} bytes")
            self.client.upload_file_bytes(MODELS_BUCKET, object_name, vectorizer_bytes)
            logger.info(f"Ticket vectorizer saved successfully")
            return {"bucket": MODELS_BUCKET, "object": object_name}
        except Exception as e:
            logger.error(f"Failed to save ticket vectorizer for instance {al_instance_id}: {e}", exc_info=True)
            raise

    def load_ticket_vectorizer(
        self,
        *,
        al_instance_id: int,
    ):
        """
        Download and deserialize a TicketVectorizer from MinIO.
        
        Uses cloudpickle to load the complete vectorizer with all dependencies.
        Works on any machine with cloudpickle installed, no source code needed.
        """
        object_name = self._with_prefix(f"vectorizers/{al_instance_id}/ticket_vectorizer.pkl")
        logger.info(f"Loading ticket vectorizer from MinIO: instance={al_instance_id}")
        try:
            downloaded = self.client.download_object(MODELS_BUCKET, object_name)
            logger.debug(f"Downloaded {len(downloaded)} bytes")
            vectorizer = cloudpickle.loads(downloaded)
            logger.info(f"Ticket vectorizer loaded successfully")
            return vectorizer
        except Exception as e:
            logger.error(f"Failed to load ticket vectorizer for instance {al_instance_id}: {e}", exc_info=True)
            raise

    def save_ticket_for_xai(self, al_instance_id: int, X: Data, ticket_ref: Optional[str] = None) -> Dict[str, str]:
        """
        Save the original tickets for XAI purposes.
        The tickets are saved in json format.
        """
        data_dict = X.model_dump()
        ticket_sha = self._encode_ticket_to_sha(data_dict) if ticket_ref is None else ticket_ref
        object_name = self._with_prefix(f"xai_tickets/{al_instance_id}/{ticket_sha}.json")
        logger.info(f"Saving ticket for XAI: instance={al_instance_id}, sha={ticket_sha}")
        try:
            tickets_bytes = X.model_dump_json().encode("utf-8")
            logger.debug(f"Ticket serialized to {len(tickets_bytes)} bytes")
            self.client.upload_file_bytes(DATA_BUCKET, object_name, tickets_bytes)
            logger.info(f"Ticket saved for XAI successfully")
            return {"bucket": DATA_BUCKET, "object": object_name, "ticket_sha": ticket_sha}
        except Exception as e:
            logger.error(f"Failed to save ticket for XAI (instance {al_instance_id}): {e}", exc_info=True)
            raise
    
    def load_xai_results(self, result_location: str, files: list[str]) -> Dict[str, Any]:
        """Load XAI results from a given MinIO location."""
        logger.info(f"Loading XAI results from MinIO: location={result_location}, files={files}")
        result = {}

        try:
            # Download all of the files in the list
            for file in files:
                object_name = result_location.rstrip("/") + "/" + file.lstrip("/")
                logger.debug(f"Downloading XAI result file: {object_name}")
                downloaded = self.client.download_object(RESULTS_BUCKET, object_name)
                # Assume the files are in JSON format and decode them
                result[file.split(".")[0]] = json.loads(downloaded.decode("utf-8"))
            
            logger.info(f"Successfully loaded {len(result)} XAI result files")
            return result
        except Exception as e:
            logger.error(f"Failed to load XAI results from {result_location}: {e}", exc_info=True)
            raise

    
    def delete_instance_objects(self, al_instance_id: int):
        """Delete all objects related to a given AL instance."""
        logger.info(f"Deleting all MinIO objects for instance: {al_instance_id}")
        
        # Define prefixes for all object types related to the instance
        prefixes_by_bucket = {
                MODELS_BUCKET: [
                    self._with_prefix(f"models/{al_instance_id}/"),
                    self._with_prefix(f"encoders/{al_instance_id}/"),
                    self._with_prefix(f"vectorizers/{al_instance_id}/"),
                ],
                DATA_BUCKET: [ 
                    self._with_prefix(f"vectorized_tickets/{al_instance_id}/"),
                    self._with_prefix(f"labels/{al_instance_id}/"),
                    self._with_prefix(f"xai_tickets/{al_instance_id}/"),
                ],
                RESULTS_BUCKET: [
                    self._with_prefix(f"xai_results/{al_instance_id}/"),
                ]
        }

        deleted_count = 0
        try:
            for bucket, prefixes in prefixes_by_bucket.items():
                for prefix in prefixes:
                    logger.debug(f"Listing objects with prefix: {prefix}")
                    listing = self.client.list_objects(bucket, prefix=prefix, filter_type="exact")
                    if listing and listing.get("matches"):
                        for obj_name in listing["matches"]:
                            logger.debug(f"Deleting {bucket}/{obj_name}")
                            self.client.delete_object(bucket, str(obj_name))
                            deleted_count += 1
            
            logger.info(f"Successfully deleted {deleted_count} objects for instance {al_instance_id}")
        except Exception as e:
            logger.error(f"Failed to delete objects for instance {al_instance_id}: {e}", exc_info=True)
            raise

    def _to_joblib(self, obj: Any) -> bytes:
        """Serialize a Python object to joblib bytes."""
        buffer = BytesIO()
        joblib.dump(obj, buffer)
        buffer.seek(0)
        return buffer.read()

    def _to_cloudpickle(self, obj: Any) -> bytes:
        """
        Serialize a Python object to cloudpickle bytes.
        
        Cloudpickle serializes the entire object including class definitions and closures,
        making it fully portable. Unlike joblib, it doesn't require class paths to be importable.
        """
        return cloudpickle.dumps(obj)

    def _get_minio_prefix(self) -> str:
        """Get an optional object-key prefix used to namespace MinIO paths."""
        raw_prefix = (os.getenv("MINIO_PREFIX") or "").strip()
        return raw_prefix.strip("/")

    def _with_prefix(self, object_name: str) -> str:
        """Apply configured MinIO prefix to an object key."""
        normalized_object_name = object_name.lstrip("/")
        if not self.minio_prefix:
            return normalized_object_name
        return f"{self.minio_prefix}/{normalized_object_name}"

    def _encode_ticket_to_sha(self, ticket: dict) -> str:
        "Encodes the ticket to a SHA256 hash, using the fields defined in SHA_FIELDS. This is used to uniquely identify tickets in MinIO."
        canonical = {}
        for k in SHA_FIELDS:
            v = ticket.get(k)
            if isinstance(v, str):
                v = unicodedata.normalize("NFC", v.strip())
            canonical[k] = v
        raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # def _to_parquet(self, df: pd.DataFrame) -> bytes:
    #     """Serialize a DataFrame to Parquet bytes."""
    #     buffer = BytesIO()
    #     df.to_parquet(buffer)
    #     buffer.seek(0)
    #     return buffer.read()
