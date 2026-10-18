#!/usr/bin/env bash
#
# Disposable Postgres for the backend test suite.
#
# WHY THIS EXISTS: three tests in `tests/test_agy_verification.py` talk to a
# real database. The suite's default `DATABASE_URL` points at
# `localhost:5432`, and on a developer machine that port is very often owned
# by an UNRELATED Postgres — the compose stack deliberately publishes no port
# for its own (see docker-compose.yml), so nothing here reserves it. The
# symptom is not a clear "no database": it is
#
#     asyncpg.exceptions.InvalidPasswordError: password authentication failed
#
# i.e. the tests reached somebody else's server. That failure was carried in
# CLAUDE.md for months as "2 pre-existing infra failures". It is not a code
# defect and it is not pre-existing anything — it is a port collision.
#
# This script starts a throwaway Postgres on a port nothing else wants,
# migrates it, and prints the DATABASE_URL to run the suite with.
#
#   ./scripts/test-db.sh up      # start + migrate, print the export line
#   ./scripts/test-db.sh down    # remove it
#   ./scripts/test-db.sh url     # just print the URL
#
set -euo pipefail

CONTAINER="fuzzzy_law_test_pg"
PORT="${TEST_DB_PORT:-55432}"
# These three must match the suite's expectations, not the production values:
# the test URL is assembled from them below and nothing else reads them.
DB_USER="fuzzzy_user"
DB_PASS="corpus_dev_pw"
DB_NAME="fuzzzy_law"

URL="postgresql+asyncpg://${DB_USER}:${DB_PASS}@localhost:${PORT}/${DB_NAME}"

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

case "${1:-up}" in
  url)
    echo "$URL"
    ;;

  down)
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
    echo "✅ removed $CONTAINER"
    ;;

  up)
    if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
      docker start "$CONTAINER" >/dev/null
      echo "▶️  reusing existing $CONTAINER on :$PORT"
    else
      docker run -d --name "$CONTAINER" \
        -e POSTGRES_DB="$DB_NAME" \
        -e POSTGRES_USER="$DB_USER" \
        -e POSTGRES_PASSWORD="$DB_PASS" \
        -p "127.0.0.1:${PORT}:5432" \
        postgres:16-alpine >/dev/null
      echo "🐘 started $CONTAINER on :$PORT"
    fi

    # pg_isready rather than a sleep: the container reports listening before
    # it will accept a connection, and a fixed sleep is how this becomes
    # flaky on a loaded machine.
    for _ in $(seq 1 30); do
      if docker exec "$CONTAINER" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done

    cd "$here"
    DATABASE_URL="$URL" .venv/bin/python -m alembic upgrade head

    cat <<EOF

✅ test database ready. Run the suite with:

   DATABASE_URL="$URL" .venv/bin/python -m pytest tests/ -q

Tear it down with:  ./scripts/test-db.sh down
EOF
    ;;

  *)
    echo "usage: $0 {up|down|url}" >&2
    exit 2
    ;;
esac
