#!/usr/bin/env bash
set -euo pipefail
# ─────────────────────────────────────────────────────────────
# validate_env.sh — Validate .env files before deployment
# Usage:  ./scripts/validate_env.sh [.env.https] [.env.memory] [.env.callcenter]
#         (no args = auto-detect all .env* files in project root)
# ─────────────────────────────────────────────────────────────

ERRORS=0
WARNINGS=0

red()    { echo -e "\033[0;31m✗ $1\033[0m"; }
yellow() { echo -e "\033[0;33m⚠ $1\033[0m"; }
green()  { echo -e "\033[0;32m✓ $1\033[0m"; }

check_required() {
  local file="$1" var="$2" label="${3:-}"
  local val
  val=$(grep -E "^${var}=" "${file}" 2>/dev/null | head -1 | cut -d'=' -f2-)
  if [[ -z "${val}" ]]; then
    red "${label:-${file}}: ${var} is empty or missing (REQUIRED)"
    ERRORS=$((ERRORS + 1))
    return 1
  fi
  return 0
}

check_not_default() {
  local file="$1" var="$2" bad_value="$3"
  local val
  val=$(grep -E "^${var}=" "${file}" 2>/dev/null | head -1 | cut -d'=' -f2-)
  if [[ "${val}" == "${bad_value}" ]]; then
    yellow "${file}: ${var} still has default value '${bad_value}' — change for production!"
    WARNINGS=$((WARNINGS + 1))
  fi
}

check_min_length() {
  local file="$1" var="$2" minlen="$3"
  local val
  val=$(grep -E "^${var}=" "${file}" 2>/dev/null | head -1 | cut -d'=' -f2-)
  if [[ -n "${val}" && ${#val} -lt ${minlen} ]]; then
    yellow "${file}: ${var} is only ${#val} chars (recommended: ${minlen}+)"
    WARNINGS=$((WARNINGS + 1))
  fi
}

check_format() {
  local file="$1" var="$2" regex="$3" hint="$4"
  local val
  val=$(grep -E "^${var}=" "${file}" 2>/dev/null | head -1 | cut -d'=' -f2-)
  if [[ -n "${val}" ]] && ! echo "${val}" | grep -qE "${regex}"; then
    red "${file}: ${var}='${val}' — expected format: ${hint}"
    ERRORS=$((ERRORS + 1))
  fi
}

# ── Discover env files ─────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

if [[ $# -gt 0 ]]; then
  ENV_FILES=("$@")
else
  ENV_FILES=()
  for f in "${PROJECT_DIR}"/.env.https "${PROJECT_DIR}"/.env.memory "${PROJECT_DIR}"/.env.callcenter; do
    [[ -f "${f}" ]] && ENV_FILES+=("${f}")
  done
fi

if [[ ${#ENV_FILES[@]} -eq 0 ]]; then
  yellow "No .env files found to validate"
  exit 0
fi

echo "Validating: ${ENV_FILES[*]}"
echo "─────────────────────────────────────────"

# ── .env.https checks ─────────────────────────────────────
for f in "${ENV_FILES[@]}"; do
  if echo "${f}" | grep -q "https"; then
    check_required "${f}" "DOMAIN_NAME"
    check_required "${f}" "SSL_EMAIL"
    check_required "${f}" "N8N_ENCRYPTION_KEY"
    check_min_length "${f}" "N8N_ENCRYPTION_KEY" 16
    check_format "${f}" "SSL_EMAIL" "^[^@]+@[^@]+\.[^@]+$" "user@domain.com"
    check_format "${f}" "DOMAIN_NAME" "^[a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$" "example.com"
  fi

  # .env.memory checks
  if echo "${f}" | grep -q "memory"; then
    check_required "${f}" "POSTGRES_MEMORY_PASSWORD"
    check_not_default "${f}" "POSTGRES_MEMORY_PASSWORD" "change_me"
    check_min_length "${f}" "POSTGRES_MEMORY_PASSWORD" 12
  fi

  # .env.callcenter checks
  if echo "${f}" | grep -q "callcenter"; then
    check_required "${f}" "POSTGRES_PASSWORD"
    check_not_default "${f}" "POSTGRES_PASSWORD" "change_me_strong_password"
    check_min_length "${f}" "POSTGRES_PASSWORD" 12
  fi
done

# ── Summary ────────────────────────────────────────────────
echo "─────────────────────────────────────────"
if [[ ${ERRORS} -gt 0 ]]; then
  red "FAILED: ${ERRORS} error(s), ${WARNINGS} warning(s)"
  exit 1
elif [[ ${WARNINGS} -gt 0 ]]; then
  yellow "PASSED with ${WARNINGS} warning(s)"
  exit 0
else
  green "ALL CHECKS PASSED"
  exit 0
fi
