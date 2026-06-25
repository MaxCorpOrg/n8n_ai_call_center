#!/usr/bin/env bash
set -euo pipefail

DEFAULT_BRANCH_ID="agtbrch_3701kv7waz0teny9xvsgv7sjt0bp"
STATE_PATH="${LOCALHOST_RUN_STATE_PATH:-/home/max/.config/lipolong-eleven-relay-state.json}"
ALLOW_QUOTA_PRESSURE=0
SKIP_STATE_REPATCH=0

usage() {
  cat <<'EOF' >&2
Usage:
  run_eleven_live_cycle.sh OUTPUT_DIR TO_NUMBER TEST_KEY [BRANCH_ID] [EXPECTED_VERSION_ID] [--allow-quota-pressure] [--skip-state-repatch]

What it does:
  1. Runs Eleven quota preflight
  2. Optionally reapplies the current relay URL from localhost.run state
  3. Runs branch selftest only if the preflight result is acceptable

Default behavior:
  - if preflight shows recent quota-limit pressure, the script stops before placing a call
EOF
  exit 1
}

if [[ $# -lt 3 ]]; then
  usage
fi

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow-quota-pressure)
      ALLOW_QUOTA_PRESSURE=1
      shift
      ;;
    --skip-state-repatch)
      SKIP_STATE_REPATCH=1
      shift
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

set -- "${POSITIONAL[@]}"

OUTPUT_DIR="$1"
TO_NUMBER="$2"
TEST_KEY="$3"
BRANCH_ID="${4:-$DEFAULT_BRANCH_ID}"
EXPECTED_VERSION_ID="${5:-}"

mkdir -p "$OUTPUT_DIR"

PREFLIGHT_DIR="$OUTPUT_DIR/preflight_gate"
STATE_REPATCH_JSON="$OUTPUT_DIR/state_repatch_result.json"
SELFTEST_DIR="$OUTPUT_DIR/selftest"
SUMMARY_JSON="$OUTPUT_DIR/live_cycle_summary.json"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$PREFLIGHT_DIR"

"$SCRIPT_DIR/report_eleven_quota_preflight.sh" "$PREFLIGHT_DIR" "$BRANCH_ID" > "$PREFLIGHT_DIR/stdout.log" 2> "$PREFLIGHT_DIR/stderr.log"

PREFLIGHT_SUMMARY="$PREFLIGHT_DIR/eleven_quota_preflight_summary.json"
PREFLIGHT_DIAGNOSIS="$(jq -r '.diagnosis // ""' "$PREFLIGHT_SUMMARY")"

if [[ "$SKIP_STATE_REPATCH" != "1" && -f "$STATE_PATH" ]]; then
  STATE_PATH="$STATE_PATH" SCRIPT_DIR="$SCRIPT_DIR" python3 - <<'PY' > "$STATE_REPATCH_JSON"
import importlib.util
import json
import os
from pathlib import Path

state_path = Path(os.environ["STATE_PATH"])
state = json.loads(state_path.read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("lrts", Path(os.environ["SCRIPT_DIR"]) / "localhost_run_tunnel_sync.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
result = mod.patch_live_workflow(
    state["relay_url"],
    state.get("target_node_name", "Eleven | Outbound HTTP"),
)
print(json.dumps(result, ensure_ascii=False, indent=2))
PY
else
  jq -n \
    --arg skipped "$( [[ "$SKIP_STATE_REPATCH" == "1" ]] && echo true || echo false )" \
    --arg state_path "$STATE_PATH" \
    '{
      ok: true,
      skipped: ($skipped == "true"),
      reason: (if ($skipped == "true") then "skip_state_repatch_requested" else "state_file_missing" end),
      state_path: $state_path
    }' > "$STATE_REPATCH_JSON"
fi

if [[ "$PREFLIGHT_DIAGNOSIS" == "provider_quota_limit_observed_recently" && "$ALLOW_QUOTA_PRESSURE" != "1" ]]; then
  jq -n \
    --arg preflight_diagnosis "$PREFLIGHT_DIAGNOSIS" \
    --arg preflight_summary "$PREFLIGHT_SUMMARY" \
    --arg state_repatch_result "$STATE_REPATCH_JSON" \
    --arg latest_conversation_id "$(jq -r '.recent_branch_activity.latest_conversation.conversation_id // ""' "$PREFLIGHT_SUMMARY")" \
    --arg latest_version_id "$(jq -r '.recent_branch_activity.latest_conversation.version_id // ""' "$PREFLIGHT_SUMMARY")" \
    --arg latest_termination_reason "$(jq -r '.recent_branch_activity.latest_conversation.termination_reason // ""' "$PREFLIGHT_SUMMARY")" \
    --arg latest_call_time_utc "$(jq -r '.recent_branch_activity.latest_conversation.start_time_utc // ""' "$PREFLIGHT_SUMMARY")" \
    --arg recommendation "$(jq -r '.call_attempt_recommendation // ""' "$PREFLIGHT_SUMMARY")" \
    '{
      ok: false,
      action: "stopped_before_call",
      reason: "quota_pressure_guard",
      note: "Preflight already shows recent provider quota-limit failures. Call was intentionally skipped.",
      preflight_diagnosis: $preflight_diagnosis,
      call_attempt_recommendation: (if $recommendation == "" then null else $recommendation end),
      latest_blocking_signal: {
        conversation_id: (if $latest_conversation_id == "" then null else $latest_conversation_id end),
        version_id: (if $latest_version_id == "" then null else $latest_version_id end),
        termination_reason: (if $latest_termination_reason == "" then null else $latest_termination_reason end),
        start_time_utc: (if $latest_call_time_utc == "" then null else $latest_call_time_utc end)
      },
      preflight_summary: $preflight_summary,
      state_repatch_result: $state_repatch_result
    }' > "$SUMMARY_JSON"
  cat "$SUMMARY_JSON"
  exit 2
fi

if [[ -n "$EXPECTED_VERSION_ID" ]]; then
  "$SCRIPT_DIR/run_eleven_branch_selftest.sh" "$SELFTEST_DIR" "$TO_NUMBER" "$TEST_KEY" "$BRANCH_ID" "$EXPECTED_VERSION_ID"
else
  "$SCRIPT_DIR/run_eleven_branch_selftest.sh" "$SELFTEST_DIR" "$TO_NUMBER" "$TEST_KEY" "$BRANCH_ID"
fi

jq -n \
  --arg preflight_summary "$PREFLIGHT_SUMMARY" \
  --arg state_repatch_result "$STATE_REPATCH_JSON" \
  --arg selftest_dir "$SELFTEST_DIR" \
  '{
    ok: true,
    action: "selftest_executed",
    preflight_summary: $preflight_summary,
    state_repatch_result: $state_repatch_result,
    selftest_dir: $selftest_dir
  }' > "$SUMMARY_JSON"

cat "$SUMMARY_JSON"
