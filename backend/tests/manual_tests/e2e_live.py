"""Live end-to-end test for the HumAL API.

Drives a real uvicorn + MinIO + RabbitMQ + real LIME worker subprocess
via ``requests``.  NOT collected by ``python -m pytest tests/`` — run
directly.

Prerequisites:
  - MinIO running and populated: ``smart-finance-data`` contains
    ``datasets/{train|test}/User Request_last_team_ANON_*.xlsx``
    (ingested on startup).
  - RabbitMQ reachable at ``RABBIT_URL`` (in ``.env.al_api``).
  - ``.env.al_api`` at project root with
    ``USE_RABBITMQ=1``, ``RABBIT_URL``, ``TASK_QUEUE``, ``RESULT_QUEUE``,
    ``MINIO_BASE_URL`` / ``MINIO_USERNAME`` / ``MINIO_PASSWORD``,
    ``JWT_SECRET_KEY``, ``SENTENCE_TRANSFORMERS_CACHE_DIR``,
    ``SENTENCE_TRANSFORMERS_LOCAL_ONLY=1``, ``HF_HUB_OFFLINE=1``,
    ``TRANSFORMERS_OFFLINE=1``.
  - ``al_api_venv`` with: ``requests``, ``aio-pika``, ``lime``,
    ``scikit-learn``, ``sentence-transformers``, ``spacy`` +
    ``en_core_web_sm`` (used by ``/xai/{id}/nearest`` on the backend),
    ``pandas``, ``numpy``.
  - ``backend/sentence_transformers_cache/`` populated (offline).

Flow (10 iterations):
  /config/capabilities (poll) → register → login → /activelearning/new
  → 10×[ /next → /data/tickets → /infer_proba → /xai/{id}/nearest
  → /xai/{id}/requests → poll /xai/jobs/{job_id} →
  simulated human delay → /label-with-info ]
  → /activelearning/{id}/export → assertions

Artifacts saved to ``./artifacts/``:
  - ``instance_{id}_export.zip``
  - ``instance_{id}_benchmark_events.json``
  - ``instance_{id}_xai_result.json``
  - ``backend.log``, ``worker.log``

Invoke (from project root, using ``al_api_venv``):
    python backend/tests/manual_tests/e2e_live.py

Expected runtime ~5-10 minutes.
"""

from __future__ import annotations

import io
import json
import os
import random
import subprocess
import sys
import time
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

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
from app.persistence.minio_storage import (
    MinioService,
    RESULTS_BUCKET,
)

BASE_URL = "http://127.0.0.1:8000"
WORKER_SCRIPT = Path(__file__).resolve().parent / "xai_rabbitmq_worker.py"
ARTIFACTS_DIR = Path("artifacts").resolve()
TEST_DUCKDB_REL = "storage/db/humal_e2e_live.duckdb"

N_ITERATIONS = 10
JOB_POLL_TIMEOUT = 60
HUMAN_DELAY_MIN = 5
HUMAN_DELAY_MAX = 15

EXPECTED_ZIP_TABLES = [
    "users",
    "al_instances",
    "tickets",
    "labels",
    "label_decisions",
    "metrics",
    "al_events",
    "model_paths",
]


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------


def build_clean_env() -> dict[str, str]:
    """Return env dict for subprocesses with stripped/forced values."""
    env = os.environ.copy()
    env["USE_RABBITMQ"] = "1"
    env["RABBIT_URL"] = env.get("RABBIT_URL", "").strip()
    env["TASK_QUEUE"] = env.get("TASK_QUEUE", "xai_jobs").strip()
    env["RESULT_QUEUE"] = env.get("RESULT_QUEUE", "xai_results").strip()
    env["MESSAGE_VERSION"] = env.get("MESSAGE_VERSION", "0.1").strip()
    env["DUCKDB_PATH"] = TEST_DUCKDB_REL
    env.setdefault("SENTENCE_TRANSFORMERS_LOCAL_ONLY", "1")
    env.setdefault("HF_HUB_OFFLINE", "1")
    env.setdefault("TRANSFORMERS_OFFLINE", "1")
    return env


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def wait_for_server(timeout: int = 60) -> list[str]:
    """Poll ``GET /config/capabilities`` until the server responds."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            r = requests.get(f"{BASE_URL}/config/capabilities", timeout=5)
            if r.status_code == 200:
                caps = r.json().get("capabilities", [])
                if "xai" in caps:
                    return caps
                print(f"[e2e] Server up but capabilities={caps};"
                      f" waiting for 'xai'...", flush=True)
            else:
                print(f"[e2e] Server responded {r.status_code}", flush=True)
        except requests.ConnectionError:
            print("[e2e] Waiting for server...", flush=True)
        time.sleep(2)
    raise RuntimeError(
        f"Server did not become ready within {timeout}s"
    )


def register_and_login(username: str, password: str) -> dict[str, str]:
    """Register (tolerate 409) and login; return Authorization headers."""
    r = requests.post(
        f"{BASE_URL}/users/register",
        json={"username": username, "password": password},
    )
    if r.status_code == 409:
        pass  # already exists
    elif r.status_code != 200:
        raise RuntimeError(f"Register failed: {r.status_code} {r.text}")

    r = requests.post(
        f"{BASE_URL}/users/login",
        json={"username": username, "password": password},
    )
    if r.status_code != 200:
        raise RuntimeError(f"Login failed: {r.status_code} {r.text}")
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def get_ticket_fields(
    headers: dict[str, str], ref: str
) -> dict[str, str | None]:
    """Fetch ticket fields for *ref* via ``POST /data/tickets``."""
    r = requests.post(
        f"{BASE_URL}/data/tickets", json=[ref], headers=headers, timeout=15
    )
    assert r.status_code == 200, f"/data/tickets: {r.status_code} {r.text}"
    tickets = r.json().get("tickets", [])
    if not tickets:
        raise RuntimeError(f"No ticket data for ref={ref}")
    t = tickets[0]
    return {
        "title_anon": t.get("Title_anon"),
        "description_anon": t.get("Description_anon"),
        "service_name": t.get("Service->Name"),
        "service_subcategory_name": t.get("Service subcategory->Name"),
    }


def poll_xai_job(
    headers: dict[str, str], job_id: str, timeout: int = JOB_POLL_TIMEOUT
) -> dict[str, Any]:
    """Poll ``GET /xai/jobs/{job_id}`` until ``completed`` (or raise)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = requests.get(
            f"{BASE_URL}/xai/jobs/{job_id}", headers=headers, timeout=10
        )
        assert r.status_code in (
            200, 503,
        ), f"GET /xai/jobs/{job_id}: {r.status_code} {r.text}"
        if r.status_code == 503:
            print(
                "[e2e] GET /xai/jobs returned 503"
                " (RabbitMQ consumer not ready?), retrying...",
                flush=True,
            )
            time.sleep(2)
            continue
        body = r.json()
        st = body.get("status", "")
        if st == "completed":
            return body
        if st in ("failed",):
            raise RuntimeError(
                f"XAI job {job_id} failed: {body}"
            )
        time.sleep(1)
    raise RuntimeError(
        f"XAI job {job_id} not completed within {timeout}s"
    )


def fetch_export_zip(
    headers: dict[str, str], instance_id: int
) -> bytes:
    """Download the export ZIP for *instance_id*."""
    r = requests.get(
        f"{BASE_URL}/activelearning/{instance_id}/export",
        headers=headers,
        stream=True,
        timeout=30,
    )
    assert r.status_code == 200, (
        f"GET /activelearning/{instance_id}/export: {r.status_code}"
    )
    content_type = r.headers.get("content-type", "")
    assert "zip" in content_type, (
        f"Expected zip, got {content_type}"
    )
    return r.content


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------


def _init_minio() -> MinioService:
    client = MinioClient()
    return MinioService(client=client)


def assert_zip_tables(zip_bytes: bytes) -> dict[str, list[dict]]:
    """Unzip *zip_bytes* and assert expected JSON table files exist.

    Returns a dict ``{table_name: list_of_row_dicts}``.
    """
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = set(z.namelist())
    tables: dict[str, list[dict]] = {}
    for t in EXPECTED_ZIP_TABLES:
        path = f"duckdb/{t}.json"
        assert path in names, (
            f"Expected table file {path} not in ZIP;"
            f" found: {sorted(names)}"
        )
        tables[t] = json.loads(z.read(path).decode("utf-8"))
    return tables


def assert_minio_core_artifacts(
    minio_svc: MinioService, instance_id: int
) -> None:
    """Assert the 5 core per-instance MinIO objects exist."""
    minio_svc.load_model(al_instance_id=instance_id, model_version=0)
    minio_svc.load_label_encoder(al_instance_id=instance_id)
    minio_svc.load_one_hot_encoder(al_instance_id=instance_id)
    minio_svc.load_vectorized_tickets(
        al_instance_id=instance_id, tickets_version=0, split="train"
    )
    minio_svc.load_labels(
        al_instance_id=instance_id, labels_version=0, split="train"
    )


def assert_benchmark_events(
    minio_svc: MinioService, instance_id: int
) -> dict[str, Any]:
    """Assert benchmarking events exist; download the last one.

    Saves to ``./artifacts/instance_{id}_benchmark_events.json``.
    """
    names = minio_svc.list_benchmark_events(instance_id)
    assert names, f"No benchmark events for instance {instance_id}"
    last_name = names[-1]
    data = minio_svc.client.download_object(RESULTS_BUCKET, last_name)
    dest = ARTIFACTS_DIR / f"instance_{instance_id}_benchmark_events.json"
    dest.write_bytes(data)
    parsed = json.loads(data.decode("utf-8"))
    assert parsed, "Benchmark events payload is empty"
    return parsed


def assert_xai_result(
    minio_svc: MinioService, instance_id: int, job_id: str
) -> dict[str, Any]:
    """Download the last XAI result; assert it has LIME feature weights.

    Saves to ``./artifacts/instance_{id}_xai_result.json``.
    """
    loc = minio_svc._with_prefix(
        f"xai_results/{instance_id}/{job_id}"
    )
    object_name = f"{loc}/result.json"
    data = minio_svc.client.download_object(RESULTS_BUCKET, object_name)
    dest = ARTIFACTS_DIR / f"instance_{instance_id}_xai_result.json"
    dest.write_bytes(data)
    parsed = json.loads(data.decode("utf-8"))
    assert isinstance(parsed, list), "XAI result should be a list"
    assert parsed, "XAI result list is empty"
    first = parsed[0]
    assert "top_words" in first, (
        f"XAI result missing 'top_words'; keys: {list(first.keys())}"
    )
    assert isinstance(first["top_words"], list), (
        "'top_words' should be a list"
    )
    if first["top_words"]:
        first_pair = first["top_words"][0]
        assert isinstance(first_pair, (list, tuple)), (
            f"Expected [word, weight] pair, got {type(first_pair)}"
        )
    return parsed


def cleanup_minio(
    minio_svc: MinioService, instance_id: int
) -> None:
    """Delete all per-instance MinIO objects (incl. benchmarking)."""
    minio_svc.delete_instance_objects(instance_id)
    prefix = minio_svc._with_prefix(f"benchmarking/{instance_id}/")
    try:
        listing = minio_svc.client.list_objects(
            RESULTS_BUCKET, prefix=prefix, filter_type="exact"
        )
        for name in (listing or {}).get("matches", []):
            try:
                minio_svc.client.delete_object(RESULTS_BUCKET, name)
            except Exception:
                pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    clean_env = build_clean_env()

    worker_log = backend_log = None
    worker_proc = uvicorn_proc = None
    instance_id: int | None = None
    minio_svc: MinioService | None = None

    try:
        # ---- Start worker FIRST (must declare queues before uvicorn) ----
        worker_log = open(ARTIFACTS_DIR / "worker.log", "w", buffering=1)
        worker_proc = subprocess.Popen(
            [sys.executable, str(WORKER_SCRIPT)],
            cwd=str(BACKEND_DIR),
            env=clean_env,
            stdout=worker_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print("[e2e] Worker started, waiting 5s for queue declarations...",
              flush=True)
        time.sleep(5)

        # ---- Start uvicorn ----
        backend_log = open(ARTIFACTS_DIR / "backend.log", "w", buffering=1)
        uvicorn_proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ],
            cwd=str(BACKEND_DIR),
            env=clean_env,
            stdout=backend_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print("[e2e] uvicorn started, polling for readiness...", flush=True)

        # ---- Wait for server + RabbitMQ ----
        caps = wait_for_server()
        print(f"[e2e] Server ready, capabilities={caps}", flush=True)

        # ---- Auth ----
        username = f"e2e_user_{int(time.time())}"
        headers = register_and_login(username, "E2Epass123!")
        print(f"[e2e] Logged in as {username}", flush=True)

        # ---- Create AL instance ----
        r = requests.post(
            f"{BASE_URL}/activelearning/new",
            json={
                "model_name": "random forest",
                "qs_strategy": "random sampling",
                "class_list": ["team_a", "team_b"],
            },
            headers=headers,
            timeout=60,
        )
        assert r.status_code == 200, (
            f"POST /activelearning/new: {r.status_code} {r.text}"
        )
        instance_id = r.json()["instance_id"]
        print(f"[e2e] Created AL instance {instance_id}", flush=True)

        # ---- Build MinIO service for assertions (parent process) ----
        minio_svc = _init_minio()

        # ---- Baseline info ----
        info = requests.get(
            f"{BASE_URL}/activelearning/{instance_id}/info",
            headers=headers,
            timeout=15,
        ).json()
        f1_before = len(info.get("f1_scores", []))

        # ---- 10-iteration loop ----
        job_ids: list[str] = []
        labeled_refs: list[str] = []

        for i in range(N_ITERATIONS):
            print(f"\n[e2e] === Iteration {i + 1}/{N_ITERATIONS} ===",
                  flush=True)

            # 1) next (batch_size=1)
            nxt = requests.get(
                f"{BASE_URL}/activelearning/{instance_id}/next",
                params={"batch_size": 1},
                headers=headers,
                timeout=15,
            )
            assert nxt.status_code == 200, (
                f"GET /next: {nxt.status_code} {nxt.text}"
            )
            ref = nxt.json()["query_idx"][0]
            print(f"[e2e]   next -> {ref}", flush=True)

            # 2) Fetch full ticket fields for /xai/requests body
            ticket_fields = get_ticket_fields(headers, ref)
            print(f"[e2e]   fetched ticket data for {ref}", flush=True)

            # 3) infer_proba
            ip = requests.post(
                f"{BASE_URL}/activelearning/{instance_id}/infer_proba",
                params={"query_idx": [ref]},
                headers=headers,
                timeout=30,
            )
            assert ip.status_code == 200, (
                f"POST /infer_proba: {ip.status_code} {ip.text}"
            )
            ip_body = ip.json()
            classes = ip_body["classes"]
            probs = ip_body["probabilities"][0]
            print(f"[e2e]   inferred classes={classes}", flush=True)

            # 4) nearest
            near = requests.post(
                f"{BASE_URL}/xai/{instance_id}/nearest",
                params={"query_idx": [ref], "top_k": 1},
                headers=headers,
                timeout=15,
            )
            assert near.status_code == 200, (
                f"POST /xai/{instance_id}/nearest: {near.status_code}"
            )
            near_body = near.json()
            assert isinstance(near_body, list) and len(near_body) == 1
            print(f"[e2e]   nearest OK", flush=True)

            # 5) XAI async request (pass ticket_ref=ref so xai_result
            #    lands on the same ref's label_decisions row)
            xr = requests.post(
                f"{BASE_URL}/xai/{instance_id}/requests",
                params={"model_id": 0, "ticket_ref": ref},
                json=ticket_fields,
                headers=headers,
                timeout=15,
            )
            assert xr.status_code == 200, (
                f"POST /xai/{instance_id}/requests:"
                f" {xr.status_code} {xr.text}"
            )
            job_id = xr.json()["job_id"]
            job_ids.append(job_id)
            print(f"[e2e]   submitted XAI job {job_id}", flush=True)

            # 6) Poll until completed
            completed = poll_xai_job(headers, job_id)
            assert completed["status"] == "completed", (
                f"XAI job {job_id} not completed: {completed}"
            )
            print(f"[e2e]   XAI job {job_id} completed", flush=True)

            # 7) Simulated human delay (bracket start/end -> duration_s)
            start_dt = datetime.now(timezone.utc)
            delay = random.uniform(HUMAN_DELAY_MIN, HUMAN_DELAY_MAX)
            time.sleep(delay)
            end_dt = datetime.now(timezone.utc)
            print(f"[e2e]   human delay ~{delay:.1f}s", flush=True)

            # 8) label-with-info
            valid_classes = [c for c in classes if c is not None]
            if not valid_classes:
                raise RuntimeError(
                    f"No valid classes from infer_proba: {classes}"
                )
            pred_idx = max(range(len(probs)), key=lambda ix: probs[ix])
            raw_pred = classes[pred_idx]
            model_prediction = (
                raw_pred if raw_pred is not None else valid_classes[0]
            )
            label = valid_classes[i % len(valid_classes)]

            lbl = requests.post(
                f"{BASE_URL}/activelearning/{instance_id}/label-with-info",
                json=[
                    {
                        "ticket_id": ref,
                        "label": label,
                        "model_prediction": model_prediction,
                        "start_time": start_dt.isoformat(),
                        "end_time": end_dt.isoformat(),
                        "most_helpful_feature": "lime",
                    }
                ],
                headers=headers,
                timeout=30,
            )
            assert lbl.status_code == 200, (
                f"POST /label-with-info: {lbl.status_code} {lbl.text}"
            )
            assert lbl.json() == {"message": "Labels updated"}
            labeled_refs.append(ref)
            print(f"[e2e]   label-with-info OK (label={label},"
                  f" pred={model_prediction})", flush=True)

        # ---- Post-loop assertions ----------------------------------------

        print("\n[e2e] Running post-loop assertions...", flush=True)

        # --- iteration_ids grew by 10 ---
        info_after = requests.get(
            f"{BASE_URL}/activelearning/{instance_id}/info",
            headers=headers,
            timeout=15,
        ).json()
        f1_after = len(info_after.get("f1_scores", []))
        assert f1_after == f1_before + N_ITERATIONS, (
            f"Expected {f1_before + N_ITERATIONS} iterations,"
            f" got {f1_after}"
        )
        print(f"[e2e]   iteration_ids grew by {N_ITERATIONS}", flush=True)

        # --- All XAI jobs completed ---
        for jid in job_ids:
            r = requests.get(
                f"{BASE_URL}/xai/jobs/{jid}",
                headers=headers,
                timeout=10,
            ).json()
            assert r["status"] == "completed", (
                f"Job {jid} has status {r['status']} (not completed)"
            )
        print(f"[e2e]   all {len(job_ids)} XAI jobs completed", flush=True)

        # --- Export ZIP ---
        zip_bytes = fetch_export_zip(headers, instance_id)
        zip_dest = ARTIFACTS_DIR / f"instance_{instance_id}_export.zip"
        zip_dest.write_bytes(zip_bytes)
        tables = assert_zip_tables(zip_bytes)
        print(f"[e2e]   export ZIP tables:"
              f" { {t: len(tables[t]) for t in tables} }",
              flush=True)

        # --- Metrics row count ---
        metrics = tables["metrics"]
        assert len(metrics) >= f1_before + N_ITERATIONS, (
            f"Expected >= {f1_before + N_ITERATIONS} metrics rows,"
            f" got {len(metrics)}"
        )
        print(f"[e2e]   metrics rows = {len(metrics)}", flush=True)

        # --- al_events counts ---
        al_events = tables["al_events"]
        label_events = [
            e for e in al_events
            if e.get("action") in ("confirm_label", "override_label")
        ]
        assert len(label_events) == N_ITERATIONS, (
            f"Expected {N_ITERATIONS} label events, got {len(label_events)}"
        )
        similar_events = [
            e for e in al_events
            if e.get("action") == "similar_tickets"
        ]
        assert len(similar_events) == N_ITERATIONS, (
            f"Expected {N_ITERATIONS} similar_tickets events,"
            f" got {len(similar_events)}"
        )
        lime_events = [
            e for e in al_events if e.get("action") == "lime"
        ]
        assert len(lime_events) == N_ITERATIONS, (
            f"Expected {N_ITERATIONS} lime events, got {len(lime_events)}"
        )
        print(f"[e2e]   al_events: label={len(label_events)},"
              f" similar={len(similar_events)}, lime={len(lime_events)}",
              flush=True)

        # --- duration_s in [5, 15] ---
        in_range = [
            e for e in label_events
            if e.get("duration_s") is not None
            and HUMAN_DELAY_MIN - 0.5 <= e["duration_s"]
            <= HUMAN_DELAY_MAX + 0.5
        ]
        assert in_range, (
            f"No label event with duration_s in"
            f" [{HUMAN_DELAY_MIN},{HUMAN_DELAY_MAX}]"
        )
        print(f"[e2e]   duration_s values:"
              f" {[round(e.get('duration_s', 0), 1) for e in label_events]}",
              flush=True)

        # --- label_decisions.xai_result & similar_tickets populated ---
        ld_by_ref = {d["ref"]: d for d in tables["label_decisions"]}
        for ref in labeled_refs:
            assert ref in ld_by_ref, (
                f"label_decisions missing ref {ref}"
            )
            assert ld_by_ref[ref].get("xai_result") is not None, (
                f"label_decisions.xai_result is None for {ref}"
            )
            assert ld_by_ref[ref].get("similar_tickets") is not None, (
                f"label_decisions.similar_tickets is None for {ref}"
            )
        print(f"[e2e]   label_decisions populated for all"
              f" {len(labeled_refs)} refs", flush=True)

        # --- MinIO core artifacts ---
        assert_minio_core_artifacts(minio_svc, instance_id)
        print(f"[e2e]   MinIO core artifacts OK", flush=True)

        # --- Benchmarking events ---
        assert_benchmark_events(minio_svc, instance_id)
        print(f"[e2e]   benchmarking events OK", flush=True)

        # --- XAI result ---
        assert_xai_result(minio_svc, instance_id, job_ids[-1])
        print(f"[e2e]   XAI result has LIME feature weights", flush=True)

        print(f"\n{'=' * 60}", flush=True)
        print(f"  E2E LIVE TEST PASSED  (instance {instance_id})",
              flush=True)
        print(f"{'=' * 60}", flush=True)

    except Exception:
        print("[e2e] FAILED", flush=True)
        traceback.print_exc()
        raise

    finally:
        # ---- Teardown ----
        print("\n[e2e] Tearing down...", flush=True)

        # Terminate uvicorn
        if uvicorn_proc is not None:
            print("[e2e] Terminating uvicorn...", flush=True)
            uvicorn_proc.terminate()
            try:
                uvicorn_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                uvicorn_proc.kill()
                uvicorn_proc.wait()

        # Terminate worker
        if worker_proc is not None:
            print("[e2e] Terminating worker...", flush=True)
            worker_proc.terminate()
            try:
                worker_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                worker_proc.kill()
                worker_proc.wait()

        # Close log files
        for f in (backend_log, worker_log):
            if f is not None:
                try:
                    f.close()
                except Exception:
                    pass

        # Delete test DuckDB (after uvicorn is dead so Windows releases)
        for suffix in ("", ".wal"):
            p = BACKEND_DIR / (TEST_DUCKDB_REL + suffix)
            try:
                p.unlink()
                print(f"[e2e] Deleted {p}", flush=True)
            except FileNotFoundError:
                pass

        # Delete per-instance MinIO objects
        if minio_svc is not None and instance_id is not None:
            try:
                cleanup_minio(minio_svc, instance_id)
                print(f"[e2e] Cleaned up MinIO objects for instance"
                      f" {instance_id}", flush=True)
            except Exception:
                print("[e2e] MinIO cleanup failed (non-fatal)", flush=True)
                traceback.print_exc()

        print("[e2e] Teardown complete", flush=True)


if __name__ == "__main__":
    main()
