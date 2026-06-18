#!/usr/bin/env bash
set -euo pipefail

SERVER_ALIAS="${SERVER_ALIAS:-ai-core-prod-147}"
REMOTE_ENV_CANDIDATES=(
  "/home/aicore/n8n-server/.env.callcenter"
  "/home/aicore/n8n-ai-clean/.env.callcenter"
)

usage() {
  cat <<'EOF' >&2
Usage:
  apply_eleven_agent_payload_via_server_env.sh PAYLOAD_JSON OUTPUT_DIR [AGENT_ID] [BRANCH_ID] [--dry-run]

Reads ElevenLabs API key from remote server `.env.callcenter` via SSH alias
and then calls local:
  scripts/apply_eleven_agent_payload.sh

Environment:
  SERVER_ALIAS   SSH alias, default: ai-core-prod-147

Example:
  scripts/apply_eleven_agent_payload_via_server_env.sh \
    .runtime/eleven_lab_llm_compare_gemini_2026-06-16/payload.json \
    .runtime/eleven_lab_llm_compare_gemini_2026-06-16/apply_result
EOF
  exit 1
}

if [[ $# -lt 2 ]]; then
  usage
fi

PAYLOAD_JSON="$1"
OUTPUT_DIR="$2"
AGENT_ID="${3:-}"
BRANCH_ID="${4:-}"
TAIL_ARG="${5:-}"

if [[ ! -f "$PAYLOAD_JSON" ]]; then
  echo "Payload file not found: $PAYLOAD_JSON" >&2
  exit 1
fi

if [[ "$AGENT_ID" == "--dry-run" ]]; then
  exec "$(dirname "$0")/apply_eleven_agent_payload.sh" "$PAYLOAD_JSON" "$OUTPUT_DIR" --dry-run
fi
if [[ "$BRANCH_ID" == "--dry-run" ]]; then
  exec "$(dirname "$0")/apply_eleven_agent_payload.sh" "$PAYLOAD_JSON" "$OUTPUT_DIR" "$AGENT_ID" --dry-run
fi
if [[ "$TAIL_ARG" == "--dry-run" ]]; then
  exec "$(dirname "$0")/apply_eleven_agent_payload.sh" "$PAYLOAD_JSON" "$OUTPUT_DIR" "$AGENT_ID" "$BRANCH_ID" --dry-run
fi

REMOTE_ENV_PATH="$(ssh -o BatchMode=yes "$SERVER_ALIAS" '
for p in /home/aicore/n8n-server/.env.callcenter /home/aicore/n8n-ai-clean/.env.callcenter; do
  if [ -f "$p" ]; then
    printf "%s\n" "$p"
    exit 0
  fi
done
exit 1
')"

if [[ -z "$REMOTE_ENV_PATH" ]]; then
  echo "Could not find remote .env.callcenter via $SERVER_ALIAS" >&2
  exit 1
fi

REMOTE_KEY="$(ssh -o BatchMode=yes "$SERVER_ALIAS" "python3 - <<'PY'
from pathlib import Path
path = Path('$REMOTE_ENV_PATH')
data = path.read_text(encoding='utf-8', errors='ignore').splitlines()
for line in data:
    s = line.strip()
    if not s or s.startswith('#') or '=' not in s:
        continue
    k, v = s.split('=', 1)
    if k.strip() in ('ELEVENLABS_API_KEY', 'ELEVEN_API_KEY'):
        print(v.strip().strip('\"').strip(\"'\"))
        break
PY
")"

if [[ -z "$REMOTE_KEY" ]]; then
  echo "Could not extract ELEVENLABS_API_KEY / ELEVEN_API_KEY from remote env file" >&2
  exit 1
fi

export ELEVENLABS_API_KEY="$REMOTE_KEY"

if [[ -n "$AGENT_ID" && -n "$BRANCH_ID" ]]; then
  exec "$(dirname "$0")/apply_eleven_agent_payload.sh" "$PAYLOAD_JSON" "$OUTPUT_DIR" "$AGENT_ID" "$BRANCH_ID"
elif [[ -n "$AGENT_ID" ]]; then
  exec "$(dirname "$0")/apply_eleven_agent_payload.sh" "$PAYLOAD_JSON" "$OUTPUT_DIR" "$AGENT_ID"
else
  exec "$(dirname "$0")/apply_eleven_agent_payload.sh" "$PAYLOAD_JSON" "$OUTPUT_DIR"
fi

