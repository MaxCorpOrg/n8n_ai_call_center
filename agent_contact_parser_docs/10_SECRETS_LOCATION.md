# Secrets Location

Локальные секреты для агента сохранены в файле:
- `/home/max/n8n_ai_call_center/agent_contact_parser_docs/.secrets/cosmetologist_hunter.env`

Файл находится внутри проекта, но исключён из git через `.gitignore`.

Что там хранится:
- `TELEGRAM_BOT_TOKEN`
- `MISTRAL_API_KEY`
- `TELEGRAM_WEBHOOK_SECRET`
- `COSMETOLOGIST_HUNTER_AUTH_TOKEN`
- `COSMETOLOGIST_HUNTER_LIVE_URL`

Для боевого запуска на сервере дополнительно нужны:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
