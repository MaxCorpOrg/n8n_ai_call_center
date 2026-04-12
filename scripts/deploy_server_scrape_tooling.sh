#!/usr/bin/env bash
set -euo pipefail

TARGET_HOST="${1:-root@147.45.213.87}"
LOCAL_SITE_CONTROL_ROOT="${LOCAL_SITE_CONTROL_ROOT:-/home/max/site-control-kit}"
REMOTE_TOOLS_ROOT="${REMOTE_TOOLS_ROOT:-/home/aicore/agent-tools}"
REMOTE_SITE_CONTROL_ROOT="${REMOTE_SITE_CONTROL_ROOT:-${REMOTE_TOOLS_ROOT}/site-control-kit}"
REMOTE_FIRECRAWL_ROOT="${REMOTE_FIRECRAWL_ROOT:-${REMOTE_TOOLS_ROOT}/firecrawl}"
REMOTE_PROJECT_ROOT="${REMOTE_PROJECT_ROOT:-/home/aicore/n8n-server}"
SITECTL_TOKEN="${SITECTL_TOKEN:-$(openssl rand -hex 24)}"
FIRECRAWL_BULL_AUTH_KEY="${FIRECRAWL_BULL_AUTH_KEY:-$(openssl rand -hex 16)}"

echo "==> Copy site-control-kit snapshot to ${TARGET_HOST}:${REMOTE_SITE_CONTROL_ROOT}"
ssh "${TARGET_HOST}" "mkdir -p '${REMOTE_TOOLS_ROOT}'"
rsync -az --delete \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.venv' \
  "${LOCAL_SITE_CONTROL_ROOT}/" "${TARGET_HOST}:${REMOTE_SITE_CONTROL_ROOT}/"

echo "==> Install site-control-kit venv and hub service"
ssh "${TARGET_HOST}" \
  "REMOTE_TOOLS_ROOT='${REMOTE_TOOLS_ROOT}' REMOTE_SITE_CONTROL_ROOT='${REMOTE_SITE_CONTROL_ROOT}' SITECTL_TOKEN='${SITECTL_TOKEN}' bash -s" \
  <<'EOF'
set -euo pipefail
mkdir -p /etc/site-control-kit
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3-venv python3.12-venv
cat >/etc/site-control-kit/hub.env <<ENV
SITECTL_HOST=127.0.0.1
SITECTL_PORT=8765
SITECTL_TOKEN=${SITECTL_TOKEN}
SITECTL_STATE_FILE=/home/aicore/.site-control-kit/state.json
ENV
chown -R aicore:aicore "${REMOTE_TOOLS_ROOT}"
su - aicore -c "python3 -m venv '${REMOTE_SITE_CONTROL_ROOT}/.venv'"
su - aicore -c "'${REMOTE_SITE_CONTROL_ROOT}/.venv/bin/pip' install --upgrade pip"
su - aicore -c "cd '${REMOTE_SITE_CONTROL_ROOT}' && '${REMOTE_SITE_CONTROL_ROOT}/.venv/bin/pip' install -e ."
cat >/etc/systemd/system/site-control-kit-hub.service <<'UNIT'
[Unit]
Description=Site Control Kit Hub
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=aicore
WorkingDirectory=__SITECTL_ROOT__
EnvironmentFile=-/etc/site-control-kit/hub.env
ExecStart=__SITECTL_ROOT__/.venv/bin/python -m webcontrol serve --host ${SITECTL_HOST} --port ${SITECTL_PORT} --token ${SITECTL_TOKEN} --state-file ${SITECTL_STATE_FILE}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
sed -i "s|__SITECTL_ROOT__|${REMOTE_SITE_CONTROL_ROOT}|g" /etc/systemd/system/site-control-kit-hub.service
systemctl daemon-reload
systemctl enable --now site-control-kit-hub.service
EOF

echo "==> Clone or refresh Firecrawl source tree"
ssh "${TARGET_HOST}" "bash -s" <<EOF
set -euo pipefail
mkdir -p '${REMOTE_TOOLS_ROOT}'
if [ ! -d '${REMOTE_FIRECRAWL_ROOT}/.git' ]; then
  git clone --depth 1 https://github.com/firecrawl/firecrawl.git '${REMOTE_FIRECRAWL_ROOT}'
fi
cat >'${REMOTE_FIRECRAWL_ROOT}/.env' <<ENV
PORT=3002
HOST=0.0.0.0
USE_DB_AUTHENTICATION=false
BULL_AUTH_KEY=${FIRECRAWL_BULL_AUTH_KEY}
ENV
chown -R aicore:aicore '${REMOTE_FIRECRAWL_ROOT}'
cd '${REMOTE_FIRECRAWL_ROOT}'
docker compose up -d --build
EOF

echo "==> Wire tooling env into cosmetologist hunter"
ssh "${TARGET_HOST}" "bash -s" <<EOF
set -euo pipefail
python3 - <<'PY'
from pathlib import Path

env_path = Path("${REMOTE_PROJECT_ROOT}") / ".env.cosmetologist_hunter"
existing = {}
lines = []
if env_path.exists():
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\n")
        lines.append(line)
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            existing[key.strip()] = value.strip()

updates = {
    "COSMETOLOGIST_HUNTER_SERVER_TOOL_ROOT": "${REMOTE_TOOLS_ROOT}",
    "COSMETOLOGIST_HUNTER_FIRECRAWL_ROOT": "${REMOTE_FIRECRAWL_ROOT}",
    "COSMETOLOGIST_HUNTER_FIRECRAWL_BASE_URL": "http://127.0.0.1:3002",
    "COSMETOLOGIST_HUNTER_SITE_CONTROL_ROOT": "${REMOTE_SITE_CONTROL_ROOT}",
    "COSMETOLOGIST_HUNTER_SITE_CONTROL_SERVER_URL": "http://127.0.0.1:8765",
    "COSMETOLOGIST_HUNTER_SITE_CONTROL_TOKEN": "${SITECTL_TOKEN}",
}

out = []
seen = set()
for line in lines:
    if "=" in line and not line.lstrip().startswith("#"):
        key, _ = line.split("=", 1)
        key = key.strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
            continue
    out.append(line)

if out and out[-1] != "":
    out.append("")
for key, value in updates.items():
    if key not in seen and key not in existing:
        out.append(f"{key}={value}")

env_path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
PY
EOF

echo "==> Restart cosmetologist hunter service"
ssh "${TARGET_HOST}" "systemctl restart cosmetologist_hunter.service && sleep 2 && systemctl is-active site-control-kit-hub.service && systemctl is-active cosmetologist_hunter.service"

echo
echo "Done."
echo "site-control-kit root: ${REMOTE_SITE_CONTROL_ROOT}"
echo "firecrawl root: ${REMOTE_FIRECRAWL_ROOT}"
echo "site-control token: ${SITECTL_TOKEN}"
echo "firecrawl base url: http://127.0.0.1:3002"
