#!/usr/bin/env bash
set -euo pipefail

SERVER_ALIAS="${SERVER_ALIAS:-ai-core-prod-147}"
STACK_DIR="${STACK_DIR:-/home/max/n8n_ai_call_center/.runtime/eleven_local_relay_stack}"
LOCAL_RELAY_PORT="${LOCAL_RELAY_PORT:-18787}"
LOCAL_RELAY_BIND="${LOCAL_RELAY_BIND:-127.0.0.1}"
RELAY_TIMEOUT="${RELAY_TIMEOUT:-35}"
RELAY_RETRY_COUNT="${RELAY_RETRY_COUNT:-1}"
RELAY_RETRY_DELAY_MS="${RELAY_RETRY_DELAY_MS:-500}"
STATE_PATH="${LOCALHOST_RUN_STATE_PATH:-/home/max/.config/lipolong-eleven-relay-state.json}"

usage() {
  cat <<'EOF' >&2
Usage:
  start_eleven_local_relay_stack.sh

What it does:
  1. Pulls ELEVEN API key + relay token from live server env
  2. Starts local relay server in background
  3. Starts localhost.run tunnel sync in background
  4. Waits for relay state file and prints a short stack summary
EOF
  exit 1
}

if [[ "${1:-}" == "--help" ]]; then
  usage
fi

mkdir -p "$STACK_DIR"

ENV_FILE="$STACK_DIR/relay.env"
RELAY_LOG="$STACK_DIR/relay.log"
TUNNEL_LOG="$STACK_DIR/tunnel.log"
RELAY_PID_FILE="$STACK_DIR/relay.pid"
TUNNEL_PID_FILE="$STACK_DIR/tunnel.pid"
SUMMARY_JSON="$STACK_DIR/stack_summary.json"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

ELEVEN_API_KEY="$(printf '%s\n' "$REMOTE_EXPORTS" | awk -F= '/^(ELEVENLABS_API_KEY|ELEVEN_API_KEY)=/ {print substr($0, index($0,$2)); exit}')"
RELAY_SHARED_TOKEN="$(printf '%s\n' "$REMOTE_EXPORTS" | awk -F= '/^ELEVEN_OUTBOUND_RELAY_TOKEN=/ {print substr($0, index($0,$2)); exit}')"

if [[ -z "$ELEVEN_API_KEY" || -z "$RELAY_SHARED_TOKEN" ]]; then
  echo "Could not extract ELEVEN_API_KEY or ELEVEN_OUTBOUND_RELAY_TOKEN from remote env" >&2
  exit 1
fi

cat > "$ENV_FILE" <<EOF
RELAY_BIND=$LOCAL_RELAY_BIND
RELAY_PORT=$LOCAL_RELAY_PORT
RELAY_SHARED_TOKEN=$RELAY_SHARED_TOKEN
RELAY_TIMEOUT=$RELAY_TIMEOUT
RELAY_RETRY_COUNT=$RELAY_RETRY_COUNT
RELAY_RETRY_DELAY_MS=$RELAY_RETRY_DELAY_MS
ELEVEN_API_KEY=$ELEVEN_API_KEY
LOCALHOST_RUN_STATE_PATH=$STATE_PATH
EOF

rm -f "$STATE_PATH"
: > "$RELAY_LOG"
: > "$TUNNEL_LOG"

if [[ -f "$RELAY_PID_FILE" ]]; then
  OLD_PID="$(cat "$RELAY_PID_FILE" 2>/dev/null || true)"
  if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    kill "$OLD_PID" 2>/dev/null || true
    sleep 1
  fi
fi

if [[ -f "$TUNNEL_PID_FILE" ]]; then
  OLD_PID="$(cat "$TUNNEL_PID_FILE" 2>/dev/null || true)"
  if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    kill "$OLD_PID" 2>/dev/null || true
    sleep 1
  fi
fi

fuser -k "${LOCAL_RELAY_PORT}/tcp" 2>/dev/null || true

env \
  RELAY_BIND="$LOCAL_RELAY_BIND" \
  RELAY_PORT="$LOCAL_RELAY_PORT" \
  RELAY_SHARED_TOKEN="$RELAY_SHARED_TOKEN" \
  RELAY_TIMEOUT="$RELAY_TIMEOUT" \
  RELAY_RETRY_COUNT="$RELAY_RETRY_COUNT" \
  RELAY_RETRY_DELAY_MS="$RELAY_RETRY_DELAY_MS" \
  ELEVEN_API_KEY="$ELEVEN_API_KEY" \
  LOCALHOST_RUN_STATE_PATH="$STATE_PATH" \
  setsid python3 "$SCRIPT_DIR/eleven_outbound_relay_server.py" </dev/null >> "$RELAY_LOG" 2>&1 &
RELAY_PID=$!
echo "$RELAY_PID" > "$RELAY_PID_FILE"

sleep 2
if ! kill -0 "$RELAY_PID" 2>/dev/null; then
  echo "Relay process failed to start. See $RELAY_LOG" >&2
  exit 1
fi

env \
  SERVER_ALIAS="$SERVER_ALIAS" \
  LOCAL_RELAY_PORT="$LOCAL_RELAY_PORT" \
  LOCALHOST_RUN_STATE_PATH="$STATE_PATH" \
  setsid script -qefc "python3 '$SCRIPT_DIR/localhost_run_tunnel_sync.py'" /dev/null </dev/null >> "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!
echo "$TUNNEL_PID" > "$TUNNEL_PID_FILE"

for _ in $(seq 1 20); do
  if ! kill -0 "$TUNNEL_PID" 2>/dev/null; then
    echo "Tunnel sync process exited early. See $TUNNEL_LOG" >&2
    exit 1
  fi
  if [[ -f "$STATE_PATH" ]] && jq -e '.relay_url // empty' "$STATE_PATH" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if [[ ! -f "$STATE_PATH" ]] || ! jq -e '.relay_url // empty' "$STATE_PATH" >/dev/null 2>&1; then
  echo "Tunnel sync did not produce a fresh relay state. See $TUNNEL_LOG" >&2
  exit 1
fi

RELAY_HEALTH_HTTP="$(curl -sS --connect-timeout 3 --max-time 8 -o "$STACK_DIR/relay_health.json" -w "%{http_code}" "http://$LOCAL_RELAY_BIND:$LOCAL_RELAY_PORT/health" || true)"

jq -n \
  --arg started_at_utc "$(date -u +%FT%TZ)" \
  --arg env_file "$ENV_FILE" \
  --arg relay_log "$RELAY_LOG" \
  --arg tunnel_log "$TUNNEL_LOG" \
  --arg state_path "$STATE_PATH" \
  --arg relay_pid "$RELAY_PID" \
  --arg tunnel_pid "$TUNNEL_PID" \
  --arg relay_health_http "$RELAY_HEALTH_HTTP" \
  --argjson state "$(if [[ -f "$STATE_PATH" ]]; then cat "$STATE_PATH"; else echo '{}'; fi)" \
  '{
    ok: true,
    started_at_utc: $started_at_utc,
    env_file: $env_file,
    relay_log: $relay_log,
    tunnel_log: $tunnel_log,
    state_path: $state_path,
    relay_pid: ($relay_pid | tonumber),
    tunnel_pid: ($tunnel_pid | tonumber),
    relay_health_http: $relay_health_http,
    relay_state: $state
  }' > "$SUMMARY_JSON"

cat "$SUMMARY_JSON"
