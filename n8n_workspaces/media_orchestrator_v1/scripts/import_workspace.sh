#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -z "${N8N_BASE_URL:-}" || -z "${N8N_API_KEY:-}" ]]; then
  echo "ERROR: set N8N_BASE_URL and N8N_API_KEY env vars"
  exit 1
fi

api() {
  local method="$1"
  local path="$2"
  local data_file="${3:-}"
  if [[ -n "$data_file" ]]; then
    curl -sS -X "$method" "${N8N_BASE_URL}${path}" \
      -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
      -H 'Content-Type: application/json' \
      --data-binary "@$data_file"
  else
    curl -sS -X "$method" "${N8N_BASE_URL}${path}" \
      -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
      -H 'Content-Type: application/json'
  fi
}

A2_FILE="$ROOT_DIR/workflows/portable_no_credentials/KeKhk230Zy3Iz0a4.portable.json"
A3_FILE="$ROOT_DIR/workflows/portable_no_credentials/KFWMYCaEpWAdVIn3.portable.json"
A4_FILE="$ROOT_DIR/workflows/portable_no_credentials/DUJBo0tvHA5qIafi.portable.json"
A5_FILE="$ROOT_DIR/workflows/portable_no_credentials/LG1KGfhnNCICjNra.portable.json"
R_FILE="$ROOT_DIR/workflows/portable_no_credentials/ABnHZb9Ee2YOtfr2.portable.json"
KB_FILE="$ROOT_DIR/workflows/portable_no_credentials/K5es5hBE05LEeB1j.portable.json"
M_FILE="$ROOT_DIR/workflows/portable_no_credentials/C8Wmmjuv5hC425PM.portable.json"

A2_ID="$(api POST /api/v1/workflows "$A2_FILE" | jq -r '.id')"
A3_ID="$(api POST /api/v1/workflows "$A3_FILE" | jq -r '.id')"
A4_ID="$(api POST /api/v1/workflows "$A4_FILE" | jq -r '.id')"
A5_ID="$(api POST /api/v1/workflows "$A5_FILE" | jq -r '.id')"
R_ID="$(api POST /api/v1/workflows "$R_FILE" | jq -r '.id')"
KB_ID="$(api POST /api/v1/workflows "$KB_FILE" | jq -r '.id')"

echo "Imported: router=$R_ID agent2=$A2_ID agent3=$A3_ID agent4=$A4_ID agent5=$A5_ID kb_sync=$KB_ID"

TMP_MASTER="$(mktemp)"
jq \
  --arg a2 "$A2_ID" \
  --arg a3 "$A3_ID" \
  --arg a4 "$A4_ID" \
  --arg a5 "$A5_ID" \
  --arg r "$R_ID" \
  '.nodes |= map(
    if .name=="Intent Router | Tool" then .parameters.workflowId.value=$r
    elif .name=="Agent 2 | Planner" then .parameters.workflowId.value=$a2
    elif .name=="Agent 3 | Nano Banana" then .parameters.workflowId.value=$a3
    elif .name=="Agent 4 | Kling" then .parameters.workflowId.value=$a4
    elif .name=="Agent 5 | Gemini Nano Banana" then .parameters.workflowId.value=$a5
    else . end
  )' "$M_FILE" > "$TMP_MASTER"

M_ID="$(api POST /api/v1/workflows "$TMP_MASTER" | jq -r '.id')"
rm -f "$TMP_MASTER"

echo "Imported master=$M_ID"

if [[ "${ACTIVATE_MASTER:-true}" == "true" ]]; then
  api POST "/api/v1/workflows/${M_ID}/activate" >/dev/null
  echo "Master activated: $M_ID"
fi

if [[ "${ACTIVATE_KB_SYNC:-false}" == "true" ]]; then
  api POST "/api/v1/workflows/${KB_ID}/activate" >/dev/null
  echo "KB Sync activated: $KB_ID"
fi

echo "DONE"
echo "Next:"
echo "1) Assign credentials in n8n UI (Telegram + OpenAI-compatible)"
echo "2) Replace placeholders REPLACE_KLING_API_KEY / REPLACE_TAVILY_API_KEY / REPLACE_GEMINI_API_KEY"
echo "3) Set env KB_GITHUB_TOKEN for KB Sync Agent (and optional N8N_PUBLIC_API_KEY)"
