from collections.abc import Iterator

import ollama

from .config import LLM_MODEL, OLLAMA_HOST, TOP_K
from .store import get_collection

_SYSTEM = (
    "You are a helpful assistant. Answer the user's question using only the provided context. "
    "If the context does not contain enough information, say so clearly. "
    "Be concise and accurate. Cite the source when relevant."
)


def query(question: str, top_k: int = TOP_K) -> tuple[list[dict], dict, Iterator[str]]:
    collection = get_collection()

    total = collection.count()
    if total == 0:
        def _empty() -> Iterator[str]:
            yield "The knowledge base is empty. Ingest some sources first."
        return [], {}, _empty()

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

    chunks = [{"source": m.get("source", "?"), "preview": d[:120].replace("\n", " ")} for d, m in zip(docs, metas)]

    client = ollama.Client(host=OLLAMA_HOST)
    stats: dict = {}

    def _stream() -> Iterator[str]:
        for part in client.generate(model=LLM_MODEL, prompt=prompt, system=_SYSTEM, stream=True):
            if part.done:
                stats["prompt_tokens"] = part.prompt_eval_count
                stats["response_tokens"] = part.eval_count
            yield part.response

    return chunks, stats, _stream()
