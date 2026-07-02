#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_unclear_ack_short_question_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow prompt-only payload that:
  - forbids bracketed stage tags absolutely
  - handles vague / garbled acknowledgements with one short question only
  - reduces long post-opener monologues after unclear user replies
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
      sub("\\n\\nUnclear acknowledgement short-question override:[\\s\\S]*$"; "")
      + "\n\nUnclear acknowledgement short-question override:\n- If the user reply after the opener is only a vague acknowledgement, weak assent, or garbled mixed phrase without a clear business meaning, do not answer with a long product sentence.\n- Examples include shapes like: `да`, `ага`, `угу`, `хорошо`, `ну да`, or a noisy mixed phrase that does not clearly answer your business question.\n- In that situation, make only one move: ask exactly one short clarifying business question.\n- Do not prepend a value monologue before that short question.\n- Do not combine a value statement plus a qualification question in the same turn after a vague or garbled user reply.\n- For a vague acknowledgement after the opener, preferred next move is one short question such as whether they work with lipolytics or whether it is relevant at all.\n- If the user reply is too garbled to extract stable meaning, ask one short clarification instead of assuming interest or launching a longer pitch.\n- This rule has priority over generic value-hook expansion after unclear acknowledgements.\n\nAbsolute plain-text override:\n- Spoken output must be plain Russian text only.\n- Never output bracketed stage directions, emotional labels, or control tags of any kind.\n- Forbidden examples include `[calm]`, `[pause]`, `[thinking]`, `[friendly]`, `[slow]`, `[fast]`, or any other square-bracket annotation.\n- If a drafted answer contains any bracket tag, regenerate it into plain text before speaking.\n- Do not preserve bracket tags even if they seem stylistic or harmless.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: unclear acknowledgement -> one short question, no bracket tags"
