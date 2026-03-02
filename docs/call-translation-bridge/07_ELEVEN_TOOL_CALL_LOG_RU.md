# Eleven Tool `call_log` -> Google Sheet (RU)

Документ фиксирует рабочий мост записи итогов звонка из ElevenLabs в Google Sheet через n8n.

## 1) Что развернуто

- Workflow в n8n: `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
- Workflow ID: `kZSdJrsAHWWIC2l6`
- Endpoint:
  - `POST https://www.n-8-n.site/webhook/eleven/tool/call-log`
- Целевая таблица:
  - `https://docs.google.com/spreadsheets/d/1E-VCKAv4vF_SFLY8DgW0UC80FvAC_DDIxbSbi8GC8kU/edit`
  - Лист: `Лиды_обзвон`

## 2) Контракт запроса

Минимальный payload (остальные поля опциональны):

```json
{
  "lead_id": "lead_001",
  "caller": "+79050000001",
  "call_result": "callback_scheduled",
  "next_step": "callback",
  "next_call_at": "2026-02-27T10:30:00+03:00",
  "notes_short": "Клиент просит перезвонить после 10:30"
}
```

Дополнительно поддерживаются: `client_ref`, `company_name`, `contact_name`, `interest_level`, `objection_text`, `manager_owner`, `call_record_url`, `eleven_conv_id`, `agent_version` и др.

## 3) Ответ webhook

Успех:

```json
{
  "ok": true,
  "tool": "call_log",
  "source": "google_sheets",
  "updated_range": "'Лиды_обзвон'!A502:AM502",
  "updated_rows": 1
}
```

Если ошибка OAuth/Sheets, `ok=false` и в `warning` возвращается причина.

## 4) Проверка вручную

```bash
curl -X POST 'https://www.n-8-n.site/webhook/eleven/tool/call-log' \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id":"sess_test_manual",
    "client_ref":"lead_demo_001",
    "caller":"+79050000001",
    "contact_name":"Тест Клиент",
    "company_name":"Тест Компания",
    "call_result":"callback_scheduled",
    "next_step":"callback",
    "next_call_at":"2026-02-27T10:30:00+03:00",
    "interest_level":"B",
    "notes_short":"Нужен повторный контакт",
    "agent_version":"AI_CALL_AGENT_1",
    "last_updated_by":"eleven_agent"
  }'
```

## 5) Подключение в ElevenLabs

1. `Tools` -> `Add webhook tool`.
2. Name: `call_log`.
3. Method: `POST`.
4. URL: `https://www.n-8-n.site/webhook/eleven/tool/call-log`.
5. В body schema добавить поля, которые агент должен передавать:
   - `lead_id`, `caller`, `call_result`, `next_step`, `next_call_at`, `notes_short`
   - опционально: `company_name`, `contact_name`, `interest_level`, `objection_text`, `manager_owner`, `call_record_url`, `eleven_conv_id`, `agent_version`
6. Привязать tool к агенту (`AI_CALL_AGENT_1`).

## 6) Важно по безопасности

- В репозитории экспорт workflow хранится в шаблонном виде с плейсхолдерами:
  - `{{GOOGLE_CLIENT_ID}}`
  - `{{GOOGLE_CLIENT_SECRET}}`
  - `{{GOOGLE_REFRESH_TOKEN}}`
- В живом n8n workflow значения уже установлены и протестированы.
