# Развёртывание

## 1. Переменные окружения
Создать файл:
- `/home/max/n8n_ai_call_center/.env.cosmetologist_hunter`

На основе:
- `/home/max/n8n_ai_call_center/.env.cosmetologist_hunter.example`

## 2. Локальный запуск сервиса
```bash
cd /home/max/n8n_ai_call_center
./scripts/run_cosmetologist_hunter_service.sh
```

Проверка:
```bash
curl http://127.0.0.1:8787/health
```

## 3. Автозапуск через systemd
Скопировать unit:
- `/home/max/n8n_ai_call_center/deploy/systemd/cosmetologist_hunter.service.example`

Далее:
```bash
sudo cp /home/max/n8n_ai_call_center/deploy/systemd/cosmetologist_hunter.service.example /etc/systemd/system/cosmetologist_hunter.service
sudo systemctl daemon-reload
sudo systemctl enable --now cosmetologist_hunter.service
sudo systemctl status cosmetologist_hunter.service
```

## 4. Импорт workflow в n8n
Импортировать файл:
- `/home/max/n8n_ai_call_center/workflows/COSMETOLOGIST_HUNTER_TELEGRAM_DRAFT.json`

После импорта нужно руками привязать:
- credential Telegram Bot
- credential Mistral

## 5. Переменная для n8n
В окружении `n8n` желательно задать:
```bash
COSMETOLOGIST_HUNTER_URL=http://127.0.0.1:8787
COSMETOLOGIST_HUNTER_AUTH_TOKEN=replace_with_long_random_token
```

Если `n8n` запущен в Docker отдельно, указывайте URL так, чтобы контейнер видел локальный сервис.

## 6. Защита HTTP-сервиса
Если задан `COSMETOLOGIST_HUNTER_AUTH_TOKEN`, сервис требует заголовок:
```bash
Authorization: Bearer <token>
```

Для продового наружного порта это обязательно.
