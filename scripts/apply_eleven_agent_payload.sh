#!/usr/bin/env bash
set -euo pipefail

DEFAULT_AGENT_ID="agent_8801kgybyekned2a8yae6rp8hk3q"
DEFAULT_BRANCH_ID="agtbrch_3701kv7waz0teny9xvsgv7sjt0bp"
MAIN_BRANCH_ID="agtbrch_7801kgybyg9nesrbv64y078pazq0"

usage() {
  cat <<'EOF' >&2
Usage:
  apply_eleven_agent_payload.sh PAYLOAD_JSON OUTPUT_DIR [AGENT_ID] [BRANCH_ID] [--dry-run]

Environment:
  ELEVENLABS_API_KEY   API key for ElevenLabs
  ELEVEN_API_KEY       fallback name for the same key
  ELEVEN_ENV_FILE      optional dotenv file to source key from
  ALLOW_MAIN_BRANCH_APPLY=1   required only if you intentionally target Main

Examples:
  ELEVEN_ENV_FILE=/tmp/.env.callcenter \
  scripts/apply_eleven_agent_payload.sh \
    .runtime/eleven_lab_llm_compare_gemini_2026-06-16/payload.json \
    .runtime/eleven_lab_llm_compare_gemini_2026-06-16/apply_result

  scripts/apply_eleven_agent_payload.sh \
    .runtime/eleven_lab_llm_compare_gemini_2026-06-16/payload.json \
    .runtime/eleven_lab_llm_compare_gemini_2026-06-16/apply_result \
    agent_8801kgybyekned2a8yae6rp8hk3q \
    agtbrch_3701kv7waz0teny9xvsgv7sjt0bp \
    --dry-run
EOF
  exit 1
}

if [[ $# -lt 2 ]]; then
  usage
fi

PAYLOAD_JSON="$1"
OUTPUT_DIR="$2"
AGENT_ID="${3:-$DEFAULT_AGENT_ID}"
BRANCH_ID="${4:-$DEFAULT_BRANCH_ID}"
DRY_RUN="${5:-}"

if [[ "$AGENT_ID" == "--dry-run" ]]; then
  AGENT_ID="$DEFAULT_AGENT_ID"
  BRANCH_ID="$DEFAULT_BRANCH_ID"
  DRY_RUN="--dry-run"
elif [[ "$BRANCH_ID" == "--dry-run" ]]; then
  BRANCH_ID="$DEFAULT_BRANCH_ID"
  DRY_RUN="--dry-run"
fi

if [[ "$DRY_RUN" != "" && "$DRY_RUN" != "--dry-run" ]]; then
  echo "Unknown fifth argument: $DRY_RUN" >&2
  usage
fi

if [[ ! -f "$PAYLOAD_JSON" ]]; then
  echo "Payload file not found: $PAYLOAD_JSON" >&2
  exit 1
fi

if [[ "$BRANCH_ID" == "$MAIN_BRANCH_ID" && "${ALLOW_MAIN_BRANCH_APPLY:-}" != "1" ]]; then
  echo "Refusing to target live Main branch without ALLOW_MAIN_BRANCH_APPLY=1" >&2
  exit 1
fi

if [[ -n "${ELEVEN_ENV_FILE:-}" ]]; then
  if [[ ! -f "${ELEVEN_ENV_FILE}" ]]; then
    echo "ELEVEN_ENV_FILE not found: ${ELEVEN_ENV_FILE}" >&2
    exit 1
  fi
  # shellcheck disable=SC1090
  set -a && source "${ELEVEN_ENV_FILE}" && set +a
fi

API_KEY="${ELEVENLABS_API_KEY:-${ELEVEN_API_KEY:-}}"

mkdir -p "$OUTPUT_DIR"

REQUEST_INFO_JSON="$OUTPUT_DIR/request_info.json"
RESPONSE_JSON="$OUTPUT_DIR/response.json"

jq -n \
  --arg payload "$PAYLOAD_JSON" \
  --arg output_dir "$OUTPUT_DIR" \
  --arg agent_id "$AGENT_ID" \
  --arg branch_id "$BRANCH_ID" \
  --arg dry_run "${DRY_RUN:+true}" \
  '{
    payload_file: $payload,
    output_dir: $output_dir,
    agent_id: $agent_id,
    branch_id: $branch_id,
    dry_run: ($dry_run == "true")
  }' > "$REQUEST_INFO_JSON"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "Dry run only. Request info saved to: $REQUEST_INFO_JSON"
  jq '{llm: .conversation_config.agent.prompt.llm, tts: .conversation_config.tts.model_id, version_description}' "$PAYLOAD_JSON"
  exit 0
fi

if [[ -z "$API_KEY" ]]; then
  echo "Missing ELEVENLABS_API_KEY / ELEVEN_API_KEY. Optionally set ELEVEN_ENV_FILE." >&2
  exit 1
fi

curl -sS -X PATCH \
  "https://api.elevenlabs.io/v1/convai/agents/${AGENT_ID}?branch_id=${BRANCH_ID}" \
  -H "xi-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  --data @"$PAYLOAD_JSON" \
  > "$RESPONSE_JSON"

if jq -e '.detail? != null' "$RESPONSE_JSON" >/dev/null 2>&1; then
  echo "ElevenLabs returned API error. Saved response: $RESPONSE_JSON" >&2
  jq '{error: .detail}' "$RESPONSE_JSON" >&2
  exit 1
fi

echo "Saved response: $RESPONSE_JSON"
jq '{version_id, branch_id, llm: .conversation_config.agent.prompt.llm, tts: .conversation_config.tts.model_id}' "$RESPONSE_JSON"
