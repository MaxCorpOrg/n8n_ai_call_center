#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_no_preopener_linecheck_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload that:
  - blocks any spoken line-check before the opener
  - keeps the current turn/filler settings untouched
  - only hardens pre-opener behavior
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
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nNo pre-opener line-check override:[\\s\\S]*$"; "")
      + "\n\nNo pre-opener line-check override:\n- Before the exact opener, do not speak any line-check, rescue phrase, reassurance phrase, or filler at all.\n- Forbidden before the opener: `Алло?`, `Вы на линии?`, `Слышно?`, `Да?`, `Поняла...`, `Так...`, or any similar phrase.\n- If pickup audio is ambiguous, weak, fragmentary, or not clearly directed to you yet, stay silent and wait for a clearer live-human cue.\n- The first spoken assistant words after a valid live-human pickup must be the exact opener itself.\n- A short ambiguous pickup fragment before the opener is never a reason to start a separate assistant line-check.\n- If the line becomes clear only on the second human cue, start the opener there directly; do not insert `Алло?` first.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: no spoken pre-opener line-check"
