"""
High-level model operations backed by MinIO.
"""
from datetime import datetime
from io import BytesIO
import os
import re
from typing import Any, Dict, Optional
import joblib
import pandas as pd
from app.core.minio_client import MinioClient
from app.data_models.active_learning_dm import Data
import hashlib, json, unicodedata

# MinIO bucket names
MODELS_BUCKET = "smart-finance-models"
DATA_BUCKET = "smart-finance-data"
RESULTS_BUCKET = "smart-finance-results"
SHA_FIELDS = ["service_subcategory_name", "service_name", "title_anon", "description_anon", "public_log_anon"]

class MinioService:
    def __init__(self, client: MinioClient):
        self.client = client
        self.minio_prefix = self._get_minio_prefix()

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
        model_bytes = self._to_joblib(model)
        self.client.upload_file_bytes(MODELS_BUCKET, object_name, model_bytes)

        metadata_result = None
        if metadata:
            metadata_result = self.client.update_metadata(MODELS_BUCKET, object_name, metadata)

        return {
            "bucket": MODELS_BUCKET,
            "object": object_name,
            "metadata": metadata_result if metadata_result is not None else metadata,
        }

    def load_model(
        self,
        *,
        al_instance_id: int,
        model_version: int,
    ):
        """Download and deserialize a model from MinIO."""
        object_name = self._with_prefix(f"models/{al_instance_id}/{model_version}.joblib")
        downloaded = self.client.download_object(MODELS_BUCKET, object_name)
        return joblib.load(BytesIO(downloaded))

    def load_metadata(
        self,
        *,
        al_instance_id: int,
        model_version: int,
    ) -> Dict[str, Any]:
        """Fetch object metadata for a stored model."""
        object_name = self._with_prefix(f"models/{al_instance_id}/{model_version}.joblib")
        return self.client.get_metadata(MODELS_BUCKET, object_name)

    def save_label_encoder(
        self,
        *,
        al_instance_id: int,
        encoder: Any,
    ):
        """Upload a label encoder (as Python object)."""
        object_name = self._with_prefix(f"encoders/{al_instance_id}/label_encoder.joblib")
        encoder_bytes = self._to_joblib(encoder)
        self.client.upload_file_bytes(MODELS_BUCKET, object_name, encoder_bytes)
        return {"bucket": MODELS_BUCKET, "object": object_name}

    def load_label_encoder(
        self,
        *,
        al_instance_id: int,
    ):
        """Download and deserialize a label encoder from MinIO."""
        object_name = self._with_prefix(f"encoders/{al_instance_id}/label_encoder.joblib")
        downloaded = self.client.download_object(MODELS_BUCKET, object_name)
        return joblib.load(BytesIO(downloaded))

    def save_one_hot_encoder(
        self,
        *,
        al_instance_id: int,
        encoder: Any,
    ):
        """Upload a one-hot encoder (as Python object)."""
        object_name = self._with_prefix(f"encoders/{al_instance_id}/one_hot_encoder.joblib")
        encoder_bytes = self._to_joblib(encoder)
        self.client.upload_file_bytes(MODELS_BUCKET, object_name, encoder_bytes)
        return {"bucket": MODELS_BUCKET, "object": object_name}

    def load_one_hot_encoder(
        self,
        *,
        al_instance_id: int,
    ):
        """Download and deserialize a one-hot encoder from MinIO."""
        object_name = self._with_prefix(f"encoders/{al_instance_id}/one_hot_encoder.joblib")
        downloaded = self.client.download_object(MODELS_BUCKET, object_name)
        return joblib.load(BytesIO(downloaded))

    def load_data(self, split: str, latest_dataset_timestamp: datetime=datetime.min) -> Optional[Dict[datetime, pd.DataFrame]]:
        """Load all newer tickets, newer than `latest_dataset_timestamp` from MinIO.

        The method checks for objects named:
        `datasets/{split}/User Request_last_team_ANON_{timestamp}.xlsx`

        The timestamp is of the format `%Y%m%dT%H%M%S`, e.g. `20240101T120000`.
        All datasets with `timestamp` greater than `latest_dataset_timestamp`,
        are downloaded and returned as a dictionary of DataFrames.

        Returns None if no newer dataset is available.
        """
        # Construct the prefix
        prefix = f"datasets/{split}/"
        # Find all of the datasets in the bucket (of the given split)
        listing = self.client.list_objects(DATA_BUCKET, prefix=prefix, filter_type="exact")
        
        if not listing or not listing.get("matches"):
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
                continue

            if ts_dt > latest_dataset_timestamp:
                downloaded = self.client.download_object(DATA_BUCKET, str(name))
                new_tickets[ts_dt] = pd.read_excel(BytesIO(downloaded))

        if new_tickets:
            return new_tickets

        return None
    
    def return_data_names(self, split: str):
        """Return the names of the datasets available in MinIO for a given split."""
        prefix = f"datasets/{split}/"
        listing = self.client.list_objects(DATA_BUCKET, prefix=prefix, filter_type="exact")
        
        if not listing or not listing.get("matches"):
            return []

        pattern = re.compile(rf"^{re.escape(prefix)}User Request_last_team_ANON_(\d{{8}}T\d{{6}})\.xlsx$")
        dataset_names = []

        for name in listing["matches"]:
            m = pattern.match(str(name))
            if m:
                dataset_names.append(str(name))

        return dataset_names

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
        tickets_bytes = self._to_joblib(df)
        self.client.upload_file_bytes(DATA_BUCKET, object_name, tickets_bytes)
        return {"bucket": DATA_BUCKET, "object": object_name}

    def load_vectorized_tickets(
        self,
        *,
        al_instance_id: int,
        tickets_version: int,
        split: str,
    ) -> pd.DataFrame:
        """Download and deserialize vectorized tickets from MinIO."""
        object_name = self._with_prefix(f"vectorized_tickets/{al_instance_id}/{tickets_version}_{split}.joblib")
        downloaded = self.client.download_object(DATA_BUCKET, object_name)
        return joblib.load(BytesIO(downloaded))
    
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
        labels_bytes = self._to_joblib(df)
        self.client.upload_file_bytes(DATA_BUCKET, object_name, labels_bytes)
        return {"bucket": DATA_BUCKET, "object": object_name}

    def load_labels(
        self,
        *,
        al_instance_id: int,
        labels_version: int,
        split: str,
    ) -> pd.Series:
        """Download and deserialize labels from MinIO."""
        object_name = self._with_prefix(f"labels/{al_instance_id}/{labels_version}_{split}.joblib")
        downloaded = self.client.download_object(DATA_BUCKET, object_name)
        return joblib.load(BytesIO(downloaded))

    def save_ticket_for_xai(self, al_instance_id: int, X: Data, ticket_ref: Optional[str] = None) -> Dict[str, str]:
        """
        Save the original tickets for XAI purposes.
        The tickets are saved in json format.
        """
        data_dict = X.model_dump()
        ticket_sha = self._encode_ticket_to_sha(data_dict) if ticket_ref is None else ticket_ref
        object_name = self._with_prefix(f"xai_tickets/{al_instance_id}/{ticket_sha}.json")
        tickets_bytes = X.model_dump_json().encode("utf-8")
        self.client.upload_file_bytes(DATA_BUCKET, object_name, tickets_bytes)
        return {"bucket": DATA_BUCKET, "object": object_name, "ticket_sha": ticket_sha}
    
    def load_xai_results(self, result_location: str, files: list[str]) -> Dict[str, Any]:
        """Load XAI results from a given MinIO location."""
        result = {}

        # Download all of the files in the list
        for file in files:
            object_name = result_location.rstrip("/") + "/" + file.lstrip("/")
            downloaded = self.client.download_object(RESULTS_BUCKET, object_name)
            # Assume the files are in JSON format and decode them
            result[file.split(".")[0]] = json.loads(downloaded.decode("utf-8"))
        return result

    
    def delete_instance_objects(self, al_instance_id: int):
        """Delete all objects related to a given AL instance."""
        # Define prefixes for all object types related to the instance
        prefixes_by_bucket = {
                MODELS_BUCKET: [
                    self._with_prefix(f"models/{al_instance_id}/"),
                    self._with_prefix(f"encoders/{al_instance_id}/"),
                ],
                DATA_BUCKET: [ 
                    self._with_prefix(f"vectorized_tickets/{al_instance_id}/"),
                    self._with_prefix(f"labels/{al_instance_id}/"),
                    self._with_prefix(f"xai_tickets/{al_instance_id}/"),
                ]
        }

        for bucket, prefixes in prefixes_by_bucket.items():
            for prefix in prefixes:
                listing = self.client.list_objects(bucket, prefix=prefix, filter_type="exact")
                if listing and listing.get("matches"):
                    for obj_name in listing["matches"]:
                        self.client.delete_object(bucket, str(obj_name))

    def _to_joblib(self, obj: Any) -> bytes:
        """Serialize a Python object to joblib bytes."""
        buffer = BytesIO()
        joblib.dump(obj, buffer)
        buffer.seek(0)
        return buffer.read()

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
