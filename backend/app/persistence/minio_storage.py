"""
High-level model operations backed by MinIO.
"""
from datetime import datetime
from io import BytesIO
import re
from typing import Any, Dict, Optional, Union
import joblib
import pandas as pd
from app.core.minio_client import MinioClient


# MinIO bucket names
MODELS_BUCKET = "smart-finance-models"
DATA_BUCKET = "smart-finance-data"


class MinioService:
    def __init__(self, client: MinioClient):
        self.client = client

    def save_model(
        self,
        *,
        al_instance_id: int,
        model_version: int,
        model: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Upload a model (as Python object) and optionally attach metadata."""
        object_name = f"models/{al_instance_id}/{model_version}.joblib"
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
        object_name = f"models/{al_instance_id}/{model_version}.joblib"
        downloaded = self.client.download_object(MODELS_BUCKET, object_name)
        return joblib.load(BytesIO(downloaded))

    def load_metadata(
        self,
        *,
        al_instance_id: int,
        model_version: int,
    ) -> Dict[str, Any]:
        """Fetch object metadata for a stored model."""
        object_name = f"models/{al_instance_id}/{model_version}.joblib"
        return self.client.get_metadata(MODELS_BUCKET, object_name)

    def save_label_encoder(
        self,
        *,
        al_instance_id: int,
        encoder: Any,
    ):
        """Upload a label encoder (as Python object)."""
        object_name = f"encoders/{al_instance_id}/label_encoder.joblib"
        encoder_bytes = self._to_joblib(encoder)
        self.client.upload_file_bytes(MODELS_BUCKET, object_name, encoder_bytes)
        return {"bucket": MODELS_BUCKET, "object": object_name}

    def load_label_encoder(
        self,
        *,
        al_instance_id: int,
    ):
        """Download and deserialize a label encoder from MinIO."""
        object_name = f"encoders/{al_instance_id}/label_encoder.joblib"
        downloaded = self.client.download_object(MODELS_BUCKET, object_name)
        return joblib.load(BytesIO(downloaded))

    def save_one_hot_encoder(
        self,
        *,
        al_instance_id: int,
        encoder: Any,
    ):
        """Upload a one-hot encoder (as Python object)."""
        object_name = f"encoders/{al_instance_id}/one_hot_encoder.joblib"
        encoder_bytes = self._to_joblib(encoder)
        self.client.upload_file_bytes(MODELS_BUCKET, object_name, encoder_bytes)
        return {"bucket": MODELS_BUCKET, "object": object_name}

    def load_one_hot_encoder(
        self,
        *,
        al_instance_id: int,
    ):
        """Download and deserialize a one-hot encoder from MinIO."""
        object_name = f"encoders/{al_instance_id}/one_hot_encoder.joblib"
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

        pattern = re.compile(rf"^datasets/{split}/User Request_last_team_ANON_(\d{{8}}T\d{{6}})\.xlsx$")
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

    def save_vectorized_tickets(
        self,
        *,
        al_instance_id: int,
        tickets_version: int,
        df: pd.DataFrame,
    ):
        """Upload vectorized tickets as Parquet format."""
        object_name = f"vectorized_tickets/{al_instance_id}/{tickets_version}.parquet"
        tickets_bytes = self._to_parquet(df)
        self.client.upload_file_bytes(DATA_BUCKET, object_name, tickets_bytes)
        return {"bucket": DATA_BUCKET, "object": object_name}

    def load_vectorized_tickets(
        self,
        *,
        al_instance_id: int,
        tickets_version: int,
    ) -> pd.DataFrame:
        """Download and deserialize vectorized tickets from MinIO."""
        object_name = f"vectorized_tickets/{al_instance_id}/{tickets_version}.parquet"
        downloaded = self.client.download_object(DATA_BUCKET, object_name)
        return pd.read_parquet(BytesIO(downloaded))

    def _to_joblib(self, obj: Any) -> bytes:
        """Serialize a Python object to joblib bytes."""
        buffer = BytesIO()
        joblib.dump(obj, buffer)
        buffer.seek(0)
        return buffer.read()

    def _to_parquet(self, df: pd.DataFrame) -> bytes:
        """Serialize a DataFrame to Parquet bytes."""
        buffer = BytesIO()
        df.to_parquet(buffer)
        buffer.seek(0)
        return buffer.read()
