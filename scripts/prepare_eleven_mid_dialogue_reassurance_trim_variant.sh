#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_mid_dialogue_reassurance_trim_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Adds a narrow prompt-only override that prevents support-style reassurance
inside an already active business dialogue.
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
      sub("\\n\\nMid-dialogue reassurance trim override:[\\s\\S]*$"; "")
      + "\n\nMid-dialogue reassurance trim override:\n- Inside an already active live business dialogue, do not switch into support-style reassurance turns.\n- Forbidden reassurance shapes include: `Да, я тут`, `Я тут`, `Да, я на линии`, `Я на линии`, `Да, слышу вас`, `Я вас слышу`.\n- If the user throws in a short line-check like `алло?`, `слышно?`, or another brief overlap while the business topic is still active, do not answer with a separate reassurance sentence.\n- Instead, continue directly from the latest business meaning in one short sentence or one short business question.\n- Do not repeat the same qualifying question after a noisy overlap unless the previous question was genuinely not delivered.\n- A short interrupted user echo or garbled ASR fragment does not justify falling back into receptionist mode.\n- If the user line-check happens right after your business question, keep the next move business-focused and concise.\n- Never add bracketed stage directions or tags in spoken text, including `[calm]`, `[pause]`, `[thinking]`, or similar.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added only: mid-dialogue reassurance trim override"
