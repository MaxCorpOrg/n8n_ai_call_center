#!/usr/bin/env bash
set -euo pipefail

SERVER_ALIAS="${SERVER_ALIAS:-ai-core-prod-147}"
DEFAULT_AGENT_ID="${DEFAULT_AGENT_ID:-agent_8801kgybyekned2a8yae6rp8hk3q}"
DEFAULT_USER_LLM="${DEFAULT_USER_LLM:-gpt-4.1-mini}"
DEFAULT_USER_LANGUAGE="${DEFAULT_USER_LANGUAGE:-ru}"
DEFAULT_NEW_TURNS_LIMIT="${DEFAULT_NEW_TURNS_LIMIT:-12}"
DEFAULT_CALLED_NUMBER="${DEFAULT_CALLED_NUMBER:-+79990000000}"
DEFAULT_CONVERSATION_ID_PREFIX="${DEFAULT_CONVERSATION_ID_PREFIX:-conv_sim_probe}"
DEFAULT_MOCKED_TOOLS="${DEFAULT_MOCKED_TOOLS:-call_log send_sms_info context_fetch}"

usage() {
  cat <<'EOF' >&2
Usage:
  run_eleven_simulation_probe_via_server_env.sh OUTPUT_DIR USER_PROMPT

Environment overrides:
  AGENT_ID=agent_...
  USER_LLM=gpt-4.1-mini
  USER_LANGUAGE=ru
  NEW_TURNS_LIMIT=12
  SIM_CALLED_NUMBER=+79990000000
  SIM_CONVERSATION_ID=conv_sim_probe_custom
  PARTIAL_HISTORY_FILE=/abs/path/history.json
  MOCKED_TOOLS="call_log send_sms_info context_fetch"

Examples:
  scripts/run_eleven_simulation_probe_via_server_env.sh \
    .runtime/sim_basic_2026-06-26 \
    "First answer only: Алло. Then stay silent."

  PARTIAL_HISTORY_FILE=.runtime/sim_history.json \
  scripts/run_eleven_simulation_probe_via_server_env.sh \
    .runtime/sim_post_opener_silence_2026-06-26 \
    "Stay silent unless the caller clearly asks a direct follow-up question."
EOF
  exit 1
}

if [[ $# -lt 2 ]]; then
  usage
fi

OUTPUT_DIR="$1"
USER_PROMPT="$2"
AGENT_ID="${AGENT_ID:-$DEFAULT_AGENT_ID}"
USER_LLM="${USER_LLM:-$DEFAULT_USER_LLM}"
USER_LANGUAGE="${USER_LANGUAGE:-$DEFAULT_USER_LANGUAGE}"
NEW_TURNS_LIMIT="${NEW_TURNS_LIMIT:-$DEFAULT_NEW_TURNS_LIMIT}"
SIM_CALLED_NUMBER="${SIM_CALLED_NUMBER:-$DEFAULT_CALLED_NUMBER}"
SIM_CONVERSATION_ID="${SIM_CONVERSATION_ID:-${DEFAULT_CONVERSATION_ID_PREFIX}_$(date +%Y%m%d_%H%M%S)}"
PARTIAL_HISTORY_FILE="${PARTIAL_HISTORY_FILE:-}"
MOCKED_TOOLS="${MOCKED_TOOLS:-$DEFAULT_MOCKED_TOOLS}"

mkdir -p "$OUTPUT_DIR"

REMOTE_ENV_PATH="$(ssh -o BatchMode=yes "$SERVER_ALIAS" '
for p in /home/aicore/n8n-server/.env.callcenter /home/aicore/n8n-ai-clean/.env.callcenter; do
  if [ -f "$p" ]; then
    printf "%s\n" "$p"
    exit 0
  fi
done
exit 1
')"

if [[ -z "$REMOTE_ENV_PATH" ]]; then
  echo "Could not find remote .env.callcenter via $SERVER_ALIAS" >&2
  exit 1
fi

REMOTE_KEY="$(ssh -o BatchMode=yes "$SERVER_ALIAS" "grep -E '^(ELEVENLABS_API_KEY|ELEVEN_API_KEY)=' '$REMOTE_ENV_PATH' | head -n1 | cut -d= -f2- | sed -e 's/^\\\"//' -e 's/\\\"$//' -e \"s/^'//\" -e \"s/'$//\"")"

if [[ -z "$REMOTE_KEY" ]]; then
  echo "Could not extract ElevenLabs API key from $REMOTE_ENV_PATH" >&2
  exit 1
fi

PAYLOAD_JSON="$OUTPUT_DIR/payload.json"
RESPONSE_JSON="$OUTPUT_DIR/response.json"
SUMMARY_JSON="$OUTPUT_DIR/summary.json"

TOOLS_JSON='{}'
for tool_name in $MOCKED_TOOLS; do
  TOOLS_JSON="$(jq \
    --arg tool_name "$tool_name" \
    '. + {($tool_name): {default_return_value: "{\"ok\":true,\"mocked\":true}", default_is_error: false}}' \
    <<<"$TOOLS_JSON")"
done

if [[ -n "$PARTIAL_HISTORY_FILE" && ! -f "$PARTIAL_HISTORY_FILE" ]]; then
  echo "Partial history file not found: $PARTIAL_HISTORY_FILE" >&2
  exit 1
fi

jq -n \
  --arg user_prompt "$USER_PROMPT" \
  --arg user_llm "$USER_LLM" \
  --arg user_language "$USER_LANGUAGE" \
  --arg called_number "$SIM_CALLED_NUMBER" \
  --arg conversation_id "$SIM_CONVERSATION_ID" \
  --argjson new_turns_limit "$NEW_TURNS_LIMIT" \
  --argjson tool_mock_config "$TOOLS_JSON" \
  --slurpfile partial_history "${PARTIAL_HISTORY_FILE:-/dev/null}" '
  {
    simulation_specification: {
      simulated_user_config: {
        language: $user_language,
        prompt: {
          prompt: $user_prompt,
          llm: $user_llm
        }
      },
      dynamic_variables: {
        system__called_number: $called_number,
        system__conversation_id: $conversation_id
      },
      tool_mock_config: $tool_mock_config
    },
    new_turns_limit: $new_turns_limit
  }
  | if ($partial_history | length) > 0 and ($partial_history[0] | type) == "array" then
      .simulation_specification.partial_conversation_history = $partial_history[0]
    else
      .
    end
' > "$PAYLOAD_JSON"

curl -sS -X POST \
  "https://api.elevenlabs.io/v1/convai/agents/${AGENT_ID}/simulate-conversation" \
  -H "xi-api-key: ${REMOTE_KEY}" \
  -H "Content-Type: application/json" \
  --data @"$PAYLOAD_JSON" \
  > "$RESPONSE_JSON"

jq '{
  turns: (.simulated_conversation | length),
  agent_turns: ([.simulated_conversation[] | select(.role == "agent")] | length),
  user_turns: ([.simulated_conversation[] | select(.role == "user")] | length),
  first_agent_message: (
    [.simulated_conversation[] | select(.role == "agent" and (.message // "") != "") | .message][0] // null
  ),
  tool_calls: [
    .simulated_conversation[]
    | select(((.tool_calls // []) | length) > 0)
    | {
        role,
        tool_names: [.tool_calls[]?.tool_name]
      }
  ],
  branch_ids_seen: [
    .simulated_conversation[]
    | .agent_metadata?.branch_id
    | select(. != null)
  ] | unique,
  version_ids_seen: [
    .simulated_conversation[]
    | .agent_metadata?.version_id
    | select(. != null)
  ] | unique,
  call_summary_title: (.analysis.call_summary_title // null),
  transcript_summary: (.analysis.transcript_summary // null)
}' "$RESPONSE_JSON" > "$SUMMARY_JSON"

echo "Saved payload:  $PAYLOAD_JSON"
echo "Saved response: $RESPONSE_JSON"
echo "Saved summary:  $SUMMARY_JSON"
jq '.' "$SUMMARY_JSON"
