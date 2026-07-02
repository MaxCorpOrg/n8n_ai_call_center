#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_post_sms_finalization_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow prompt-only payload that:
  - hardens the post-SMS finalization path
  - prevents extra normal assistant speech before call_log/end_call
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
      sub("\\n\\nPost-SMS finalization override:[\\s\\S]*$"; "")
      + "\n\nPost-SMS finalization override:\n- Once `send_sms_info` succeeds, the conversation is already in terminal wrap-up mode.\n- After successful `send_sms_info`, do not emit a separate normal assistant confirmation before backend finalization.\n- Correct order after SMS success is exactly:\n  1. silent `call_log(send_kp_pending_callback)`\n  2. one short spoken `end_call.system__message_to_speak`\n  3. stop\n- The one allowed spoken close after SMS success must live only inside `end_call.system__message_to_speak`.\n- Forbidden sequence after SMS success:\n  1. normal assistant message like `Информацию отправила в SMS...`\n  2. then silent `call_log`\n  3. then another spoken close in `end_call`\n- If the user says `спасибо`, `хорошо`, `буду ждать`, `всего доброго`, or another closing acknowledgment after SMS agreement or while SMS finalization is in progress, do not reopen the dialogue and do not add a new normal assistant turn.\n- In that case continue straight through silent `call_log` and one short `end_call` close only.\n- If the user asks one last direct clarification tied only to the SMS itself, answer in one very short sentence and then immediately return to silent `call_log` -> one short `end_call` close.\n- Do not add extra support tails like `Если появятся вопросы — пишите или звоните.` as a separate normal assistant message before `call_log`.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: post-SMS finalization via call_log -> end_call only"
