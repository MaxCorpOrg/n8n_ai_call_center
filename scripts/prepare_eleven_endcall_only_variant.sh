#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_endcall_only_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Example:
  scripts/prepare_eleven_endcall_only_variant.sh \
    .runtime/eleven_lab_finalization_tool_fix_2026-06-17/revert_to_safe_v1/apply_result/response.json \
    .runtime/eleven_lab_endcall_only_fix_2026-06-17/payload.json \
    "Lab: end_call description only fix"

Builds a minimal lab-only payload that:
  - keeps current LLM / TTS / prompt / turn-taking
  - does not add new prompt overrides
  - changes only the end_call tool description
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
           if .name == "end_call" then
             .description = "Internal end-call tool. Use this immediately after final silent call_log. Put the one and only final farewell only into end_call.system__message_to_speak. Do not say the same farewell first as a normal assistant message and then again in end_call."
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
echo "Patched only: end_call.description"
