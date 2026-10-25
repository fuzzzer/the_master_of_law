#!/usr/bin/env bash
# One command for the full Fuzzzy Law check: answers -> automatic checks + AI judge -> pass/fail sheet
# against eval/TARGETS.md, plus optional live-server probes and app-flow tests.
#
#   eval/run_full_check.sh --out DIR [--target local|live|external] [--worktree PATH] [--set tuning|heldback|all|lean]
#                          [--judge agent|gemini|claude|none] [--compare EARLIER_DIR] [--gap 45] [--cap N] [--usd-cap USD]
#                          [--worker NAME] [--ids a,b] [--probes] [--app-flows] [--skip-answers]
#
# Keys are read from the macOS keychain inline, by service name, and never printed:
#   local target and Gemini judge: gemini_api_key (Google Cloud key, Vertex express)
#   live target and live probes:   law_aistudio_key (Google AI Studio key, "AIza...")
#   Claude judge / external Claude: fuzzzy_law_anthropic
# A missing key skips that part with a clear line; it never fails silently.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SC="$HERE/scorecard"
TARGET=local; WORKTREE="$(cd "$HERE/.." && pwd)"; SET=all; JUDGE=agent; COMPARE=""; GAP=45; CAP=10000
USDCAP=8; WORKER=scorecard; IDS=""; OUT=""; PROBES=0; APPFLOWS=0; SKIP_ANSWERS=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2;; --target) TARGET="$2"; shift 2;; --worktree) WORKTREE="$2"; shift 2;;
    --set) SET="$2"; shift 2;; --judge) JUDGE="$2"; shift 2;; --compare) COMPARE="$2"; shift 2;;
    --gap) GAP="$2"; shift 2;; --cap) CAP="$2"; shift 2;; --usd-cap) USDCAP="$2"; shift 2;; --worker) WORKER="$2"; shift 2;; --ids) IDS="$2"; shift 2;;
    --probes) PROBES=1; shift;; --app-flows) APPFLOWS=1; shift;; --skip-answers) SKIP_ANSWERS=1; shift;;
    *) echo "unknown flag $1"; exit 2;;
  esac
done
[[ -z "$OUT" ]] && { echo "--out DIR is required"; exit 2; }
mkdir -p "$OUT"
CORPUS="${FL_CORPUS_DIR:-/Volumes/Fuzzzity 2/fuzzzy_company/work/fuzzzy-law-overnight-20261025/scorecard/corpus}"
STORE="$CORPUS/georgian_laws/article_store.db"
PY="$WORKTREE/backend/.venv/bin/python"; [[ -x "$PY" ]] || PY="$HERE/../backend/.venv/bin/python"
[[ -x "$PY" ]] || { echo "no backend venv found (set one up per .agents/context/REPO_FACTS.md)"; exit 2; }
has_key() { security find-generic-password -a fuzzycore -s "$1" >/dev/null 2>&1; }
IDS_ARG=(); [[ -n "$IDS" ]] && IDS_ARG=(--ids "$IDS")

if [[ $SKIP_ANSWERS -eq 0 ]]; then
  case "$TARGET" in
    local)
      if has_key gemini_api_key; then
        FL_KEY="$(security find-generic-password -a fuzzycore -s gemini_api_key -w)" FL_CORPUS_DIR="$CORPUS" \
          "$PY" -I -B "$SC/run_answers.py" --target local --worktree "$WORKTREE" --set "$SET" --out "$OUT" \
          --gap "$GAP" --cap "$CAP" --usd-cap "$USDCAP" --worker "$WORKER" ${IDS_ARG[@]+"${IDS_ARG[@]}"} 2>&1 \
          | grep --line-buffered -v "model_config_read_failed\|chroma_collection_missing" | tee -a "$OUT/run.log"
      else echo "SKIP answers: key gemini_api_key absent"; fi;;
    live)
      if has_key law_aistudio_key; then
        FL_KEY="$(security find-generic-password -a fuzzycore -s law_aistudio_key -w)" \
          "$PY" -I -B "$SC/run_answers.py" --target live --set "$SET" --out "$OUT" --gap "$GAP" --cap "$CAP" --usd-cap "$USDCAP" \
          --worker "$WORKER" ${IDS_ARG[@]+"${IDS_ARG[@]}"} 2>&1 | tee -a "$OUT/run.log"
      else echo "SKIP live answers: key law_aistudio_key absent (the live server accepts only AI Studio keys)"; fi;;
    external)
      KEY=""; has_key fuzzzy_law_anthropic && KEY="$(security find-generic-password -a fuzzycore -s fuzzzy_law_anthropic -w)"
      FL_KEY="$KEY" "$PY" -I -B "$SC/run_answers.py" --target external --set "$SET" --out "$OUT" --gap "$GAP" \
        --cap "$CAP" --worker "$WORKER" ${IDS_ARG[@]+"${IDS_ARG[@]}"} 2>&1 | tee -a "$OUT/run.log"; KEY="";;
  esac
fi

case "$JUDGE" in
  gemini) if has_key gemini_api_key; then
            FL_JUDGE_KEY="$(security find-generic-password -a fuzzycore -s gemini_api_key -w)" \
              "$PY" -I -B "$SC/judge.py" --results "$OUT" --store "$STORE" --judge gemini ${IDS_ARG[@]+"${IDS_ARG[@]}"} | tee -a "$OUT/judge.log"
          else echo "SKIP judge: key gemini_api_key absent"; fi;;
  claude) if has_key fuzzzy_law_anthropic; then
            FL_JUDGE_KEY="$(security find-generic-password -a fuzzycore -s fuzzzy_law_anthropic -w)" \
              "$PY" -I -B "$SC/judge.py" --results "$OUT" --store "$STORE" --judge claude ${IDS_ARG[@]+"${IDS_ARG[@]}"} | tee -a "$OUT/judge.log"
          else echo "SKIP judge: key fuzzzy_law_anthropic absent"; fi;;
  agent) "$PY" -I -B "$SC/judge.py" --results "$OUT" --store "$STORE" --judge packets ${IDS_ARG[@]+"${IDS_ARG[@]}"}
         echo "judge packets written to $OUT/judge/packets/: have a Claude agent judge them with rubric/JUDGE_RUBRIC.md (no API cost), one JSON per item into $OUT/judge/<id>.json, then rerun with --skip-answers --judge none";;
  none) echo "judge skipped (--judge none): judge-based targets will show 'not measured'";;
esac

CMP=(); [[ -n "$COMPARE" ]] && CMP=(--compare "$COMPARE")
SHEETSET=all; [[ "$SET" == "lean" ]] && SHEETSET=lean
"$PY" -I -B "$SC/sheet.py" --results "$OUT" --store "$STORE" --set "$SHEETSET" ${CMP[@]+"${CMP[@]}"}

if [[ $PROBES -eq 1 ]]; then
  if has_key law_aistudio_key; then
    FL_KEY="$(security find-generic-password -a fuzzycore -s law_aistudio_key -w)" "$PY" -I -B "$SC/live_probes.py" --out "$OUT"
  else
    "$PY" -I -B "$SC/live_probes.py" --out "$OUT"
  fi
fi
if [[ $APPFLOWS -eq 1 ]]; then
  if [[ -x "$WORKTREE/frontend/scripts/run_app_flows.sh" ]]; then (cd "$WORKTREE/frontend" && scripts/run_app_flows.sh)
  else echo "SKIP app flows: frontend/scripts/run_app_flows.sh not found in $WORKTREE"; fi
fi
echo "sheet: $OUT/sheet.md"
