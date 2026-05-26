#!/usr/bin/env bash
set -euo pipefail

SITECTL_ROOT="${SITECTL_ROOT:-/home/aicore/agent-tools/site-control-kit}"
SITECTL_HUB_ENV="${SITECTL_HUB_ENV:-/etc/site-control-kit/hub.env}"
SITECTL_HUB_URL="${SITECTL_HUB_URL:-http://127.0.0.1:8765}"
SITECTL_BROWSER_RUNTIME_ROOT="${SITECTL_BROWSER_RUNTIME_ROOT:-/home/aicore/.local/share/site-control-kit-browser}"
SITECTL_BROWSER_CLIENT_ID="${SITECTL_BROWSER_CLIENT_ID:-client-cosmetologist-browser}"
SITECTL_BROWSER_DISPLAY="${SITECTL_BROWSER_DISPLAY:-:99}"
SITECTL_BROWSER_WINDOW_SIZE="${SITECTL_BROWSER_WINDOW_SIZE:-1440,1600}"
SITECTL_BROWSER_START_URL="${SITECTL_BROWSER_START_URL:-about:blank}"

if [[ ! -f "${SITECTL_HUB_ENV}" ]]; then
  echo "Missing hub env file: ${SITECTL_HUB_ENV}" >&2
  exit 1
fi

SITECTL_TOKEN="$(awk -F= '/^SITECTL_TOKEN=/{print $2}' "${SITECTL_HUB_ENV}")"
if [[ -z "${SITECTL_TOKEN}" ]]; then
  echo "SITECTL_TOKEN is empty in ${SITECTL_HUB_ENV}" >&2
  exit 1
fi

if [[ ! -d "${SITECTL_ROOT}/extension" ]]; then
  echo "Missing site-control extension directory: ${SITECTL_ROOT}/extension" >&2
  exit 1
fi

BROWSER_BIN="${SITECTL_BROWSER_BIN:-}"
if [[ -z "${BROWSER_BIN}" ]]; then
  BROWSER_BIN="$(find /home/aicore/.cache/ms-playwright -type f -name chrome 2>/dev/null | sort | tail -n 1 || true)"
fi
if [[ -z "${BROWSER_BIN}" || ! -x "${BROWSER_BIN}" ]]; then
  echo "Could not find a Chromium executable. Set SITECTL_BROWSER_BIN." >&2
  exit 1
fi

RUNTIME_ROOT="${SITECTL_BROWSER_RUNTIME_ROOT}"
EXT_RUNTIME="${RUNTIME_ROOT}/extension"
PROFILE_DIR="${RUNTIME_ROOT}/chrome-profile"
XVFB_PID_FILE="${RUNTIME_ROOT}/xvfb.pid"
mkdir -p "${RUNTIME_ROOT}" "${PROFILE_DIR}"
rm -rf "${EXT_RUNTIME}"
mkdir -p "${EXT_RUNTIME}"
cp -R "${SITECTL_ROOT}/extension/." "${EXT_RUNTIME}/"

python3 - "${EXT_RUNTIME}/background.js" "${SITECTL_HUB_URL}" "${SITECTL_TOKEN}" "${SITECTL_BROWSER_CLIENT_ID}" <<'PY'
import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
server_url = sys.argv[2]
token = sys.argv[3]
client_id = sys.argv[4]
text = path.read_text()
match = re.search(r"const DEFAULT_CONFIG = \{.*?\n\};", text, re.S)
if not match:
    raise SystemExit("DEFAULT_CONFIG block not found in background.js")
replacement = (
    "const DEFAULT_CONFIG = {\n"
    f"  serverUrl: {json.dumps(server_url)},\n"
    f"  token: {json.dumps(token)},\n"
    f"  clientId: {json.dumps(client_id)},\n"
    "  pollIntervalMs: 2000,\n"
    "  heartbeatIntervalMs: 8000\n"
    "};"
)
path.write_text(text[:match.start()] + replacement + text[match.end():])
PY

if [[ -f "${XVFB_PID_FILE}" ]]; then
  if kill -0 "$(cat "${XVFB_PID_FILE}")" >/dev/null 2>&1; then
    :
  else
    rm -f "${XVFB_PID_FILE}"
  fi
fi

if ! pgrep -af "Xvfb ${SITECTL_BROWSER_DISPLAY}" >/dev/null 2>&1; then
  Xvfb "${SITECTL_BROWSER_DISPLAY}" -screen 0 1440x1600x24 -nolisten tcp >/tmp/site-control-xvfb.log 2>&1 &
  echo $! > "${XVFB_PID_FILE}"
  sleep 2
fi

export DISPLAY="${SITECTL_BROWSER_DISPLAY}"

exec "${BROWSER_BIN}" \
  --user-data-dir="${PROFILE_DIR}" \
  --no-first-run \
  --no-default-browser-check \
  --no-sandbox \
  --disable-setuid-sandbox \
  --disable-dev-shm-usage \
  --disable-features=DialMediaRouteProvider \
  --disable-extensions-except="${EXT_RUNTIME}" \
  --load-extension="${EXT_RUNTIME}" \
  --window-size="${SITECTL_BROWSER_WINDOW_SIZE}" \
  "${SITECTL_BROWSER_START_URL}"
