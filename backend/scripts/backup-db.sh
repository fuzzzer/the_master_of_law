#!/usr/bin/env bash
#
# Postgres backup for the deployed stack.
#
# `.agents/workflows/08_deploy_checklist.md` step 4 has called this script for
# months and it did not exist, which means every deploy that "followed the
# checklist" ran its migrations with no backup behind it.
#
# Runs on the VPS, next to docker-compose.yml. The database publishes no port
# (by design — see the compose file), so the dump goes through `docker compose
# exec`, not through a host connection.
#
#   ./scripts/backup-db.sh              # write a new dump, prune old ones
#   ./scripts/backup-db.sh --list       # what is on disk
#
# Cron it daily:
#   0 3 * * * cd /var/www/fuzzzy_law/backend && ./scripts/backup-db.sh >> /var/log/fuzzzy-backup.log 2>&1
#
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/fuzzzy-law}"
KEEP_DAYS="${KEEP_DAYS:-14}"
DB_NAME="fuzzzy_law"
DB_USER="fuzzzy_user"

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ "${1:-}" == "--list" ]]; then
  ls -lh "$BACKUP_DIR" 2>/dev/null || echo "no backups yet in $BACKUP_DIR"
  exit 0
fi

mkdir -p "$BACKUP_DIR"

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="$BACKUP_DIR/fuzzzy_law-$stamp.sql.gz"

echo "📦 dumping $DB_NAME → $out"

# --clean --if-exists so the dump can be restored over a live database
# without a manual drop first. Piped straight into gzip: the dump never
# exists uncompressed, so a full disk cannot leave a half-written plain file
# that looks like a valid backup.
#
# `-T` because there is no TTY under cron, and without it docker exec fails
# there while working fine by hand — a difference that shows up at 3am.
set -o pipefail
docker compose exec -T postgres \
  pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists \
  | gzip -9 > "$out"

# A dump that failed after the header is still a file, and `ls` cannot tell
# you which one that is. gzip -t reads the whole stream, so a truncated dump
# is caught HERE rather than during the restore that follows an outage.
if ! gzip -t "$out"; then
  echo "❌ dump is not a valid gzip stream — removing $out" >&2
  rm -f "$out"
  exit 1
fi

size="$(du -h "$out" | cut -f1)"
echo "✅ $out ($size)"

# Prune only AFTER a verified new dump exists, never before: pruning first
# turns a failed backup into a lost history.
find "$BACKUP_DIR" -name 'fuzzzy_law-*.sql.gz' -type f -mtime "+$KEEP_DAYS" -print -delete

echo "🗂  $(find "$BACKUP_DIR" -name 'fuzzzy_law-*.sql.gz' | wc -l | tr -d ' ') backups retained (keeping $KEEP_DAYS days)"

cat <<'EOF'

⚠️  This backs up PostgreSQL only — conversations, messages, feedback and
    traces. It does NOT cover:
      * the law corpus (law_corpus/data/, 907 MB) — rebuildable, and not in
        git either; keep one copy off the VPS
      * users' cases, which live in Hive ON THE DEVICE and exist nowhere
        else. A user who loses their phone loses their case file. That is a
        product decision to make consciously, not a backup this script can
        take.
EOF
