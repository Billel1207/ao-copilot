#!/usr/bin/env bash
# ── AO Copilot — Automated PostgreSQL Backup to S3 ────────────────────────
#
# Usage:
#   ./scripts/backup_db.sh
#
# Environment variables (from .env):
#   DATABASE_URL_SYNC — PostgreSQL connection string
#   S3_ENDPOINT_URL   — S3 endpoint (Scaleway / MinIO)
#   S3_BUCKET         — S3 bucket name (default: aocopilot-backups)
#   AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY — S3 credentials
#
# Cron example (daily at 2am):
#   0 2 * * * /app/scripts/backup_db.sh >> /var/log/backup.log 2>&1

set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────────
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/aocopilot_backups"
DB_NAME="${DB_NAME:-aocopilot}"
DB_USER="${DB_USER:-aocopilot}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
S3_BUCKET="${S3_BUCKET:-aocopilot-backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_FILE="${BACKUP_DIR}/aocopilot_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting PostgreSQL backup..."

# ── Dump ──────────────────────────────────────────────────────────────
PGPASSWORD="${PGPASSWORD:-aocopilot_secret}" pg_dump \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  --no-owner \
  --no-privileges \
  --format=plain \
  | gzip > "${BACKUP_FILE}"

FILESIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
echo "[$(date)] Backup created: ${BACKUP_FILE} (${FILESIZE})"

# ── Upload to S3 ──────────────────────────────────────────────────────
if command -v aws &>/dev/null && [ -n "${S3_ENDPOINT_URL:-}" ]; then
  aws s3 cp "${BACKUP_FILE}" \
    "s3://${S3_BUCKET}/backups/aocopilot_${TIMESTAMP}.sql.gz" \
    --endpoint-url "${S3_ENDPOINT_URL}" \
    --quiet
  echo "[$(date)] Uploaded to S3: s3://${S3_BUCKET}/backups/aocopilot_${TIMESTAMP}.sql.gz"

  # ── Cleanup old backups (S3) ─────────────────────────────────────
  CUTOFF=$(date -d "-${RETENTION_DAYS} days" +%Y%m%d 2>/dev/null || date -v-${RETENTION_DAYS}d +%Y%m%d)
  aws s3 ls "s3://${S3_BUCKET}/backups/" --endpoint-url "${S3_ENDPOINT_URL}" \
    | while read -r line; do
      FILE=$(echo "$line" | awk '{print $4}')
      FILE_DATE=$(echo "$FILE" | grep -oP '\d{8}' | head -1)
      if [ -n "$FILE_DATE" ] && [ "$FILE_DATE" -lt "$CUTOFF" ]; then
        aws s3 rm "s3://${S3_BUCKET}/backups/${FILE}" --endpoint-url "${S3_ENDPOINT_URL}" --quiet
        echo "[$(date)] Deleted old backup: ${FILE}"
      fi
    done
else
  echo "[$(date)] S3 not configured — backup kept locally at ${BACKUP_FILE}"
fi

# ── Cleanup local ────────────────────────────────────────────────────
find "${BACKUP_DIR}" -name "aocopilot_*.sql.gz" -mtime +3 -delete 2>/dev/null || true

echo "[$(date)] Backup complete."
