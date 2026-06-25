#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

WITH_FETCH=0
DATE_TAG="${DATE_TAG:-$(date +%F)}"
TO_NUMBER="${TO_NUMBER:-+79251130826}"
LATEST_DIR=".runtime/eleven_control_tower_latest"

usage() {
  cat <<'EOF' >&2
Usage:
  refresh_eleven_control_tower.sh [--with-fetch] [--date-tag YYYY-MM-DD] [--to-number E164]

What it refreshes in one pass:
  1. Optional current agent snapshot fetch from live env
  2. Quota preflight
  3. Live readiness
  4. Docs alignment
  5. interruptible_balanced payload
  6. interruptible_softfill payload
  7. interruptible_latefill payload
  8. Turn-variant checks + matrix
  9. Post-quota execution pack
  10. Operational brief
  11. Stable latest-entrypoint aliases
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-fetch)
      WITH_FETCH=1
      shift
      ;;
    --date-tag)
      [[ $# -ge 2 ]] || usage
      DATE_TAG="$2"
      shift 2
      ;;
    --to-number)
      [[ $# -ge 2 ]] || usage
      TO_NUMBER="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      ;;
  esac
done

SNAPSHOT_DIR=".runtime/eleven_current_branch_snapshot_${DATE_TAG}_now"
QUOTA_DIR=".runtime/eleven_quota_preflight_${DATE_TAG}_check_now"
READINESS_DIR=".runtime/eleven_live_readiness_${DATE_TAG}_check_now"
ALIGNMENT_JSON=".runtime/eleven_docs_alignment_${DATE_TAG}.json"
BALANCED_JSON=".runtime/eleven_interruptible_balanced_variant_${DATE_TAG}.json"
SOFTFILL_JSON=".runtime/eleven_interruptible_softfill_variant_${DATE_TAG}.json"
LATEFILL_JSON=".runtime/eleven_interruptible_latefill_variant_${DATE_TAG}.json"
TURN_CHECK_DIR=".runtime/eleven_turn_variant_checks_${DATE_TAG}"
BRIEF_JSON=".runtime/eleven_operational_brief_${DATE_TAG}.json"
BRIEF_MD=".runtime/eleven_operational_brief_${DATE_TAG}.md"
ADVISOR_JSON=".runtime/eleven_next_variant_advisor_${DATE_TAG}.json"
ADVISOR_MD=".runtime/eleven_next_variant_advisor_${DATE_TAG}.md"
PACK_DIR=".runtime/eleven_post_quota_test_pack_${DATE_TAG}"

link_latest() {
  local src="$1"
  local dest="$2"
  mkdir -p "$(dirname "$dest")"
  ln -sfn "$(realpath "$src")" "$dest"
}

if [[ "$WITH_FETCH" -eq 1 ]]; then
  echo "[1/11] Fetch current live snapshot"
  "$SCRIPT_DIR/fetch_eleven_agent_snapshot_via_server_env.sh" "$SNAPSHOT_DIR"
else
  echo "[1/11] Reuse existing current snapshot"
  [[ -f "$SNAPSHOT_DIR/response.json" ]] || {
    echo "Missing snapshot: $SNAPSHOT_DIR/response.json" >&2
    echo "Run with --with-fetch or create the snapshot first." >&2
    exit 1
  }
fi

echo "[2/11] Quota preflight"
bash "$SCRIPT_DIR/report_eleven_quota_preflight.sh" "$QUOTA_DIR"

echo "[3/11] Live readiness"
bash "$SCRIPT_DIR/report_eleven_live_readiness.sh" "$READINESS_DIR"

echo "[4/11] Docs alignment"
python3 "$SCRIPT_DIR/report_eleven_docs_alignment.py" \
  "$SNAPSHOT_DIR/response.json" \
  --output "$ALIGNMENT_JSON" \
  >/dev/null

echo "[5/11] Build interruptible_balanced"
bash "$SCRIPT_DIR/prepare_eleven_interruptible_balanced_variant.sh" \
  "$SNAPSHOT_DIR/response.json" \
  "$BALANCED_JSON" \
  "Lab variant: interruptible balanced from ${DATE_TAG}" \
  >/dev/null

echo "[6/11] Build interruptible_softfill"
bash "$SCRIPT_DIR/prepare_eleven_interruptible_softfill_variant.sh" \
  "$SNAPSHOT_DIR/response.json" \
  "$SOFTFILL_JSON" \
  "Lab variant: interruptible softfill from ${DATE_TAG}" \
  >/dev/null

echo "[7/11] Build interruptible_latefill"
bash "$SCRIPT_DIR/prepare_eleven_interruptible_latefill_variant.sh" \
  "$SNAPSHOT_DIR/response.json" \
  "$LATEFILL_JSON" \
  "Lab variant: interruptible latefill from ${DATE_TAG}" \
  >/dev/null

echo "[8/11] Turn-variant checks"
mkdir -p "$TURN_CHECK_DIR"
python3 "$SCRIPT_DIR/check_eleven_turn_variant_invariants.py" \
  "$SNAPSHOT_DIR/response.json" \
  published_current > "$TURN_CHECK_DIR/published_current.json"
python3 "$SCRIPT_DIR/check_eleven_turn_variant_invariants.py" \
  "$BALANCED_JSON" \
  interruptible_balanced > "$TURN_CHECK_DIR/interruptible_balanced.json"
python3 "$SCRIPT_DIR/check_eleven_turn_variant_invariants.py" \
  "$SOFTFILL_JSON" \
  interruptible_softfill > "$TURN_CHECK_DIR/interruptible_softfill.json"
python3 "$SCRIPT_DIR/check_eleven_turn_variant_invariants.py" \
  "$LATEFILL_JSON" \
  interruptible_latefill > "$TURN_CHECK_DIR/interruptible_latefill.json"
python3 "$SCRIPT_DIR/report_eleven_turn_variant_matrix.py" \
  published_current "$SNAPSHOT_DIR/response.json" \
  interruptible_balanced "$BALANCED_JSON" \
  interruptible_softfill "$SOFTFILL_JSON" \
  interruptible_latefill "$LATEFILL_JSON" > "$TURN_CHECK_DIR/variant_matrix.json"

echo "[9/11] Post-quota pack"
CURRENT_SUMMARY_SRC="$SNAPSHOT_DIR/summary.json" \
CURRENT_RESPONSE_SRC="$SNAPSHOT_DIR/response.json" \
ALIGNMENT_SRC="$ALIGNMENT_JSON" \
INTERRUPTIBLE_SRC="$BALANCED_JSON" \
INTERRUPTIBLE_SOFTFILL_SRC="$SOFTFILL_JSON" \
INTERRUPTIBLE_LATEFILL_SRC="$LATEFILL_JSON" \
TURN_VARIANT_CHECK_DIR="$TURN_CHECK_DIR" \
QUOTA_SUMMARY_SRC="$QUOTA_DIR/eleven_quota_preflight_summary.json" \
READINESS_SUMMARY_SRC="$READINESS_DIR/live_readiness_summary.json" \
VARIANT_MATRIX_SRC="$TURN_CHECK_DIR/variant_matrix.json" \
bash "$SCRIPT_DIR/prepare_eleven_post_quota_test_pack.sh" "$PACK_DIR" "$TO_NUMBER"

echo "[10/11] Operational brief"
python3 "$SCRIPT_DIR/report_eleven_operational_brief.py" \
  --quota "$QUOTA_DIR/eleven_quota_preflight_summary.json" \
  --readiness "$READINESS_DIR/live_readiness_summary.json" \
  --pack "$PACK_DIR/manifest.json" \
  --matrix "$TURN_CHECK_DIR/variant_matrix.json" \
  --alignment "$ALIGNMENT_JSON" \
  --json-output "$BRIEF_JSON" \
  --md-output "$BRIEF_MD" \
  >/dev/null
python3 "$SCRIPT_DIR/report_eleven_next_variant_advisor.py" \
  --matrix "$TURN_CHECK_DIR/variant_matrix.json" \
  --json-output "$ADVISOR_JSON" \
  --md-output "$ADVISOR_MD" \
  >/dev/null

echo "[11/11] Refresh latest entrypoint"
rm -rf "$LATEST_DIR"
mkdir -p "$LATEST_DIR"
link_latest "$SNAPSHOT_DIR" "$LATEST_DIR/snapshot"
link_latest "$QUOTA_DIR" "$LATEST_DIR/quota"
link_latest "$READINESS_DIR" "$LATEST_DIR/readiness"
link_latest "$ALIGNMENT_JSON" "$LATEST_DIR/alignment.json"
link_latest "$BALANCED_JSON" "$LATEST_DIR/interruptible_balanced.json"
link_latest "$SOFTFILL_JSON" "$LATEST_DIR/interruptible_softfill.json"
link_latest "$LATEFILL_JSON" "$LATEST_DIR/interruptible_latefill.json"
link_latest "$TURN_CHECK_DIR" "$LATEST_DIR/turn_checks"
link_latest "$ADVISOR_JSON" "$LATEST_DIR/next_variant_advisor.json"
link_latest "$ADVISOR_MD" "$LATEST_DIR/next_variant_advisor.md"
link_latest "$PACK_DIR" "$LATEST_DIR/pack"
python3 "$SCRIPT_DIR/report_eleven_operational_brief.py" \
  --quota "$LATEST_DIR/quota/eleven_quota_preflight_summary.json" \
  --readiness "$LATEST_DIR/readiness/live_readiness_summary.json" \
  --pack "$LATEST_DIR/pack/manifest.json" \
  --matrix "$LATEST_DIR/turn_checks/variant_matrix.json" \
  --alignment "$LATEST_DIR/alignment.json" \
  --json-output "$LATEST_DIR/operational_brief.json" \
  --md-output "$LATEST_DIR/operational_brief.md" \
  >/dev/null
cat > "$LATEST_DIR/README.txt" <<EOF
Eleven Control Tower Latest

Это стабильная точка входа в самое свежее состояние ElevenLabs без привязки к дате.

Смотри в первую очередь:
- $LATEST_DIR/operational_brief.md
- $LATEST_DIR/next_variant_advisor.md
- $LATEST_DIR/readiness/live_readiness_summary.json
- $LATEST_DIR/quota/eleven_quota_preflight_summary.json
- $LATEST_DIR/pack/

Полный refresh:
- ./scripts/refresh_eleven_control_tower.sh --date-tag $DATE_TAG
- ./scripts/refresh_eleven_control_tower.sh --with-fetch --date-tag $DATE_TAG
EOF

echo
echo "Refreshed Eleven control tower:"
echo "- snapshot: $SNAPSHOT_DIR"
echo "- quota: $QUOTA_DIR/eleven_quota_preflight_summary.json"
echo "- readiness: $READINESS_DIR/live_readiness_summary.json"
echo "- alignment: $ALIGNMENT_JSON"
echo "- balanced: $BALANCED_JSON"
echo "- softfill: $SOFTFILL_JSON"
echo "- latefill: $LATEFILL_JSON"
echo "- checks: $TURN_CHECK_DIR"
echo "- brief: $PACK_DIR/operational_brief.md"
echo "- advisor: $LATEST_DIR/next_variant_advisor.md"
echo "- pack: $PACK_DIR"
echo "- latest: $LATEST_DIR/operational_brief.md"
