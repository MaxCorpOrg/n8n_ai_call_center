#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_voice_only_variant.sh SOURCE_AGENT_JSON TARGET_TTS_MODEL OUTPUT_JSON [VERSION_DESCRIPTION]

Examples:
  TARGET_SPEED=1.08 TARGET_STABILITY=0.42 TARGET_SIMILARITY_BOOST=0.78 \
  scripts/prepare_eleven_voice_only_variant.sh \
    .runtime/eleven_noninterruptible_finalization_2026-06-26/apply_result/response.json \
    eleven_v3_conversational \
    .runtime/eleven_voice_switch_matrix_2026-07-09/payload_logic4401_v3.json \
    "Lab voice-only: 4401 logic + Eleven v3 Conversational"

Builds an ElevenLabs Update Agent payload that keeps the source logic intact
and changes only the voice/TTS layer:
  - conversation_config.tts.model_id
  - optional conversation_config.tts.voice_id
  - optional voice tuning fields: speed, stability, similarity_boost

This helper is for lab branch work. It intentionally does not edit prompt,
workflow, tools, call_log, end_call, machine rules, or turn-taking.

Optional environment overrides:
  TARGET_VOICE_ID
  TARGET_SPEED
  TARGET_STABILITY
  TARGET_SIMILARITY_BOOST
  TARGET_OPTIMIZE_STREAMING_LATENCY
  TARGET_TEXT_NORMALISATION_TYPE
  TARGET_EXPRESSIVE_MODE              true/false; defaults by TTS model
EOF
  exit 1
fi

SOURCE_JSON="$1"
TARGET_TTS_MODEL="$2"
OUTPUT_JSON="$3"
VERSION_DESCRIPTION="${4:-}"

if [[ ! -f "$SOURCE_JSON" ]]; then
  echo "Source file not found: $SOURCE_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSON")"

jq \
  --arg target_tts_model "$TARGET_TTS_MODEL" \
  --arg target_voice_id "${TARGET_VOICE_ID:-}" \
  --arg target_speed "${TARGET_SPEED:-}" \
  --arg target_stability "${TARGET_STABILITY:-}" \
  --arg target_similarity_boost "${TARGET_SIMILARITY_BOOST:-}" \
  --arg target_optimize_streaming_latency "${TARGET_OPTIMIZE_STREAMING_LATENCY:-}" \
  --arg target_text_normalisation_type "${TARGET_TEXT_NORMALISATION_TYPE:-}" \
  --arg target_expressive_mode "${TARGET_EXPRESSIVE_MODE:-}" \
  --arg version_description "$VERSION_DESCRIPTION" '
  {
    conversation_config: .conversation_config,
    platform_settings: .platform_settings,
    workflow: .workflow
  }
  | del(.conversation_config.agent.prompt.tool_ids)
  | .conversation_config.tts.model_id = $target_tts_model
  | .conversation_config.tts.expressive_mode =
      (
        if $target_expressive_mode != "" then
          ($target_expressive_mode == "true")
        elif $target_tts_model == "eleven_v3_conversational" then
          true
        else
          false
        end
      )
  | if $target_voice_id != "" then
      .conversation_config.tts.voice_id = $target_voice_id
    else
      .
    end
  | if $target_speed != "" then
      .conversation_config.tts.speed = ($target_speed | tonumber)
    else
      .
    end
  | if $target_stability != "" then
      .conversation_config.tts.stability = ($target_stability | tonumber)
    else
      .
    end
  | if $target_similarity_boost != "" then
      .conversation_config.tts.similarity_boost = ($target_similarity_boost | tonumber)
    else
      .
    end
  | if $target_optimize_streaming_latency != "" then
      .conversation_config.tts.optimize_streaming_latency = ($target_optimize_streaming_latency | tonumber)
    else
      .
    end
  | if $target_text_normalisation_type != "" then
      .conversation_config.tts.text_normalisation_type = $target_text_normalisation_type
    else
      .
    end
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
jq '{
  version_description,
  llm: .conversation_config.agent.prompt.llm,
  tts: .conversation_config.tts,
  turn: {
    turn_timeout: .conversation_config.turn.turn_timeout,
    turn_eagerness: .conversation_config.turn.turn_eagerness,
    soft_timeout_seconds: .conversation_config.turn.soft_timeout_config.timeout_seconds,
    soft_timeout_message: .conversation_config.turn.soft_timeout_config.message,
    soft_timeout_llm_generated: .conversation_config.turn.soft_timeout_config.use_llm_generated_message
  },
  prompt_length: (.conversation_config.agent.prompt.prompt | length),
  tool_names: (.conversation_config.agent.prompt.tools // [] | map(.name))
}' "$OUTPUT_JSON"
