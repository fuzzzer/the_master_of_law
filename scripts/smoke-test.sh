#!/usr/bin/env bash
#
# Post-deploy smoke test. Run it against the API you just deployed.
#
#   ./scripts/smoke-test.sh https://api.example.ge
#   ./scripts/smoke-test.sh http://127.0.0.1:8000        # on the VPS itself
#
# Every check below is a REAL response shape verified against a running
# instance, not a guess. Checks that need a caller's Google key are listed at
# the end and deliberately not automated — under BYOK the server has no key of
# its own, so a script cannot make a model call without someone lending theirs.
#
set -uo pipefail

BASE="${1:-http://127.0.0.1:8000}"
BASE="${BASE%/}"

pass=0
fail=0

# Asserts on the response BODY and ignores the status code. Two checks below
# expect a deliberate 4xx and still need to read what came back, so `curl -f`
# (which discards the body on non-2xx) cannot be used here.
check() {
  local name="$1" url="$2" expect="$3"
  local body
  body="$(curl -sS -m 20 "$url" 2>&1)"
  if [[ "$body" == *"$expect"* ]]; then
    printf '  ✅ %-38s\n' "$name"
    pass=$((pass + 1))
  else
    printf '  ❌ %-38s missing %q in: %s\n' "$name" "$expect" "${body:0:90}"
    fail=$((fail + 1))
  fi
}

check_status() {
  local name="$1" url="$2" want="$3"
  local code
  code="$(curl -s -o /dev/null -m 20 -w '%{http_code}' "$url")"
  if [[ "$code" == "$want" ]]; then
    printf '  ✅ %-38s HTTP %s\n' "$name" "$code"
    pass=$((pass + 1))
  else
    printf '  ❌ %-38s HTTP %s, wanted %s\n' "$name" "$code" "$want"
    fail=$((fail + 1))
  fi
}

echo "🔍 smoke testing $BASE"
echo

echo "── liveness ────────────────────────────────────────"
check "health"                "$BASE/api/v1/health"        '"status":"ok"'
check "service identity"      "$BASE/api/v1/health"        '"service":"fuzzzy-law"'

echo
echo "── the corpus is actually mounted ──────────────────"
# The single most important check after a rebuild. The 907 MB corpus is NOT in
# git, so a VPS restored from `git pull` alone comes up HEALTHY with an empty
# vector store and answers every legal question from nothing. `health/ready`
# reports the real document count, which is why this asserts on the word
# "collection" rather than on `status: ok` alone.
check "chromadb loaded"       "$BASE/api/v1/health/ready"  'collection'
check "readiness ok"          "$BASE/api/v1/health/ready"  '"status":"ok"'

echo
echo "── retrieval, no key required ──────────────────────"
# Browsing the corpus is pure retrieval and is exempt from the BYOK gate
# (byok_middleware.NO_KEY_PREFIXES). If this needs a key, the exemption list
# regressed and every user hits a paywall on the law browser.
check "law codes list"        "$BASE/api/v1/laws/codes"    'code_id'
check "law search"            "$BASE/api/v1/laws/search?q=%E1%83%A8%E1%83%A0%E1%83%9D%E1%83%9B%E1%83%90&top_k=3" 'results'

echo
echo "── the BYOK gate is closed ─────────────────────────"
# Proves the operator is not silently paying for user traffic. A 200 here
# means either BYOK_REQUIRED got turned off or a server-side key leaked into
# the container — both of which bill the operator for every request.
check "model route rejects keyless" "$BASE/api/v1/rag/collections" 'byok_key_required'

echo
echo "── nothing internal is exposed ─────────────────────"
check_status "docs closed in production" "$BASE/docs" 404

echo
echo "────────────────────────────────────────────────────"
printf '  %d passed, %d failed\n' "$pass" "$fail"

cat <<'EOF'

Not covered here — do these BY HAND with a real Google AI Studio key:

  1. Send a chat message and get a grounded answer with citations.
  2. Send a SECOND message on the SAME open WebSocket connection without
     closing it in between. A skipped test
     (test_websocket_requires_credits_and_deducts) records that turn 2 went
     unanswered under a test client, with the disconnect-watcher task the
     prime suspect and the diagnosis UNPROVEN. Until someone confirms it on a
     real server, treat a second-message hang as expected-and-unfixed, not as
     a surprise.
  3. Create a case, add a fact, close the app, reopen it — cases live in Hive
     on the device, so this is the only check that they survive.
  4. Open the app on a phone in Georgian at font scale 1.3 and read one full
     case screen.
EOF

[[ "$fail" -eq 0 ]]
