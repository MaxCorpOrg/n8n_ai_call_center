#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_late_linecheck_singleclose_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload that targets only:
  - late line-check inside an already active dialogue;
  - duplicate spoken close before end_call.
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
           if .name == "end_call" then
             .description = "Internal end-call tool. First complete silent call_log. Then put the one and only final spoken close only into end_call.system__message_to_speak. Never say the same farewell first as a normal assistant message and then again in end_call."
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nLate line-check and single-close override:[\\s\\S]*$"; "")
      + "\n\nLate line-check and single-close override:\n- The one rescue line-check is allowed only in the immediate post-opener silence window. It is not a general fallback for the rest of the call.\n- Once the call has already entered active business dialogue, never use a generic line-check like `Алло?`, `Алло, вы на линии?`, or `Слышно меня?` later in the same call.\n- Active business dialogue means the user has already given any meaningful business, correction, objection, clarification, consent, or product-related reply after the opener.\n- If a short silence or `...` happens later inside an active dialogue, do not switch back to rescue mode. Wait briefly or continue from the latest business meaning, but do not say `Алло?`.\n- A short `алло?` from the user inside an active dialogue does not justify a separate reassurance turn and does not justify a rescue line-check back.\n- For any final live-human outcome, do not speak the farewell as a normal assistant message before tools.\n- Correct final sequence is exactly: silent `call_log` -> one spoken `end_call.system__message_to_speak` -> stop.\n- If you already know the call is ending, do not produce a normal assistant close draft at all.\n- Never say the same close twice in any form.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added only: late line-check and single-close override"
