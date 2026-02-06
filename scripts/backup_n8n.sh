#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-/home/aicore/n8n-server/docker-compose.ip.yml}"
BACKUP_DIR="${BACKUP_DIR:-/home/aicore/n8n-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP="$(date +"%Y-%m-%d_%H-%M-%S")"
ARCHIVE="${BACKUP_DIR}/n8n-backup_${TIMESTAMP}.tar.gz"
LOG_FILE="${BACKUP_DIR}/backup.log"

mkdir -p "${BACKUP_DIR}"

N8N_CID="$(docker compose -f "${COMPOSE_FILE}" ps -q n8n)"
if [ -z "${N8N_CID}" ]; then
  echo "[$(date)] ERROR: n8n container not found via compose file ${COMPOSE_FILE}" | tee -a "${LOG_FILE}"
  exit 1
fi

# Backup the persistent n8n data from mounted volume in n8n container.
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --volumes-from "${N8N_CID}":ro \
  -v "${BACKUP_DIR}":/backup \
  busybox \
  sh -c "tar czf /backup/$(basename "${ARCHIVE}") -C /home/node/.n8n ."

find "${BACKUP_DIR}" -type f -name "n8n-backup_*.tar.gz" -mtime +"${RETENTION_DAYS}" -delete

SIZE="$(du -h "${ARCHIVE}" | cut -f1)"
echo "[$(date)] OK: ${ARCHIVE} (${SIZE})" | tee -a "${LOG_FILE}"
