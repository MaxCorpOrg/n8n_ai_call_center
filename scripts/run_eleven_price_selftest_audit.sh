#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_FULL="$SCRIPT_DIR/run_eleven_selftest_audit.sh"
PRICE_ANALYZE="$SCRIPT_DIR/analyze_eleven_price_scenario.py"

usage() {
  cat <<'EOF' >&2
Usage:
  run_eleven_price_selftest_audit.sh OUTPUT_DIR TO_NUMBER TEST_KEY [BRANCH_ID] [EXPECTED_VERSION_ID]
  run_eleven_price_selftest_audit.sh OUTPUT_DIR TO_NUMBER TEST_KEY [BRANCH_ID] [EXPECTED_VERSION_ID] --dry-run
  run_eleven_price_selftest_audit.sh --price-only OUTPUT_DIR

Modes:
  1) Full cycle:
     - runs normal self-test + finalization audit
     - then runs price-specific transcript audit
     - writes price_scenario_audit.json

  2) Price-only:
     - reads existing OUTPUT_DIR/conversation_poll_final.json
     - writes OUTPUT_DIR/price_scenario_audit.json
EOF
  exit 1
}

print_summary() {
  local audit_json="$1"
  jq '{
    conversation_id,
    branch_id,
    version_id,
    price_question_detected,
    issues_count,
    issue_types: [.issues[].type]
  }' "$audit_json"
}

run_price_only() {
  local output_dir="$1"
  local final_json="$output_dir/conversation_poll_final.json"
  local audit_json="$output_dir/price_scenario_audit.json"

  if [[ ! -f "$final_json" ]]; then
    echo "Missing final conversation JSON: $final_json" >&2
    exit 1
  fi

  "$PRICE_ANALYZE" "$final_json" > "$audit_json"
  echo "Saved price audit: $audit_json"
  print_summary "$audit_json"
}

if [[ $# -lt 1 ]]; then
  usage
fi

if [[ "$1" == "--price-only" ]]; then
  [[ $# -eq 2 ]] || usage
  run_price_only "$2"
  exit 0
fi

if [[ $# -lt 3 ]]; then
  usage
fi

OUTPUT_DIR="$1"
TO_NUMBER="$2"
TEST_KEY="$3"
BRANCH_ID="${4:-}"
EXPECTED_VERSION_ID="${5:-}"
TAIL_ARG="${6:-}"

if [[ ! -x "$RUN_FULL" ]]; then
  echo "Missing or non-executable: $RUN_FULL" >&2
  exit 1
fi

if [[ ! -x "$PRICE_ANALYZE" ]]; then
  echo "Missing or non-executable: $PRICE_ANALYZE" >&2
  exit 1
fi

if [[ -n "$BRANCH_ID" && -n "$EXPECTED_VERSION_ID" ]]; then
  if [[ "$TAIL_ARG" == "--dry-run" ]]; then
    "$RUN_FULL" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY" "$BRANCH_ID" "$EXPECTED_VERSION_ID" --dry-run
    exit 0
  fi
  "$RUN_FULL" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY" "$BRANCH_ID" "$EXPECTED_VERSION_ID"
elif [[ -n "$BRANCH_ID" ]]; then
  if [[ "$EXPECTED_VERSION_ID" == "--dry-run" ]]; then
    "$RUN_FULL" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY" "$BRANCH_ID" --dry-run
    exit 0
  fi
  "$RUN_FULL" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY" "$BRANCH_ID"
else
  if [[ "$BRANCH_ID" == "--dry-run" ]]; then
    "$RUN_FULL" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY" --dry-run
    exit 0
  fi
  "$RUN_FULL" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY"
fi

run_price_only "$OUTPUT_DIR"
