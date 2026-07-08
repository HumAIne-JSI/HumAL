"""Real RabbitMQ XAI worker for the HumAL live e2e test.

Replaces (does not delete) xai_rabbitmq_simulator.py. Runs real LIME
explanations (10 features, 1000 samples, per top-k class) matching
XaiService.explain_lime semantics.

Prerequisites:
  - RabbitMQ reachable at RABBIT_URL (default from .env.al_api).
  - MinIO reachable (MINIO_BASE_URL / USERNAME / PASSWORD in .env.al_api)
    with the per-instance artifacts already uploaded by
    POST /activelearning/new and POST /xai/{id}/requests.
  - sentence_transformers_cache populated locally + offline flags set
    (SENTENCE_TRANSFORMERS_LOCAL_ONLY=1, HF_HUB_OFFLINE=1,
    TRANSFORMERS_OFFLINE=1) — no internet.
  - cloudpickle, joblib, lime, pandas, numpy, aio_pika, scikit-learn,
    sentence-transformers installed (al_api_venv).

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
import time
from pathlib import Path
from typing import Any

import aio_pika
import numpy as np
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


def _init_minio() -> MinioService:
    client = MinioClient()
    return MinioService(client=client)


def run_lime(payload: dict) -> list[dict]:
    """Execute real LIME on the ticket described in *payload*.

    Returns a **flat** list of per-class dicts (``{class, top_words, error}``)
    that the backend ``update_xai_job`` walker can parse.
    """
    al_instance_id: int = payload["al_instance_id"]
    model_id: int = payload.get("model_id", 0)
    artifacts: dict = payload["artifacts"]
    job_id: str = payload["job_id"]

    minio_svc = _init_minio()
    _client = minio_svc.client

    try:
        # --- Download the saved ticket ---
        raw = _client.download_object(
            "smart-finance-data", artifacts["ticket"]
        )
        ticket = Data.model_validate_json(raw.decode("utf-8"))

        # --- Download model, encoders & vectorizer from the canonical locations ---
        model = minio_svc.load_model(al_instance_id=al_instance_id, model_version=model_id)
        le = minio_svc.load_label_encoder(al_instance_id=al_instance_id)
        oh = minio_svc.load_one_hot_encoder(al_instance_id=al_instance_id)
        vectorizer = minio_svc.load_ticket_vectorizer(al_instance_id=al_instance_id)
        vectorizer.set_one_hot_encoder(oh)
        vectorizer.set_base_ticket(ticket.model_dump())

        # --- Build the LIME input text ---
        text = (ticket.title_anon or "") + " " + (ticket.description_anon or "")

        # --- Determine top-k classes via baseline prediction ---
        classes = le.classes_.tolist()
        valid_idx = [i for i, c in enumerate(classes) if c is not None]
        if not valid_idx:
            err = f"No valid classes found in label encoder for instance {al_instance_id}"
            print(f"[worker] {err}", flush=True)
            return [{"class": None, "top_words": [], "error": err}]

        base_proba = model.predict_proba(
            vectorizer.transform_with_base_ticket([text])
        )[0]
        top_k = min(TOP_K, len(valid_idx))
        sorted_idx = np.argsort(base_proba)[::-1][:top_k]

        # --- LIME explainer ---
        explainer = LimeTextExplainer(class_names=le.classes_)

        def _predict_proba(texts):
            return model.predict_proba(
                vectorizer.transform_with_base_ticket(texts)
            )

        explanation = explainer.explain_instance(
            text,
            _predict_proba,
            num_features=10,
            num_samples=1000,
            labels=tuple(sorted_idx),
        )

        # --- Build flat output list ---
        out: list[dict] = []
        for idx in sorted_idx:
            out.append(
                {
                    "class": classes[idx],
                    "top_words": [
                        [w, float(s)] for w, s in explanation.as_list(label=idx)
                    ],
                    "error": None,
                }
            )
        return out

    except Exception as exc:
        print(f"[worker] LIME error for job {job_id}: {exc}", flush=True)
        return [
            {
                "class": None,
                "top_words": [],
                "error": f"LIME error: {exc}",
            }
        ]


def build_result_message(payload: dict, lime_output: list[dict]) -> dict:
    """Write ``result.json`` to MinIO and return the RESULT_QUEUE message."""
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

                lime_output = run_lime(payload)
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
