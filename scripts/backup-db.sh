#!/bin/bash
# ============================================================
# Common Ground — Database Backup Script
# ============================================================
# Dumps PostgreSQL database from the cg-db container.
# Keeps the last 14 daily backups, deletes older ones.
#
# Usage:
#   ./scripts/backup-db.sh
#
# Crontab (daily at 3 AM):
#   0 3 * * * /root/commonground/scripts/backup-db.sh >> /root/commonground/backups/backup.log 2>&1
# ============================================================

set -euo pipefail

BACKUP_DIR="/root/commonground/backups"
CONTAINER="cg-db"
DB_NAME="commonground"
DB_USER="cg_user"
KEEP_DAYS=14
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/cg_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# Dump via docker exec, compress on the fly
docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup complete: $BACKUP_FILE ($SIZE)"

# Prune backups older than KEEP_DAYS
DELETED=$(find "$BACKUP_DIR" -name "cg_*.sql.gz" -mtime +${KEEP_DAYS} -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date)] Pruned $DELETED backup(s) older than ${KEEP_DAYS} days"
fi

echo "[$(date)] Done."
