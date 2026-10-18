#!/usr/bin/env bash
# Incremental update — re-scrape and re-process only changed laws.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

SINCE="${1:-$(date -v-7d +%Y-%m-%d 2>/dev/null || date -d '7 days ago' +%Y-%m-%d)}"

echo "═══════════════════════════════════════════════"
echo "  Georgian Law Corpus — Incremental Update"
echo "  Since: $SINCE"
echo "═══════════════════════════════════════════════"

python -m pipeline.main update --since "$SINCE"

echo ""
echo "▶ Rebuilding article store (exact-lookup grounding DB)…"
python scripts/build_article_store.py

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✓ Incremental update complete!"
echo "═══════════════════════════════════════════════"
