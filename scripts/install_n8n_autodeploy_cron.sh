#!/usr/bin/env bash
set -Eeuo pipefail

CRON_FILE="${CRON_FILE:-/etc/cron.d/n8n-autodeploy-clean}"
CRON_SCHEDULE="${CRON_SCHEDULE:-*/5 * * * *}"
AUTODEPLOY_CMD="${AUTODEPLOY_CMD:-/usr/local/bin/n8n-autodeploy-clean}"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo $0"
  exit 1
fi

cat > "${CRON_FILE}" <<EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
${CRON_SCHEDULE} root ${AUTODEPLOY_CMD}
EOF

chmod 644 "${CRON_FILE}"
systemctl restart cron

echo "Installed ${CRON_FILE}:"
cat "${CRON_FILE}"
