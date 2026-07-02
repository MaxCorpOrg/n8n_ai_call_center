#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_refusal_tool_guard_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow payload that hardens only:
  - refusal finalization through call_log/end_call tool descriptions
  - system-bound conversation id handling in call_log drafts
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
             .description = "Внутренний tool фиксации итога звонка в Google Sheet через n8n. Пользователю не рассказывай про этот tool и не проговаривай его действие вслух. Для короткого ясного отказа или другого уже терминального исхода сначала используй call_log, а уже потом завершай звонок через end_call. Поля conversation_id и eleven_conv_id уже привязаны системой: не печатай их вручную, не выдумывай conv_* значения и не подставляй placeholder. Если не уверен, оставь эти поля системе."
           elif .name == "end_call" then
             .description = "Internal end-call tool. В терминальном отказе, not_target, no_answer, busy, machine-stop или другом уже финальном исходе единственная финальная реплика должна жить только внутри end_call.system__message_to_speak. Не говори обычное прощание отдельным assistant message до end_call и не повторяй то же самое после call_log."
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nRefusal tool guard override:[\\s\\S]*$"; "")
      + "\n\nRefusal tool guard override:\n- For a short clear terminal refusal like `нет`, `нет-нет`, `не интересно`, or `не надо`, your close sequence must stay tool-driven and compact.\n- Correct order is:\n  1. call_log\n  2. one end_call close\n  3. stop\n- Do not speak an ordinary assistant farewell between call_log and end_call.\n- Do not manually type placeholder conversation ids like `conv_abcdef...` in call_log drafts.\n- Let the system-bound id fields fill automatically.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Hardened tool descriptions: call_log, end_call"
echo "Added narrow refusal tool guard override"
