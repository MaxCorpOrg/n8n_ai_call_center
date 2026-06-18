#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_sms_fastlane_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Example:
  scripts/prepare_eleven_sms_fastlane_variant.sh \
    .runtime/eleven_lab_gpt5mini_v3_softfill_2026-06-17/apply_result/response.json \
    .runtime/eleven_lab_gpt5mini_v3_sms_fastlane_2026-06-17/payload.json \
    "Lab: GPT-5 Mini + Eleven V3 + SMS fastlane"

Builds a minimal ElevenLabs Update Agent payload that keeps the current
LLM / TTS / workflow / platform settings and only appends a prompt override
for faster transition into send_sms_info after explicit SMS consent.

The helper removes prompt.tools and keeps prompt.tool_ids to avoid
Update Agent conflicts between resolved tools and tool_ids.
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
  | .conversation_config.agent.prompt.prompt += "\n\nSMS decision-gap fastlane override:\n- If the user explicitly asks to send SMS, text, contact details, product info by message, or says they will read it later and call back themselves, treat that as the final next step immediately.\n- Examples include: \"отправьте смс\", \"скиньте смс\", \"давайте смс\", \"отправьте информацию\", \"я сам перезвоню, отправьте смс\", \"пришлите на этот номер\".\n- If explicit SMS intent is present, your very next action should be `send_sms_info`.\n- Do not spend an extra turn summarizing, re-explaining, comparing products, or asking another question.\n- Do not wait for a cleaner reformulation if the request is already understandable.\n- If the same user utterance also contains hesitation, off-topic words, flirt, jokes, filler sounds, or a goodbye, ignore that noise and still move straight to `send_sms_info`.\n- In this explicit SMS case, avoid a thinking filler before the tool call whenever possible. Prefer immediate tool execution over spoken hesitation.\n- After `send_sms_info` succeeds, go straight to short close and end_call. Do not reopen the dialogue.\n"
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "SMS fastlane override appended to prompt"
