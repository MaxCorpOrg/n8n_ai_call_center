#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash bootstrap_ubuntu.sh"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${1:-${SCRIPT_DIR}/.env}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Env file not found: ${ENV_FILE}"
  echo "Copy .env.example to .env and fill values."
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

required_vars=(
  PUBLIC_IP
  MANGO_IP
  ELEVEN_SIP_HOST
  ELEVEN_SIP_PORT
  TARGET_NUMBER_E164
  BRIDGE_EXT
  BIND_IP
  BIND_PORT
  RTP_START
  RTP_END
)

for v in "${required_vars[@]}"; do
  if [[ -z "${!v:-}" ]]; then
    echo "Missing required variable: ${v}"
    exit 1
  fi
done

export PUBLIC_IP MANGO_IP ELEVEN_SIP_HOST ELEVEN_SIP_PORT TARGET_NUMBER_E164 BRIDGE_EXT BIND_IP BIND_PORT RTP_START RTP_END

echo "[1/6] Installing packages..."
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y asterisk gettext-base ufw

echo "[2/6] Backing up existing configs..."
mkdir -p /etc/asterisk/backup
for f in pjsip.conf extensions.conf rtp.conf; do
  if [[ -f "/etc/asterisk/${f}" ]]; then
    cp -f "/etc/asterisk/${f}" "/etc/asterisk/backup/${f}.$(date +%Y%m%d%H%M%S).bak"
  fi
done

echo "[3/6] Rendering Asterisk templates..."
envsubst < "${SCRIPT_DIR}/templates/pjsip.conf.template" > /etc/asterisk/pjsip.conf
envsubst < "${SCRIPT_DIR}/templates/extensions.conf.template" > /etc/asterisk/extensions.conf

cat > /etc/asterisk/rtp.conf <<EOF
[general]
rtpstart=${RTP_START}
rtpend=${RTP_END}
icesupport=no
stunaddr=
EOF

echo "[4/6] Opening firewall (if ufw enabled)..."
if ufw status | grep -q "Status: active"; then
  ufw allow "${BIND_PORT}/udp" || true
  ufw allow "${BIND_PORT}/tcp" || true
  ufw allow "${RTP_START}:${RTP_END}/udp" || true
fi

echo "[5/6] Restarting Asterisk..."
systemctl enable asterisk
systemctl restart asterisk

echo "[6/6] Basic checks..."
asterisk -rx "core show version" || true
asterisk -rx "pjsip show endpoints" || true
asterisk -rx "dialplan show from-mango" || true

cat <<EOF

Done.
Next:
1) Mango SIP trunk -> IP: ${PUBLIC_IP}, port: ${BIND_PORT}, codec: G.711A, DTMF RFC2833, mode UDP.
2) Mango routing rule: route to extension ${BRIDGE_EXT} (quick mode) or pass full number (dynamic mode).
3) Test call and watch logs:
   journalctl -u asterisk -f
   asterisk -rvvv

EOF
