#!/usr/bin/env bash
set -euo pipefail

DEFAULT_BRANCH_ID="agtbrch_3701kv7waz0teny9xvsgv7sjt0bp"
SERVER_ALIAS="${SERVER_ALIAS:-ai-core-prod-147}"

usage() {
  cat <<'EOF' >&2
Usage:
  report_eleven_quota_preflight.sh OUTPUT_DIR [BRANCH_ID]

What it does:
  1. Reads the ElevenLabs API key from the live server env
  2. Saves raw subscription snapshot
  3. Saves recent conversations for the target branch
  4. Builds a short quota/preflight summary JSON
EOF
  exit 1
}

if [[ $# -lt 1 ]]; then
  usage
fi

OUTPUT_DIR="$1"
BRANCH_ID="${2:-$DEFAULT_BRANCH_ID}"

mkdir -p "$OUTPUT_DIR"

SUBSCRIPTION_JSON="$OUTPUT_DIR/eleven_subscription_snapshot.json"
RECENT_JSON="$OUTPUT_DIR/eleven_recent_branch_conversations.json"
SUMMARY_JSON="$OUTPUT_DIR/eleven_quota_preflight_summary.json"

REMOTE_ENV_PATH="$(ssh -o BatchMode=yes "$SERVER_ALIAS" '
for p in /home/aicore/n8n-server/.env.callcenter /home/aicore/n8n-ai-clean/.env.callcenter; do
  if [ -f "$p" ]; then
    printf "%s\n" "$p"
    exit 0
  fi
done
exit 1
')"

REMOTE_KEY="$(
  ssh -o BatchMode=yes "$SERVER_ALIAS" "python3 - <<'PY'
from pathlib import Path
path = Path('$REMOTE_ENV_PATH')
for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
    s = line.strip()
    if not s or s.startswith('#') or '=' not in s:
        continue
    k, v = s.split('=', 1)
    if k.strip() in ('ELEVENLABS_API_KEY', 'ELEVEN_API_KEY'):
        print(v.strip().strip('\"').strip(\"'\"))
        break
PY
"
)"

if [[ -z "$REMOTE_KEY" ]]; then
  echo "Could not extract ElevenLabs API key from remote env" >&2
  exit 1
fi

curl -sS \
  "https://api.elevenlabs.io/v1/user/subscription" \
  -H "xi-api-key: ${REMOTE_KEY}" \
  > "$SUBSCRIPTION_JSON"

curl -sS -G \
  "https://api.elevenlabs.io/v1/convai/conversations" \
  -H "xi-api-key: ${REMOTE_KEY}" \
  --data-urlencode "branch_id=${BRANCH_ID}" \
  --data-urlencode "page_size=50" \
  --data-urlencode "summary_mode=exclude" \
  > "$RECENT_JSON"

jq -n \
  --arg branch_id "$BRANCH_ID" \
  --slurpfile subscription "$SUBSCRIPTION_JSON" \
  --slurpfile recent "$RECENT_JSON" \
  '
    def ts_utc($v):
      if $v == null then null else ($v | strftime("%Y-%m-%dT%H:%M:%SZ")) end;
    def age_minutes($v):
      if $v == null then null else (((now - ($v | tonumber)) / 60) | floor) end;
    ($subscription[0] // {}) as $sub
    | ($recent[0].conversations // []) as $convs
    | ($convs
        | map(select(((.termination_reason // "") | ascii_downcase) | test("quota limit")))
      ) as $quotaFails
    | ($quotaFails
        | sort_by(.start_time_unix_secs // 0)
        | reverse
        | .[0]
      ) as $latestQuotaFail
    | ($convs
        | sort_by(.start_time_unix_secs // 0)
        | reverse
        | .[0]
      ) as $latestAny
    | {
        checked_at_utc: (now | todateiso8601),
        branch_id: $branch_id,
        subscription: {
          access_error: ($sub.detail // null),
          tier: $sub.tier,
          status: $sub.status,
          character_count: $sub.character_count,
          character_limit: $sub.character_limit,
          percent_used: (
            if (($sub.character_limit // 0) | tonumber) > 0
            then (((($sub.character_count // 0) | tonumber) / (($sub.character_limit // 1) | tonumber)) * 100)
            else null
            end
          ),
          can_extend_character_limit: $sub.can_extend_character_limit,
          allowed_to_extend_character_limit: $sub.allowed_to_extend_character_limit,
          max_character_limit_extension: $sub.max_character_limit_extension,
          max_credit_limit_extension: $sub.max_credit_limit_extension,
          has_open_invoices: $sub.has_open_invoices,
          current_overage: $sub.current_overage
        },
        recent_branch_activity: {
          sample_size: ($convs | length),
          latest_conversation: (
            if $latestAny == null then null else {
              conversation_id: $latestAny.conversation_id,
              status: $latestAny.status,
              termination_reason: $latestAny.termination_reason,
              call_successful: $latestAny.call_successful,
              start_time_unix_secs: $latestAny.start_time_unix_secs,
              start_time_utc: ts_utc($latestAny.start_time_unix_secs),
              age_minutes: age_minutes($latestAny.start_time_unix_secs),
              version_id: $latestAny.version_id
            } end
          ),
          quota_fail_count: ($quotaFails | length),
          latest_quota_fail: (
            if $latestQuotaFail == null then null else {
              conversation_id: $latestQuotaFail.conversation_id,
              status: $latestQuotaFail.status,
              termination_reason: $latestQuotaFail.termination_reason,
              call_successful: $latestQuotaFail.call_successful,
              start_time_unix_secs: $latestQuotaFail.start_time_unix_secs,
              start_time_utc: ts_utc($latestQuotaFail.start_time_unix_secs),
              age_minutes: age_minutes($latestQuotaFail.start_time_unix_secs),
              version_id: $latestQuotaFail.version_id
            } end
          ),
          latest_conversation_is_quota_fail: (
            ($latestAny != null)
            and (((($latestAny.termination_reason // "") | ascii_downcase) | test("quota limit")))
          )
        },
        call_attempt_recommendation: (
          if (($quotaFails | length) > 0)
             and ($latestAny != null)
             and (((($latestAny.termination_reason // "") | ascii_downcase) | test("quota limit")))
          then "do_not_call_until_quota_is_restored"
          elif (($quotaFails | length) > 0) then
            "quota_pressure_seen_verify_before_call"
          else
            "no_quota_stop_seen_in_recent_sample"
          end
        ),
        warnings: [
          (if (($sub.detail.status // "") == "missing_permissions")
           then "subscription endpoint is unavailable for the current API key because user_read permission is missing"
           else empty end),
          (if (($quotaFails | length) > 0)
           then "recent branch history already shows quota-limit failures"
           else empty end)
        ],
        diagnosis: (
          if (($quotaFails | length) > 0) then
            "provider_quota_limit_observed_recently"
          elif (($sub.detail.status // "") == "missing_permissions") then
            "subscription_endpoint_forbidden_for_current_api_key"
          elif (($sub.status // "") != "active") then
            "subscription_not_active"
          elif (($sub.character_limit // 0) > 0 and ($sub.character_count // 0) >= ($sub.character_limit // 0)) then
            "character_limit_reached"
          else
            "no_recent_quota_signal"
          end
        )
      }
  ' > "$SUMMARY_JSON"

echo "Saved subscription snapshot: $SUBSCRIPTION_JSON"
echo "Saved recent branch conversations: $RECENT_JSON"
echo "Saved quota preflight summary: $SUMMARY_JSON"

jq '.' "$SUMMARY_JSON"
