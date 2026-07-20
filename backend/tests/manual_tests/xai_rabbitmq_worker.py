"""Real RabbitMQ XAI worker for the HumAL live e2e test.

Replaces (does not delete) xai_rabbitmq_simulator.py. Runs real LIME
explanations (10 features, 250 samples, per top-k class).

Emits the ``XaiWorkerResult`` schema (``schema_version: 1``) — the
current external-worker contract.  On LIME failure the worker publishes
``status="failed"`` (no result file) instead of ``"completed"``.

Prerequisites:
  - RabbitMQ reachable at RABBIT_URL (default from .env.al_api).
  - The HumAL backend API reachable at API_BASE_URL (default
    http://127.0.0.1:8000) with the AL instance trained, so
    POST /activelearning/{id}/infer_proba can serve batch inference.
  - MinIO reachable (MINIO_BASE_URL / USERNAME / PASSWORD in .env.al_api)
    for downloading the saved ticket (artifacts["ticket"]) and uploading
    result.json. Per-instance model/encoder/vectorizer artifacts are NOT
    loaded by this worker — inference is delegated to the API.
  - lime, numpy, aio_pika, requests installed (al_api_venv).

Consumes TASK_QUEUE, runs LIME, writes
{MINIO_PREFIX}/xai_results/{al_instance_id}/{job_id}/result.json
to smart-finance-results, and publishes a completion message to
RESULT_QUEUE so the backend's update_xai_job callback marks the job
completed.

Invoke (from project root, using al_api_venv):
    python backend/tests/manual_tests/xai_rabbitmq_worker.py
Or spawned automatically by e2e_live.py.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import aio_pika
import numpy as np
import requests
from aio_pika import Message
from dotenv import load_dotenv
from lime.lime_text import LimeTextExplainer

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

ENV_FILE = PROJECT_ROOT / ".env.al_api"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv(PROJECT_ROOT / ".env")

from app.core.minio_client import MinioClient
from app.data_models.active_learning_dm import Data
from app.persistence.minio_storage import MinioService, RESULTS_BUCKET

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@localhost/").strip()
TASK_QUEUE = os.getenv("TASK_QUEUE", "xai_jobs").strip()
RESULT_QUEUE = os.getenv("RESULT_QUEUE", "xai_results").strip()
MESSAGE_VERSION = os.getenv("MESSAGE_VERSION", "0.1").strip()
TOP_K = int(os.getenv("XAI_LIME_TOP_K", "1"))
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").strip().rstrip("/")
NUM_SAMPLES = int(os.getenv("XAI_LIME_NUM_SAMPLES", "250"))


def _init_minio() -> MinioService:
    client = MinioClient()
    return MinioService(client=client)


def _infer_proba(al_instance_id: int, data_list: list[dict]) -> tuple[list, list[list[float]]]:
    url = f"{API_BASE_URL}/activelearning/{al_instance_id}/infer_proba"
    resp = requests.post(url, json=data_list, timeout=120)
    resp.raise_for_status()
    body = resp.json()
    return body["classes"], body["probabilities"]


def run_lime(payload: dict) -> dict:
    """Execute real LIME on the ticket described in *payload*.

    Inference is delegated to the backend ``POST /infer_proba`` endpoint,
    so no model/encoder/vectorizer artifacts are loaded by this worker.

    Returns a dict matching the ``XaiWorkerResult`` schema (external worker
    contract, ``schema_version: 1``).  Raises on failure — the caller
    (`on_task`) publishes ``status="failed"`` instead of ``"completed"``.
    """
    al_instance_id: int = payload["al_instance_id"]
    artifacts: dict = payload["artifacts"]
    job_id: str = payload["job_id"]
    ticket_index: str = payload.get("ticket_sha", job_id)

    minio_svc = _init_minio()
    _client = minio_svc.client

    # --- Download the saved ticket ---
    raw = _client.download_object("smart-finance-data", artifacts["ticket"])
    ticket = Data.model_validate_json(raw.decode("utf-8"))

    # --- Build the LIME input text ---
    text = (ticket.title_anon or "") + " " + (ticket.description_anon or "")

    def _build_data(texts):
        return [
            {
                "title_anon": str(t),
                "description_anon": "",
                "service_name": ticket.service_name,
                "service_subcategory_name": ticket.service_subcategory_name,
            }
            for t in texts
        ]

    # --- Determine top-k classes via baseline prediction ---
    classes, probabilities = _infer_proba(al_instance_id, _build_data([text]))
    base_proba = probabilities[0]

    valid_idx = [i for i, c in enumerate(classes) if c is not None]
    if not valid_idx:
        raise ValueError(f"No valid classes found for instance {al_instance_id}")

    top_k = min(TOP_K, len(valid_idx))
    sorted_idx = list(np.argsort(base_proba)[::-1][:top_k])

    # --- LIME explainer ---
    explainer = LimeTextExplainer(class_names=classes)

    def _predict_proba(texts):
        _, probs = _infer_proba(al_instance_id, _build_data(texts))
        return np.array(probs)

    explanation = explainer.explain_instance(
        text,
        _predict_proba,
        num_features=10,
        num_samples=NUM_SAMPLES,
        labels=tuple(sorted_idx),
    )

    # --- Build predictions array (new external-worker schema) ---
    predictions = []
    for rank, idx in enumerate(sorted_idx, start=1):
        class_idx = int(idx)
        label = str(classes[class_idx])
        proba = float(base_proba[class_idx])
        class_weights = [
            [w, float(s)] for w, s in explanation.as_list(label=class_idx)
        ]
        class_max_abs = max((abs(s) for _, s in class_weights), default=1.0)
        if class_max_abs == 0:
            class_max_abs = 1.0
        predictions.append({
            "rank": rank,
            "class_index": class_idx,
            "label": label,
            "probability": proba,
            "lime": {
                "word_weights": class_weights,
                "highlighted_tokens": [
                    {
                        "token": str(w),
                        "weight": float(s),
                        "direction": "support" if s > 0 else ("oppose" if s < 0 else "neutral"),
                        "intensity": abs(s) / class_max_abs,
                    }
                    for w, s in class_weights
                ],
            },
        })

    return {
        "schema_version": 1,
        "ticket_sha": ticket_index,
        "text": text,
        "predictions": predictions,
    }


def build_result_message(payload: dict, lime_output: dict) -> dict:
    """Write ``result.json`` to MinIO and return the ``status="completed"`` RESULT_QUEUE message.

    Called only on success.  On failure the caller publishes ``status="failed"``
    without writing any result file.
    """
    job_id: str = payload["job_id"]
    al_instance_id: int = payload["al_instance_id"]

    minio_svc = _init_minio()
    _client = minio_svc.client

    result_location = minio_svc._with_prefix(
        f"xai_results/{al_instance_id}/{job_id}"
    )
    object_name = f"{result_location}/result.json"
    payload_bytes = json.dumps(lime_output, default=str).encode("utf-8")
    _client.upload_file_bytes(
        RESULTS_BUCKET, object_name, payload_bytes, filename="result.json"
    )
    print(
        f"[worker] Wrote {len(payload_bytes)} bytes to"
        f" {RESULTS_BUCKET}/{object_name}",
        flush=True,
    )

    return {
        "version": MESSAGE_VERSION,
        "job_id": str(job_id),
        "status": "completed",
        "result_location": result_location,
        "result_file_names": ["result.json"],
    }


async def main() -> None:
    print(f"[worker] Connecting to RabbitMQ: {RABBIT_URL}", flush=True)
    connection = await aio_pika.connect_robust(RABBIT_URL)

    async with connection:
        channel = await connection.channel()

        # Declare both queues durably so the backend's passive-declare succeeds.
        await channel.declare_queue(TASK_QUEUE, durable=True)
        await channel.declare_queue(RESULT_QUEUE, durable=True)

        task_queue = await channel.declare_queue(TASK_QUEUE, durable=True)

        print(
            f"[worker] Waiting for tasks on '{TASK_QUEUE}'"
            f" (publishing results to '{RESULT_QUEUE}')",
            flush=True,
        )

        async def on_task(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            async with message.process():
                try:
                    payload = json.loads(message.body.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    print(f"[worker] Invalid JSON: {exc}", flush=True)
                    return

                jid = payload.get("job_id", "?")
                aid = payload.get("al_instance_id", "?")
                print(
                    f"[worker] Received job_id={jid} al_instance_id={aid}",
                    flush=True,
                )

                try:
                    lime_output = run_lime(payload)
                except Exception as exc:
                    print(f"[worker] LIME error for job_id={jid}: {exc}", flush=True)
                    result_message = {
                        "version": MESSAGE_VERSION,
                        "job_id": str(jid),
                        "status": "failed",
                    }
                    await channel.default_exchange.publish(
                        Message(
                            body=json.dumps(result_message).encode("utf-8"),
                            delivery_mode=2,
                        ),
                        routing_key=RESULT_QUEUE,
                    )
                    print(
                        f"[worker] Published failed result for job_id={jid}",
                        flush=True,
                    )
                    return

                result_message = build_result_message(payload, lime_output)

                await channel.default_exchange.publish(
                    Message(
                        body=json.dumps(result_message).encode("utf-8"),
                        delivery_mode=2,
                    ),
                    routing_key=RESULT_QUEUE,
                )
                print(
                    f"[worker] Published completed result for job_id={jid}",
                    flush=True,
                )

        await task_queue.consume(on_task)
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[worker] Stopped", flush=True)
