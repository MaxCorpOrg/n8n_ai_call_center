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
7. Настроены резервные копии:
   - `scripts/backup_n8n.sh` — создание архива `n8n_data`;
   - `scripts/restore_n8n.sh` — восстановление `n8n_data`;
   - ежедневный cron-запуск backup-скрипта.

## Файлы конфигурации
- `docker-compose.yml` — основной продакшн стек (HTTPS).
- `docker-compose.https.yml` — явный HTTPS-стек.
- `docker-compose.ip.yml` — временный IP/HTTP стек.
- `.env.example` — шаблон для IP-режима.
- `.env.https.example` — шаблон для HTTPS-режима.

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

# Бэкап
cd ~/n8n-server
./scripts/backup_n8n.sh

# Восстановление
cd ~/n8n-server
./scripts/restore_n8n.sh /home/aicore/n8n-backups/n8n-backup_YYYY-MM-DD_HH-MM-SS.tar.gz
```
