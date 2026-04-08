#!/usr/bin/env bash
set -euo pipefail
# ─────────────────────────────────────────────────────────────
# test_backup_restore.sh — Validate backup/restore cycle
# Creates a test volume, backs it up, restores, verifies data.
# Usage:  ./scripts/test_backup_restore.sh
# ─────────────────────────────────────────────────────────────

TEST_VOLUME="n8n_backup_test_$$"
TEST_BACKUP_DIR="/tmp/n8n_backup_test_$$"
PASS=0
FAIL=0

green()  { echo -e "\033[0;32m  ✓ $1\033[0m"; PASS=$((PASS + 1)); }
red()    { echo -e "\033[0;31m  ✗ $1\033[0m"; FAIL=$((FAIL + 1)); }

cleanup() {
  echo ""
  echo "Cleaning up..."
  docker volume rm "${TEST_VOLUME}" 2>/dev/null || true
  rm -rf "${TEST_BACKUP_DIR}"
  echo "Done."
}
trap cleanup EXIT

echo "═══ Backup/Restore Integration Test ═══"
echo ""

# ── Setup: create test volume with data ────────────────────
echo "Setup: creating test volume with sample data..."
docker volume create "${TEST_VOLUME}" >/dev/null

docker run --rm \
  -v "${TEST_VOLUME}":/data \
  busybox \
  sh -c 'echo "test-data-12345" > /data/test.txt && echo "hello-world" > /data/config.json && mkdir -p /data/subdir && echo "nested" > /data/subdir/nested.txt'

green "Test volume created with sample data"

# ── Test 1: Backup ─────────────────────────────────────────
echo ""
echo "Test 1: Backup"
mkdir -p "${TEST_BACKUP_DIR}"

export PROJECT_NAME="backup-test"
export VOLUME_NAME="${TEST_VOLUME}"
export BACKUP_DIR="${TEST_BACKUP_DIR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${SCRIPT_DIR}/backup_n8n.sh"

ARCHIVE=$(ls -1t "${TEST_BACKUP_DIR}"/n8n-backup_*.tar.gz 2>/dev/null | head -1)
if [[ -n "${ARCHIVE}" && -f "${ARCHIVE}" ]]; then
  green "Backup created: $(basename "${ARCHIVE}")"
else
  red "Backup file not created"
  exit 1
fi

# ── Test 2: Archive integrity ──────────────────────────────
echo ""
echo "Test 2: Archive integrity"
if tar tzf "${ARCHIVE}" >/dev/null 2>&1; then
  green "Archive passes tar integrity check"
else
  red "Archive is corrupt"
fi

FILE_COUNT=$(tar tzf "${ARCHIVE}" | wc -l)
if [[ ${FILE_COUNT} -ge 3 ]]; then
  green "Archive contains ${FILE_COUNT} entries (expected ≥3)"
else
  red "Archive contains only ${FILE_COUNT} entries (expected ≥3)"
fi

# ── Test 3: Checksum file ──────────────────────────────────
echo ""
echo "Test 3: Checksum verification"
CHECKSUM_FILE="${ARCHIVE}.sha256"
if [[ -f "${CHECKSUM_FILE}" ]]; then
  green "Checksum file exists"
  if sha256sum --check --quiet "${CHECKSUM_FILE}" 2>/dev/null; then
    green "Checksum matches"
  else
    red "Checksum mismatch"
  fi
else
  red "Checksum file not created"
fi

# ── Test 4: Corrupt the volume, then restore ───────────────
echo ""
echo "Test 4: Restore after corruption"
docker run --rm \
  -v "${TEST_VOLUME}":/data \
  busybox \
  sh -c 'rm -rf /data/*'

# Verify corruption
EMPTY_CHECK=$(docker run --rm -v "${TEST_VOLUME}":/data busybox sh -c 'ls /data/ 2>/dev/null | wc -l')
if [[ "${EMPTY_CHECK}" == "0" ]]; then
  green "Volume corrupted (emptied) for restore test"
else
  red "Volume not properly emptied"
fi

# Restore (manual — restore_n8n.sh requires docker compose)
docker run --rm \
  -v "${TEST_VOLUME}":/data \
  -v "$(dirname "${ARCHIVE}")":/backup:ro \
  busybox \
  sh -c "tar xzf /backup/$(basename "${ARCHIVE}") -C /data"

# ── Test 5: Verify restored data ──────────────────────────
echo ""
echo "Test 5: Data integrity after restore"
RESTORED_DATA=$(docker run --rm -v "${TEST_VOLUME}":/data busybox cat /data/test.txt 2>/dev/null || echo "")
if [[ "${RESTORED_DATA}" == "test-data-12345" ]]; then
  green "Restored data matches original"
else
  red "Restored data mismatch: got '${RESTORED_DATA}'"
fi

NESTED_DATA=$(docker run --rm -v "${TEST_VOLUME}":/data busybox cat /data/subdir/nested.txt 2>/dev/null || echo "")
if [[ "${NESTED_DATA}" == "nested" ]]; then
  green "Nested file restored correctly"
else
  red "Nested file missing or wrong"
fi

# ── Summary ────────────────────────────────────────────────
echo ""
echo "─────────────────────────────────────────"
TOTAL=$((PASS + FAIL))
echo "Results: ${PASS}/${TOTAL} passed, ${FAIL} failed"

if [[ ${FAIL} -gt 0 ]]; then
  exit 1
fi
