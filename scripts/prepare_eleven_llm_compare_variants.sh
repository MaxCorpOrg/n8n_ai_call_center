#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_llm_compare_variants.sh SOURCE_AGENT_JSON OUTPUT_ROOT [DATE_TAG]

Example:
  scripts/prepare_eleven_llm_compare_variants.sh \
    .runtime/eleven_lab_flash_return_2026-06-16/response.json \
    .runtime \
    2026-06-16

Creates ready-to-apply LLM comparison payloads for the current lab baseline:
  - gemini-2.5-flash
  - claude-sonnet-4-5
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_ROOT="$2"
DATE_TAG="${3:-$(date +%F)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER="$SCRIPT_DIR/prepare_eleven_llm_variant.sh"

if [[ ! -x "$HELPER" ]]; then
  echo "Helper script is missing or not executable: $HELPER" >&2
  exit 1
fi

"$HELPER" \
  "$SOURCE_JSON" \
  "gemini-2.5-flash" \
  "$OUTPUT_ROOT/eleven_lab_llm_compare_gemini_${DATE_TAG}/payload.json" \
  "Lab LLM compare: GPT-4.1 -> Gemini 2.5 Flash"

"$HELPER" \
  "$SOURCE_JSON" \
  "claude-sonnet-4-5" \
  "$OUTPUT_ROOT/eleven_lab_llm_compare_claude_${DATE_TAG}/payload.json" \
  "Lab LLM compare: GPT-4.1 -> Claude Sonnet 4.5"

cat <<EOF
Prepared variants:
  $OUTPUT_ROOT/eleven_lab_llm_compare_gemini_${DATE_TAG}/payload.json
  $OUTPUT_ROOT/eleven_lab_llm_compare_claude_${DATE_TAG}/payload.json
EOF

