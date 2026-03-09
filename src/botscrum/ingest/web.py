import hashlib

import httpx
from bs4 import BeautifulSoup

from ..chunker import chunk_text
from ..store import get_collection

_HEADERS = {"User-Agent": "botscrum/0.1 (local RAG tool)"}
_REMOVE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "form"]


def _fetch_text(url: str) -> str:
    from ..auth import load_cookies
    cookies = load_cookies(url)
    resp = httpx.get(url, follow_redirects=True, timeout=30, headers=_HEADERS, cookies=cookies or None)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(_REMOVE_TAGS):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def ingest_url(url: str) -> int:
    text = _fetch_text(url)
    source_id = hashlib.sha256(url.encode()).hexdigest()[:16]

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
            {"source": url, "source_id": source_id, "type": "url", "index": i}
            for i in range(len(chunks))
        ],
    )
    return len(chunks)
