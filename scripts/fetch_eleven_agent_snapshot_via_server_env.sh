#!/usr/bin/env bash
set -euo pipefail

SERVER_ALIAS="${SERVER_ALIAS:-ai-core-prod-147}"
DEFAULT_AGENT_ID="agent_8801kgybyekned2a8yae6rp8hk3q"
DEFAULT_BRANCH_ID="agtbrch_3701kv7waz0teny9xvsgv7sjt0bp"

usage() {
  cat <<'EOF' >&2
Usage:
  fetch_eleven_agent_snapshot_via_server_env.sh OUTPUT_DIR [AGENT_ID] [BRANCH_ID]

What it does:
  1. Reads Eleven API key from remote .env.callcenter via SSH
  2. Downloads current agent/branch snapshot from ElevenLabs
  3. Saves response.json plus a short summary.json
EOF
  exit 1
}

if [[ $# -lt 1 || $# -gt 3 ]]; then
  usage
fi

OUTPUT_DIR="$1"
AGENT_ID="${2:-$DEFAULT_AGENT_ID}"
BRANCH_ID="${3:-$DEFAULT_BRANCH_ID}"

mkdir -p "$OUTPUT_DIR"

REMOTE_ENV_PATH="$(ssh -o BatchMode=yes "$SERVER_ALIAS" '
for p in /home/aicore/n8n-server/.env.callcenter /home/aicore/n8n-ai-clean/.env.callcenter; do
  if [ -f "$p" ]; then
    printf "%s\n" "$p"
    exit 0
  fi
done
exit 1
')"

REMOTE_KEY="$(
  ssh -o BatchMode=yes "$SERVER_ALIAS" "python3 - <<'PY'
from pathlib import Path
path = Path('$REMOTE_ENV_PATH')
for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
    s = line.strip()
    if not s or s.startswith('#') or '=' not in s:
        continue
    k, v = s.split('=', 1)
    if k.strip() in ('ELEVENLABS_API_KEY', 'ELEVEN_API_KEY'):
        print(v.strip().strip('\"').strip(\"'\"))
        break
PY
"
)"

if [[ -z "$REMOTE_KEY" ]]; then
  echo "Could not extract ElevenLabs API key from remote env" >&2
  exit 1
fi

RESPONSE_JSON="$OUTPUT_DIR/response.json"
SUMMARY_JSON="$OUTPUT_DIR/summary.json"

curl -sS \
  "https://api.elevenlabs.io/v1/convai/agents/${AGENT_ID}?branch_id=${BRANCH_ID}" \
  -H "xi-api-key: ${REMOTE_KEY}" \
  > "$RESPONSE_JSON"

if jq -e '.detail? != null' "$RESPONSE_JSON" >/dev/null 2>&1; then
  echo "ElevenLabs returned API error. Saved response: $RESPONSE_JSON" >&2
  jq '{error: .detail}' "$RESPONSE_JSON" >&2
  exit 1
fi

jq '{
  agent_id,
  branch_id,
  version_id,
  version_name,
  version_description,
  llm: .conversation_config.agent.prompt.llm,
  tts: .conversation_config.tts.model_id,
  first_message: .conversation_config.agent.first_message,
  turn_timeout: .conversation_config.turn.turn_timeout,
  soft_timeout_seconds: .conversation_config.turn.soft_timeout_config.timeout_seconds,
  tool_names: (.conversation_config.agent.prompt.tools | map(.name))
}' "$RESPONSE_JSON" > "$SUMMARY_JSON"

echo "Saved response: $RESPONSE_JSON"
echo "Saved summary: $SUMMARY_JSON"
jq '.' "$SUMMARY_JSON"
