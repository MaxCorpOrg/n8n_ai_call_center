#!/usr/bin/env bash
set -euo pipefail

SERVER_ALIAS="${SERVER_ALIAS:-ai-core-prod-147}"

usage() {
  cat <<'EOF' >&2
Usage:
  patch_eleven_tool_flags_via_server_env.sh OUTPUT_DIR TOOL_ID [TOOL_ID...]

Reads ElevenLabs API key from remote .env.callcenter via SSH, backs up each tool,
then patches selected tool_config flags directly through Eleven Tools API.

Optional environment overrides:
  TOOL_DISABLE_INTERRUPTIONS=true|false
  TOOL_PRE_TOOL_SPEECH=auto|none|<string>
  TOOL_FORCE_PRE_TOOL_SPEECH=true|false
  TOOL_CALL_SOUND=<value>|null
  TOOL_CALL_SOUND_BEHAVIOR=auto|always|never

Example:
  TOOL_DISABLE_INTERRUPTIONS=true \
  scripts/patch_eleven_tool_flags_via_server_env.sh \
    .runtime/eleven_tool_flags_patch_2026-06-26 \
    tool_5701ktec2x6wfnj8t5b1rwhtw51p
EOF
  exit 1
}

if [[ $# -lt 2 ]]; then
  usage
fi

OUTPUT_DIR="$1"
shift
TOOL_IDS=("$@")

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
  RESPONSE_JSON="$OUTPUT_DIR/${tool_id}_response.json"
  AFTER_JSON="$OUTPUT_DIR/${tool_id}_after.json"

  curl -sS \
    "https://api.elevenlabs.io/v1/convai/tools/${tool_id}" \
    -H "xi-api-key: ${REMOTE_KEY}" \
    > "$BEFORE_JSON"

  jq '
    .tool_config as $cfg
    | {
        tool_config:
          (
            $cfg
            | if env.TOOL_DISABLE_INTERRUPTIONS != null and env.TOOL_DISABLE_INTERRUPTIONS != "" then
                .disable_interruptions = (env.TOOL_DISABLE_INTERRUPTIONS == "true")
              else
                .
              end
            | if env.TOOL_PRE_TOOL_SPEECH != null and env.TOOL_PRE_TOOL_SPEECH != "" then
                .pre_tool_speech =
                  (if env.TOOL_PRE_TOOL_SPEECH == "null" then null else env.TOOL_PRE_TOOL_SPEECH end)
              else
                .
              end
            | if env.TOOL_FORCE_PRE_TOOL_SPEECH != null and env.TOOL_FORCE_PRE_TOOL_SPEECH != "" then
                .force_pre_tool_speech = (env.TOOL_FORCE_PRE_TOOL_SPEECH == "true")
              else
                .
              end
            | if env.TOOL_CALL_SOUND != null and env.TOOL_CALL_SOUND != "" then
                .tool_call_sound =
                  (if env.TOOL_CALL_SOUND == "null" then null else env.TOOL_CALL_SOUND end)
              else
                .
              end
            | if env.TOOL_CALL_SOUND_BEHAVIOR != null and env.TOOL_CALL_SOUND_BEHAVIOR != "" then
                .tool_call_sound_behavior = env.TOOL_CALL_SOUND_BEHAVIOR
              else
                .
              end
          )
      }
  ' "$BEFORE_JSON" > "$PATCH_JSON"

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
        disable_interruptions: ($before[0].tool_config.disable_interruptions // null),
        pre_tool_speech: ($before[0].tool_config.pre_tool_speech // null),
        force_pre_tool_speech: ($before[0].tool_config.force_pre_tool_speech // null),
        tool_call_sound: ($before[0].tool_config.tool_call_sound // null),
        tool_call_sound_behavior: ($before[0].tool_config.tool_call_sound_behavior // null)
      },
      after: {
        disable_interruptions: ($after[0].tool_config.disable_interruptions // null),
        pre_tool_speech: ($after[0].tool_config.pre_tool_speech // null),
        force_pre_tool_speech: ($after[0].tool_config.force_pre_tool_speech // null),
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
