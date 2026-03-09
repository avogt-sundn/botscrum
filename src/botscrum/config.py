import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", "~/.botscrum/chroma")).expanduser()
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K = int(os.getenv("TOP_K", "5"))
AUTH_FILE = Path(os.getenv("AUTH_FILE", "~/.botscrum/auth.json")).expanduser()
