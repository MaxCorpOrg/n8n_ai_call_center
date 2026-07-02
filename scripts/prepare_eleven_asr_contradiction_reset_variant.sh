#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_asr_contradiction_reset_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow prompt-only payload that:
  - handles "I did not say that / what are you talking about" resets
  - blocks late line-check and premature qualification after a contradiction
  - adds a short hostile-confusion exit
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
      sub("\\n\\nASR contradiction reset override:[\\s\\S]*$"; "")
      + "\n\nASR contradiction reset override:\n- If the user says they did not say that, you misheard them, you misunderstood them, or sounds confused by your previous interpretation, treat that as an ASR-contradiction reset, not as a normal business answer.\n- Strong reset examples include phrases like: `я этого не говорил`, `вы что`, `вы чё`, `ошиблись`, `не понял`, `что вы имеете в виду`, `я не это сказал`, `вы меня не так поняли`.\n- After such a contradiction reset, do not ask a line-check like `Вы на линии?`.\n- After such a contradiction reset, do not jump into qualification like `Вы вообще с липолитиками работаете?`.\n- If the exact opener has not yet been delivered cleanly, immediately reset and deliver the exact opener cleanly once from the beginning.\n- If the exact opener was already delivered earlier, then answer the confusion in one short sentence and continue from the latest real business meaning.\n- Do not continue the wrong branch after the user denies that branch.\n- A contradiction reset cancels any pending callback-later, no_answer, rescue, or qualification path that was inferred from the previous ambiguous fragment.\n\nHostile confusion exit override:\n- If right after a contradiction reset the user adds strong directed hostility or profanity and there is still no stable business dialogue, do not keep selling and do not continue qualification.\n- In that case, use one very short calm close, log the final outcome, and end the call.\n- Do not answer hostility with `Вы на линии?`.\n- Do not answer hostility with a product-qualification question.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: ASR contradiction reset + hostile confusion exit"
