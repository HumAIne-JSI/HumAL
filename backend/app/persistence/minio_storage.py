"""
High-level model operations backed by MinIO.
"""
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

    def load_data(self, latest_dataset_timestamp: Union[int, str, None]) -> Optional[pd.DataFrame]:
        """Load the latest dataset from MinIO if a newer one exists.

        The method checks for objects named:
        `datasets/User Request_last_team_ANON_{timestamp}.xlsx`

        If the largest discovered `{timestamp}` is greater than `latest_dataset_timestamp`,
        the newest XLSX dataset is downloaded and loaded.

        Returns None if no newer dataset is available.
        """

        def to_int_ts(value: Union[int, str, None]) -> int:
            if value is None:
                return 0
            if isinstance(value, int):
                return value
            s = str(value).strip()

            m = re.search(r"(\d+)", s)
            return int(m.group(1)) if m else 0

        current_ts = to_int_ts(latest_dataset_timestamp)

        # Discover newest uploaded dataset XLSX object.
        # Response shape depends on the API facade; handle common variants.
        listing = self.client.list_objects(DATA_BUCKET, prefix="datasets/", filter_type="exact")

        def iter_object_names(listing_obj):
            if listing_obj is None:
                return
            if isinstance(listing_obj, list):
                for item in listing_obj:
                    if isinstance(item, str):
                        yield item
                    elif isinstance(item, dict):
                        yield (
                            item.get("object")
                            or item.get("object_name")
                            or item.get("name")
                            or item.get("key")
                        )
                return
            if isinstance(listing_obj, dict):
                if "matches" in listing_obj and isinstance(listing_obj["matches"], list):
                    yield from iter_object_names(listing_obj["matches"])
                return

        pattern = re.compile(r"^datasets/User Request_last_team_ANON_(\d+)\.xlsx$")
        newest_ts = None
        newest_object = None

        for name in iter_object_names(listing):
            if not name:
                continue
            m = pattern.match(str(name))
            if not m:
                continue
            ts = int(m.group(1))
            if newest_ts is None or ts > newest_ts:
                newest_ts = ts
                newest_object = str(name)

        if newest_ts is not None and newest_object is not None and newest_ts > current_ts:
            downloaded = self.client.download_object(DATA_BUCKET, newest_object)
            return pd.read_excel(BytesIO(downloaded))

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
