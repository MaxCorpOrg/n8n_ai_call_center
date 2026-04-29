# Email Followup Agent (RU)

## Что это

Отдельный контур для email-follow-up без участия ElevenLabs.

Он делает три вещи:
- находит в Google Sheets таблицы `контакты_косметологов_москва_*`;
- при необходимости может работать по фиксированному списку spreadsheet id, чтобы обходить только нужные обзвонные таблицы;
- ищет строки, где клиенту нужно отправить информацию по продукту на почту;
- проверяет/исправляет email, при необходимости ищет его на сайте по номеру и названию компании, после чего отправляет письмо;
- прикладывает к письму PDF-коммерческое предложение;
- обрабатывает bounce-ответы из почты, помечает проблемные адреса и ведет локальный blacklist доменов;
- повторно пытается автоисправить email при `domain_not_found`, ищет альтернативу по номеру/компании и фильтрует placeholder-адреса;
- умеет отправлять короткий операционный отчет в Telegram, включая статус по каждой таблице.

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
2. Сервис через Google Drive API находит таблицы по префиксу или берет их из `EMAIL_FOLLOWUP_SPREADSHEET_IDS`, если список задан явно.
3. В каждой таблице читает лист `Лиды_обзвон`.
4. Собирает состояние по лидам, чтобы не реагировать на старые исторические строки.
5. Ищет email:
   - сначала в явных email-полях;
   - потом в `notes_short` / `notes_redacted`;
   - затем в “неправильных” полях вроде `phone_primary` или `source_record_key`, если туда случайно попал email;
   - если email нет или он битый, ищет сайт через поиск по номеру/компании и вытаскивает email уже со страницы сайта.
6. Перед новой отправкой может разобрать bounce-сообщения из почты через IMAP и пометить уже умершие адреса.
7. Дописывает техколонки в лист и обновляет запись.
8. Перед отправкой собирает PDF-вложение с коммерческим предложением. Если файл не найден, письмо не уходит молча без вложения, а прогон возвращает явную ошибку.
9. Отправляет письмо через SMTP.
10. По итогам прогона может отправить краткий отчет в Telegram, где видно, по каким таблицам были отправки, а где новых записей не было.

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
- `email_bounced_at`
- `email_bounce_reason`
- `email_blacklisted_at`
- `email_blacklist_reason`

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
   `EMAIL_FOLLOWUP_RESOLVER_TOTAL_TIMEOUT_SEC=60`
   `EMAIL_FOLLOWUP_RESOLVER_SEARCH_LIMIT=4`
   `EMAIL_FOLLOWUP_RESOLVER_MAX_VISITS=4`
   Если на сервере поднят `firecrawl-compat-bridge`, рекомендуется сразу подключить:
   `EMAIL_FOLLOWUP_FIRECRAWL_BASE_URL=http://127.0.0.1:3002`
10. Для более агрессивного поиска email по номеру можно включить:
   `EMAIL_FOLLOWUP_USE_JINA_SEARCH_FALLBACK=true`
   `EMAIL_FOLLOWUP_INFER_EMAIL_FROM_DOMAIN=true`
11. Для обхода всех рабочих обзвонных таблиц без конфликта с дозвоном стоит закрепить список таблиц в env:
   `EMAIL_FOLLOWUP_SPREADSHEET_IDS=1FUHh8lS8pEx58eRK2Rt6AYn3cy6ogWSO32vZWqYw_Fc,1t0FtCL84l0QJvL9_7XDnmafJS1NHUSdiVyKgqNWOVmA,1pLrCNeQ_thipr5-fajPusgNZZSd5NHEZFmGkegfpIqI`
12. Для Telegram-отчета даже при пустом прогоне:
   `EMAIL_FOLLOWUP_TELEGRAM_REPORT_ON_EMPTY=true`
13. Для вложения КП по умолчанию используется:
   `Документация по скриптам /КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ (2).pdf`
14. Рабочее расписание для live workflow:
   `09:00` и `15:00` по `Europe/Moscow`

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
- `POST /process-bounces`
- `POST /send-test`

Пример ручного запуска:

```bash
curl -X POST 'http://127.0.0.1:8791/run' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <EMAIL_FOLLOWUP_AUTH_TOKEN>' \
  -d '{
    "dry_run": true,
    "limit_sheets": 3,
    "max_records": -1
  }'
```

Ручной запуск через `n8n` production webhook:

```bash
curl -X POST 'https://www.n-8-n.site/webhook/email-followup-live/run' \
  -H 'Content-Type: application/json' \
  -d '{
    "dry_run": true,
    "limit_sheets": 3,
    "max_records": -1
  }'
```

SMTP smoke-test:

```bash
cd /home/max/n8n_ai_call_center
python3 scripts/email_followup_service.py send-test --to-email your_test_email@example.com
```

Ручная обработка bounce-писем:

```bash
cd /home/max/n8n_ai_call_center
python3 scripts/email_followup_service.py process-bounces --limit-sheets 25 --limit-messages 20
```

## Что ещё нужно руками

- заполнить `.env.email_followup`;
- дать рабочие Google OAuth credentials;
- задать SMTP credentials;
- задать IMAP credentials для обработки bounce;
- для Telegram-отчета указать bot token и `chat_id` либо переиспользовать существующего бота и передать его токен в env;
- убедиться, что у сервера есть исходящий доступ к `https://api.telegram.org`;
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
- `EMAIL_FOLLOWUP_IMAP_HOST`
- `EMAIL_FOLLOWUP_IMAP_PORT`
- `EMAIL_FOLLOWUP_IMAP_USERNAME`
- `EMAIL_FOLLOWUP_IMAP_PASSWORD`
- `EMAIL_FOLLOWUP_BOUNCE_STATE_PATH`
- `EMAIL_FOLLOWUP_DOMAIN_BLACKLIST_PATH`
- `EMAIL_FOLLOWUP_SPREADSHEET_IDS`
- `EMAIL_FOLLOWUP_ATTACHMENT_PATH`
- `EMAIL_FOLLOWUP_ATTACHMENT_NAME`
- `EMAIL_FOLLOWUP_TELEGRAM_REPORTS_ENABLED`
- `EMAIL_FOLLOWUP_TELEGRAM_BOT_TOKEN`
- `EMAIL_FOLLOWUP_TELEGRAM_API_BASE`
- `EMAIL_FOLLOWUP_TELEGRAM_CHAT_ID`
- `EMAIL_FOLLOWUP_TELEGRAM_THREAD_ID`
- `EMAIL_FOLLOWUP_USE_JINA_SEARCH_FALLBACK`
- `EMAIL_FOLLOWUP_INFER_EMAIL_FROM_DOMAIN`

В Markdown и handoff-документах хранить только путь и имена переменных, без самого пароля.
