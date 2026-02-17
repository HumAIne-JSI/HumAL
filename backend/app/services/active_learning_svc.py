from skactiveml.classifier import SklearnClassifier
from skactiveml.utils import MISSING_LABEL
import numpy as np
import joblib
import os
from typing import Optional
import pandas as pd
from sklearn.metrics import f1_score
from scipy.stats import entropy
from app.config.config import model_dict, qs_dict
from app.core.storage import ActiveLearningStorage
from app.data_models.active_learning_dm import NewInstance, LabelRequest
from app.persistence.duckdb import DuckDbPersistenceService
from app.persistence.local_artifacts import LocalArtifactsStore
from app.services.data_preprocessing import dispatch_team

class ActiveLearningService:
    def __init__(
        self,
        storage: ActiveLearningStorage,
        duckdb_service: Optional[DuckDbPersistenceService] = None,
        local_artifacts_store: Optional[LocalArtifactsStore] = None,
    ):
        self.storage = storage
        self.duckdb_service = duckdb_service
        self.local_artifacts_store = local_artifacts_store
        if self.duckdb_service is not None and self.local_artifacts_store is not None:
            self._load_from_persistence()

    # Logic for creating a new active learning instance
    def create_instance(self, new_instance: NewInstance):
        # Get next available instance ID
        instance_id = self.storage.get_next_instance_id()
        
        # Define the classes as integers
        new_instance.class_list = new_instance.class_list
        classes = list(range(len(new_instance.class_list)+1))
        
        # Initialize active learning instance
        self.storage.al_instances_dict[instance_id] = {
            'model': model_dict[new_instance.model_name],
            'model_name': new_instance.model_name,
            'qs': new_instance.qs_strategy,
            'classes': classes
        }
        
        # Preprocess the data (indices stay as Ref)
        X_train, y_train, le, oh = dispatch_team(new_instance.train_data_path, test_set=False, classes=new_instance.class_list)
        X_test, y_test, _, _ = dispatch_team(new_instance.test_data_path, test_set=True, le=le, oh=oh)
        
        # Get the index of np.nan in the LabelEncoder's classes
        empty = le.transform([np.nan])[0]
        # Replace missing values with MISSING_LABEL in y_train (indexed by Ref)
        y_train = y_train.replace(empty, MISSING_LABEL)
        
        # save the data to the dataset dictionary
        self.storage.dataset_dict[instance_id] = {
            'X_train': X_train,
            'y_train': y_train,
            'X_test': X_test,
            'y_test': y_test,
            'le': le,
            'oh': oh,
            'train_data_path': new_instance.train_data_path,
            'test_data_path': new_instance.test_data_path
        }

        # Save the dictionary elements to persistence
        if self.duckdb_service is not None and self.local_artifacts_store is not None:
            al_instance_data = self.storage.al_instances_dict[instance_id]
            al_instance_data["train_data_path"] = new_instance.train_data_path
            al_instance_data["test_data_path"] = new_instance.test_data_path

            self.duckdb_service.save_al_instance(
                instance_id=instance_id,
                instance_data = al_instance_data
            )

            self.local_artifacts_store.save_encoders(
                al_instance_id=instance_id,
                label_encoder=le,
                one_hot_encoder=oh
            )

            self.local_artifacts_store.save_vectorized_dataset(
                al_instance_id=instance_id,
                X=X_train,
                split="train"
            )
            self.local_artifacts_store.save_vectorized_dataset(
                al_instance_id=instance_id,
                X=X_test,
                split="test"
            )


        return instance_id

    def _load_from_persistence(self) -> None:
        instances = self.duckdb_service.get_all_instances()
        if not instances:
            return

        for instance_id, instance_data in instances.items():
            model_name = instance_data.get("model_name")
            qs_name = instance_data.get("qs")
            classes = instance_data.get("classes")
            train_data_path = instance_data.get("train_data_path")
            test_data_path = instance_data.get("test_data_path")

            model = model_dict.get(model_name)
            if model is None or qs_name not in qs_dict:
                print(f"Warning: Skipping instance {instance_id} - invalid model '{model_name}' or query strategy '{qs_name}'")
                continue

            if train_data_path is None or test_data_path is None:
                print(f"Warning: Skipping instance {instance_id} - missing train or test data path")
                continue

            try:
                le, oh = self.local_artifacts_store.load_encoders(instance_id)
                X_train = self.local_artifacts_store.load_vectorized_dataset(
                    instance_id,
                    split="train",
                )
                X_test = self.local_artifacts_store.load_vectorized_dataset(
                    instance_id,
                    split="test",
                )
            except FileNotFoundError:
                print(f"Warning: Skipping instance {instance_id} - missing encoders or vectorized datasets")
                continue

            y_train = self.duckdb_service.load_labels(instance_id, split="train")
            y_train = self._encode_labels(y_train, le)
            y_train = self._align_labels(y_train, X_train.index, fill_missing=MISSING_LABEL)

            y_test = self.duckdb_service.load_labels(instance_id, split="test")
            y_test = self._encode_labels(y_test, le)
            y_test = self._align_labels(y_test, X_test.index, fill_missing=np.nan)

            self.storage.al_instances_dict[instance_id] = {
                "model": model,
                "model_name": model_name,
                "qs": qs_name,
                "classes": classes,
            }

            self.storage.dataset_dict[instance_id] = {
                "X_train": X_train,
                "y_train": y_train,
                "X_test": X_test,
                "y_test": y_test,
                "le": le,
                "oh": oh,
                "train_data_path": train_data_path,
                "test_data_path": test_data_path
            }

            metrics = self.duckdb_service.load_all_metrics(instance_id)
            self.storage.results_dict[instance_id] = {
                "mean_entropies": [m["mean_entropy"] for m in metrics],
                "f1_scores": [m["f1_score"] for m in metrics],
                "num_labeled": [m["num_labeled"] for m in metrics],
            }

            model_paths = self.duckdb_service.load_model_paths(instance_id)
            self.storage.model_paths_dict[instance_id] = model_paths

    def _align_labels(
        self,
        labels: pd.Series,
        index: pd.Index,
        *,
        fill_missing: object,
    ) -> pd.Series:
        if labels is None or labels.empty:
            return pd.Series([fill_missing] * len(index), index=index)

        # Create result series with fill_missing as default
        result = pd.Series([fill_missing] * len(index), index=index, dtype=object)
        # Update with actual labels where they exist
        result.loc[labels.index] = labels.values
        return result
    
    def _encode_labels(self, labels: pd.Series, label_encoder) -> pd.Series:
        """Encode labels using label encoder, preserving NaN as NaN."""
        if labels is None or labels.empty:
            return labels
        
        encoded = labels.copy()
        mask = labels.notna()
        encoded[mask] = labels[mask].apply(lambda x: label_encoder.transform([x])[0])
        return encoded

    # Logic for getting the next instances
    def get_next_instances(self, al_instance_id: int, batch_size: int = 1):        
        # Get the data
        X = self.storage.dataset_dict[al_instance_id]['X_train']
        y = self.storage.dataset_dict[al_instance_id]['y_train']
        
        # Get the query strategy, model and classes
        instance = self.storage.al_instances_dict[al_instance_id]
        qs_name = instance['qs']
        qs = qs_dict[qs_name]
        model = instance['model']
        classes = instance['classes']
        
        # Initialize classifier
        clf = SklearnClassifier(model, classes=classes)
        
        # Get the query indices
        if qs_name == 'random sampling':
            query_idx = qs.query(X=X, y=y, batch_size=batch_size)
        #elif qs_name == 'query by committee':
        #    query_idx = qs.query(X=X, y=y, batch_size=batch_size, ensemble=qb_c)
        elif qs_name == 'value of information':
            query_idx = qs.query(X=X, y=y, clf=clf, ignore_partial_fit=True, batch_size=batch_size)
        else:
            query_idx = qs.query(X=X, y=y, batch_size=batch_size, clf=clf)
        
        # convert the query_idx to the original Ref values using positional lookup
        query_idx = list(self.storage.dataset_dict[al_instance_id]['X_train'].index[query_idx])
        
        # Return the query indices
        return query_idx

    # Logic for labeling instances
    def label_instance(self, al_instance_id: int, label_request: LabelRequest):
        # get the data
        # X = self.storage.dataset_dict[al_instance_id]['X_train']
        y = self.storage.dataset_dict[al_instance_id]['y_train']
        # X_test = self.storage.dataset_dict[al_instance_id]['X_test']
        # y_test = self.storage.dataset_dict[al_instance_id]['y_test']
        
        # Get the query indices and labels
        query_idx = label_request.query_idx
        labels = label_request.labels
        # change None to np.nan
        labels = [np.nan if label is None else label for label in labels]
        
        le = self.storage.dataset_dict[al_instance_id]['le']
        # convert the labels to integers
        labels = le.transform(labels)
        
        if al_instance_id not in self.storage.al_instances_dict:
            return {"error": "Instance not found"}
        
        #instance = self.storage.al_instances_dict[al_instance_id]
        
        # update the labels
        # use Ref-based labels directly against index
        y.loc[query_idx] = labels

        # Save the labels to persistence
        self.duckdb_service.save_labels(
            al_instance_id=al_instance_id,
            user_id="00000000-0000-0000-0000-000000000000",  # System user ID for now
            labels_dict=dict(zip(query_idx, labels)),
            split="train"
        )

    # Logic for updating the model
    def update_model(self, al_instance_id: int):
        # Instance
        instance = self.storage.al_instances_dict[al_instance_id]

        # get the data
        X = self.storage.dataset_dict[al_instance_id]['X_train']
        y = self.storage.dataset_dict[al_instance_id]['y_train']
        
        # get the model
        model = instance['model']
        clf = SklearnClassifier(model, classes=instance['classes'])

        # Train the model
        clf.fit(X, y)
        
        # create the model directory if it doesn't exist
        os.makedirs(f'models/{al_instance_id}', exist_ok=True)
        
        # save the model (the clf object)
        model_path = self.local_artifacts_store.save_model(
            al_instance_id=al_instance_id, 
            model_id=0, 
            model=clf)
        
        
        # save the model path
        if al_instance_id not in self.storage.model_paths_dict:
            self.storage.model_paths_dict[al_instance_id] = {}
        self.storage.model_paths_dict[al_instance_id][0] = model_path

        # Save the model path to persistence
        self.duckdb_service.save_model_path(
            al_instance_id=al_instance_id,
            model_id=0,
            path_to_model=model_path
        )


    def calculate_metrics(self, al_instance_id: int):
        # Get the data
        X_test = self.storage.dataset_dict[al_instance_id]['X_test']
        y_test = self.storage.dataset_dict[al_instance_id]['y_test']
        y = self.storage.dataset_dict[al_instance_id]['y_train']

        # Get the label encoder
        le = self.storage.dataset_dict[al_instance_id]['le']

        # Get the model
        clf = self.local_artifacts_store.load_model(al_instance_id, 0)

        # calculate the entropy of the model
        mean_entropy = np.mean(entropy(clf.predict_proba(X_test), axis=1))
        
        # calculate the number of labeled instances
        num_labeled = int(y.value_counts().sum())
        
        # save the mean entropy
        if al_instance_id not in self.storage.results_dict:
            self.storage.results_dict[al_instance_id] = {
                "mean_entropies": [],
                "f1_scores": [],
                "num_labeled": []
            }
        self.storage.results_dict[al_instance_id]["mean_entropies"].append(mean_entropy)
        
        self.storage.results_dict[al_instance_id]["num_labeled"].append(num_labeled)
        # calculate the f1 score of the model
        predictions = clf.predict(X_test)
        
        # Handle NaN values in y_test before calculating f1_score
        # Check if y_test contains string values or numerical values
        if y_test.dtype.kind in ['U', 'S', 'O']:  # String or object dtype
            # For string values, replace NaN with "NotANumber"
            y_test = np.array(["NotANumber" if pd.isna(val) else val for val in y_test])
        else:  # Numerical dtype
            # For numerical values, replace NaN with inf
            y_test = np.array([float('inf') if pd.isna(val) else val for val in y_test])
        
        f1 = f1_score(y_test, le.inverse_transform(predictions), average='macro')
        self.storage.results_dict[al_instance_id]["f1_scores"].append(f1)

        # Save the metrics to persistence
        self.duckdb_service.save_metrics(
            al_instance_id=al_instance_id,
            f1_score=f1,
            mean_entropy=mean_entropy,
            num_labeled=num_labeled
        )

    # Logic for saving the model
    def save_model(self, al_instance_id: int):
        if al_instance_id not in self.storage.model_paths_dict:
            self.storage.model_paths_dict[al_instance_id] = {}

        # Get the current model
        current_model = self.local_artifacts_store.load_model(al_instance_id, 0)
        
        # Save the model
        model_id = max(self.storage.model_paths_dict[al_instance_id].keys()) + 1
        model_path = self.local_artifacts_store.save_model(
            al_instance_id=al_instance_id, 
            model_id=model_id, 
            model=current_model
            )
        
        # Save the model path
        self.storage.model_paths_dict[al_instance_id][model_id] = model_path

        # Save the model path to persistence
        self.duckdb_service.save_model_path(
            al_instance_id=al_instance_id,
            model_id=model_id,
            path_to_model=model_path
        )

        return model_id
    
    # Logic for deleting an active learning instance
    def delete_instance(self, al_instance_id: int):
        # delete the instance from the dictionaries
        del self.storage.al_instances_dict[al_instance_id]
        del self.storage.dataset_dict[al_instance_id]
        del self.storage.results_dict[al_instance_id]
        
        # delete the model dictionary
        del self.storage.model_paths_dict[al_instance_id]

        # Delete the local artifacts
        self.local_artifacts_store.delete_instance_artifacts(al_instance_id)

        # Delete the instance from persistence
        self.duckdb_service.delete_al_instance(al_instance_id)
