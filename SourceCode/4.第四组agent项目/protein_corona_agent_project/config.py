from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / "storage" / "chroma"
COLLECTION_NAME = "course_knowledge_base_bge_m3_v2"
VECTOR_STORE_DIR = PROJECT_ROOT / "storage" / "vector_store_bge_m3"
STRUCTURED_KB_PATH = PROJECT_ROOT / "storage" / "structured_kb.sqlite3"
MEMORY_DB_PATH = PROJECT_ROOT / "storage" / "memory.sqlite3"


OLLAMA_BASE_URL = ""
EMBEDDING_MODEL = "bge-m3"
# Empty means generation will use an external API instead of local Ollama.
LLM_MODEL = ""
EXTERNAL_LLM_BASE_URL = os.getenv("EXTERNAL_LLM_BASE_URL", "")
EXTERNAL_LLM_MODEL = os.getenv("EXTERNAL_LLM_MODEL", "deepseek-ai/DeepSeek-V4-Flash")
EXTERNAL_LLM_API_KEY = os.getenv("EXTERNAL_LLM_API_KEY", "")
EXTERNAL_LLM_MAX_TOKENS = int(os.getenv("EXTERNAL_LLM_MAX_TOKENS", "1200"))
EXTERNAL_LLM_TEMPERATURE = float(os.getenv("EXTERNAL_LLM_TEMPERATURE", "0.2"))
OLLAMA_TIMEOUT = 120

# Do not force CPU fallback on the shared server.
# GPU selection is controlled by the Ollama Docker container, not by this project.
LLM_OPTIONS = {
    "num_predict": 512,
}

CHUNK_SIZE = 900
CHUNK_OVERLAP = 120
EMBEDDING_BATCH_SIZE = 8
EMBEDDING_MAX_TEXT_LENGTH = 1800
EMBEDDING_RETRY_COUNT = 4
EMBEDDING_RETRY_SECONDS = 5

RAG_TOP_K = 6
RAG_MAX_CONTEXT_CHARS = 12000

MEMORY_WORKING_MAX_ITEMS = 20
MEMORY_RETRIEVAL_LIMIT = 5

UNIPROT_BASE_URL = "https://rest.uniprot.org"
UNIPROT_TIMEOUT = 30
SKILL_CALL_LOG_PATH = PROJECT_ROOT / "storage" / "runtime" / "skill_call_log.jsonl"
