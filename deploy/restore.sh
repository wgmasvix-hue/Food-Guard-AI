#!/usr/bin/env bash
# Food Guard AI — restore from a backup made by deploy/backup.sh.
#
# DESTRUCTIVE: replaces the current database (and optionally the uploads
# volume) with the contents of the given backup. Never run via cron —
# this is a manual, deliberate operation.
#
# Usage:
#   sudo bash deploy/restore.sh /opt/food-guard-ai/backups/db-20260729-020000.dump [uploads-20260729-020000.tar.gz]
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/food-guard-ai}"
DB_DUMP="${1:-}"
UPLOADS_ARCHIVE="${2:-}"

log()  { printf '\033[1;32m[restore]\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$1"; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$1"; exit 1; }

[[ -n "$DB_DUMP" ]] || die "Usage: bash deploy/restore.sh <db-dump-file> [uploads-archive.tar.gz]"
[[ -f "$DB_DUMP" ]] || die "$DB_DUMP not found."
[[ -z "$UPLOADS_ARCHIVE" || -f "$UPLOADS_ARCHIVE" ]] || die "$UPLOADS_ARCHIVE not found."

cd "$INSTALL_DIR"

warn "This will REPLACE the current database with $DB_DUMP."
if [[ -n "$UPLOADS_ARCHIVE" ]]; then
  warn "It will also REPLACE all uploaded files with the contents of $UPLOADS_ARCHIVE."
fi
if [[ "${CONFIRM:-}" != "YES" ]]; then
  read -r -p "Type YES to continue: " reply
  [[ "$reply" == "YES" ]] || die "Aborted."
fi

log "Stopping the API so nothing writes to the database mid-restore..."
docker compose stop api

log "Restoring database from $DB_DUMP..."
docker compose exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_restore -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' \
  < "$DB_DUMP"

if [[ -n "$UPLOADS_ARCHIVE" ]]; then
  log "Restoring uploads from $UPLOADS_ARCHIVE..."
  ABS_ARCHIVE="$(readlink -f "$UPLOADS_ARCHIVE")"
  docker run --rm \
    -v food-guard-ai_api-uploads:/data \
    -v "$(dirname "$ABS_ARCHIVE")":/backup:ro \
    alpine:3.20 sh -c "rm -rf /data/* && tar xzf /backup/$(basename "$ABS_ARCHIVE") -C /data"
fi

log "Starting the API back up..."
docker compose start api

API_HOST_PORT="$(grep -E '^API_HOST_PORT=' .env 2>/dev/null | cut -d= -f2- || true)"
API_HOST_PORT="${API_HOST_PORT:-8000}"
log "Waiting for the API to become healthy on 127.0.0.1:${API_HOST_PORT}..."
for i in $(seq 1 30); do
  curl -fsS "http://127.0.0.1:${API_HOST_PORT}/health" >/dev/null 2>&1 && break
  sleep 2
  [[ $i -eq 30 ]] && warn "API did not report healthy within 60s — check 'docker compose logs api'."
done

log "Restore complete."
