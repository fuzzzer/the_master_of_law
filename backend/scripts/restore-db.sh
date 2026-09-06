#!/usr/bin/env bash
#
# Restore a dump made by backup-db.sh.
#
# A backup nobody has restored is a hypothesis, not a backup. Run this once
# against a throwaway database BEFORE launch — the checklist item is in
# LAUNCH.md — so the first restore is not the one performed during an outage.
#
#   ./scripts/restore-db.sh /var/backups/fuzzzy-law/fuzzzy_law-20260906T030000Z.sql.gz
#
set -euo pipefail

DUMP="${1:-}"
DB_NAME="fuzzzy_law"
DB_USER="fuzzzy_user"

if [[ -z "$DUMP" ]]; then
  echo "usage: $0 <dump.sql.gz>" >&2
  exit 2
fi

if [[ ! -f "$DUMP" ]]; then
  echo "❌ no such dump: $DUMP" >&2
  exit 1
fi

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! gzip -t "$DUMP"; then
  echo "❌ $DUMP is not a valid gzip stream — do not restore it" >&2
  exit 1
fi

cat <<EOF
⚠️  About to restore into the RUNNING database.

    dump:     $DUMP
    database: $DB_NAME
    stack:    $(pwd)

    The dump was written with --clean --if-exists, so it DROPS every object
    it recreates. Everything written since the dump was taken is lost.
EOF

read -r -p "Type the database name to confirm: " confirm
if [[ "$confirm" != "$DB_NAME" ]]; then
  echo "aborted."
  exit 1
fi

# Stop the API first. Restoring under live traffic means requests hitting
# tables mid-drop, and the errors that produces look like application bugs.
echo "⏸  stopping api"
docker compose stop api

echo "📥 restoring"
gunzip -c "$DUMP" | docker compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1

echo "🔼 bringing the schema up to the code's expectations"
docker compose start api
docker compose exec -T api alembic upgrade head

echo "🩺 health"
sleep 3
curl -fsS http://127.0.0.1:8000/api/v1/health && echo

echo "✅ restored from $DUMP"
