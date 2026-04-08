#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 /path/to/n8n-backup_YYYY-MM-DD_HH-MM-SS.tar.gz"
  exit 1
fi

ARCHIVE_PATH="$1"
PROJECT_NAME="${PROJECT_NAME:-n8n-server}"
VOLUME_NAME="${VOLUME_NAME:-${PROJECT_NAME}_n8n_data}"
COMPOSE_FILE="${COMPOSE_FILE:-/home/aicore/n8n-server/docker-compose.https.yml}"
ENV_FILE="${ENV_FILE:-/home/aicore/n8n-server/.env.https}"
BACKUP_DIR="${BACKUP_DIR:-/home/aicore/n8n-backups}"
LOCK_FILE="/tmp/n8n_restore.lock"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

cleanup() {
  rm -f "${LOCK_FILE}"
}
trap 'cleanup' EXIT

# Prevent concurrent restores
if [[ -f "${LOCK_FILE}" ]]; then
  log "ERROR: Another restore is running (lock: ${LOCK_FILE}). Aborting."
  exit 1
fi
echo $$ > "${LOCK_FILE}"

# --- Pre-flight validation (BEFORE stopping anything) ---
if [ ! -f "${ARCHIVE_PATH}" ]; then
  log "ERROR: Archive not found: ${ARCHIVE_PATH}"
  exit 1
fi

if ! tar tzf "${ARCHIVE_PATH}" >/dev/null 2>&1; then
  log "ERROR: Archive is corrupt or unreadable: ${ARCHIVE_PATH}"
  exit 1
fi

# Verify checksum if .sha256 file exists
CHECKSUM_FILE="${ARCHIVE_PATH}.sha256"
if [ -f "${CHECKSUM_FILE}" ]; then
  if ! sha256sum --check --quiet "${CHECKSUM_FILE}" 2>/dev/null; then
    log "ERROR: Checksum mismatch for ${ARCHIVE_PATH}. Archive may be tampered."
    exit 1
  fi
  log "OK: Checksum verified"
fi

if ! docker volume inspect "${VOLUME_NAME}" >/dev/null 2>&1; then
  log "ERROR: Docker volume '${VOLUME_NAME}' not found"
  exit 1
fi

ARCHIVE_DIR="$(dirname "${ARCHIVE_PATH}")"
ARCHIVE_FILE="$(basename "${ARCHIVE_PATH}")"

# --- Pre-restore backup of current state ---
PRE_RESTORE_BACKUP="${BACKUP_DIR}/n8n-pre-restore_$(date +%Y-%m-%d_%H-%M-%S).tar.gz"
log "Creating pre-restore backup: ${PRE_RESTORE_BACKUP}"
mkdir -p "${BACKUP_DIR}"
if docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${VOLUME_NAME}":/data:ro \
  -v "${BACKUP_DIR}":/backup \
  busybox \
  sh -c "tar czf /backup/$(basename "${PRE_RESTORE_BACKUP}") -C /data ."; then
  log "OK: Pre-restore backup saved"
else
  log "WARNING: Pre-restore backup failed (volume may be empty). Continuing."
fi

# --- Stop n8n, restore, restart ---
log "Stopping n8n service..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" stop n8n

log "Restoring archive ${ARCHIVE_FILE} into volume ${VOLUME_NAME}..."
if ! docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${VOLUME_NAME}":/data \
  -v "${ARCHIVE_DIR}":/backup:ro \
  busybox \
  sh -c "rm -rf /data/* /data/.[!.]* /data/..?* 2>/dev/null || true; tar xzf /backup/${ARCHIVE_FILE} -C /data"; then
  log "ERROR: Restore failed! Attempting rollback from pre-restore backup..."
  if [ -f "${PRE_RESTORE_BACKUP}" ]; then
    docker run --rm \
      --user "$(id -u):$(id -g)" \
      -v "${VOLUME_NAME}":/data \
      -v "${BACKUP_DIR}":/backup:ro \
      busybox \
      sh -c "rm -rf /data/* /data/.[!.]* /data/..?* 2>/dev/null || true; tar xzf /backup/$(basename "${PRE_RESTORE_BACKUP}") -C /data"
    log "Rollback applied. Starting n8n with previous data..."
  fi
  docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d n8n
  exit 1
fi

log "Starting n8n service..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d n8n

# Verify n8n came up
sleep 5
if docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps n8n 2>/dev/null | grep -q "Up"; then
  log "OK: Restore completed successfully. Pre-restore backup: ${PRE_RESTORE_BACKUP}"
else
  log "WARNING: n8n may not be fully up yet. Check: docker compose ps"
fi
