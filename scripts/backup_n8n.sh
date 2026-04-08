#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="${PROJECT_NAME:-n8n-server}"
VOLUME_NAME="${VOLUME_NAME:-${PROJECT_NAME}_n8n_data}"
BACKUP_DIR="${BACKUP_DIR:-/home/aicore/n8n-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP="$(date +"%Y-%m-%d_%H-%M-%S")"
ARCHIVE="${BACKUP_DIR}/n8n-backup_${TIMESTAMP}.tar.gz"
CHECKSUM_FILE="${ARCHIVE}.sha256"
LOG_FILE="${BACKUP_DIR}/backup.log"
LOCK_FILE="/tmp/n8n_backup.lock"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"; }

cleanup() {
  rm -f "${LOCK_FILE}"
  if [[ "${1:-}" == "error" && -f "${ARCHIVE}" ]]; then
    rm -f "${ARCHIVE}" "${CHECKSUM_FILE}"
    log "ERROR: Cleaned up incomplete backup"
  fi
}
trap 'cleanup error' ERR
trap 'cleanup' EXIT

# Prevent concurrent backups
if [[ -f "${LOCK_FILE}" ]]; then
  log "ERROR: Another backup is running (lock: ${LOCK_FILE}). Aborting."
  exit 1
fi
echo $$ > "${LOCK_FILE}"

mkdir -p "${BACKUP_DIR}"

if ! docker volume inspect "${VOLUME_NAME}" >/dev/null 2>&1; then
  log "ERROR: Docker volume '${VOLUME_NAME}' not found"
  exit 1
fi

log "START: Backing up volume '${VOLUME_NAME}'..."

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${VOLUME_NAME}":/data:ro \
  -v "${BACKUP_DIR}":/backup \
  busybox \
  sh -c "tar czf /backup/$(basename "${ARCHIVE}") -C /data ."

# Verify archive integrity
if ! tar tzf "${ARCHIVE}" >/dev/null 2>&1; then
  log "ERROR: Archive verification failed — ${ARCHIVE} is corrupt"
  rm -f "${ARCHIVE}"
  exit 1
fi

# Store checksum for future verification
sha256sum "${ARCHIVE}" > "${CHECKSUM_FILE}"

# Cleanup old backups (only after successful new backup)
find "${BACKUP_DIR}" -type f -name "n8n-backup_*.tar.gz" -mtime +"${RETENTION_DAYS}" -delete
find "${BACKUP_DIR}" -type f -name "n8n-backup_*.tar.gz.sha256" -mtime +"${RETENTION_DAYS}" -delete

FILE_COUNT=$(tar tzf "${ARCHIVE}" | wc -l)
SIZE="$(du -h "${ARCHIVE}" | cut -f1)"
log "OK: ${ARCHIVE} (${SIZE}, ${FILE_COUNT} files, checksum saved)"
