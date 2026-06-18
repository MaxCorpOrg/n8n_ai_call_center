#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_softfill_cleanup_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Example:
  scripts/prepare_eleven_softfill_cleanup_variant.sh \
    .runtime/eleven_lab_gpt5mini_v3_softfill_2026-06-17/revert_after_fastlane/response.json \
    .runtime/eleven_lab_gpt5mini_v3_softfill_cleanup_2026-06-17/payload.json \
    "Lab: V3 softfill cleanup for rescue and single close"

Builds a minimal prompt-only cleanup payload on top of the current
GPT-5 Mini + Eleven v3 + softfill lab snapshot.

What it changes:
  - keeps current LLM / TTS / workflow / platform settings
  - locks soft-timeout filler to fixed "Так..." instead of LLM-generated filler
  - hardens post-opener lexical reply handling so rescue cannot reappear
  - hardens final not_target / refusal sequencing so close is spoken once only
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
  | .conversation_config.turn.soft_timeout_config.timeout_seconds = 2.8
  | .conversation_config.turn.soft_timeout_config.message = "Так..."
  | .conversation_config.turn.soft_timeout_config.additional_soft_timeout_messages = []
  | .conversation_config.turn.soft_timeout_config.use_llm_generated_message = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.agent.prompt.prompt += "\n\nPost-opener lexical reply hard-cancel override:\n- After the exact opener, any lexical live-human reply counts as a meaningful answer and permanently cancels rescue for the rest of the call.\n- This includes short replies such as: \"алло\", \"чего\", \"что?\", \"да\", \"нет\", \"секунду\", \"подождите\", \"слышно?\", or another directed human word.\n- Once such a lexical reply appears after the opener, do not answer with a line-check and do not return to rescue mode later in the same call.\n- In that case, respond to the business meaning directly, even if the reply is short, confused, hesitant, or overlaps with your previous turn.\n- Do not treat post-opener \"алло?\" as silence. It is a live reply.\n- Never use bracketed tags or stage directions in any spoken text at all. Forbidden examples: \"[slow]\", \"[pause]\", \"[thinking]\", \"[calm]\".\n- If a soft-timeout filler is needed while you are still thinking, it must stay exactly one short non-question filler and must not become a line-check.\n\nSingle-close hard sequencing override:\n- On final live-human outcomes such as `not_target`, `refusal_soft`, or another terminal refusal, do not speak the closing sentence as a normal assistant message before tools.\n- Preferred hard order is always: first silent `call_log`, then one spoken `end_call` close, then stop.\n- If you already started drafting a spoken close before `call_log`, discard that draft and keep the close only inside `end_call.system__message_to_speak`.\n- Never say the same close twice.\n- A trailing noise fragment such as `...`, rustling, or a non-business `алло` after the user already clearly refused does not justify a second spoken close.\n- For a clear `not_target`, the only spoken close should be exactly one short sentence inside `end_call`, for example: `Поняла, спасибо. Хорошего дня.`\n\nFinalization silence hard gate override:\n- Once you have already determined a final outcome like `not_target`, `refusal_soft`, `no_answer`, `busy`, or successful post-SMS wrap-up, your next action must be backend finalization, not another normal spoken assistant turn.\n- In finalization mode, do not emit any ordinary assistant message before `call_log`.\n- In finalization mode, soft-timeout filler is forbidden. Do not say `Так...`, `Поняла...`, or any other filler while drafting `call_log` or `end_call`.\n- In finalization mode, stay silent while tools are being prepared.\n- A trailing `...`, rustling, or a non-business line-check after a clear final refusal does not reopen the dialogue and does not justify filler, rescue, or a second close.\n- For clear `not_target`, the correct sequence is exactly: silent `call_log(not_target)` -> one `end_call` close -> stop.\n\nConflict-resolution examples override:\n- If any earlier line in the prompt conflicts with the examples below, the examples below win.\n- Correct example after opener:\n  - user: `Алло?`\n  - assistant: answer the business meaning directly.\n  - forbidden: `Алло, вы на линии?`\n- Correct example after opener:\n  - user: `Чего?`\n  - assistant: explain what ЛипоЛонг is in one short sentence and ask one short business question.\n  - forbidden: rescue line-check.\n- Correct final `not_target` example:\n  1. user: `Нет, не работаем.`\n  2. assistant: silent `call_log(not_target)`\n  3. assistant: `end_call(system__message_to_speak=\"Поняла, спасибо. Хорошего дня.\")`\n- Forbidden final `not_target` example:\n  1. assistant says `Поняла, спасибо. Хорошего дня.` as a normal turn\n  2. assistant says filler like `Так...` or asks `Вы на линии?`\n  3. assistant then calls `call_log`\n  4. assistant repeats `Поняла, спасибо. Хорошего дня.` inside `end_call`\n"
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Soft timeout filler fixed to: Так..."
echo "Added overrides: lexical reply cancels rescue, single-close hard sequencing"
