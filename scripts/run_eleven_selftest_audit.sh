#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SELFTEST="$SCRIPT_DIR/run_eleven_branch_selftest.sh"
ANALYZE="$SCRIPT_DIR/analyze_eleven_conversation.py"

usage() {
  cat <<'EOF' >&2
Usage:
  run_eleven_selftest_audit.sh OUTPUT_DIR TO_NUMBER TEST_KEY [BRANCH_ID] [EXPECTED_VERSION_ID]
  run_eleven_selftest_audit.sh OUTPUT_DIR TO_NUMBER TEST_KEY [BRANCH_ID] [EXPECTED_VERSION_ID] --dry-run
  run_eleven_selftest_audit.sh --audit-only OUTPUT_DIR

Modes:
  1) Full cycle:
     - runs branch-targeted self-test
     - waits for conversation_poll_final.json
     - writes finalization_audit.json
     - prints short issue summary

  2) Audit-only:
     - reads existing OUTPUT_DIR/conversation_poll_final.json
     - writes OUTPUT_DIR/finalization_audit.json
     - prints short issue summary
EOF
  exit 1
}

print_summary() {
  local audit_json="$1"
  jq '{
    conversation_id,
    branch_id,
    version_id,
    call_summary_title,
    termination_reason,
    issues_count,
    issue_types: [.issues[].type]
  }' "$audit_json"
}

run_audit_only() {
  local output_dir="$1"
  local final_json="$output_dir/conversation_poll_final.json"
  local audit_json="$output_dir/finalization_audit.json"

  if [[ ! -f "$final_json" ]]; then
    echo "Missing final conversation JSON: $final_json" >&2
    exit 1
  fi

  "$ANALYZE" "$final_json" > "$audit_json"
  echo "Saved audit: $audit_json"
  print_summary "$audit_json"
}

if [[ $# -lt 1 ]]; then
  usage
fi

if [[ "$1" == "--audit-only" ]]; then
  [[ $# -eq 2 ]] || usage
  run_audit_only "$2"
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

if [[ ! -x "$RUN_SELFTEST" ]]; then
  echo "Missing or non-executable: $RUN_SELFTEST" >&2
  exit 1
fi

if [[ ! -x "$ANALYZE" ]]; then
  echo "Missing or non-executable: $ANALYZE" >&2
  exit 1
fi

if [[ -n "$BRANCH_ID" && -n "$EXPECTED_VERSION_ID" ]]; then
  if [[ "$TAIL_ARG" == "--dry-run" ]]; then
    "$RUN_SELFTEST" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY" "$BRANCH_ID" "$EXPECTED_VERSION_ID" --dry-run
    exit 0
  fi
  "$RUN_SELFTEST" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY" "$BRANCH_ID" "$EXPECTED_VERSION_ID"
elif [[ -n "$BRANCH_ID" ]]; then
  if [[ "$EXPECTED_VERSION_ID" == "--dry-run" ]]; then
    "$RUN_SELFTEST" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY" "$BRANCH_ID" --dry-run
    exit 0
  fi
  "$RUN_SELFTEST" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY" "$BRANCH_ID"
else
  if [[ "$BRANCH_ID" == "--dry-run" ]]; then
    "$RUN_SELFTEST" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY" --dry-run
    exit 0
  fi
  "$RUN_SELFTEST" "$OUTPUT_DIR" "$TO_NUMBER" "$TEST_KEY"
fi

run_audit_only "$OUTPUT_DIR"
