#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_terminal_meta_silence_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow ElevenLabs payload that:
  - forbids spoken leakage of internal tool-planning text
  - hardens immediate close on clear farewell / terminal refusal
  - keeps final spoken close only inside end_call
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
      sub("\\n\\nTerminal meta-silence override:[\\s\\S]*$"; "")
      + "\n\nTerminal meta-silence override:\n- Internal tool-planning text must never be spoken aloud to the user.\n- Forbidden spoken shapes include any raw planning or tool text such as: `silent_call_log`, `call_log with`, `end_call(`, parameter lists, field names, backtick-formatted instructions, or narration of what tool you are about to call.\n- If such internal wording appears in your draft response, discard it completely and stay silent instead.\n- Clear farewell phrases like `пока`, `до свидания`, `всего доброго`, `ладно, пока`, `не надо, пока`, or another direct terminal goodbye mean the live dialogue is over.\n- After a clear farewell, do not ask a new question, do not reopen qualification, and do not produce any normal assistant speech turn before backend finalization.\n- Correct order after clear farewell is:\n  1. silent `call_log`\n  2. one short spoken `end_call.system__message_to_speak`\n  3. stop\n- If the user already gave a clear terminal goodbye, keep the final spoken close very short and do not add any extra explanation.\n- A hesitant refusal like `м-м-м, нет`, `эм, нет`, `ну нет`, or `наверное, нет` is still a real refusal signal and must not be treated as empty silence or endless answer-in-progress.\n- If such a refusal is then followed by a goodbye, finalize immediately instead of returning to a new question.\n- Never answer a post-close line-check with a new mini-dialogue like `Да?` if the user has already clearly ended the call.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: terminal meta silence + clear farewell immediate finalization"
