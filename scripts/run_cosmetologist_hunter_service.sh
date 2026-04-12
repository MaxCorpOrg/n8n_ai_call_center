#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_DIR}"

if [[ -f "${PROJECT_DIR}/.env.cosmetologist_hunter" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${PROJECT_DIR}/.env.cosmetologist_hunter"
  set +a
fi

exec python3 scripts/cosmetologist_hunter_service.py serve \
  --host "${COSMETOLOGIST_HUNTER_HOST:-127.0.0.1}" \
  --port "${COSMETOLOGIST_HUNTER_PORT:-8787}"
