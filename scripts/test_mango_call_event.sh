#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <webhook_url> <vpbx_api_key> <vpbx_api_salt> <to_number_hint>"
  echo "Example:"
  echo "  $0 'https://n8n.example.com/webhook/mango/events/call' 'KEY' 'SALT' 'sip:ai@domain'"
  exit 1
fi

WEBHOOK_URL="$1"
VPBX_API_KEY="$2"
VPBX_API_SALT="$3"
TO_NUMBER_HINT="$4"

CALL_ID="test-call-$(date +%s)"
JSON_PAYLOAD=$(cat <<JSON
{"entry_id":"test-entry","call_id":"${CALL_ID}","timestamp":$(date +%s),"seq":1,"call_state":"Appeared","location":"ivr","from":{"number":"79000000000"},"to":{"number":"${TO_NUMBER_HINT}"}}
JSON
)

SIGN_INPUT="${VPBX_API_KEY}${JSON_PAYLOAD}${VPBX_API_SALT}"
SIGN=$(printf '%s' "$SIGN_INPUT" | sha256sum | awk '{print $1}')

echo "Webhook URL: $WEBHOOK_URL"
echo "Call ID:      $CALL_ID"
echo "Sign:         $SIGN"
echo

curl -sS -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "vpbx_api_key=${VPBX_API_KEY}" \
  --data-urlencode "sign=${SIGN}" \
  --data-urlencode "json=${JSON_PAYLOAD}" | sed -n '1,200p'

echo
