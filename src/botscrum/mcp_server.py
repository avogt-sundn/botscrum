from mcp.server.fastmcp import FastMCP

from .config import TOP_K
from .store import get_collection

mcp = FastMCP("botscrum")


@mcp.tool()
def botscrum_retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    """Retrieve the most relevant chunks from the botscrum knowledge base for a question.

    Returns raw chunks with their source and text so the caller can reason over them directly.
    """
    collection = get_collection()
    total = collection.count()
    if total == 0:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=min(top_k, total),
        include=["documents", "metadatas"],
    )

    return [
        {
            "source": m.get("source", "unknown"),
            "source_id": m.get("source_id", ""),
            "type": m.get("type", ""),
            "index": m.get("index", 0),
            "text": doc,
        }
        for doc, m in zip(results["documents"][0], results["metadatas"][0])
    ]


@mcp.tool()
def botscrum_list_sources() -> list[dict]:
    """List all sources currently ingested in the botscrum knowledge base."""
    collection = get_collection()
    result = collection.get(include=["metadatas"])

    sources: dict[str, dict] = {}
    for meta in result["metadatas"]:
        sid = meta.get("source_id", "unknown")
        if sid not in sources:
            sources[sid] = {
                "source_id": sid,
                "source": meta.get("source", "?"),
                "type": meta.get("type", "?"),
                "chunks": 0,
            }
        sources[sid]["chunks"] += 1

    return list(sources.values())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
