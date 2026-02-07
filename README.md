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
- `scripts/backup_n8n.sh` — бэкап тома `n8n_data`.
- `scripts/restore_n8n.sh` — восстановление `n8n_data` из архива.
- `legacy/` — устаревшие конфиги, оставлены только для справки.

## Быстрый запуск
1. Подготовьте `.env.https` на сервере (на основе `.env.https.example`).
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

## GitHub Actions Deploy
Для workflow `.github/workflows/deploy.yml` должны быть настроены:
- `secrets.SERVER_SSH_KEY` (или `secrets.DEPLOY_SSH_KEY`) — приватный SSH-ключ пользователя `aicore`.
- `secrets.SERVER_HOST` (или `vars.SERVER_HOST`) — IP/домен сервера.
