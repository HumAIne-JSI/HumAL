import pandas as pd
import numpy as np
from app.core.storage import ActiveLearningStorage

class DataService:
    def __init__(self, storage=ActiveLearningStorage):
        self.storage = storage

    def get_tickets(self, al_instance_id: int, indices: list[str], train_data_path: str = None):
        """
        Get tickets by their indices.
        """
        # If the al_instance_id is 0, the train_data_path is provided
        if al_instance_id != 0:
            train_data_path = self.storage.dataset_dict[al_instance_id]['train_data_path']
        
        df = pd.read_csv(train_data_path)
        df = df.loc[df['Ref'].isin(indices)]
        
        # Replace NaN with None to be compatible with json
        df = df.replace({np.nan: None})
        return {"tickets": df.to_dict(orient='records')}

    def get_teams(self, al_instance_id: int, train_data_path: str = None):
        """
        Get teams from the dataset.
        """
        # If the al_instance_id is 0, the train_data_path is provided
        if al_instance_id != 0:
            train_data_path = self.storage.dataset_dict[al_instance_id]['train_data_path']
        
        df = pd.read_csv(train_data_path)
        
        # Extract unique teams that are not NaN
        teams = df['Team->Name'].dropna().unique().tolist()
        return {"teams": teams}

    def get_categories(self, al_instance_id: int, train_data_path: str = None):
        """
        Get categories from the dataset.
        """
        # If the al_instance_id is 0, the train_data_path is provided
        if al_instance_id != 0:
            train_data_path = self.storage.dataset_dict[al_instance_id]['train_data_path']

        df = pd.read_csv(train_data_path)
        categories = df['Service->Name'].dropna().unique().tolist()
        return {"categories": categories}

    def get_subcategories(self, al_instance_id: int, train_data_path: str = None):
        """
        Get subcategories from the dataset.
        """
        # If the al_instance_id is 0, the train_data_path is provided
        if al_instance_id != 0:
            train_data_path = self.storage.dataset_dict[al_instance_id]['train_data_path']

        df = pd.read_csv(train_data_path)
        subcategories = df['Service subcategory->Name'].dropna().unique().tolist()
        return {"subcategories": subcategories}