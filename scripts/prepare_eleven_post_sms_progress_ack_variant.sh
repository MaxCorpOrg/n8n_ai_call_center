#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_post_sms_progress_ack_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow ElevenLabs payload that:
  - keeps the current branch behavior intact
  - adds one immediate spoken acknowledgement before send_sms_info
  - keeps the final SMS close only inside end_call
  - avoids tool music and dead silence on the SMS-consent path

Optional environment overrides:
  TARGET_SOFT_TIMEOUT      default: 2.6
  TARGET_SOFT_MESSAGE      default: Да...
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_JSON="$2"
VERSION_DESCRIPTION="${3:-}"
TARGET_SOFT_TIMEOUT="${TARGET_SOFT_TIMEOUT:-2.6}"
TARGET_SOFT_MESSAGE="${TARGET_SOFT_MESSAGE:-Да...}"

if [[ ! -f "$SOURCE_JSON" ]]; then
  echo "Source file not found: $SOURCE_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSON")"

jq \
  --arg version_description "$VERSION_DESCRIPTION" \
  --argjson target_soft_timeout "$TARGET_SOFT_TIMEOUT" \
  --arg target_soft_message "$TARGET_SOFT_MESSAGE" '
  {
    conversation_config: .conversation_config,
    platform_settings: .platform_settings,
    workflow: .workflow
  }
  | del(.conversation_config.agent.prompt.tool_ids)
  | .conversation_config.turn.soft_timeout_config.timeout_seconds = $target_soft_timeout
  | .conversation_config.turn.soft_timeout_config.message = $target_soft_message
  | .conversation_config.turn.soft_timeout_config.additional_soft_timeout_messages = []
  | .conversation_config.turn.soft_timeout_config.use_llm_generated_message = true
  | .conversation_config.turn.soft_timeout_config.randomize_fillers = false
  | .conversation_config.turn.soft_timeout_config.max_soft_timeouts_per_generation = 1
  | .conversation_config.turn.soft_timeout_config.llm_generated_message_prompt_override =
      "Generate one ultra-short natural Russian thinking filler only inside an already active live phone conversation and only while the assistant is preparing the real next reply. Never produce any filler before the exact opener. Never produce a line-check. Never produce a question. Never produce support-style phrases. Never use forms like Алло..., Да, я на линии..., Я на линии..., Секунду..., Момент..., Поняла..., or Сейчас.... Good shapes are only very short neutral spoken fillers such as: Да... / Угу... / Так... / Хорошо... If no filler is clearly needed, return an empty string."
  | .conversation_config.agent.prompt.tools =
      (.conversation_config.agent.prompt.tools
       | map(
           if .name == "send_sms_info" then
             .pre_tool_speech = "force"
             | .tool_call_sound = null
             | .tool_call_sound_behavior = "auto"
           elif .name == "call_log" then
             .pre_tool_speech = "off"
             | .tool_call_sound = null
             | .tool_call_sound_behavior = "auto"
           elif .name == "context_fetch" then
             .tool_call_sound = null
             | .tool_call_sound_behavior = "auto"
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nPost-SMS progress ack override:[\\s\\S]*$"; "")
      + "\n\nPost-SMS progress ack override:\n- If the user gives explicit permission to send SMS or contact info, do not leave dead silence before backend work starts.\n- On explicit SMS consent, give one ultra-short spoken acknowledgement immediately, then call `send_sms_info` right away.\n- Good acknowledgement shapes are short and natural, for example: `Да...`, `Да, отправляю.`, `Хорошо...`.\n- This acknowledgement is a progress cue, not the final close.\n- Do not ask a new question after SMS consent.\n- Do not continue pitching after SMS consent.\n- Do not produce more than one acknowledgement before `send_sms_info`.\n- After that acknowledgement, execute `send_sms_info` immediately.\n- After successful `send_sms_info`, keep the normal assistant message silent during backend finalization.\n- The only final spoken close after SMS success must remain inside `end_call.system__message_to_speak`.\n- Forbidden SMS consent sequence:\n  1. user agrees to SMS\n  2. 3 to 4 seconds of silence\n  3. `send_sms_info`\n- Correct SMS consent sequence:\n  1. user agrees to SMS\n  2. one ultra-short spoken acknowledgement\n  3. immediate `send_sms_info`\n  4. silent `call_log`\n  5. one short `end_call` close\n  6. stop\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "soft_timeout: $TARGET_SOFT_TIMEOUT"
echo "soft_message: $TARGET_SOFT_MESSAGE"
echo "Added override: immediate post-SMS spoken acknowledgement before send_sms_info"
