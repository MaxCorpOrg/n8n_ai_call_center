# n8n_ai_call_center
Продакшн-конфигурация сервера AI Call Center на базе n8n (Ubuntu 24.04, Docker, HTTPS).

## Краткое описание проекта
Проект разворачивает n8n для автоматизации AI-робота и call-сценариев:
- временный запуск по IP (`docker-compose.ip.yml`);
- продакшн-запуск по домену и HTTPS через Traefik + Let's Encrypt (`docker-compose.https.yml`);
- регулярные бэкапы данных n8n (`scripts/backup_n8n.sh`).

## Основные файлы
- `docker-compose.ip.yml` — запуск n8n по IP/HTTP для первичной настройки.
- `docker-compose.https.yml` — продакшн-режим с TLS.
- `.env.example` и `.env.https.example` — шаблоны переменных окружения.
- `scripts/backup_n8n.sh` — скрипт резервного копирования тома n8n с retention.

## Быстрый запуск
1. Заполнить `.env` (для IP-режима) или `.env.https` (для HTTPS-режима).
2. Запустить нужный compose:
   - `docker compose -f docker-compose.ip.yml up -d`
   - `docker compose --env-file .env.https -f docker-compose.https.yml up -d`
