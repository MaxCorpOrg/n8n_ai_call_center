#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_lexical_nottarget_terminal_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow ElevenLabs payload that:
  - forces immediate not_target close on lexical category-mismatch
  - prevents renewed pitch after "не работаем / не используем / не наш профиль"
  - keeps other current prompt fixes intact
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
      sub("\\n\\nLexical not-target terminal override:[\\s\\S]*$"; "")
      + "\n\nLexical not-target terminal override:\n- A lexical category-mismatch answer is stronger than mild curiosity or earlier interest.\n- If the user says phrases like `не работаем`, `ещё не работаем`, `не используем`, `не занимаемся этим`, `не наш профиль`, `не делаем такое`, that means current not-target for this sales path.\n- In that case do not resume product value, do not offer SMS, do not offer callback, and do not continue qualification.\n- Correct behavior after lexical category-mismatch is immediate terminal handling:\n  1. silent `call_log(not_target)`\n  2. one short spoken `end_call.system__message_to_speak`\n  3. stop\n- Even if the user previously sounded curious and asked `что интересного`, lexical mismatch later overrides that earlier curiosity.\n- Even if the user says `да` earlier, a later clear line like `нет, ещё не работаем` or `не-не, мы не работаем` must override it and close as not_target.\n- Do not interpret hesitation sounds like `а-а-а` after a lexical mismatch as fresh consent for SMS. Ask nothing further and finalize instead.\n- If the user shifts from lexical mismatch into factual questions like price or source, answer only one short sentence if needed, but do not convert them back into an active target if they already said they do not work with this category.\n- If after lexical mismatch they explicitly refuse and say goodbye, close immediately with the single-close terminal pattern.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: immediate lexical not_target terminal handling"
