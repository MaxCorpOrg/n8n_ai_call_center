#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_finalization_interrupt_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Example:
  scripts/prepare_eleven_finalization_interrupt_variant.sh \
    .runtime/eleven_lab_endcall_only_fix_2026-06-17/apply_result/response.json \
    .runtime/eleven_lab_finalization_interrupt_fix_2026-06-17/payload.json \
    "Lab: finalization interrupt micro-fix"

Builds a lab-only payload that:
  - keeps current prompt / LLM / TTS / tools
  - adds only a tiny finalization-interrupt rule
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
  | .conversation_config.agent.prompt.prompt += "\n\nPending-finalization interrupt micro-override:\n- If `call_log` has already been completed and you are about to end the call, do not emit a normal assistant close as a separate message.\n- In that pending-finalization window, any final spoken close must live only inside `end_call.system__message_to_speak`.\n- If the user makes only a cut-off fragment, trailing noise, or a non-substantive last-second interruption after `call_log`, do not switch to a normal assistant reply; finish with one `end_call` close only.\n- Only abort the close if the user clearly starts a new meaningful business turn.\n"
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added only: pending-finalization interrupt micro-override"
