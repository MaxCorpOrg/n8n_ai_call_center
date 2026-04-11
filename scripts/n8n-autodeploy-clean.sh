#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/aicore/n8n-ai-clean}"
PROJECT_NAME="${PROJECT_NAME:-n8n-server}"
LOG_FILE="${LOG_FILE:-/var/log/n8n-autodeploy-clean.log}"
LOCK_FILE="${LOCK_FILE:-/tmp/n8n-autodeploy-clean.lock}"

exec >>"$LOG_FILE" 2>&1

log() { echo "=== $(date '+%F %T') $1 ==="; }

if [ -f "$LOCK_FILE" ]; then
  log "lock exists: $LOCK_FILE"
  exit 0
fi

trap 'rm -f "$LOCK_FILE"' EXIT
touch "$LOCK_FILE"

if [[ ! -d "$PROJECT_DIR" ]]; then
  log "missing project dir: $PROJECT_DIR"
  exit 1
fi

cd "$PROJECT_DIR"
log "autodeploy start"

for required in .env.https .env.memory .env.callcenter docker-compose.https.yml docker-compose.callcenter.yml docker-compose.memory.yml docker-compose.adminer.yml; do
  if [[ ! -f "$required" ]]; then
    log "missing required file: $required"
    exit 1
  fi
done

if [[ -x "./scripts/validate_env.sh" ]]; then
  ./scripts/validate_env.sh .env.https .env.memory .env.callcenter
fi

git fetch origin main
LOCAL="$(git rev-parse HEAD)"
REMOTE="$(git rev-parse origin/main)"

if [ "$LOCAL" = "$REMOTE" ]; then
  log "no changes"
  exit 0
fi

log "update: $LOCAL -> $REMOTE"
git pull --ff-only origin main

COMPOSE_PROJECT_NAME="$PROJECT_NAME" docker compose \
  --env-file .env.https \
  --env-file .env.memory \
  --env-file .env.callcenter \
  -f docker-compose.https.yml \
  -f docker-compose.callcenter.yml \
  -f docker-compose.memory.yml \
  -f docker-compose.adminer.yml \
  pull

COMPOSE_PROJECT_NAME="$PROJECT_NAME" docker compose \
  --env-file .env.https \
  --env-file .env.memory \
  --env-file .env.callcenter \
  -f docker-compose.https.yml \
  -f docker-compose.callcenter.yml \
  -f docker-compose.memory.yml \
  -f docker-compose.adminer.yml \
  up -d --remove-orphans

if [ -f "$PROJECT_DIR/sql/006_observability.sql" ]; then
  docker exec -i "${PROJECT_NAME}-postgres-1" \
    psql -U call_center -d call_center \
    < "$PROJECT_DIR/sql/006_observability.sql" || true
fi

if [[ -x "./scripts/healthcheck_all.sh" ]]; then
  ./scripts/healthcheck_all.sh
fi

docker ps --format 'table {{.Names}}\t{{.Status}}'
log "autodeploy done"
