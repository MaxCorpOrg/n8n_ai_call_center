# N8N Watchlist (RU)

Документ фиксирует регулярный контроль обновлений и security advisory по `n8n-io/n8n`.

## Цель
- не пропускать критические уязвимости (HIGH/CRITICAL);
- держать прод на актуальном стабильном релизе 2.x;
- обновлять n8n контролируемо: бэкап -> обновление -> проверка.

## Текущий baseline (на 6 февраля 2026)
- Текущий pinned image: `docker.n8n.io/n8nio/n8n:2.6.4`
- Последний stable 2.x: `n8n@2.6.4`
- Последний pre-release 2.x: `n8n@2.7.2`

Проверено через:
- `https://github.com/n8n-io/n8n/releases`
- `https://github.com/n8n-io/n8n/security/advisories`

## Ключевые security-advisory для мониторинга
- `GHSA-8398-gmmx-564h` (CVE-2026-25115)
- `GHSA-hv53-3329-vmrm` (CVE-2026-25056)
- `GHSA-6cqr-8cfr-67f8` (CVE-2026-25049)
- `GHSA-9g95-qf3f-ggrw` (CVE-2026-25053)
- `GHSA-v4pr-fm98-w9pg` (CVE-2026-21858)
- `GHSA-v364-rw7m-3263` (CVE-2026-21877)
- `GHSA-62r4-hw23-cc8v` (CVE-2025-68668)
- `GHSA-v98v-ff95-f3cp` (CVE-2025-68613)

Важно: список выше не финальный. Источником истины всегда остаётся live-лента advisory в GitHub.

## Автоматическая проверка
Используйте скрипт:
```bash
cd ~/n8n-server
./scripts/check_n8n_watchlist.sh
```

Что делает скрипт:
- запрашивает GitHub API релизов и security advisory;
- сравнивает ваш текущий pinned tag из `docker-compose.https.yml` с latest stable 2.x;
- печатает список HIGH/CRITICAL advisory;
- сохраняет отчёт в `logs/watchlist/`.

## Рекомендуемый cron (ежедневно в 09:00 UTC)
```bash
0 9 * * * cd /home/aicore/n8n-server && ./scripts/check_n8n_watchlist.sh >> /home/aicore/n8n-backups/watchlist.log 2>&1
```

## Процедура безопасного обновления
1. Проверить watchlist и release notes.
2. Сделать бэкап:
   - `./scripts/backup_n8n.sh`
3. Обновить тег `n8n` в `docker-compose.https.yml`.
4. Применить обновление:
   - `docker compose --env-file .env.https -f docker-compose.https.yml pull`
   - `docker compose --env-file .env.https -f docker-compose.https.yml up -d`
5. Smoke-check:
   - `curl -I https://n8n.n-8-n.site`
   - проверить логи `n8n` и `traefik`.
6. При проблеме: восстановление из бэкапа `scripts/restore_n8n.sh`.
