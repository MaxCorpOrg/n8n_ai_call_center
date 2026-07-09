#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_turn_latency_allo_recovery_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload for the confirmed post-4701 latency issue:
  - trims turn_timeout for faster phone replies
  - lowers soft timeout for earlier spoken filler during generation waits
  - keeps interruptions enabled
  - prevents repeated "Алло" from sending the agent into line-check mode

Optional environment overrides:
  TARGET_TURN_TIMEOUT      default: 1.55
  TARGET_TURN_EAGERNESS    default: normal
  TARGET_SOFT_TIMEOUT      default: 1.8
  TARGET_SOFT_MESSAGE      default: Да...
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_JSON="$2"
VERSION_DESCRIPTION="${3:-}"
TARGET_TURN_TIMEOUT="${TARGET_TURN_TIMEOUT:-1.55}"
TARGET_TURN_EAGERNESS="${TARGET_TURN_EAGERNESS:-normal}"
TARGET_SOFT_TIMEOUT="${TARGET_SOFT_TIMEOUT:-1.8}"
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
  | .conversation_config.turn.soft_timeout_config.additional_soft_timeout_messages = []
  | .conversation_config.turn.soft_timeout_config.use_llm_generated_message = false
  | .conversation_config.turn.soft_timeout_config.randomize_fillers = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nTurn latency and repeated allo recovery override:[\\s\\S]*$"; "")
      + "\n\nTurn latency and repeated allo recovery override:\n- Phone dialogue must feel immediate. After short live-human replies like `да`, `алло`, `что такое`, `чё такое`, `слушаю`, answer quickly and do not wait for a long extra pause.\n- A repeated `Алло` right after the opener or during an interrupted opener usually means the human did not catch the phrase. Do not answer with line-checks like `Вы слышите меня?`, `Вы меня слышите?`, `Алло, меня слышно?`, or `Вы на линии?`.\n- If the opener was interrupted or cut off, calmly restart the exact opener once from the beginning.\n- If the opener was already fully delivered and the human asks `что это?` or `что за ЛипоЛонг?`, answer directly in one short sentence, then ask whether to send SMS or connect a manager.\n- Do not loop `Алло` / line-check phrases during a live-human conversation. Use line-check only for real silence, not for a human repeatedly trying to hear you.\n- Keep machine / voicemail / `абонент` hard-stop rules unchanged.\n- Keep SMS finalization ordering unchanged: acknowledgement before tools, then `send_sms_info`, silent `call_log`, spoken `end_call`, stop.\n"
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
echo "Added override: faster turn-taking + repeated allo recovery"
