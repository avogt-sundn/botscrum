from __future__ import annotations

import chromadb
from chromadb.api.client import Client
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

from .config import CHROMA_DIR, EMBED_MODEL, OLLAMA_HOST

COLLECTION_NAME = "knowledge"


def _embedding_function() -> OllamaEmbeddingFunction:
    return OllamaEmbeddingFunction(
        url=f"{OLLAMA_HOST}/api/embeddings",
        model_name=EMBED_MODEL,
    )


def get_client() -> Client:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection(client: Client | None = None) -> chromadb.Collection:
    if client is None:
        client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def reset_collection() -> chromadb.Collection:
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return get_collection(client)
