from collections.abc import Iterator

import ollama

from .config import LLM_MODEL, OLLAMA_HOST, TOP_K
from .store import get_collection

_SYSTEM = (
    "You are a helpful assistant. Answer the user's question using only the provided context. "
    "If the context does not contain enough information, say so clearly. "
    "Be concise and accurate. Cite the source when relevant."
)


def query(question: str, top_k: int = TOP_K) -> Iterator[str]:
    collection = get_collection()

    total = collection.count()
    if total == 0:
        yield "The knowledge base is empty. Ingest some sources first."
        return

    results = collection.query(
        query_texts=[question],
        n_results=min(top_k, total),
        include=["documents", "metadatas"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    context = "\n\n---\n\n".join(
        f"[Source: {m.get('source', 'unknown')}]\n{doc}"
        for doc, m in zip(docs, metas)
    )

    prompt = f"Context:\n\n{context}\n\nQuestion: {question}"

    client = ollama.Client(host=OLLAMA_HOST)
    for part in client.generate(model=LLM_MODEL, prompt=prompt, system=_SYSTEM, stream=True):
        yield part.response
