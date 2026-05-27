import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock

from app.config.config import GROUND_TRUTH_AL_INSTANCE_ID, SYSTEM_USER_ID
from app.persistence.duckdb import DuckDbPersistenceService
from app.services.active_learning_svc import ActiveLearningService
from app.core.storage import ActiveLearningStorage
from app.data_models.active_learning_dm import NewInstance, LabelRequest


def test_indices_use_ref_round_trip(monkeypatch):
    class_list = ["Team A", "Team B"]

    class DummyArtifactsStore:
        def save_encoders(self, *args, **kwargs):
            return None

        def save_vectorized_dataset(self, *args, **kwargs):
            return None

        def save_model(self, *args, **kwargs):
            return "models/1/model_0.joblib"

        def load_model(self, *args, **kwargs):
            class DummyClassifier:
                def predict_proba(self, X):
                    return np.array([[0.7, 0.3] for _ in range(len(X))])

                def predict(self, X):
                    return np.array([index % 2 for index in range(len(X))])

            return DummyClassifier()

    def fake_dispatch_team(duckdb_service, test_set=False, le=None, oh=None, classes=None):
        if not test_set:
            refs = [f"R{i}" for i in range(1, 54)]
            x_train = pd.DataFrame(
                [[float(i), float(i + 1)] for i in range(1, 54)],
                index=refs,
            )
            label_encoder = __import__("sklearn.preprocessing", fromlist=["LabelEncoder"]).LabelEncoder()
            label_encoder.fit(class_list + [np.nan])
            empty_value = label_encoder.transform([np.nan])[0]
            y_train = pd.Series(
                [label_encoder.transform([class_list[i % 2]])[0] for i in range(50)] + [empty_value, empty_value, empty_value],
                index=refs,
            )
            one_hot_encoder = __import__("sklearn.preprocessing", fromlist=["OneHotEncoder"]).OneHotEncoder(handle_unknown="ignore")
            one_hot_encoder.fit([["Hardware", "Network"]])
            return x_train, y_train, label_encoder, one_hot_encoder

        refs = ["T5", "T6"]
        x_test = pd.DataFrame([[0.5, 0.4], [0.6, 0.3]], index=refs)
        y_test = pd.Series([class_list[0], class_list[1]], index=refs)
        return x_test, y_test, le, oh

    monkeypatch.setattr("app.services.active_learning_svc.dispatch_team", fake_dispatch_team)

    storage = ActiveLearningStorage()
    duckdb_service = MagicMock(spec=DuckDbPersistenceService)
    duckdb_service.get_all_instances.return_value = {}
    duckdb_service.save_al_instance.return_value = None
    duckdb_service.save_model_path.return_value = None
    duckdb_service.save_metrics.return_value = None
    duckdb_service.save_labels.return_value = None
    duckdb_service.save_labels.return_value = None

    svc = ActiveLearningService(
        storage,
        duckdb_service=duckdb_service,
        local_artifacts_store=DummyArtifactsStore(),
    )

    new_instance = NewInstance(
        model_name="svm",
        qs_strategy="random sampling",
        class_list=class_list,
        train_data_path="train.csv",
        test_data_path="test.csv",
    )

    instance_id = svc.create_instance(new_instance)

    # When querying, returned ids should be Ref values from X_train index
    query_refs = svc.get_next_instances(instance_id, batch_size=3)
    X_index = storage.dataset_dict[instance_id]["X_train"].index

    assert len(query_refs) > 0
    assert all(ref in X_index for ref in query_refs)

    # Label using Ref values and ensure y is updated at those Ref indices
    le = storage.dataset_dict[instance_id]["le"]
    label_value = class_list[0]
    encoded_label = le.transform([label_value])[0]

    label_request = LabelRequest(query_idx=query_refs, labels=[label_value] * len(query_refs))
    svc.label_instance(instance_id, label_request)

    y_series = storage.dataset_dict[instance_id]["y_train"]
    assert all(y_series.loc[ref] == encoded_label for ref in query_refs)

