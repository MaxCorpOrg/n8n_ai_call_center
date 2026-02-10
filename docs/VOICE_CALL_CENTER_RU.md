# Голосовой call center на n8n для звонков по РФ

Документ даёт рабочий минимальный контур:
- исходящий звонок на российский номер через API/SIP-провайдера;
- приём webhook-событий звонка;
- запись результатов в PostgreSQL.

## 1) Что уже добавлено в репозиторий
- `docker-compose.callcenter.yml` — Postgres как отдельный сервис.
- `.env.callcenter.example` — переменные окружения для телефонии и БД.
- `sql/001_call_center.sql` — таблицы `call_tasks` и `call_events`.

## 2) Запуск стека
```bash
cd ~/n8n-server
cp .env.callcenter.example .env.callcenter
# Заполните реальные значения переменных в .env.callcenter

docker compose \
  --env-file .env.callcenter \
  -f docker-compose.https.yml \
  -f docker-compose.callcenter.yml \
  up -d
```

Проверка:
```bash
docker compose --env-file .env.callcenter -f docker-compose.https.yml -f docker-compose.callcenter.yml ps
```

## 3) База данных
Postgres поднимется автоматически и применит `sql/001_call_center.sql`.

Таблицы:
- `call_tasks` — задания на звонки.
- `call_events` — события и результаты звонков (включая `recording_url`, `transcript`, `summary`).

## 4) Настройка n8n (2 workflow)

### Workflow A: `CC | Start Call`
Назначение: принять задачу на звонок и отправить вызов провайдеру.

Ноды:
1. `Webhook` (`POST /cc/start-call`, `Response mode: response node`).
2. `Code` (валидация и нормализация номера в формат `+7XXXXXXXXXX`).
3. `Postgres` (insert в `call_tasks`, статус `queued`).
4. `HTTP Request` (вызов API провайдера: создать звонок).
5. `Postgres` (update `status='dialing'`, сохранить `provider_call_id`).
6. `Respond to Webhook` (код 202, тело `{"ok": true}`).

Пример кода для ноды `Code`:
```javascript
const body = $json.body ?? $json;
const raw = String(body.phone || '').replace(/\D/g, '');
let phone = raw;
if (raw.startsWith('8') && raw.length === 11) phone = '7' + raw.slice(1);
if (raw.length === 10) phone = '7' + raw;
if (!/^7\d{10}$/.test(phone)) {
  throw new Error('phone must be RU number in format +7XXXXXXXXXX or 8XXXXXXXXXX');
}
return [{
  external_id: body.external_id || null,
  lead_id: body.lead_id || null,
  contact_name: body.contact_name || null,
  phone_e164: `+${phone}`,
  script_version: body.script_version || 'v1',
  consent_source: body.consent_source || null
}];
```

Пример SQL вставки:
```sql
INSERT INTO call_tasks (external_id, lead_id, contact_name, phone_e164, script_version, consent_source, status)
VALUES ($1, $2, $3, $4, $5, $6, 'queued')
RETURNING id;
```

### Workflow B: `CC | Call Events`
Назначение: принять callback/webhook от телефонии и зафиксировать результат.

Ноды:
1. `Webhook` (`POST /cc/events`, `Response mode: response node`).
2. `IF` (проверка секрета: header/query `token == {{$env.CALL_EVENT_TOKEN}}`).
3. `Postgres` (insert в `call_events`, `raw_payload` = весь JSON).
4. `Postgres` (update `call_tasks.status` по типу события: `completed`, `failed`, `busy`, `no_answer`).
5. `Respond to Webhook` (`{"ok": true}`).

Рекомендация: сохраняйте `provider_call_id` и используйте его как ключ связывания между `call_tasks` и `call_events`.

## 5) Что передавать в API провайдера
У каждого провайдера поля разные, но минимум обычно такой:
- `from`: исходящий номер (ваш номер у провайдера);
- `to`: номер клиента `+7...`;
- `callback_url`: `https://<ваш_домен>/webhook/cc/events`;
- `callback_token` или подпись.

## 6) Юридический минимум для РФ
- Фиксируйте источник согласия (`consent_source`) до автодозвона.
- Храните факт/время согласия и возможность отзыва.
- Для ПДн в БД применяйте минимизацию и ограничение доступа.

## 7) Полезные источники (официальные)
- n8n Webhook node: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/
- n8n HTTP Request node: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/
- n8n Postgres node: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.postgres/
- MANGO OFFICE API: https://www.mango-office.ru/support/api/
- Zadarma API v1: https://zadarma.com/support/api/
- ФЗ-38 (реклама), ст.18: https://www.consultant.ru/document/cons_doc_LAW_58968/
- ФЗ-152 (персональные данные): https://www.consultant.ru/document/cons_doc_LAW_61801/

## 8) Минимальный входящий payload для старта звонка
```json
{
  "external_id": "crm-100045",
  "lead_id": "lead-204",
  "contact_name": "Иван Петров",
  "phone": "+7 (999) 123-45-67",
  "script_version": "v1",
  "consent_source": "checkbox:landing:2026-02-08T10:45:00Z"
}
```
