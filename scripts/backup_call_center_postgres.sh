#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/aicore/n8n-ai-clean}"
PROJECT_NAME="${PROJECT_NAME:-n8n-server}"
BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-/home/aicore/n8n-backups/postgres}"
BACKUP_SUBDIR="${BACKUP_SUBDIR:-call_center}"
BACKUP_DIR="${BACKUP_BASE_DIR}/${BACKUP_SUBDIR}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
LOG_FILE="${BACKUP_BASE_DIR}/call_center_backup.log"
LOCK_FILE="/tmp/call_center_postgres_backup.lock"
TIMESTAMP="$(date +"%Y-%m-%d_%H-%M-%S")"
ARCHIVE="${BACKUP_DIR}/call_center_${TIMESTAMP}.sql.gz"
CHECKSUM_FILE="${ARCHIVE}.sha256"

COMPOSE_FILES=(
  -f "${PROJECT_DIR}/docker-compose.https.yml"
  -f "${PROJECT_DIR}/docker-compose.callcenter.yml"
)

ENV_FILES=()
[[ -f "${PROJECT_DIR}/.env.https" ]] && ENV_FILES+=(--env-file "${PROJECT_DIR}/.env.https")
[[ -f "${PROJECT_DIR}/.env.callcenter" ]] && ENV_FILES+=(--env-file "${PROJECT_DIR}/.env.callcenter")

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"; }

cleanup() {
  rm -f "${LOCK_FILE}"
  if [[ "${1:-}" == "error" && -f "${ARCHIVE}" ]]; then
    rm -f "${ARCHIVE}" "${CHECKSUM_FILE}"
    log "ERROR: Removed incomplete dump ${ARCHIVE}"
  fi
}
trap 'cleanup error' ERR
trap 'cleanup' EXIT

if [[ -f "${LOCK_FILE}" ]]; then
  log "ERROR: Another call_center backup is already running"
  exit 1
fi
echo $$ > "${LOCK_FILE}"

mkdir -p "${BACKUP_DIR}" "${BACKUP_BASE_DIR}"

if [[ ! -d "${PROJECT_DIR}" ]]; then
  log "ERROR: PROJECT_DIR not found: ${PROJECT_DIR}"
  exit 1
fi

if [[ ${#ENV_FILES[@]} -eq 0 ]]; then
  log "ERROR: No env files found in ${PROJECT_DIR}"
  exit 1
fi

if [[ -x "${PROJECT_DIR}/scripts/validate_env.sh" ]]; then
  if ! "${PROJECT_DIR}/scripts/validate_env.sh" "${PROJECT_DIR}/.env.callcenter" >/dev/null; then
    log "ERROR: .env.callcenter validation failed"
    exit 1
  fi
fi

log "START: pg_dump call_center from ${PROJECT_DIR}"

COMPOSE_PROJECT_NAME="${PROJECT_NAME}" docker compose \
  "${ENV_FILES[@]}" \
  "${COMPOSE_FILES[@]}" \
  exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-call_center}" -d "${POSTGRES_DB:-call_center}" \
  | gzip -c > "${ARCHIVE}"

if ! gzip -t "${ARCHIVE}" >/dev/null 2>&1; then
  log "ERROR: Gzip verification failed for ${ARCHIVE}"
  exit 1
fi

sha256sum "${ARCHIVE}" > "${CHECKSUM_FILE}"

find "${BACKUP_DIR}" -type f -name "call_center_*.sql.gz" -mtime +"${RETENTION_DAYS}" -delete
find "${BACKUP_DIR}" -type f -name "call_center_*.sql.gz.sha256" -mtime +"${RETENTION_DAYS}" -delete

SIZE="$(du -h "${ARCHIVE}" | cut -f1)"
log "OK: ${ARCHIVE} (${SIZE}, checksum saved)"
