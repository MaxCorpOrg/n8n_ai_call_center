#!/usr/bin/env bash
set -euo pipefail
# ─────────────────────────────────────────────────────────────
# test_e2e_callflow.sh — End-to-end call flow integration test
# Tests: webhook delivery → response parsing → basic validation
# Usage:  ./scripts/test_e2e_callflow.sh <webhook_url> <vpbx_api_key> <vpbx_api_salt> <to_number>
# ─────────────────────────────────────────────────────────────

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <webhook_url> <vpbx_api_key> <vpbx_api_salt> <to_number_hint>"
  echo ""
  echo "Tests:"
  echo "  1. Webhook reachability (GET)"
  echo "  2. Valid call event delivery (POST)"
  echo "  3. Invalid signature rejection"
  echo "  4. Malformed payload rejection"
  exit 1
fi

WEBHOOK_URL="$1"
VPBX_API_KEY="$2"
VPBX_API_SALT="$3"
TO_NUMBER_HINT="$4"

PASS=0
FAIL=0

green()  { echo -e "\033[0;32m  ✓ PASS: $1\033[0m"; PASS=$((PASS + 1)); }
red()    { echo -e "\033[0;31m  ✗ FAIL: $1\033[0m"; FAIL=$((FAIL + 1)); }

echo "═══ E2E Call Flow Test ═══"
echo "Webhook: ${WEBHOOK_URL}"
echo "Time:    $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# ── Test 1: Webhook reachability ───────────────────────────
echo "Test 1: Webhook reachability"
HTTP_CODE=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "${WEBHOOK_URL}" 2>/dev/null || echo "000")
if [[ "${HTTP_CODE}" != "000" ]]; then
  green "Webhook reachable (HTTP ${HTTP_CODE})"
else
  red "Webhook unreachable (connection failed)"
fi

# ── Test 2: Valid call event ───────────────────────────────
echo ""
echo "Test 2: Valid call event delivery"
CALL_ID="e2e-test-$(date +%s)"
JSON_PAYLOAD=$(cat <<JSON
{"entry_id":"e2e-entry","call_id":"${CALL_ID}","timestamp":$(date +%s),"seq":1,"call_state":"Appeared","location":"ivr","from":{"number":"79001234567"},"to":{"number":"${TO_NUMBER_HINT}"}}
JSON
)

SIGN_INPUT="${VPBX_API_KEY}${JSON_PAYLOAD}${VPBX_API_SALT}"
SIGN=$(printf '%s' "$SIGN_INPUT" | sha256sum | awk '{print $1}')

RESPONSE=$(curl -sS -X POST "${WEBHOOK_URL}" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "vpbx_api_key=${VPBX_API_KEY}" \
  --data-urlencode "sign=${SIGN}" \
  --data-urlencode "json=${JSON_PAYLOAD}" \
  --max-time 15 2>/dev/null || echo '{"error":"timeout"}')

if echo "${RESPONSE}" | grep -qiE '"(route_sent|ok|accepted|queued|skipped|processed)"'; then
  green "Valid event accepted — call_id=${CALL_ID}"
elif echo "${RESPONSE}" | grep -qi '"error"'; then
  red "Valid event rejected: ${RESPONSE:0:200}"
else
  green "Event delivered (response: ${RESPONSE:0:100})"
fi

# ── Test 3: Invalid signature ─────────────────────────────
echo ""
echo "Test 3: Invalid signature rejection"
BAD_SIGN="0000000000000000000000000000000000000000000000000000000000000000"

RESPONSE=$(curl -sS -X POST "${WEBHOOK_URL}" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "vpbx_api_key=${VPBX_API_KEY}" \
  --data-urlencode "sign=${BAD_SIGN}" \
  --data-urlencode "json=${JSON_PAYLOAD}" \
  --max-time 10 -w "\n%{http_code}" 2>/dev/null || echo -e "\n000")

HTTP_CODE=$(echo "${RESPONSE}" | tail -1)
BODY=$(echo "${RESPONSE}" | sed '$d')

if [[ "${HTTP_CODE}" == "401" || "${HTTP_CODE}" == "403" ]]; then
  green "Invalid signature correctly rejected (HTTP ${HTTP_CODE})"
elif echo "${BODY}" | grep -qiE '"(invalid|forbidden|unauthorized|bad_sign)"'; then
  green "Invalid signature rejected with error message"
else
  red "Invalid signature NOT rejected (HTTP ${HTTP_CODE}, body: ${BODY:0:100})"
fi

# ── Test 4: Malformed payload ──────────────────────────────
echo ""
echo "Test 4: Malformed payload handling"
BAD_JSON='{"this":"is_not_valid_call_event"}'
BAD_SIGN_INPUT="${VPBX_API_KEY}${BAD_JSON}${VPBX_API_SALT}"
BAD_SIGN2=$(printf '%s' "$BAD_SIGN_INPUT" | sha256sum | awk '{print $1}')

RESPONSE=$(curl -sS -X POST "${WEBHOOK_URL}" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "vpbx_api_key=${VPBX_API_KEY}" \
  --data-urlencode "sign=${BAD_SIGN2}" \
  --data-urlencode "json=${BAD_JSON}" \
  --max-time 10 -w "\n%{http_code}" 2>/dev/null || echo -e "\n000")

HTTP_CODE=$(echo "${RESPONSE}" | tail -1)

if [[ "${HTTP_CODE}" =~ ^(200|400|422)$ ]]; then
  green "Malformed payload handled gracefully (HTTP ${HTTP_CODE})"
else
  red "Malformed payload returned HTTP ${HTTP_CODE}"
fi

# ── Summary ────────────────────────────────────────────────
echo ""
echo "─────────────────────────────────────────"
TOTAL=$((PASS + FAIL))
echo "Results: ${PASS}/${TOTAL} passed, ${FAIL} failed"

if [[ ${FAIL} -gt 0 ]]; then
  exit 1
fi
