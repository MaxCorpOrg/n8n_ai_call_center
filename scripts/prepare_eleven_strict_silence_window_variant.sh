#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_strict_silence_window_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload that hardens the post-opener silence window.
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
      sub("\\n\\nStrict post-opener silence override:[\\s\\S]*$"; "")
      + "\n\nStrict post-opener silence override:\n- Silence after the opener is a special no-answer state, not a sales state.\n- If after the exact opener there is only silence, `...`, rustling, cut-off noise, or no meaningful business reply, do not continue discovery, do not explain the product further, and do not offer SMS, callback, or manager options yet.\n- In that state, you may use exactly one short rescue line-check only once.\n- If there is still no meaningful business reply about 2 more seconds after that one rescue, immediately do silent `call_log(no_answer)` and end the call silently.\n- Do not ask repeated `Алло?` questions.\n- Do not loop qualification questions during silence.\n- Do not say inbound-support phrases like `Да? Чем могу помочь?`, `Чем могу помочь?`, `Можно перезвонить позже или отправить SMS?`, or similar while the call is still in the silence/no-answer state.\n- A bare post-opener `алло?` or `меня слышно?` without business meaning is only a line-quality check. It does not switch the call into inbound support mode and does not justify a new sales branch by itself.\n- If a real business reply appears, then exit the silence state and continue normally.\n- Otherwise, silence must end in exactly one no-answer finalization path, not in a loop.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added only: strict post-opener silence override"
