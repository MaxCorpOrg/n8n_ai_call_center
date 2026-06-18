#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_system_binding_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Example:
  scripts/prepare_eleven_system_binding_variant.sh \
    .runtime/eleven_lab_gpt5mini_v3_softfill_2026-06-17/revert_after_cleanup_series/response.json \
    .runtime/eleven_lab_system_binding_fix_2026-06-17/payload.json \
    "Lab: system binding fix for conversation ids and context gate"

Builds a minimal lab-only payload that:
  - keeps current LLM / TTS / workflow / platform settings
  - preserves prompt.tools so tool schemas can be patched safely
  - binds context_fetch.session_id to system__conversation_id
  - binds send_sms_info.conversation_id to system__conversation_id
  - adds a narrow prompt override so the model stops inventing conv_* ids
    and stops calling context_fetch before the opener for generic context
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
  | .conversation_config.agent.prompt.tools =
      (.conversation_config.agent.prompt.tools
       | map(
           if .name == "context_fetch" then
             .api_schema.request_body_schema.properties.session_id = {
               type: "string",
               description: "",
               enum: null,
               is_system_provided: false,
               dynamic_variable: "system__conversation_id",
               allowed_values_dynamic_variable: "",
               constant_value: "",
               is_omitted: false
             }
           elif .name == "send_sms_info" then
             .api_schema.request_body_schema.properties.conversation_id = {
               type: "string",
               description: "",
               enum: null,
               is_system_provided: false,
               dynamic_variable: "system__conversation_id",
               allowed_values_dynamic_variable: "",
               constant_value: "",
               is_omitted: false
             }
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt += "\n\nSystem-bound tool fields override:\n- Never invent, guess, or hardcode fake conversation ids like `conv_123`, `conv_abcdef`, `conv_current`, or similar placeholders.\n- Never send the literal text `system__conversation_id` as a user-authored value.\n- If a tool field is system-bound by schema, let the system binding fill it instead of drafting your own surrogate value.\n- This especially applies to:\n  - `context_fetch.session_id`\n  - `send_sms_info.conversation_id`\n  - `call_log.conversation_id`\n  - `call_log.eleven_conv_id`\n- If you are unsure of a conversation id, do not fabricate one.\n- For `call_log`, do not manually type `conversation_id` or `eleven_conv_id` in the drafted JSON at all. Leave those schema-bound fields for the system binding.\n- For `send_sms_info`, do not manually type `conversation_id` in the drafted JSON. Leave it to the system binding.\n- If an earlier traceability rule says to include those ids, satisfy that rule by using the system-bound fields, not by fabricating literal `conv_*` text yourself.\n\nContext-fetch gate override:\n- Do not call `context_fetch` on pickup or before the exact opener for a generic request like `initial call context`.\n- Do not call `context_fetch` only to restate data that is already available in dynamic variables.\n- Call `context_fetch` only after a live human dialogue is clearly underway and only if a missing fact is truly needed for the next business answer.\n- In normal opener, qualification, objection, SMS, callback, not_target, no_answer, busy, and machine-stop flows, prefer staying in the live call flow without `context_fetch` unless a real gap blocks the answer.\n"
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Patched bindings:"
echo "  context_fetch.session_id -> system__conversation_id"
echo "  send_sms_info.conversation_id -> system__conversation_id"
echo "Added narrow prompt override for system-bound ids and context-fetch gate"
