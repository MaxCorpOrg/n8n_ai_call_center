#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_latency_masking_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload that reduces perceived silence by:
  - lowering soft-timeout slightly
  - enabling tool call sounds for slower webhook tools
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
  | .conversation_config.turn.soft_timeout_config.timeout_seconds = 2.4
  | .conversation_config.turn.soft_timeout_config.message = "..."
  | .conversation_config.turn.soft_timeout_config.additional_soft_timeout_messages = []
  | .conversation_config.turn.soft_timeout_config.randomize_fillers = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.agent.prompt.tools =
      (.conversation_config.agent.prompt.tools
       | map(
           if (.name == "call_log" or .name == "send_sms_info" or .name == "context_fetch") then
             .tool_call_sound = "typing"
             | .tool_call_sound_behavior = "always"
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nLatency masking override:[\\s\\S]*$"; "")
      + "\n\nLatency masking override:\n- If you are about to use a slower webhook tool like `call_log`, `send_sms_info`, or `context_fetch`, avoid long dead silence.\n- When a tool path is already the correct next action, prefer moving into the tool immediately instead of spending an extra explanatory turn.\n- Do not add a long spoken preface before a tool if the tool itself is the main next step.\n- Soft-timeout filler is only for genuine LLM thinking delay. Keep it ultra-short and never let it turn into a line-check or support phrase.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added only: latency masking override"
