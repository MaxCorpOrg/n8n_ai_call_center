#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_single_close_binding_prompt_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow prompt-only payload that:
  - forces single-close finalization on terminal refusal
  - forbids placeholder conv_* ids in drafted call_log payloads
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
      sub("\\n\\nSingle-close binding prompt override:[\\s\\S]*$"; "")
      + "\n\nSingle-close binding prompt override:\n- For a clear terminal refusal like `нет`, `нет-нет`, `не интересно`, `не надо`, or another already-final soft refusal, your final spoken close must exist only inside `end_call.system__message_to_speak`.\n- Forbidden sequence:\n  1. normal assistant message `Поняла, спасибо. Хорошего дня.`\n  2. then `end_call` repeats the same close\n- Correct sequence:\n  1. silent `call_log(refusal_soft)`\n  2. `end_call(system__message_to_speak=\"Поняла, спасибо. Хорошего дня.\")`\n  3. stop\n- After successful `call_log`, do not emit any ordinary assistant message before `end_call`.\n- For terminal refusal, the first and only spoken final close of the sequence must be the `end_call` close itself.\n\nSystem-bound call_log id override:\n- In drafted `call_log` JSON, never fabricate placeholder values like `conv_abcdef1234567890`, `conv_123`, `conv_current`, or any surrogate `conv_*` string.\n- Do not manually type `conversation_id` or `eleven_conv_id` when those fields are already system-bound by schema.\n- Let the system binding fill them.\n- If you are uncertain, leave those fields out of the drafted payload instead of inventing a value.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added overrides: single-close refusal, no placeholder conv ids"
