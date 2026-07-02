#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_plaintext_terminal_singleclose_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow ElevenLabs payload that:
  - switches soft filler to static plain text
  - reinforces no bracket tags anywhere
  - enforces single-close terminal behavior across not_target/refusal/callback/SMS
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_JSON="$2"
VERSION_DESCRIPTION="${3:-}"
TARGET_SOFT_TIMEOUT="${TARGET_SOFT_TIMEOUT:-2.6}"
TARGET_SOFT_MESSAGE="${TARGET_SOFT_MESSAGE:-Да...}"

if [[ ! -f "$SOURCE_JSON" ]]; then
  echo "Source file not found: $SOURCE_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSON")"

jq \
  --arg version_description "$VERSION_DESCRIPTION" \
  --argjson target_soft_timeout "$TARGET_SOFT_TIMEOUT" \
  --arg target_soft_message "$TARGET_SOFT_MESSAGE" '
  {
    conversation_config: .conversation_config,
    platform_settings: .platform_settings,
    workflow: .workflow
  }
  | del(.conversation_config.agent.prompt.tool_ids)
  | .conversation_config.turn.soft_timeout_config.timeout_seconds = $target_soft_timeout
  | .conversation_config.turn.soft_timeout_config.message = $target_soft_message
  | .conversation_config.turn.soft_timeout_config.additional_soft_timeout_messages = []
  | .conversation_config.turn.soft_timeout_config.use_llm_generated_message = false
  | .conversation_config.turn.soft_timeout_config.randomize_fillers = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nPlaintext terminal single-close override:[\\s\\S]*$"; "")
      + "\n\nPlaintext terminal single-close override:\n- Speak only plain Russian text. Never include square-bracket tags, stage directions, emotional labels, or control hints anywhere in spoken output.\n- Forbidden examples include `[calm]`, `[pause]`, `[thinking]`, `[friendly]`, `[slow]`, and any similar bracket annotation.\n- If a drafted line contains a bracket tag or stage direction, regenerate it into plain text before speaking.\n- For every terminal live-human outcome, including `not_target`, `refusal_soft`, `callback_scheduled`, `manager_call`, and successful SMS next-step, use one single-close pattern only.\n- Single-close pattern means:\n  1. silent `call_log`\n  2. one short spoken `end_call.system__message_to_speak`\n  3. stop\n- In a terminal sequence, the assistant `message` field must stay empty before `end_call`.\n- Do not produce a normal assistant speech turn after `call_log`.\n- Do not say a spoken close first and then repeat the same close inside `end_call`.\n- If you are about to call both `call_log` and `end_call`, keep all final spoken words only inside `end_call.system__message_to_speak`.\n- For clear `not_target` answers like `не работаем`, `не используем`, `это не наш профиль`, do not keep probing. Finalize immediately with the single-close pattern.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "soft_timeout: $TARGET_SOFT_TIMEOUT"
echo "soft_message: $TARGET_SOFT_MESSAGE"
echo "Added override: static plain filler + global terminal single-close"
