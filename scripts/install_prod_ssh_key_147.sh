#!/usr/bin/env bash
set -Eeuo pipefail

KEY_PATH="${KEY_PATH:-$HOME/.ssh/n8n_ai_call_center_prod_147_ed25519}"
PUBKEY_PATH="${KEY_PATH}.pub"
TARGET_HOST="${TARGET_HOST:-root@147.45.213.87}"

if [[ ! -f "${KEY_PATH}" || ! -f "${PUBKEY_PATH}" ]]; then
  echo "Missing key pair:"
  echo "  ${KEY_PATH}"
  echo "  ${PUBKEY_PATH}"
  exit 1
fi

echo "Installing public key ${PUBKEY_PATH} to ${TARGET_HOST}"
ssh-copy-id -i "${PUBKEY_PATH}" "${TARGET_HOST}"

echo "Done. Test with:"
echo "  ssh ai-core-prod-147"
