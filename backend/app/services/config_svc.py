from app.config.config import model_dict, qs_dict
from typing import List
import os

class ConfigService:
    def __init__(self):
        pass
    
    def get_available_models(self):
        """Get list of available model names."""
        return {"models": list(model_dict.keys())}
    
    def get_available_query_strategies(self):
        """Get list of available query strategy names."""
        return {"strategies": list(qs_dict.keys())}
    
    def get_available_capabilities(self):
        """Get list of available capabilities."""
        capabilities = ["xai" if os.getenv("USE_RABBITMQ") == "1" else None]
        return {
            "capabilities": [
                cap for cap in capabilities if cap is not None
            ]
        }
