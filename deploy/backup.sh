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

# ---------- optional offsite copy ----------
# Set BACKUP_RCLONE_REMOTE in .env (e.g. "s3-backup:my-bucket/food-guard-ai"
# or "gdrive:backups/food-guard-ai") to also push backups to any rclone
# remote (S3, Backblaze B2, Google Drive, SFTP, ...). Requires `rclone`
# installed and configured (`rclone config`) — see docs/OPERATIONS.md.
# Unset by default: a fresh install keeps working with local-only backups
# and just prints the reminder below, it never fails the backup job.
RCLONE_REMOTE="$(grep -E '^BACKUP_RCLONE_REMOTE=' .env 2>/dev/null | cut -d= -f2- || true)"
if [[ -n "$RCLONE_REMOTE" ]]; then
  if command -v rclone >/dev/null 2>&1; then
    echo "[backup] Syncing $BACKUP_DIR to offsite remote $RCLONE_REMOTE ..."
    if rclone sync "$BACKUP_DIR" "$RCLONE_REMOTE" --create-empty-src-dirs; then
      echo "[backup] Offsite sync complete."
    else
      echo "[backup] WARNING: offsite sync to $RCLONE_REMOTE failed — local backups are still intact, but nothing left this disk. Check rclone config/credentials." >&2
    fi
  else
    echo "[backup] WARNING: BACKUP_RCLONE_REMOTE is set but rclone is not installed — skipping offsite sync. Install with: curl https://rclone.org/install.sh | sudo bash" >&2
  fi
else
  echo "[backup] NOTE: these live on the same disk as the app. Set BACKUP_RCLONE_REMOTE in .env to also copy them offsite automatically (rclone: S3/B2/Drive/SFTP/...) — a disk failure would otherwise take out backups and app data together. See docs/OPERATIONS.md."
fi
