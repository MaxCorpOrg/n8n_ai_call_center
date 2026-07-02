#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_wordfill_pause_polish_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow ElevenLabs payload that:
  - keeps the current branch behavior intact
  - replaces raw/awkward soft-timeout masking with short spoken Russian word-fillers
  - prevents service-style filler phrases during long response gaps

Optional environment overrides:
  TARGET_SOFT_TIMEOUT      default: 3.2
  TARGET_SOFT_MESSAGE      default: Да...
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_JSON="$2"
VERSION_DESCRIPTION="${3:-}"
TARGET_SOFT_TIMEOUT="${TARGET_SOFT_TIMEOUT:-3.2}"
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
  | .conversation_config.turn.soft_timeout_config.use_llm_generated_message = true
  | .conversation_config.turn.soft_timeout_config.randomize_fillers = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.turn.soft_timeout_config.llm_generated_message_prompt_override =
      "Generate one ultra-short natural Russian thinking filler only inside an already active live phone conversation and only while the assistant is preparing the real next reply. Never produce any filler before the exact opener. Never produce a line-check. Never produce a question. Never produce support-style phrases. Never use forms like Алло..., Да, я на линии..., Я на линии..., Секунду..., Момент..., Поняла..., or Сейчас.... Good shapes are only very short neutral spoken fillers such as: Да... / Угу... / Так... If no filler is clearly needed, return an empty string."
  | .conversation_config.agent.prompt.tools =
      (.conversation_config.agent.prompt.tools
       | map(
           if (.name == "context_fetch" or .name == "call_log" or .name == "send_sms_info") then
             .tool_call_sound = null
             | .tool_call_sound_behavior = "auto"
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nWord-fill pause polish override:[\\s\\S]*$"; "")
      + "\n\nWord-fill pause polish override:\n- If a slow backend or thinking pause appears during an already active live-human dialogue, you may use at most one ultra-short neutral spoken filler.\n- Allowed filler shapes are tiny natural acknowledgements like `Да...`, `Угу...`, or `Так...`.\n- Do not use filler as a line-check.\n- Do not say `Да, я на линии`, `Я на линии`, `Секунду`, `Момент`, or `Алло` as filler masking.\n- After one filler, either continue with the real answer or yield to the human; never start a side dialogue with yourself.\n"
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
echo "word-fill pause polish applied"
