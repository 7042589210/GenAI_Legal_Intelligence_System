import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AQ.Ab8RN6J6UEZKDPdvvKsGmjOJqCl3_lROMV_0iNgXK0KmO5EcCw")

# Vector Database Path
DB_CHROMA_PATH = os.getenv("DB_CHROMA_PATH", "vectorstore/db_chroma")

# Tesseract Executable Path (Windows Default)
TESSERACT_CMD = os.getenv(
    "TESSERACT_CMD",
    r'C:\Program Files\Tesseract-OCR\tesseract.exe'
)

# Relational Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tata_legal.db")

# Embedding Model — local, free, no API key required
# BAAI/bge-base-en-v1.5 produces 768-dimensional vectors
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")

# Embedding vector dimension — must match the chosen EMBEDDING_MODEL
# BAAI/bge-base-en-v1.5  → 768
# BAAI/bge-small-en-v1.5 → 384
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))

# LLM Model Definitions (uses OpenRouter API for generation)
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b")

# Specialized LLM Model Definitions
LLM_SCAN_MODEL = os.getenv("LLM_SCAN_MODEL", "qwen/qwen3.8-27b")
LLM_REASONING_MODEL = os.getenv("LLM_REASONING_MODEL", "openai/gpt-oss-120b")

def get_openrouter_api_key() -> str:
    """Returns the OpenRouter API key or raises a clear ValueError if missing."""
    key = os.getenv("OPENROUTER_API_KEY") or OPENROUTER_API_KEY
    if not key:
        raise ValueError(
            "OPENROUTER_API_KEY is missing! Ensure your .env file exists in the project root "
            "and contains OPENROUTER_API_KEY=your_actual_key"
        )
    return key