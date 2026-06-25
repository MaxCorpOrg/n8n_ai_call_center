#!/usr/bin/env bash
set -euo pipefail

SERVER_ALIAS="${SERVER_ALIAS:-ai-core-prod-147}"
STATE_PATH="${LOCALHOST_RUN_STATE_PATH:-/home/max/.config/lipolong-eleven-relay-state.json}"
DEFAULT_BRANCH_ID="agtbrch_3701kv7waz0teny9xvsgv7sjt0bp"

usage() {
  cat <<'EOF' >&2
Usage:
  report_eleven_live_readiness.sh OUTPUT_DIR [BRANCH_ID]

What it does:
  1. Runs quota preflight
  2. Reads the last known localhost.run state
  3. Checks health of the public relay URL from state
  4. Reads back the current live workflow URL from server Postgres
  5. Builds one readiness summary JSON
EOF
  exit 1
}

if [[ $# -lt 1 ]]; then
  usage
fi

OUTPUT_DIR="$1"
BRANCH_ID="${2:-$DEFAULT_BRANCH_ID}"

mkdir -p "$OUTPUT_DIR"

PREFLIGHT_DIR="$OUTPUT_DIR/preflight"
STATE_JSON="$OUTPUT_DIR/state_snapshot.json"
PUBLIC_HEALTH_JSON="$OUTPUT_DIR/public_relay_health.json"
PUBLIC_HEALTH_RAW="$OUTPUT_DIR/public_relay_health.raw"
WORKFLOW_URL_TXT="$OUTPUT_DIR/live_workflow_url.txt"
CONFIG_INVENTORY_JSON="$OUTPUT_DIR/eleven_config_inventory.json"
RUNTIME_STACK_JSON="$OUTPUT_DIR/runtime_stack_snapshot.json"
SUMMARY_JSON="$OUTPUT_DIR/live_readiness_summary.json"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$PREFLIGHT_DIR"

"$SCRIPT_DIR/report_eleven_quota_preflight.sh" "$PREFLIGHT_DIR" "$BRANCH_ID" > "$PREFLIGHT_DIR/stdout.log" 2> "$PREFLIGHT_DIR/stderr.log"

if [[ -f "$STATE_PATH" ]]; then
  cp "$STATE_PATH" "$STATE_JSON"
else
  jq -n --arg state_path "$STATE_PATH" '{missing: true, state_path: $state_path}' > "$STATE_JSON"
fi

STATE_RELAY_URL="$(jq -r '.relay_url // ""' "$STATE_JSON" 2>/dev/null || true)"

if [[ -n "$STATE_RELAY_URL" ]]; then
  HEALTH_URL="${STATE_RELAY_URL%/eleven/outbound-call}/health"
  HTTP_CODE="$(curl -sS --connect-timeout 5 --max-time 12 -o "$PUBLIC_HEALTH_RAW" -w "%{http_code}" "$HEALTH_URL" || true)"
  if jq -e . "$PUBLIC_HEALTH_RAW" >/dev/null 2>&1; then
    cp "$PUBLIC_HEALTH_RAW" "$PUBLIC_HEALTH_JSON"
  else
    jq -n \
      --arg raw "$(sed -n '1,20p' "$PUBLIC_HEALTH_RAW" | tr '\n' ' ')" \
      '{ok:false, non_json_body:true, raw_preview:$raw}' > "$PUBLIC_HEALTH_JSON"
  fi
else
  jq -n '{ok:false, reason:"missing_state_relay_url"}' > "$PUBLIC_HEALTH_JSON"
  HTTP_CODE=""
fi

ssh "$SERVER_ALIAS" "docker exec -e PGPASSWORD=5KIZBaFTYcJxLo12Plz0MzO72Q0w4rYP n8n-server-postgres-1 psql -U n8n -d n8n_prod -At -c \"select elem->'parameters'->>'url' from workflow_entity, json_array_elements(nodes::json) elem where id='sHTbALayEZdy8Mzs' and elem->>'name'='Eleven | Outbound HTTP';\"" > "$WORKFLOW_URL_TXT"

ssh "$SERVER_ALIAS" "python3 - <<'PY'
import json
import subprocess
from pathlib import Path

env_files = []
for raw in ('/home/aicore/n8n-server/.env.callcenter', '/home/aicore/n8n-ai-clean/.env.callcenter'):
    p = Path(raw)
    if not p.exists():
        continue
    has_eleven_key = False
    has_relay_token = False
    for line in p.read_text(encoding='utf-8', errors='ignore').splitlines():
        s = line.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        k = s.split('=', 1)[0].strip()
        if k in ('ELEVENLABS_API_KEY', 'ELEVEN_API_KEY'):
            has_eleven_key = True
        if k == 'ELEVEN_OUTBOUND_RELAY_TOKEN':
            has_relay_token = True
    env_files.append({
        'path': raw,
        'has_eleven_key': has_eleven_key,
        'has_relay_token': has_relay_token,
    })

creds_raw = subprocess.check_output([
    'docker', 'exec', 'n8n-server-postgres-1',
    'psql', '-U', 'n8n', '-d', 'n8n_prod', '-At',
    '-c', \"select id,name,type from credentials_entity where lower(name) like '%eleven%' order by name;\"
], text=True)

creds = []
for row in creds_raw.splitlines():
    parts = row.split('|')
    if len(parts) != 3:
        continue
    creds.append({'id': parts[0], 'name': parts[1], 'type': parts[2]})

print(json.dumps({
    'server_env_files': env_files,
    'server_env_files_with_eleven_key_count': sum(1 for x in env_files if x['has_eleven_key']),
    'server_env_files_with_relay_token_count': sum(1 for x in env_files if x['has_relay_token']),
    'n8n_named_eleven_credentials': creds,
    'n8n_named_eleven_credential_count': len(creds),
    'note': 'Server env mirrors may duplicate the same key material; this snapshot tracks named config slots, not distinct secret values.',
}, ensure_ascii=False))
PY" > "$CONFIG_INVENTORY_JSON"

python3 - <<'PY' > "$RUNTIME_STACK_JSON"
import json
import subprocess

def sh(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

relay = sh(['pgrep', '-af', 'eleven_outbound_relay_server.py'])
tunnel = sh(['pgrep', '-af', 'localhost_run_tunnel_sync.py|ssh -tt -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -R 80:localhost:18787'])
ss = sh(['ss', '-ltnp', '( sport = :18787 )'])

print(json.dumps({
    'relay_process_running': relay.returncode == 0,
    'relay_processes': [line for line in relay.stdout.splitlines() if line.strip()],
    'tunnel_process_running': tunnel.returncode == 0,
    'tunnel_processes': [line for line in tunnel.stdout.splitlines() if line.strip()],
    'listener_18787_present': '127.0.0.1:18787' in ss.stdout,
    'listener_snapshot': ss.stdout.strip(),
}, ensure_ascii=False))
PY

PREFLIGHT_SUMMARY="$PREFLIGHT_DIR/eleven_quota_preflight_summary.json"

jq -n \
  --arg checked_at_utc "$(date -u +%FT%TZ)" \
  --arg state_path "$STATE_PATH" \
  --arg state_relay_url "$STATE_RELAY_URL" \
  --arg public_health_http_code "$HTTP_CODE" \
  --arg workflow_url "$(tr -d '\n' < "$WORKFLOW_URL_TXT")" \
  --slurpfile preflight "$PREFLIGHT_SUMMARY" \
  --slurpfile state "$STATE_JSON" \
  --slurpfile public_health "$PUBLIC_HEALTH_JSON" \
  --slurpfile config_inventory "$CONFIG_INVENTORY_JSON" \
  --slurpfile runtime_stack "$RUNTIME_STACK_JSON" \
  '
    ($preflight[0] // {}) as $pf
    | ($state[0] // {}) as $stateJson
    | ($public_health[0] // {}) as $health
    | ($config_inventory[0] // {}) as $inventory
    | ($runtime_stack[0] // {}) as $stack
    | {
        checked_at_utc: $checked_at_utc,
        quota_preflight: {
          diagnosis: $pf.diagnosis,
          call_attempt_recommendation: ($pf.call_attempt_recommendation // null),
          warnings: ($pf.warnings // []),
          quota_fail_count: ($pf.recent_branch_activity.quota_fail_count // null),
          latest_quota_fail: ($pf.recent_branch_activity.latest_quota_fail // null),
          latest_conversation: ($pf.recent_branch_activity.latest_conversation // null)
        },
        tunnel_state: {
          state_path: $state_path,
          relay_url: $state_relay_url,
          state_snapshot: $stateJson
        },
        public_relay_health: {
          http_code: (if $public_health_http_code == "" then null else $public_health_http_code end),
          body: $health
        },
        live_workflow: {
          workflow_id: "sHTbALayEZdy8Mzs",
          target_node_name: "Eleven | Outbound HTTP",
          current_url: $workflow_url
        },
        config_inventory: $inventory,
        runtime_stack: $stack,
        checks: {
          workflow_matches_state: (
            ($state_relay_url != "")
            and ($workflow_url == $state_relay_url)
          ),
          public_health_ok: (
            ($public_health_http_code == "200")
            and (($health.ok // false) == true)
          ),
          local_stack_running: (
            (($stack.relay_process_running // false) == true)
            and (($stack.tunnel_process_running // false) == true)
            and (($stack.listener_18787_present // false) == true)
          ),
          quota_guard_recommended: (
            ($pf.diagnosis // "") == "provider_quota_limit_observed_recently"
          ),
          calls_should_be_blocked_now: (
            ($pf.call_attempt_recommendation // "") == "do_not_call_until_quota_is_restored"
          ),
          alternate_named_eleven_credential_detected: (
            (($inventory.n8n_named_eleven_credential_count // 0) > 1)
          )
        },
        overall_diagnosis: (
          if (($pf.call_attempt_recommendation // "") == "do_not_call_until_quota_is_restored") then
            "quota_blocker_active"
          elif (($pf.diagnosis // "") == "provider_quota_limit_observed_recently") then
            "quota_pressure_seen_history_only"
          elif ((($stack.relay_process_running // false) != true) or (($stack.tunnel_process_running // false) != true) or (($stack.listener_18787_present // false) != true)) then
            "local_stack_not_running"
          elif (($state_relay_url == "") or ($workflow_url == "") or ($workflow_url != $state_relay_url)) then
            "relay_state_mismatch"
          elif (($public_health_http_code != "200") or (($health.ok // false) != true)) then
            "public_relay_unhealthy"
          else
            "ready_for_controlled_call"
          end
        )
      }
  ' > "$SUMMARY_JSON"

echo "Saved readiness summary: $SUMMARY_JSON"
jq '.' "$SUMMARY_JSON"
