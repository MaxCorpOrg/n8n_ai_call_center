#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_positive_polarity_qualification_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow ElevenLabs payload that:
  - bans negative-polarity qualification questions
  - hardens not-target classification for ambiguous "да/нет" replies
  - keeps the rest of the current terminal improvements intact
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
      sub("\\n\\nPositive-polarity qualification override:[\\s\\S]*$"; "")
      + "\n\nPositive-polarity qualification override:\n- When qualifying category fit, use only positive-polarity business questions.\n- Preferred shape is exactly: `Вы вообще с липолитиками работаете?`\n- Do not ask negative-polarity versions like:\n  - `Вы не работаете с липолитиками?`\n  - `Вы не используете такое?`\n  - `То есть вы этим не занимаетесь?`\n- Negative-polarity qualification creates ambiguity in Russian `да/нет` answers and is forbidden.\n- If the person already said `нет` to interest and then gives a second clarification like `не работаем`, `не используем`, `нам не надо`, `это не наш профиль`, treat this as final `not_target` or final refusal immediately.\n- If the reply contains both `да/нет` ambiguity and a clear lexical clarification such as `не работаем`, trust the lexical clarification, not the single particle.\n- Example:\n  - forbidden bad path:\n    - agent: `Вы не работаете с липолитиками?`\n    - user: `Да.`\n    - agent wrongly assumes they do work with lipolytics\n  - correct path:\n    - agent: `Вы вообще с липолитиками работаете?`\n    - if user then says `нет`, `не работаем`, `не используем`, or similar, finalize as `not_target` immediately.\n- After a confirmed `not_target`, do not pitch product value, do not offer SMS, and do not offer callback. Finalize with the single-close terminal pattern only.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: positive-polarity qualification and lexical not-target disambiguation"
