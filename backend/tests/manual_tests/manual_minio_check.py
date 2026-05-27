"""
Simple MinIO smoke check for MinioService.

Requires MINIO_BASE_URL, MINIO_USERNAME, MINIO_PASSWORD env vars.
Optional: MINIO_PREFIX to namespace objects (e.g. test/) inside each bucket.
This script performs real uploads/downloads; verify results in your MinIO UI.
"""
from dotenv import load_dotenv
load_dotenv()

from io import BytesIO
import json
import pandas as pd
import numpy as np
import time
from app.core.minio_client import MinioClient
from app.persistence.minio_storage import MinioService, MODELS_BUCKET, DATA_BUCKET


def main():
    al_instance_id = 12
    model_version = 0
    tickets_version = 0

    client = MinioClient()
    svc = MinioService(client)

    # Model round trip
    model_obj = {"model": "demo", "ts": al_instance_id}
    print(f"Uploading model to bucket={MODELS_BUCKET} object=models/{al_instance_id}/{model_version}.joblib")
    
    start = time.time()
    save_result = svc.save_model(
        al_instance_id=al_instance_id,
        model_version=model_version,
        model=model_obj,
        metadata={"stage": "smoke"},
    )
    save_time = time.time() - start
    print("Save result:", save_result)
    print(f"Model save time: {save_time:.4f}s")

    start = time.time()
    loaded_model = svc.load_model(al_instance_id=al_instance_id, model_version=model_version)
    load_time = time.time() - start
    print("Loaded model:", loaded_model)
    print(f"Model load time: {load_time:.4f}s")

    start = time.time()
    metadata = svc.load_metadata(al_instance_id=al_instance_id, model_version=model_version)
    metadata_time = time.time() - start
    print("Metadata:", metadata)
    print(f"Metadata load time: {metadata_time:.4f}s")

    # Encoders round trip
    label_encoder_obj = ["alpha", "gamma", "delta"]
    one_hot_encoder_obj = {"cats": [0, 1]}

    print(f"\nUploading label encoder to encoders/{al_instance_id}/label_encoder.joblib")
    start = time.time()
    label_res = svc.save_label_encoder(al_instance_id=al_instance_id, encoder=label_encoder_obj)
    label_save_time = time.time() - start
    print("Label encoder save result:", label_res)
    print(f"Label encoder save time: {label_save_time:.4f}s")

    print(f"Uploading one-hot encoder to encoders/{al_instance_id}/one_hot_encoder.joblib")
    start = time.time()
    ohe_res = svc.save_one_hot_encoder(al_instance_id=al_instance_id, encoder=one_hot_encoder_obj)
    ohe_save_time = time.time() - start
    print("One-hot encoder save result:", ohe_res)
    print(f"One-hot encoder save time: {ohe_save_time:.4f}s")

    start = time.time()
    loaded_label = svc.load_label_encoder(al_instance_id=al_instance_id)
    label_load_time = time.time() - start
    print("Loaded label encoder:", loaded_label)
    print(f"Label encoder load time: {label_load_time:.4f}s")

    start = time.time()
    loaded_ohe = svc.load_one_hot_encoder(al_instance_id=al_instance_id)
    ohe_load_time = time.time() - start
    print("Loaded one-hot encoder:", loaded_ohe)
    print(f"One-hot encoder load time: {ohe_load_time:.4f}s")

    # Vectorized tickets round trip
    print(f"\nUploading vectorized tickets to vectorized_tickets/{al_instance_id}/{tickets_version}.parquet")
    tickets_df = pd.DataFrame({
        "embedding_1": np.random.rand(10),
        "embedding_2": np.random.rand(10),
        "embedding_3": np.random.rand(10),
        "label": ["A", "B", "C", "A", "B", "C", "A", "B", "C", "A"],
    })
    print("Sample tickets DataFrame:\n", tickets_df.head())
    
    start = time.time()
    tickets_res = svc.save_vectorized_tickets(
        al_instance_id=al_instance_id,
        tickets_version=tickets_version,
        df=tickets_df,
    )
    tickets_save_time = time.time() - start
    print("Save result:", tickets_res)
    print(f"Vectorized tickets save time: {tickets_save_time:.4f}s")

    start = time.time()
    loaded_tickets = svc.load_vectorized_tickets(
        al_instance_id=al_instance_id,
        tickets_version=tickets_version,
    )
    tickets_load_time = time.time() - start
    print("Loaded vectorized tickets:\n", loaded_tickets.head())
    print("Tickets shape:", loaded_tickets.shape)
    print(f"Vectorized tickets load time: {tickets_load_time:.4f}s")

    # Check for newer datasets XLSX (load_data returns all datasets newer than timestamp, or None)
    print(f"\nChecking for newer datasets XLSX from MinIO")
    latest_dataset_timestamp = "2026-01-24T00:00:00Z"

    start = time.time()
    maybe_new_data = svc.load_data(latest_dataset_timestamp)
    load_time = time.time() - start
    if maybe_new_data is None:
        print(f"No newer datasets found (latest_dataset_timestamp={latest_dataset_timestamp}).")
        print(f"Check time: {load_time:.4f}s")
    else:
        print(f"New datasets loaded in {load_time:.4f}s")
        print("New datasets head:\n", maybe_new_data.head())
        print("New datasets shape:", maybe_new_data.shape)

    print("\nDone. Verify objects exist in MinIO if needed.")


if __name__ == "__main__":
    main()
