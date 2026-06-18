#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_llm_variant.sh SOURCE_AGENT_JSON TARGET_LLM OUTPUT_JSON [VERSION_DESCRIPTION]

Example:
  scripts/prepare_eleven_llm_variant.sh \
    .runtime/eleven_lab_flash_return_2026-06-16/response.json \
    gemini-2.5-flash \
    .runtime/eleven_lab_llm_compare_gemini_2026-06-16/payload.json \
    "Lab LLM compare: switch GPT-4.1 -> Gemini 2.5 Flash"

Builds a minimal ElevenLabs Update Agent payload that keeps the current
conversation/tool/voice/workflow config and only changes:
  - conversation_config.agent.prompt.llm
  - version_description (optional)

The helper intentionally removes resolved prompt.tools from response snapshots,
because Update Agent rejects payloads that contain both:
  - prompt.tool_ids
  - prompt.tools
EOF
  exit 1
fi

SOURCE_JSON="$1"
TARGET_LLM="$2"
OUTPUT_JSON="$3"
VERSION_DESCRIPTION="${4:-}"

if [[ ! -f "$SOURCE_JSON" ]]; then
  echo "Source file not found: $SOURCE_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSON")"

jq \
  --arg llm "$TARGET_LLM" \
  --arg version_description "$VERSION_DESCRIPTION" '
  {
    conversation_config: .conversation_config,
    platform_settings: .platform_settings,
    workflow: .workflow
  }
  | del(.conversation_config.agent.prompt.tools)
  | .conversation_config.agent.prompt.llm = $llm
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Target LLM: $TARGET_LLM"
