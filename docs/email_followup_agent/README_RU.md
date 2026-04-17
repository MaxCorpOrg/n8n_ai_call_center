# Email Followup Agent (RU)

## Что это

Отдельный контур для email-follow-up без участия ElevenLabs.

Он делает три вещи:
- находит в Google Sheets таблицы `контакты_косметологов_москва_*`;
- ищет строки, где клиенту нужно отправить информацию по продукту на почту;
- проверяет/исправляет email, при необходимости ищет его на сайте по номеру и названию компании, после чего отправляет письмо.

## Файлы

- Workflow draft:
  - `/home/max/n8n_ai_call_center/workflows/EMAIL_FOLLOWUP_AGENT_DRAFT.json`
  - `/home/max/n8n_ai_call_center/workflows/EMAIL_FOLLOWUP_AGENT_MANUAL_DRAFT.json`
- Сервис:
  - `/home/max/n8n_ai_call_center/scripts/email_followup_service.py`
- Run script:
  - `/home/max/n8n_ai_call_center/scripts/run_email_followup_service.sh`
- Env template:
  - `/home/max/n8n_ai_call_center/.env.email_followup.example`
- Systemd unit:
  - `/home/max/n8n_ai_call_center/deploy/systemd/email_followup.service.example`

## Как работает

1. `n8n` по расписанию или через manual webhook вызывает отдельный host-сервис `/run`.
2. Сервис через Google Drive API находит таблицы по префиксу.
3. В каждой таблице читает лист `Лиды_обзвон`.
4. Собирает состояние по лидам, чтобы не реагировать на старые исторические строки.
5. Ищет email:
   - сначала в явных email-полях;
   - потом в `notes_short` / `notes_redacted`;
   - затем в “неправильных” полях вроде `phone_primary` или `source_record_key`, если туда случайно попал email;
   - если email нет или он битый, ищет сайт через поиск по номеру/компании и вытаскивает email уже со страницы сайта.
6. Дописывает техколонки в лист и обновляет запись.
7. Отправляет письмо через SMTP.

## Какие колонки сервис добавляет

Сервис не трогает диапазон `A:AM`, который уже используется звонковым контуром. Новые колонки добавляются в конец листа:

- `contact_email`
- `email_source_url`
- `email_verified_at`
- `email_verification_status`
- `email_send_status`
- `email_sent_at`
- `email_sent_to`
- `email_last_error`

Это сделано специально, чтобы не ломать текущие `call_log` и `AUTODIAL_DISPATCHER`.

## Когда строка считается кандидатом

Сервис смотрит в первую очередь на:
- `preferred_channel = email`
- `next_step = send_kp`
- `call_result = send_kp_pending_callback`
- упоминания `email / e-mail / почта / на почту` в заметках
- уже записанный email в строке

## Проверка без отправки

```bash
cd /home/max/n8n_ai_call_center
python3 scripts/email_followup_service.py run --dry-run --limit-sheets 1 --max-records 5
```

## Боевой запуск на сервере

Основной режим сейчас такой:

1. Host-сервис работает через `systemd`.
2. `n8n` контейнер получает `EMAIL_FOLLOWUP_URL` и `EMAIL_FOLLOWUP_AUTH_TOKEN` из `.env.email_followup`.
3. Из Docker сети `n8n` ходит в сервис по адресу `http://172.18.0.1:8791`.
4. В `n8n` должен быть разрешён доступ к env в нодах: `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`.
5. На host нужен firewall rule для Docker bridge:
   `ufw allow proto tcp from 172.18.0.0/16 to any port 8791 comment 'email_followup_docker_bridge'`
6. Cron-workflow должен быть только schedule-only, без manual webhook внутри.
7. Для ручного запуска используется отдельный manual-only workflow с webhook path:
   `email-followup-live/run`
8. У manual webhook должен быть задан `webhookId`, иначе `n8n 2.6.4` может зарегистрировать только служебный namespaced path вместо короткого production-path.
9. Для стабильного runtime стоит ограничить сетевой резолвинг:
   `EMAIL_FOLLOWUP_HTTP_TIMEOUT_SEC=15`
   `EMAIL_FOLLOWUP_RESOLVER_TOTAL_TIMEOUT_SEC=25`
   `EMAIL_FOLLOWUP_RESOLVER_SEARCH_LIMIT=4`
   `EMAIL_FOLLOWUP_RESOLVER_MAX_VISITS=4`

Проверка:

```bash
curl -H 'Authorization: Bearer <EMAIL_FOLLOWUP_AUTH_TOKEN>' \
  'http://127.0.0.1:8791/health'
```

После изменения `.env.email_followup` перезапустите `n8n`, чтобы контейнер перечитал переменные:

```bash
cd /home/aicore/n8n-server
docker compose up -d n8n
systemctl restart email_followup.service
```

## HTTP endpoints

- `GET /health`
- `POST /run`
- `POST /send-test`

Пример ручного запуска:

```bash
curl -X POST 'http://127.0.0.1:8791/run' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <EMAIL_FOLLOWUP_AUTH_TOKEN>' \
  -d '{
    "dry_run": true,
    "limit_sheets": 1,
    "max_records": 5
  }'
```

Ручной запуск через `n8n` production webhook:

```bash
curl -X POST 'https://www.n-8-n.site/webhook/email-followup-live/run' \
  -H 'Content-Type: application/json' \
  -d '{
    "dry_run": true,
    "limit_sheets": 1,
    "max_records": 5
  }'
```

SMTP smoke-test:

```bash
cd /home/max/n8n_ai_call_center
python3 scripts/email_followup_service.py send-test --to-email your_test_email@example.com
```

## Что ещё нужно руками

- заполнить `.env.email_followup`;
- дать рабочие Google OAuth credentials;
- задать SMTP credentials;
- импортировать `EMAIL_FOLLOWUP_AGENT_DRAFT.json` в `n8n`.

## Где лежат локальные секреты

Локальные секреты email-followup сохранены в файле:
- `/home/max/n8n_ai_call_center/.env.email_followup`

Файл исключён из git через `.gitignore`.

Что там сейчас должно храниться:
- `EMAIL_FOLLOWUP_SMTP_HOST`
- `EMAIL_FOLLOWUP_SMTP_PORT`
- `EMAIL_FOLLOWUP_SMTP_USERNAME`
- `EMAIL_FOLLOWUP_SMTP_PASSWORD`
- `EMAIL_FOLLOWUP_FROM_EMAIL`
- `EMAIL_FOLLOWUP_REPLY_TO`

В Markdown и handoff-документах хранить только путь и имена переменных, без самого пароля.
