import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import numpy as np
import pandas as pd
import uuid

from app.core.storage import ActiveLearningStorage
from app.services.inference_svc import InferenceService
from app.services.xai_svc import XaiService
from app.data_models.active_learning_dm import Data
from app.persistence.local_artifacts import LocalArtifactsStore
from app.persistence.duckdb.service import DuckDbPersistenceService
from app.persistence.minio_storage import MinioService
from app.core.rabbitmq_client import RabbitMQClient
from app.services.ticket_vectorizer_svc import TicketVectorizerService

@pytest.fixture
def mock_storage():
    storage = MagicMock(spec=ActiveLearningStorage)
    
    # Mocking storage variables needed for xai_svc
    mock_le = MagicMock()
    mock_le.classes_ = ["Team A", "Team B"]
    mock_le.inverse_transform.side_effect = lambda x: np.array([f"Team {i}" for i in x])
    mock_le.transform.side_effect = lambda x: [0] * len(x)
    
    X_train = pd.DataFrame({
        "Title_anon": ["Title 1", "Title 2", "Title 3"],
        "Description_anon": ["Desc 1", "Desc 2", "Desc 3"]
    }, index=["ref1", "ref2", "ref3"])
    
    y_train = pd.Series([0, 1, 0], index=["ref1", "ref2", "ref3"])
    
    storage.dataset_dict = {
        1: {
            'le': mock_le,
            'oh': MagicMock(),
            'X_train': X_train,
            'y_train': y_train
        }
    }
    return storage

@pytest.fixture
def test_data():
    return Data(
        title_anon="Fix printer",
        description_anon="Printer is broken",
        service_name="IT",
        service_subcategory_name="Hardware"
    )

@pytest.fixture
def mock_inference_svc():
    inference_svc = MagicMock(spec=InferenceService)
    inference_svc.infer.return_value = ["Team A"]
    inference_svc.infer_proba.return_value = {
        "probabilities": [[0.8, 0.2]],
        "classes": ["Team A", "Team B"]
    }
    return inference_svc

@pytest.fixture
def mock_dependencies():
    return {
        "local_artifacts_store": MagicMock(spec=LocalArtifactsStore),
        "minio_service": MagicMock(spec=MinioService),
        "duckdb_service": MagicMock(spec=DuckDbPersistenceService),
        "rabbitmq_client": AsyncMock(spec=RabbitMQClient),
        "ticket_vectorizer_service": MagicMock(spec=TicketVectorizerService)
    }

@pytest.fixture
@patch('app.services.xai_svc.SentenceTransformer')
def xai_service(mock_st, mock_storage, mock_inference_svc, mock_dependencies):
    return XaiService(
        storage=mock_storage,
        inference_service=mock_inference_svc,
        **mock_dependencies
    )

@patch('app.services.xai_svc.LimeTextExplainer')
def test_explain_lime(mock_lime, xai_service, test_data):
    mock_explainer = MagicMock()
    mock_lime.return_value = mock_explainer
    
    # Mocking as_list which LimeTextExplainer uses
    mock_explanation = MagicMock()
    mock_explanation.as_list.return_value = [("printer", 0.15)]
    mock_explainer.explain_instance.return_value = mock_explanation

    res = xai_service.explain_lime(1, [test_data])
    
    assert len(res) == 1
    assert res[0]["top_words"] == [("printer", 0.15)]
    assert res[0]["error"] is None

@patch('app.services.xai_svc.inference')
@patch.object(XaiService, '_compute_nearest')
def test_find_nearest(mock_compute_nearest, mock_inference, xai_service, test_data):
    mock_inference.return_value = pd.DataFrame(np.random.rand(1, 10))
    mock_compute_nearest.return_value = [{"ref": "ref1", "similarity": 0.9}]
    
    res = xai_service.find_nearest(1, test_data, top_k=1, distinct_classes=True)
    
    assert len(res) == 1
    mock_compute_nearest.assert_called_once()
    args, kwargs = mock_compute_nearest.call_args
    assert args[2] == 1  # top_k
    assert args[4] == {"Team A"}  # target_classes

def test_find_nearest_by_idx(xai_service):
    xai_service.duckdb_service.load_tickets_by_ref.return_value = pd.DataFrame({
        "Ref": ["ref1"],
        "Title_anon": ["Title 1"],
        "Description_anon": ["Desc 1"],
        "Service->Name": ["IT"],
        "Service subcategory->Name": ["Software"]
    })
    
    with patch.object(XaiService, '_compute_nearest') as mock_compute:
        mock_compute.return_value = []
        xai_service.find_nearest_by_idx(1, "ref1", top_k=2)
        mock_compute.assert_called_once()
        args = mock_compute.call_args[0]
        # input_title and input_description passed correctly
        assert args[5] == "Title 1"
        assert args[6] == "Desc 1"

def test_compute_nearest(xai_service, test_data):
    # Setup DuckDB return
    xai_service.duckdb_service.load_tickets_by_ref.return_value = pd.DataFrame({
        "Ref": ["ref1", "ref2"],
        "Title_anon": ["Fix printer issue", "Another printer issue"],
        "Description_anon": ["Printer is broken here", "Broken printer"],
    })
    
    target_embedding = np.random.rand(1, 384)
    # Patch similarities
    with patch('app.services.xai_svc.cosine_similarity') as mock_cos:
        mock_cos.return_value = np.array([[0.9, 0.8, 0.7]])
        
        res = xai_service._compute_nearest(
            1, target_embedding, top_k=2, distinct_classes=False,
            input_title="printer issue", input_description="broken printer"
        )
        
        assert len(res) == 2
        assert res[0]["ref"] == "ref1"
        assert res[0]["overlapping_terms"] is not None

@patch('app.services.xai_svc.inference')
def test_find_nearest_by_ticket(mock_inference, xai_service, test_data):
    mock_inference.return_value = pd.DataFrame(np.random.rand(1, 384))
    
    with patch('app.services.xai_svc.cosine_similarity') as mock_cos:
        mock_cos.return_value = np.array([[0.9, 0.8, 0.7]])
        
        res = xai_service.find_nearest_by_ticket(1, test_data)
        assert res["nearest_ticket_ref"] == "ref1"

def test_find_nearest_by_query_idx(xai_service):
    with patch('app.services.xai_svc.cosine_similarity') as mock_cos:
        mock_cos.return_value = np.array([[0.9, 0.8, 0.7]])
        
        res = xai_service.find_nearest_by_query_idx(1, ["ref1"])
        assert len(res["nearest_ticket_ref"]) == 1
        assert res["nearest_ticket_ref"][0] == "ref1"


import asyncio
import os

@patch.dict(os.environ, {"USE_RABBITMQ": "1", "TASK_QUEUE": "test_queue"})
def test_create_xai_request(xai_service, test_data):
    xai_service.minio_service.save_ticket_for_xai.return_value = {
        "ticket_sha": "testsha123",
        "object": "ticket/testsha123.json"
    }
    
    xai_service.ticket_vectorizer_service.create_vectorizer.return_value = MagicMock()
    xai_service.ticket_vectorizer_service.save_vectorizer.return_value = {
        "object": "vectorizer/path"
    }
    
    xai_service.minio_service.return_data_names.return_value = ["data1"]
    
    job_id = asyncio.run(xai_service.create_xai_request(1, test_data, model_id=0))
    
    assert isinstance(job_id, uuid.UUID)
    xai_service.duckdb_service.create_xai_job.assert_called_once()
    xai_service.rabbitmq_client.publish.assert_called_once()

def test_get_xai_job(xai_service):
    job_id = uuid.uuid4()
    xai_service.duckdb_service.get_xai_job.return_value = {"job_id": job_id}
    
    res = xai_service.get_xai_job(job_id)
    assert res["job_id"] == job_id
    
def test_update_xai_job(xai_service):
    job_id = uuid.uuid4()
    data = {"job_id": str(job_id), "status": "completed", "result_location": "minio/res", "result_file_names": {"lime": "f.json"}}
    
    asyncio.run(xai_service.update_xai_job(data))
    
    xai_service.duckdb_service.update_xai_job_status.assert_called_once_with(
        job_id=job_id,
        status="completed",
        result_location="minio/res",
        result_file_names={"lime": "f.json"}
    )

