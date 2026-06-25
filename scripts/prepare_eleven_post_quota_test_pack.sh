#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_post_quota_test_pack.sh OUTPUT_DIR [TO_NUMBER]

Builds a ready-to-run post-quota test pack with:
  - manifest.json
  - copied payload candidates
  - copied current snapshot summary
  - run_commands.sh
  - compare_commands.sh
  - README.txt
EOF
  exit 1
fi

OUTPUT_DIR="$1"
TO_NUMBER="${2:-+79251130826}"

mkdir -p "$OUTPUT_DIR"

LATEST_DIR="${LATEST_DIR:-.runtime/eleven_control_tower_latest}"

CURRENT_SUMMARY_SRC="${CURRENT_SUMMARY_SRC:-$LATEST_DIR/snapshot/summary.json}"
CURRENT_RESPONSE_SRC="${CURRENT_RESPONSE_SRC:-$LATEST_DIR/snapshot/response.json}"
ALIGNMENT_SRC="${ALIGNMENT_SRC:-$LATEST_DIR/alignment.json}"
LEADERBOARD_SRC="${LEADERBOARD_SRC:-.runtime/eleven_lab_version_leaderboard_2026-06-18.json}"
INTERRUPTIBLE_SRC="${INTERRUPTIBLE_SRC:-$LATEST_DIR/interruptible_balanced.json}"
INTERRUPTIBLE_SOFTFILL_SRC="${INTERRUPTIBLE_SOFTFILL_SRC:-$LATEST_DIR/interruptible_softfill.json}"
INTERRUPTIBLE_LATEFILL_SRC="${INTERRUPTIBLE_LATEFILL_SRC:-$LATEST_DIR/interruptible_latefill.json}"
REPEATABLE_FALLBACK_SRC="${REPEATABLE_FALLBACK_SRC:-.runtime/eleven_lab_llm_compare_gemini_2026-06-17/payload_tool_only_final_close.json}"
REPEATABLE_FALLBACK_RESPONSE="${REPEATABLE_FALLBACK_RESPONSE:-.runtime/eleven_lab_llm_compare_gemini_2026-06-17/server_apply_result_v13_tool_only_final_close/response.json}"
TURN_VARIANT_CHECK_DIR="${TURN_VARIANT_CHECK_DIR:-$LATEST_DIR/turn_checks}"
QUOTA_SUMMARY_SRC="${QUOTA_SUMMARY_SRC:-$LATEST_DIR/quota/eleven_quota_preflight_summary.json}"
READINESS_SUMMARY_SRC="${READINESS_SUMMARY_SRC:-$LATEST_DIR/readiness/live_readiness_summary.json}"
VARIANT_MATRIX_SRC="${VARIANT_MATRIX_SRC:-$TURN_VARIANT_CHECK_DIR/variant_matrix.json}"

cp "$CURRENT_SUMMARY_SRC" "$OUTPUT_DIR/current_published_summary.json"
cp "$CURRENT_RESPONSE_SRC" "$OUTPUT_DIR/current_published_response.json"
cp "$ALIGNMENT_SRC" "$OUTPUT_DIR/docs_alignment.json"
cp "$LEADERBOARD_SRC" "$OUTPUT_DIR/version_leaderboard.json"
cp "$INTERRUPTIBLE_SRC" "$OUTPUT_DIR/payload_interruptible_balanced.json"
cp "$INTERRUPTIBLE_SOFTFILL_SRC" "$OUTPUT_DIR/payload_interruptible_softfill.json"
cp "$INTERRUPTIBLE_LATEFILL_SRC" "$OUTPUT_DIR/payload_interruptible_latefill.json"
cp "$REPEATABLE_FALLBACK_SRC" "$OUTPUT_DIR/payload_repeatable_fallback.json"
cp "$REPEATABLE_FALLBACK_RESPONSE" "$OUTPUT_DIR/repeatable_fallback_response.json"
mkdir -p "$OUTPUT_DIR/variant_checks"
cp "$TURN_VARIANT_CHECK_DIR/published_current.json" "$OUTPUT_DIR/variant_checks/published_current.json"
cp "$TURN_VARIANT_CHECK_DIR/interruptible_balanced.json" "$OUTPUT_DIR/variant_checks/interruptible_balanced.json"
cp "$TURN_VARIANT_CHECK_DIR/interruptible_softfill.json" "$OUTPUT_DIR/variant_checks/interruptible_softfill.json"
cp "$TURN_VARIANT_CHECK_DIR/interruptible_latefill.json" "$OUTPUT_DIR/variant_checks/interruptible_latefill.json"
cp "$TURN_VARIANT_CHECK_DIR/variant_matrix.json" "$OUTPUT_DIR/variant_checks/variant_matrix.json"

MANIFEST_JSON="$OUTPUT_DIR/manifest.json"
README_TXT="$OUTPUT_DIR/README.txt"
RUN_COMMANDS_SH="$OUTPUT_DIR/run_commands.sh"
COMPARE_COMMANDS_SH="$OUTPUT_DIR/compare_commands.sh"
VALIDATE_VARIANTS_SH="$OUTPUT_DIR/validate_variants.sh"
RECOMMEND_NEXT_VARIANT_SH="$OUTPUT_DIR/recommend_next_variant.sh"
OPERATIONAL_BRIEF_JSON="$OUTPUT_DIR/operational_brief.json"
OPERATIONAL_BRIEF_MD="$OUTPUT_DIR/operational_brief.md"

jq -n \
  --arg created_at_utc "$(date -u +%FT%TZ)" \
  --arg to_number "$TO_NUMBER" \
  --arg current_summary "current_published_summary.json" \
  --arg current_response "current_published_response.json" \
  --arg docs_alignment "docs_alignment.json" \
  --arg leaderboard "version_leaderboard.json" \
  --arg interruptible_payload "payload_interruptible_balanced.json" \
  --arg interruptible_softfill_payload "payload_interruptible_softfill.json" \
  --arg interruptible_latefill_payload "payload_interruptible_latefill.json" \
  --arg repeatable_payload "payload_repeatable_fallback.json" \
  --arg repeatable_response "repeatable_fallback_response.json" \
  --arg variant_checks_dir "variant_checks" \
  '{
    created_at_utc: $created_at_utc,
    objective: "Post-quota first execution pack for the best next Eleven agent cycle",
    to_number_default: $to_number,
    current_published: {
      branch_id: "agtbrch_3701kv7waz0teny9xvsgv7sjt0bp",
      version_id: "agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k",
      llm: "gpt-5-mini",
      tts: "eleven_v3_conversational",
      source_summary: $current_summary,
      source_response: $current_response
    },
    primary_lab_candidate: {
      label: "interruptible_balanced_from_published",
      purpose: "Fix likely barge-in / give-the-human-room problem",
      payload_file: $interruptible_payload
    },
    secondary_lab_candidate: {
      label: "interruptible_softfill_from_published",
      purpose: "Preserve barge-in improvements while making fillers less bot-like and less time-promising",
      payload_file: $interruptible_softfill_payload
    },
    tertiary_lab_candidate: {
      label: "interruptible_latefill_from_published",
      purpose: "Preserve softer filler behavior while delaying filler masking slightly closer to official-doc starting guidance",
      payload_file: $interruptible_latefill_payload
    },
    repeatable_fallback_candidate: {
      label: "repeatable_fallback_tool_only_final_close",
      version_id: "agtvrsn_0901kva21515f08v6xn9w3v05zg3",
      purpose: "Best repeatable fallback from current evidence",
      payload_file: $repeatable_payload,
      source_response: $repeatable_response
    },
    advisory_inputs: {
      docs_alignment: $docs_alignment,
      version_leaderboard: $leaderboard,
      variant_checks_dir: $variant_checks_dir
    },
    execution_order: [
      "Run pack-local variant validation",
      "Run readiness after quota is restored",
      "Self-test current published version 9601",
      "Apply and self-test interruptible balanced variant",
      "If needed, apply and self-test interruptible softfill variant",
      "If needed, apply and self-test interruptible latefill variant",
      "If needed, apply and self-test repeatable fallback 0901-family payload"
    ]
  }' > "$MANIFEST_JSON"

python3 ./scripts/report_eleven_operational_brief.py \
  --quota "$QUOTA_SUMMARY_SRC" \
  --readiness "$READINESS_SUMMARY_SRC" \
  --pack "$MANIFEST_JSON" \
  --matrix "$VARIANT_MATRIX_SRC" \
  --alignment "$ALIGNMENT_SRC" \
  --json-output "$OPERATIONAL_BRIEF_JSON" \
  --md-output "$OPERATIONAL_BRIEF_MD" \
  >/dev/null

cat > "$README_TXT" <<EOF
POST-QUOTA TEST PACK

Что внутри:
- current_published_summary.json
- docs_alignment.json
- version_leaderboard.json
- payload_interruptible_balanced.json
- payload_interruptible_softfill.json
- payload_interruptible_latefill.json
- payload_repeatable_fallback.json
- variant_checks/
- operational_brief.json
- operational_brief.md
- run_commands.sh
- compare_commands.sh
- validate_variants.sh
- recommend_next_variant.sh

Логика запуска:
1. Сначала локально прогнать validate_variants.sh.
2. Потом проверить readiness после пополнения квоты.
3. Потом один self-test на текущей published version 9601.
4. Потом lab-only variant "interruptible balanced".
5. Если стало лучше, но fillers всё ещё звучат слишком рано или слишком по-ботски, проверить "interruptible softfill".
6. Если softfill уже лучше, но filler всё ещё включается чуть рановато, проверить "interruptible latefill".
7. Если published и interruptible-варианты не дадут нужный результат, проверить repeatable fallback 0901-family.

Почему такой порядок:
- published 9601 — текущая реальность;
- interruptible balanced — самый вероятный фикс жалобы "она не даёт мне говорить";
- interruptible softfill — тот же human-room fix, но с более аккуратным filler behavior;
- interruptible latefill — тот же аккуратный filler behavior, но с более поздним стартом filler masking;
- repeatable fallback — лучший воспроизводимый кандидат из архива разговоров.
EOF

cat > "$RUN_COMMANDS_SH" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

PACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TO_NUMBER="${1:-+79251130826}"
DATE_TAG="$(date +%F_%H-%M-%S)"
READINESS_DIR=".runtime/post_quota_readiness_${DATE_TAG}"

echo "[1/7] validate local pack variants"
"$PACK_DIR/validate_variants.sh"

echo "[2/7] readiness"
./scripts/report_eleven_live_readiness.sh "$READINESS_DIR"

DIAGNOSIS="$(jq -r '.overall_diagnosis // ""' "$READINESS_DIR/live_readiness_summary.json")"
if [[ "$DIAGNOSIS" == "quota_blocker_active" ]]; then
  echo "Quota blocker is still active. Stop here."
  echo "See: $READINESS_DIR/live_readiness_summary.json"
  exit 2
fi

echo "[3/7] current published self-test"
./scripts/run_eleven_selftest_audit.sh \
  ".runtime/post_quota_current_${DATE_TAG}" \
  "$TO_NUMBER" \
  "post_quota_current" \
  "agtbrch_3701kv7waz0teny9xvsgv7sjt0bp" \
  "agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k"

echo "[4/7] apply interruptible balanced variant to lab branch"
./scripts/apply_eleven_agent_payload.sh \
  "$PACK_DIR/payload_interruptible_balanced.json" \
  ".runtime/post_quota_apply_interruptible_${DATE_TAG}"

echo "[5/7] self-test interruptible balanced variant"
./scripts/run_eleven_selftest_audit.sh \
  ".runtime/post_quota_interruptible_${DATE_TAG}" \
  "$TO_NUMBER" \
  "post_quota_interruptible" \
  "agtbrch_3701kv7waz0teny9xvsgv7sjt0bp"

echo "[6/7] optional interruptible softfill apply"
echo "If interruptible balanced still sounds too bot-like in fillers, run:"
echo "./scripts/apply_eleven_agent_payload.sh \"$PACK_DIR/payload_interruptible_softfill.json\" \".runtime/post_quota_apply_softfill_${DATE_TAG}\""
echo "./scripts/run_eleven_selftest_audit.sh \".runtime/post_quota_softfill_${DATE_TAG}\" \"$TO_NUMBER\" \"post_quota_softfill\" \"agtbrch_3701kv7waz0teny9xvsgv7sjt0bp\""
echo

echo "[6.5/7] optional interruptible latefill apply"
echo "If softfill is close but fillers still begin too early, run:"
echo "./scripts/apply_eleven_agent_payload.sh \"$PACK_DIR/payload_interruptible_latefill.json\" \".runtime/post_quota_apply_latefill_${DATE_TAG}\""
echo "./scripts/run_eleven_selftest_audit.sh \".runtime/post_quota_latefill_${DATE_TAG}\" \"$TO_NUMBER\" \"post_quota_latefill\" \"agtbrch_3701kv7waz0teny9xvsgv7sjt0bp\""
echo

echo "[7/7] optional repeatable fallback apply"
echo "If needed, run:"
echo "./scripts/apply_eleven_agent_payload.sh \"$PACK_DIR/payload_repeatable_fallback.json\" \".runtime/post_quota_apply_repeatable_${DATE_TAG}\""
echo "./scripts/run_eleven_selftest_audit.sh \".runtime/post_quota_repeatable_${DATE_TAG}\" \"$TO_NUMBER\" \"post_quota_repeatable\" \"agtbrch_3701kv7waz0teny9xvsgv7sjt0bp\""
echo
echo "After you have 2 or more run dirs, compare them with:"
echo "\"$PACK_DIR/compare_commands.sh\" \".runtime/post_quota_current_${DATE_TAG}\" \".runtime/post_quota_interruptible_${DATE_TAG}\" [additional_run_dirs]"
echo
echo "If you want a recommendation from an audit file, run dir, or complaint text, use:"
echo "\"$PACK_DIR/recommend_next_variant.sh\" [AUDIT_JSON_OR_RUN_DIR] [FREEFORM_COMPLAINT...]"
EOF

cat > "$COMPARE_COMMANDS_SH" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 RUN_DIR_1 RUN_DIR_2 [RUN_DIR_3 ...]" >&2
  exit 1
fi

DATE_TAG="$(date +%F_%H-%M-%S)"
./scripts/compare_eleven_candidate_runs.py "$@" \
  --output ".runtime/post_quota_candidate_comparison_${DATE_TAG}.json"
EOF

cat > "$VALIDATE_VARIANTS_SH" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

PACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[variant-check] published_current"
python3 ./scripts/check_eleven_turn_variant_invariants.py \
  "$PACK_DIR/current_published_response.json" \
  published_current

echo "[variant-check] interruptible_balanced"
python3 ./scripts/check_eleven_turn_variant_invariants.py \
  "$PACK_DIR/payload_interruptible_balanced.json" \
  interruptible_balanced

echo "[variant-check] interruptible_softfill"
python3 ./scripts/check_eleven_turn_variant_invariants.py \
  "$PACK_DIR/payload_interruptible_softfill.json" \
  interruptible_softfill

echo "[variant-check] interruptible_latefill"
python3 ./scripts/check_eleven_turn_variant_invariants.py \
  "$PACK_DIR/payload_interruptible_latefill.json" \
  interruptible_latefill

echo "[variant-matrix]"
python3 ./scripts/report_eleven_turn_variant_matrix.py \
  published_current "$PACK_DIR/current_published_response.json" \
  interruptible_balanced "$PACK_DIR/payload_interruptible_balanced.json" \
  interruptible_softfill "$PACK_DIR/payload_interruptible_softfill.json" \
  interruptible_latefill "$PACK_DIR/payload_interruptible_latefill.json"
EOF

cat > "$RECOMMEND_NEXT_VARIANT_SH" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

PACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

AUDIT_JSON=""
if [[ $# -ge 1 && -d "$1" && -f "$1/finalization_audit.json" ]]; then
  AUDIT_JSON="$1/finalization_audit.json"
  shift
elif [[ $# -ge 1 && -f "$1" ]]; then
  AUDIT_JSON="$1"
  shift
elif [[ $# -ge 1 && "$1" == *.json ]]; then
  echo "Audit JSON not found: $1" >&2
  exit 1
fi

ARGS=(--matrix "$PACK_DIR/variant_checks/variant_matrix.json")

if [[ -n "$AUDIT_JSON" ]]; then
  ARGS+=(--audit "$AUDIT_JSON")
fi

if [[ $# -gt 0 ]]; then
  ARGS+=(--complaint "$*")
fi

python3 ./scripts/report_eleven_next_variant_advisor.py "${ARGS[@]}"
EOF

chmod +x "$RUN_COMMANDS_SH"
chmod +x "$COMPARE_COMMANDS_SH"
chmod +x "$VALIDATE_VARIANTS_SH"
chmod +x "$RECOMMEND_NEXT_VARIANT_SH"

echo "Prepared post-quota test pack: $OUTPUT_DIR"
echo "Manifest: $MANIFEST_JSON"
