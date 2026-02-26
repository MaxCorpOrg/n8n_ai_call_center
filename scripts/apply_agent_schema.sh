#!/usr/bin/env bash
set -euo pipefail

# Применяет SQL-схему агента к работающему postgres контейнеру из docker compose.
# По умолчанию: postgres_memory + .env.https + .env.memory

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DB_SERVICE="${AGENT_DB_SERVICE:-postgres_memory}"
DB_NAME="${AGENT_DB_NAME:-${POSTGRES_MEMORY_DB:-n8n_memory}}"
DB_USER="${AGENT_DB_USER:-${POSTGRES_MEMORY_USER:-n8n_memory}}"

ENV_ARGS=()
if [[ -f .env.https ]]; then ENV_ARGS+=(--env-file .env.https); fi
if [[ -f .env.memory ]]; then ENV_ARGS+=(--env-file .env.memory); fi
if [[ -f .env.callcenter ]]; then ENV_ARGS+=(--env-file .env.callcenter); fi

if [[ ${#ENV_ARGS[@]} -eq 0 ]]; then
  echo "[ERR] Не найден ни один env-файл (.env.https/.env.memory/.env.callcenter)."
  exit 1
fi

echo "[INFO] Применяем 003_call_agent_pro.sql -> service=${DB_SERVICE}, db=${DB_NAME}, user=${DB_USER}"
docker compose "${ENV_ARGS[@]}" exec -T "$DB_SERVICE" \
  psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" < sql/003_call_agent_pro.sql

echo "[INFO] Применяем 004_seed_lipolong.sql -> service=${DB_SERVICE}, db=${DB_NAME}, user=${DB_USER}"
docker compose "${ENV_ARGS[@]}" exec -T "$DB_SERVICE" \
  psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" < sql/004_seed_lipolong.sql

echo "[INFO] Применяем 005_seed_lipolong_kb_pack.sql -> service=${DB_SERVICE}, db=${DB_NAME}, user=${DB_USER}"
docker compose "${ENV_ARGS[@]}" exec -T "$DB_SERVICE" \
  psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" < sql/005_seed_lipolong_kb_pack.sql

echo "[OK] Схема и seed (включая KB pack) применены."
