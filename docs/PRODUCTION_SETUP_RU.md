# Продакшн-настройка сервера AI Core (Ubuntu 24.04)

## Что настроено
1. Обновлена ОС Ubuntu 24.04 до актуального состояния.
2. Подготовлен пользователь `aicore` для рабочих операций.
3. Усилен SSH:
   - отключён вход `root`;
   - отключена парольная аутентификация;
   - разрешён вход только по ключам.
4. Установлены Docker Engine и Docker Compose Plugin.
5. Включён UFW с минимально необходимыми портами:
   - 22/tcp (SSH)
   - 80/tcp (HTTP)
   - 443/tcp (HTTPS)
6. Поднят n8n в двух режимах:
   - IP/HTTP для первичной инициализации;
   - домен/HTTPS через Traefik + Let's Encrypt.
7. Настроен автоматический бэкап данных n8n:
   - скрипт `scripts/backup_n8n.sh`;
   - ежедневный cron-запуск;
   - удаление старых архивов по retention.

## Файлы конфигурации
- `docker-compose.ip.yml` — временный режим запуска по IP.
- `docker-compose.https.yml` — продакшн через домен и TLS.
- `.env.example` — базовый шаблон переменных.
- `.env.https.example` — шаблон переменных для HTTPS-режима.

## Команды эксплуатации
```bash
# Статус сервисов
cd ~/n8n-server
docker compose --env-file .env.https -f docker-compose.https.yml ps

# Логи
cd ~/n8n-server
docker compose --env-file .env.https -f docker-compose.https.yml logs -f n8n
docker compose --env-file .env.https -f docker-compose.https.yml logs -f traefik

# Перезапуск
cd ~/n8n-server
docker compose --env-file .env.https -f docker-compose.https.yml restart n8n

# Бэкапы
ls -lah ~/n8n-backups
tail -n 100 ~/n8n-backups/backup.log
```
