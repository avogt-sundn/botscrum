# botscrum

A fully local RAG (Retrieval-Augmented Generation) pipeline that ingests documents and other sources into a knowledge base, then uses that knowledge base to augment LLM prompts.

Runs entirely on-device — no external APIs, no cloud dependencies.

- example for a interaction on the terminal:

    ````bash
    botscrum ingest file README.md
    # Ingested README.md  (15 chunks)

    botscrum  query "what is botscrum"
    #
    # Q: what is botscrum
    #
    # A: **botscrum** is a lightweight, fully‑local Retrieval‑Augmented Generation (RAG) tool.
    # It ingests documents (PDF, Markdown, TXT, or web pages) into a local knowledge base, stores the data in a ChromaDB collection, and then uses that stored information to augment prompts sent to a locally‑hosted LLM (via Ollama). The entire pipeline runs on‑device, with no external APIs or cloud dependencies.
    #
    # Key features (from the README):
    #
    # - **CLI commands**: `ingest`, `query`, `list`, `clear` for managing sources.
    # - **Local storage**: `~/.botscrum/chroma/` persists data across sessions.
    # - **Configuration**: Environment variables control the Ollama host, embedding and LLM models, and chunking settings.
    #
    # Source: `/workspaces/botscrum/README.md`.
    ````
---
## Design Goals

- **Fully local**: all inference and storage runs on-device via Ollama and ChromaDB
- **Incremental ingestion**: sources can be added over time; each ingest run is idempotent
- **Extensible sources**: start with files and URLs; Confluence, Jira, and Git repos are planned
- **Simple interface**: CLI-first, no server required to use

---

## Stack

| Layer | Tool | Reason |
|---|---|---|
| LLM inference | [Ollama](https://ollama.com) | local model serving, broad model support |
| Embedding model | `nomic-embed-text` (via Ollama) | fast, high quality, runs well on Apple Silicon |
| Default LLM | `llama3.2` (configurable) | good instruction-following, fits in 48GB RAM; swap for larger models as needed |
| Vector store | [ChromaDB](https://www.trychroma.com) | local persistent storage, no separate server, simple Python API |
| CLI framework | [Typer](https://typer.tiangolo.com) + [Rich](https://rich.readthedocs.io) | clean commands, streaming output, progress indicators |
| PDF parsing | `pypdf` | lightweight, no external dependencies |
| Web fetching | `httpx` + `beautifulsoup4` | simple HTTP client + HTML text extraction |
| Package manager | [uv](https://docs.astral.sh/uv/) | fast, modern Python tooling |

---

## Architecture

### Data flow — ingestion

```
source (file / URL / ...)
  → load raw text
  → clean and normalize
  → chunk into overlapping segments
  → embed each chunk (Ollama: nomic-embed-text)
  → store chunks + metadata + embeddings (ChromaDB)
```

### Data flow — query

```
user question
  → embed question (Ollama: nomic-embed-text)
  → retrieve top-k similar chunks (ChromaDB cosine similarity)
  → build prompt: system instructions + retrieved context + question
  → stream response (Ollama LLM)
```

### Chunking strategy

- Fixed-size character chunks with overlap (default: 500 chars, 50 char overlap)
- Overlap preserves context across chunk boundaries
- Chunk size and overlap are configurable via environment variables

### Deduplication

- Sources are identified by a hash of their content (files) or URL (web pages)
- Re-ingesting the same source replaces existing chunks rather than duplicating them
- Chunk IDs are derived from `{source_id}_{chunk_index}`

---

## Storage

All data is persisted at `~/.botscrum/chroma/`. This directory is created automatically on first run and survives across sessions.

---

## CLI Commands

```
botscrum ingest file <path>      Ingest a local file (PDF, Markdown, TXT)
botscrum ingest url <url>        Ingest a web page
botscrum query "<question>"      Query the knowledge base (streamed response)
botscrum list                    List all ingested sources
botscrum clear                   Remove all sources (or a specific one)
```

---

## Configuration

Configured via environment variables or a `.env` file in the working directory:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server address |
| `EMBED_MODEL` | `nomic-embed-text` | Ollama model used for embeddings |
| `LLM_MODEL` | `llama3.2` | Ollama model used for response generation |
| `CHROMA_DIR` | `~/.botscrum/chroma` | ChromaDB persistence directory |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between consecutive chunks |
| `TOP_K` | `5` | Number of chunks retrieved per query |

---

## Prerequisites

- macOS with [Ollama](https://ollama.com) installed and running
- Required Ollama models pulled:
  ```
  ollama pull nomic-embed-text
  ollama pull llama3.2
  ```
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) installed

---

## Planned Sources

The ingestion layer is designed to be extended. Planned connectors:

- **Confluence**: ingest spaces or individual pages via Confluence REST API
- **Jira**: ingest issues, epics, and comments via Jira REST API
- **Git repositories**: ingest source code and markdown docs from local or remote repos

Each connector will follow the same interface: load text, chunk, embed, store.

---

## Project Structure

```
botscrum/
├── pyproject.toml
├── .env.example
├── README.md
└── src/
    └── botscrum/
        ├── __init__.py
        ├── cli.py            # Typer CLI entry point
        ├── config.py         # Environment-based configuration
        ├── store.py          # ChromaDB collection wrapper
        ├── query.py          # Retrieve + generate
        ├── chunker.py        # Text chunking utilities
        └── ingest/
            ├── __init__.py
            ├── files.py      # Local file ingestion (PDF, MD, TXT)
            └── web.py        # URL ingestion
```
