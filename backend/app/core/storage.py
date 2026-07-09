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
        self.skipped_tickets: dict[int, set[str]] = {}
    