"""Configuration constants for resolution service"""
import os

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"Error loading environment variables: {e}")

# Model Paths
TEAM_CLASSIFIER_PATH = os.getenv("TEAM_CLASSIFIER_PATH", "./perfect_team_classifier")
TICKET_CLASSIFIER_PATH = os.getenv("TICKET_CLASSIFIER_PATH", "./ticket_classifier_model")

# Embedding Configuration
SENTENCE_MODEL_NAME = os.getenv("SENTENCE_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_CACHE_DIR = os.getenv("EMBEDDING_CACHE_DIR", "embeddings_cache")


# Default Parameters
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
DEFAULT_KB_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "backend/data/tickets_large_first_reply_label.csv")

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")  # Change from gpt-4 for cost savings
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "800"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# Team Mapping
TEAM_MAPPING = {
    0: "(GI-CF) Security & RPA",
    1: "(GI-CyberSec) Security Operation Center",
    2: "(GI-IaaS) Admin - License & Asset Management",
    3: "(GI-IaaS) Admin - Local IT purchase",
    4: "(GI-IaaS) Backend Application Srv. & Project Support",
    5: "(GI-IaaS) Development Platform",
    6: "(GI-IaaS) Network On-Prem (LAN,WLAN,WAN 2nd level)",
    7: "(GI-SM) Service Desk",
    8: "(GI-SaaS) SAP & Synertrade",
    9: "(GI-SaaS) Salesforce",
    10: "(GI-UX) Account Management",
    11: "(GI-UX) Application",
    12: "(GI-UX) Group",
    13: "(GI-UX) Network Access",
    14: "(GI-UX) Office365 & MS-Teams",
    15: "(GI-UX) Unified Communication",
    16: "(GI-UX) Windows"
}

# OpenAI Configuration
_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_OPENAI_CLIENT_MODE = "unavailable"
_OPENAI_INIT_ERROR = None