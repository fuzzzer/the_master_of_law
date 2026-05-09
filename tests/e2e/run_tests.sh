#!/usr/bin/env bash
#
# run_tests.sh — Run the full E2E test suite for The Master of Law.
#
# Prerequisites:
#   - Docker & docker-compose installed
#   - Node.js 18+ installed
#   - Flutter SDK installed (for web build)
#
# Usage:
#   ./tests/e2e/run_tests.sh          # Run all E2E tests
#   ./tests/e2e/run_tests.sh --headed # Run in headed mode (for debugging)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
E2E_DIR="${SCRIPT_DIR}"

HEADED_FLAG=""
if [[ "${1:-}" == "--headed" ]]; then
    HEADED_FLAG="--headed"
fi

echo "═══════════════════════════════════════════════"
echo "  The Master of Law — E2E Test Runner"
echo "═══════════════════════════════════════════════"

# ── Step 1: Start backend ──────────────────────────
echo ""
echo "▶ Step 1: Starting backend (docker compose)..."
cd "${PROJECT_ROOT}/backend"
if docker compose ps --services --filter "status=running" 2>/dev/null | grep -q "api"; then
    echo "  ✓ Backend already running"
else
    docker compose up -d
    echo "  Waiting for backend to be ready..."
    for i in $(seq 1 30); do
        if curl -s "http://localhost:8000/api/v1/health" > /dev/null 2>&1; then
            echo "  ✓ Backend ready"
            break
        fi
        sleep 1
    done
fi

# Run database migrations
echo "  Running alembic migrations..."
docker compose exec -T api alembic upgrade head 2>/dev/null || echo "  ⚠ Migration skipped (may already be current)"

# ── Step 2: Build & serve Flutter web ──────────────
echo ""
echo "▶ Step 2: Building Flutter web..."
cd "${PROJECT_ROOT}/frontend"
if [ -d "build/web" ]; then
    echo "  ✓ Flutter web build exists (skipping rebuild)"
else
    flutter build web --release
    echo "  ✓ Flutter web build complete"
fi

# Serve Flutter web (background)
echo "  Serving Flutter web on :8080..."
if lsof -i :8080 > /dev/null 2>&1; then
    echo "  ✓ Port 8080 already in use (assuming Flutter web is served)"
else
    npx -y serve build/web -l 8080 &
    SERVE_PID=$!
    sleep 2
    echo "  ✓ Flutter web served (PID: ${SERVE_PID})"
fi

# ── Step 3: Install Playwright deps ───────────────
echo ""
echo "▶ Step 3: Installing Playwright dependencies..."
cd "${E2E_DIR}"
npm install --silent
npx playwright install chromium --with-deps 2>/dev/null || npx playwright install chromium
echo "  ✓ Playwright ready"

# ── Step 4: Run E2E tests ─────────────────────────
echo ""
echo "▶ Step 4: Running E2E tests..."
echo ""
npx playwright test ${HEADED_FLAG}
TEST_EXIT=$?

# ── Step 5: Report ────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════"
if [ $TEST_EXIT -eq 0 ]; then
    echo "  ✅ ALL E2E TESTS PASSED"
else
    echo "  ❌ SOME TESTS FAILED (exit code: ${TEST_EXIT})"
    echo "  View report: cd tests/e2e && npx playwright show-report"
fi
echo "═══════════════════════════════════════════════"

# Cleanup serve process if we started it
if [ -n "${SERVE_PID:-}" ]; then
    kill "${SERVE_PID}" 2>/dev/null || true
fi

exit $TEST_EXIT
