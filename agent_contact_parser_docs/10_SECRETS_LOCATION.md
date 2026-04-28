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

Отдельно для email-followup локальные секреты сохранены в файле:
- `/home/max/n8n_ai_call_center/.env.email_followup`

Что там хранится:
- `EMAIL_FOLLOWUP_SMTP_HOST`
- `EMAIL_FOLLOWUP_SMTP_PORT`
- `EMAIL_FOLLOWUP_SMTP_USERNAME`
- `EMAIL_FOLLOWUP_SMTP_PASSWORD`
- `EMAIL_FOLLOWUP_FROM_EMAIL`
- `EMAIL_FOLLOWUP_REPLY_TO`
- `EMAIL_FOLLOWUP_IMAP_HOST`
- `EMAIL_FOLLOWUP_IMAP_PORT`
- `EMAIL_FOLLOWUP_IMAP_USERNAME`
- `EMAIL_FOLLOWUP_IMAP_PASSWORD`
- `EMAIL_FOLLOWUP_BOUNCE_STATE_PATH`
- `EMAIL_FOLLOWUP_DOMAIN_BLACKLIST_PATH`
- `EMAIL_FOLLOWUP_TELEGRAM_REPORTS_ENABLED`
- `EMAIL_FOLLOWUP_TELEGRAM_BOT_TOKEN`
- `EMAIL_FOLLOWUP_TELEGRAM_CHAT_ID`
- `EMAIL_FOLLOWUP_TELEGRAM_THREAD_ID`

Файл также исключён из git и не должен раскрываться в Markdown целиком.
