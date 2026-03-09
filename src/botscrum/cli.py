from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(help="botscrum — local RAG knowledge base", add_completion=False, no_args_is_help=True)
ingest_app = typer.Typer(help="Ingest sources into the knowledge base", no_args_is_help=True)
app.add_typer(ingest_app, name="ingest")
list_app = typer.Typer(help="List knowledge base contents", no_args_is_help=True)
app.add_typer(list_app, name="list")

console = Console()


def _print_ingest_result(source: str, token_counts: list[int]) -> None:
    if not token_counts:
        console.print(f"[yellow]No content found in[/yellow] {source}")
        return

    table = Table(title=f"[green]Ingested[/green] {source}", show_footer=True)
    table.add_column("Chunk", justify="right", style="dim", no_wrap=True, footer="Total")
    table.add_column("Tokens", justify="right", footer=str(sum(token_counts)))

    for i, tokens in enumerate(token_counts, 1):
        table.add_row(str(i), str(tokens))

    console.print(table)


@ingest_app.command("file")
def ingest_file_cmd(
    path: Path = typer.Argument(..., help="Path to file (PDF, Markdown, TXT, RST, HTML)"),
) -> None:
    """Ingest a local file into the knowledge base."""
    if not path.exists():
        console.print(f"[red]Error:[/red] file not found: {path}")
        raise typer.Exit(1)

    from .ingest.files import ingest_file

    try:
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console, transient=True) as p:
            p.add_task(f"Ingesting [bold]{path.name}[/bold]...")
            token_counts = ingest_file(path)
        _print_ingest_result(str(path), token_counts)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@ingest_app.command("url")
def ingest_url_cmd(
    url: str = typer.Argument(..., help="URL of the web page to ingest"),
) -> None:
    """Ingest a web page into the knowledge base."""
    from .ingest.web import ingest_url

    try:
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console, transient=True) as p:
            p.add_task(f"Fetching [bold]{url}[/bold]...")
            token_counts = ingest_url(url)
        _print_ingest_result(url, token_counts)
    except Exception as e:
        msg = str(e)
        console.print(f"[red]Error:[/red] {msg}")
        if "401" in msg or "403" in msg:
            from urllib.parse import urlparse
            host = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            console.print(f"[yellow]Hint:[/yellow] run [bold]botscrum auth {host}[/bold] to log in via browser first.")
        raise typer.Exit(1)


@app.command()
def auth(
    url: str = typer.Argument(..., help="Base URL of the Jira or Confluence instance"),
) -> None:
    """Authenticate with a Jira or Confluence instance via browser login."""
    from .auth import browser_login

    console.print(f"[cyan]Starting local proxy for[/cyan] {url}")
    console.print("[dim]A login URL will be printed — open it in your browser and log in.[/dim]")
    try:
        count = browser_login(url)
        console.print(f"[green]Saved[/green] {count} session cookies for {url}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def query(
    question: str = typer.Argument(..., help="Question to ask the knowledge base"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show retrieved chunks before the answer"),
) -> None:
    """Query the knowledge base and stream a response."""
    from .query import query as run_query

    try:
        console.print(f"\n[bold cyan]Q:[/bold cyan] {question}\n")
        chunks, stats, stream = run_query(question)

        if verbose and chunks:
            table = Table(title=f"Retrieved {len(chunks)} chunk(s)", show_lines=True)
            table.add_column("#", justify="right", style="dim", no_wrap=True)
            table.add_column("Source", style="cyan")
            table.add_column("Preview")
            for i, c in enumerate(chunks, 1):
                preview = c["preview"]
                if len(preview) == 120:
                    preview += "…"
                table.add_row(str(i), c["source"], preview)
            console.print(table)
            console.print()

        console.print("[bold cyan]A:[/bold cyan] ", end="")
        for part in stream:
            print(part, end="", flush=True)
        print("\n")

        if stats:
            console.print(
                f"[dim]prompt: {stats['prompt_tokens']:,} tokens · "
                f"response: {stats['response_tokens']:,} tokens[/dim]"
            )
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)


@list_app.command("sources")
def list_sources() -> None:
    """List all ingested sources."""
    from .store import get_collection

    collection = get_collection()
    result = collection.get(include=["metadatas"])

    if not result["ids"]:
        console.print("[yellow]No sources ingested yet.[/yellow]")
        return

    # Aggregate chunk counts per source
    sources: dict[str, dict] = {}
    for meta in result["metadatas"]:
        sid = meta.get("source_id", "unknown")
        if sid not in sources:
            sources[sid] = {"type": meta.get("type", "?"), "source": meta.get("source", "?"), "chunks": 0}
        sources[sid]["chunks"] += 1

    table = Table(title=f"Knowledge base — {len(sources)} source(s), {len(result['ids'])} chunk(s) total")
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Source")
    table.add_column("Chunks", justify="right", style="dim")
    table.add_column("Source ID", style="dim")

    for sid, info in sources.items():
        table.add_row(info["type"], info["source"], str(info["chunks"]), sid)

    console.print(table)


@list_app.command("chunks")
def list_chunks(
    source: str = typer.Option(None, "--source", "-s", help="Filter by source ID"),
) -> None:
    """List individual chunks in the knowledge base."""
    from .store import get_collection

    collection = get_collection()
    result = collection.get(
        where={"source_id": source} if source else None,
        include=["documents", "metadatas"],
    )

    if not result["ids"]:
        msg = f"No chunks found for source '{source}'." if source else "No chunks ingested yet."
        console.print(f"[yellow]{msg}[/yellow]")
        return

    table = Table(title=f"{len(result['ids'])} chunk(s)")
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Source", style="cyan")
    table.add_column("Preview")

    for i, (doc, meta) in enumerate(zip(result["documents"], result["metadatas"]), 1):
        preview = doc[:120].replace("\n", " ")
        if len(doc) > 120:
            preview += "…"
        table.add_row(str(i), meta.get("source", "?"), preview)

    console.print(table)


@app.command()
def clear(
    source: str = typer.Option(None, "--source", "-s", help="Source ID to remove (see 'botscrum list')"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
) -> None:
    """Remove sources from the knowledge base."""
    from .store import get_collection, reset_collection

    collection = get_collection()

    if source:
        result = collection.get(where={"source_id": source})
        if not result["ids"]:
            console.print(f"[red]Error:[/red] no source found with ID '{source}'")
            raise typer.Exit(1)
        source_name = result["metadatas"][0].get("source", source)
        if not force:
            typer.confirm(f"Remove '{source_name}' ({len(result['ids'])} chunks)?", abort=True)
        collection.delete(ids=result["ids"])
        console.print(f"[green]Removed[/green] {source_name}")
    else:
        total = collection.count()
        if total == 0:
            console.print("[yellow]Knowledge base is already empty.[/yellow]")
            return
        if not force:
            typer.confirm(f"Remove all {total} chunks from the knowledge base?", abort=True)
        reset_collection()
        console.print("[green]Knowledge base cleared.[/green]")
