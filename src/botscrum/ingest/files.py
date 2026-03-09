import hashlib
from pathlib import Path

from ..chunker import chunk_text
from ..store import get_collection

_SUPPORTED = {".pdf", ".md", ".txt", ".rst", ".html"}


def _load_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="replace")


def ingest_file(path: Path) -> int:
    path = path.resolve()
    if path.suffix.lower() not in _SUPPORTED:
        raise ValueError(f"Unsupported file type: {path.suffix}. Supported: {', '.join(_SUPPORTED)}")

    text = _load_text(path)
    source_id = hashlib.sha256(str(path).encode()).hexdigest()[:16]

    collection = get_collection()

    existing = collection.get(where={"source_id": source_id})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    chunks = chunk_text(text)
    if not chunks:
        return 0

    collection.add(
        ids=[f"{source_id}_{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[
            {"source": str(path), "source_id": source_id, "type": "file", "index": i}
            for i in range(len(chunks))
        ],
    )
    return len(chunks)
