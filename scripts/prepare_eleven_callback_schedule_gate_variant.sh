#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_callback_schedule_gate_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow prompt-only payload that:
  - blocks late line-checks after meaningful post-opener replies
  - prevents premature callback call_log before callback timing is actually collected
  - hardens final callback close so it goes straight to end_call
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
      sub("\\n\\nCallback schedule gate override:[\\s\\S]*$"; "")
      + "\n\nCallback schedule gate override:\n- After the opener, any meaningful lexical user reply permanently cancels late line-check mode for the rest of the call.\n- Once a real business reply already happened, never say `Алло?`, `Вы на линии?`, `Вы всё ещё на линии?`, or similar again later in the same call.\n- If the user says `алло` after a tool was being prepared or after an overlap, treat it as an interruption of an active business flow and answer the latest business meaning directly.\n\nCallback scheduling override:\n- If the user says `перезвоните позже`, `попозже`, `сейчас неудобно`, `завтра`, `после обеда`, or another callback-later meaning, do not start `call_log(callback_scheduled)` until the callback timing is sufficiently collected.\n- While callback timing is still missing or still being уточнено, stay in the scheduling dialogue and do not begin backend finalization yet.\n- Ask at most one short scheduling question per turn.\n- Good order for callback scheduling is:\n  1. user asks for later callback\n  2. assistant gathers the minimal needed time window\n  3. silent `call_log(callback_scheduled)` exactly once\n  4. one short `end_call` close\n  5. stop\n- Forbidden order:\n  1. user asks for later callback\n  2. assistant starts `call_log(callback_scheduled)` too early\n  3. user keeps speaking\n  4. assistant falls into `Алло?` or filler mode\n\nFinal callback close override:\n- Once callback timing is already collected and `call_log(callback_scheduled)` succeeds, do not emit filler, line-check, or any new scheduling question.\n- After successful callback `call_log`, immediately finish with one short `end_call.system__message_to_speak` and stop.\n- Do not say support-style tails like `Могу я чем-то ещё помочь?`.\n- Do not say `Да, я вас слышу` as a separate reassurance turn inside callback finalization.\n- If the user interrupts before callback time is fully collected, continue collecting the callback timing instead of finalizing early.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added overrides: no late line-check, callback schedule gate, clean callback close"
