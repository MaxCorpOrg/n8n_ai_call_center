# 06. Устранение неполадок и эскалация

## 1) Частые проблемы

| Симптом | Возможная причина | Решение |
|---|---|---|
| Бот не отвечает | workflow не активен / Telegram token error | Проверить activation + credential |
| Ошибка генерации через Gemini/Flow | quota/geo/API | Переключить движок на Pollinations, проверить Agent 5 |
| n8n недоступен по HTTPS | Traefik/сертификат/DNS | Проверить `traefik` logs + DNS + 443 |
| Ошибки после обновления | несовместимость версии | rollback из backup |
| Доступ к боту у посторонних | не настроен access control | Проверить `Access Control` узел master |

## 2) Быстрый чек-лист диагностики
```bash
cd /home/aicore/n8n-server

docker compose --env-file .env.https -f docker-compose.https.yml ps
docker compose --env-file .env.https -f docker-compose.https.yml logs --tail 200 n8n
docker compose --env-file .env.https -f docker-compose.https.yml logs --tail 200 traefik
curl -I https://n8n.n-8-n.site
```

## 3) Runbook инцидента (P1)
1. Зафиксировать время и симптомы.
2. Проверить доступность сервиса и последние деплои.
3. Включить safe mode (ограничить внешние триггеры при необходимости).
4. Восстановить сервис/rollback.
5. Провести postmortem и обновить KB.

## 4) Контакты поддержки (шаблон)

| Роль | Контакт | SLA |
|---|---|---|
| Владелец платформы | TODO | 30 мин |
| DevOps/SRE | TODO | 30 мин |
| Backend/n8n инженер | TODO | 60 мин |
