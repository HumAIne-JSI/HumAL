import pandas as pd
from pathlib import Path

from app.services.active_learning_svc import ActiveLearningService
from app.core.storage import ActiveLearningStorage
from app.data_models.active_learning_dm import NewInstance, LabelRequest


def test_indices_use_ref_round_trip():
    base_dir = Path(__file__).resolve().parents[2]  # backend/
    data_dir = base_dir / "data"

    train_path = str(data_dir / "al_demo_train_data.csv")
    test_path = str(data_dir / "al_demo_test_data.csv")
    labels_path = data_dir / "al_demo_train_labels_dispatch.csv"

    labels_df = pd.read_csv(labels_path)
    labels_df.set_index("Ref", inplace=True)
    class_list = [c for c in labels_df["Team->Name"].dropna().unique().tolist()]

    storage = ActiveLearningStorage()
    svc = ActiveLearningService(storage)

    new_instance = NewInstance(
        model_name="svm",
        qs_strategy="random sampling",
        class_list=class_list,
        train_data_path=train_path,
        test_data_path=test_path,
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

