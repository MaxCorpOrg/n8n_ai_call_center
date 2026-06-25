#!/usr/bin/env bash
set -euo pipefail

STACK_DIR="${STACK_DIR:-/home/max/n8n_ai_call_center/.runtime/eleven_local_relay_stack}"

usage() {
  cat <<'EOF' >&2
Usage:
  stop_eleven_local_relay_stack.sh

Stops the background relay + localhost.run tunnel processes started by
start_eleven_local_relay_stack.sh.
EOF
  exit 1
}

if [[ "${1:-}" == "--help" ]]; then
  usage
fi

STOPPED=0

for pid_file in "$STACK_DIR/relay.pid" "$STACK_DIR/tunnel.pid"; do
  if [[ -f "$pid_file" ]]; then
    PID="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
      kill "$PID" 2>/dev/null || true
      STOPPED=1
    fi
    rm -f "$pid_file"
  fi
done

echo "{\"ok\":true,\"stopped_any\":$STOPPED,\"stack_dir\":\"$STACK_DIR\"}"
