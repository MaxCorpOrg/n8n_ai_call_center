#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_single_shot_opener_nottarget_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload that:
  - enables interruption handling
  - keeps opener single-shot and blocks opener restart after a live reply
  - cancels late rescue / late line-check after any meaningful post-opener reply
  - hardens lexical not_target finalization and bans helpdesk tails

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
      sub("\\n\\nSingle-shot opener and lexical terminal override:[\\s\\S]*$"; "")
      + "\n\nSingle-shot opener and lexical terminal override:\n- The exact opener may be spoken only once per call.\n- If the opener was partially interrupted but the user already gives any directed live reply such as `алло`, `да`, `слушаю`, `говорите`, `что`, or `чего`, do not restart the opener and do not repeat the full opener again.\n- In that situation, continue from the meaning already reached: give one short clarification or one short explanation, then ask one short business question.\n- A short post-opener reply like `алло` means the person is live and engaged. Treat it as confusion about the content, not as a reason to restart the call from the top.\n- After the opener, any meaningful lexical live-human reply permanently cancels rescue and late line-check mode for the rest of the call.\n- Once such a reply happened, never say `Алло?`, `Вы на линии?`, `Вы всё ещё на линии?`, or similar again later in the same call.\n- If the user line-checks with `алло` during an already active dialogue, answer the latest business meaning directly instead of switching into support or rescue mode.\n- If the user clearly says lexical category-mismatch phrases like `не работаем`, `ещё не работаем`, `не используем`, `не занимаемся этим`, `не наш профиль`, or `не делаем такое`, treat that as immediate `not_target`.\n- After a clear lexical `not_target`, do not continue pitch, do not offer SMS, do not offer callback, and do not ask another qualification question.\n- Correct sequence after lexical `not_target` is exactly:\n  1. silent `call_log(not_target)`\n  2. one short spoken `end_call.system__message_to_speak`\n  3. stop\n- After any final human outcome, do not add helpdesk tails such as `Могу чем-то ещё помочь?`, `Это ваше подтверждение?`, or another support-style follow-up.\n- Once finalization has started, do not reopen the dialogue because of late `алло`, `...`, or trailing fragments.\n"
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
echo "Added override: single-shot opener, no late line-check, lexical not_target terminal"
