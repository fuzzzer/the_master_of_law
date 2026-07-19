#!/usr/bin/env bash
# Weekly auto-audit (grounding plan 4.3).
#
# Replays the certification rubric's automated layer over the live system and
# files a findings report to .tasks/audits/. Run weekly (cron/launchd) or
# manually; hand the report + attached traces to a reviewing agent for the
# manual checks (M1-M3, VERIFICATION_PROTOCOL §4).
#
# Usage: eval/run_weekly_audit.sh [BASE_URL]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
BASE_URL="${1:-http://127.0.0.1:8000}"
STAMP="$(date +%Y-%m-%d)"
OUT="$ROOT/.tasks/audits/auto_audit_$STAMP.md"

echo "═══ Weekly grounding auto-audit — $STAMP ═══"

echo "▶ 1/3 Golden grounding subset (one question per domain)…"
GOLDEN_EXIT=0
python3 "$SCRIPT_DIR/run_golden_retrieval.py" \
  --base-url "$BASE_URL" --ids G1,G2,G6,G12,G15,G18,G21,G24,G28,G29 \
  --tag weekly --sleep 25 || GOLDEN_EXIT=$?
LATEST_GOLDEN=$(ls -td "$SCRIPT_DIR"/results/golden/*_weekly | head -1)

echo "▶ 2/3 Grounding metrics snapshot (last 7 days of real traces)…"
METRICS=$(curl -s "$BASE_URL/api/v1/traces/metrics/grounding?days=7")

echo "▶ 3/3 Live drift sampling (store vs matsne.gov.ge)…"
DRIFT_EXIT=0
python3 "$ROOT/law_corpus/scripts/drift_check.py" --samples 10 || DRIFT_EXIT=$?

{
  echo "# Auto-audit — $STAMP (plan 4.3)"
  echo
  echo "## Golden subset (exit $GOLDEN_EXIT — 0 = all checks green)"
  echo
  cat "$LATEST_GOLDEN/report.md"
  echo
  echo "## 7-day grounding metrics"
  echo
  echo '```json'
  echo "$METRICS" | python3 -m json.tool
  echo '```'
  echo
  echo "## Live drift check (exit $DRIFT_EXIT — 0 = no drift)"
  echo
  echo '```json'
  cat "$ROOT/law_corpus/data/georgian_laws/drift_report.json"
  echo '```'
  echo
  echo "## Follow-up"
  echo
  echo "- Any ❌ above: open the trace via \`/api/v1/traces/<id>\` and root-cause."
  echo "- Manual rubric (M1-M3): review attached golden responses in \`$LATEST_GOLDEN\`."
} > "$OUT"

echo "✓ Findings filed → $OUT"
[ "$GOLDEN_EXIT" -eq 0 ] && [ "$DRIFT_EXIT" -eq 0 ]
