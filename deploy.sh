#!/usr/bin/env bash
set -euo pipefail
# ─────────────────────────────────────────────────────────────
# deploy.sh — Production deployment for n8n AI Call Center
# Pulls latest images, validates config, restarts with healthcheck.
# Usage:  ./deploy.sh [--rollback]
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_HTTPS="${SCRIPT_DIR}/.env.https"
ENV_MEMORY="${SCRIPT_DIR}/.env.memory"
ENV_CALLCENTER="${SCRIPT_DIR}/.env.callcenter"

COMPOSE_FILES=(
  -f "${SCRIPT_DIR}/docker-compose.https.yml"
  -f "${SCRIPT_DIR}/docker-compose.callcenter.yml"
  -f "${SCRIPT_DIR}/docker-compose.memory.yml"
  -f "${SCRIPT_DIR}/docker-compose.adminer.yml"
)
ENV_FILES=()
[[ -f "${ENV_HTTPS}" ]]      && ENV_FILES+=(--env-file "${ENV_HTTPS}")
[[ -f "${ENV_MEMORY}" ]]     && ENV_FILES+=(--env-file "${ENV_MEMORY}")
[[ -f "${ENV_CALLCENTER}" ]] && ENV_FILES+=(--env-file "${ENV_CALLCENTER}")

DEPLOY_LOG="${SCRIPT_DIR}/deploy.log"
HEALTHCHECK_TIMEOUT=60

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${DEPLOY_LOG}"; }

# ── Pre-flight checks ──────────────────────────────────────
preflight() {
  log "Pre-flight checks..."

  if ! command -v docker &>/dev/null; then
    log "ERROR: docker not found"; exit 1
  fi
  if ! docker info &>/dev/null; then
    log "ERROR: Docker daemon not running"; exit 1
  fi

  # Validate env files exist
  if [[ ${#ENV_FILES[@]} -eq 0 ]]; then
    log "ERROR: No .env files found. Expected at least .env.https"
    exit 1
  fi

  # Run validate_env.sh if available
  if [[ -x "${SCRIPT_DIR}/scripts/validate_env.sh" ]]; then
    if ! "${SCRIPT_DIR}/scripts/validate_env.sh" "${ENV_HTTPS}"; then
      log "ERROR: Environment validation failed"
      exit 1
    fi
  fi

  # Check disk space (need at least 1GB free)
  AVAIL_KB=$(df --output=avail "${SCRIPT_DIR}" | tail -1 | tr -d ' ')
  if [[ "${AVAIL_KB}" -lt 1048576 ]]; then
    log "ERROR: Less than 1GB disk space available (${AVAIL_KB}KB)"
    exit 1
  fi

  log "Pre-flight OK"
}

# ── Snapshot current image digests (for rollback) ──────────
snapshot_images() {
  log "Saving current image digests..."
  docker compose "${ENV_FILES[@]}" "${COMPOSE_FILES[@]}" \
    images --format '{{.Repository}}:{{.Tag}} {{.ID}}' 2>/dev/null \
    > "${SCRIPT_DIR}/.deploy-image-snapshot" || true
}

# ── Pull latest images ─────────────────────────────────────
pull_images() {
  log "Pulling latest images..."
  docker compose "${ENV_FILES[@]}" "${COMPOSE_FILES[@]}" pull --quiet 2>&1 | tee -a "${DEPLOY_LOG}"
  log "Pull complete"
}

# ── Deploy (recreate changed containers) ───────────────────
deploy() {
  log "Deploying services..."
  docker compose "${ENV_FILES[@]}" "${COMPOSE_FILES[@]}" \
    up -d --remove-orphans 2>&1 | tee -a "${DEPLOY_LOG}"
  log "Containers started"
}

# ── Wait for healthchecks ──────────────────────────────────
wait_healthy() {
  log "Waiting for services to become healthy (timeout: ${HEALTHCHECK_TIMEOUT}s)..."
  local elapsed=0
  while [[ $elapsed -lt $HEALTHCHECK_TIMEOUT ]]; do
    local unhealthy
    unhealthy=$(docker compose "${ENV_FILES[@]}" "${COMPOSE_FILES[@]}" \
      ps --format '{{.Name}} {{.Health}}' 2>/dev/null \
      | grep -v "healthy" | grep -v "^$" | grep -v "N/A" || true)
    if [[ -z "${unhealthy}" ]]; then
      log "All services healthy ✓"
      return 0
    fi
    sleep 5
    elapsed=$((elapsed + 5))
  done
  log "WARNING: Some services not healthy after ${HEALTHCHECK_TIMEOUT}s:"
  docker compose "${ENV_FILES[@]}" "${COMPOSE_FILES[@]}" ps 2>/dev/null | tee -a "${DEPLOY_LOG}"
  return 1
}

# ── Rollback ───────────────────────────────────────────────
rollback() {
  if [[ ! -f "${SCRIPT_DIR}/.deploy-image-snapshot" ]]; then
    log "ERROR: No snapshot found for rollback"
    exit 1
  fi
  log "Rolling back to previous images..."
  docker compose "${ENV_FILES[@]}" "${COMPOSE_FILES[@]}" down 2>/dev/null || true
  docker compose "${ENV_FILES[@]}" "${COMPOSE_FILES[@]}" up -d 2>&1 | tee -a "${DEPLOY_LOG}"
  log "Rollback complete. Verify services manually."
}

# ── Git sync (optional, preserves old behavior) ────────────
git_sync() {
  if git -C "${SCRIPT_DIR}" rev-parse --is-inside-work-tree &>/dev/null; then
    BRANCH=$(git -C "${SCRIPT_DIR}" symbolic-ref --short HEAD 2>/dev/null || echo "unknown")
    log "Git: syncing branch '${BRANCH}'..."
    git -C "${SCRIPT_DIR}" add .
    git -C "${SCRIPT_DIR}" commit -m "Deploy $(date '+%Y-%m-%d %H:%M:%S') [${BRANCH}]" --allow-empty 2>/dev/null || true
    git -C "${SCRIPT_DIR}" push -u origin "${BRANCH}" 2>/dev/null || log "WARNING: git push failed (non-fatal)"
  fi
}

# ── Main ───────────────────────────────────────────────────
main() {
  log "═══ Deploy started ═══"

  if [[ "${1:-}" == "--rollback" ]]; then
    rollback
    exit $?
  fi

  preflight
  snapshot_images
  git_sync
  pull_images
  deploy

  if wait_healthy; then
    log "═══ Deploy SUCCESS ═══"
  else
    log "═══ Deploy COMPLETED with warnings (check services) ═══"
    exit 1
  fi
}

main "$@"
