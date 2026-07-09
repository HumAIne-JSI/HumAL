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

from app.config.config import GROUND_TRUTH_AL_INSTANCE_ID, SYSTEM_USER_ID, TEAM_NAME


def _deserialize_varchar_array(value: Any) -> Optional[list[str]]:
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [value]
        except json.JSONDecodeError:
            return [value]
    return [str(value)]


def _deserialize_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _json_value_is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (dict, list, str, tuple, set)):
        return len(value) > 0
    return True


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    raise TypeError(f"Object of type {value.__class__.__name__} is not JSON serializable")


@dataclass(frozen=True)
class DuckDbPersistenceService:
    db_path: Optional[str | Path] = None

    def __post_init__(self) -> None:
        init_database(self.db_path)

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
    def get_next_instance_id(self) -> int:
        """Return the next AL instance ID from the persistent DuckDB sequence.

        Draws from ``al_instance_id_seq`` so the ID is monotonic and never
        reused across deletes or pod restarts. The reserved ground-truth ID
        (``GROUND_TRUTH_AL_INSTANCE_ID == 0``) is skipped defensively.

        The ``nextval`` call is wrapped in an explicit transaction so the
        advanced sequence value is committed to the file before the connection
        closes; without this, DuckDB's autocommit mode would not persist the
        counter across reconnections.
        """
        with connect(self.db_path) as conn:
            while True:
                conn.execute("BEGIN")
                value = conn.execute("SELECT nextval('al_instance_id_seq')").fetchone()[0]
                conn.execute("COMMIT")
                if int(value) != GROUND_TRUTH_AL_INSTANCE_ID:
                    return int(value)

    def save_al_instance(self, al_instance_id: int, instance_data: Dict[str, Any], user_id: Optional[str | uuid.UUID] = None) -> None:
        resolved_user_id = uuid.UUID(str(user_id)) if user_id is not None else uuid.UUID(SYSTEM_USER_ID)
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO al_instances
                (al_instance_id, model_name, query_strategy, classes, user_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    al_instance_id,
                    instance_data.get("model_name"),
                    instance_data.get("qs"),
                    instance_data.get("classes"),
                    str(resolved_user_id),
                ],
            )

    def load_al_instance(self, al_instance_id: int) -> Optional[Dict[str, Any]]:
        with connect(self.db_path) as conn:
            result = conn.execute(
                """
                SELECT model_name, query_strategy, classes, user_id, created_at
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
            "user_id": str(result[3]) if result[3] is not None else None,
            "created_at": result[4],
        }

    def get_all_instances(
        self, user_id: Optional[str | uuid.UUID] = None
    ) -> Dict[int, Dict[str, Any]]:
        query = """
            SELECT al_instance_id, model_name, query_strategy, classes, user_id
            FROM al_instances
        """
        params = []
        if user_id is not None:
            query += " WHERE user_id = ?"
            params.append(str(uuid.UUID(str(user_id))))
        query += " ORDER BY al_instance_id"
        with connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()

        instances: Dict[int, Dict[str, Any]] = {}
        for row in rows:
            instances[int(row[0])] = {
                "model_name": row[1],
                "qs": row[2],
                "classes": row[3],
                "user_id": str(row[4]) if row[4] is not None else None,
            }
        return instances

    # --- Tickets ---
    def upsert_tickets_df(
        self,
        tickets_df: pd.DataFrame,
        *,
        split: str,
        dataset_timestamp: Optional[datetime] = None,
    ) -> int:
        """Upsert ticket rows from a dataframe.

        Requires column: Ref
        Optional columns will be mapped to the schema.

        Args:
            tickets_df: DataFrame with ticket data
            split: 'train' or 'test'
            dataset_timestamp: Optional timestamp for the dataset
        """
        if tickets_df is None or tickets_df.empty:
            return 0

        if "Ref" not in tickets_df.columns:
            raise ValueError("tickets_df must contain 'Ref' column")

        # Map DataFrame columns to schema columns
        column_mapping = {
            "Ref": "ref",
            "Service subcategory->Name": "service_subcategory_name",
            "Service->Name": "service_name",
            "Request Type": "request_type",
            "Last team ID->Name": "last_team_id_name",
            "Title_anon": "title_anon",
            "Description_anon": "description_anon",
            "Public_log_anon": "public_log_anon",
        }

        df = tickets_df.copy()
        
        # Rename columns that exist in the DataFrame
        df = df.rename(columns=column_mapping)

        # Add split and dataset_timestamp
        df["split"] = split
        df["dataset_timestamp"] = dataset_timestamp

        # Ensure all schema columns exist
        schema_cols = [
            "ref",
            "service_subcategory_name",
            "service_name",
            "request_type",
            "last_team_id_name",
            "title_anon",
            "description_anon",
            "public_log_anon",
            "split",
            "dataset_timestamp",
        ]

        for col in schema_cols:
            if col not in df.columns:
                df[col] = None

        df = df[schema_cols]

        with connect(self.db_path) as conn:
            conn.register("_tickets_df", df)
            conn.execute(
                """
                INSERT OR REPLACE INTO tickets
                SELECT * FROM _tickets_df
                """
            )
            conn.unregister("_tickets_df")

        return int(len(df))

    def load_tickets(self, split: str) -> pd.DataFrame:
        """Load tickets for a given split ('train' or 'test').
        
        Args:
            split: 'train' or 'test'
            
        Returns:
            DataFrame with all tickets for the specified split
        """
        if split not in ('train', 'test'):
            raise ValueError("split must be 'train' or 'test'")
        
        with connect(self.db_path) as conn:
            df = conn.execute(
                """
                SELECT ref, service_subcategory_name, service_name, request_type, 
                       last_team_id_name, title_anon, description_anon, public_log_anon, 
                       split, dataset_timestamp
                FROM tickets
                WHERE split = ?
                """,
                [split],
            ).df()
        
        df = df.rename(columns={
            "ref": "Ref",
            "service_subcategory_name": "Service subcategory->Name",
            "service_name": "Service->Name",
            "request_type": "Request Type",
            "last_team_id_name": "Last team ID->Name",
            "title_anon": "Title_anon",
            "description_anon": "Description_anon",
            "public_log_anon": "Public_log_anon"})
        
        df['Ref'] = df['Ref'].astype(str)
        
        return df
    
    def load_tickets_by_ref(self, ref_list: list[str]) -> Optional[pd.DataFrame]:
        """Load tickets for a given list of refs."""
        if not ref_list:
            return None
        
        with connect(self.db_path) as conn:
            df = conn.execute(
                f"""
                SELECT ref, service_subcategory_name, service_name, request_type, 
                       last_team_id_name, title_anon, description_anon, public_log_anon, 
                       split, dataset_timestamp
                FROM tickets
                WHERE ref IN ({','.join(['?']*len(ref_list))})
                """,
                ref_list,
            ).df()
        
        df = df.rename(columns={
            "ref": "Ref",
            "service_subcategory_name": "Service subcategory->Name",
            "service_name": "Service->Name",
            "request_type": "Request Type",
            "last_team_id_name": "Last team ID->Name",
            "title_anon": "Title_anon",
            "description_anon": "Description_anon",
            "public_log_anon": "Public_log_anon"})
        
        df['Ref'] = df['Ref'].astype(str)

        return df
    
    def get_ticket_counts_by_split(self) -> Dict[str, int]:
        """Get counts of tickets by split."""
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT split, COUNT(*) as count
                FROM tickets
                GROUP BY split
                """
            ).fetchall()

        return {row[0]: row[1] for row in rows}
    
    def get_latest_dataset_timestamp(self, split) -> Optional[str]:
        """Get the latest dataset timestamp for a given split."""
        with connect(self.db_path) as conn:
            result = conn.execute(
                """
                SELECT MAX(dataset_timestamp)
                FROM tickets
                WHERE split = ?
                """,
                [split],
            ).fetchone()

        return result[0] if result and result[0] is not None else None

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
                    VALUES (?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
                    """,
                    [al_instance_id, str(user_uuid), str(ref), str(label), split, timestamp],
                )
                saved += 1

        return saved

    def upsert_label_decision(
        self,
        *,
        al_instance_id: int,
        ref: str,
        user_id: str | uuid.UUID | None = None,
        label: Optional[str] = None,
        labeled_at: Optional[datetime] = None,
        model_prediction: Optional[str] = None,
        latency_ms: Optional[int] = None,
        most_helpful_feature: Optional[str] = None,
        is_tired: Optional[bool] = None,
        is_difficult: Optional[bool] = None,
        i_dont_know: Optional[bool] = None,
        xai_result: Optional[Any] = None,
        similar_tickets: Optional[Any] = None,
    ) -> None:
        """Insert or update a staged label-decision record without clearing existing fields."""
        resolved_user_id = uuid.UUID(str(user_id)) if user_id is not None else None

        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO label_decisions (
                    al_instance_id,
                    ref,
                    user_id,
                    label,
                    labeled_at,
                    model_prediction,
                    latency_ms,
                    most_helpful_feature,
                    is_tired,
                    is_difficult,
                    i_dont_know,
                    xai_result,
                    similar_tickets
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (al_instance_id, ref) DO UPDATE SET
                    user_id = COALESCE(EXCLUDED.user_id, label_decisions.user_id),
                    label = COALESCE(EXCLUDED.label, label_decisions.label),
                    labeled_at = COALESCE(EXCLUDED.labeled_at, label_decisions.labeled_at),
                    model_prediction = COALESCE(EXCLUDED.model_prediction, label_decisions.model_prediction),
                    latency_ms = COALESCE(EXCLUDED.latency_ms, label_decisions.latency_ms),
                    most_helpful_feature = COALESCE(EXCLUDED.most_helpful_feature, label_decisions.most_helpful_feature),
                    is_tired = COALESCE(EXCLUDED.is_tired, label_decisions.is_tired),
                    is_difficult = COALESCE(EXCLUDED.is_difficult, label_decisions.is_difficult),
                    i_dont_know = COALESCE(EXCLUDED.i_dont_know, label_decisions.i_dont_know),
                    xai_result = COALESCE(EXCLUDED.xai_result, label_decisions.xai_result),
                    similar_tickets = COALESCE(EXCLUDED.similar_tickets, label_decisions.similar_tickets)
                """,
                [
                    al_instance_id,
                    ref,
                    str(resolved_user_id) if resolved_user_id is not None else None,
                    label,
                    labeled_at,
                    model_prediction,
                    latency_ms,
                    most_helpful_feature,
                    is_tired,
                    is_difficult,
                    i_dont_know,
                    json.dumps(xai_result, default=_json_default) if xai_result is not None else None,
                    json.dumps(similar_tickets, default=_json_default) if similar_tickets is not None else None,
                ],
            )

    def get_label_decision(self, *, al_instance_id: int, ref: str) -> Optional[Dict[str, Any]]:
        """Load a staged label-decision row for inspection or tests."""
        with connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT al_instance_id, ref, user_id, label, labeled_at, model_prediction,
                       latency_ms, most_helpful_feature, is_tired, is_difficult, i_dont_know,
                       skipped_for_training, xai_result, similar_tickets
                FROM label_decisions
                WHERE al_instance_id = ? AND ref = ?
                """,
                [al_instance_id, ref],
            ).fetchone()

        if not row:
            return None

        return {
            "al_instance_id": row[0],
            "ref": row[1],
            "user_id": str(row[2]) if row[2] is not None else None,
            "label": row[3],
            "labeled_at": row[4],
            "model_prediction": row[5],
            "latency_ms": row[6],
            "most_helpful_feature": row[7],
            "is_tired": row[8],
            "is_difficult": row[9],
            "i_dont_know": row[10],
            "skipped_for_training": row[11],
            "xai_result": _deserialize_json(row[12]),
            "similar_tickets": _deserialize_json(row[13]),
        }

    def load_label_decisions_with_xai(self, *, al_instance_id: int) -> list[Dict[str, Any]]:
        """Load label-decision rows that already contain XAI history or stored similar tickets.

        Args:
            al_instance_id: Active learning instance identifier to filter by.

        Returns:
            A list of dictionaries containing ref, xai_result, similar_tickets,
            model_prediction, most_helpful_feature, and label when present.
        """
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT ref, label, xai_result, similar_tickets, model_prediction, most_helpful_feature
                FROM label_decisions
                WHERE al_instance_id = ?
                                    AND label IS NOT NULL
                  AND (xai_result IS NOT NULL OR similar_tickets IS NOT NULL)
                """,
                [al_instance_id],
            ).fetchall()

        results: list[Dict[str, Any]] = []
        for row in rows:
            xai_result = _deserialize_json(row[2])
            similar_tickets = _deserialize_json(row[3])

            if not (_json_value_is_non_empty(xai_result) or _json_value_is_non_empty(similar_tickets)):
                continue

            results.append(
                {
                    "ref": str(row[0]),
                    "label": row[1],
                    "xai_result": xai_result,
                    "similar_tickets": similar_tickets,
                    "model_prediction": row[4],
                    "most_helpful_feature": row[5],
                }
            )

        return results

    def load_skipped_refs(self, *, al_instance_id: int) -> list[str]:
        """Return refs of label_decisions flagged skipped_for_training for an instance."""
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT ref FROM label_decisions WHERE al_instance_id = ? AND skipped_for_training = TRUE",
                [al_instance_id],
            ).fetchall()
        return [str(r[0]) for r in rows]

    def load_labels(self, al_instance_id: int, user_id: Optional[str | uuid.UUID] = None, split: Optional[str] = None) -> pd.Series:
        """Load labels for an instance, optionally filtered by user and/or split."""
        query = "SELECT ref, label, labeled_at FROM labels WHERE al_instance_id IN (?, ?)"
        params: list[Any] = [al_instance_id, GROUND_TRUTH_AL_INSTANCE_ID]
        
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

    # --- Model paths ---
    def save_model_path(self, al_instance_id: int, model_id: int, path_to_model: str) -> None:
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO model_paths (al_instance_id, model_id, path_to_model)
                VALUES (?, ?, ?)
                """,
                [al_instance_id, model_id, path_to_model],
            )

    def load_model_paths(self, al_instance_id: int) -> Dict[int, str]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT model_id, path_to_model
                FROM model_paths
                WHERE al_instance_id = ?
                ORDER BY model_id
                """,
                [al_instance_id],
            ).fetchall()

        return {int(model_id): str(path) for (model_id, path) in rows}

    # --- Metrics ---
    def save_metrics(
        self,
        al_instance_id: int,
        *,
        iteration_id: Optional[int] = None,
        f1_score: Optional[float] = None,
        mean_entropy: Optional[float] = None,
        num_labeled: Optional[int] = None,
        accuracy: Optional[float] = None,
        precision_macro: Optional[float] = None,
        precision_weighted: Optional[float] = None,
        recall_macro: Optional[float] = None,
        recall_weighted: Optional[float] = None,
        f1_per_class: Optional[list[float]] = None,
        confusion_matrix: Optional[list[list[int]]] = None,
        roc_auc_ovr_macro: Optional[float] = None,
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
                iteration_id = int(result[0]) if result is not None else 1

            conn.execute(
                """
                INSERT OR REPLACE INTO metrics
                (al_instance_id, iteration_id, f1_score, mean_entropy, num_labeled,
                 accuracy, precision_macro, precision_weighted, recall_macro, recall_weighted,
                 f1_per_class, confusion_matrix, roc_auc_ovr_macro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    al_instance_id, iteration_id, f1_score, mean_entropy, num_labeled,
                    accuracy, precision_macro, precision_weighted, recall_macro, recall_weighted,
                    json.dumps(f1_per_class) if f1_per_class is not None else None,
                    json.dumps(confusion_matrix) if confusion_matrix is not None else None,
                    roc_auc_ovr_macro,
                ],
            )

        return int(iteration_id)

    def load_metrics(self, al_instance_id: int, iteration_id: Optional[int] = None) -> Dict[str, Any]:
        with connect(self.db_path) as conn:
            if iteration_id is None:
                # Load the latest iteration
                row = conn.execute(
                    """
                    SELECT iteration_id, f1_score, mean_entropy, num_labeled,
                           accuracy, precision_macro, precision_weighted, recall_macro,
                           recall_weighted, f1_per_class, confusion_matrix, roc_auc_ovr_macro
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
                    SELECT iteration_id, f1_score, mean_entropy, num_labeled,
                           accuracy, precision_macro, precision_weighted, recall_macro,
                           recall_weighted, f1_per_class, confusion_matrix, roc_auc_ovr_macro
                    FROM metrics
                    WHERE al_instance_id = ? AND iteration_id = ?
                    """,
                    [al_instance_id, iteration_id],
                ).fetchone()

        if not row:
            return {
                "iteration_id": None, "f1_score": None, "mean_entropy": None, "num_labeled": None,
                "accuracy": None, "precision_macro": None, "precision_weighted": None,
                "recall_macro": None, "recall_weighted": None,
                "f1_per_class": None, "confusion_matrix": None, "roc_auc_ovr_macro": None,
            }

        return {
            "iteration_id": row[0], "f1_score": row[1], "mean_entropy": row[2], "num_labeled": row[3],
            "accuracy": row[4], "precision_macro": row[5], "precision_weighted": row[6],
            "recall_macro": row[7], "recall_weighted": row[8],
            "f1_per_class": json.loads(row[9]) if row[9] is not None else None,
            "confusion_matrix": json.loads(row[10]) if row[10] is not None else None,
            "roc_auc_ovr_macro": row[11],
        }

    def load_all_metrics(self, al_instance_id: int) -> list[Dict[str, Any]]:
        """Load all metrics iterations for an AL instance."""
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT iteration_id, f1_score, mean_entropy, num_labeled,
                       accuracy, precision_macro, precision_weighted, recall_macro,
                       recall_weighted, f1_per_class, confusion_matrix, roc_auc_ovr_macro
                FROM metrics
                WHERE al_instance_id = ?
                ORDER BY iteration_id ASC
                """,
                [al_instance_id],
            ).fetchall()

        return [
            {
                "iteration_id": row[0], "f1_score": row[1], "mean_entropy": row[2], "num_labeled": row[3],
                "accuracy": row[4], "precision_macro": row[5], "precision_weighted": row[6],
                "recall_macro": row[7], "recall_weighted": row[8],
                "f1_per_class": json.loads(row[9]) if row[9] is not None else None,
                "confusion_matrix": json.loads(row[10]) if row[10] is not None else None,
                "roc_auc_ovr_macro": row[11],
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
        actor_type: Optional[str] = None,
        agent: Optional[str] = None,
        object_id: Optional[str] = None,
        duration_s: Optional[float] = None,
        correct: Optional[bool] = None,
        ai_suggested: Optional[str] = None,
    ) -> None:
        resolved_user_id = uuid.UUID(str(user_id)) if user_id is not None else None

        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO al_events (al_instance_id, user_id, action, latency_ms, payload, actor_type, agent, object_id, duration_s, correct, ai_suggested)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    al_instance_id,
                    str(resolved_user_id) if resolved_user_id is not None else None,
                    action,
                    latency_ms,
                    json.dumps(payload, default=_json_default) if payload is not None else None,
                    actor_type,
                    agent,
                    object_id,
                    duration_s,
                    correct,
                    ai_suggested,
                ],
            )

    def get_al_events(
        self,
        al_instance_id: int,
        since_timestamp: Optional[datetime] = None,
        actions: Optional[list[str]] = None,
        limit: Optional[int] = None,
    ) -> list[Dict[str, Any]]:
        query = [
            "SELECT timestamp, user_id, action, latency_ms, payload, actor_type, agent, object_id, duration_s, correct, ai_suggested",
            "FROM al_events",
            "WHERE al_instance_id = ?",
        ]
        params: list[Any] = [al_instance_id]

        if since_timestamp is not None:
            query.append("AND timestamp > ?")
            params.append(since_timestamp)

        if actions:
            placeholders = ", ".join(["?"] * len(actions))
            query.append(f"AND action IN ({placeholders})")
            params.extend(actions)

        query.append("ORDER BY timestamp ASC")

        if limit is not None:
            query.append("LIMIT ?")
            params.append(limit)

        with connect(self.db_path) as conn:
            rows = conn.execute("\n".join(query), params).fetchall()

        return [
            {
                "timestamp": row[0],
                "user_id": str(row[1]) if row[1] is not None else None,
                "action": row[2],
                "latency_ms": row[3],
                "payload": _deserialize_json(row[4]),
                "actor_type": row[5],
                "agent": row[6],
                "object_id": row[7],
                "duration_s": row[8],
                "correct": row[9],
                "ai_suggested": row[10],
            }
            for row in rows
        ]

    def get_last_benchmark_export(self, al_instance_id: int) -> Optional[datetime]:
        with connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT MAX(timestamp)
                FROM al_events
                WHERE al_instance_id = ? AND action = ?
                """,
                [al_instance_id, "benchmark_export"],
            ).fetchone()

        return row[0] if row and row[0] is not None else None

    def count_label_events_since(
        self,
        al_instance_id: int,
        since_timestamp: Optional[datetime],
    ) -> int:
        query = [
            "SELECT COUNT(*)",
            "FROM al_events",
            "WHERE al_instance_id = ?",
            "AND action IN (?, ?)",
        ]
        params: list[Any] = [al_instance_id, "confirm_label", "override_label"]

        if since_timestamp is not None:
            query.append("AND timestamp > ?")
            params.append(since_timestamp)

        with connect(self.db_path) as conn:
            row = conn.execute("\n".join(query), params).fetchone()

        if row is None:
            return 0

        return int(row[0] or 0)

    # --- XAI Jobs ---
    def create_xai_job(
            self, 
            al_instance_id: int, 
            job_id: uuid.UUID, 
            model_id: int, 
            ticket_ref_or_sha: str, 
            request_ticket_location: str, 
            request_model_location: str, 
            request_preprocessor_location: Optional[str],
            request_one_hot_encoder_location: Optional[str],
            request_raw_tickets_locations: list[str],
            status: str = "queued",
            user_id: Optional[str | uuid.UUID] = None,
            ) -> None:

        """Create a new XAI job entry in the database."""
        import json
        resolved_user_id = uuid.UUID(str(user_id)) if user_id is not None else None
        
        # Convert Python list to JSON string for DuckDB (arrays stored as JSON strings)
        request_raw_tickets_locations_serialized = json.dumps(request_raw_tickets_locations)
        
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO xai_jobs 
                (job_id, al_instance_id, user_id, model_id, ticket_ref_or_sha, status, request_ticket_location, 
                 request_model_location, request_preprocessor_location, request_one_hot_encoder_location, request_raw_tickets_locations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [str(job_id), al_instance_id, str(resolved_user_id) if resolved_user_id is not None else None, model_id, ticket_ref_or_sha, status, request_ticket_location,
                 request_model_location, request_preprocessor_location, request_one_hot_encoder_location, request_raw_tickets_locations_serialized]
            )
            
    def update_xai_job_status(self, job_id: uuid.UUID, status: str, result_location: Optional[str] = None, result_file_names: Optional[list[str]] = None) -> None:

        """Update the status and optionally result location of an existing XAI job."""
        import json
        
        # Convert Python list to JSON string for DuckDB (arrays stored as JSON strings)
        result_file_names_serialized = None
        if result_file_names is not None:
            result_file_names_serialized = json.dumps(result_file_names)
        
        with connect(self.db_path) as conn:
            if result_location is not None or result_file_names is not None:
                conn.execute(
                    """
                    UPDATE xai_jobs
                    SET status = ?, result_location = ?, result_file_names = ?, finished_at = CURRENT_TIMESTAMP
                    WHERE job_id = ?
                    """,
                    [status, result_location, result_file_names_serialized, job_id],
                )
            else:
                conn.execute(
                    """
                    UPDATE xai_jobs
                    SET status = ?
                    WHERE job_id = ?
                    """,
                    [status, job_id],
                )

    def get_xai_job(self, job_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Retrieve XAI job details by job_id."""
        with connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT job_id, al_instance_id, model_id, ticket_ref_or_sha, status, request_ticket_location, request_model_location, request_preprocessor_location, request_raw_tickets_locations, result_location, result_file_names, created_at, finished_at, user_id
                FROM xai_jobs
                WHERE job_id = ?
                """,
                [job_id],
            ).fetchone()

        if not row:
            return None

        return {
            "job_id": str(row[0]),
            "al_instance_id": row[1],
            "model_id": row[2],
            "ticket_ref_or_sha": row[3],
            "status": row[4],
            "request_ticket_location": row[5],
            "request_model_location": row[6],
            "request_preprocessor_location": row[7],
            "request_raw_tickets_locations": _deserialize_varchar_array(row[8]),
            "result_location": row[9],
            "result_file_names": _deserialize_varchar_array(row[10]),
            "created_at": row[11],
            "finished_at": row[12],
            "user_id": str(row[13]) if row[13] is not None else None,
        }

    # --- Deletes ---
    def delete_instance(self, al_instance_id: int) -> None:
        """Delete all database records for an instance. Continues even if some deletes fail."""
        import logging
        logger = logging.getLogger(__name__)
        
        if al_instance_id == GROUND_TRUTH_AL_INSTANCE_ID:
            raise ValueError("Cannot delete ground truth AL instance")
        
        # Attempt each delete independently so partial deletions don't block cleanup
        tables_and_queries = [
            ("al_events", "DELETE FROM al_events WHERE al_instance_id = ?"),
            ("labels", "DELETE FROM labels WHERE al_instance_id = ?"),
            ("label_decisions", "DELETE FROM label_decisions WHERE al_instance_id = ?"),
            ("model_paths", "DELETE FROM model_paths WHERE al_instance_id = ?"),
            ("metrics", "DELETE FROM metrics WHERE al_instance_id = ?"),
            ("xai_jobs", "DELETE FROM xai_jobs WHERE al_instance_id = ?"),
            ("instance_delegations", "DELETE FROM instance_delegations WHERE al_instance_id = ?"),
            ("al_instances", "DELETE FROM al_instances WHERE al_instance_id = ?"),
        ]
        
        for table_name, query in tables_and_queries:
            try:
                with connect(self.db_path) as conn:
                    conn.execute(query, [al_instance_id])
            except Exception as e:
                logger.warning(f"Failed to delete instance {al_instance_id} from {table_name}: {e}")

    def delegate_instance(
        self,
        *,
        al_instance_id: int,
        delegate_user_id: str,
        granted_by: str,
    ) -> None:
        """Grant a user access to an AL instance."""
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO instance_delegations (al_instance_id, delegate_user_id, granted_by)
                VALUES (?, ?::UUID, ?::UUID)
                ON CONFLICT (al_instance_id, delegate_user_id) DO NOTHING
                """,
                [al_instance_id, delegate_user_id, granted_by],
            )

    def revoke_delegation(
        self,
        *,
        al_instance_id: int,
        delegate_user_id: str,
    ) -> None:
        """Remove a user's delegated access to an instance."""
        with connect(self.db_path) as conn:
            conn.execute(
                """
                DELETE FROM instance_delegations
                WHERE al_instance_id = ? AND delegate_user_id = ?::UUID
                """,
                [al_instance_id, delegate_user_id],
            )

    def get_delegates_for_instance(
        self,
        *,
        al_instance_id: int,
    ) -> list[dict]:
        """Get all users delegated access to an instance."""
        with connect(self.db_path) as conn:
            result = conn.execute(
                """
                SELECT 
                    d.delegate_user_id,
                    d.granted_by,
                    d.granted_at,
                    u.username
                FROM instance_delegations d
                LEFT JOIN users u ON u.user_id = d.delegate_user_id
                WHERE d.al_instance_id = ?
                ORDER BY d.granted_at
                """,
                [al_instance_id],
            ).fetchall()
            return [
                {
                    "delegate_user_id": str(row[0]),
                    "granted_by": str(row[1]),
                    "granted_at": row[2],
                    "username": row[3],
                }
                for row in result
            ]

    def is_user_delegate(
        self,
        *,
        al_instance_id: int,
        user_id: str,
    ) -> bool:
        """Check if a user has been delegated access to an instance."""
        with connect(self.db_path) as conn:
            result = conn.execute(
                """
                SELECT 1 FROM instance_delegations
                WHERE al_instance_id = ? AND delegate_user_id = ?::UUID
                """,
                [al_instance_id, user_id],
            ).fetchone()
            return result is not None

    def get_delegated_instance_ids(
        self,
        *,
        user_id: str,
    ) -> set[int]:
        """Get all instance IDs delegated to a user."""
        with connect(self.db_path) as conn:
            result = conn.execute(
                """
                SELECT al_instance_id FROM instance_delegations
                WHERE delegate_user_id = ?::UUID
                """,
                [user_id],
            ).fetchall()
            return {row[0] for row in result}

    def delete_all_delegations_for_instance(
        self,
        *,
        al_instance_id: int,
    ) -> None:
        """Remove all delegations for an instance (called when instance is deleted)."""
        with connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM instance_delegations WHERE al_instance_id = ?",
                [al_instance_id],
            )

    # --- Export ---
    def export_instance_rows(self, al_instance_id: int) -> Dict[str, list[Dict[str, Any]]]:
        """Return raw rows for every DuckDB table relevant to an AL instance export.

        Instance-scoped tables (``al_instances``, ``labels``, ``label_decisions``,
        ``metrics``, ``model_paths``, ``al_events``, ``xai_jobs``,
        ``instance_delegations``) are filtered by ``al_instance_id``. The full
        ``tickets`` table is returned (it is global). ``users`` is scoped to the
        users involved with the instance (owner, delegates, labelers, event
        actors, XAI job submitters) and the ``password`` column is set to
        ``None`` in every returned row.

        ``ground_truth_labels`` holds the raw labels for the reserved ground
        truth instance (``GROUND_TRUTH_AL_INSTANCE_ID``); it is always included
        so the analyst can merge it with the requested instance's labels if
        desired. ``labels`` is never merged with ground truth in the export.

        JSON columns (``al_events.payload``, ``label_decisions.xai_result``,
        ``label_decisions.similar_tickets``) are deserialized into Python
        objects. UUID columns are returned as strings. VARCHAR[] columns on
        ``xai_jobs`` are returned as Python lists.

        Args:
            al_instance_id: The instance to dump.

        Returns:
            A mapping of table name to a list of row dicts.
        """
        user_ids: set[str] = set()

        def _add_user(value: Any) -> None:
            if value is not None:
                user_ids.add(str(value))

        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT al_instance_id, model_name, query_strategy, classes, user_id, created_at
                FROM al_instances WHERE al_instance_id = ?
                """,
                [al_instance_id],
            ).fetchall()
            al_instances = [
                {
                    "al_instance_id": r[0],
                    "model_name": r[1],
                    "query_strategy": r[2],
                    "classes": r[3],
                    "user_id": str(r[4]) if r[4] is not None else None,
                    "created_at": r[5],
                }
                for r in rows
            ]
            for inst in al_instances:
                _add_user(inst["user_id"])

            rows = conn.execute(
                """
                SELECT al_instance_id, iteration_id, f1_score, mean_entropy, num_labeled,
                       accuracy, precision_macro, precision_weighted, recall_macro,
                       recall_weighted, f1_per_class, confusion_matrix, roc_auc_ovr_macro, created_at
                FROM metrics WHERE al_instance_id = ? ORDER BY iteration_id
                """,
                [al_instance_id],
            ).fetchall()
            metrics = [
                {
                    "al_instance_id": r[0],
                    "iteration_id": r[1],
                    "f1_score": r[2],
                    "mean_entropy": r[3],
                    "num_labeled": r[4],
                    "accuracy": r[5],
                    "precision_macro": r[6],
                    "precision_weighted": r[7],
                    "recall_macro": r[8],
                    "recall_weighted": r[9],
                    "f1_per_class": json.loads(r[10]) if r[10] is not None else None,
                    "confusion_matrix": json.loads(r[11]) if r[11] is not None else None,
                    "roc_auc_ovr_macro": r[12],
                    "created_at": r[13],
                }
                for r in rows
            ]

            rows = conn.execute(
                """
                SELECT al_instance_id, model_id, path_to_model, created_at
                FROM model_paths WHERE al_instance_id = ? ORDER BY model_id
                """,
                [al_instance_id],
            ).fetchall()
            model_paths = [
                {
                    "al_instance_id": r[0],
                    "model_id": r[1],
                    "path_to_model": r[2],
                    "created_at": r[3],
                }
                for r in rows
            ]

            rows = conn.execute(
                """
                SELECT al_instance_id, timestamp, user_id, action, latency_ms, payload,
                       actor_type, agent, object_id, duration_s, correct, ai_suggested
                FROM al_events WHERE al_instance_id = ? ORDER BY timestamp
                """,
                [al_instance_id],
            ).fetchall()
            al_events = [
                {
                    "al_instance_id": r[0],
                    "timestamp": r[1],
                    "user_id": str(r[2]) if r[2] is not None else None,
                    "action": r[3],
                    "latency_ms": r[4],
                    "payload": _deserialize_json(r[5]),
                    "actor_type": r[6],
                    "agent": r[7],
                    "object_id": r[8],
                    "duration_s": r[9],
                    "correct": r[10],
                    "ai_suggested": r[11],
                }
                for r in rows
            ]
            for ev in al_events:
                _add_user(ev["user_id"])

            rows = conn.execute(
                """
                SELECT al_instance_id, user_id, ref, label, split, labeled_at
                FROM labels WHERE al_instance_id = ? ORDER BY ref, labeled_at
                """,
                [al_instance_id],
            ).fetchall()
            labels = [
                {
                    "al_instance_id": r[0],
                    "user_id": str(r[1]) if r[1] is not None else None,
                    "ref": r[2],
                    "label": r[3],
                    "split": r[4],
                    "labeled_at": r[5],
                }
                for r in rows
            ]
            for lb in labels:
                _add_user(lb["user_id"])

            rows = conn.execute(
                """
                SELECT al_instance_id, user_id, ref, label, split, labeled_at
                FROM labels WHERE al_instance_id = ? ORDER BY ref, labeled_at
                """,
                [GROUND_TRUTH_AL_INSTANCE_ID],
            ).fetchall()
            ground_truth_labels = [
                {
                    "al_instance_id": r[0],
                    "user_id": str(r[1]) if r[1] is not None else None,
                    "ref": r[2],
                    "label": r[3],
                    "split": r[4],
                    "labeled_at": r[5],
                }
                for r in rows
            ]
            for gl in ground_truth_labels:
                _add_user(gl["user_id"])

            rows = conn.execute(
                """
                SELECT al_instance_id, ref, user_id, label, labeled_at, model_prediction,
                       latency_ms, most_helpful_feature, is_tired, is_difficult, i_dont_know,
                       skipped_for_training, xai_result, similar_tickets
                FROM label_decisions WHERE al_instance_id = ? ORDER BY ref
                """,
                [al_instance_id],
            ).fetchall()
            label_decisions = [
                {
                    "al_instance_id": r[0],
                    "ref": r[1],
                    "user_id": str(r[2]) if r[2] is not None else None,
                    "label": r[3],
                    "labeled_at": r[4],
                    "model_prediction": r[5],
                    "latency_ms": r[6],
                    "most_helpful_feature": r[7],
                    "is_tired": r[8],
                    "is_difficult": r[9],
                    "i_dont_know": r[10],
                    "skipped_for_training": r[11],
                    "xai_result": _deserialize_json(r[12]),
                    "similar_tickets": _deserialize_json(r[13]),
                }
                for r in rows
            ]
            for ld in label_decisions:
                _add_user(ld["user_id"])

            rows = conn.execute(
                """
                SELECT job_id, al_instance_id, user_id, model_id, ticket_ref_or_sha, status,
                       request_ticket_location, request_model_location, request_preprocessor_location,
                       request_one_hot_encoder_location, request_raw_tickets_locations,
                       result_location, result_file_names, created_at, finished_at
                FROM xai_jobs WHERE al_instance_id = ? ORDER BY created_at
                """,
                [al_instance_id],
            ).fetchall()
            xai_jobs = [
                {
                    "job_id": str(r[0]),
                    "al_instance_id": r[1],
                    "user_id": str(r[2]) if r[2] is not None else None,
                    "model_id": r[3],
                    "ticket_ref_or_sha": r[4],
                    "status": r[5],
                    "request_ticket_location": r[6],
                    "request_model_location": r[7],
                    "request_preprocessor_location": r[8],
                    "request_one_hot_encoder_location": r[9],
                    "request_raw_tickets_locations": _deserialize_varchar_array(r[10]),
                    "result_location": r[11],
                    "result_file_names": _deserialize_varchar_array(r[12]),
                    "created_at": r[13],
                    "finished_at": r[14],
                }
                for r in rows
            ]
            for job in xai_jobs:
                _add_user(job["user_id"])

            rows = conn.execute(
                """
                SELECT al_instance_id, delegate_user_id, granted_by, granted_at
                FROM instance_delegations WHERE al_instance_id = ? ORDER BY granted_at
                """,
                [al_instance_id],
            ).fetchall()
            instance_delegations = [
                {
                    "al_instance_id": r[0],
                    "delegate_user_id": str(r[1]) if r[1] is not None else None,
                    "granted_by": str(r[2]) if r[2] is not None else None,
                    "granted_at": r[3],
                }
                for r in rows
            ]
            for d in instance_delegations:
                _add_user(d["delegate_user_id"])
                _add_user(d["granted_by"])

            rows = conn.execute(
                """
                SELECT ref, service_subcategory_name, service_name, request_type, last_team_id_name,
                       title_anon, description_anon, public_log_anon, split, dataset_timestamp
                FROM tickets ORDER BY split, ref
                """,
            ).fetchall()
            tickets = [
                {
                    "ref": r[0],
                    "service_subcategory_name": r[1],
                    "service_name": r[2],
                    "request_type": r[3],
                    "last_team_id_name": r[4],
                    "title_anon": r[5],
                    "description_anon": r[6],
                    "public_log_anon": r[7],
                    "split": r[8],
                    "dataset_timestamp": r[9],
                }
                for r in rows
            ]

            if user_ids:
                placeholders = ", ".join(["?::UUID"] * len(user_ids))
                rows = conn.execute(
                    f"SELECT user_id, username, created_at FROM users WHERE user_id IN ({placeholders}) ORDER BY username",
                    list(user_ids),
                ).fetchall()
                users = [
                    {
                        "user_id": str(r[0]),
                        "username": r[1],
                        "password": None,
                        "created_at": r[2],
                    }
                    for r in rows
                ]
            else:
                users = []

        return {
            "al_instances": al_instances,
            "metrics": metrics,
            "model_paths": model_paths,
            "al_events": al_events,
            "labels": labels,
            "ground_truth_labels": ground_truth_labels,
            "label_decisions": label_decisions,
            "xai_jobs": xai_jobs,
            "instance_delegations": instance_delegations,
            "tickets": tickets,
            "users": users,
        }
