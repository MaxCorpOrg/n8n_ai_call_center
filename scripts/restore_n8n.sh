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

if [ ! -f "${ARCHIVE_PATH}" ]; then
  echo "ERROR: Archive not found: ${ARCHIVE_PATH}"
  exit 1
fi

if ! docker volume inspect "${VOLUME_NAME}" >/dev/null 2>&1; then
  echo "ERROR: Docker volume '${VOLUME_NAME}' not found"
  exit 1
fi

ARCHIVE_DIR="$(dirname "${ARCHIVE_PATH}")"
ARCHIVE_FILE="$(basename "${ARCHIVE_PATH}")"

echo "Stopping n8n service..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" stop n8n

echo "Restoring archive ${ARCHIVE_FILE} into volume ${VOLUME_NAME}..."
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${VOLUME_NAME}":/data \
  -v "${ARCHIVE_DIR}":/backup:ro \
  busybox \
  sh -c "rm -rf /data/* /data/.[!.]* /data/..?* 2>/dev/null || true; tar xzf /backup/${ARCHIVE_FILE} -C /data"

echo "Starting n8n service..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d n8n

echo "Restore completed successfully."
