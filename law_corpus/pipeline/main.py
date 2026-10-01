"""
Pipeline orchestrator and CLI entry point.

Usage:
    python -m pipeline.main run --priority P0
    python -m pipeline.main scrape --source matsne
    python -m pipeline.main parse --input-dir data/raw
    python -m pipeline.main chunk --input-dir data/parsed
    python -m pipeline.main embed --input-dir data/chunks
    python -m pipeline.main index --backend chroma
    python -m pipeline.main thresholds
    python -m pipeline.main stats
    python -m pipeline.main validate
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pipeline.config import VectorStoreBackend, settings
from pipeline.utils.logger import get_logger, setup_logging

app = typer.Typer(
    name="law-corpus",
    help="Georgian Law Corpus Pipeline — scrape, parse, chunk, embed, index.",
    add_completion=False,
)
console = Console()
logger = get_logger(__name__)


# ── Helper to run async functions from sync CLI ─────────────

def _run(coro):
    """Run an async coroutine from synchronous CLI context."""
    return asyncio.run(coro)


# ── SCRAPE ───────────────────────────────────────────────────

@app.command()
def scrape(
    source: str = typer.Option("matsne", help="Data source (matsne, parliament)"),
    priority: Optional[list[str]] = typer.Option(None, "--priority", "-p", help="Priority filter (P0, P1, P2, P3)"),
    laws: Optional[str] = typer.Option(None, help="Comma-separated law slugs"),
) -> None:
    """Download legal documents from the specified source."""
    setup_logging(settings.log_level.value)
    settings.ensure_dirs()

    async def _scrape():
        from pipeline.scraper.matsne_scraper import MatsneScraper
        from pipeline.scraper.session_manager import SessionManager

        async with SessionManager() as session:
            scraper = MatsneScraper(session)
            results = await scraper.scrape_all(priorities=priority or None)
            console.print(f"[green]✓[/green] Scraped {len(results)} documents")

    _run(_scrape())


# ── PARSE ────────────────────────────────────────────────────

@app.command()
def parse(
    input_dir: Path = typer.Option(None, help="Directory with raw HTML files"),
) -> None:
    """Parse downloaded HTML/PDF files into structured documents."""
    setup_logging(settings.log_level.value)
    settings.ensure_dirs()
    raw_dir = input_dir or settings.raw_html_dir

    from pipeline.parser.html_parser import HtmlLegalParser
    from pipeline.models.scrape_result import ContentFormat, ScrapeResult
    from datetime import datetime, timezone

    parser = HtmlLegalParser()
    parsed_count = 0

    for html_file in sorted(raw_dir.glob("*.html")):
        doc_id = html_file.stem
        content = html_file.read_bytes()

        # Load seed metadata if available
        meta_path = settings.raw_metadata_dir / f"{doc_id}.json"
        seed_meta = None
        if meta_path.exists():
            seed_meta = json.loads(meta_path.read_text("utf-8"))

        result = ScrapeResult(
            url=seed_meta.get("url", "") if seed_meta else "",
            document_id=doc_id,
            content=content,
            content_format=ContentFormat.HTML,
            encoding="utf-8",
            scraped_at=datetime.now(timezone.utc),
            content_hash="",
        )

        document = parser.parse(result, seed_meta)

        # Save parsed document
        out_path = settings.parsed_dir / f"{doc_id}.json"
        out_path.write_text(
            document.model_dump_json(indent=2, exclude={"raw_html", "raw_text"}),
            encoding="utf-8",
        )
        parsed_count += 1
        console.print(f"  Parsed {doc_id}: {document.article_count} articles")

    console.print(f"[green]✓[/green] Parsed {parsed_count} documents")


# ── CHUNK ────────────────────────────────────────────────────

@app.command()
def chunk(
    input_dir: Path = typer.Option(None, help="Directory with parsed JSON files"),
) -> None:
    """Chunk parsed documents into embeddable pieces."""
    setup_logging(settings.log_level.value)
    settings.ensure_dirs()
    parsed_dir = input_dir or settings.parsed_dir

    from pipeline.chunker.legal_chunker import LegalChunker
    from pipeline.chunker.chunk_validator import validate_chunks
    from pipeline.models.legal_document import LegalDocument

    chunker = LegalChunker()
    total_chunks = 0

    for json_file in sorted(parsed_dir.glob("*.json")):
        doc = LegalDocument.model_validate_json(json_file.read_text("utf-8"))
        chunks = chunker.chunk_document(doc)
        validate_chunks(chunks)

        # Save chunks
        out_path = settings.chunks_dir / f"{doc.document_id}.json"
        import orjson
        out_path.write_bytes(orjson.dumps(
            [c.model_dump(exclude={"embedding"}) for c in chunks],
            option=orjson.OPT_INDENT_2,
        ))
        total_chunks += len(chunks)
        console.print(f"  Chunked {doc.document_id}: {len(chunks)} chunks")

    console.print(f"[green]✓[/green] Generated {total_chunks} chunks")


# ── EMBED ────────────────────────────────────────────────────

@app.command()
def embed(
    input_dir: Path = typer.Option(None, help="Directory with chunk JSON files"),
) -> None:
    """Generate embeddings for all chunks via Vertex AI."""
    setup_logging(settings.log_level.value)
    settings.ensure_dirs()
    chunks_dir = input_dir or settings.chunks_dir

    async def _embed():
        from pipeline.embedder.batch_embedder import BatchEmbedder
        from pipeline.models.legal_chunk import LegalChunk
        import orjson

        embedder = BatchEmbedder()
        total = 0

        for json_file in sorted(chunks_dir.glob("*.json")):
            raw = orjson.loads(json_file.read_bytes())
            chunks = [LegalChunk.model_validate(c) for c in raw]
            embedded = await embedder.embed_chunks(chunks)
            total += len([c for c in embedded if c.embedding is not None])
            console.print(f"  Embedded {json_file.stem}: {len(embedded)} chunks")

        console.print(f"[green]✓[/green] Embedded {total} chunks total")

    _run(_embed())


# ── INDEX ────────────────────────────────────────────────────

@app.command()
def index(
    backend: str = typer.Option("chroma", help="Vector store backend (chroma, vertex)"),
) -> None:
    """Index embedded chunks into the vector store."""
    setup_logging(settings.log_level.value)
    settings.ensure_dirs()

    from pipeline.indexer.vector_store_indexer import VectorStoreIndexer
    from pipeline.indexer.search_index_builder import SearchIndexBuilder
    from pipeline.embedder.embedding_cache import EmbeddingCache
    from pipeline.models.legal_chunk import LegalChunk
    import orjson

    store_backend = VectorStoreBackend(backend)
    indexer = VectorStoreIndexer(backend=store_backend)
    search_builder = SearchIndexBuilder()
    cache = EmbeddingCache()
    all_chunks: list[LegalChunk] = []

    for json_file in sorted(settings.chunks_dir.glob("*.json")):
        raw = orjson.loads(json_file.read_bytes())
        chunks = [LegalChunk.model_validate(c) for c in raw]
        all_chunks.extend(chunks)

    # Hydrate embeddings from cache — chunk JSON files exclude the embedding
    # field (LegalChunk.embedding has exclude=True), so we must load them
    # from the file-backed EmbeddingCache populated during the embed stage.
    hydrated = 0
    missing_embeddings: list[str] = []
    for chunk in all_chunks:
        embedding = cache.get(chunk.chunk_id, chunk.content_hash or "")
        if embedding is not None:
            chunk.embedding = embedding
            hydrated += 1
        else:
            missing_embeddings.append(chunk.chunk_id)

    if missing_embeddings:
        console.print(
            f"[yellow]⚠ {len(missing_embeddings)} chunks have no cached embedding[/yellow]"
        )
        for cid in missing_embeddings[:10]:
            console.print(f"  Missing: {cid}")
        if len(missing_embeddings) > 10:
            console.print(f"  ... and {len(missing_embeddings) - 10} more")
    else:
        console.print(f"[green]✓[/green] Loaded {hydrated} embeddings from cache")

    count = indexer.index_chunks(all_chunks)
    search_builder.build(all_chunks)
    console.print(f"[green]✓[/green] Indexed {count} chunks into {backend}")


# ── THRESHOLDS ───────────────────────────────────────────────

@app.command()
def thresholds(
    dry_run: bool = typer.Option(False, "--dry-run", help="Print instead of ingesting"),
) -> None:
    """Ingest legal thresholds (e.g., drug quantities) from the catalog."""
    setup_logging(settings.log_level.value)
    
    import sys
    from pathlib import Path
    
    # Ensure root directory is in sys.path so we can import ingest_thresholds
    root_dir = str(Path(__file__).parent.parent.resolve())
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
        
    from ingest_thresholds import ingest
    
    console.print("[bold]Ingesting thresholds from catalog...[/bold]")
    ingest(dry_run=dry_run)
    console.print("[green]✓[/green] Thresholds ingested")


# ── RUN (full pipeline) ─────────────────────────────────────

@app.command()
def run(
    priority: Optional[list[str]] = typer.Option(None, "--priority", "-p"),
) -> None:
    """Run the full pipeline: scrape → parse → chunk → embed → index."""
    setup_logging(settings.log_level.value)
    settings.ensure_dirs()
    console.print("[bold]Running full pipeline…[/bold]")

    scrape(source="matsne", priority=priority, laws=None)
    parse(input_dir=None)
    chunk(input_dir=None)
    embed(input_dir=None)
    index(backend=settings.vector_store_backend.value)
    thresholds(dry_run=False)

    console.print("[bold green]✓ Pipeline complete![/bold green]")


# ── STATS ────────────────────────────────────────────────────

@app.command()
def stats() -> None:
    """Display corpus statistics."""
    setup_logging(settings.log_level.value)

    table = Table(title="Corpus Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    # Count raw files
    raw_count = len(list(settings.raw_html_dir.glob("*.html"))) if settings.raw_html_dir.exists() else 0
    table.add_row("Raw documents", str(raw_count))

    # Count parsed files
    parsed_count = len(list(settings.parsed_dir.glob("*.json"))) if settings.parsed_dir.exists() else 0
    table.add_row("Parsed documents", str(parsed_count))

    # Count chunks
    chunk_count = 0
    if settings.chunks_dir.exists():
        import orjson
        for f in settings.chunks_dir.glob("*.json"):
            try:
                data = orjson.loads(f.read_bytes())
                chunk_count += len(data)
            except Exception:
                pass
    table.add_row("Total chunks", str(chunk_count))

    # Embedding cache size
    cache_index = settings.embeddings_dir / "_cache_index.json"
    emb_count = 0
    if cache_index.exists():
        try:
            emb_count = len(json.loads(cache_index.read_text("utf-8")))
        except Exception:
            pass
    table.add_row("Cached embeddings", str(emb_count))

    console.print(table)


# ── VALIDATE ─────────────────────────────────────────────────

@app.command()
def validate() -> None:
    """Validate corpus completeness and quality."""
    setup_logging(settings.log_level.value)

    from pipeline.scraper.matsne_scraper import SEED_LAWS

    issues: list[str] = []
    p0_laws = [l for l in SEED_LAWS if l["priority"] == "P0"]
    p1_laws = [l for l in SEED_LAWS if l["priority"] == "P1"]

    # Check P0 completeness
    for law in p0_laws:
        parsed = settings.parsed_dir / f"{law['document_id']}.json"
        if not parsed.exists():
            issues.append(f"[P0] Missing: {law['document_id']} ({law['title_en']})")

    # Check P1 completeness
    p1_missing = 0
    for law in p1_laws:
        parsed = settings.parsed_dir / f"{law['document_id']}.json"
        if not parsed.exists():
            p1_missing += 1
            issues.append(f"[P1] Missing: {law['document_id']} ({law['title_en']})")

    if issues:
        console.print("[yellow]Validation issues:[/yellow]")
        for issue in issues:
            console.print(f"  ⚠ {issue}")
    else:
        console.print("[green]✓ All P0 and P1 laws are present[/green]")


# ── UPDATE (incremental) ────────────────────────────────────

@app.command()
def update(
    since: str = typer.Option(..., help="ISO date (YYYY-MM-DD) — update laws changed since"),
) -> None:
    """Incrementally update only laws changed since the given date."""
    setup_logging(settings.log_level.value)
    console.print(f"[yellow]Incremental update since {since} — not yet implemented[/yellow]")


# ── Entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    app()
