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
  patch_eleven_tool_call_sounds_via_server_env.sh OUTPUT_DIR TOOL_ID [TOOL_ID...]

Reads ElevenLabs API key from remote .env.callcenter via SSH, backs up each tool,
then patches:
  tool_call_sound = ${TOOL_CALL_SOUND:-typing}
  tool_call_sound_behavior = ${TOOL_CALL_SOUND_BEHAVIOR:-always}

Example:
  scripts/patch_eleven_tool_call_sounds_via_server_env.sh \
    .runtime/eleven_tool_sound_patch_2026-06-18 \
    tool_1601km62rxpqegqr52m9gk9sftr3 \
    tool_5701ktec2x6wfnj8t5b1rwhtw51p \
    tool_1701km86jmcpek4rj2j1rbhxqtfr
EOF
  exit 1
}

if [[ $# -lt 2 ]]; then
  usage
fi

OUTPUT_DIR="$1"
shift
TOOL_IDS=("$@")
TOOL_CALL_SOUND="${TOOL_CALL_SOUND:-typing}"
TOOL_CALL_SOUND_BEHAVIOR="${TOOL_CALL_SOUND_BEHAVIOR:-always}"

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

if [[ -z "$REMOTE_ENV_PATH" ]]; then
  echo "Could not find remote .env.callcenter via $SERVER_ALIAS" >&2
  exit 1
fi

REMOTE_KEY="$(ssh -o BatchMode=yes "$SERVER_ALIAS" "python3 - <<'PY'
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
")"

if [[ -z "$REMOTE_KEY" ]]; then
  echo "Could not extract ElevenLabs API key from $REMOTE_ENV_PATH" >&2
  exit 1
fi

SUMMARY_JSON="$OUTPUT_DIR/summary.json"
printf '[]\n' > "$SUMMARY_JSON"

for tool_id in "${TOOL_IDS[@]}"; do
  BEFORE_JSON="$OUTPUT_DIR/${tool_id}_before.json"
  PATCH_JSON="$OUTPUT_DIR/${tool_id}_patch.json"
  AFTER_JSON="$OUTPUT_DIR/${tool_id}_after.json"
  RESPONSE_JSON="$OUTPUT_DIR/${tool_id}_response.json"

  curl -sS \
    "https://api.elevenlabs.io/v1/convai/tools/${tool_id}" \
    -H "xi-api-key: ${REMOTE_KEY}" \
    > "$BEFORE_JSON"

  jq '
    {
      tool_config:
        (.tool_config
         | .tool_call_sound = $tool_call_sound
         | .tool_call_sound_behavior = $tool_call_sound_behavior)
    }
  ' \
    --arg tool_call_sound "$TOOL_CALL_SOUND" \
    --arg tool_call_sound_behavior "$TOOL_CALL_SOUND_BEHAVIOR" \
    "$BEFORE_JSON" > "$PATCH_JSON"

  curl -sS -X PATCH \
    "https://api.elevenlabs.io/v1/convai/tools/${tool_id}" \
    -H "xi-api-key: ${REMOTE_KEY}" \
    -H "Content-Type: application/json" \
    --data @"$PATCH_JSON" \
    > "$RESPONSE_JSON"

  curl -sS \
    "https://api.elevenlabs.io/v1/convai/tools/${tool_id}" \
    -H "xi-api-key: ${REMOTE_KEY}" \
    > "$AFTER_JSON"

  jq \
    --arg tool_id "$tool_id" \
    '. + [{
      tool_id: $tool_id,
      name: ($after[0].tool_config.name // $before[0].tool_config.name // ""),
      before: {
        tool_call_sound: ($before[0].tool_config.tool_call_sound // null),
        tool_call_sound_behavior: ($before[0].tool_config.tool_call_sound_behavior // null)
      },
      after: {
        tool_call_sound: ($after[0].tool_config.tool_call_sound // null),
        tool_call_sound_behavior: ($after[0].tool_config.tool_call_sound_behavior // null)
      }
    }]' \
    --slurpfile before "$BEFORE_JSON" \
    --slurpfile after "$AFTER_JSON" \
    "$SUMMARY_JSON" \
    > "$SUMMARY_JSON.tmp"
  mv "$SUMMARY_JSON.tmp" "$SUMMARY_JSON"
done

jq '.' "$SUMMARY_JSON"
