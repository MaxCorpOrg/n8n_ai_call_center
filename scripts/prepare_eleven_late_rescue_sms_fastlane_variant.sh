#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_late_rescue_sms_fastlane_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow update payload on top of the current published snapshot.

What it changes:
  - keeps current LLM / TTS / workflow / platform settings
  - removes resolved prompt.tools to avoid tool_id/update conflicts
  - hard-cancels late rescue after any meaningful post-opener lexical reply
  - accelerates explicit SMS intent directly into send_sms_info
  - avoids spoken filler before send_sms_info where possible
  - keeps opener and machine-stop logic unchanged
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
  | .conversation_config.turn.soft_timeout_config.timeout_seconds = 2.4
  | .conversation_config.turn.soft_timeout_config.message = "Так..."
  | .conversation_config.turn.soft_timeout_config.additional_soft_timeout_messages = []
  | .conversation_config.turn.soft_timeout_config.use_llm_generated_message = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.agent.prompt.prompt += "\n\nLate rescue cancellation override:\n- After the exact opener, any lexical live-human reply counts as a meaningful answer and permanently cancels rescue for the rest of the call.\n- This includes short replies such as: \"алло\", \"чего\", \"что?\", \"да\", \"нет\", \"не интересно\", \"работаем\", \"подождите\", \"слышно?\", or another directed human phrase.\n- Once such a reply appears after the opener, do not answer with a line-check and do not return to rescue mode later in the same call.\n- Do not say `Алло?`, `Вы на линии?`, or similar line-checks after a meaningful business reply already happened.\n- Do not treat post-opener `алло?` as silence if it is spoken by a live human during an active dialogue.\n- If a soft-timeout filler is truly needed while you are still thinking inside an active dialogue, keep it to one very short neutral non-question filler only.\n\nNo stage directions override:\n- Never output bracketed tags, stage directions, or emotion labels in spoken text.\n- Forbidden examples: `[calm]`, `[pause]`, `[thinking]`, `[slow]`, `(calmly)`, `(pause)`.\n- Spoken text must always be plain natural Russian only.\n\nExplicit SMS fastlane override:\n- If the user explicitly asks to send SMS, text, contact details, product info by message, or says they will read it later and call back themselves, treat that as the final next step immediately.\n- Examples include: \"отправьте смс\", \"скиньте смс\", \"давайте смс\", \"отправьте информацию\", \"я сам перезвоню, отправьте смс\", \"пришлите на этот номер\".\n- If explicit SMS intent is present, your very next action should be `send_sms_info`.\n- Do not spend an extra turn summarizing, re-explaining, comparing products, or asking another question after explicit SMS consent.\n- Do not wait for a cleaner reformulation if the request is already understandable.\n- In this explicit SMS case, avoid a thinking filler before the tool call whenever possible. Prefer immediate tool execution over spoken hesitation.\n- After `send_sms_info` succeeds, confirm it once briefly and finish the call cleanly.\n- After successful `send_sms_info`, do not reopen the dialogue with a new question.\n\nTerminal callback finalization override:\n- If the user clearly asks to talk later, says they are busy now, asks for a callback later, or says `перезвоните позже`, that is a terminal callback outcome.\n- In a terminal callback outcome, the correct order is exactly:\n  1. silent `call_log(callback_scheduled)`\n  2. one short spoken `end_call`\n  3. stop\n- After `call_log(callback_scheduled)`, do not ask `Могу чем-то ещё помочь?` and do not reopen the dialogue.\n- Callback finalization is not a support dialogue. No helpdesk tails are allowed.\n- Good close shape: `Поняла, перезвоню позже. Хорошего дня.`\n- Forbidden close shape: `Поняла, перезвоню позже. Могу чем-то ещё помочь?`\n"
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added overrides: late rescue cancellation + explicit SMS fastlane"
