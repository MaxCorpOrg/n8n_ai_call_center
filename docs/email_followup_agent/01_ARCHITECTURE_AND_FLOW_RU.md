# Email Followup Agent: Архитектура и Поток

## Назначение

`EMAIL_FOLLOWUP_AGENT` — это отдельный production-контур для email-follow-up по лидам из обзвонных Google Sheets.

Контур отделён от голосового агента и не зависит от `ElevenLabs`. Его задача:

- находить лиды, которым по итогам разговора нужно отправить информацию;
- находить или перепроверять email;
- отправлять письмо с PDF-коммерческим предложением;
- разбирать bounce и убирать мусор из дальнейшей автоматизации;
- отправлять операционный отчёт в Telegram.

## Главные компоненты

### 1. Google Sheets / Google Drive

Агент читает таблицы обзвона:

- по префиксу `контакты_косметологов_москва_`, или
- по явному списку `EMAIL_FOLLOWUP_SPREADSHEET_IDS`.

Рабочий лист по умолчанию:

- `Лиды_обзвон`

### 2. Python-сервис

Основной сервис:

- `scripts/email_followup_service.py`

Он отвечает за:

- чтение таблиц;
- группировку строк в лид;
- поиск email;
- SMTP-отправку;
- IMAP bounce-обработку;
- Telegram-отчёты;
- HTTP endpoints `/health`, `/run`, `/send-test`, `/process-bounces`.

### 3. n8n workflows

Есть два workflow:

- scheduled: `EMAIL_FOLLOWUP_AGENT_LIVE`
- manual/webhook: `EMAIL_FOLLOWUP_AGENT_MANUAL_LIVE`

Они вызывают отдельный host-сервис, а не содержат бизнес-логику внутри себя.

### 4. SMTP

SMTP используется только для фактической отправки писем.

Письмо содержит:

- тему;
- текстовую и HTML-версию;
- ссылки на продукт;
- контакты менеджера;
- PDF-вложение с коммерческим предложением.

### 5. IMAP bounce watcher

IMAP нужен для чтения bounce-писем и последующей автоматической маркировки проблемных адресов:

- `domain_not_found`
- `mailbox_not_found`
- `mailbox_full`
- `policy_blocked`
- `temporary_failure`
- `delivery_failed`

### 6. Web resolver

Email ищется не только в строке таблицы, но и через web-resolver:

- поиск по номеру телефона;
- поиск по названию компании;
- переход с каталога на внешний сайт организации;
- вытягивание email со страницы сайта;
- верификация домена;
- фильтрация мусорных платформенных адресов.

### 7. Telegram reporting

После прогона агент может отправлять summary в Telegram:

- сколько таблиц пройдено;
- сколько лидов реально обработано;
- сколько ушло в `sent`;
- сколько осталось в `manual_review`;
- по каким таблицам есть новые записи, а по каким их нет.

## Поток обработки

1. `n8n` вызывает `/run`.
2. Сервис при live-прогоне сначала разбирает bounce через IMAP.
3. Сервис получает список целевых таблиц.
4. Для каждой таблицы читается лист `Лиды_обзвон`.
5. Строки группируются в лид:
   - `lead_id`
   - `source_record_key`
   - нормализованный `phone_primary`
   - fallback `row_<номер>`
6. По каждому лиду собирается merged context.
7. Агент решает, есть ли email-сигнал:
   - `preferred_channel=email`
   - `next_step=send_kp|send_email|email_followup`
   - `call_result=send_kp_pending_callback|manager_call`
   - упоминание `email / почта / на почту`
   - уже записанный email
8. Агент ищет email:
   - явные поля;
   - заметки;
   - исправление “битых” полей;
   - поиск по сайту/номеру/компании;
   - phone-history cache.
9. Агент верифицирует email и домен.
10. Если email найден и валиден, формируется письмо с вложением.
11. При live-прогоне письмо отправляется через SMTP.
12. Таблица обновляется техническими колонками.
13. По итогам строится per-sheet summary и при необходимости уходит в Telegram.

## Технические колонки, которые пишет агент

Агент дописывает и использует:

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

## Статусы email-агента

### Статусы отправки

- `sent`
- `manual_review`
- `bounced`
- `send_failed`

### Статусы верификации

- `from_sheet`
- `from_notes`
- `from_misplaced_field`
- `verified_from_website`
- `from_phone_history`
- `domain_not_found`
- `domain_check_failed`
- `not_found`
- `blacklisted_domain`

## Важный operational принцип

Email-контур работает отдельно от автодозвона и запускается в безопасные окна.

Это сделано специально, чтобы:

- не пересекаться с активным обзвоном;
- не мешать `AUTODIAL_DISPATCHER`;
- не писать конкурентно в одни и те же строки в разгар звонковой сессии.
