#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_no_tool_music_softfill_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow ElevenLabs payload that:
  - disables musical tool-call masking for webhook tools
  - enables one short spoken soft-timeout filler instead
  - keeps the rest of the current branch configuration intact

Optional environment overrides:
  SOFT_TIMEOUT_SECONDS           default: 2.4
  SOFT_TIMEOUT_FALLBACK_MESSAGE  default: Да...
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_JSON="$2"
VERSION_DESCRIPTION="${3:-}"
SOFT_TIMEOUT_SECONDS="${SOFT_TIMEOUT_SECONDS:-2.4}"
SOFT_TIMEOUT_FALLBACK_MESSAGE="${SOFT_TIMEOUT_FALLBACK_MESSAGE:-Да...}"

if [[ ! -f "$SOURCE_JSON" ]]; then
  echo "Source file not found: $SOURCE_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSON")"

jq \
  --arg version_description "$VERSION_DESCRIPTION" \
  --argjson soft_timeout_seconds "$SOFT_TIMEOUT_SECONDS" \
  --arg soft_timeout_fallback_message "$SOFT_TIMEOUT_FALLBACK_MESSAGE" '
  {
    conversation_config: .conversation_config,
    platform_settings: .platform_settings,
    workflow: .workflow
  }
  | del(.conversation_config.agent.prompt.tool_ids)
  | .conversation_config.turn.soft_timeout_config.timeout_seconds = $soft_timeout_seconds
  | .conversation_config.turn.soft_timeout_config.message = $soft_timeout_fallback_message
  | .conversation_config.turn.soft_timeout_config.additional_soft_timeout_messages = []
  | .conversation_config.turn.soft_timeout_config.use_llm_generated_message = true
  | .conversation_config.turn.soft_timeout_config.randomize_fillers = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.turn.soft_timeout_config.llm_generated_message_prompt_override =
      "Generate one ultra-short natural Russian filler for a live phone conversation only after the user has already said something and the assistant is genuinely preparing the real next reply. The filler must be 1 to 2 words, not a question, not a line-check, not a sales phrase, not a time promise, and never before the opener. Good shapes: Да... / Поняла... / Ясно... / Момент... If no filler is truly needed, return an empty string."
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
      sub("\\n\\nNo-tool-music override:[\\s\\S]*$"; "")
      + "\n\nNo-tool-music override:\n- Do not rely on musical or synthetic tool-call masking during slow backend actions.\n- If a backend step is slow, you may use at most one ultra-short spoken filler and then continue with the actual answer.\n- Never use filler as a line-check, rescue phrase, or opener prefix.\n- Never loop fillers. One short filler maximum per slow response window.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Soft timeout seconds: $SOFT_TIMEOUT_SECONDS"
echo "Fallback filler: $SOFT_TIMEOUT_FALLBACK_MESSAGE"
echo "Webhook tools: tool_call_sound -> null / auto"
