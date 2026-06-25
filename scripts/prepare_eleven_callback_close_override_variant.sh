#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_callback_close_override_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a very narrow published payload that only strengthens the
callback-later closing behavior.

What it changes:
  - keeps current LLM / TTS / workflow / platform settings
  - removes resolved prompt.tools to avoid tool_id/update conflicts
  - appends only a callback-close override
  - does not touch opener, rescue, machine-stop, or SMS rules
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
  | del(.conversation_config.agent.prompt.tools)
  | .conversation_config.agent.prompt.prompt += "\n\nCallback close override:\n- If the person clearly says they are busy now, not ready now, or asks to talk later, treat that as a callback-later outcome and finish briefly.\n- In that callback-later outcome, do not reopen the conversation with a new question.\n- Do not ask `Могу чем-то ещё помочь?`, `Могу ли я ещё чем-то помочь?`, or any similar helpdesk-style tail.\n- Keep the spoken close to one short natural sentence only.\n- Good close shapes:\n  - `Поняла, перезвоню позже. Хорошего дня.`\n  - `Хорошо, тогда вернусь позже. Хорошего дня.`\n- Bad close shapes:\n  - `Поняла, перезвоню позже. Могу чем-то ещё помочь?`\n  - `Хорошо, тогда вернусь позже. Уточню ещё один момент.`\n"
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: callback close only"
