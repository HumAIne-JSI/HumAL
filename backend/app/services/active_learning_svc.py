from skactiveml.classifier import SklearnClassifier
from skactiveml.utils import MISSING_LABEL, is_unlabeled
import numpy as np
import joblib
import json
import os
import time
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Optional
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize
from scipy.stats import entropy
from app.config.config import model_dict, qs_dict, SENTENCE_TRANSFORMERS_MODEL
from app.core.storage import ActiveLearningStorage
from app.data_models.active_learning_dm import LabelInfo, LabelRequest, NewInstance
from app.persistence.duckdb import DuckDbPersistenceService
from app.persistence.local_artifacts import LocalArtifactsStore
from app.services.data_preprocessing import dispatch_team
from app.config.config import SYSTEM_USER_ID
from app.persistence.minio_storage import MinioService
from app.services.benchmarking_svc import BenchmarkingService
import logging

logger = logging.getLogger(__name__)

MIN_INITIAL_LABELED = 50


class ActiveLearningService:
    def __init__(
        self,
        storage: ActiveLearningStorage,
        duckdb_service: Optional[DuckDbPersistenceService] = None,
        local_artifacts_store: Optional[LocalArtifactsStore] = None,
        minio_service: Optional[MinioService] = None,
        benchmarking_service: Optional[BenchmarkingService] = None,
    ):
        self.storage = storage
        self.duckdb_service = duckdb_service
        self.local_artifacts_store = local_artifacts_store
        self.minio_service = minio_service
        self.benchmarking_service = benchmarking_service
        if self.duckdb_service is not None and self.local_artifacts_store is not None:
            self._load_from_persistence()

    def _log_event(
        self,
        *,
        al_instance_id: int,
        action: str,
        latency_ms: int,
        payload: dict,
        user_id: str = SYSTEM_USER_ID,
        actor_type: Optional[str] = None,
        agent: Optional[str] = None,
        object_id: Optional[str] = None,
        duration_s: Optional[float] = None,
        correct: Optional[bool] = None,
        ai_suggested: Optional[str] = None,
    ) -> None:
        if self.duckdb_service is None:
            return

        self.duckdb_service.log_event(
            al_instance_id=al_instance_id,
            user_id=user_id,
            action=action,
            latency_ms=latency_ms,
            payload=payload,
            actor_type=actor_type,
            agent=agent,
            object_id=object_id,
            duration_s=duration_s,
            correct=correct,
            ai_suggested=ai_suggested,
        )

    # Logic for creating a new active learning instance
    def create_instance(self, new_instance: NewInstance, user_id: str = SYSTEM_USER_ID):
        start_time = time.perf_counter()
        # Get next available instance ID
        instance_id = self.duckdb_service.get_next_instance_id()
        
        # Define the classes as integers
        new_instance.class_list = new_instance.class_list
        classes = list(range(len(new_instance.class_list)+1))
        
        # Preprocess the data (indices stay as Ref)
        X_train, y_train, le, oh = dispatch_team(duckdb_service=self.duckdb_service, test_set=False, classes=new_instance.class_list)
        X_test, y_test, _, _ = dispatch_team(duckdb_service=self.duckdb_service, test_set=True, le=le, oh=oh)
        
        # Get the index of np.nan in the LabelEncoder's classes
        empty = le.transform([np.nan])[0]
        # Replace missing values with MISSING_LABEL in y_train (indexed by Ref)
        y_train = y_train.replace(empty, MISSING_LABEL)

        labeled_count = int(y_train.notna().sum())
        if labeled_count < MIN_INITIAL_LABELED:
            raise ValueError(
                "Initial dataset must contain at least 50 labeled instances to create an AL instance."
            )

        # Initialize active learning instance after the threshold check passes.
        self.storage.al_instances_dict[instance_id] = {
            'model': model_dict[new_instance.model_name],
            'model_name': new_instance.model_name,
            'qs': new_instance.qs_strategy,
            'classes': classes,
            'user_id': user_id,
        }
        
        # save the data to the dataset dictionary
        self.storage.dataset_dict[instance_id] = {
            'X_train': X_train,
            'y_train': y_train,
            'X_test': X_test,
            'y_test': y_test,
            'le': le,
            'oh': oh,
        }

        # Save the dictionary elements to persistence
        if self.duckdb_service is not None and self.local_artifacts_store is not None:
            al_instance_data = self.storage.al_instances_dict[instance_id]

            self.duckdb_service.save_al_instance(
                al_instance_id=instance_id,
                instance_data=al_instance_data,
                user_id=user_id,
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

            self.update_model(instance_id)
            self.calculate_metrics(instance_id)

        # Save the datasets, encoders and labels to MinIO
        if self.minio_service is not None:
            self.minio_service.save_label_encoder(
                al_instance_id=instance_id,
                encoder=le
            )

            self.minio_service.save_one_hot_encoder(
                al_instance_id=instance_id,
                encoder=oh
            )

            self.minio_service.save_vectorized_tickets(
                al_instance_id=instance_id,
                tickets_version=0,
                split="train",
                df=X_train
            )

            self.minio_service.save_vectorized_tickets(
                al_instance_id=instance_id,
                tickets_version=0,
                df=X_test,
                split="test"
            )

            self.minio_service.save_labels(
                al_instance_id=instance_id,
                labels_version=0,
                split="train",
                df=y_train
            )

            self.minio_service.save_labels(
                al_instance_id=instance_id,
                labels_version=0,
                split="test",
                df=y_test
            )

        self._log_event(
            al_instance_id=instance_id,
            action="create_al_instance",
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            actor_type="system",
            agent="orchestrator",
            object_id=str(instance_id),
            payload={
                "pool_size": int(len(X_train)),
                "embedding_model": SENTENCE_TRANSFORMERS_MODEL,
                "train_data_path": self.minio_service.return_data_names("train") if self.minio_service is not None else "",
                "test_data_path": self.minio_service.return_data_names("test") if self.minio_service is not None else "",
            },
            user_id=user_id,
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

            model = model_dict.get(model_name)
            if model is None or qs_name not in qs_dict:
                print(f"Warning: Skipping instance {instance_id} - invalid model '{model_name}' or query strategy '{qs_name}'")
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
            y_train = self._align_labels(y_train, X_train.index, fill_missing=MISSING_LABEL)
            y_train = self._encode_labels(y_train, le)

            y_test = self.duckdb_service.load_labels(instance_id, split="test")
            y_test = self._align_labels(y_test, X_test.index, fill_missing=np.nan)
            #y_test = self._encode_labels(y_test, le)

            self.storage.al_instances_dict[instance_id] = {
                "model": model,
                "model_name": model_name,
                "qs": qs_name,
                "classes": classes,
                "user_id": instance_data.get("user_id"),
            }

            self.storage.dataset_dict[instance_id] = {
                "X_train": X_train,
                "y_train": y_train,
                "X_test": X_test,
                "y_test": y_test,
                "le": le,
                "oh": oh,
            }

            metrics = self.duckdb_service.load_all_metrics(instance_id)
            self.storage.results_dict[instance_id] = {
                "mean_entropies": [m["mean_entropy"] for m in metrics],
                "f1_scores": [m["f1_score"] for m in metrics],
                "num_labeled": [m["num_labeled"] for m in metrics],
                "accuracies": [m.get("accuracy") for m in metrics],
                "precisions_macro": [m.get("precision_macro") for m in metrics],
                "precisions_weighted": [m.get("precision_weighted") for m in metrics],
                "recalls_macro": [m.get("recall_macro") for m in metrics],
                "recalls_weighted": [m.get("recall_weighted") for m in metrics],
                "f1_per_class": [m.get("f1_per_class") for m in metrics],
                "confusion_matrices": [m.get("confusion_matrix") for m in metrics],
                "roc_aucs_ovr_macro": [m.get("roc_auc_ovr_macro") for m in metrics],
            }

            model_paths = self.duckdb_service.load_model_paths(instance_id)
            self.storage.model_paths_dict[instance_id] = model_paths

            skipped_refs = self.duckdb_service.load_skipped_refs(al_instance_id=instance_id)
            self.storage.skipped_tickets[instance_id] = set(skipped_refs)

    def _align_labels(
        self,
        labels: pd.Series,
        index: pd.Index,
        *,
        fill_missing: object,
    ) -> pd.Series:
        if labels is None or labels.empty:
            return pd.Series([fill_missing] * len(index), index=index)

        return labels.reindex(index).fillna(fill_missing)

    def _validate_labels(self, labels: list[object], label_encoder) -> None:
        """Validate that every non-missing label exists in the fitted encoder.

        Args:
            labels: Raw labels received from the client or persistence layer.
            label_encoder: Fitted ``LabelEncoder`` for the active-learning instance.

        Raises:
            ValueError: If one or more labels are not present in the encoder classes.
        """
        if labels is None:
            return

        allowed_labels = label_encoder.classes_.tolist()
        unknown_labels = []

        for label in labels:
            if pd.isna(label):
                continue
            if label not in label_encoder.classes_ and label not in unknown_labels:
                unknown_labels.append(label)

        if unknown_labels:
            raise ValueError(
                f"Unknown labels: {unknown_labels}. Available labels: {allowed_labels}"
            )
    
    def _encode_labels(self, labels: pd.Series, label_encoder) -> pd.Series:
        """Encode labels using label encoder, preserving NaN as NaN."""
        if labels is None or labels.empty:
            return labels
        
        encoded = labels.copy()
        self._validate_labels(encoded.tolist(), label_encoder)
        encoded = label_encoder.transform(encoded)

        encoded = pd.Series(encoded, index=labels.index)

        # Get the index of np.nan in the LabelEncoder's classes
        empty = label_encoder.transform([np.nan])[0]
        # Replace missing values with MISSING_LABEL in y_train (indexed by Ref)
        encoded = encoded.replace(empty, MISSING_LABEL)
        
        # encoded = labels.copy()
        # mask = labels.notna()
        # encoded[mask] = labels[mask].apply(lambda x: label_encoder.transform([x])[0])
        return encoded

    def _apply_label_request(self, al_instance_id: int, query_idx: list[int | str], labels: list[str | int | None], user_id: str = SYSTEM_USER_ID) -> None:
        y = self.storage.dataset_dict[al_instance_id]['y_train']

        normalized_labels = [np.nan if label is None else label for label in labels]
        le = self.storage.dataset_dict[al_instance_id]['le']
        self._validate_labels(normalized_labels, le)

        labels_encoded = le.transform(normalized_labels)

        # Use Ref-based labels directly against the index.
        y.loc[query_idx] = labels_encoded

        if self.duckdb_service is not None:
            self.duckdb_service.save_labels(
                al_instance_id=al_instance_id,
                user_id=user_id,
                labels_dict={str(ticket_id): label for ticket_id, label in zip(query_idx, normalized_labels)},
                split="train",
            )

        if self.minio_service is not None:
            self.minio_service.save_labels(
                al_instance_id=al_instance_id,
                labels_version=0,
                split="train",
                df=y,
            )

    # Logic for getting the next instances
    def get_next_instances(self, al_instance_id: int, batch_size: int = 1, user_id: str = SYSTEM_USER_ID):
        start_time = time.perf_counter()
        # Get the data
        X = self.storage.dataset_dict[al_instance_id]['X_train']
        y = self.storage.dataset_dict[al_instance_id]['y_train']

        # Get the query strategy, model and classes
        instance = self.storage.al_instances_dict[al_instance_id]
        qs_name = instance['qs']
        qs = qs_dict[qs_name]
        model = instance['model']
        classes = instance['classes']

        self._log_event(
            al_instance_id=al_instance_id,
            action="request_batch",
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            actor_type="system",
            agent="orchestrator",
            object_id="pool_main",
            payload={
                "batch_size": batch_size,
                "strategy": qs_name,
                "pool_size": int(len(X)),
            },
            user_id=user_id,
        )

        # Build the candidate set: unlabeled tickets that are not retired via i_dont_know.
        skip_refs = self.storage.skipped_tickets.get(al_instance_id, set())
        unlabeled_mask = np.asarray(is_unlabeled(y, missing_label=MISSING_LABEL))
        not_skipped = ~np.asarray(y.index.isin(list(skip_refs)))
        candidates_idx = np.where(unlabeled_mask & not_skipped)[0]

        if len(candidates_idx) == 0:
            batch_id = int(time.time() * 1000)
            self._log_event(
                al_instance_id=al_instance_id,
                action="select_batch",
                latency_ms=int((time.perf_counter() - start_time) * 1000),
                actor_type="ai",
                agent="al_model",
                object_id=f"BATCH_{batch_id}",
                payload={
                    "batch_id": batch_id,
                    "ids": [],
                    "uncertainties": None,
                },
                user_id=user_id,
            )
            return []

        # Initialize classifier
        clf = SklearnClassifier(model, classes=classes)

        # Get the query indices
        if qs_name == 'random sampling':
            query_idx = qs.query(X=X, y=y, candidates=candidates_idx, batch_size=batch_size)
        #elif qs_name == 'query by committee':
        #    query_idx = qs.query(X=X, y=y, candidates=candidates_idx, batch_size=batch_size, ensemble=qb_c)
        elif qs_name == 'value of information':
            query_idx = qs.query(X=X, y=y, clf=clf, ignore_partial_fit=True, candidates=candidates_idx, batch_size=batch_size)
        else:
            query_idx = qs.query(X=X, y=y, candidates=candidates_idx, batch_size=batch_size, clf=clf)

        # convert the query_idx to the original Ref values using positional lookup
        query_idx = list(self.storage.dataset_dict[al_instance_id]['X_train'].index[query_idx])

        batch_id = int(time.time() * 1000)
        self._log_event(
            al_instance_id=al_instance_id,
            action="select_batch",
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            actor_type="ai",
            agent="al_model",
            object_id=f"BATCH_{batch_id}",
            payload={
                "batch_id": batch_id,
                "ids": query_idx,
                "uncertainties": None,
            },
            user_id=user_id,
        )

        # Return the query indices
        return query_idx

    # Logic for labeling instances
    def label_instance(self, al_instance_id: int, label_request: LabelRequest, user_id: str = SYSTEM_USER_ID):
        if al_instance_id not in self.storage.al_instances_dict:
            return {"error": "Instance not found"}
        self._apply_label_request(al_instance_id, label_request.query_idx, label_request.labels, user_id=user_id)

    def label_with_info(self, al_instance_id: int, label_info: list[LabelInfo], user_id: str = SYSTEM_USER_ID, username: str = "system"):
        """Label tickets and log the human review metadata.

        Args:
            al_instance_id: Active-learning instance identifier.
            label_info: Validated label metadata objects for each labeled ticket.
            user_id: User identifier used for event logging.
            username: Username of the acting user, used as the agent field for human events.

        Returns:
            A simple success payload after labels are applied, events are logged,
            and any configured benchmark export is triggered.

        Raises:
            ValueError: If the provided labels are invalid for the fitted encoder.
        """
        request_start = time.perf_counter()

        real_items = [item for item in label_info if not item.i_dont_know]
        idk_items = [item for item in label_info if item.i_dont_know]

        if real_items:
            query_idx = [item.ticket_id for item in real_items]
            labels = [item.label for item in real_items]
            self._apply_label_request(al_instance_id, query_idx, labels, user_id=user_id)

        skip_set = self.storage.skipped_tickets.setdefault(al_instance_id, set())
        for item in idk_items:
            skip_set.add(str(item.ticket_id))

        if self.duckdb_service is not None:
            for item in label_info:
                is_idk = bool(item.i_dont_know)
                if is_idk:
                    action = "i_dont_know"
                elif item.model_prediction is not None and item.label != item.model_prediction:
                    action = "override_label"
                else:
                    action = "confirm_label"

                duration_s = (item.end_time - item.start_time).total_seconds()
                payload = {
                    "ticket_id": item.ticket_id,
                    "new_label": None if is_idk else item.label,
                }
                if item.model_prediction is not None:
                    payload["model_prediction"] = item.model_prediction
                if item.most_helpful_feature is not None:
                    payload["most_helpful_feature"] = item.most_helpful_feature
                if is_idk:
                    payload["i_dont_know"] = True

                self._log_event(
                    al_instance_id=al_instance_id,
                    action=action,
                    latency_ms=int((time.perf_counter() - request_start) * 1000),
                    actor_type="human",
                    agent=username,
                    object_id=item.ticket_id,
                    duration_s=duration_s,
                    correct=None if is_idk else ((item.label == item.model_prediction) if item.model_prediction is not None else None),
                    ai_suggested=item.model_prediction,
                    payload=payload,
                    user_id=user_id,
                )

                self.duckdb_service.upsert_label_decision(
                    al_instance_id=al_instance_id,
                    ref=str(item.ticket_id),
                    user_id=user_id,
                    label=None if is_idk else item.label,
                    labeled_at=item.end_time,
                    model_prediction=item.model_prediction,
                    latency_ms=int(duration_s * 1000),
                    most_helpful_feature=item.most_helpful_feature,
                    is_tired=item.is_tired,
                    is_difficult=item.is_difficult,
                    i_dont_know=item.i_dont_know,
                )

        if self.duckdb_service is not None and self.benchmarking_service is not None:
            self.benchmarking_service.export_if_needed(al_instance_id, user_id=user_id)

        return {"message": "Labels updated"}

    # Logic for updating the model
    def update_model(self, al_instance_id: int, user_id: str = SYSTEM_USER_ID):
        start_time = time.perf_counter()
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

        self._log_event(
            al_instance_id=al_instance_id,
            action="train",
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            actor_type="system",
            agent="classifier_model",
            object_id="model",
            payload={
                "model_name": instance['model_name'],
                "num_labeled": int(y.value_counts().sum()),
                "train_samples": int(len(X)),
                "model_id": 0,
            },
            user_id=user_id,
        )
        
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

        # Save the model to MinIO (original model, not the clf wrapper (easier integration with outside services))
        if self.minio_service is not None:
            self.minio_service.save_model(
                al_instance_id=al_instance_id,
                model_version=0,
                model=clf.estimator_
            )


    def calculate_metrics(self, al_instance_id: int, user_id: str = SYSTEM_USER_ID):
        start_time = time.perf_counter()
        # Get the data
        X_test = self.storage.dataset_dict[al_instance_id]['X_test']
        y_test_raw = self.storage.dataset_dict[al_instance_id]['y_test']
        y = self.storage.dataset_dict[al_instance_id]['y_train']

        # Get the label encoder and the model's class labels
        le = self.storage.dataset_dict[al_instance_id]['le']
        class_labels = [c for c in le.classes_ if not pd.isna(c)]

        # Get the model
        clf = self.local_artifacts_store.load_model(al_instance_id, 0)

        # --- SINGLE inference pass (reused for every metric) ---
        proba = clf.predict_proba(X_test)
        mean_entropy = np.mean(entropy(proba, axis=1))
        # argmax(proba) == clf.predict() because classes are encoded 0..n-1
        predictions = le.inverse_transform(np.argmax(proba, axis=1))

        # number of labeled instances
        num_labeled = int(y.value_counts().sum())

        # Filter out unlabeled test rows (where y_test is NaN). The model is
        # not at fault for unlabeled rows, so they are dropped from every metric
        # rather than treated as a phantom "NotANumber" class.
        valid_mask = ~pd.isna(np.asarray(y_test_raw))
        y_test = np.asarray(y_test_raw)[valid_mask]
        proba = proba[valid_mask]
        predictions = (
            le.inverse_transform(np.argmax(proba, axis=1))
            if len(proba) > 0
            else np.array([], dtype=object)
        )

        # --- Classification metrics (all reuse the single `predictions`) ---
        if len(y_test) == 0:
            accuracy = f1 = precision_macro = precision_weighted = recall_macro = recall_weighted = roc_auc = None
            f1_per_class = cm = None
        else:
            accuracy = accuracy_score(y_test, predictions)
            f1 = f1_score(y_test, predictions, average='macro', zero_division=0)
            f1_per_class = f1_score(
                y_test, predictions, average=None, labels=class_labels, zero_division=0
            ).tolist()
            precision_macro = precision_score(y_test, predictions, average='macro', zero_division=0)
            precision_weighted = precision_score(y_test, predictions, average='weighted', zero_division=0)
            recall_macro = recall_score(y_test, predictions, average='macro', zero_division=0)
            recall_weighted = recall_score(y_test, predictions, average='weighted', zero_division=0)
            cm = confusion_matrix(y_test, predictions, labels=class_labels).tolist()

            # --- ROC-AUC (one-vs-rest, macro) ---
            roc_auc = None
            n_classes = proba.shape[1]
            if len(np.unique(y_test)) >= 2:
                try:
                    if n_classes > 2:
                        y_bin = label_binarize(y_test, classes=class_labels)
                        roc_auc = roc_auc_score(
                            y_bin, proba, multi_class='ovr', average='macro'
                        )
                    elif n_classes == 2:
                        roc_auc = roc_auc_score(le.transform(y_test), proba[:, 1])
                except (ValueError, IndexError):
                    roc_auc = None
                if roc_auc is not None and np.isnan(roc_auc):
                    roc_auc = None

        # --- In-memory results ---
        if al_instance_id not in self.storage.results_dict:
            self.storage.results_dict[al_instance_id] = {
                "mean_entropies": [],
                "f1_scores": [],
                "num_labeled": [],
                "accuracies": [],
                "precisions_macro": [],
                "precisions_weighted": [],
                "recalls_macro": [],
                "recalls_weighted": [],
                "f1_per_class": [],
                "confusion_matrices": [],
                "roc_aucs_ovr_macro": [],
            }
        r = self.storage.results_dict[al_instance_id]
        r["mean_entropies"].append(mean_entropy)
        r["num_labeled"].append(num_labeled)
        r["f1_scores"].append(f1)
        r["accuracies"].append(accuracy)
        r["precisions_macro"].append(precision_macro)
        r["precisions_weighted"].append(precision_weighted)
        r["recalls_macro"].append(recall_macro)
        r["recalls_weighted"].append(recall_weighted)
        r["f1_per_class"].append(f1_per_class)
        r["confusion_matrices"].append(cm)
        r["roc_aucs_ovr_macro"].append(roc_auc)

        # --- DuckDB persistence ---
        self.duckdb_service.save_metrics(
            al_instance_id=al_instance_id,
            f1_score=f1,
            mean_entropy=mean_entropy,
            num_labeled=num_labeled,
            accuracy=accuracy,
            precision_macro=precision_macro,
            precision_weighted=precision_weighted,
            recall_macro=recall_macro,
            recall_weighted=recall_weighted,
            f1_per_class=f1_per_class,
            confusion_matrix=cm,
            roc_auc_ovr_macro=roc_auc,
        )

        self._log_event(
            al_instance_id=al_instance_id,
            action="evaluate",
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            actor_type="system",
            agent="classifier_model",
            object_id="model",
            payload={
                "f1_macro": float(f1) if f1 is not None else None,
                "mean_entropy": float(mean_entropy),
                "num_labeled": int(num_labeled),
                "accuracy": float(accuracy) if accuracy is not None else None,
                "precision_macro": float(precision_macro) if precision_macro is not None else None,
                "precision_weighted": float(precision_weighted) if precision_weighted is not None else None,
                "recall_macro": float(recall_macro) if recall_macro is not None else None,
                "recall_weighted": float(recall_weighted) if recall_weighted is not None else None,
                "f1_per_class": f1_per_class,
                "confusion_matrix": cm,
                "roc_auc_ovr_macro": float(roc_auc) if roc_auc is not None else None,
            },
            user_id=user_id,
        )

    def get_instance_info(self, al_instance_id: int):
        # Base info
        info = self.storage.results_dict.get(al_instance_id, {}).copy()
        
        # Enrich with instance info from duckdb (like creation date)
        if self.duckdb_service is not None:
            db_info = self.duckdb_service.load_al_instance(al_instance_id)
            if db_info:
                info["created_at"] = db_info.get("created_at")
            
        # Get training datasets names available from MinIO if configured
        if self.minio_service is not None:
            try:
                info["train_datasets_minio"] = self.minio_service.return_data_names("train")
            except Exception as e:
                logger.warning(f"Could not retrieve train dataset names from MinIO: {e}")
        else:
            info["train_datasets_minio"] = []
            
        return info

    # Logic for saving the model
    def save_model(self, al_instance_id: int, user_id: str = SYSTEM_USER_ID):
        start_time = time.perf_counter()
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

        # Save the model, vectorized datasets and labels to MinIO
        if self.minio_service is not None:
            self.minio_service.save_vectorized_tickets(
                al_instance_id=al_instance_id,
                tickets_version=model_id,
                split="train",
                df=self.storage.dataset_dict[al_instance_id]['X_train']
            )

            self.minio_service.save_vectorized_tickets(
                al_instance_id=al_instance_id,
                tickets_version=model_id,
                df=self.storage.dataset_dict[al_instance_id]['X_test'],
                split="test"
            )

            self.minio_service.save_labels(
                al_instance_id=al_instance_id,
                labels_version=model_id,
                split="train",
                df=self.storage.dataset_dict[al_instance_id]['y_train']
            )

            self.minio_service.save_labels(
                al_instance_id=al_instance_id,
                labels_version=model_id,
                split="test",
                df=self.storage.dataset_dict[al_instance_id]['y_test']
            )

            minio_model_info = self.minio_service.save_model(
                al_instance_id=al_instance_id,
                model_version=model_id,
                model=current_model
            )

            self._log_event(
                al_instance_id=al_instance_id,
                action="model_checkpoint",
                latency_ms=int((time.perf_counter() - start_time) * 1000),
                actor_type="system",
                agent="orchestrator",
                object_id=str(model_id),
                payload={
                    "model_id": model_id,
                    "local_path": model_path,
                    "minio_object": minio_model_info["object"],
                },
                user_id=user_id,
            )

        return model_id
    
    # Logic for deleting an active learning instance
    def delete_instance(self, al_instance_id: int):
        """Delete an instance and all its artifacts. Continues on partial failures."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Delete from in-memory storage (non-critical if missing)
        try:
            del self.storage.al_instances_dict[al_instance_id]
        except KeyError:
            logger.warning(f"Instance {al_instance_id} not in al_instances_dict")
        
        try:
            del self.storage.dataset_dict[al_instance_id]
        except KeyError:
            logger.warning(f"Instance {al_instance_id} not in dataset_dict")
        
        try:
            del self.storage.results_dict[al_instance_id]
        except KeyError:
            logger.warning(f"Instance {al_instance_id} not in results_dict")
        
        try:
            del self.storage.model_paths_dict[al_instance_id]
        except KeyError:
            logger.warning(f"Instance {al_instance_id} not in model_paths_dict")

        # Delete local artifacts (non-critical if missing)
        try:
            self.local_artifacts_store.delete_instance_artifacts(al_instance_id)
        except Exception as e:
            logger.warning(f"Failed to delete local artifacts for instance {al_instance_id}: {e}")

        # Delete from DuckDB (non-critical if missing)
        try:
            self.duckdb_service.delete_instance(al_instance_id)
        except Exception as e:
            logger.warning(f"Failed to delete instance from DuckDB: {e}")

        # Delete from MinIO (non-critical if missing or unavailable)
        if self.minio_service is not None:
            try:
                self.minio_service.delete_instance_objects(al_instance_id)
            except Exception as e:
                logger.warning(f"Failed to delete instance objects from MinIO: {e}")

        # Clean up delegations
        try:
            self.duckdb_service.delete_all_delegations_for_instance(al_instance_id=al_instance_id)
        except Exception as e:
            logger.warning(f"Failed to delete delegations for instance {al_instance_id}: {e}")

    def delegate_instance(
        self,
        *,
        al_instance_id: int,
        delegate_username: str,
        owner_user_id: str,
    ) -> dict:
        """Delegate an AL instance to another user.
        
        Args:
            al_instance_id: The instance to delegate.
            delegate_username: Username of the user to grant access to.
            owner_user_id: UUID of the current user (must be the owner).
            
        Returns:
            Dict with delegate info.
            
        Raises:
            ValueError: If instance not found, user not owner, or delegate user doesn't exist.
        """
        instance = self.storage.al_instances_dict.get(al_instance_id)
        if instance is None:
            raise ValueError(f"Instance {al_instance_id} not found")
        
        if instance.get("user_id") != owner_user_id:
            raise ValueError("Only the instance owner can delegate access")
        
        delegate_user = self.duckdb_service.get_user_by_username(username=delegate_username)
        if delegate_user is None:
            raise ValueError(f"User '{delegate_username}' not found")
        
        delegate_user_id = str(delegate_user["user_id"])
        
        if delegate_user_id == owner_user_id:
            raise ValueError("Cannot delegate to yourself")
        
        self.duckdb_service.delegate_instance(
            al_instance_id=al_instance_id,
            delegate_user_id=delegate_user_id,
            granted_by=owner_user_id,
        )
        
        delegates = self.duckdb_service.get_delegates_for_instance(al_instance_id=al_instance_id)
        for delegate in delegates:
            if delegate["delegate_user_id"] == delegate_user_id:
                return delegate
        
        raise ValueError("Delegation succeeded but failed to retrieve delegate info")

    def revoke_delegation(
        self,
        *,
        al_instance_id: int,
        delegate_username: str,
        owner_user_id: str,
    ) -> None:
        """Revoke a user's delegated access to an instance.
        
        Args:
            al_instance_id: The instance to revoke access from.
            delegate_username: Username of the user to revoke access from.
            owner_user_id: UUID of the current user (must be the owner).
            
        Raises:
            ValueError: If instance not found or user not owner.
        """
        instance = self.storage.al_instances_dict.get(al_instance_id)
        if instance is None:
            raise ValueError(f"Instance {al_instance_id} not found")
        
        if instance.get("user_id") != owner_user_id:
            raise ValueError("Only the instance owner can revoke delegation")
        
        delegate_user = self.duckdb_service.get_user_by_username(username=delegate_username)
        if delegate_user is None:
            raise ValueError(f"User '{delegate_username}' not found")
        
        delegate_user_id = str(delegate_user["user_id"])
        
        self.duckdb_service.revoke_delegation(
            al_instance_id=al_instance_id,
            delegate_user_id=delegate_user_id,
        )

    def get_delegates(
        self,
        *,
        al_instance_id: int,
        owner_user_id: str,
    ) -> list[dict]:
        """Get all delegates for an instance.
        
        Args:
            al_instance_id: The instance to query.
            owner_user_id: UUID of the current user (must be the owner).
            
        Returns:
            List of delegate dicts.
            
        Raises:
            ValueError: If instance not found or user not owner.
        """
        instance = self.storage.al_instances_dict.get(al_instance_id)
        if instance is None:
            raise ValueError(f"Instance {al_instance_id} not found")
        
        if instance.get("user_id") != owner_user_id:
            raise ValueError("Only the instance owner can view delegates")
        
        return self.duckdb_service.get_delegates_for_instance(al_instance_id=al_instance_id)

    def export_instance(self, al_instance_id: int) -> tuple[BytesIO, str]:
        """Build a downloadable ZIP containing a raw JSON dump of all DuckDB
        tables relevant to ``al_instance_id``.

        The archive contains a ``manifest.json`` and one ``duckdb/<table>.json``
        file per table (a JSON array of row objects). Instance-scoped tables are
        filtered to the requested instance; the full ``tickets`` table and the
        instance-relevant ``users`` (with ``password`` omitted) are included.
        Ground-truth labels from instance 0 are provided as a separate
        ``ground_truth_labels.json`` and are not merged with ``labels``.
        MinIO artifacts are intentionally excluded.

        Args:
            al_instance_id: The instance to export.

        Returns:
            A ``(buffer, filename)`` tuple where ``buffer`` is a ``BytesIO``
            positioned at offset 0 containing the ZIP, and ``filename`` is a
            suggested download name.

        Raises:
            ValueError: If DuckDB persistence is not configured.
        """
        if self.duckdb_service is None:
            raise ValueError("DuckDB persistence is not configured; export unavailable.")

        rows_by_table = self.duckdb_service.export_instance_rows(al_instance_id)

        manifest = {
            "schema_version": 1,
            "al_instance_id": al_instance_id,
            "exported_at": datetime.now().isoformat(),
            "tables": {table: len(rows) for table, rows in rows_by_table.items()},
        }

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, default=str, indent=2))
            for table_name, rows in rows_by_table.items():
                zf.writestr(f"duckdb/{table_name}.json", json.dumps(rows, default=str, indent=2))
        buffer.seek(0)

        filename = f"export_al_{al_instance_id}_{datetime.now().strftime('%Y%m%dT%H%M%S')}.zip"
        return buffer, filename
