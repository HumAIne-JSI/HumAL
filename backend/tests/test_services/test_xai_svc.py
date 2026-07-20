import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest
import uuid

from app.core.storage import ActiveLearningStorage
from app.data_models.active_learning_dm import Data, XaiResultFile, XaiWorkerResult, parse_xai_result
from app.core.rabbitmq_client import RabbitMQClient
from app.persistence.duckdb.service import DuckDbPersistenceService
from app.persistence.local_artifacts import LocalArtifactsStore
from app.persistence.minio_storage import MinioService
from app.services.inference_svc import InferenceService
from app.services.ticket_vectorizer_svc import TicketVectorizerService
from app.services.xai_svc import XaiService


class _FakeSentence:
    def __init__(self, text: str):
        self.text = text


class _FakeDoc:
    def __init__(self, text: str):
        self.sents = [_FakeSentence(part.strip()) for part in text.split(".") if part.strip()]
        self.noun_chunks = []
        self.ents = []


class _FakeNlp:
    def __call__(self, text: str):
        return _FakeDoc(text)


@pytest.fixture
def mock_storage():
    storage = MagicMock(spec=ActiveLearningStorage)

    mock_le = MagicMock()
    mock_le.classes_ = ["Team A", "Team B"]
    mock_le.inverse_transform.side_effect = lambda values: np.array(["Team A" if int(value) == 0 else "Team B" for value in values])
    mock_le.transform.side_effect = lambda values: [0] * len(values)

    x_train = pd.DataFrame(
        {
            "Title_anon": ["Title 1", "Title 2", "Title 3"],
            "Description_anon": ["Desc 1", "Desc 2", "Desc 3"],
        },
        index=["ref1", "ref2", "ref3"],
    )
    y_train = pd.Series([0, 1, 0], index=["ref1", "ref2", "ref3"])

    storage.dataset_dict = {
        1: {
            "le": mock_le,
            "oh": MagicMock(),
            "X_train": x_train,
            "y_train": y_train,
        }
    }
    return storage


@pytest.fixture
def test_data():
    return Data(
        title_anon="Fix printer",
        description_anon="Printer is broken",
        service_name="IT",
        service_subcategory_name="Hardware",
    )


@pytest.fixture
def mock_inference_svc():
    inference_svc = MagicMock(spec=InferenceService)
    inference_svc.infer.return_value = ["Team A"]
    inference_svc.infer_proba.return_value = {
        "probabilities": [[0.8, 0.2]],
        "classes": ["Team A", "Team B"],
    }
    return inference_svc


@pytest.fixture
def mock_dependencies():
    return {
        "local_artifacts_store": MagicMock(spec=LocalArtifactsStore),
        "minio_service": MagicMock(spec=MinioService),
        "duckdb_service": MagicMock(spec=DuckDbPersistenceService),
        "rabbitmq_client": AsyncMock(spec=RabbitMQClient),
        "ticket_vectorizer_service": MagicMock(spec=TicketVectorizerService),
    }


@pytest.fixture
@patch("app.services.xai_svc.SentenceTransformer")
def xai_service(mock_sentence_transformer, mock_storage, mock_inference_svc, mock_dependencies):
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
    mock_sentence_transformer.return_value = mock_model

    service = XaiService(
        storage=mock_storage,
        inference_service=mock_inference_svc,
        **mock_dependencies,
    )
    return service


def _predicted_neighbors():
    return [
        {
            "ref": "ref1",
            "label": "Team A",
            "similarity": 0.91,
            "title": "Title 1",
            "description": "Desc 1",
            "best_sentence": "Title 1",
            "best_sentence_score": 0.87,
            "sentence_score_components": {
                "embedding_similarity": 0.9,
                "keyword_overlap": 0.05,
                "entity_overlap": 0.02,
            },
        }
    ]


def _historical_neighbors():
    return [
        {
            "ref": "ref2",
            "label": "Team B",
            "similarity": 0.84,
            "title": "Title 2",
            "description": "Desc 2",
            "best_sentence": "Desc 2",
            "best_sentence_score": 0.8,
            "sentence_score_components": {
                "embedding_similarity": 0.82,
                "keyword_overlap": 0.03,
                "entity_overlap": 0.0,
            },
            "xai_result": {"top_words": [["printer", 0.15]]},
            "similar_tickets": [{"ref": "ref9", "similarity": 0.5}],
            "model_prediction": "Team B",
            "most_helpful_feature": "lime",
        }
    ]


@patch("app.services.xai_svc.inference")
def test_find_nearest_returns_predicted_and_historical_neighbors(mock_inference, xai_service, test_data):
    ticket_with_ref = MagicMock()
    ticket_with_ref.ref = "ref_ticket"
    ticket_with_ref.title_anon = test_data.title_anon
    ticket_with_ref.description_anon = test_data.description_anon
    ticket_with_ref.service_name = test_data.service_name
    ticket_with_ref.service_subcategory_name = test_data.service_subcategory_name
    ticket_with_ref.public_log_anon = None
    ticket_with_ref.model_dump.return_value = {
        "title_anon": test_data.title_anon,
        "description_anon": test_data.description_anon,
        "service_name": test_data.service_name,
        "service_subcategory_name": test_data.service_subcategory_name,
        "public_log_anon": None,
    }

    mock_inference.return_value = pd.DataFrame(np.array([[0.4, 0.6]]))
    xai_service.duckdb_service.load_label_decisions_with_xai.return_value = [{"ref": "ref2", "xai_result": {"a": 1}, "similar_tickets": [{"b": 2}], "model_prediction": "Team B", "most_helpful_feature": "lime"}]

    with patch.object(XaiService, "_build_predicted_class_neighbors", return_value=_predicted_neighbors()) as mock_predicted, patch.object(XaiService, "_build_historical_neighbors", return_value=_historical_neighbors()) as mock_historical:
        result = xai_service.find_nearest(1, ticket_with_ref, top_k=1)

    assert set(result.keys()) == {"predicted_class_neighbors", "historical_neighbors"}
    assert result["predicted_class_neighbors"][0]["best_sentence"] == "Title 1"
    assert result["historical_neighbors"][0]["xai_result"] == {"top_words": [["printer", 0.15]]}
    assert "reason" not in result["predicted_class_neighbors"][0]
    assert "overlapping_terms" not in result["predicted_class_neighbors"][0]
    assert "reason" not in result["historical_neighbors"][0]
    assert "overlapping_terms" not in result["historical_neighbors"][0]
    mock_predicted.assert_called_once()
    mock_historical.assert_called_once()

    xai_service.duckdb_service.log_event.assert_called_once()
    xai_service.duckdb_service.upsert_label_decision.assert_called_once()
    saved_payload = xai_service.duckdb_service.upsert_label_decision.call_args.kwargs["similar_tickets"]
    assert set(saved_payload.keys()) == {"predicted_class_neighbors", "historical_neighbors"}
    assert "title" in saved_payload["predicted_class_neighbors"][0]
    assert "description" in saved_payload["predicted_class_neighbors"][0]
    assert "xai_result" not in saved_payload["predicted_class_neighbors"][0]
    assert "similar_tickets" not in saved_payload["predicted_class_neighbors"][0]
    assert "title" in saved_payload["historical_neighbors"][0]
    assert "description" in saved_payload["historical_neighbors"][0]
    assert "xai_result" not in saved_payload["historical_neighbors"][0]
    assert "similar_tickets" not in saved_payload["historical_neighbors"][0]
    assert xai_service.duckdb_service.upsert_label_decision.call_args.kwargs["ref"] == "ref_ticket"


@patch("app.services.xai_svc.inference")
def test_find_nearest_by_idx_returns_dual_neighbors(mock_inference, xai_service):
    xai_service.duckdb_service.load_tickets_by_ref.return_value = pd.DataFrame(
        {
            "Ref": ["ref1"],
            "Title_anon": ["Title 1"],
            "Description_anon": ["Desc 1"],
            "Service->Name": ["IT"],
            "Service subcategory->Name": ["Software"],
        }
    )
    mock_inference.return_value = pd.DataFrame(np.array([[0.4, 0.6]]))

    with patch.object(XaiService, "_build_predicted_class_neighbors", return_value=_predicted_neighbors()) as mock_predicted, patch.object(XaiService, "_build_historical_neighbors", return_value=_historical_neighbors()) as mock_historical:
        result = xai_service.find_nearest_by_idx(1, "ref1", top_k=2)

    assert len(result["predicted_class_neighbors"]) == 1
    assert len(result["historical_neighbors"]) == 1
    mock_predicted.assert_called_once()
    mock_historical.assert_called_once()
    xai_service.duckdb_service.log_event.assert_called_once()
    xai_service.duckdb_service.upsert_label_decision.assert_called_once()


def test_neighbor_deprecated_fields_removed(xai_service):
    result = {
        "predicted_class_neighbors": _predicted_neighbors(),
        "historical_neighbors": _historical_neighbors(),
    }

    for group in result.values():
        for neighbor in group:
            assert "reason" not in neighbor
            assert "overlapping_terms" not in neighbor


def test_sentence_scoring_selects_highest_score(xai_service):
    fake_scores = {
        "First sentence": (0.21, {"embedding_similarity": 0.2, "keyword_overlap": 0.05, "entity_overlap": 0.0}),
        "Second sentence": (0.73, {"embedding_similarity": 0.9, "keyword_overlap": 0.5, "entity_overlap": 0.0}),
    }

    xai_service._get_spacy_nlp = MagicMock(return_value=_FakeNlp())
    xai_service._sentence_score_components = MagicMock(side_effect=lambda *, sentence, original_text_embedding, original_doc: fake_scores[sentence])

    best_sentence, best_score, best_components = xai_service._best_sentence_from_text(
        "First sentence. Second sentence.",
        np.array([[1.0, 0.0, 0.0]]),
    )

    assert best_sentence == "Second sentence"
    assert best_score == 0.73
    assert best_components == {"embedding_similarity": 0.9, "keyword_overlap": 0.5, "entity_overlap": 0.0}


def test_ticket_text_excludes_public_log(xai_service):
    ticket = Data(
        title_anon="Title",
        description_anon="Description",
        public_log_anon="Public log content",
    )

    result = xai_service._ticket_text(ticket)

    assert result == "Title Description"
    assert "Public" not in result


def test_get_predicted_classes_raises_without_proba(xai_service, mock_inference_svc):
    mock_inference_svc.infer_proba.side_effect = ValueError("Model does not support probabilities")
    ticket = Data(title_anon="T", description_anon="D")

    with pytest.raises(ValueError):
        xai_service._get_predicted_classes(1, ticket, top_k=2)


def test_best_sentence_uses_description_only(xai_service):
    captured_texts = []

    def fake_best_sentence(text, original_text_embedding):
        captured_texts.append(text)
        return "Desc sentence one", 0.0, None

    xai_service.storage.dataset_dict[1]["X_train"] = pd.DataFrame(
        [[0.1, 0.2, 0.3], [0.2, 0.3, 0.4], [0.3, 0.4, 0.5]],
        index=["ref1", "ref2", "ref3"],
    )

    xai_service.duckdb_service.load_tickets_by_ref.return_value = pd.DataFrame(
        {
            "Ref": ["ref1"],
            "Title_anon": ["Title 1"],
            "Description_anon": ["Desc sentence one. Desc sentence two."],
        }
    )

    with patch.object(XaiService, "_get_predicted_classes", return_value=["Team A"]), patch.object(
        XaiService,
        "_best_sentence_from_text",
        side_effect=fake_best_sentence,
    ):
        xai_service._build_predicted_class_neighbors(
            al_instance_id=1,
            target_embedding=np.array([[0.1, 0.2, 0.3]]),
            original_text_embedding=np.array([[1.0, 0.0, 0.0]]),
            original_text="Title 1 Desc sentence one",
            top_k=1,
            ticket=Data(title_anon="Title 1", description_anon="Desc sentence one. Desc sentence two."),
        )

    assert captured_texts == ["Desc sentence one. Desc sentence two."]


@patch("app.services.xai_svc.inference")
def test_label_decision_save_structure_for_dual_neighbors(mock_inference, xai_service, test_data):
    ticket_with_ref = MagicMock()
    ticket_with_ref.ref = "ref_ticket"
    ticket_with_ref.title_anon = test_data.title_anon
    ticket_with_ref.description_anon = test_data.description_anon
    ticket_with_ref.service_name = test_data.service_name
    ticket_with_ref.service_subcategory_name = test_data.service_subcategory_name
    ticket_with_ref.public_log_anon = None
    ticket_with_ref.model_dump.return_value = {
        "title_anon": test_data.title_anon,
        "description_anon": test_data.description_anon,
        "service_name": test_data.service_name,
        "service_subcategory_name": test_data.service_subcategory_name,
        "public_log_anon": None,
    }

    mock_inference.return_value = pd.DataFrame(np.array([[0.4, 0.6]]))
    with patch.object(XaiService, "_build_predicted_class_neighbors", return_value=_predicted_neighbors()), patch.object(XaiService, "_build_historical_neighbors", return_value=_historical_neighbors()):
        xai_service.find_nearest(1, ticket_with_ref, top_k=1)

    saved_payload = xai_service.duckdb_service.upsert_label_decision.call_args.kwargs["similar_tickets"]
    assert set(saved_payload.keys()) == {"predicted_class_neighbors", "historical_neighbors"}
    for neighbor in saved_payload["predicted_class_neighbors"]:
        assert "title" in neighbor
        assert "description" in neighbor
        assert "xai_result" not in neighbor
        assert "similar_tickets" not in neighbor
    for neighbor in saved_payload["historical_neighbors"]:
        assert "title" in neighbor
        assert "description" in neighbor
        assert "xai_result" not in neighbor
        assert "similar_tickets" not in neighbor


def test_sanitize_neighbor_keeps_title_and_description(xai_service):
    neighbor = {
        "ref": "R1",
        "title": "T1",
        "description": "D1",
        "xai_result": {"words": []},
        "similar_tickets": [],
    }

    result = xai_service._sanitize_neighbor_for_storage(neighbor)

    assert result["title"] == "T1"
    assert result["description"] == "D1"
    assert "xai_result" not in result
    assert "similar_tickets" not in result


@patch.dict(os.environ, {"USE_RABBITMQ": "1", "TASK_QUEUE": "test_queue"})
def test_create_xai_request(xai_service, test_data):
    xai_service.minio_service.save_ticket_for_xai.return_value = {
        "ticket_sha": "testsha123",
        "object": "ticket/testsha123.json",
    }

    xai_service.ticket_vectorizer_service.create_vectorizer.return_value = MagicMock()
    xai_service.ticket_vectorizer_service.save_vectorizer.return_value = {
        "object": "vectorizer/path",
    }

    xai_service.minio_service.return_data_names.return_value = ["data1"]

    job_id = asyncio.run(xai_service.create_xai_request(1, test_data, model_id=0))

    assert isinstance(job_id, uuid.UUID)
    xai_service.duckdb_service.create_xai_job.assert_called_once()
    xai_service.rabbitmq_client.publish.assert_called_once()


def test_create_xai_request_message_matches_contract(xai_service, test_data, monkeypatch):
    monkeypatch.setenv("USE_RABBITMQ", "1")
    monkeypatch.setenv("TASK_QUEUE", "test_queue")
    monkeypatch.delenv("MESSAGE_VERSION", raising=False)

    xai_service.minio_service.save_ticket_for_xai.return_value = {
        "ticket_sha": "testsha123", "object": "ticket/testsha123.json"}
    xai_service.ticket_vectorizer_service.create_vectorizer.return_value = MagicMock()
    xai_service.ticket_vectorizer_service.save_vectorizer.return_value = {"object": "vectorizer/path"}
    xai_service.minio_service.return_data_names.return_value = ["datasets/test/foo.xlsx"]

    asyncio.run(xai_service.create_xai_request(1, test_data, model_id=0))

    msg = xai_service.rabbitmq_client.publish.call_args.kwargs["message"]
    assert set(msg.keys()) == {"version", "job_id", "al_instance_id", "model_id", "ticket_sha", "artifacts"}
    assert msg["version"] == 0.3 and isinstance(msg["version"], float)
    assert msg["al_instance_id"] == 1 and msg["model_id"] == 0
    assert msg["ticket_sha"] == "testsha123" and isinstance(msg["job_id"], str)
    arts = msg["artifacts"]
    assert set(arts.keys()) == {"ticket", "model", "preprocessor", "one_hot_encoder", "raw_tickets"}
    assert arts["ticket"] == "ticket/testsha123.json"
    assert arts["preprocessor"] == "vectorizer/path"
    assert isinstance(arts["raw_tickets"], str) and arts["raw_tickets"] == "datasets/test/foo.xlsx"


def test_create_xai_request_raw_tickets_first_element_duckdb_keeps_list(xai_service, test_data, monkeypatch):
    monkeypatch.setenv("USE_RABBITMQ", "1")
    monkeypatch.setenv("TASK_QUEUE", "test_queue")
    xai_service.minio_service.save_ticket_for_xai.return_value = {"ticket_sha": "sha", "object": "t.json"}
    xai_service.ticket_vectorizer_service.create_vectorizer.return_value = MagicMock()
    xai_service.ticket_vectorizer_service.save_vectorizer.return_value = {"object": "v"}
    xai_service.minio_service.return_data_names.return_value = ["first.xlsx", "second.xlsx"]

    asyncio.run(xai_service.create_xai_request(1, test_data, model_id=0))

    msg = xai_service.rabbitmq_client.publish.call_args.kwargs["message"]
    assert msg["artifacts"]["raw_tickets"] == "first.xlsx"
    assert not isinstance(msg["artifacts"]["raw_tickets"], list)
    assert xai_service.duckdb_service.create_xai_job.call_args.kwargs["request_raw_tickets_locations"] == ["first.xlsx", "second.xlsx"]


def test_create_xai_request_raw_tickets_empty_list_yields_none(xai_service, test_data, monkeypatch):
    monkeypatch.setenv("USE_RABBITMQ", "1")
    monkeypatch.setenv("TASK_QUEUE", "test_queue")
    xai_service.minio_service.save_ticket_for_xai.return_value = {"ticket_sha": "sha", "object": "t.json"}
    xai_service.ticket_vectorizer_service.create_vectorizer.return_value = MagicMock()
    xai_service.ticket_vectorizer_service.save_vectorizer.return_value = {"object": "v"}
    xai_service.minio_service.return_data_names.return_value = []

    asyncio.run(xai_service.create_xai_request(1, test_data, model_id=0))  # must not raise

    msg = xai_service.rabbitmq_client.publish.call_args.kwargs["message"]
    assert msg["artifacts"]["raw_tickets"] is None
    assert xai_service.duckdb_service.create_xai_job.call_args.kwargs["request_raw_tickets_locations"] == []


def test_create_xai_request_version_env_override(xai_service, test_data, monkeypatch):
    monkeypatch.setenv("USE_RABBITMQ", "1")
    monkeypatch.setenv("TASK_QUEUE", "test_queue")
    monkeypatch.setenv("MESSAGE_VERSION", "0.5")
    xai_service.minio_service.save_ticket_for_xai.return_value = {"ticket_sha": "sha", "object": "t.json"}
    xai_service.ticket_vectorizer_service.create_vectorizer.return_value = MagicMock()
    xai_service.ticket_vectorizer_service.save_vectorizer.return_value = {"object": "v"}
    xai_service.minio_service.return_data_names.return_value = ["d.xlsx"]

    asyncio.run(xai_service.create_xai_request(1, test_data, model_id=0))

    msg = xai_service.rabbitmq_client.publish.call_args.kwargs["message"]
    assert msg["version"] == 0.5 and isinstance(msg["version"], float)


def test_create_xai_request_no_vectorizer_preprocessor_none(xai_service, test_data, monkeypatch):
    monkeypatch.setenv("USE_RABBITMQ", "1")
    monkeypatch.setenv("TASK_QUEUE", "test_queue")
    monkeypatch.delenv("MESSAGE_VERSION", raising=False)
    xai_service.ticket_vectorizer_service = None
    xai_service.minio_service.save_ticket_for_xai.return_value = {"ticket_sha": "sha", "object": "t.json"}
    xai_service.minio_service.return_data_names.return_value = ["d.xlsx"]

    asyncio.run(xai_service.create_xai_request(1, test_data, model_id=0))  # must not raise

    msg = xai_service.rabbitmq_client.publish.call_args.kwargs["message"]
    assert msg["artifacts"]["preprocessor"] is None
    assert msg["artifacts"]["raw_tickets"] == "d.xlsx"


def test_get_xai_job(xai_service):
    job_id = uuid.uuid4()
    xai_service.duckdb_service.get_xai_job.return_value = {"job_id": job_id}

    res = xai_service.get_xai_job(job_id)
    assert res["job_id"] == job_id


def test_update_xai_job(xai_service):
    """update_xai_job parses canonical XaiWorkerResult and logs per-ticket event."""
    job_id = uuid.uuid4()
    data = {"job_id": str(job_id), "status": "completed", "result_location": "minio/res", "result_file_names": {"lime": "f.json"}}

    xai_service.duckdb_service.get_xai_job.return_value = {
        "job_id": job_id,
        "al_instance_id": 1,
        "ticket_ref_or_sha": "ref1",
        "result_location": "minio/res",
        "result_file_names": ["f.json"],
        "created_at": pd.Timestamp("2026-01-01 10:00:00"),
        "finished_at": pd.Timestamp("2026-01-01 10:00:01"),
    }
    canonical_result = {
        "schema_version": 1,
        "ticket_sha": "ref1",
        "text": "Fix printer Printer is broken",
        "predictions": [
            {
                "rank": 1,
                "class_index": 0,
                "label": "Team A",
                "probability": 0.8,
                "lime": {
                    "word_weights": [["printer", 0.15]],
                    "highlighted_tokens": [
                        {"token": "printer", "weight": 0.15, "direction": "support", "intensity": 1.0}
                    ],
                },
            },
        ],
    }
    xai_service.minio_service.load_xai_results.return_value = {
        "result.json": canonical_result
    }

    asyncio.run(xai_service.update_xai_job(data))

    xai_service.duckdb_service.update_xai_job_status.assert_called_once_with(
        job_id=job_id,
        status="completed",
        result_location="minio/res",
        result_file_names={"lime": "f.json"},
    )
    xai_service.duckdb_service.log_event.assert_called_once()
    call_kwargs = xai_service.duckdb_service.log_event.call_args.kwargs
    assert call_kwargs["action"] == "lime"
    assert call_kwargs["object_id"] == "ref1"
    assert call_kwargs["payload"]["ticket_id"] == "ref1"
    assert call_kwargs["payload"]["error"] is None
    assert call_kwargs["payload"]["result"]["ticket_sha"] == "ref1"


def test_update_xai_job_rejects_old_format(xai_service):
    """Old-format [{class, top_words, error}] results are rejected with result: null."""
    job_id = uuid.uuid4()
    data = {"job_id": str(job_id), "status": "completed", "result_location": "minio/res", "result_file_names": {"lime": "f.json"}}

    xai_service.duckdb_service.get_xai_job.return_value = {
        "job_id": job_id,
        "al_instance_id": 1,
        "ticket_ref_or_sha": "ref1",
        "result_location": "minio/res",
        "result_file_names": ["f.json"],
        "created_at": pd.Timestamp("2026-01-01 10:00:00"),
        "finished_at": pd.Timestamp("2026-01-01 10:00:01"),
    }
    old_format_result = [{"class": "Team A", "top_words": [["printer", 0.15]], "error": None}]
    xai_service.minio_service.load_xai_results.return_value = {
        "result.json": old_format_result
    }

    asyncio.run(xai_service.update_xai_job(data))

    xai_service.duckdb_service.log_event.assert_called_once()
    call_kwargs = xai_service.duckdb_service.log_event.call_args.kwargs
    assert call_kwargs["payload"]["result"] is None
    assert "rejected" in (call_kwargs["payload"]["error"] or "")


def test_update_xai_job_rejects_old_xairesultfile_shape(xai_service):
    """Old XaiResultFile-shaped dicts are rejected with result: null."""
    job_id = uuid.uuid4()
    data = {"job_id": str(job_id), "status": "completed", "result_location": "minio/res", "result_file_names": {"lime": "f.json"}}

    xai_service.duckdb_service.get_xai_job.return_value = {
        "job_id": job_id,
        "al_instance_id": 1,
        "ticket_ref_or_sha": "ref1",
        "result_location": "minio/res",
        "result_file_names": ["f.json"],
        "created_at": pd.Timestamp("2026-01-01 10:00:00"),
        "finished_at": pd.Timestamp("2026-01-01 10:00:01"),
    }
    old_shape_result = {
        "text": "Fix printer",
        "prediction": {"label": "Team A", "probabilities": {"Team A": 0.8}},
        "word_weights": [],
        "highlighted_tokens": [],
        "index": "ref1",
        "error": None,
        "class_explanations": [],
    }
    xai_service.minio_service.load_xai_results.return_value = {
        "result.json": old_shape_result
    }

    asyncio.run(xai_service.update_xai_job(data))

    xai_service.duckdb_service.log_event.assert_called_once()
    call_kwargs = xai_service.duckdb_service.log_event.call_args.kwargs
    assert call_kwargs["payload"]["result"] is None
    assert "rejected" in (call_kwargs["payload"]["error"] or "")


def test_explain_lime_top_k_classes(xai_service, test_data):
    """Happy path: explain_lime returns one XaiResultFile per ticket with canonical fields."""
    mock_explanation = MagicMock()
    mock_explanation.as_list.side_effect = lambda label: [("word1", 0.5), ("word2", 0.3)]

    with patch("app.services.xai_svc.LimeTextExplainer") as mock_cls:
        mock_explainer = MagicMock()
        mock_explainer.explain_instance.return_value = mock_explanation
        mock_cls.return_value = mock_explainer

        res = xai_service.explain_lime(
            1, [test_data], model_id=0, top_k=2, user_id="u1", ticket_refs=["ref1"]
        )

    assert len(res) == 1
    ticket_result = res[0]
    assert isinstance(ticket_result, XaiResultFile)
    assert ticket_result.text == "Fix printer Printer is broken"
    assert ticket_result.prediction.label == "Team A"
    assert ticket_result.prediction.probabilities == {"Team A": 0.8, "Team B": 0.2}
    assert len(ticket_result.word_weights) == 2
    assert ticket_result.word_weights[0] == ["word1", 0.5]
    assert ticket_result.index == "ref1"
    assert ticket_result.error is None
    assert len(ticket_result.class_explanations) == 2


def test_explain_lime_top_k_capped_by_num_classes(xai_service, test_data):
    """top_k larger than num_classes is silently capped."""
    mock_explanation = MagicMock()
    mock_explanation.as_list.side_effect = lambda label: [("word1", 0.5)]

    with patch("app.services.xai_svc.LimeTextExplainer") as mock_cls:
        mock_explainer = MagicMock()
        mock_explainer.explain_instance.return_value = mock_explanation
        mock_cls.return_value = mock_explainer

        res = xai_service.explain_lime(
            1, [test_data], model_id=0, top_k=10, user_id="u1", ticket_refs=["ref1"]
        )

    assert len(res[0].class_explanations) == 2


def test_explain_lime_logs_event(xai_service, test_data):
    """One lime event per ticket is logged to DuckDB (per-ticket logging)."""
    mock_explanation = MagicMock()
    mock_explanation.as_list.side_effect = lambda label: [("word1", 0.5)]

    with patch("app.services.xai_svc.LimeTextExplainer") as mock_cls:
        mock_explainer = MagicMock()
        mock_explainer.explain_instance.return_value = mock_explanation
        mock_cls.return_value = mock_explainer

        xai_service.explain_lime(
            1, [test_data], model_id=0, top_k=1, user_id="u1", ticket_refs=["ref1"]
        )

    xai_service.duckdb_service.log_event.assert_called_once()
    call_kwargs = xai_service.duckdb_service.log_event.call_args.kwargs
    assert call_kwargs["action"] == "lime"
    assert call_kwargs["al_instance_id"] == 1
    assert call_kwargs["user_id"] == "u1"
    assert call_kwargs["latency_ms"] >= 0
    assert call_kwargs["actor_type"] == "ai"
    assert call_kwargs["agent"] == "xai_lime"
    assert call_kwargs["object_id"] == "ref1"
    assert "result" in call_kwargs["payload"]
    assert call_kwargs["payload"]["ticket_id"] == "ref1"
    assert call_kwargs["payload"]["error"] is None


def test_explain_lime_upserts_label_decision_with_ref(xai_service, test_data):
    """When a ticket_ref is provided, the result is upserted into label_decisions."""
    mock_explanation = MagicMock()
    mock_explanation.as_list.side_effect = lambda label: [("word1", 0.5)]

    with patch("app.services.xai_svc.LimeTextExplainer") as mock_cls:
        mock_explainer = MagicMock()
        mock_explainer.explain_instance.return_value = mock_explanation
        mock_cls.return_value = mock_explainer

        xai_service.explain_lime(
            1, [test_data], model_id=0, top_k=1, user_id="u1", ticket_refs=["ref1"]
        )

    xai_service.duckdb_service.upsert_label_decision.assert_called_once()
    call_kwargs = xai_service.duckdb_service.upsert_label_decision.call_args.kwargs
    assert call_kwargs["al_instance_id"] == 1
    assert call_kwargs["ref"] == "ref1"
    assert call_kwargs["user_id"] == "u1"
    assert call_kwargs["xai_result"] is not None
    assert isinstance(call_kwargs["xai_result"], dict)
    assert call_kwargs["xai_result"]["index"] == "ref1"
    assert call_kwargs["xai_result"]["error"] is None


def test_explain_lime_no_upsert_without_ref(xai_service, test_data):
    """When ticket_refs contains only None, no log_event and no upsert_label_decision."""
    mock_explanation = MagicMock()
    mock_explanation.as_list.side_effect = lambda label: [("word1", 0.5)]

    with patch("app.services.xai_svc.LimeTextExplainer") as mock_cls:
        mock_explainer = MagicMock()
        mock_explainer.explain_instance.return_value = mock_explanation
        mock_cls.return_value = mock_explainer

        xai_service.explain_lime(
            1, [test_data], model_id=0, top_k=1, user_id="u1", ticket_refs=[None]
        )

    xai_service.duckdb_service.log_event.assert_not_called()
    xai_service.duckdb_service.upsert_label_decision.assert_not_called()


def test_explain_lime_logs_one_event_per_ref(xai_service, test_data):
    """When 2 ticket_refs are provided, 2 log_event calls are made (one per ticket)."""
    mock_explanation = MagicMock()
    mock_explanation.as_list.side_effect = lambda label: [("word1", 0.5), ("word2", 0.3)]

    with patch("app.services.xai_svc.LimeTextExplainer") as mock_cls:
        mock_explainer = MagicMock()
        mock_explainer.explain_instance.return_value = mock_explanation
        mock_cls.return_value = mock_explainer

        xai_service.explain_lime(
            1, [test_data, test_data], model_id=0, top_k=1, user_id="u1", ticket_refs=["refA", "refB"]
        )

    assert xai_service.duckdb_service.log_event.call_count == 2
    first = xai_service.duckdb_service.log_event.call_args_list[0]
    second = xai_service.duckdb_service.log_event.call_args_list[1]
    assert first.kwargs["object_id"] == "refA"
    assert first.kwargs["payload"]["ticket_id"] == "refA"
    assert "result" in first.kwargs["payload"]
    assert second.kwargs["object_id"] == "refB"
    assert second.kwargs["payload"]["ticket_id"] == "refB"
    assert "result" in second.kwargs["payload"]


def test_explain_lime_skips_none_refs_in_mixed_batch(xai_service, test_data):
    """None refs in a mixed batch are skipped, truthy refs are logged."""
    mock_explanation = MagicMock()
    mock_explanation.as_list.side_effect = lambda label: [("word1", 0.5)]

    with patch("app.services.xai_svc.LimeTextExplainer") as mock_cls:
        mock_explainer = MagicMock()
        mock_explainer.explain_instance.return_value = mock_explanation
        mock_cls.return_value = mock_explainer

        xai_service.explain_lime(
            1, [test_data, test_data], model_id=0, top_k=1, user_id="u1", ticket_refs=["refA", None]
        )

    assert xai_service.duckdb_service.log_event.call_count == 1
    assert xai_service.duckdb_service.log_event.call_args.kwargs["object_id"] == "refA"
    # upsert_label_decision only for the truthy ref
    xai_service.duckdb_service.upsert_label_decision.assert_called_once()
    assert xai_service.duckdb_service.upsert_label_decision.call_args.kwargs["ref"] == "refA"


def test_explain_lime_no_persistence_when_duckdb_none(mock_storage, mock_inference_svc, test_data):
    """If duckdb_service is None, explain_lime still returns results without crashing."""
    from unittest.mock import MagicMock, patch

    with patch("app.services.xai_svc.SentenceTransformer") as mock_st:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_st.return_value = mock_model

        mock_explanation = MagicMock()
        mock_explanation.as_list.side_effect = lambda label: [("word1", 0.5)]

        with patch("app.services.xai_svc.LimeTextExplainer") as mock_cls:
            mock_explainer = MagicMock()
            mock_explainer.explain_instance.return_value = mock_explanation
            mock_cls.return_value = mock_explainer

            svc = XaiService(
                storage=mock_storage,
                inference_service=mock_inference_svc,
                local_artifacts_store=MagicMock(),
                duckdb_service=None,
            )
            res = svc.explain_lime(1, [test_data], model_id=0, top_k=1, user_id="u1")
            assert len(res) == 1


def test_find_nearest_by_ticket_and_query_idx_removed(xai_service):
    """The /nearest_ticket endpoint and its backing service methods were removed."""
    assert not hasattr(xai_service, "find_nearest_by_ticket")
    assert not hasattr(xai_service, "find_nearest_by_query_idx")
