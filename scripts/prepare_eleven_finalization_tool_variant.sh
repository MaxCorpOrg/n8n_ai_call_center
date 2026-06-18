#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_finalization_tool_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Example:
  scripts/prepare_eleven_finalization_tool_variant.sh \
    .runtime/eleven_lab_system_binding_fix_2026-06-17/revert_to_v1/apply_result/response.json \
    .runtime/eleven_lab_finalization_tool_fix_2026-06-17/payload.json \
    "Lab: finalization tool sequencing fix"

Builds a minimal lab-only payload that:
  - keeps the current voice / LLM / turn-taking state
  - preserves prompt.tools so tool descriptions can be tightened
  - hardens call_log/end_call sequencing at the tool layer
  - adds only a narrow finalization override in the prompt
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
  | .conversation_config.agent.prompt.tools =
      (.conversation_config.agent.prompt.tools
       | map(
           if .name == "call_log" then
             .description = "Внутренний тихий tool для фиксации итога звонка в Google Sheet через n8n. Пользователю на линии про этот tool ничего не говорить. В финализации живого разговора сначала молча вызови call_log, без отдельной обычной реплики ассистента перед этим. Не произноси итог звонка вслух через обычное сообщение ассистента."
           elif .name == "end_call" then
             .description = "Internal termination tool. In a final live-human close, call it immediately after silent call_log. The one and only allowed farewell of the finalization sequence must live inside end_call.system__message_to_speak. Do not say the same farewell first as a normal assistant message and then again in end_call. Do not produce a duplicate close."
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt += "\n\nTool-layer finalization sequencing override:\n- For any final live-human close, do not speak a normal assistant close before backend finalization.\n- Final order must be:\n  1. silent `call_log`\n  2. exactly one spoken `end_call.system__message_to_speak`\n  3. stop\n- The spoken close inside `end_call` is the only allowed farewell of the finalization sequence.\n- Forbidden sequence:\n  - normal assistant says `Поняла, спасибо. Хорошего дня.`\n  - then `call_log`\n  - then `end_call` repeats the same close\n- Correct sequence:\n  - silent `call_log`\n  - `end_call(system__message_to_speak=\"Поняла, спасибо. Хорошего дня.\")`\n  - stop\n"
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Hardened tool descriptions: call_log, end_call"
echo "Added narrow finalization sequencing override"
