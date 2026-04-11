# 03. Процессы и автоматизация

## 1) Деплой и эксплуатация

| Процесс | Скрипт/файл | Команда |
|---|---|---|
| Деплой stack | `docker-compose.https.yml` | `docker compose --env-file .env.https -f docker-compose.https.yml up -d` |
| Деплой memory stack | `docker-compose.memory.yml` | `docker compose --env-file .env.https --env-file .env.memory -f docker-compose.https.yml -f docker-compose.memory.yml up -d postgres_memory postgrest` |
| Деплой Adminer | `docker-compose.adminer.yml` | `docker compose --env-file .env.https --env-file .env.memory -f docker-compose.https.yml -f docker-compose.memory.yml -f docker-compose.adminer.yml up -d adminer` |
| Автодеплой clean-clone | `scripts/n8n-autodeploy-clean.sh` | `/usr/local/bin/n8n-autodeploy-clean` |
| Установка cron автодеплоя | `scripts/install_n8n_autodeploy_cron.sh` | `sudo ./scripts/install_n8n_autodeploy_cron.sh` |
| Бэкап n8n | `scripts/backup_n8n.sh` | `./scripts/backup_n8n.sh` |
| Бэкап `call_center` Postgres | `scripts/backup_call_center_postgres.sh` | `./scripts/backup_call_center_postgres.sh` |
| Restore n8n | `scripts/restore_n8n.sh` | `./scripts/restore_n8n.sh <archive.tar.gz>` |
| Watchlist check | `scripts/check_n8n_watchlist.sh` | `./scripts/check_n8n_watchlist.sh` |

## 2) График бэкапов (шаблон)

| Тип | Период | Retention | Хранилище | Проверка восстановления |
|---|---|---|---|---|
| n8n_data full | ежедневно 03:00 UTC | 14 дней | `/home/aicore/n8n-backups` | еженедельно |
| postgres_memory dump | ежедневно 03:20 UTC | 14 дней | `/home/aicore/n8n-backups/postgres` | еженедельно |
| watchlist log | ежедневно 09:00 UTC | 30 дней | `/home/aicore/n8n-backups/watchlist.log` | n/a |

Пример cron:
```cron
0 3 * * * cd /home/aicore/n8n-server && ./scripts/backup_n8n.sh >> /home/aicore/n8n-backups/backup.log 2>&1
10 3 * * * cd /home/aicore/n8n-ai-clean && ./scripts/backup_call_center_postgres.sh >> /home/aicore/n8n-backups/postgres/call_center_backup.log 2>&1
20 3 * * * cd /home/aicore/n8n-server && docker compose --env-file .env.https --env-file .env.memory -f docker-compose.https.yml -f docker-compose.memory.yml exec -T postgres_memory pg_dump -U n8n_memory -d n8n_memory > /home/aicore/n8n-backups/postgres/agent_memory_$(date +\%F_\%H-\%M-\%S).sql
0 9 * * * cd /home/aicore/n8n-server && ./scripts/check_n8n_watchlist.sh >> /home/aicore/n8n-backups/watchlist.log 2>&1
*/5 * * * * /usr/local/bin/n8n-autodeploy-clean >> /var/log/n8n-autodeploy-clean.log 2>&1
```

Важно:
- на live `147.45.213.87` cron автодеплоя уже включён через `/etc/cron.d/n8n-autodeploy-clean`;
- clean deploy должен работать из `/home/aicore/n8n-ai-clean`, а не из `/home/aicore/n8n-server`;
- для `call_center` Postgres теперь есть отдельный backup-скрипт и live-cron `/etc/cron.d/n8n-callcenter-backup`;
- bind mounts clean-clone должны опираться на `SERVER_RUNTIME_ROOT=/home/aicore/n8n-server`, чтобы не расходиться с живыми SQL и `local-files`.

## 3) Процедура восстановления (SOP)
1. Остановить/изолировать запись в n8n.
2. Проверить целостность архива.
3. Запустить `restore_n8n.sh`.
4. При необходимости восстановить memory БД:
   - `cat /path/to/dump.sql | docker compose --env-file .env.https --env-file .env.memory -f docker-compose.https.yml -f docker-compose.memory.yml exec -T postgres_memory psql -U n8n_memory -d n8n_memory`
5. Поднять stack.
6. Smoke-test webhooks, Telegram, workflow execution.

## 4) Примеры автоматизации

### Bash
```bash
#!/usr/bin/env bash
set -euo pipefail
cd /home/aicore/n8n-server
docker compose --env-file .env.https -f docker-compose.https.yml pull
./scripts/backup_n8n.sh
docker compose --env-file .env.https --env-file .env.memory \
  -f docker-compose.https.yml -f docker-compose.memory.yml -f docker-compose.adminer.yml up -d
```

### Ansible (пример)
```yaml
- hosts: ai_core
  become: true
  tasks:
    - name: Pull and restart n8n stack
      shell: |
        cd /home/aicore/n8n-server
        docker compose --env-file .env.https -f docker-compose.https.yml pull
        docker compose --env-file .env.https --env-file .env.memory -f docker-compose.https.yml -f docker-compose.memory.yml -f docker-compose.adminer.yml pull
        docker compose --env-file .env.https --env-file .env.memory -f docker-compose.https.yml -f docker-compose.memory.yml -f docker-compose.adminer.yml up -d
```
