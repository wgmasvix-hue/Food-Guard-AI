#!/usr/bin/env bash
# Installed by install*.sh into /usr/local/bin and run nightly via cron.
# Dumps the Postgres database and archives the uploads volume into
# $INSTALL_DIR/backups/, then prunes anything older than
# BACKUP_RETENTION_DAYS. Safe to run manually too.
#
# Restore with deploy/restore.sh.
set -euo pipefail

INSTALL_DIR="__INSTALL_DIR__"
cd "$INSTALL_DIR"

RETENTION_DAYS="$(grep -E '^BACKUP_RETENTION_DAYS=' .env 2>/dev/null | cut -d= -f2- || true)"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

BACKUP_DIR="$INSTALL_DIR/backups"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"

echo "[backup] Dumping database..."
docker compose exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h localhost -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' \
  > "$BACKUP_DIR/db-${STAMP}.dump"

echo "[backup] Archiving uploads volume..."
docker run --rm \
  -v food-guard-ai_api-uploads:/data:ro \
  -v "$BACKUP_DIR":/backup \
  alpine:3.20 tar czf "/backup/uploads-${STAMP}.tar.gz" -C /data .

echo "[backup] Pruning backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -type f \( -name 'db-*.dump' -o -name 'uploads-*.tar.gz' \) -mtime "+${RETENTION_DAYS}" -print -delete

echo "[backup] Done: db-${STAMP}.dump, uploads-${STAMP}.tar.gz"
echo "[backup] NOTE: these live on the same disk as the app. Copy $BACKUP_DIR offsite regularly (rsync/rclone/S3) — a disk failure would otherwise take out backups and app data together."
