#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_noninterruptible_finalization_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow payload that:
  - makes call_log and end_call non-interruptible
  - hardens refusal finalization against late line-check interruptions
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
           if (.name == "call_log" or .name == "end_call") then
             .disable_interruptions = true
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nNon-interruptible finalization override:[\\s\\S]*$"; "")
      + "\n\nNon-interruptible finalization override:\n- After a clear terminal refusal or confirmed not_target, once finalization has started you must not reopen the dialogue because of a late `алло`, `алло?`, or other line-check fragment.\n- If call_log for a terminal refusal has already started or already completed, do not answer with filler, line-check, or another ordinary assistant sentence.\n- In that finalization window, proceed straight to the one short end_call close and stop.\n- A late `алло` after terminal refusal is not a reason to restart the conversation.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "call_log/end_call disable_interruptions = true"
echo "Added non-interruptible finalization override"
