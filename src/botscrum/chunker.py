from .config import CHUNK_OVERLAP, CHUNK_SIZE

# Ordered by preference: break at the widest natural boundary first
_SEPARATORS = ("\n\n", "\n", ". ", "! ", "? ", " ")


def count_tokens(text: str) -> int:
    """Estimate token count (approx. 1 token per 4 characters)."""
    return max(1, len(text) // 4)


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))

        if end < len(text):
            # Try to break at a natural boundary in the second half of the window
            midpoint = start + size // 2
            for sep in _SEPARATORS:
                pos = text.rfind(sep, midpoint, end)
                if pos != -1:
                    end = pos + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        next_start = end - overlap
        # Guard against infinite loop when overlap >= chunk size
        start = next_start if next_start > start else end

    return chunks
