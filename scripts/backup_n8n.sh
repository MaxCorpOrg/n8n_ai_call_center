#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="${PROJECT_NAME:-n8n-server}"
VOLUME_NAME="${VOLUME_NAME:-${PROJECT_NAME}_n8n_data}"
BACKUP_DIR="${BACKUP_DIR:-/home/aicore/n8n-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP="$(date +"%Y-%m-%d_%H-%M-%S")"
ARCHIVE="${BACKUP_DIR}/n8n-backup_${TIMESTAMP}.tar.gz"
LOG_FILE="${BACKUP_DIR}/backup.log"

mkdir -p "${BACKUP_DIR}"

if ! docker volume inspect "${VOLUME_NAME}" >/dev/null 2>&1; then
  echo "[$(date)] ERROR: Docker volume '${VOLUME_NAME}' not found" | tee -a "${LOG_FILE}"
  exit 1
fi

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${VOLUME_NAME}":/data:ro \
  -v "${BACKUP_DIR}":/backup \
  busybox \
  sh -c "tar czf /backup/$(basename "${ARCHIVE}") -C /data ."

find "${BACKUP_DIR}" -type f -name "n8n-backup_*.tar.gz" -mtime +"${RETENTION_DAYS}" -delete

SIZE="$(du -h "${ARCHIVE}" | cut -f1)"
echo "[$(date)] OK: ${ARCHIVE} (${SIZE})" | tee -a "${LOG_FILE}"
