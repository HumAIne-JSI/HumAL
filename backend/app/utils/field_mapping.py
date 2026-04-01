import pandas as pd
from app.persistence.duckdb.service import DuckDbPersistenceService
from functools import lru_cache

def normalise_and_validate_dataframe(
    al_instance_id: int,
    df: pd.DataFrame,
    *,
    duckdb_service: DuckDbPersistenceService
) -> pd.DataFrame:
    """
    Normalize dataframe columns based on dataset config fields.

    - Maps aliases/frontend aliases to canonical field names.
    - Ensures all configured columns exist (missing optional columns are added with None).
    - Ensures required columns contain non-empty values.
    """
    rename_dict, name_required = create_renaming_dictionaries(
        al_instance_id=al_instance_id,
        duckdb_service=duckdb_service,
    )

    # Remove the columns that are not in the config (alias)
    df = df.copy()
    df = df[[col for col in df.columns if col in rename_dict["alias_name"].keys()]]

    # Ensure that the dataframe has all of the columns (aliases)
    for alias in rename_dict["alias_name"].keys():
        if alias not in df.columns:
            df[alias] = None

    # Rename all of the columns from alias to name
    df = df.rename(columns=rename_dict["alias_name"])

    # Check that all required columns are present and contain non-empty values
    for name, required in name_required.items():
        if not required:
            continue

        if name not in df.columns:
            raise ValueError(f"Missing required field: {name}")

        values = df[name]
        empty = values.isna() | (values.astype(str).str.strip() == "")
        if empty.any():
            raise ValueError(f"Required field '{name}' contains empty values")

    return df

@lru_cache(maxsize=50)
def create_renaming_dictionaries(
        al_instance_id: int, 
        duckdb_service: DuckDbPersistenceService
        ) -> tuple[dict[str, dict[str, str]], dict[str, bool]]:
    """
    Creates 2 dictionaries:
    - rename_dict: maps all possible column names between each other:
        - name_alias (canonical name to data source name)
        - alias_name (data source name to canonical name)
        - name_frontend_alias (canonical name to frontend name)
        - frontend_alias_name (frontend name to canonical name)
        - alias_frontend_alias (data source name to frontend name)
        - frontend_alias_alias (frontend name to data source name)
    - name_required (canonical name to required boolean)
    """
    config = duckdb_service.load_dataset_config(al_instance_id=al_instance_id)

    if config is None:
        raise ValueError(f"Dataset config not found for al_instance_id={al_instance_id}")

    fields = config.get("fields") or []
    if not isinstance(fields, list) or not fields:
        raise ValueError("Dataset config 'fields' must be a non-empty list")

    rename_dict = {
        'name_alias': {},
        'alias_name': {},
        'name_frontend_alias': {},
        'frontend_alias_name': {},
        'alias_frontend_alias': {},
        'frontend_alias_alias': {}
    }
    name_required: dict[str, bool] = {}

    for field in fields:
        name = field.get("name")
        alias = field.get("alias")
        frontend_alias = field.get("frontend_alias")
        required = field.get("required")

        # Check if any is missing
        if not name or not alias or not frontend_alias or required is None:
            raise ValueError(f"Each field must have 'name', 'alias', 'frontend_alias', and 'required'. Found: {field}")

        rename_dict['name_alias'][name] = alias
        rename_dict['alias_name'][alias] = name
        rename_dict['name_frontend_alias'][name] = frontend_alias
        rename_dict['frontend_alias_name'][frontend_alias] = name
        rename_dict['alias_frontend_alias'][alias] = frontend_alias
        rename_dict['frontend_alias_alias'][frontend_alias] = alias
        name_required[name] = bool(required)

    return rename_dict, name_required

