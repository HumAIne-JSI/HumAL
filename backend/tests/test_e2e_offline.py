"""End-to-end offline integration test for the HumAL API.

Exercises the full active-learning loop against the real FastAPI app via
``TestClient`` with mocked infrastructure (MinioClient, SentenceTransformer,
spacy.load -- all set up in ``conftest.py``) while keeping the real
``ActiveLearningService``, ``InferenceService`` and ``XaiService`` code paths.

Run:  cd backend && python -m pytest tests/test_e2e_offline.py -v
"""
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

# Defensive re-assertion of JWT env (matches the convention in test_routers/*).
os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from app.core import dependencies
from app.config.config import SYSTEM_USER_ID
from app.main import app
from app.persistence.duckdb import init_database
from app.persistence.local_artifacts import LocalArtifactsStore

# --- Dataset sizing ---
NUM_LABELED_TRAIN = 50   # == MIN_INITIAL_LABELED (active_learning_svc.py:36)
NUM_UNLABELED_TRAIN = 15  # unlabeled pool for `next` to query (>= 10 for the loop)
NUM_TEST = 10
CLASSES = ["Team A", "Team B"]


def _build_tickets_df(n: int, prefix: str) -> pd.DataFrame:
    """Build a tickets DataFrame in the CSV-style column names expected by upsert_tickets_df."""
    refs = [f"{prefix}{i:03d}" for i in range(1, n + 1)]
    return pd.DataFrame({
        "Ref": refs,
        "Service subcategory->Name": ["SubCat A" if i % 2 == 0 else "SubCat B" for i in range(n)],
        "Service->Name": ["Service A" if i % 2 == 0 else "Service B" for i in range(n)],
        "Request Type": ["Incident"] * n,
        "Last team ID->Name": [None] * n,                 # dispatch_team keeps only isna() rows
        "Title_anon": [f"Title {prefix} {i}" for i in range(1, n + 1)],
        "Description_anon": [f"Description {prefix} {i} with some text." for i in range(1, n + 1)],
        "Public_log_anon": [None] * n,
    })


def _seed_duckdb(duckdb_service) -> None:
    """Seed the temp DuckDB with tickets + ground-truth labels (al_instance_id=0)."""
    train_df = _build_tickets_df(NUM_LABELED_TRAIN + NUM_UNLABELED_TRAIN, "TR")
    test_df = _build_tickets_df(NUM_TEST, "TE")

    duckdb_service.upsert_tickets_df(train_df, split="train")
    duckdb_service.upsert_tickets_df(test_df, split="test")

    # >=50 labeled train rows (alternating classes) -> passes MIN_INITIAL_LABELED.
    train_refs = train_df["Ref"].tolist()
    train_labels = {ref: CLASSES[i % 2] for i, ref in enumerate(train_refs[:NUM_LABELED_TRAIN])}
    duckdb_service.save_labels(
        al_instance_id=0, user_id=SYSTEM_USER_ID, labels_dict=train_labels, split="train",
    )

    # Test labels with both classes (needed for roc_auc in calculate_metrics).
    test_refs = test_df["Ref"].tolist()
    test_labels = {ref: CLASSES[i % 2] for i, ref in enumerate(test_refs)}
    duckdb_service.save_labels(
        al_instance_id=0, user_id=SYSTEM_USER_ID, labels_dict=test_labels, split="test",
    )


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Yield a TestClient backed by a fresh temp DuckDB and temp artifact dirs."""
    db_path = Path(os.environ["DUCKDB_PATH"])

    # Reset the DuckDB file (init_database only drops on schema-version mismatch,
    # so delete the file + WAL first to guarantee a clean state every run).
    for p in (db_path, Path(str(db_path) + ".wal")):
        if p.exists():
            p.unlink()
    init_database(db_path)  # recreates schema, system user, ground-truth instance 0

    duckdb = dependencies.duckdb_persistence_service
    _seed_duckdb(duckdb)

    # Redirect local artifacts to fresh temp dirs so create_instance never writes
    # into backend/storage/ (the import-time singleton still defaults vectorized_data_dir
    # to backend/storage/vectorized_data, which is git-ignored and left empty).
    artifacts = LocalArtifactsStore(
        models_dir=tmp_path / "models",
        encoders_dir=tmp_path / "encoders",
        vectorized_data_dir=tmp_path / "vectorized",
    )
    dependencies.al_service.local_artifacts_store = artifacts
    dependencies.inference_service.local_artifacts_store = artifacts
    dependencies.xai_service.local_artifacts_store = artifacts

    # Clear the in-memory storage singleton (stale instances from prior runs).
    for d in (
        dependencies.storage.al_instances_dict,
        dependencies.storage.dataset_dict,
        dependencies.storage.model_paths_dict,
        dependencies.storage.results_dict,
        dependencies.storage.skipped_tickets,
    ):
        d.clear()

    # No-op startup so the FastAPI lifespan doesn't pull data from MinIO.
    class _NoopStartup:
        def load_data_from_minio_into_duckdb(self):
            return None

    monkeypatch.setattr(dependencies, "startup_service", _NoopStartup())

    with TestClient(app) as test_client:
        yield test_client


def _auth(client) -> dict:
    """Register + login alice, return Authorization headers."""
    client.post("/users/register", json={"username": "alice", "password": "secret"})
    resp = client.post("/users/login", json={"username": "alice", "password": "secret"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_e2e_offline_active_learning_loop(client):
    """Full AL loop: register -> login -> new -> 10x[next, label-with-info,
    infer_proba, nearest, explain_lime] with persistence assertions."""
    duckdb = dependencies.duckdb_persistence_service
    headers = _auth(client)

    # --- Create an AL instance (real create_instance -> dispatch_team -> train -> metrics) ---
    new_resp = client.post(
        "/activelearning/new",
        json={"model_name": "random forest", "qs_strategy": "random sampling", "class_list": CLASSES},
        headers=headers,
    )
    assert new_resp.status_code == 200, new_resp.text
    instance_id = new_resp.json()["instance_id"]
    assert isinstance(instance_id, int) and instance_id > 0

    # --- Async XAI endpoints must 503 with RabbitMQ disabled (USE_RABBITMQ=0 in conftest) ---
    r503 = client.post(
        f"/xai/{instance_id}/requests",
        params={"model_id": 0},
        json={"title_anon": "t", "description_anon": "d"},
        headers=headers,
    )
    assert r503.status_code == 503
    r503job = client.get(f"/xai/jobs/{uuid.uuid4()}", headers=headers)
    assert r503job.status_code == 503

    # --- Baseline metrics / iteration state ---
    info_before = client.get(f"/activelearning/{instance_id}/info", headers=headers)
    assert info_before.status_code == 200, info_before.text
    f1_before = len(info_before.json().get("f1_scores", []))
    metrics_before = len(duckdb.load_all_metrics(instance_id))
    assert metrics_before >= 1  # create_instance already wrote iteration 1

    labeled_refs = []

    for i in range(10):
        # 1) next (batch_size=1 -> one unlabeled ref)
        nxt = client.get(
            f"/activelearning/{instance_id}/next", params={"batch_size": 1}, headers=headers,
        )
        assert nxt.status_code == 200, nxt.text
        qidx = nxt.json()["query_idx"]
        assert isinstance(qidx, list) and len(qidx) == 1
        ref = qidx[0]
        labeled_refs.append(ref)

        # 2) label-with-info (triggers benchmark_export on the 10th iteration)
        start = datetime(2026, 1, 1, 0, 0, 0)
        end = start + timedelta(seconds=i + 1)
        lbl = client.post(
            f"/activelearning/{instance_id}/label-with-info",
            json=[{
                "ticket_id": ref,
                "label": CLASSES[i % 2],
                "model_prediction": None,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "most_helpful_feature": None,
            }],
            headers=headers,
        )
        assert lbl.status_code == 200, lbl.text
        assert lbl.json() == {"message": "Labels updated"}

        # 3) infer_proba (verify model updates after retrain)
        ip = client.post(
            f"/activelearning/{instance_id}/infer_proba",
            params={"query_idx": [ref]},
            headers=headers,
        )
        assert ip.status_code == 200, ip.text
        ip_body = ip.json()
        assert "classes" in ip_body and "probabilities" in ip_body
        assert len(ip_body["probabilities"]) == 1
        assert len(ip_body["probabilities"][0]) == len(ip_body["classes"])
        assert "Team A" in ip_body["classes"] and "Team B" in ip_body["classes"]

        # 4) nearest (similar tickets) via query_idx
        near = client.post(
            f"/xai/{instance_id}/nearest",
            params={"query_idx": [ref], "top_k": 1},
            headers=headers,
        )
        assert near.status_code == 200, near.text
        near_body = near.json()
        assert isinstance(near_body, list) and len(near_body) == 1
        assert near_body[0]["query_idx"] == ref

        # 5) explain_lime via query_idx (populates label_decisions.xai_result)
        lime = client.post(
            f"/xai/{instance_id}/explain_lime",
            params={"query_idx": [ref], "top_k": 1},
            headers=headers,
        )
        assert lime.status_code == 200, lime.text
        lime_body = lime.json()
        assert isinstance(lime_body, list) and len(lime_body) == 1

    # --- Persistence assertions ---

    # metrics row count grew by 10 (one calculate_metrics per label-with-info).
    metrics_after = len(duckdb.load_all_metrics(instance_id))
    assert metrics_after == metrics_before + 10, (metrics_before, metrics_after)

    # GET /info shows a new iteration (f1_scores list grew; num_labeled increased).
    info_after = client.get(f"/activelearning/{instance_id}/info", headers=headers)
    assert info_after.status_code == 200
    f1_after = len(info_after.json().get("f1_scores", []))
    assert f1_after == f1_before + 10
    assert info_after.json()["num_labeled"][-1] > info_before.json()["num_labeled"][-1]

    # al_events: 10 label (confirm/override), 10 similar_tickets, 10 lime.
    assert len(duckdb.get_al_events(instance_id, actions=["confirm_label", "override_label"])) == 10
    assert len(duckdb.get_al_events(instance_id, actions=["similar_tickets"])) == 10
    assert len(duckdb.get_al_events(instance_id, actions=["lime"])) == 10

    # label_decisions.xai_result (and similar_tickets) populated for every labeled ref.
    for ref in labeled_refs:
        ld = duckdb.get_label_decision(al_instance_id=instance_id, ref=ref)
        assert ld is not None, ref
        assert ld["xai_result"] is not None, ref
        assert ld["similar_tickets"] is not None, ref

    # 10th-label benchmarking export fired exactly once.
    assert len(duckdb.get_al_events(instance_id, actions=["benchmark_export"])) == 1


def test_e2e_all_idk_batch_skips_retrain_and_retires_ticket(client):
    """Submit an i_dont_know batch and verify no retrain, no re-surface, survive restart rebuild."""
    duckdb = dependencies.duckdb_persistence_service
    headers = _auth(client)

    # --- Create an AL instance ---
    new_resp = client.post(
        "/activelearning/new",
        json={"model_name": "random forest", "qs_strategy": "random sampling", "class_list": CLASSES},
        headers=headers,
    )
    assert new_resp.status_code == 200, new_resp.text
    instance_id = new_resp.json()["instance_id"]

    # --- Baseline metrics ---
    metrics_before = len(duckdb.load_all_metrics(instance_id))
    assert metrics_before >= 1

    # --- Get a ref from 'next' ---
    nxt = client.get(
        f"/activelearning/{instance_id}/next", params={"batch_size": 1}, headers=headers,
    )
    assert nxt.status_code == 200, nxt.text
    qidx = nxt.json()["query_idx"]
    assert isinstance(qidx, list) and len(qidx) == 1
    ref = qidx[0]

    # --- Submit an all-idk batch (no label) ---
    start = datetime(2026, 6, 1, 0, 0, 0)
    end = start + timedelta(seconds=5)
    lbl = client.post(
        f"/activelearning/{instance_id}/label-with-info",
        json=[{
            "ticket_id": ref,
            "i_dont_know": True,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }],
        headers=headers,
    )
    assert lbl.status_code == 200, lbl.text
    assert lbl.json() == {"message": "Labels updated"}

    # --- No retrain → no new metrics row ---
    metrics_after = len(duckdb.load_all_metrics(instance_id))
    assert metrics_after == metrics_before, f"metrics grew from {metrics_before} to {metrics_after}"

    # --- label_decisions row persisted correctly ---
    ld = duckdb.get_label_decision(al_instance_id=instance_id, ref=ref)
    assert ld is not None
    assert ld["i_dont_know"] is True
    assert ld["skipped_for_training"] is True
    assert ld["label"] is None

    # --- Ticket is retired: 'next' never returns it ---
    seen = set()
    for _ in range(5):
        nxt2 = client.get(
            f"/activelearning/{instance_id}/next", params={"batch_size": 1}, headers=headers,
        )
        assert nxt2.status_code == 200, nxt2.text
        ret = nxt2.json()["query_idx"]
        if ret:
            seen.update(ret)
    assert ref not in seen, f"retired ref {ref} re-surfaced in next"

    # --- Restart simulation: rebuild skip set from persistence ---
    dependencies.al_service._load_from_persistence()
    assert ref in dependencies.storage.skipped_tickets.get(instance_id, set()), \
        f"skipped_tickets should contain {ref} after reload"

    # --- Still no re-surface after simulated restart ---
    for _ in range(3):
        nxt3 = client.get(
            f"/activelearning/{instance_id}/next", params={"batch_size": 1}, headers=headers,
        )
        assert nxt3.status_code == 200, nxt3.text
        ret = nxt3.json()["query_idx"]
        if ref in ret:
            pytest.fail(f"ref {ref} re-surfaced after restart rebuild")
