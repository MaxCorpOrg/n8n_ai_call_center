#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HTTPS_COMPOSE="${HTTPS_COMPOSE:-${REPO_ROOT}/docker-compose.https.yml}"
OUT_DIR="${OUT_DIR:-${REPO_ROOT}/logs/watchlist}"
RELEASES_URL="https://api.github.com/repos/n8n-io/n8n/releases?per_page=50"
ADVISORIES_URL="https://api.github.com/repos/n8n-io/n8n/security-advisories?per_page=100"
NOW_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

mkdir -p "${OUT_DIR}"
TMP_RELEASES="$(mktemp)"
TMP_ADVISORIES="$(mktemp)"
trap 'rm -f "${TMP_RELEASES}" "${TMP_ADVISORIES}"' EXIT

curl -fsSL "${RELEASES_URL}" > "${TMP_RELEASES}"
curl -fsSL "${ADVISORIES_URL}" > "${TMP_ADVISORIES}"

CURRENT_TAG="$(awk -F':' '/image: docker\.n8n\.io\/n8nio\/n8n:/ {gsub(/[[:space:]]/,"",$3); print $3; exit}' "${HTTPS_COMPOSE}")"
if [ -z "${CURRENT_TAG}" ]; then
  echo "ERROR: Could not detect current n8n tag from ${HTTPS_COMPOSE}" >&2
  exit 1
fi

REPORT_FILE="${OUT_DIR}/n8n_watchlist_${NOW_UTC//:/-}.txt"

python3 - <<'PY' "${TMP_RELEASES}" "${TMP_ADVISORIES}" "${CURRENT_TAG}" "${NOW_UTC}" > "${REPORT_FILE}"
import json
import sys
from datetime import datetime

releases_path, advisories_path, current_tag, now_utc = sys.argv[1:5]

with open(releases_path, 'r', encoding='utf-8') as f:
    releases = json.load(f)
with open(advisories_path, 'r', encoding='utf-8') as f:
    advisories = json.load(f)

stable_2x = [
    r for r in releases
    if (not r.get('prerelease')) and str(r.get('tag_name', '')).startswith('n8n@2.')
]
stable_2x.sort(key=lambda r: r.get('published_at') or '', reverse=True)
latest_stable = stable_2x[0] if stable_2x else None

prerelease_2x = [
    r for r in releases
    if r.get('prerelease') and str(r.get('tag_name', '')).startswith('n8n@2.')
]
prerelease_2x.sort(key=lambda r: r.get('published_at') or '', reverse=True)
latest_prerelease = prerelease_2x[0] if prerelease_2x else None

active_high_critical = [
    a for a in advisories
    if a.get('state') == 'published' and str(a.get('severity', '')).lower() in {'high', 'critical'}
]
active_high_critical.sort(key=lambda a: a.get('published_at') or '', reverse=True)

print('=== n8n Watchlist Report ===')
print(f'Generated (UTC): {now_utc}')
print(f'Current pinned n8n tag: {current_tag}')
print('')

if latest_stable:
    latest_tag = latest_stable.get('tag_name', '-')
    latest_at = latest_stable.get('published_at', '-')
    latest_url = latest_stable.get('html_url', '-')
    print(f'Latest stable 2.x: {latest_tag} ({latest_at})')
    print(f'Release URL: {latest_url}')
    if current_tag == latest_tag.replace('n8n@', ''):
        print('Status: OK (pinned tag is latest stable 2.x)')
    else:
        print('Status: UPDATE AVAILABLE')
else:
    print('Latest stable 2.x: not found')

print('')
if latest_prerelease:
    print(f'Latest pre-release 2.x: {latest_prerelease.get("tag_name", "-")} ({latest_prerelease.get("published_at", "-")})')
    print(f'Pre-release URL: {latest_prerelease.get("html_url", "-")}')
else:
    print('Latest pre-release 2.x: not found')

print('')
print(f'Published HIGH/CRITICAL advisories: {len(active_high_critical)}')
for adv in active_high_critical[:15]:
    ghsa = adv.get('ghsa_id', '-')
    sev = str(adv.get('severity', '-')).upper()
    cve = adv.get('cve_id') or '-'
    pub = adv.get('published_at') or '-'
    summary = (adv.get('summary') or '').strip().replace('\n', ' ')
    url = adv.get('html_url') or '-'
    print(f'- [{sev}] {ghsa} / {cve} ({pub})')
    print(f'  {summary}')
    print(f'  {url}')

print('')
print('Primary sources:')
print('- https://github.com/n8n-io/n8n/releases')
print('- https://github.com/n8n-io/n8n/security/advisories')
PY

cat "${REPORT_FILE}"
echo
echo "Saved report: ${REPORT_FILE}"
