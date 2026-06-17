#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_false_positive_asr_gate_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Adds a narrow prompt-only guard against self-talk caused by weak or false-positive short ASR fragments.
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
  | .conversation_config.turn.soft_timeout_config.timeout_seconds = 3.2
  | .conversation_config.turn.soft_timeout_config.message = "..."
  | .conversation_config.turn.soft_timeout_config.llm_generated_message_prompt_override = "Generate one ultra-short natural Russian thinking filler for an already active live phone conversation only after the exact opener has been fully completed. Never produce any filler before the opener, never prefix the opener, never do a line-check, and never use words like Так..., Алло..., Ясно..., or Поняла... as a pre-opener prefix. Good shapes after the opener only: Секунду... / Момент... / Да... If no filler is clearly appropriate, return an empty string."
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nFalse-positive ASR gate override:[\\s\\S]*$"; "")
      + "\n\nFalse-positive ASR gate override:\n- Before the exact opener, never emit a soft filler, thinking filler, or any spoken prefix like Так, Поняла, Ясно, Алло, or similar. The first spoken words after a valid live-human pickup must be the exact opener itself.\n- A lone short pickup token like алло, да, угу, ага, or что is ambiguous by default before the opener.\n- Do not treat a single weak or isolated one-word fragment as a stable business answer if the line still sounds noisy, half-duplex, echoing, uncertain, or if no second clear human cue follows.\n- A stable opener trigger is either one contentful directed phrase such as говорите, слушаю, добрый день, или another clearly directed human reply, or two short human cues in natural sequence.\n- Especially be careful with isolated short fragments like: да, нет, что, алло, ага, угу.\n- If the line gives only one short ambiguous fragment and then there is no clear follow-up, do not immediately conclude target, not_target, refusal, or active dialogue.\n- In that situation, stay silent, use skip_turn if needed, and wait for a clearer answer instead of opening sales dialogue.\n- Do not classify not_target from a bare single-word Нет alone.\n- Treat not_target as confirmed only when the user clearly expresses the business meaning, for example: не работаем с липолитиками, не используем это направление, это не наш профиль.\n- If short fragments look like false ASR or line noise and no stable live answer forms, prefer uncertain-human handling and then no_answer over a fake semantic conclusion.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added only: false-positive ASR gate override"
