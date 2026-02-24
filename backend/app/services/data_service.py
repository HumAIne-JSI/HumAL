import pandas as pd
import numpy as np
from app.persistence.duckdb.service import DuckDbPersistenceService

from app.config.config import TRAIN_SPLIT, TEAM_NAME

class DataService:
    def __init__(
            self, 
            duckdb_service: DuckDbPersistenceService = None
            ):
        self.duckdb_service = duckdb_service or DuckDbPersistenceService()

    def get_tickets(self, indices: list[str]):
        """
        Get tickets by their indices.
        """
        df = self.duckdb_service.load_tickets_by_ref(ref_list=indices)

        if df is None or df.empty:
            return {"tickets": []}
        
        # Replace NaN with None to be compatible with json
        df = df.replace({np.nan: None})
        df = df[[col for col in df.columns if col not in ['split', 'dataset_timestamp']]]  # Exclude internal columns from the response
        
        return {"tickets": df.to_dict(orient='records')}

    def get_teams(self):
        """
        Get teams from the dataset.
        """
        df = self.duckdb_service.load_tickets(split=TRAIN_SPLIT)

        if df is None or df.empty:
            return {"teams": []}
        
        # Extract unique teams that are not NaN
        teams = df[TEAM_NAME].dropna().unique().tolist()
        return {"teams": teams}

    def get_categories(self):
        """
        Get categories from the dataset.
        """
        df = self.duckdb_service.load_tickets(split=TRAIN_SPLIT)

        if df is None or df.empty:
            return {"categories": []}
        
        categories = df['Service->Name'].dropna().unique().tolist()
        return {"categories": categories}

    def get_subcategories(self):
        """
        Get subcategories from the dataset.
        """
        df = self.duckdb_service.load_tickets(split=TRAIN_SPLIT)

        if df is None or df.empty:
            return {"subcategories": []}
        
        subcategories = df['Service subcategory->Name'].dropna().unique().tolist()
        return {"subcategories": subcategories}