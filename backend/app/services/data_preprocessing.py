import pandas as pd
import numpy as np
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder
import joblib

from app.persistence.duckdb.service import DuckDbPersistenceService
from app.config.config import TRAIN_SPLIT, TEST_SPLIT, TEAM_NAME, GROUND_TRUTH_AL_INSTANCE_ID
from app.core.dependencies import get_duckdb_persistence_service

from app.utils.field_mapping import normalise_and_validate_dataframe

# Data preprocessing for the dispatch team endpoint
def dispatch_team(duckdb_service: DuckDbPersistenceService, test_set: bool = False, le: LabelEncoder = None, oh: OneHotEncoder = None, classes: list[int | str] = None):
    """
    This function preprocesses the data for the dispatch team endpoint.
    It takes the raw tabular text data and returs a dataframe with embeddings
    for the title and description and one-hot encoded service subcategory and service name.
    """
    
    # Get the data
    if not test_set:
        df = duckdb_service.load_tickets(split=TRAIN_SPLIT)
    else:
        df = duckdb_service.load_tickets(split=TEST_SPLIT)

    if df is None or df.empty:
        raise ValueError("No data found for the specified split.")

    # In DB-backed datasets labels are stored in the labels table.
    # If Team->Name is not present on tickets, recover it from persisted ground truth labels.
    if TEAM_NAME not in df.columns:
        split = TEST_SPLIT if test_set else TRAIN_SPLIT
        labels = duckdb_service.load_labels(
            al_instance_id=GROUND_TRUTH_AL_INSTANCE_ID,
            split=split,
        )
        if labels is not None and not labels.empty:
            df[TEAM_NAME] = labels.reindex(df['Ref']).to_numpy()
        else:
            df[TEAM_NAME] = np.nan
    
    # Keep Ref as stable identifier index
    df.set_index('Ref', inplace=True)

    # Define one-hot encoder and label encoder if not provided
    if not test_set:
        le = LabelEncoder()
        oh = OneHotEncoder(handle_unknown='ignore')

    # Keep only the tickets that never changed the group
    df = df[df['Last team ID->Name'].isna()]

    # Create a column that contains the title and descripiton
    df['Title+Description'] = df['Title_anon'] + df['Description_anon']
    
    if test_set:
        # If the data iselete the rows that don't have the  
        # title and description or Team->Name
        # Test data has to contain all of the categories (also Team->Name)
        df = df.dropna(subset=['Title+Description', 'Team->Name'])
    else:
        # Delete the rows that don't have the title and description
        # Train data doesn't have to contain Team->Name (AL -> dataset not labeled)
        df = df.dropna(subset=['Title+Description'])

    # Embeddings for the Title+Description
    sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    sentences = df['Title+Description'].astype(str).tolist()
    embeddings = sentence_model.encode(sentences, show_progress_bar=False)
    # Convert to a dataframe aligned to original index
    X = pd.DataFrame(embeddings, index=df.index)
    # Align features to Ref index for downstream .loc usage
    X.index = df.index
    
    if not test_set:
        # If train set, fit the one-hot encoder
        one_hot = oh.fit_transform(df[['Service subcategory->Name', 'Service->Name']])
    else:
        # If test set, transform the one-hot encoder (we have one fitted on train data)
        one_hot = oh.transform(df[['Service subcategory->Name', 'Service->Name']])
    
    # Convert one-hot sparse matrix to dense array then DataFrame
    one_hot = pd.DataFrame(one_hot.toarray(), index=df.index)  # keep Ref alignment
    # Add the dataframes together
    X = pd.concat([X, one_hot], axis=1)
    # Convert the column names to strings
    X.columns = X.columns.astype(str)

    # If train set, fit the label encoder
    if not test_set:
        classes = [np.nan if x == None else x for x in classes]
        classes = classes + [np.nan]
        le.fit(classes)
        y_true = le.transform(df['Team->Name'])
    else:
        # If test set, use the label encoder fitted on train data
        y_true = df['Team->Name']
    
    # Align labels to Ref index (keeps Ref stable everywhere)
    y_true = pd.Series(y_true, index=df.index)
    
    # Return the preprocessed data, the label encoder, and the one-hot encoder
    return X, y_true, le, oh


def inference(df: pd.DataFrame, le: LabelEncoder, oh: OneHotEncoder, sentence_model: SentenceTransformer = None):
    """
    This function preprocesses the data for the inference endpoint.
    It takes the dataframe with fields defined in the dataset config.
    It then preprocesses the data based on the preprocessing steps in dataset config.
    """

    # Rename the columns to match the original column names
    df = df.rename(columns={'title_anon': 'Title_anon', 
                            'description_anon': 'Description_anon',
                            'service_subcategory_name': 'Service subcategory->Name',
                            'service_name': 'Service->Name'})

    # Create a column that contains the title and descripiton
    df['Title+Description'] = df['Title_anon'] + df['Description_anon']
    
    # Embeddings for the Title+Description
    if sentence_model is None:
        sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        
    sentences = df['Title+Description'].astype(str).tolist()
    embeddings = sentence_model.encode(sentences, show_progress_bar=False)
    # Convert to a dataframe
    X = pd.DataFrame(embeddings)

    # One-hot encode the service subcategory and service name
    one_hot = oh.transform(df[['Service subcategory->Name', 'Service->Name']])
    # Convert one-hot sparse matrix to dense array then DataFrame
    one_hot = pd.DataFrame(one_hot.toarray(), index=df.index)  # keep original row alignment

    # Add the dataframes together
    X = pd.concat([X, one_hot], axis=1)
    
    # Convert the column names to strings
    X.columns = X.columns.astype(str)
    
    return X

def inference_general(df: pd.DataFrame, al_instance_id: int):
    """
    This function preprocesses the data for the inference endpoint for a general dataset.
    It takes the dataframe with fields defined in the dataset config.
    It then preprocesses the data based on the preprocessing steps in dataset config and returns the df.

    Note: Some artifacts should be available from the preprocessing 
    of the training data (e.g. label encoder, one-hot encoder ...).
    """

    # Transform the column names to match the json schema of the dataset config (using the field mapping utils)
    df = normalise_and_validate_dataframe(al_instance_id=al_instance_id, df=df)

    duckdb_service = get_duckdb_persistence_service()
    config = duckdb_service.load_dataset_config(al_instance_id=al_instance_id)
    if config is None:
        raise ValueError(f"Dataset config not found for al_instance_id={al_instance_id}")

    fields_cfg = config.get("fields") or {}
    if not isinstance(fields_cfg, dict):
        fields_cfg = {}

    preprocessing = config.get("preprocessing") or {}
    task_cfg = config.get("task") or {}

    text_fields = [
        name for name, field in fields_cfg.items()
        if isinstance(field, dict) and field.get("role") == "text"
    ]
    categorical_fields = [
        name for name, field in fields_cfg.items()
        if isinstance(field, dict) and field.get("role") == "categorical"
    ]
    numeric_fields = [
        name for name, field in fields_cfg.items()
        if isinstance(field, dict) and field.get("type") in {"integer", "int", "float", "number"}
    ]

    # Drop rows (based on drop_if_all_missing)
    for group in preprocessing.get("drop_if_all_missing", []):
        if not isinstance(group, list):
            continue
        subset = [col for col in group if col in df.columns]
        if subset:
            df = df.dropna(subset=subset, how="all")

    # Drop duplicates (based on deduplication)
    dedup_cfg = preprocessing.get("deduplication") or {}
    if dedup_cfg.get("enabled"):
        df = df.drop_duplicates()

    if df.empty:
        raise ValueError("No valid rows remain after preprocessing row filtering")

    # Cast types (based on fields - type)
    for name, field in fields_cfg.items():
        if name not in df.columns or not isinstance(field, dict):
            continue

        field_type = str(field.get("type", "")).lower()
        if field_type in {"integer", "int"}:
            df[name] = pd.to_numeric(df[name], errors="coerce").astype("Int64")
        elif field_type in {"float", "number"}:
            df[name] = pd.to_numeric(df[name], errors="coerce")
        elif field_type in {"string", "text"}:
            mask = df[name].notna()
            df.loc[mask, name] = df.loc[mask, name].astype(str)
        elif field_type in {"boolean", "bool"}:
            df[name] = df[name].astype("boolean")

    # Clean text fields (based on text_cleaning)
    text_cleaning_cfg = preprocessing.get("text_cleaning") or {}
    for col in text_fields:
        if col not in df.columns:
            continue
        values = df[col]
        if "fill_missing" in text_cleaning_cfg:
            values = values.fillna(text_cleaning_cfg.get("fill_missing", ""))
        if text_cleaning_cfg.get("strip_whitespace"):
            values = values.astype(str).str.strip()
        if text_cleaning_cfg.get("lowercase"):
            values = values.astype(str).str.lower()
        df[col] = values

    categorical_cleaning_cfg = preprocessing.get("categorical_cleaning") or {}
    for col in categorical_fields:
        if col not in df.columns:
            continue
        values = df[col]
        if categorical_cleaning_cfg.get("strip_whitespace"):
            values = values.astype(str).str.strip()
        if categorical_cleaning_cfg.get("lowercase"):
            values = values.astype(str).str.lower()
        df[col] = values

    # Validate labels (separate for classification and regression)
    label_field = task_cfg.get("label_field")
    task_type = str(task_cfg.get("type", "")).lower()
    label_cfg = preprocessing.get("label") or {}

    if label_field and label_field in df.columns:
        allowed_values = label_cfg.get("allowed_values")
        drop_unknown = bool(label_cfg.get("drop_unknown", False))

        if task_type == "classification" and isinstance(allowed_values, list) and allowed_values:
            mask = df[label_field].isin(allowed_values) | df[label_field].isna()
            if drop_unknown:
                df = df.loc[mask]
            elif (~mask).any():
                raise ValueError(f"Label field '{label_field}' contains values outside allowed_values")

        if task_type == "regression":
            numeric_label = pd.to_numeric(df[label_field], errors="coerce")
            if drop_unknown:
                df = df.loc[numeric_label.notna()]
            elif numeric_label.isna().any():
                raise ValueError(f"Label field '{label_field}' contains non-numeric values for regression")
            df[label_field] = numeric_label

    if df.empty:
        raise ValueError("No valid rows remain after label validation")

    # Combine text fields (based on text_combination)
    text_combination_cfg = preprocessing.get("text_combination") or {}
    combine_fields = text_combination_cfg.get("fields") or []
    if combine_fields:
        separator = text_combination_cfg.get("separator", " ")
        output_field = text_combination_cfg.get("output_field", "input_text")
        subset = [col for col in combine_fields if col in df.columns]
        if subset:
            df[output_field] = df[subset].fillna("").astype(str).agg(separator.join, axis=1)

    # Encode categorical fields (based on categorical_encoding)
    categorical_encoding_cfg = preprocessing.get("categorical_encoding") or {}
    if categorical_encoding_cfg.get("strategy") == "onehot":
        subset = [col for col in categorical_fields if col in df.columns]
        if subset:
            encoders_dir = Path("backend/storage/encoders") / str(al_instance_id)
            onehot_path = encoders_dir / "onehot_encoder.joblib"
            if not onehot_path.exists():
                raise ValueError(f"Missing one-hot encoder artifact: {onehot_path}")

            onehot_encoder = joblib.load(onehot_path)
            transformed = onehot_encoder.transform(df[subset])
            if hasattr(onehot_encoder, "get_feature_names_out"):
                encoded_columns = onehot_encoder.get_feature_names_out(subset)
            else:
                encoded_columns = [f"onehot_{i}" for i in range(transformed.shape[1])]

            encoded_df = pd.DataFrame(transformed.toarray(), index=df.index, columns=encoded_columns)
            df = pd.concat([df.drop(columns=subset), encoded_df], axis=1)

    # Encode labels (classification -int)
    label_encoding_cfg = preprocessing.get("label_encoding") or {}
    if (
        task_type == "classification"
        and label_encoding_cfg.get("enabled")
        and label_field
        and label_field in df.columns
    ):
        output_field = label_encoding_cfg.get("output_field", "label_id")
        mapping = label_encoding_cfg.get("mapping")

        if isinstance(mapping, dict) and mapping:
            encoded = df[label_field].map(mapping)
        else:
            encoders_dir = Path("backend/storage/encoders") / str(al_instance_id)
            label_path = encoders_dir / "label_encoder.joblib"
            if not label_path.exists():
                raise ValueError(f"Missing label encoder artifact: {label_path}")
            label_encoder = joblib.load(label_path)
            encoded = pd.Series(label_encoder.transform(df[label_field]), index=df.index)

        df[output_field] = encoded

    # Scale numeric fields
    numeric_scaling_cfg = preprocessing.get("numeric_scaling") or {}
    if numeric_scaling_cfg.get("strategy") in {"standard", "minmax"} and numeric_fields:
        scaler_path = Path("backend/storage/encoders") / str(al_instance_id) / "numeric_scaler.joblib"
        if scaler_path.exists():
            scaler = joblib.load(scaler_path)
            subset = [col for col in numeric_fields if col in df.columns]
            if subset:
                df[subset] = scaler.transform(df[subset])

    # Vectorize text fields (use the same model as for training data)
    vectorization_cfg = preprocessing.get("vectorization") or {}
    vectorization_strategy = vectorization_cfg.get("strategy")
    vectorization_fields = [
        col for col in (vectorization_cfg.get("fields") or [])
        if col in df.columns
    ]

    if vectorization_fields and vectorization_strategy == "tfidf":
        vectorizer_path = Path("backend/storage/encoders") / str(al_instance_id) / "vectorizer.joblib"
        if not vectorizer_path.exists():
            raise ValueError(f"Missing fitted vectorizer artifact: {vectorizer_path}")

        vectorizer = joblib.load(vectorizer_path)
        source_col = vectorization_fields[0]
        text_series = df[source_col].fillna("").astype(str)
        transformed = vectorizer.transform(text_series)
        vectorized_df = pd.DataFrame(
            transformed.toarray(),
            index=df.index,
            columns=[f"tfidf_{i}" for i in range(transformed.shape[1])],
        )
        df = pd.concat([df.drop(columns=[source_col]), vectorized_df], axis=1)
    elif vectorization_fields and vectorization_strategy in {"sentence_transformer", "sentence-transformer"}:
        source_col = vectorization_fields[0]
        params = vectorization_cfg.get("params") or {}
        model_name = params.get("model_name", "all-MiniLM-L6-v2")
        sentence_model = SentenceTransformer(model_name)
        embeddings = sentence_model.encode(df[source_col].fillna("").astype(str).tolist(), show_progress_bar=False)
        embedding_df = pd.DataFrame(
            embeddings,
            index=df.index,
            columns=[f"embed_{i}" for i in range(embeddings.shape[1])],
        )
        df = pd.concat([df.drop(columns=[source_col]), embedding_df], axis=1)

    # Return the preprocessed dataframe ready for inference
    return df
