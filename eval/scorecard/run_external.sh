#!/usr/bin/env bash
# "Outside AI + connector" scorecard runs: Claude and OpenAI's model, each with and without the
# Fuzzzy Law connector, on the same items. Keys are read inline from the keychain and never printed;
# an assistant whose key is absent is skipped.
#
#   eval/scorecard/run_external.sh <results root> [--set tuning|heldback|all] [--limit N] [other run_answers flags]
#
# Needs: the backend venv (backend/.venv) for the local connector, and the two SDKs in the python that
# runs the scorecard:  <python> -m pip install -r eval/scorecard/targets/requirements-external.txt
# Environment: PY (scorecard python, default backend/.venv/bin/python), CORPUS (folder holding chroma/
# and georgian_laws/article_store.db), FL_CONNECTOR_URL to use an already running or public connector
# (then no local one is started), FL_CONNECTOR_MODE=remote_mcp to let the provider call <url>/mcp itself.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
out="${1:?results root}"; shift
PY="${PY:-$repo/backend/.venv/bin/python}"
CORPUS="${CORPUS:-/Volumes/Fuzzzity 2/fuzzzy_company/work/fuzzzy-law-overnight-20261025/scorecard/corpus}"

started=""
if [[ -z "${FL_CONNECTOR_URL:-}" ]]; then
  export FL_CONNECTOR_URL="http://127.0.0.1:8010"
  (cd "$repo/backend" && CHROMA_PERSIST_DIR="$CORPUS/chroma" .venv/bin/uvicorn app.connector_main:app \
      --host 127.0.0.1 --port 8010 > "$out.connector.log" 2>&1) &
  started=$!
  trap '[[ -n "$started" ]] && kill "$started" 2>/dev/null; pkill -f "app.connector_main:app --host 127.0.0.1 --port 8010" || true' EXIT
  for _ in $(seq 1 30); do curl -sf "$FL_CONNECTOR_URL/api/v1/connector/codes" >/dev/null && break; sleep 1; done
fi

run() {  # assistant, keychain service, extra flag, results subfolder
  local assistant="$1" service="$2" flag="$3" sub="$4"
  shift 4
  if ! security find-generic-password -a fuzzycore -s "$service" >/dev/null 2>&1; then
    echo "SKIP $assistant ($sub): no key '$service' in the keychain"
    return 0
  fi
  FL_KEY="$(security find-generic-password -a fuzzycore -s "$service" -w)" \
    "$PY" -I -B "$here/run_answers.py" --target external --assistant "$assistant" $flag \
      --out "$out/$sub" --worker connector-scorecard --purpose "external assistant answer" "$@"
}

shift_args=("$@")
for pair in "claude fuzzzy_law_anthropic" "chatgpt fuzzzy_law_openai"; do
  set -- $pair
  a="$1"; s="$2"; set -- "${shift_args[@]+"${shift_args[@]}"}"
  run "$a" "$s" "" "external_${a}_with_connector" "$@"
  run "$a" "$s" "--no-connector" "external_${a}_alone" "$@"
done
