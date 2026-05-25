# Email Followup Agent: Runbook и Эксплуатация

## Базовые проверки

### На сервере

```bash
ssh ai-core-prod-147
systemctl status email_followup.service --no-pager -l
```

### Health

```bash
AUTH="$(grep ^EMAIL_FOLLOWUP_AUTH_TOKEN= /home/aicore/n8n-server/.env.email_followup | cut -d= -f2-)"
curl -H "Authorization: Bearer $AUTH" http://127.0.0.1:8791/health
```

На что смотреть:

- `smtp_enabled`
- `imap_bounce_enabled`
- `firecrawl_enabled`
- `attachment_exists`
- `telegram_reports_enabled`
- `target_spreadsheet_ids`

## Ручные команды сервиса

### Dry-run

```bash
cd /home/aicore/n8n-server
python3 scripts/email_followup_service.py run --dry-run --limit-sheets 3 --max-records -1
```

### Live run

```bash
cd /home/aicore/n8n-server
python3 scripts/email_followup_service.py run --limit-sheets 3 --max-records -1
```

### SMTP smoke test

```bash
cd /home/aicore/n8n-server
python3 scripts/email_followup_service.py send-test --to-email your_test_email@example.com
```

### Bounce-only

```bash
cd /home/aicore/n8n-server
python3 scripts/email_followup_service.py process-bounces --limit-sheets 25 --limit-messages 20
```

## HTTP endpoints

- `GET /health`
- `POST /run`
- `POST /send-test`
- `POST /process-bounces`

### Пример live `/run`

```bash
AUTH="$(grep ^EMAIL_FOLLOWUP_AUTH_TOKEN= /home/aicore/n8n-server/.env.email_followup | cut -d= -f2-)"
curl -X POST \
  -H "Authorization: Bearer $AUTH" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8791/run \
  -d '{"dry_run":false,"force_resend":false,"limit_sheets":3,"max_records":-1}'
```

## Проверка n8n

### Scheduled workflow

Проверить:

- workflow активен;
- cron = `0 9,15 * * *`;
- body = `limit_sheets=100`, `max_records=-1`.

### Manual workflow

Проверить:

- webhook path = `email-followup-live/run`;
- workflow активен;
- отвечает JSON-результатом.

### Production webhook test

```bash
curl -X POST 'https://www.n-8-n.site/webhook/email-followup-live/run' \
  -H 'Content-Type: application/json' \
  -d '{"dry_run":true,"limit_sheets":1,"max_records":1}'
```

## Проверка Telegram

### Прямой тест

```bash
python3 - <<'PY'
import requests
base='https://api.telegram.org'
token='...'
chat_id='...'
r = requests.post(f'{base}/bot{token}/sendMessage', json={'chat_id': chat_id, 'text': 'probe'}, timeout=20)
print(r.status_code, r.text)
PY
```

Если `403 Forbidden`, проверять:

- верный ли `chat_id`;
- не заблокировал ли пользователь бота;
- не отправляются ли отчёты в чужой чат.

## Порядок безопасного live-изменения

1. Проверить текущий `git status`.
2. Снять backup нужных prod-файлов.
3. Внести изменения локально.
4. Прогнать локальную валидацию:
   - `python3 -m py_compile`
   - `build_email()`
   - `format_summary()`
5. Залить файл на сервер.
6. Проверить `py_compile` на сервере.
7. Перезапустить `email_followup.service`.
8. Проверить `/health`.
9. Прогнать `send-test`.
10. Прогнать `dry-run`.
11. Только потом делать live `/run`.

## Что считать обязательным aftercare

После значимых изменений нужно:

- обновить `docs/email_followup_agent/06_CHECKPOINT_RU.md`;
- обновить `docs/knowledge_base/09_PROJECT_CHANGELOG_AND_STATE.md`;
- если изменилось live-состояние — обновить `документация_для_агента/02_ТЕКУЩЕЕ_LIVE_СОСТОЯНИЕ.md`.

## Типовые проблемы

### `/health` показывает `firecrawl_enabled=false`

Проверить:

- `EMAIL_FOLLOWUP_FIRECRAWL_BASE_URL`
- `firecrawl-compat-bridge.service`
- `curl http://127.0.0.1:3002/health`

### Письмо ушло без смысла на каталог или платформу

Проверить:

- не вернулся ли seed email из старой строки;
- не попал ли домен в список каталогов;
- не нужен ли rollback конкретной строки в `manual_review`.

### Telegram-отчёт не пришёл

Проверить:

- `EMAIL_FOLLOWUP_TELEGRAM_CHAT_ID`
- `getUpdates`
- `getChat`
- не заблокирован ли бот пользователем

### Dry-run показывает `ready`, а live пошёл не туда

Проверить:

- merged context для лида;
- `extract_row_email()`;
- `resolve_best_email_candidate()`;
- нет ли старого `contact_email` в seed-строке.
