#!/usr/bin/env bash
# Full pipeline execution — scrape, parse, chunk, embed, index all Georgian laws.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "═══════════════════════════════════════════════"
echo "  Georgian Law Corpus — Full Pipeline Run"
echo "═══════════════════════════════════════════════"

# Optionally filter by priority
PRIORITIES="${1:---priority P0 --priority P1}"

echo ""
echo "▶ Step 1: Scraping from matsne.gov.ge…"
python -m pipeline.main scrape --source matsne $PRIORITIES

echo ""
echo "▶ Step 2: Parsing HTML documents…"
python -m pipeline.main parse

echo ""
echo "▶ Step 3: Chunking parsed documents…"
python -m pipeline.main chunk

echo ""
echo "▶ Step 4: Generating embeddings via Vertex AI…"
python -m pipeline.main embed

echo ""
echo "▶ Step 5: Indexing into vector store…"
python -m pipeline.main index --backend "${VECTOR_STORE_BACKEND:-chroma}"

echo ""
echo "▶ Step 6: Validating corpus…"
python -m pipeline.main validate

echo ""
echo "▶ Step 7: Statistics…"
python -m pipeline.main stats

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✓ Pipeline complete!"
echo "═══════════════════════════════════════════════"
