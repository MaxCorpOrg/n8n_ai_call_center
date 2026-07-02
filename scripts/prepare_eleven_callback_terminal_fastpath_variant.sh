#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_callback_terminal_fastpath_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow ElevenLabs payload that:
  - hardens explicit manager-callback terminal handling
  - prevents filler/normal speech before call_log on callback close
  - keeps the final spoken close only inside end_call
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
      sub("\\n\\nCallback terminal fast-path override:[\\s\\S]*$"; "")
      + "\n\nCallback terminal fast-path override:\n- If the user explicitly asks for a manager callback or agrees that the manager should call back, treat that as a terminal next-step decision immediately.\n- Examples include phrases like: `пусть перезвонит менеджер`, `передайте менеджеру`, `да, пусть менеджер свяжется`, `можно, чтобы менеджер перезвонил`, `перезвоните потом`.\n- Once explicit callback consent is present, do not keep thinking out loud, do not stall, and do not start a new explanatory turn.\n- In this callback-finalization window, do not say filler words like `Так...`, `Угу...`, `Да...`, or another thinking sound before backend work.\n- Correct order after explicit callback consent is:\n  1. silent `call_log(callback_scheduled or manager_call as appropriate)`\n  2. one short spoken `end_call.system__message_to_speak`\n  3. stop\n- Do not produce a normal assistant message before `call_log`.\n- Do not produce a second normal assistant message after `call_log`.\n- The only spoken close in this callback-finalization sequence must live inside `end_call.system__message_to_speak`.\n- Good callback close shape inside `end_call` is short and concrete, for example: `Поняла, организую перезвон менеджера. Хорошего дня.`\n- If the user has already clearly chosen callback, do not ask another question and do not offer parallel options like SMS again.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: callback terminal fast-path with single end_call close"
