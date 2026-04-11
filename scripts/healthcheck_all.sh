#!/usr/bin/env bash
set -euo pipefail
# ─────────────────────────────────────────────────────────────
# healthcheck_all.sh — Check all Docker services health
# Usage:  ./scripts/healthcheck_all.sh [--env-file .env.https]
# Exit 0 = all OK, Exit 1 = at least one problem
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

PROBLEMS=0

green()  { echo -e "\033[0;32m✓ $1\033[0m"; }
red()    { echo -e "\033[0;31m✗ $1\033[0m"; }
yellow() { echo -e "\033[0;33m⚠ $1\033[0m"; }

check_docker() {
  if ! docker info &>/dev/null; then
    red "Docker daemon not running"
    exit 1
  fi
  green "Docker daemon running"
}

check_containers() {
  echo ""
  echo "Docker containers:"
  echo "─────────────────────────────────────────"

  local containers
  containers=$(docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || true)

  if [[ -z "${containers}" ]]; then
    yellow "No running containers found"
    PROBLEMS=$((PROBLEMS + 1))
    return
  fi

  while IFS=$'\t' read -r name status ports; do
    if echo "${status}" | grep -qi "unhealthy"; then
      red "${name}: ${status}"
      PROBLEMS=$((PROBLEMS + 1))
    elif echo "${status}" | grep -qi "healthy"; then
      green "${name}: ${status}"
    elif echo "${status}" | grep -qi "starting"; then
      yellow "${name}: ${status} (still starting)"
    else
      green "${name}: ${status}"
    fi
  done <<< "${containers}"
}

check_redis() {
  echo ""
  echo "Redis:"
  echo "─────────────────────────────────────────"

  local redis_container
  redis_container=$(docker ps --filter "name=redis" --format '{{.Names}}' 2>/dev/null | head -1)
  if [[ -z "${redis_container}" ]]; then
    yellow "Redis container not found (may be expected)"
    return
  fi

  if docker exec "${redis_container}" redis-cli ping 2>/dev/null | grep -q "PONG"; then
    local info
    info=$(docker exec "${redis_container}" redis-cli info memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
    green "Redis PONG (memory: ${info:-unknown})"
  else
    red "Redis not responding"
    PROBLEMS=$((PROBLEMS + 1))
  fi
}

check_postgres() {
  echo ""
  echo "PostgreSQL:"
  echo "─────────────────────────────────────────"

  local pg_containers
  pg_containers=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E '(^|-)postgres(-|$)|(^|-)postgres_memory(-|$)' || true)

  for pg_container in ${pg_containers}; do
    if docker exec "${pg_container}" pg_isready 2>/dev/null | grep -q "accepting"; then
      green "${pg_container}: accepting connections"
    else
      red "${pg_container}: not ready"
      PROBLEMS=$((PROBLEMS + 1))
    fi
  done
}

check_disk() {
  echo ""
  echo "Disk space:"
  echo "─────────────────────────────────────────"

  local usage_pct
  usage_pct=$(df --output=pcent "${PROJECT_DIR}" | tail -1 | tr -d ' %')
  if [[ "${usage_pct}" -gt 90 ]]; then
    red "Disk ${usage_pct}% full — CRITICAL"
    PROBLEMS=$((PROBLEMS + 1))
  elif [[ "${usage_pct}" -gt 80 ]]; then
    yellow "Disk ${usage_pct}% full — getting full"
    PROBLEMS=$((PROBLEMS + 1))
  else
    green "Disk ${usage_pct}% used"
  fi

  # Docker volume sizes
  local docker_usage
  docker_usage=$(docker system df --format '{{.Type}}\t{{.Size}}\t{{.Reclaimable}}' 2>/dev/null || true)
  if [[ -n "${docker_usage}" ]]; then
    echo "  Docker usage:"
    echo "${docker_usage}" | while IFS=$'\t' read -r type size reclaim; do
      echo "    ${type}: ${size} (reclaimable: ${reclaim})"
    done
  fi
}

check_n8n_health() {
  echo ""
  echo "n8n:"
  echo "─────────────────────────────────────────"

  local n8n_container
  n8n_container=$(docker ps --filter "name=n8n" --format '{{.Names}}' 2>/dev/null | head -1)
  if [[ -z "${n8n_container}" ]]; then
    yellow "n8n container not found"
    return
  fi

  local health_status
  health_status=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${n8n_container}" 2>/dev/null || echo "unknown")

  if [[ "${health_status}" == "healthy" ]]; then
    green "n8n container health: healthy"
    return
  fi

  if docker exec "${n8n_container}" sh -lc '
    if command -v wget >/dev/null 2>&1; then
      wget -qO- http://127.0.0.1:5678 >/dev/null 2>&1
    elif command -v curl >/dev/null 2>&1; then
      curl -fsS http://127.0.0.1:5678 >/dev/null 2>&1
    else
      exit 1
    fi
  ' 2>/dev/null; then
    green "n8n HTTP responding"
  else
    red "n8n HTTP not responding"
    PROBLEMS=$((PROBLEMS + 1))
  fi
}

# ── Main ───────────────────────────────────────────────────
echo "═══ Service Health Check ═══"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

check_docker
check_containers
check_redis
check_postgres
check_n8n_health
check_disk

echo ""
echo "─────────────────────────────────────────"
if [[ ${PROBLEMS} -gt 0 ]]; then
  red "PROBLEMS FOUND: ${PROBLEMS}"
  exit 1
else
  green "ALL CHECKS PASSED"
  exit 0
fi
