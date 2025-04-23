# app/core/storage.py
from dataclasses import dataclass, field
from typing import Dict, Any
import joblib
import os
from pathlib import Path

class ActiveLearningStorage:
    def __init__(self):
        self.al_instances_dict = {}
        self.model_paths_dict = {}
        self.results_dict = {}
        self.dataset_dict = {}
    
    # Get the next available instance ID
    def get_next_instance_id(self) -> int:
        return 1 if not self.al_instances_dict else max(self.al_instances_dict.keys()) + 1
    