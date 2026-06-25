#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_gap_masking_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a lab-only payload that reduces dead air in two layers:
  - faster soft-timeout for pure LLM thinking pauses
  - audible tool-call masking for slower webhook tools

Optional environment overrides:
  SOFT_TIMEOUT_SECONDS   default: 1.9
  TOOL_CALL_SOUND        default: elevator3
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_JSON="$2"
VERSION_DESCRIPTION="${3:-}"
SOFT_TIMEOUT_SECONDS="${SOFT_TIMEOUT_SECONDS:-1.9}"
TOOL_CALL_SOUND="${TOOL_CALL_SOUND:-elevator3}"

if [[ ! -f "$SOURCE_JSON" ]]; then
  echo "Source file not found: $SOURCE_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSON")"

jq \
  --arg version_description "$VERSION_DESCRIPTION" \
  --argjson soft_timeout_seconds "$SOFT_TIMEOUT_SECONDS" \
  --arg tool_call_sound "$TOOL_CALL_SOUND" '
  {
    conversation_config: .conversation_config,
    platform_settings: .platform_settings,
    workflow: .workflow
  }
  | del(.conversation_config.agent.prompt.tool_ids)
  | .conversation_config.turn.soft_timeout_config.timeout_seconds = $soft_timeout_seconds
  | .conversation_config.turn.soft_timeout_config.message = "..."
  | .conversation_config.turn.soft_timeout_config.additional_soft_timeout_messages = []
  | .conversation_config.turn.soft_timeout_config.use_llm_generated_message = true
  | .conversation_config.turn.soft_timeout_config.randomize_fillers = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.turn.soft_timeout_config.llm_generated_message_prompt_override =
      "Generate one ultra-short natural Russian filler for a live phone conversation only after the exact opener has already finished and only while the assistant is genuinely preparing the next answer. The filler must be 1 to 2 words, not a question, not a line-check, not a promise about time, and not a sales phrase. Good shapes: Да... / Секунду... / Момент... If a filler is not needed, return an empty string."
  | .conversation_config.agent.prompt.tools =
      (.conversation_config.agent.prompt.tools
       | map(
           if (.name == "call_log" or .name == "send_sms_info" or .name == "context_fetch") then
             .tool_call_sound = $tool_call_sound
             | .tool_call_sound_behavior = "always"
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nGap masking override:[\\s\\S]*$"; "")
      + "\n\nGap masking override:\n- Avoid dead silence between user reply and your next action.\n- If the correct next step is a tool path like `context_fetch`, `send_sms_info`, or `call_log`, move into the tool path immediately instead of spending an extra explanatory turn.\n- During genuine thinking delay after a real user reply, allow at most one ultra-short filler and then continue with the real answer.\n- The filler must never become a line-check, rescue phrase, support phrase, or sales line.\n- During slow tool execution, rely on audible tool-call masking rather than extra spoken filler.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Soft timeout seconds: $SOFT_TIMEOUT_SECONDS"
echo "Tool call sound: $TOOL_CALL_SOUND / always"
