#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_plaintext_finalclose_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload that targets:
  - duplicate spoken close before end_call;
  - helpdesk-style final tails;
  - bracket tags in spoken text.
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
             .description = "Internal end-call tool. Finish the call only through end_call after silent call_log. Keep the one and only final spoken close only inside end_call.system__message_to_speak. Never output a separate normal assistant farewell before end_call. Never include helpdesk tails like `Могу чем-то ещё помочь?` in outbound final closes."
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nPlain spoken text and final-close override:[\\s\\S]*$"; "")
      + "\n\nPlain spoken text and final-close override:\n- Output only plain spoken Russian text. Never include bracket tags, stage directions, or meta-markers such as `[calm]`, `[pause]`, `[thinking]`, or any text in square brackets.\n- If a draft spoken turn contains square brackets or a stage tag, regenerate it into plain spoken Russian before speaking.\n- For any final live-human close, never emit the farewell as a normal assistant message before `end_call`.\n- The final spoken close must exist only once and only inside `end_call.system__message_to_speak`.\n- Final outbound closes must not contain helpdesk tails such as `Могу чем-то ещё помочь?`, `Чем-то ещё помочь?`, or similar support-style endings.\n- For manager callback, SMS sent, refusal, not_target, and goodbye endings, use one short plain closing sentence only.\n- If you are about to call `end_call`, do not first say the same close as a normal assistant turn.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added only: plain spoken text and final-close override"
