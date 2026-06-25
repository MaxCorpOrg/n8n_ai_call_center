#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_interruptible_latefill_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a lab-only payload for:
  - interruptions enabled
  - less aggressive turn-taking
  - later filler masking start, closer to official-doc starting guidance

Optional environment overrides:
  TARGET_TURN_TIMEOUT      default: 2.3
  TARGET_TURN_EAGERNESS    default: normal
  TARGET_SOFT_TIMEOUT      default: 3.0
  TARGET_SOFT_MESSAGE      default: Да...
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_JSON="$2"
VERSION_DESCRIPTION="${3:-}"
TARGET_TURN_TIMEOUT="${TARGET_TURN_TIMEOUT:-2.3}"
TARGET_TURN_EAGERNESS="${TARGET_TURN_EAGERNESS:-normal}"
TARGET_SOFT_TIMEOUT="${TARGET_SOFT_TIMEOUT:-3.0}"
TARGET_SOFT_MESSAGE="${TARGET_SOFT_MESSAGE:-Да...}"

if [[ ! -f "$SOURCE_JSON" ]]; then
  echo "Source file not found: $SOURCE_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSON")"

jq \
  --arg version_description "$VERSION_DESCRIPTION" \
  --argjson target_turn_timeout "$TARGET_TURN_TIMEOUT" \
  --arg target_turn_eagerness "$TARGET_TURN_EAGERNESS" \
  --argjson target_soft_timeout "$TARGET_SOFT_TIMEOUT" \
  --arg target_soft_message "$TARGET_SOFT_MESSAGE" '
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
  | .conversation_config.turn.soft_timeout_config.timeout_seconds = $target_soft_timeout
  | .conversation_config.turn.soft_timeout_config.message = $target_soft_message
  | .conversation_config.turn.soft_timeout_config.use_llm_generated_message = true
  | .conversation_config.turn.soft_timeout_config.randomize_fillers = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.turn.soft_timeout_config.llm_generated_message_prompt_override =
      "Generate one ultra-short natural Russian filler for a live phone conversation only after the exact opener has already finished and only while the assistant is genuinely preparing the next answer. The filler must be 1 to 2 words, not a question, not a line-check, not a promise about time, and not a sales phrase. Prefer neutral thinking sounds or brief acknowledgements such as: Да... / Так... / Угу... If a filler is not needed, return an empty string."
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nInterruptible balanced override:[\\s\\S]*$"; "")
      | sub("\\n\\nInterruptible softfill override:[\\s\\S]*$"; "")
      | sub("\\n\\nInterruptible latefill override:[\\s\\S]*$"; "")
      + "\n\nInterruptible latefill override:\n- Prefer natural barge-in handling over premature assistant continuation.\n- If the human starts speaking, yield and let them finish instead of racing into the next scripted line.\n- Do not treat short live-human fillers as empty silence.\n- Delay filler masking slightly longer than the softfill variant so the assistant answers quickly when ready, but does not rush into filler too early.\n- If filler masking is needed, use only very short neutral sounds and never promise time.\n- Keep the current opener and machine-stop logic unchanged; this variant only relaxes turn-taking and starts filler masking later.\n"
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
echo "soft_timeout: $TARGET_SOFT_TIMEOUT"
echo "soft_message: $TARGET_SOFT_MESSAGE"
echo "client_events: interruption ensured"
