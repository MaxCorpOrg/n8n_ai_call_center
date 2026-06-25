#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_terminal_finalization_gate_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload that hardens the terminal finalization window:
  - no normal assistant speech after call_log
  - no helpdesk tails after final refusal / not_target
  - trailing silence/noise does not reopen the dialogue
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
             .description = ((.description // "")
               + " For terminal outcomes like not_target, refusal_soft, no_answer, busy, or completed SMS wrap-up, call this silently and do not reopen the dialogue afterwards.")
           elif .name == "end_call" then
             .description = "Internal end-call tool. For any terminal outcome, first complete silent call_log, then place the one and only final spoken close only into end_call.system__message_to_speak, then stop. Never produce a normal assistant reply after call_log. Never add helpdesk tails like `Могу ли я ещё чем-то помочь?`."
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nTerminal finalization gate override:[\\s\\S]*$"; "")
      + "\n\nTerminal finalization gate override:\n- A clear final outcome like `not_target`, `refusal_soft`, `no_answer`, `busy`, machine-stop, or completed SMS/callback wrap-up closes the conversation state immediately.\n- After such a final outcome is clear, your next action must be backend finalization, not another normal assistant turn.\n- Correct order is exactly:\n  1. silent `call_log`\n  2. one short spoken `end_call.system__message_to_speak`\n  3. stop\n- After `call_log`, never produce a normal assistant message.\n- After `call_log`, the only allowed spoken text is the one final close inside `end_call.system__message_to_speak`.\n- Do not ask helpdesk or support tails such as `Могу ли я ещё чем-то помочь?`, `Могу чем-то ещё помочь?`, `Чем-то ещё помочь?`, or similar after a terminal outbound outcome.\n- If the user already clearly refused or said they do not work with the product, trailing `...`, silence, rustling, cut-off fragments, repeated goodbye, or line-noise do not reopen the dialogue.\n- In that case do not clarify again, do not re-check the line, and do not ask a new question. Finish the close only.\n- If you have already said a normal close by mistake, do not continue the dialogue. Move straight to finalization and do not add more spoken turns.\n- A terminal `not_target` or refusal must not end with a support-style offer of more help.\n\nTerminal examples override:\n- Correct `not_target` example:\n  1. user: `Нет, не работаем.`\n  2. assistant: silent `call_log(not_target)`\n  3. assistant: `end_call(system__message_to_speak=\"Поняла, спасибо. Хорошего дня.\")`\n- Forbidden `not_target` example:\n  1. assistant: `Поняла, спасибо. Хорошего дня.`\n  2. user: `...`\n  3. assistant: `Вы ещё на линии?`\n  4. assistant: `Поняла, закрываю разговор.`\n  5. assistant: `call_log(not_target)`\n  6. assistant: `Могу ли я ещё чем-то помочь?`\n- Forbidden post-call_log example:\n  1. assistant: silent `call_log(not_target)`\n  2. assistant: `Я уже зафиксировала... Могу ли я ещё чем-то помочь?`\n- Correct post-call_log example:\n  1. assistant: silent `call_log(not_target)`\n  2. assistant: one short `end_call` close only\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added only: terminal finalization gate override"
