#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SELFTEST="$SCRIPT_DIR/run_eleven_branch_selftest.sh"
ANALYZE="$SCRIPT_DIR/analyze_eleven_conversation.py"
ADVISOR="$SCRIPT_DIR/report_eleven_next_variant_advisor.py"
DEFAULT_VARIANT_MATRIX=".runtime/eleven_control_tower_latest/turn_checks/variant_matrix.json"

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
    timing_summary: {
      long_gap_threshold_secs: .timing_summary.long_gap_threshold_secs,
      first_user_to_agent_gap_secs: .timing_summary.first_user_to_agent_gap_secs,
      user_to_agent_gap_stats_secs: .timing_summary.user_to_agent_gap_stats_secs,
      known_path_stats_secs: .timing_summary.known_path_stats_secs,
      unexplained_overhead_stats_secs: .timing_summary.unexplained_overhead_stats_secs,
      primary_bottleneck_counts: .timing_summary.primary_bottleneck_counts,
      llm_ttfb_stats_secs: .timing_summary.llm_ttfb_stats_secs,
      tts_ttfb_stats_secs: .timing_summary.tts_ttfb_stats_secs
    },
    top_recommendations: [.recommendations[0:3][] | {priority, code, title}],
    issues_count,
    issue_types: [.issues[].type]
  }' "$audit_json"
}

print_next_variant_summary() {
  local advice_json="$1"
  jq '{
    inputs,
    detected_reasons,
    ready_for_variant_testing,
    action_plan: [.action_plan[0:3][] | {
      kind,
      code,
      title
    }],
    recommended_order: [.recommended_order[0:3][] | {
      variant,
      why,
      turn_timeout,
      turn_eagerness,
      soft_timeout_seconds,
      interruptions_enabled
    }]
  }' "$advice_json"
}

generate_next_variant_advice() {
  local output_dir="$1"
  local audit_json="$output_dir/finalization_audit.json"
  local advice_json="$output_dir/next_variant_advice.json"
  local advice_md="$output_dir/next_variant_advice.md"
  local matrix_path="${ADVISOR_MATRIX_PATH:-$DEFAULT_VARIANT_MATRIX}"

  if [[ ! -f "$matrix_path" ]]; then
    echo "Variant matrix not found, skipping advisor: $matrix_path"
    return 0
  fi

  python3 "$ADVISOR" \
    --matrix "$matrix_path" \
    --audit "$audit_json" \
    --json-output "$advice_json" \
    --md-output "$advice_md" \
    >/dev/null

  echo "Saved next-variant advice: $advice_json"
  print_next_variant_summary "$advice_json"
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
  generate_next_variant_advice "$output_dir"
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

if [[ ! -f "$ADVISOR" ]]; then
  echo "Missing advisor script: $ADVISOR" >&2
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
