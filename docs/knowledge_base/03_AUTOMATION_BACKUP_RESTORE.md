# 03. Процессы и автоматизация

## 1) Деплой и эксплуатация

| Процесс | Скрипт/файл | Команда |
|---|---|---|
| Деплой stack | `docker-compose.https.yml` | `docker compose --env-file .env.https -f docker-compose.https.yml up -d` |
| Деплой memory stack | `docker-compose.memory.yml` | `docker compose --env-file .env.https --env-file .env.memory -f docker-compose.https.yml -f docker-compose.memory.yml up -d postgres_memory postgrest` |
| Деплой Adminer | `docker-compose.adminer.yml` | `docker compose --env-file .env.https --env-file .env.memory -f docker-compose.https.yml -f docker-compose.memory.yml -f docker-compose.adminer.yml up -d adminer` |
| Бэкап n8n | `scripts/backup_n8n.sh` | `./scripts/backup_n8n.sh` |
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
20 3 * * * cd /home/aicore/n8n-server && docker compose --env-file .env.https --env-file .env.memory -f docker-compose.https.yml -f docker-compose.memory.yml exec -T postgres_memory pg_dump -U n8n_memory -d n8n_memory > /home/aicore/n8n-backups/postgres/agent_memory_$(date +\%F_\%H-\%M-\%S).sql
0 9 * * * cd /home/aicore/n8n-server && ./scripts/check_n8n_watchlist.sh >> /home/aicore/n8n-backups/watchlist.log 2>&1
```

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
