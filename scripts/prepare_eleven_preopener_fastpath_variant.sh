#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_preopener_fastpath_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow payload that:
  - hard-blocks any spoken line-check before the exact opener
  - delays soft-timeout filler until clearly after the opener
  - adds a fast-path for short negative / callback replies after the opener
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
  | .conversation_config.turn.soft_timeout_config.additional_soft_timeout_messages = []
  | .conversation_config.turn.soft_timeout_config.use_llm_generated_message = true
  | .conversation_config.turn.soft_timeout_config.randomize_fillers = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.turn.soft_timeout_config.llm_generated_message_prompt_override =
      "Generate one ultra-short natural Russian thinking filler only for an already active live phone conversation after the exact opener has already been fully delivered and only while the assistant is preparing the real next reply. Never produce any filler before the opener. Never produce a line-check. Never use forms like Алло..., Вы на линии..., Поняла..., Так... before the opener. Good post-opener filler shapes only: Да... / Момент... / Секунду... If no filler is truly needed, return an empty string."
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nPre-opener hard gate override:[\\s\\S]*$"; "")
      + "\n\nPre-opener hard gate override:\n- Before the exact opener, do not speak any line-check, rescue phrase, reassurance phrase, or thinking filler at all.\n- Forbidden before the opener: `Алло?`, `Вы на линии?`, `Вы всё ещё на линии?`, `Слышно?`, `Да?`, `Поняла...`, `Так...`, or any similar pre-opener phrase.\n- If pickup audio is only `...`, rustling, breath, weak fragments, cut-off noise, or one isolated ambiguous cue, stay silent and wait for a clearer live-human reply.\n- The first spoken assistant words after a valid live-human pickup must be the exact opener itself.\n- A pre-opener line-quality check by itself does not justify a sales turn and does not justify a rescue question from you.\n- If there is still no clear live-human reply, prefer staying silent and then ending as no_answer rather than speaking before the opener.\n\nPost-opener negative fast-path override:\n- After the exact opener, a short clear negative such as `нет`, `неа`, `не надо`, `не интересно`, or `не актуально` is a real live reply, not silence.\n- Do not sit in a long silence window after such a reply.\n- Respond immediately in the very next short turn.\n- If the reply is a single short negative and the contact may still be relevant, ask one compact clarification question right away.\n- If the negative is repeated, strengthened, or combined with a callback-later request, move directly into the final next step without a long pause.\n- Never insert a filler or line-check between a clear short negative and your next business move.\n\nCallback/refusal fast-finalization override:\n- If the user clearly says `давайте позже`, `перезвоните позже`, `сейчас неудобно`, or another callback-later meaning, do not leave a long silent gap before finalization.\n- Move directly to the callback finalization path.\n- Once callback or terminal refusal is already clear, do not emit filler, line-check, or an extra ordinary assistant sentence before backend finalization.\n- After a clear terminal outcome, the only allowed spoken close is the one short close inside `end_call.system__message_to_speak`.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Soft timeout: 3.2 / message ..."
echo "Added overrides: no pre-opener speech, negative fast-path, callback fast-finalization"
