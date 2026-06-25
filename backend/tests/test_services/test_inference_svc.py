import pytest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from app.core.storage import ActiveLearningStorage
from app.persistence.local_artifacts import LocalArtifactsStore
from app.services.inference_svc import InferenceService
from app.data_models.active_learning_dm import Data

@pytest.fixture
def mock_storage():
    storage = ActiveLearningStorage()
    storage.dataset_dict = {
        1: {
            'le': MagicMock(),
            'oh': MagicMock()
        }
    }
    return storage

@pytest.fixture
def mock_local_artifacts():
    return MagicMock(spec=LocalArtifactsStore)

@pytest.fixture
@patch('app.services.inference_svc.SentenceTransformer')
def inference_service(mock_st, mock_storage, mock_local_artifacts):
    return InferenceService(mock_storage, local_artifacts_store=mock_local_artifacts)

@patch('app.services.inference_svc.inference')
def test_inference_single(mock_inference, inference_service):
    # Setup mocks
    mock_model = MagicMock()
    mock_model.predict.return_value = [0]
    inference_service.local_artifacts_store.load_model.return_value = mock_model
    
    mock_le = inference_service.storage.dataset_dict[1]['le']
    mock_le.inverse_transform.return_value = np.array(["Team A"])
    
    mock_inference.return_value = pd.DataFrame([["feat1", "feat2"]])
    
    # Execute with single item
    data = Data(title_anon="Single Title", description_anon="Single Description")
    result = inference_service.infer(1, data, model_id=0)
    
    # Verify expected outcomes
    assert result == ["Team A"]
    mock_model.predict.assert_called_once()
    mock_le.inverse_transform.assert_called_once_with([0])

    # Check dataframe assembly behavior inside `infer`
    # inference(df, le, oh, sentence_model)
    df_arg = mock_inference.call_args.kwargs.get('df')
    if df_arg is None:
        df_arg = mock_inference.call_args[0][0]
    assert len(df_arg) == 1
    assert df_arg.iloc[0]['title_anon'] == "Single Title"


@patch('app.services.inference_svc.inference')
def test_inference_batch(mock_inference, inference_service):
    # Setup mocks
    mock_model = MagicMock()
    mock_model.predict.return_value = [0, 1]
    inference_service.local_artifacts_store.load_model.return_value = mock_model
    
    mock_le = inference_service.storage.dataset_dict[1]['le']
    mock_le.inverse_transform.return_value = np.array(["Team A", "Team B"])
    
    mock_inference.return_value = pd.DataFrame([["feat1", "feat2"], ["feat3", "feat4"]])
    
    # Execute with batch of items
    data1 = Data(title_anon="Batch Title 1", description_anon="Batch Description 1")
    data2 = Data(title_anon="Batch Title 2", description_anon="Batch Description 2")
    
    result = inference_service.infer(1, [data1, data2], model_id=0)
    
    # Verify expected outcomes
    assert result == ["Team A", "Team B"]
    mock_model.predict.assert_called_once()
    mock_le.inverse_transform.assert_called_once_with([0, 1])

    # Check batch assembly
    df_arg = mock_inference.call_args.kwargs.get('df')
    if df_arg is None:
        df_arg = mock_inference.call_args[0][0]
    assert len(df_arg) == 2
    assert df_arg.iloc[1]['description_anon'] == "Batch Description 2"


@patch('app.services.inference_svc.inference')
def test_infer_proba_single(mock_inference, inference_service):
    # Setup mocks
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.7, 0.3]])
    inference_service.local_artifacts_store.load_model.return_value = mock_model

    mock_le = inference_service.storage.dataset_dict[1]['le']
    mock_le.classes_ = np.array(["Team A", "Team B"])

    mock_inference.return_value = pd.DataFrame([["feat1", "feat2"]])

    data = Data(title_anon="Single Title", description_anon="Single Description")
    result = inference_service.infer_proba(1, data, model_id=0)

    assert result == {
        "classes": ["Team A", "Team B"],
        "probabilities": [[0.7, 0.3]]
    }
    mock_model.predict_proba.assert_called_once()


@patch('app.services.inference_svc.inference')
def test_infer_proba_batch(mock_inference, inference_service):
    # Setup mocks
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([
        [0.7, 0.3],
        [0.1, 0.9]
    ])
    inference_service.local_artifacts_store.load_model.return_value = mock_model

    mock_le = inference_service.storage.dataset_dict[1]['le']
    mock_le.classes_ = np.array(["Team A", "Team B"])

    mock_inference.return_value = pd.DataFrame([["feat1", "feat2"]])

    data1 = Data(title_anon="Batch Title 1", description_anon="Batch Description 1")
    data2 = Data(title_anon="Batch Title 2", description_anon="Batch Description 2")
    result = inference_service.infer_proba(1, [data1, data2], model_id=0)

    assert result == {
        "classes": ["Team A", "Team B"],
        "probabilities": [[0.7, 0.3], [0.1, 0.9]]
    }
    mock_model.predict_proba.assert_called_once()


@patch('app.services.inference_svc.inference')
def test_infer_proba_missing_predict_proba(mock_inference, inference_service):
    # Setup mocks
    inference_service.local_artifacts_store.load_model.return_value = object()
    inference_service.storage.dataset_dict[1]['le'].classes_ = np.array(["Team A", "Team B"])
    mock_inference.return_value = pd.DataFrame([["feat1", "feat2"]])

    data = Data(title_anon="Single Title", description_anon="Single Description")

    with pytest.raises(ValueError, match="predict_proba"):
        inference_service.infer_proba(1, data, model_id=0)


@patch('app.services.inference_svc.inference')
def test_infer_logs_prediction(mock_inference, inference_service):
    duckdb_service = MagicMock()
    inference_service.duckdb_service = duckdb_service

    mock_model = MagicMock()
    mock_model.predict.return_value = [0]
    inference_service.local_artifacts_store.load_model.return_value = mock_model

    mock_le = inference_service.storage.dataset_dict[1]['le']
    mock_le.inverse_transform.return_value = np.array(["Team A"])
    mock_inference.return_value = pd.DataFrame([["feat1", "feat2"]])

    result = inference_service.infer(1, Data(title_anon="A", description_anon="B"), model_id=0)

    assert result == ["Team A"]
    duckdb_service.log_event.assert_called_once()
    assert duckdb_service.log_event.call_args.kwargs["action"] == "predict"
    assert duckdb_service.log_event.call_args.kwargs["actor_type"] == "ai"
    assert duckdb_service.log_event.call_args.kwargs["agent"] == "classifier_model"


@patch('app.services.inference_svc.inference')
def test_infer_with_ref_sets_object_id(mock_inference, inference_service):
    duckdb_service = MagicMock()
    inference_service.duckdb_service = duckdb_service

    mock_model = MagicMock()
    mock_model.predict.return_value = [0]
    inference_service.local_artifacts_store.load_model.return_value = mock_model

    mock_le = inference_service.storage.dataset_dict[1]['le']
    mock_le.inverse_transform.return_value = np.array(["Team A"])
    mock_inference.return_value = pd.DataFrame([["feat1", "feat2"]])

    inference_service.infer(1, Data(title_anon="A", description_anon="B"), model_id=0, ref="R-123")

    duckdb_service.log_event.assert_called_once()
    assert duckdb_service.log_event.call_args.kwargs["object_id"] == "R-123"


@patch('app.services.inference_svc.inference')
def test_infer_logs_with_user_id(mock_inference, inference_service):
    duckdb_service = MagicMock()
    inference_service.duckdb_service = duckdb_service
    custom_user_id = "33333333-3333-3333-3333-333333333333"

    mock_model = MagicMock()
    mock_model.predict.return_value = [0]
    inference_service.local_artifacts_store.load_model.return_value = mock_model

    mock_le = inference_service.storage.dataset_dict[1]['le']
    mock_le.inverse_transform.return_value = np.array(["Team A"])
    mock_inference.return_value = pd.DataFrame([["feat1", "feat2"]])

    result = inference_service.infer(1, Data(title_anon="A", description_anon="B"), model_id=0, user_id=custom_user_id)

    assert result == ["Team A"]
    duckdb_service.log_event.assert_called_once()
    assert duckdb_service.log_event.call_args.kwargs["user_id"] == custom_user_id


@patch('app.services.inference_svc.inference')
def test_infer_proba_logs_with_user_id(mock_inference, inference_service):
    duckdb_service = MagicMock()
    inference_service.duckdb_service = duckdb_service
    custom_user_id = "44444444-4444-4444-4444-444444444444"

    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.7, 0.3]])
    inference_service.local_artifacts_store.load_model.return_value = mock_model

    mock_le = inference_service.storage.dataset_dict[1]['le']
    mock_le.classes_ = np.array(["Team A", "Team B"])
    mock_inference.return_value = pd.DataFrame([["feat1", "feat2"]])

    result = inference_service.infer_proba(1, Data(title_anon="A", description_anon="B"), model_id=0, user_id=custom_user_id)

    assert result["classes"] == ["Team A", "Team B"]
    duckdb_service.log_event.assert_called_once()
    assert duckdb_service.log_event.call_args.kwargs["user_id"] == custom_user_id
    assert duckdb_service.log_event.call_args.kwargs["actor_type"] == "ai"
    assert duckdb_service.log_event.call_args.kwargs["agent"] == "classifier_model"
