from app.config.config import model_dict, qs_dict
from typing import List

class ConfigService:
    def __init__(self):
        pass
    
    def get_available_models(self):
        """Get list of available model names."""
        return {"models": list(model_dict.keys())}
    
    def get_available_query_strategies(self):
        """Get list of available query strategy names."""
        return {"strategies": list(qs_dict.keys())}
