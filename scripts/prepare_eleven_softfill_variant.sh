#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_softfill_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Example:
  scripts/prepare_eleven_softfill_variant.sh \
    .runtime/eleven_lab_gpt5mini_v3_tuned2_2026-06-17/revert_to_tuned1_apply_result/response.json \
    .runtime/eleven_lab_gpt5mini_v3_softfill_2026-06-17/payload.json \
    "Lab: GPT-5 Mini + Eleven V3 + soft timeout + SMS typing mask"

Builds an ElevenLabs Update Agent payload for the naturalness lab:
  - keeps current LLM / TTS / workflow / platform settings from source snapshot
  - enables a short soft-timeout filler for slow LLM turns
  - applies minimal tool masking only to send_sms_info

The helper intentionally removes prompt.tool_ids and keeps prompt.tools,
because we need tool-level sound settings in the payload.
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
  | .conversation_config.turn.soft_timeout_config.timeout_seconds = 2.8
  | .conversation_config.turn.soft_timeout_config.message = "Так..."
  | .conversation_config.turn.soft_timeout_config.additional_soft_timeout_messages = []
  | .conversation_config.turn.soft_timeout_config.use_llm_generated_message = true
  | .conversation_config.turn.soft_timeout_config.randomize_fillers = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.turn.soft_timeout_config.llm_generated_message_prompt_override =
      "Generate one ultra-short natural Russian thinking filler for a live phone conversation while the assistant is still formulating the main answer. It must not ask the user a question, must not check whether the line is alive, must not promise a specific waiting time, and must be only 1 to 3 words. Good shapes: Так... / Поняла... / Ясно... Keep it human and brief."
  | .conversation_config.agent.prompt.tools =
      (.conversation_config.agent.prompt.tools
       | map(
           if .name == "send_sms_info" then
             .tool_call_sound = "typing"
             | .tool_call_sound_behavior = "always"
           else
             .
           end
         ))
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Soft timeout: 2.8s, llm-generated filler enabled"
echo "Tool sound: send_sms_info -> typing / always"
