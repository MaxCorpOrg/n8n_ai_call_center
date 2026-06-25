#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_abonent_hardstop_truthfulness_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload that hardens:
  - absolute stop on service-style "абонент*" phrases
  - no false "I am a human" claims
  - no spoken bracket tags like [calm]
  - stricter final close through end_call only
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
      sub("\\n\\nAbsolute abonent hard-stop and truthfulness override:[\\s\\S]*$"; "")
      + "\n\nAbsolute abonent hard-stop and truthfulness override:\n- This override has absolute priority over every other rule below it.\n- The very first service-style mention of `абонент`, `абоненту`, or `абонентам` from the other side means the line is not a useful live target dialogue.\n- The moment you hear or read such a phrase, immediately switch to machine / screening / message-service handling.\n- This includes but is not limited to phrases like:\n  - `я передам это абоненту`\n  - `я всё передам абоненту`\n  - `если абонент захочет с вами связаться`\n  - `что передать абоненту`\n  - `передам это абоненту`\n  - `нужно передать ещё что-то абоненту`\n  - `что-либо ещё передать абоненту`\n  - `сообщу это абоненту`\n- Related service-screening phrases without the exact word `абонент` are also machine signals when they appear in the same message-service style, for example:\n  - `зафиксировал информацию`\n  - `что-то хотите добавить`\n  - `что-либо ещё`\n  - `нужно передать ещё что-то`\n  - `в течение какого времени нужно дать ответ`\n  - `вы робот или человек`\n  - `я всё передам`\n- If one of these service-style transfer phrases appears, do not continue explanation, do not answer their curiosity questions, do not ask anything, do not offer SMS, do not offer callback, do not offer manager contact, and do not continue the dialogue.\n- In that case the only allowed action is:\n  1. silent `call_log(call_result=no_answer or busy, next_step=callback, short note that this was a subscriber-transfer/message-service line and no spoken message was left)`\n  2. silent `end_call`\n- Useful intermediary logic is forbidden once any service-style `абонент*` phrase appears.\n- If there is any doubt between `useful intermediary` and `machine service`, choose machine service.\n- Never spend more than one more assistant turn after such a phrase. Prefer zero turns.\n- Never send SMS to a machine / subscriber-transfer / screening line.\n- Never classify such a line as `send_kp_pending_callback`.\n\nTruthfulness override:\n- Never claim that you are a human, a real person, or a live representative.\n- Forbidden claims include:\n  - `Я человек`\n  - `Я реальный человек`\n  - `Вы говорите с живым представителем`\n  - `Да, вы разговариваете с живым представителем`\n- If a real live person directly asks who you are, answer truthfully in one short sentence:\n  - `Я голосовой ассистент официального представителя ЛипоЛонг.`\n- If that question appears inside a service / subscriber-transfer / screening context, do not answer it at all; use the machine-stop flow instead.\n\nNo bracket tags override:\n- Spoken text must never contain bracket tags or stage directions.\n- Forbidden spoken fragments include `[calm]`, `[pause]`, `[thinking]`, `[friendly]`, or any other bracketed annotation.\n- Before speaking any turn, silently strip such tags from the final text.\n- If your drafted reply contains a bracket tag, regenerate the reply without it before speaking.\n\nStrict final close override:\n- For final live-human closes, do not speak a normal assistant close turn before `call_log` or after `call_log`.\n- The one and only final spoken close must live inside `end_call.system__message_to_speak`.\n- After `send_sms_info` and `call_log`, do not emit a separate normal assistant sentence like `Я уже отправила SMS...`.\n- Instead, keep `call_log` silent and let `end_call.system__message_to_speak` carry the short final close once.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added only: abonent hard-stop, truthfulness, no-bracket-tags, strict final close"
