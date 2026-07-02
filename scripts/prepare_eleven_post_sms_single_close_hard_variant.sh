#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_post_sms_single_close_hard_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow prompt-only payload that:
  - hard-bans normal assistant speech after call_log on SMS success
  - forces exactly one spoken close inside end_call only
  - keeps the rest of the current branch configuration intact
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_JSON="$2"
VERSION_DESCRIPTION="${3:-}"

if [[ ! -f "$SOURCE_JSON" ]]; then
  echo "Source file not found: $SOURCE_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSON")"

jq \
  --arg version_description "$VERSION_DESCRIPTION" '
  {
    conversation_config: .conversation_config,
    platform_settings: .platform_settings,
    workflow: .workflow
  }
  | del(.conversation_config.agent.prompt.tool_ids)
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nPost-SMS single-close hard override:[\\s\\S]*$"; "")
      + "\n\nPost-SMS single-close hard override:\n- On successful SMS sending, the final spoken sentence must exist exactly once and only inside `end_call.system__message_to_speak`.\n- After `send_sms_info` succeeds and after `call_log` succeeds, your normal assistant message must stay completely silent.\n- In that post-SMS finalization window, the assistant `message` field should be empty and the next spoken words must come only from `end_call.system__message_to_speak`.\n- Forbidden SMS finalization sequence:\n  1. `send_sms_info` succeeds\n  2. silent `call_log`\n  3. normal assistant message: `Я уже отправила SMS на этот номер. Хорошего дня.`\n  4. `end_call(system__message_to_speak=\"Я уже отправила SMS на этот номер. Хорошего дня.\")`\n- Correct SMS finalization sequence:\n  1. `send_sms_info` succeeds\n  2. silent `call_log`\n  3. `end_call(system__message_to_speak=\"Я уже отправила SMS на этот номер. Хорошего дня.\")`\n  4. stop\n- If you are about to call `end_call`, do not surface the same close as a normal assistant turn first.\n- After `call_log` on SMS success, the only allowed spoken close is the one inside `end_call`.\n- If you internally formulate a close before `end_call`, discard it and keep it silent.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: post-SMS close only inside end_call"
