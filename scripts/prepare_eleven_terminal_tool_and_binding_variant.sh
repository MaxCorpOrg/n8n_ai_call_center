#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_terminal_tool_and_binding_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload that hardens:
  - terminal tool sequencing for call_log/end_call
  - system-bound conversation id handling in tool drafts
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
             .description = "Internal call outcome logging tool. For terminal outcomes like refusal_soft, not_target, no_answer, busy, machine-stop, or completed SMS wrap-up, call this silently before any final spoken close. Do not say filler before this tool in terminal mode. Do not reopen the dialogue after call_log. Do not manually fabricate conversation_id or eleven_conv_id; let system-bound fields fill them."
           elif .name == "end_call" then
             .description = "Internal end-call tool. Use it immediately after silent call_log for terminal outcomes. The one and only allowed final spoken close must live only inside end_call.system__message_to_speak. Never say filler before this tool in terminal mode. Never say the same close first as a normal assistant turn and then again in end_call. Never produce a normal assistant reply after call_log."
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nTerminal tool sequencing and binding override:[\\s\\S]*$"; "")
      + "\n\nTerminal tool sequencing and binding override:\n- For terminal outcomes such as `refusal_soft`, `not_target`, `no_answer`, `busy`, machine-stop, or completed SMS wrap-up, the close must be executed only through tools.\n- Correct order is exactly:\n  1. silent `call_log`\n  2. one short spoken `end_call.system__message_to_speak`\n  3. stop\n- Terminal mode forbids filler. Do not say `Да...`, `Так...`, `Секунду...`, `Момент...`, or any other filler before `call_log` or before `end_call` after a clear refusal/goodbye.\n- Do not speak the close as a normal assistant turn before `call_log`.\n- Do not speak the close again as a normal assistant turn after `call_log`.\n- After `call_log`, the only allowed spoken text is the single close inside `end_call.system__message_to_speak`.\n- For `refusal_soft` and `not_target`, forbidden patterns include:\n  - filler like `Да...` before `call_log`\n  - a normal `Поняла, спасибо. Хорошего дня.` turn before `call_log`\n  - then another `Поняла, спасибо. Хорошего дня.` inside `end_call`\n  - any support-style tail like `Могу ли я ещё чем-то помочь?`\n- If the user already clearly refused or said goodbye, then trailing `...`, silence, rustling, or cut-off noise do not justify any new spoken assistant turn.\n- Never manually invent, guess, or hardcode placeholder values like `conv_abcdef`, `conv_current`, `conv_123`, or similar for `call_log.conversation_id` or `call_log.eleven_conv_id`.\n- If those ids are schema-bound by the system, let the system binding fill them. Do not type a surrogate `conv_*` string yourself.\n- If you are unsure of a conversation id, do not fabricate one.\n\nTerminal refusal examples override:\n- Correct example:\n  1. user: `Нет, не интересно. До свидания.`\n  2. assistant: silent `call_log(refusal_soft)`\n  3. assistant: `end_call(system__message_to_speak=\"Поняла, спасибо. Хорошего дня.\")`\n- Forbidden example:\n  1. assistant says filler `Да...`\n  2. assistant says `Поняла, спасибо. Хорошего дня.`\n  3. assistant calls `call_log(refusal_soft)`\n  4. assistant repeats `Поняла, спасибо. Хорошего дня.` inside `end_call`\n- Forbidden tool draft example:\n  - `conversation_id: conv_abcdef1234567890`\n  - `eleven_conv_id: conv_abcdef1234567890`\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added only: terminal tool sequencing and binding override"
