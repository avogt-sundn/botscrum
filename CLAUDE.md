# botscrum — context for Claude

## Project

Local RAG CLI tool. Python 3.12, managed with `uv`. Entry point: `botscrum` (Typer CLI).

## Key files

```
src/botscrum/
  cli.py          # all CLI commands
  query.py        # retrieval + Ollama streaming
  chunker.py      # chunk_text(), count_tokens()
  store.py        # ChromaDB wrapper (get_collection, reset_collection)
  config.py       # env-based config (OLLAMA_HOST, LLM_MODEL, EMBED_MODEL, etc.)
  ingest/
    files.py      # ingest_file(path) -> list[int]
    web.py        # ingest_url(url)   -> list[int]
```

## Conventions

- **Ingest functions** return `list[int]` — one estimated token count per chunk (`len(chunk) // 4`)
- **`query()`** returns `(chunks: list[dict], stats: dict, stream: Iterator[str])`
  - `chunks` — retrieved docs with `source` and `preview` keys
  - `stats` — populated after stream is consumed: `prompt_tokens`, `response_tokens`
  - `stream` — lazy generator; token stats only available after it is fully consumed
- **CLI structure**: `app` has subapps `ingest_app` (name=`ingest`) and `list_app` (name=`list`)
- **Rich tables** used for all structured output; `console = Console()` is module-level in `cli.py`
- **No server** — ChromaDB runs as a local persistent client; Ollama runs separately

## CLI commands

```
botscrum ingest file <path>
botscrum ingest url <url>
botscrum query "<question>" [-v]
botscrum list sources
botscrum list chunks [-s <source-id>]
botscrum clear [--source <id>] [--force]
botscrum auth <base-url>
```

## Adding a new ingest source

1. Create `src/botscrum/ingest/<name>.py` with a function returning `list[int]`
2. Add a `@ingest_app.command("<name>")` in `cli.py` calling `_print_ingest_result()`
