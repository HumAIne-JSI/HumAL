from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from .connection import connect
from .schema import init_database

from datetime import datetime

from app.config.config import GROUND_TRUTH_AL_INSTANCE_ID, TEAM_NAME


@dataclass(frozen=True)
class DuckDbPersistenceService:
    db_path: Optional[str | Path] = None

    def __post_init__(self) -> None:
        init_database(self.db_path)

    @staticmethod
    def _json_dumps(value: Any) -> str:
        return json.dumps(value)

    @staticmethod
    def _json_loads(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value

    # --- Users ---
    def upsert_user(
        self,
        *,
        user_id: str | uuid.UUID | None = None,
        username: str,
        password: str,
    ) -> uuid.UUID:
        """Insert or replace a user row.

        If user_id is None, a new random UUID (uuid4) is generated.
        """
        user_uuid = uuid.UUID(str(user_id)) if user_id is not None else uuid.uuid4()
        with connect(self.db_path) as conn:
            # Delete existing user if present to avoid unique constraint issues
            conn.execute("DELETE FROM users WHERE user_id = ?", [str(user_uuid)])
            conn.execute(
                """
                INSERT INTO users (user_id, username, password)
                VALUES (?, ?, ?)
                """,
                [str(user_uuid), username, password],
            )
        return user_uuid

    def get_user(self, *, user_id: str | uuid.UUID) -> Optional[Dict[str, Any]]:
        user_uuid = uuid.UUID(str(user_id))
        with connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT user_id, username, password, created_at
                FROM users
                WHERE user_id = ?
                """,
                [str(user_uuid)],
            ).fetchone()

        if not row:
            return None

        return {
            "user_id": str(row[0]),
            "username": row[1],
            "password": row[2],
            "created_at": row[3],
        }

    def get_user_by_username(self, *, username: str) -> Optional[Dict[str, Any]]:
        with connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT user_id, username, password, created_at
                FROM users
                WHERE username = ?
                """,
                [username],
            ).fetchone()

        if not row:
            return None

        return {
            "user_id": str(row[0]),
            "username": row[1],
            "password": row[2],
            "created_at": row[3],
        }

    # --- AL instances ---
    def save_al_instance(self, al_instance_id: int, instance_data: Dict[str, Any]) -> None:
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO al_instances
                (al_instance_id, model_name, query_strategy, classes, train_data_path, test_data_path)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    al_instance_id,
                    instance_data.get("model_name"),
                    instance_data.get("qs"),
                    instance_data.get("classes"),
                    instance_data.get("train_data_path"),
                    instance_data.get("test_data_path")
                ],
            )

    def load_al_instance(self, al_instance_id: int) -> Optional[Dict[str, Any]]:
        with connect(self.db_path) as conn:
            result = conn.execute(
                """
                SELECT model_name, query_strategy, classes, train_data_path, test_data_path
                FROM al_instances
                WHERE al_instance_id = ?
                """,
                [al_instance_id],
            ).fetchone()

        if not result:
            return None

        return {
            "model_name": result[0],
            "qs": result[1],
            "classes": result[2],
            "train_data_path": result[3],
            "test_data_path": result[4],
        }

    def get_all_instances(self) -> Dict[int, Dict[str, Any]]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT al_instance_id, model_name, query_strategy, classes, train_data_path, test_data_path
                FROM al_instances
                ORDER BY al_instance_id
                """
            ).fetchall()

        instances: Dict[int, Dict[str, Any]] = {}
        for row in rows:
            instances[int(row[0])] = {
                "model_name": row[1],
                "qs": row[2],
                "classes": row[3],
                "train_data_path": row[4],
                "test_data_path": row[5],
            }
        return instances

    # --- Dataset Configs ---
    def save_dataset_config(
        self,
        *,
        al_instance_id: int,
        dataset_name: str,
        version: str,
        dataset_format: str,
        id_field: str,
        splits: Any,
        fields: Any,
        task: Any,
        features: Any,
        preprocessing: Optional[Any] = None,
    ) -> None:
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO dataset_configs
                (
                    al_instance_id,
                    dataset_name,
                    version,
                    dataset_format,
                    id_field,
                    splits,
                    fields,
                    task,
                    features,
                    preprocessing,
                    config
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    al_instance_id,
                    dataset_name,
                    version,
                    dataset_format,
                    id_field,
                    self._json_dumps(splits),
                    self._json_dumps(fields),
                    self._json_dumps(task),
                    self._json_dumps(features),
                    self._json_dumps(preprocessing) if preprocessing is not None else None,
                ],
            )

    def load_dataset_config(
        self,
        *,
        al_instance_id: int,
        dataset_name: str,
        version: str = "1.0",
    ) -> Optional[Dict[str, Any]]:
        with connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    al_instance_id,
                    dataset_name,
                    version,
                    dataset_format,
                    id_field,
                    splits,
                    fields,
                    task,
                    features,
                    preprocessing,
                    created_at
                FROM dataset_configs
                WHERE al_instance_id = ? AND dataset_name = ? AND version = ?
                """,
                [al_instance_id, dataset_name, version],
            ).fetchone()

        if not row:
            return None

        return {
            "al_instance_id": row[0],
            "dataset_name": row[1],
            "version": row[2],
            "dataset_format": row[3],
            "id_field": row[4],
            "splits": self._json_loads(row[5]),
            "fields": self._json_loads(row[6]),
            "task": self._json_loads(row[7]),
            "features": self._json_loads(row[8]),
            "preprocessing": self._json_loads(row[9]),
            "created_at": row[11],
        }

    

    def delete_dataset_config(self, *, al_instance_id: int, dataset_name: str, version: str) -> bool:
        with connect(self.db_path) as conn:
            result = conn.execute(
                """
                DELETE FROM dataset_configs
                WHERE al_instance_id = ? AND dataset_name = ? AND version = ?
                """,
                [al_instance_id, dataset_name, version],
            )
        return result.rowcount > 0

 

    # --- Labels ---
    def save_labels(self, al_instance_id: int, user_id: str | uuid.UUID, labels_dict: Dict[str, Any], split: str, timestamp: Optional[datetime] = None) -> int:
        """Persist non-null labels for a user/instance. Returns count saved."""
        user_uuid = uuid.UUID(str(user_id))

        if not labels_dict:
            return 0

        saved = 0
        with connect(self.db_path) as conn:
            for ref, label in labels_dict.items():
                if pd.isna(label):
                    continue

                conn.execute(
                    """
                    INSERT OR REPLACE INTO labels (al_instance_id, user_id, ref, label, split, labeled_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [al_instance_id, str(user_uuid), str(ref), str(label), split, timestamp],
                )
                saved += 1

        return saved

    def load_labels(self, al_instance_id: int, user_id: Optional[str | uuid.UUID] = None, split: Optional[str] = None) -> pd.Series:
        """Load labels for an instance, optionally filtered by user and/or split."""
        query = "SELECT ref, label, labeled_at FROM labels WHERE al_instance_id IN (?, ?)"
        params = [al_instance_id, GROUND_TRUTH_AL_INSTANCE_ID]
        
        if user_id is not None:
            user_uuid = uuid.UUID(str(user_id))
            query += " AND user_id = ?"
            params.append(str(user_uuid))
        
        if split is not None:
            if split not in ("train", "test"):
                raise ValueError("split must be 'train' or 'test'")
            query += " AND split = ?"
            params.append(split)
        
        with connect(self.db_path) as conn:
            df = conn.execute(query, params).df()

        if df.empty:
            return pd.Series(dtype=object)
        
        df = self._keep_majority_or_latest_label(df)

        df["ref"] = df["ref"].astype(str)
        df = df.rename(columns={"label": TEAM_NAME})
        return df.set_index("ref")[TEAM_NAME]
    
    def _keep_majority_or_latest_label(self, labels: pd.DataFrame) -> pd.DataFrame:
        """Helper to resolve label conflicts by keeping the majority label or latest if tie."""

        if labels is None or labels.empty:
            return pd.DataFrame(columns=["ref", "label"])

        if "ref" in labels.columns:
            grouped = labels.groupby("ref", sort=False)
        else:
            raise NameError("Labels DataFrame must contain 'ref' column")

        rows = []
        for ref, ref_rows in grouped:
            if isinstance(ref_rows, pd.Series):
                ref_rows = ref_rows.to_frame().T

            label_counts = ref_rows["label"].value_counts()
            max_count = label_counts.max()
            most_frequent_labels = label_counts[label_counts == max_count].index.tolist()

            if len(most_frequent_labels) == 1:
                chosen_label = most_frequent_labels[0]
            else:
                candidate_rows = ref_rows[ref_rows["label"].isin(most_frequent_labels)]
                if "labeled_at" in candidate_rows.columns:
                    candidate_rows = candidate_rows.sort_values("labeled_at", ascending=False)
                else:
                    raise NameError("Labels DataFrame must contain 'labeled_at' column for tie-breaking")
                chosen_label = candidate_rows.iloc[0]["label"]

            rows.append({"ref": ref, "label": chosen_label})

        return pd.DataFrame(rows, columns=["ref", "label"])


    # --- Metrics ---
    def save_metrics(
        self,
        al_instance_id: int,
        *,
        iteration_id: Optional[int] = None,
        f1_score: Optional[float] = None,
        mean_entropy: Optional[float] = None,
        num_labeled: Optional[int] = None,
    ) -> int:
        with connect(self.db_path) as conn:
            if iteration_id is None:
                # Get the next iteration_id for this al_instance_id
                result = conn.execute(
                    """
                    SELECT COALESCE(MAX(iteration_id), 0) + 1
                    FROM metrics
                    WHERE al_instance_id = ?
                    """,
                    [al_instance_id],
                ).fetchone()
                iteration_id = result[0]

            conn.execute(
                """
                INSERT OR REPLACE INTO metrics
                (al_instance_id, iteration_id, f1_score, mean_entropy, num_labeled)
                VALUES (?, ?, ?, ?, ?)
                """,
                [al_instance_id, iteration_id, f1_score, mean_entropy, num_labeled],
            )
        
        return iteration_id

    def load_metrics(self, al_instance_id: int, iteration_id: Optional[int] = None) -> Dict[str, any]:
        with connect(self.db_path) as conn:
            if iteration_id is None:
                # Load the latest iteration
                row = conn.execute(
                    """
                    SELECT iteration_id, f1_score, mean_entropy, num_labeled
                    FROM metrics
                    WHERE al_instance_id = ?
                    ORDER BY iteration_id DESC
                    LIMIT 1
                    """,
                    [al_instance_id],
                ).fetchone()
            else:
                # Load specific iteration
                row = conn.execute(
                    """
                    SELECT iteration_id, f1_score, mean_entropy, num_labeled
                    FROM metrics
                    WHERE al_instance_id = ? AND iteration_id = ?
                    """,
                    [al_instance_id, iteration_id],
                ).fetchone()

        if not row:
            return {
                "iteration_id": None,
                "f1_score": None,
                "mean_entropy": None,
                "num_labeled": None,
            }

        return {
            "iteration_id": row[0],
            "f1_score": row[1],
            "mean_entropy": row[2],
            "num_labeled": row[3],
        }

    def load_all_metrics(self, al_instance_id: int) -> list[Dict[str, any]]:
        """Load all metrics iterations for an AL instance."""
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT iteration_id, f1_score, mean_entropy, num_labeled
                FROM metrics
                WHERE al_instance_id = ?
                ORDER BY iteration_id ASC
                """,
                [al_instance_id],
            ).fetchall()

        return [
            {
                "iteration_id": row[0],
                "f1_score": row[1],
                "mean_entropy": row[2],
                "num_labeled": row[3],
            }
            for row in rows
        ]

    # --- Events ---
    def log_event(
        self,
        *,
        al_instance_id: Optional[int] = None,
        user_id: Optional[str | uuid.UUID] = None,
        action: str,
        latency_ms: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        resolved_user_id = uuid.UUID(str(user_id)) if user_id is not None else None

        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO al_events (al_instance_id, user_id, action, latency_ms, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    al_instance_id,
                    str(resolved_user_id) if resolved_user_id is not None else None,
                    action,
                    latency_ms,
                    json.dumps(payload) if payload is not None else None,
                ],
            )

    

    # --- Deletes ---
    def delete_instance(self, al_instance_id: int) -> None:
        if al_instance_id==GROUND_TRUTH_AL_INSTANCE_ID:
            raise ValueError("Cannot delete ground truth AL instance")
        with connect(self.db_path) as conn:
            conn.execute("DELETE FROM al_events WHERE al_instance_id = ?", [al_instance_id])
            conn.execute("DELETE FROM labels WHERE al_instance_id = ?", [al_instance_id])
            conn.execute("DELETE FROM metrics WHERE al_instance_id = ?", [al_instance_id])
            conn.execute("DELETE FROM dataset_configs WHERE al_instance_id = ?", [al_instance_id])
            conn.execute("DELETE FROM al_instances WHERE al_instance_id = ?", [al_instance_id])
