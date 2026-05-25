# n8n_ai_call_center
Продакшн-конфигурация AI Call Center на базе n8n (Ubuntu 24.04, Docker, Traefik, HTTPS, автоматические бэкапы).

## Краткое описание
Проект предназначен для развёртывания n8n в продакшн-режиме:
- HTTPS через Traefik + Let's Encrypt;
- отдельный временный IP-режим для первичной настройки;
- резервное копирование и восстановление данных n8n.

## Структура
- `docker-compose.yml` — основной продакшн стек (HTTPS).
- `docker-compose.https.yml` — явный HTTPS стек (идентичен прод-режиму).
- `docker-compose.ip.yml` — временный HTTP режим по IP.
- `.env.example` — шаблон переменных для IP-режима.
- `.env.https.example` — шаблон переменных для HTTPS-режима.
- `.env.memory.example` — шаблон переменных для Postgres Memory + PostgREST API.
- `scripts/backup_n8n.sh` — бэкап тома `n8n_data`.
- `scripts/restore_n8n.sh` — восстановление `n8n_data` из архива.
- `legacy/` — устаревшие конфиги, оставлены только для справки.

## Документация Для Агентов
- Главная точка входа для любого нового агента:
  - `AGENTS.md`
- Документация по парсеру контактов и правилам работы агентов:
  - `agent_contact_parser_docs/00_INDEX.md`
  - `agent_contact_parser_docs/11_SERVER_TOOL_PATHS.md`
- Готовый агент-сборщик косметологов для `n8n` + Telegram:
  - `docs/cosmetologist_hunter_agent/README_RU.md`
  - `docs/cosmetologist_hunter_agent/06_SERVER_TOOLING_RU.md`
  - `workflows/COSMETOLOGIST_HUNTER_TELEGRAM_DRAFT.json`
  - `scripts/cosmetologist_hunter_service.py`
- Отдельный email-followup контур по таблицам `контакты_косметологов_москва_*`:
  - `docs/email_followup_agent/README_RU.md`
  - `docs/email_followup_agent/01_ARCHITECTURE_AND_FLOW_RU.md`
  - `docs/email_followup_agent/02_LIVE_CONFIG_AND_SCHEDULE_RU.md`
  - `docs/email_followup_agent/03_SEARCH_RULES_AND_FILTERS_RU.md`
  - `docs/email_followup_agent/04_RUNBOOK_AND_OPERATIONS_RU.md`
  - `docs/email_followup_agent/05_TEST_REPORT_2026-04-29_RU.md`
  - `docs/email_followup_agent/06_CHECKPOINT_RU.md`
  - `workflows/EMAIL_FOLLOWUP_AGENT_DRAFT.json`
  - `scripts/email_followup_service.py`

## Быстрый запуск
1. Подготовьте `.env.https` на сервере (на основе `.env.https.example`).
   - Для KB Sync Agent задайте:
     - `KB_GITHUB_TOKEN` (PAT с доступом к repo);
     - `N8N_PUBLIC_API_KEY` (опционально, для статистики workflow через n8n API).
   - Для Memory Neuro Agent задайте:
     - `MEMORY_GITHUB_TOKEN` (PAT с доступом к `MaxCorpOrg/memory`);
     - опционально `MEMORY_CONNECTOR_GDRIVE_URL` / `MEMORY_CONNECTOR_DROPBOX_URL` / `MEMORY_CONNECTOR_S3_URL` (+ `MEMORY_CONNECTOR_AUTH_TOKEN`).
2. Запустите продакшн стек:
   - `docker compose --env-file .env.https -f docker-compose.https.yml up -d`

## Бэкапы
- Ручной запуск:
  - `./scripts/backup_n8n.sh`
- Восстановление:
  - `./scripts/restore_n8n.sh /home/aicore/n8n-backups/n8n-backup_YYYY-MM-DD_HH-MM-SS.tar.gz`

## Watchlist
- Проверка релизов и security advisory:
  - `./scripts/check_n8n_watchlist.sh`
- Подробный регламент:
  - `docs/N8N_WATCHLIST_RU.md`

## Voice Call Center (RU)
- Быстрый старт для исходящих звонков по РФ + запись результатов в PostgreSQL:
  - `docs/VOICE_CALL_CENTER_RU.md`
- Архитектура SIP-трансляции и материалы по обучаемому агенту:
  - `docs/call-translation-bridge/README_RU.md`
- Текущее live-состояние ElevenLabs-агента и voice-настроек:
  - `docs/call-translation-bridge/08_LIVE_ELEVEN_AGENT_RU.md`
- Дополнительный compose override с Postgres:
  - `docker-compose.callcenter.yml`
- SQL-схема:
  - `sql/001_call_center.sql`

## Postgres Memory + API (RU)
- Готовый compose override с Postgres (для памяти агента) и PostgREST (REST API):
  - `docker-compose.memory.yml`
- SQL-схема памяти:
  - `sql/002_agent_memory.sql`
- Шаблон переменных:
  - `.env.memory.example`
- Запуск вместе с основным стеком:
  - `cp .env.memory.example .env.memory`
  - `docker compose --env-file .env.https --env-file .env.memory -f docker-compose.https.yml -f docker-compose.memory.yml up -d`
- Подключение в n8n (`Postgres Chat Memory`):
  - Host: `postgres_memory`
  - Port: `5432`
  - Database: `${POSTGRES_MEMORY_DB}`
  - User: `${POSTGRES_MEMORY_USER}`
  - Password: `${POSTGRES_MEMORY_PASSWORD}`
  - Session Key: `={{ $json.session_id || $json.chatId || $json.userId }}`
- Для call-center агента (долговременная non-PII память + аудит действий):
  - `sql/003_call_agent_pro.sql`
  - `sql/004_seed_lipolong.sql`
  - `sql/005_seed_lipolong_kb_pack.sql`
  - `docs/agent_kb_lipolong/README_RU.md`
  - `docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_RU.md`
  - `docs/agent_kb_lipolong/09_DIALOG_SCRIPTS_RU.md`
  - `docs/call-translation-bridge/05_AGENT_ENV_AND_DB_RU.md`
  - `docs/call-translation-bridge/07_ELEVEN_TOOL_CALL_LOG_RU.md`
  - `docs/call-translation-bridge/09_ELEVEN_TOOL_SEND_SMS_RU.md`
  - `scripts/create_google_sheet_callcenter.py` (создание таблицы логирования звонков)
  - `workflows/ELEVEN_TOOL_CALL_LOG_BRIDGE_DRAFT.json` (шаблон bridge для записи итогов звонка в Google Sheet)
  - `workflows/ELEVEN_TOOL_SEND_SMS_BRIDGE_DRAFT.json` (шаблон bridge для отправки SMS через Mango direct API `vpbx/commands/sms`)

## Adminer UI (RU)
- Отдельный HTTPS вход в PostgreSQL через Traefik:
  - `docker-compose.adminer.yml`
- Переменные в `.env.https`:
  - `ADMINER_DOMAIN` (например `db.example.com`)
  - `ADMINER_BASICAUTH` в формате `user:hash` (htpasswd APR1)
- Пример генерации хеша:
  - `printf "admin:%s\n" "$(openssl passwd -apr1 'StrongPasswordHere')"`
- Запуск вместе с основным стеком:
  - `docker compose --env-file .env.https --env-file .env.memory -f docker-compose.https.yml -f docker-compose.memory.yml -f docker-compose.adminer.yml up -d adminer`
- После запуска открой:
  - `https://${ADMINER_DOMAIN}`
- Параметры подключения внутри Adminer:
  - System: `PostgreSQL`
  - Server: `postgres_memory`
  - Username: `${POSTGRES_MEMORY_USER}`
  - Password: `${POSTGRES_MEMORY_PASSWORD}`
  - Database: `${POSTGRES_MEMORY_DB}`

## GitHub Actions Deploy
Для workflow `.github/workflows/deploy.yml` должны быть настроены:
- `secrets.SERVER_SSH_KEY` (или `secrets.DEPLOY_SSH_KEY`) — приватный SSH-ключ пользователя `aicore`.
- `secrets.SERVER_HOST` (или `vars.SERVER_HOST`) — IP/домен сервера.
