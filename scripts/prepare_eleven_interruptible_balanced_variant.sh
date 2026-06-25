#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_interruptible_balanced_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a lab-only payload for "give the human room to talk":
  - enables interruptions by adding `interruption` to client_events
  - relaxes turn eagerness from eager to normal
  - raises turn_timeout slightly

Optional environment overrides:
  TARGET_TURN_TIMEOUT   default: 2.3
  TARGET_TURN_EAGERNESS default: normal
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_JSON="$2"
VERSION_DESCRIPTION="${3:-}"
TARGET_TURN_TIMEOUT="${TARGET_TURN_TIMEOUT:-2.3}"
TARGET_TURN_EAGERNESS="${TARGET_TURN_EAGERNESS:-normal}"

if [[ ! -f "$SOURCE_JSON" ]]; then
  echo "Source file not found: $SOURCE_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSON")"

jq \
  --arg version_description "$VERSION_DESCRIPTION" \
  --argjson target_turn_timeout "$TARGET_TURN_TIMEOUT" \
  --arg target_turn_eagerness "$TARGET_TURN_EAGERNESS" '
  {
    conversation_config: .conversation_config,
    platform_settings: .platform_settings,
    workflow: .workflow
  }
  | del(.conversation_config.agent.prompt.tool_ids)
  | .conversation_config.turn.turn_timeout = $target_turn_timeout
  | .conversation_config.turn.turn_eagerness = $target_turn_eagerness
  | .conversation_config.conversation.client_events =
      (
        (.conversation_config.conversation.client_events // [])
        + ["interruption"]
        | unique
      )
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nInterruptible balanced override:[\\s\\S]*$"; "")
      + "\n\nInterruptible balanced override:\n- Prefer natural barge-in handling over premature assistant continuation.\n- If the human starts speaking, yield and let them finish instead of racing into the next scripted line.\n- Do not treat short live-human fillers as empty silence.\n- Keep the current opener and machine-stop logic unchanged; this variant only relaxes turn-taking slightly.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "turn_timeout: $TARGET_TURN_TIMEOUT"
echo "turn_eagerness: $TARGET_TURN_EAGERNESS"
echo "client_events: interruption ensured"
