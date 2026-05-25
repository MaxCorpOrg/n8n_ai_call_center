# Email Followup Agent: Live Конфиг и Расписание

## Текущий live-контур

### Сервер

- host: `ai-core-prod-147`
- рабочий каталог: `/home/aicore/n8n-server`
- systemd service: `email_followup.service`

### Основные файлы на сервере

- `/home/aicore/n8n-server/scripts/email_followup_service.py`
- `/home/aicore/n8n-server/.env.email_followup`
- `/home/aicore/n8n-server/workflows/EMAIL_FOLLOWUP_AGENT_DRAFT.json`
- `/home/aicore/n8n-server/workflows/EMAIL_FOLLOWUP_AGENT_MANUAL_DRAFT.json`

## Live workflow

### Scheduled workflow

- name: `EMAIL_FOLLOWUP_AGENT_LIVE`
- workflow id: `VnIb8ZWUNkxGjgBZ`
- schedule: `09:00` и `15:00` по `Europe/Moscow`
- run body:
  - `dry_run=false`
  - `force_resend=false`
  - `limit_sheets=100`
  - `max_records=-1`

### Manual workflow

- name: `EMAIL_FOLLOWUP_AGENT_MANUAL_LIVE`
- workflow id: `2a319674-55ff-44fd-9aee-0a743838bea7`
- webhook path: `email-followup-live/run`

## Целевые таблицы в live

Сейчас в проде закреплены три таблицы:

1. `контакты_косметологов_москва_1`
   - `1FUHh8lS8pEx58eRK2Rt6AYn3cy6ogWSO32vZWqYw_Fc`
2. `контакты_косметологов_москва_2`
   - `1t0FtCL84l0QJvL9_7XDnmafJS1NHUSdiVyKgqNWOVmA`
3. `контакты_косметологов_москва_47`
   - `1pLrCNeQ_thipr5-fajPusgNZZSd5NHEZFmGkegfpIqI`

Это задаётся через `EMAIL_FOLLOWUP_SPREADSHEET_IDS`.

## Важные live-параметры

### Производственный режим

- `EMAIL_FOLLOWUP_MAX_SHEETS_PER_RUN=100`
- `EMAIL_FOLLOWUP_MAX_RECORDS_PER_RUN=-1`
- `EMAIL_FOLLOWUP_RESOLVER_TOTAL_TIMEOUT_SEC=60`
- `EMAIL_FOLLOWUP_USE_JINA_SEARCH_FALLBACK=true`
- `EMAIL_FOLLOWUP_INFER_EMAIL_FROM_DOMAIN=true`

### Web scraping / resolver

- `EMAIL_FOLLOWUP_FIRECRAWL_BASE_URL=http://127.0.0.1:3002`

На сервере живы:

- `firecrawl-compat-bridge.service`
- `firecrawl-playwright.service`
- `site-control-kit-browser.service`
- `site-control-kit-hub.service`

### Вложение

Текущее PDF-вложение:

- `/home/aicore/n8n-server/Документация по скриптам /КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ (2).pdf`

Файл обязателен для отправки. Если он пропал, агент должен не “молча слать без КП”, а возвращать ошибку.

### Почта

На проде должны быть включены:

- SMTP
- IMAP

Фактическое состояние подтверждается через `/health`.

### Telegram

Текущий recipient отчётов:

- username: `@M_a_x_i_m_M_i_k_h_a_i_l_o_v`
- chat type: `private`

Важно:

- токен бота хранится только в `.env.email_followup`;
- в документации не копировать токен;
- при смене recipient нужно обновлять `EMAIL_FOLLOWUP_TELEGRAM_CHAT_ID` и сразу делать тест `sendMessage`.

## Что подтверждено в live на 2026-04-29

- сервис активен;
- `/health` отвечает;
- `smtp_enabled=true`;
- `imap_bounce_enabled=true`;
- `firecrawl_enabled=true`;
- `attachment_exists=true`;
- `telegram_reports_enabled=true`;
- Telegram-отчёты после фикса recipient снова доходят.

## Почему расписание именно 09:00 и 15:00 MSK

Расписание вынесено в окна, где агент не конфликтует с обзвонным контуром:

- `09:00 MSK` — до основного окна звонков;
- `15:00 MSK` — после основного окна обзвона.

Это уменьшает риск пересечения:

- голосовой агент работает по таблице;
- email-агент одновременно правит те же записи.

## Что обязательно проверить после любых live-изменений

1. `systemctl status email_followup.service`
2. `curl /health`
3. workflow cron в `EMAIL_FOLLOWUP_AGENT_LIVE`
4. manual webhook path
5. Telegram test
6. `send-test` с вложением
