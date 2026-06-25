#!/usr/bin/env bash
set -euo pipefail

DEFAULT_AGENT_ID="agent_8801kgybyekned2a8yae6rp8hk3q"
DEFAULT_PHONE_NUMBER_ID="phnum_8501khxz93vnfnnsvdjqn1g92yfs"
DEFAULT_BRANCH_ID="agtbrch_3701kv7waz0teny9xvsgv7sjt0bp"
DEFAULT_LIVE_MAIN_BRANCH_ID="agtbrch_7801kgybyg9nesrbv64y078pazq0"
DEFAULT_WEBHOOK_URL="https://www.n-8-n.site/webhook/eleven/outbound-call"
DEFAULT_LOCAL_RELAY_URL="http://127.0.0.1:18787/eleven/outbound-call"
DEFAULT_RELAY_URL="http://151.241.228.232:8787/eleven/outbound-call"
DEFAULT_TRANSPORT_ORDER="local_relay,relay_via_server,relay,webhook"
DEFAULT_ENVIRONMENT="production"
DEFAULT_POLL_SECONDS=180
DEFAULT_POLL_INTERVAL=5
DEFAULT_CONNECT_TIMEOUT=10
DEFAULT_REQUEST_TIMEOUT=35
SERVER_ALIAS="${SERVER_ALIAS:-ai-core-prod-147}"
TRANSPORT_ORDER="${ELEVEN_SELFTEST_TRANSPORT_ORDER:-$DEFAULT_TRANSPORT_ORDER}"

post_json_with_curl() {
  local url="$1"
  local request_json="$2"
  local output_json="$3"
  local stderr_log="$4"
  local header_name="${5:-}"
  local header_value="${6:-}"

  local -a cmd
  cmd=(
    curl
    -sS
    --connect-timeout "$DEFAULT_CONNECT_TIMEOUT"
    --max-time "$DEFAULT_REQUEST_TIMEOUT"
    -X POST "$url"
    -H "Content-Type: application/json"
    --data @"$request_json"
    -o "$output_json"
    -w "%{http_code}"
  )

  if [[ -n "$header_name" ]]; then
    cmd+=(-H "${header_name}: ${header_value}")
  fi

  "${cmd[@]}" 2> "$stderr_log"
}

response_has_success() {
  local response_json="$1"
  jq -e '
    (
      .success == true
      and (.conversation_id // "") != ""
    )
    or
    (
      (.action // "") == "call_requested"
      and ((.eleven_response.conversation_id // "") != "")
    )
  ' "$response_json" >/dev/null 2>&1
}

response_looks_like_cloudflare_block() {
  local response_file="$1"
  [[ -s "$response_file" ]] || return 1
  if jq -e . "$response_file" >/dev/null 2>&1; then
    return 1
  fi
  grep -qiE 'Just a moment|Enable JavaScript and cookies to continue|help\.elevenlabs\.io|__cf_chl_|cloudflare' "$response_file"
}

response_looks_like_sanctioned_country() {
  local response_file="$1"
  [[ -s "$response_file" ]] || return 1
  jq -e '
    (.status // "") == "sanctioned_country"
    or (.error // "") == "provider_restricted_country"
    or (.message // "") == "This functionality is not available in your location."
  ' "$response_file" >/dev/null 2>&1
}

build_blocked_outbound_json() {
  local source_file="$1"
  local attempts_json="$2"
  local output_json="$3"
  local transport="$4"

  local reason="unknown_upstream_block"
  local note="Outbound request did not create a conversation."

  if response_looks_like_cloudflare_block "$source_file"; then
    reason="cloudflare_challenge"
    note="Outbound request was redirected to a Cloudflare/help.elevenlabs block page instead of returning JSON."
  elif response_looks_like_sanctioned_country "$source_file"; then
    reason="sanctioned_country"
    note="Outbound request was rejected by ElevenLabs because this functionality is not available from the current server location."
  fi

  jq -n \
    --arg reason "$reason" \
    --arg note "$note" \
    --arg transport "$transport" \
    --slurpfile attempts "$attempts_json" \
    '{
      ok: false,
      success: false,
      action: "selftest_blocked",
      reason: $reason,
      note: $note,
      transport: (if $transport == "" then null else $transport end),
      attempts: ($attempts[0] // [])
    }' > "$output_json"
}

extract_conversation_id_from_response() {
  local response_json="$1"
  jq -r '
    if (.success == true and (.conversation_id // "") != "") then
      .conversation_id
    elif ((.action // "") == "call_requested" and (.eleven_response.conversation_id // "") != "") then
      .eleven_response.conversation_id
    else
      ""
    end
  ' "$response_json" 2>/dev/null || true
}

lookup_recent_conversation() {
  local request_json="$1"
  local output_json="$2"
  local remote_key="$3"
  local call_start_after_unix="$4"

  local user_id branch_id
  user_id="$(jq -r '.conversation_initiation_client_data.user_id // ""' "$request_json")"
  branch_id="$(jq -r '.conversation_initiation_client_data.branch_id // ""' "$request_json")"

  if [[ -z "$user_id" || -z "$branch_id" || -z "$remote_key" ]]; then
    return 1
  fi

  local -a curl_cmd
  curl_cmd=(
    curl -sS -G
    "https://api.elevenlabs.io/v1/convai/conversations"
    -H "xi-api-key: ${remote_key}"
    --data-urlencode "user_id=${user_id}"
    --data-urlencode "branch_id=${branch_id}"
    --data-urlencode "page_size=10"
    --data-urlencode "summary_mode=exclude"
  )

  if [[ -n "$call_start_after_unix" ]]; then
    curl_cmd+=(--data-urlencode "call_start_after_unix=${call_start_after_unix}")
  fi

  "${curl_cmd[@]}" > "$output_json"
}

recover_recent_conversation_with_fallback() {
  local request_json="$1"
  local output_json="$2"
  local remote_key="$3"
  local call_start_after_unix="$4"

  if ! lookup_recent_conversation "$request_json" "$output_json" "$remote_key" "$call_start_after_unix"; then
    return 1
  fi

  local count
  count="$(jq -r '.conversations | length // 0' "$output_json" 2>/dev/null || echo 0)"
  if [[ "$count" != "0" ]]; then
    return 0
  fi

  # Fallback: some successful webhook paths return an empty body and the
  # conversation appears slightly outside the narrow time window. Retry
  # once without the time cutoff and with a bigger page.
  local fallback_json="${output_json%.json}_fallback.json"
  local user_id branch_id
  user_id="$(jq -r '.conversation_initiation_client_data.user_id // ""' "$request_json")"
  branch_id="$(jq -r '.conversation_initiation_client_data.branch_id // ""' "$request_json")"
  [[ -n "$user_id" && -n "$branch_id" && -n "$remote_key" ]] || return 0

  local retry_index=0
  while true; do
    curl -sS -G \
      "https://api.elevenlabs.io/v1/convai/conversations" \
      -H "xi-api-key: ${remote_key}" \
      --data-urlencode "user_id=${user_id}" \
      --data-urlencode "branch_id=${branch_id}" \
      --data-urlencode "page_size=25" \
      --data-urlencode "summary_mode=exclude" \
      > "$fallback_json"

    count="$(jq -r '.conversations | length // 0' "$fallback_json" 2>/dev/null || echo 0)"
    if [[ "$count" != "0" || "$retry_index" -ge 3 ]]; then
      break
    fi

    retry_index=$((retry_index + 1))
    sleep 2
  done

  if [[ "$count" != "0" ]]; then
    cp "$fallback_json" "$output_json"
    return 0
  fi

  # Second fallback: some webhook-initiated calls are visible in branch history
  # before they become queryable by user_id. In that case, recover from the
  # recent branch call list instead of failing the selftest.
  local branch_only_json="${output_json%.json}_branch_only.json"
  local -a branch_only_cmd
  branch_only_cmd=(
    curl -sS -G
    "https://api.elevenlabs.io/v1/convai/conversations"
    -H "xi-api-key: ${remote_key}"
    --data-urlencode "branch_id=${branch_id}"
    --data-urlencode "page_size=25"
    --data-urlencode "summary_mode=exclude"
  )

  if [[ -n "$call_start_after_unix" ]]; then
    branch_only_cmd+=(--data-urlencode "call_start_after_unix=${call_start_after_unix}")
  fi

  retry_index=0
  while true; do
    "${branch_only_cmd[@]}" > "$branch_only_json"
    count="$(jq -r '.conversations | length // 0' "$branch_only_json" 2>/dev/null || echo 0)"
    if [[ "$count" != "0" || "$retry_index" -ge 3 ]]; then
      break
    fi

    retry_index=$((retry_index + 1))
    sleep 2
  done

  if [[ "$count" != "0" ]]; then
    cp "$branch_only_json" "$output_json"
  fi
}

enrich_final_conversation_with_list_data() {
  local final_json="$1"
  local request_json="$2"
  local remote_key="$3"
  local output_json="$4"
  local lookup_json="$5"

  cp "$final_json" "$output_json"

  local conv_id branch_id
  conv_id="$(jq -r '.conversation_id // ""' "$final_json" 2>/dev/null || true)"
  branch_id="$(jq -r '.conversation_initiation_client_data.branch_id // ""' "$request_json" 2>/dev/null || true)"

  [[ -n "$conv_id" && -n "$branch_id" && -n "$remote_key" ]] || return 0

  curl -sS -G \
    "https://api.elevenlabs.io/v1/convai/conversations" \
    -H "xi-api-key: ${remote_key}" \
    --data-urlencode "branch_id=${branch_id}" \
    --data-urlencode "page_size=50" \
    --data-urlencode "summary_mode=exclude" \
    > "$lookup_json"

  jq \
    --arg conv_id "$conv_id" \
    '
      . as $base
      | (input.conversations // [] | map(select(.conversation_id == $conv_id)) | .[0]) as $match
      | if $match == null then
          $base
        else
          $base
          + {
              branch_id: ($base.branch_id // $match.branch_id),
              version_id: ($base.version_id // $match.version_id),
              termination_reason: ($base.termination_reason // $match.termination_reason),
              call_successful: ($base.call_successful // $match.call_successful),
              summary_list_match: $match
            }
        end
    ' "$final_json" "$lookup_json" > "$output_json.tmp" && mv "$output_json.tmp" "$output_json"
}

record_attempt() {
  local attempts_json="$1"
  local transport="$2"
  local http_code="$3"
  local body_file="$4"
  local stderr_file="$5"

  jq \
    --arg transport "$transport" \
    --arg http_code "$http_code" \
    --arg body_file "$body_file" \
    --arg stderr_file "$stderr_file" \
    '. += [{
      transport: $transport,
      http_code: $http_code,
      body_file: $body_file,
      stderr_file: $stderr_file
    }]' \
    "$attempts_json" > "$attempts_json.tmp" && mv "$attempts_json.tmp" "$attempts_json"
}

post_via_server_relay() {
  local request_json="$1"
  local output_json="$2"
  local payload_b64
  payload_b64="$(base64 -w0 "$request_json")"

  ssh -o BatchMode=yes "$SERVER_ALIAS" python3 - "$payload_b64" > "$output_json" <<'PY'
import base64, json, os, sys
from pathlib import Path
from urllib import request, error

payload = base64.b64decode(sys.argv[1])
env_path = None
for raw in ('/home/aicore/n8n-server/.env.callcenter', '/home/aicore/n8n-ai-clean/.env.callcenter'):
    p = Path(raw)
    if p.exists():
        env_path = p
        break

if env_path is None:
    print(json.dumps({"ok": False, "error": "missing_env_callcenter"}))
    sys.exit(0)

token = ""
for line in env_path.read_text(encoding='utf-8', errors='ignore').splitlines():
    s = line.strip()
    if not s or s.startswith('#') or '=' not in s:
        continue
    k, v = s.split('=', 1)
    if k.strip() == 'ELEVEN_OUTBOUND_RELAY_TOKEN':
        token = v.strip().strip('"').strip("'")
        break

if not token:
    print(json.dumps({"ok": False, "error": "missing_relay_token"}))
    sys.exit(0)

req = request.Request(
    'http://151.241.228.232:8787/eleven/outbound-call',
    data=payload,
    method='POST',
    headers={
        'Content-Type': 'application/json',
        'X-Relay-Token': token,
    },
)
try:
    with request.urlopen(req, timeout=25) as resp:
        sys.stdout.write(resp.read().decode())
except error.HTTPError as exc:
    sys.stdout.write((exc.read() or b'').decode() or json.dumps({"ok": False, "error": f"http_{exc.code}"}))
except Exception as exc:
    sys.stdout.write(json.dumps({"ok": False, "error": "relay_request_failed", "message": str(exc)}))
PY
}

usage() {
  cat <<'EOF' >&2
Usage:
  run_eleven_branch_selftest.sh OUTPUT_DIR TO_NUMBER TEST_KEY [BRANCH_ID] [EXPECTED_VERSION_ID] [--dry-run]

Example:
  scripts/run_eleven_branch_selftest.sh \
    .runtime/eleven_lab_llm_compare_gemini_2026-06-16/call_01_selftest \
    +79251130826 \
    gemini_call_01 \
    agtbrch_3701kv7waz0teny9xvsgv7sjt0bp \
    agtvrsn_3901kv89xcg3fnntrp2zwbjt0xcb

What it does:
  1. Builds branch-targeted outbound request.json
  2. Tries outbound transports in configured order
     (default: local_relay -> relay_via_server -> relay -> webhook)
  3. Saves outbound_response.json
  4. Polls ElevenLabs conversation details until done/failed or timeout
EOF
  exit 1
}

if [[ $# -lt 3 ]]; then
  usage
fi

OUTPUT_DIR="$1"
TO_NUMBER="$2"
TEST_KEY="$3"
BRANCH_ID="${4:-$DEFAULT_BRANCH_ID}"
EXPECTED_VERSION_ID="${5:-}"
DRY_RUN="${6:-}"

if [[ "$BRANCH_ID" == "--dry-run" ]]; then
  BRANCH_ID="$DEFAULT_BRANCH_ID"
  EXPECTED_VERSION_ID=""
  DRY_RUN="--dry-run"
elif [[ "$EXPECTED_VERSION_ID" == "--dry-run" ]]; then
  EXPECTED_VERSION_ID=""
  DRY_RUN="--dry-run"
fi

if [[ ! "$TO_NUMBER" =~ ^\+[0-9]{8,15}$ ]]; then
  echo "TO_NUMBER must be E.164, e.g. +79251130826" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

REQUEST_JSON="$OUTPUT_DIR/request.json"
OUTBOUND_RESPONSE_JSON="$OUTPUT_DIR/outbound_response.json"
CONV_ID_TXT="$OUTPUT_DIR/conversation_id.txt"
TRANSPORT_TXT="$OUTPUT_DIR/transport.txt"
WEBHOOK_RESPONSE_JSON="$OUTPUT_DIR/webhook_response.json"
RELAY_RESPONSE_JSON="$OUTPUT_DIR/relay_response.json"
SERVER_RELAY_RESPONSE_JSON="$OUTPUT_DIR/server_relay_response.json"
WEBHOOK_STDERR="$OUTPUT_DIR/webhook_curl.stderr"
RELAY_STDERR="$OUTPUT_DIR/relay_curl.stderr"
SERVER_RELAY_STDERR="$OUTPUT_DIR/server_relay.stderr"
ATTEMPTS_JSON="$OUTPUT_DIR/transport_attempts.json"
RECENT_CONVERSATIONS_JSON="$OUTPUT_DIR/recent_conversations_lookup.json"
PREFLIGHT_DIR="$OUTPUT_DIR/preflight"

mkdir -p "$PREFLIGHT_DIR"

DATE_TAG="$(date +%F)"
TS_TAG="$(date +%s)"
USER_ID="lab_${TEST_KEY}_${TS_TAG}"
REQUEST_ID="manual.${DATE_TAG}.${TEST_KEY}"

jq -n \
  --arg agent_id "$DEFAULT_AGENT_ID" \
  --arg agent_phone_number_id "$DEFAULT_PHONE_NUMBER_ID" \
  --arg to_number "$TO_NUMBER" \
  --arg user_id "$USER_ID" \
  --arg branch_id "$BRANCH_ID" \
  --arg environment "$DEFAULT_ENVIRONMENT" \
  --arg lead_id "$USER_ID" \
  --arg caller "$TO_NUMBER" \
  --arg phone_primary "$TO_NUMBER" \
  --arg source_record_key "$USER_ID" \
  --arg company_name "manual_self_test" \
  --arg contact_name "Max manual test" \
  --arg request_id "$REQUEST_ID" \
  '{
    agent_id: $agent_id,
    agent_phone_number_id: $agent_phone_number_id,
    to_number: $to_number,
    conversation_initiation_client_data: {
      user_id: $user_id,
      branch_id: $branch_id,
      environment: $environment,
      dynamic_variables: {
        lead_id: $lead_id,
        caller: $caller,
        phone_primary: $phone_primary,
        source_record_key: $source_record_key,
        company_name: $company_name,
        contact_name: $contact_name,
        request_id: $request_id
      }
    }
  }' > "$REQUEST_JSON"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "Dry run only. Saved request: $REQUEST_JSON"
  jq \
    --arg expected_version_id "$EXPECTED_VERSION_ID" \
    '{
      request: .,
      expected_version_id: (if $expected_version_id == "" then null else $expected_version_id end)
    }' "$REQUEST_JSON"
  exit 0
fi

REMOTE_ENV_PATH="$(ssh -o BatchMode=yes "$SERVER_ALIAS" '
for p in /home/aicore/n8n-server/.env.callcenter /home/aicore/n8n-ai-clean/.env.callcenter; do
  if [ -f "$p" ]; then
    printf "%s\n" "$p"
    exit 0
  fi
done
exit 1
')"

REMOTE_EXPORTS="$(ssh -o BatchMode=yes "$SERVER_ALIAS" "python3 - <<'PY'
from pathlib import Path
path = Path('$REMOTE_ENV_PATH')
vals = {}
for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
    s = line.strip()
    if not s or s.startswith('#') or '=' not in s:
        continue
    k, v = s.split('=', 1)
    k = k.strip()
    if k in ('ELEVENLABS_API_KEY', 'ELEVEN_API_KEY', 'ELEVEN_OUTBOUND_RELAY_TOKEN'):
        vals[k] = v.strip().strip('\"').strip(\"'\")
for key in ('ELEVENLABS_API_KEY', 'ELEVEN_API_KEY', 'ELEVEN_OUTBOUND_RELAY_TOKEN'):
    if key in vals:
        print(f'{key}={vals[key]}')
PY
")"

REMOTE_KEY="$(printf '%s\n' "$REMOTE_EXPORTS" | awk -F= '/^(ELEVENLABS_API_KEY|ELEVEN_API_KEY)=/ {print substr($0, index($0,$2)); exit}')"
RELAY_TOKEN="$(printf '%s\n' "$REMOTE_EXPORTS" | awk -F= '/^ELEVEN_OUTBOUND_RELAY_TOKEN=/ {print substr($0, index($0,$2)); exit}')"

if [[ -z "$REMOTE_KEY" ]]; then
  echo "Could not extract ElevenLabs API key from remote env" >&2
  exit 1
fi

if [[ -x "${PWD}/scripts/report_eleven_quota_preflight.sh" ]]; then
  SERVER_ALIAS="$SERVER_ALIAS" "${PWD}/scripts/report_eleven_quota_preflight.sh" "$PREFLIGHT_DIR" "$BRANCH_ID" > "$PREFLIGHT_DIR/stdout.log" 2> "$PREFLIGHT_DIR/stderr.log" || true
fi

jq -n '[]' > "$ATTEMPTS_JSON"

TRANSPORT=""
IFS=',' read -r -a ORDERED_TRANSPORTS <<< "$TRANSPORT_ORDER"

for transport_name in "${ORDERED_TRANSPORTS[@]}"; do
  transport_name="$(printf '%s' "$transport_name" | xargs)"
  [[ -n "$transport_name" ]] || continue
  [[ -z "$TRANSPORT" ]] || break

  case "$transport_name" in
    relay_via_server)
      if post_via_server_relay "$REQUEST_JSON" "$SERVER_RELAY_RESPONSE_JSON" 2> "$SERVER_RELAY_STDERR"; then
        :
      fi
      if [[ -s "$SERVER_RELAY_RESPONSE_JSON" ]]; then
        cp "$SERVER_RELAY_RESPONSE_JSON" "$OUTBOUND_RESPONSE_JSON"
      fi
      record_attempt "$ATTEMPTS_JSON" "relay_via_server" "n/a" "$SERVER_RELAY_RESPONSE_JSON" "$SERVER_RELAY_STDERR"
      if response_has_success "$SERVER_RELAY_RESPONSE_JSON"; then
        TRANSPORT="relay_via_server"
      fi
      ;;

    relay)
      if [[ -n "$RELAY_TOKEN" ]]; then
        RELAY_HTTP="curl_failed"
        if RELAY_HTTP="$(post_json_with_curl "$DEFAULT_RELAY_URL" "$REQUEST_JSON" "$RELAY_RESPONSE_JSON" "$RELAY_STDERR" "X-Relay-Token" "$RELAY_TOKEN")"; then
          :
        else
          RELAY_HTTP="curl_failed"
        fi

        if [[ -s "$RELAY_RESPONSE_JSON" ]]; then
          cp "$RELAY_RESPONSE_JSON" "$OUTBOUND_RESPONSE_JSON"
        fi

        record_attempt "$ATTEMPTS_JSON" "relay" "$RELAY_HTTP" "$RELAY_RESPONSE_JSON" "$RELAY_STDERR"

        if response_has_success "$RELAY_RESPONSE_JSON"; then
          TRANSPORT="relay"
        fi
      fi
      ;;

    local_relay)
      if [[ -n "$RELAY_TOKEN" ]]; then
        RELAY_HTTP="curl_failed"
        if RELAY_HTTP="$(post_json_with_curl "$DEFAULT_LOCAL_RELAY_URL" "$REQUEST_JSON" "$RELAY_RESPONSE_JSON" "$RELAY_STDERR" "X-Relay-Token" "$RELAY_TOKEN")"; then
          :
        else
          RELAY_HTTP="curl_failed"
        fi

        if [[ -s "$RELAY_RESPONSE_JSON" ]]; then
          cp "$RELAY_RESPONSE_JSON" "$OUTBOUND_RESPONSE_JSON"
        fi

        record_attempt "$ATTEMPTS_JSON" "local_relay" "$RELAY_HTTP" "$RELAY_RESPONSE_JSON" "$RELAY_STDERR"

        if response_has_success "$RELAY_RESPONSE_JSON"; then
          TRANSPORT="local_relay"
        fi
      fi
      ;;

    webhook)
      if [[ -n "$BRANCH_ID" && "$BRANCH_ID" != "$DEFAULT_LIVE_MAIN_BRANCH_ID" && "${ELEVEN_SELFTEST_ALLOW_WEBHOOK_BRANCH_FALLBACK:-0}" != "1" ]]; then
        continue
      fi

      WEBHOOK_HTTP="curl_failed"
      if WEBHOOK_HTTP="$(post_json_with_curl "$DEFAULT_WEBHOOK_URL" "$REQUEST_JSON" "$WEBHOOK_RESPONSE_JSON" "$WEBHOOK_STDERR")"; then
        :
      else
        WEBHOOK_HTTP="curl_failed"
      fi

      if [[ -s "$WEBHOOK_RESPONSE_JSON" ]]; then
        cp "$WEBHOOK_RESPONSE_JSON" "$OUTBOUND_RESPONSE_JSON"
      fi

      record_attempt "$ATTEMPTS_JSON" "webhook" "$WEBHOOK_HTTP" "$WEBHOOK_RESPONSE_JSON" "$WEBHOOK_STDERR"

      if response_has_success "$WEBHOOK_RESPONSE_JSON"; then
        TRANSPORT="webhook"
      fi
      ;;

    *)
      echo "Unknown transport in ELEVEN_SELFTEST_TRANSPORT_ORDER: $transport_name" >&2
      exit 2
      ;;
  esac
done

printf '%s\n' "$TRANSPORT" > "$TRANSPORT_TXT"

if ! response_has_success "$OUTBOUND_RESPONSE_JSON"; then
  if recover_recent_conversation_with_fallback "$REQUEST_JSON" "$RECENT_CONVERSATIONS_JSON" "$REMOTE_KEY" "$TS_TAG"; then
    RECOVERED_CONV_ID="$(jq -r '
      .conversations // []
      | map(select((.conversation_id // "") != ""))
      | sort_by(.start_time_unix_secs // 0)
      | reverse
      | .[0].conversation_id // ""
    ' "$RECENT_CONVERSATIONS_JSON" 2>/dev/null || true)"
    RECOVERED_VERSION_ID="$(jq -r '
      .conversations // []
      | map(select((.conversation_id // "") != ""))
      | sort_by(.start_time_unix_secs // 0)
      | reverse
      | .[0].version_id // ""
    ' "$RECENT_CONVERSATIONS_JSON" 2>/dev/null || true)"
    RECOVERED_BRANCH_ID="$(jq -r '
      .conversations // []
      | map(select((.conversation_id // "") != ""))
      | sort_by(.start_time_unix_secs // 0)
      | reverse
      | .[0].branch_id // ""
    ' "$RECENT_CONVERSATIONS_JSON" 2>/dev/null || true)"

    if [[ -n "$RECOVERED_CONV_ID" && "$RECOVERED_BRANCH_ID" == "$BRANCH_ID" ]]; then
      jq -n \
        --arg conversation_id "$RECOVERED_CONV_ID" \
        --arg version_id "$RECOVERED_VERSION_ID" \
        --arg branch_id "$RECOVERED_BRANCH_ID" \
        '{
          success: true,
          recovered_via: "list_conversations",
          conversation_id: $conversation_id,
          version_id: $version_id,
          branch_id: $branch_id
        }' > "$OUTBOUND_RESPONSE_JSON"
    fi
  fi
fi

if [[ ! -s "$OUTBOUND_RESPONSE_JSON" ]]; then
  jq -n \
    --arg transport "${TRANSPORT:-}" \
    --slurpfile attempts "$ATTEMPTS_JSON" \
    '{
      ok: false,
      success: false,
      action: "selftest_failed",
      note: "No outbound response body was captured from any configured transport.",
      transport: $transport,
      attempts: ($attempts[0] // [])
    }' > "$OUTBOUND_RESPONSE_JSON"
fi

if [[ -s "$OUTBOUND_RESPONSE_JSON" ]] && ! response_has_success "$OUTBOUND_RESPONSE_JSON"; then
  if response_looks_like_cloudflare_block "$OUTBOUND_RESPONSE_JSON"; then
    build_blocked_outbound_json "$OUTBOUND_RESPONSE_JSON" "$ATTEMPTS_JSON" "$OUTBOUND_RESPONSE_JSON" "$TRANSPORT"
  fi
fi

if ! response_has_success "$OUTBOUND_RESPONSE_JSON"; then
  echo "Outbound webhook did not return success=true with conversation_id" >&2
  if jq -e . "$OUTBOUND_RESPONSE_JSON" >/dev/null 2>&1; then
    jq '.' "$OUTBOUND_RESPONSE_JSON" >&2
  else
    sed -n '1,80p' "$OUTBOUND_RESPONSE_JSON" >&2 || true
  fi
  exit 1
fi

CONVERSATION_ID="$(extract_conversation_id_from_response "$OUTBOUND_RESPONSE_JSON")"
printf '%s\n' "$CONVERSATION_ID" > "$CONV_ID_TXT"

DEADLINE=$(( $(date +%s) + DEFAULT_POLL_SECONDS ))
POLL_INDEX=1
FINAL_JSON="$OUTPUT_DIR/conversation_poll_final.json"
FINAL_ENRICHED_JSON="$OUTPUT_DIR/conversation_poll_final_enriched.json"
FINAL_LIST_LOOKUP_JSON="$OUTPUT_DIR/conversation_poll_final_list_lookup.json"
RUNTIME_DIAGNOSIS_JSON="$OUTPUT_DIR/runtime_diagnosis.json"

while true; do
  POLL_JSON="$OUTPUT_DIR/conversation_poll_${POLL_INDEX}.json"
  curl -sS \
    "https://api.elevenlabs.io/v1/convai/conversations/${CONVERSATION_ID}" \
    -H "xi-api-key: ${REMOTE_KEY}" \
    > "$POLL_JSON"

  STATUS="$(jq -r '.status // ""' "$POLL_JSON")"
  if [[ "$STATUS" == "done" || "$STATUS" == "failed" ]]; then
    cp "$POLL_JSON" "$FINAL_JSON"
    break
  fi

  if [[ $(date +%s) -ge $DEADLINE ]]; then
    cp "$POLL_JSON" "$FINAL_JSON"
    echo "Polling timeout reached after ${DEFAULT_POLL_SECONDS}s" >&2
    break
  fi

  sleep "$DEFAULT_POLL_INTERVAL"
  POLL_INDEX=$((POLL_INDEX + 1))
done

echo "Saved request: $REQUEST_JSON"
echo "Saved outbound response: $OUTBOUND_RESPONSE_JSON"
echo "Saved final conversation poll: $FINAL_JSON"

enrich_final_conversation_with_list_data "$FINAL_JSON" "$REQUEST_JSON" "$REMOTE_KEY" "$FINAL_ENRICHED_JSON" "$FINAL_LIST_LOOKUP_JSON"

jq \
  --arg transport "$TRANSPORT" \
  'if ((.termination_reason // "" | ascii_downcase) | test("quota limit"))
   then
     {
       ok: false,
       diagnosis: "provider_quota_limit",
       note: (.termination_reason // "This request exceeds your quota limit."),
       transport: (if $transport == "" then null else $transport end),
       conversation_id: .conversation_id,
       branch_id: .branch_id,
       version_id: .version_id,
       call_successful: .call_successful
     }
   elif (.status == "in-progress"
       and (.has_audio == false)
       and (.has_user_audio == false)
       and (.has_response_audio == false)
       and ((.transcript | length) == 0)
       and ((.metadata.call_duration_secs // 0) == 0))
   then
     {
       ok: false,
       diagnosis: "sip_pending_no_media",
       note: "Conversation was created, but after polling timeout there is still no audio, no transcript, and zero call duration.",
       transport: (if $transport == "" then null else $transport end),
       conversation_id: .conversation_id,
       branch_id: .branch_id,
       version_id: .version_id,
       phone_call: .metadata.phone_call
     }
   else
     {
       ok: true,
       diagnosis: "runtime_progressed_or_finished",
       transport: (if $transport == "" then null else $transport end),
       conversation_id: .conversation_id,
       status: .status,
       termination_reason: .termination_reason,
       call_successful: .call_successful
     }
   end' "$FINAL_ENRICHED_JSON" > "$RUNTIME_DIAGNOSIS_JSON"

echo "Saved runtime diagnosis: $RUNTIME_DIAGNOSIS_JSON"

jq \
  --arg expected_version_id "$EXPECTED_VERSION_ID" \
  --arg transport "$TRANSPORT" \
  '{
    transport: $transport,
    conversation_id,
    status,
    branch_id,
    version_id,
    termination_reason,
    call_successful,
    expected_version_id: (if $expected_version_id == "" then null else $expected_version_id end),
    version_matches_expected: (if $expected_version_id == "" then null else (.version_id == $expected_version_id) end)
  }' "$FINAL_ENRICHED_JSON"
