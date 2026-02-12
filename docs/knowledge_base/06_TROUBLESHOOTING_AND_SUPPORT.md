# 06. Устранение неполадок и эскалация

## 1) Частые проблемы

| Симптом | Возможная причина | Решение |
|---|---|---|
| Бот не отвечает | workflow не активен / Telegram token error | Проверить activation + credential |
| Ошибка генерации через Gemini/Flow | quota/geo/API | Переключить движок на Pollinations, проверить Agent 5 |
| n8n недоступен по HTTPS | Traefik/сертификат/DNS | Проверить `traefik` logs + DNS + 443 |
| Ошибки после обновления | несовместимость версии | rollback из backup |
| Доступ к боту у посторонних | не настроен access control | Проверить `Access Control` узел master |
| Агент “залипает” в повторных уточнениях | некорректный intent/tag routing | Проверить `Router | Intent Parse`, `Reply Guardrail`, ветку error-output у `AGENT 1 | Manager` |
| Память диалога не сохраняется | не подключен `Postgres Chat Memory` или неверные креды | Проверить соединение n8n -> `postgres_memory`, таблицу `agent_memory` |
| Adminer не открывается | не поднят сервис / неверный Traefik route | Проверить `adminer` container, labels, HTTPS роутер |

## 2) Быстрый чек-лист диагностики
```bash
cd /home/aicore/n8n-server

docker compose --env-file .env.https --env-file .env.memory \
  -f docker-compose.https.yml -f docker-compose.memory.yml -f docker-compose.adminer.yml ps
docker compose --env-file .env.https --env-file .env.memory \
  -f docker-compose.https.yml -f docker-compose.memory.yml -f docker-compose.adminer.yml logs --tail 200 n8n
docker compose --env-file .env.https --env-file .env.memory \
  -f docker-compose.https.yml -f docker-compose.memory.yml -f docker-compose.adminer.yml logs --tail 200 traefik postgres_memory postgrest adminer
curl -I https://${DOMAIN_NAME}
curl -I https://${ADMINER_DOMAIN}
```

## 3) Runbook инцидента (P1)
1. Зафиксировать время и симптомы.
2. Проверить доступность сервиса и последние деплои.
3. Включить safe mode (ограничить внешние триггеры при необходимости).
4. Восстановить сервис/rollback.
5. Провести postmortem и обновить KB.

## 4) Проверка памяти вручную (SQL)
```bash
docker compose --env-file .env.https --env-file .env.memory \
  -f docker-compose.https.yml -f docker-compose.memory.yml exec -T postgres_memory psql -U n8n_memory -d n8n_memory \
  -c "SELECT session_id, role, left(content, 100) AS content_preview, created_at FROM agent_memory ORDER BY created_at DESC LIMIT 20;"
```
## 5) Контакты поддержки (шаблон)

| Роль | Контакт | SLA |
|---|---|---|
| Владелец платформы | TODO | 30 мин |
| DevOps/SRE | TODO | 30 мин |
| Backend/n8n инженер | TODO | 60 мин |
