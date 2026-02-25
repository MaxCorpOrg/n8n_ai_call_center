#!/usr/bin/env bash
set -euo pipefail

# Регистрирует внешние клиентские источники в non-PII памяти.
# PII не сохраняется: в БД пишутся только client_ref + ссылка на внешний источник.
#
# Пример:
# scripts/import_leads_lipolong.sh '/home/max/AI_CORE/колл_центр_доки /Обзвон Воронин Г.П..xlsx' \
#   'gdrive://<sheet_or_file_id>'

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <xlsx_path> [external_locator]"
  exit 1
fi

XLSX_PATH="$1"
if [[ ! -f "$XLSX_PATH" ]]; then
  echo "[ERR] File not found: $XLSX_PATH"
  exit 2
fi

EXTERNAL_LOCATOR="${2:-${CLIENT_SOURCE_LOCATOR:-local://$XLSX_PATH}}"
SOURCE_SYSTEM="${CLIENT_SOURCE_SYSTEM:-manual}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TMP_CSV="$(mktemp /tmp/client_refs_XXXXXX.csv)"
trap 'rm -f "$TMP_CSV"' EXIT

python3 scripts/xlsx_leads_to_csv.py "$XLSX_PATH" "$TMP_CSV" "$EXTERNAL_LOCATOR" "$SOURCE_SYSTEM"

DB_SERVICE="${AGENT_DB_SERVICE:-postgres_memory}"
DB_NAME="${AGENT_DB_NAME:-${POSTGRES_MEMORY_DB:-n8n_memory}}"
DB_USER="${AGENT_DB_USER:-${POSTGRES_MEMORY_USER:-n8n_memory}}"

ENV_ARGS=()
if [[ -f .env.https ]]; then ENV_ARGS+=(--env-file .env.https); fi
if [[ -f .env.memory ]]; then ENV_ARGS+=(--env-file .env.memory); fi
if [[ -f .env.callcenter ]]; then ENV_ARGS+=(--env-file .env.callcenter); fi

if [[ ${#ENV_ARGS[@]} -eq 0 ]]; then
  echo "[ERR] Не найден ни один env-файл (.env.https/.env.memory/.env.callcenter)."
  exit 3
fi

CID="$(docker compose "${ENV_ARGS[@]}" ps -q "$DB_SERVICE")"
if [[ -z "$CID" ]]; then
  echo "[ERR] Контейнер сервиса $DB_SERVICE не найден. Подними стек docker compose."
  exit 4
fi

docker cp "$TMP_CSV" "$CID:/tmp/client_refs_import.csv"

docker compose "${ENV_ARGS[@]}" exec -T "$DB_SERVICE" psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" <<'SQL'
CREATE TEMP TABLE tmp_client_refs_import (
  client_ref TEXT,
  source_system TEXT,
  external_locator TEXT,
  record_key TEXT,
  tags TEXT
);

\copy tmp_client_refs_import FROM '/tmp/client_refs_import.csv' WITH (FORMAT csv, HEADER true)

INSERT INTO client_memory_refs (
  client_ref,
  primary_source_system,
  primary_locator,
  tags,
  status
)
SELECT
  client_ref,
  source_system,
  external_locator,
  CASE WHEN nullif(tags, '') IS NULL THEN ARRAY[]::TEXT[] ELSE string_to_array(tags, '|') END,
  'active'
FROM tmp_client_refs_import
ON CONFLICT (client_ref) DO UPDATE
SET
  primary_source_system = EXCLUDED.primary_source_system,
  primary_locator = EXCLUDED.primary_locator,
  tags = EXCLUDED.tags,
  status = 'active',
  updated_at = NOW();

INSERT INTO client_source_links (
  client_ref,
  external_system,
  external_locator,
  record_key,
  source_status,
  metadata
)
SELECT
  client_ref,
  source_system,
  external_locator,
  record_key,
  'active',
  jsonb_build_object('import_type', 'xlsx_ref_registry')
FROM tmp_client_refs_import
ON CONFLICT (external_system, external_locator, record_key) DO UPDATE
SET
  client_ref = EXCLUDED.client_ref,
  source_status = 'active',
  updated_at = NOW();

DROP TABLE IF EXISTS tmp_client_refs_import;
SQL

docker compose "${ENV_ARGS[@]}" exec -T "$DB_SERVICE" rm -f /tmp/client_refs_import.csv >/dev/null 2>&1 || true

echo "[OK] Референсы клиентов зарегистрированы: $XLSX_PATH"
