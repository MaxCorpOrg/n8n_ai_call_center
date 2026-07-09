#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_preopener_and_sms_singleclose_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload that fixes two confirmed runtime defects:
  - no context_fetch before the exact opener
  - SMS/call_log finalization must be single-close, with no normal speech
    after call_log

This helper does not change voice, LLM, tool bindings, workflow, or turn settings.
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
      sub("\\n\\nPre-opener and SMS single-close runtime override:[\\s\\S]*$"; "")
      + "\n\nPre-opener and SMS single-close runtime override:\n- Before the exact opener has been fully spoken, do not call `context_fetch`.\n- If the first live-human input is `алло`, `да`, `слушаю`, short noise, or another line-opening phrase, immediately say the exact opener first. Do not fetch context first, do not say `Алло...`, and do not ask a line-check before the opener.\n- `context_fetch` is allowed only after the exact opener was already delivered and the human has given a meaningful business reply that needs lead/product context.\n- For SMS consent, use this exact ordering:\n  1. Say one short immediate acknowledgement before tools: `Да, отправляю.`\n  2. Call `send_sms_info` silently.\n  3. Call `call_log` silently.\n  4. Call `end_call` with `system__message_to_speak=\"SMS отправила, хорошего дня.\"`\n  5. Stop.\n- After `send_sms_info` result, do not produce a normal assistant message unless it is before `call_log` and is strictly needed as the short acknowledgement already described.\n- After successful `call_log`, never produce a normal assistant message. The only remaining spoken words must be inside `end_call.system__message_to_speak`.\n- Forbidden SMS finalization sequence: `send_sms_info` -> `call_log` -> normal assistant message `Я уже отправила SMS...` -> `end_call`.\n- Correct SMS finalization sequence: short spoken acknowledgement before tools -> `send_sms_info` -> silent `call_log` -> spoken `end_call` -> stop.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: no pre-opener context_fetch + SMS single-close finalization"
