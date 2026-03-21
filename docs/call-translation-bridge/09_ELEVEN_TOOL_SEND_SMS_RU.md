# Eleven Tool `send_sms_info` -> Mango SMS via n8n (RU)

Документ фиксирует рабочую схему отправки SMS из ElevenLabs в Mango через `n8n`.

## 1) Что работает сейчас

- Workflow в репозитории:
  - `/home/max/n8n_ai_call_center/workflows/ELEVEN_TOOL_SEND_SMS_BRIDGE_DRAFT.json`
- Webhook path:
  - `POST /webhook/eleven/tool/send-sms`
- Назначение:
  - ElevenLabs-агент вызывает `send_sms_info`;
  - `n8n` валидирует payload, собирает SMS и отправляет её через Mango direct API `vpbx/commands/sms`;
  - если клиент сказал `на этот номер`, номер берётся из `system__called_number`, а не собирается из речи.

## 2) Переменные окружения

Добавьте в окружение `n8n`:

- `MANGO_VPBX_API_KEY`
  - API key виртуальной АТС Mango
- `MANGO_VPBX_API_SALT`
  - salt для подписи запросов
- `MANGO_VPBX_FROM_EXTENSION`
  - внутренний номер/extension отправителя, например `1`
- `MANGO_SMS_SENDER`
  - необязательный sender name, если используется в Mango
- `MANGO_SMS_TIMEOUT_MS`
  - по умолчанию `15000`
- `MANGO_SMS_MAX_LENGTH`
  - по умолчанию `480`

В live Mango принимает `POST https://app.mango-office.ru/vpbx/commands/sms` с полями `vpbx_api_key`, `sign`, `json`.

## 3) Контракт запроса от ElevenLabs

Минимальный payload:

```json
{
  "message_intent": "short_info"
}
```

Рекомендуемый payload:

```json
{
  "request_id": "sms_req_001",
  "conversation_id": "conv_123",
  "current_call_number": "+79251130826",
  "client_name": "Максим",
  "product": "LipoLong",
  "message_intent": "short_info"
}
```

Поддерживаются поля:

- `message_intent`
- `phone_target`
- `current_call_number`
- `request_id`
- `conversation_id`
- `lead_id`
- `client_name`
- `contact_name`
- `company_name`
- `product`
- `sms_text`
- `material_url`
- `reply_phone`
- `manager_phone`
- `callback_at`
- `next_call_at`

Правило выбора номера:

1. если передан валидный `phone_target`, используется он;
2. если `phone_target` пустой или битый, используется `current_call_number`;
3. если клиент просит отправить на другой номер, агент обязан переспросить, повторить номер и только потом передавать его в `phone_target`.

## 4) Как формируется SMS

Логика workflow:

- если передан `sms_text`, используется он;
- если `sms_text` не передан, `n8n` собирает шаблон по `message_intent`;
- для `short_info` используется рабочий контактный блок;
- номер нормализуется в формат `+7...`, если это российский номер;
- текст ограничивается длиной `MANGO_SMS_MAX_LENGTH`.

Текущий рабочий SMS-блок:

```text
Отправляю контакты и условия для сотрудничества:
Телефон: 8 999 556-67-77
Telegram: @Vorgesar_Peptides
Messenger Max: @Vorgesar_Peptides
Сайт: lipolong.com
Чаты Telegram: @MadCoreChat / @Peptides_shop / @vl26g_official / @Zhirotop_Shop
Условия оплаты: безналичный расчёт +6%
Реквизиты: ИП Клочков Сергей Александрович, ИНН 645308371993
```

Поддержанные `message_intent`:

- `short_info`
- `callback_confirmation`
- `offer`

## 5) Ответ webhook

Успех:

```json
{
  "ok": true,
  "tool": "send_sms_info",
  "status": "sent",
  "provider": "mango_sms",
  "phone_target": "+79251130826",
  "sms_length": 335,
  "message_intent": "short_info"
}
```

Успех с fallback на номер текущего звонка:

```json
{
  "ok": true,
  "tool": "send_sms_info",
  "status": "sent",
  "phone_target": "+79251130826",
  "warning": "phone_target not provided explicitly, used current_call_number fallback"
}
```

Ошибка валидации:

```json
{
  "ok": false,
  "tool": "send_sms_info",
  "status": "invalid_request",
  "warning": "phone_target is empty or invalid"
}
```

## 6) Ручной тест

Тест `на этот номер`:

```bash
curl -X POST 'https://<YOUR_N8N_DOMAIN>/webhook/eleven/tool/send-sms' \
  -H 'Content-Type: application/json' \
  -d '{
    "request_id":"sms_req_same_number_001",
    "conversation_id":"conv_manual_001",
    "current_call_number":"+79251130826",
    "client_name":"Тест Клиент",
    "product":"LipoLong",
    "message_intent":"short_info"
  }'
```

Тест `на другой номер`:

```bash
curl -X POST 'https://<YOUR_N8N_DOMAIN>/webhook/eleven/tool/send-sms' \
  -H 'Content-Type: application/json' \
  -d '{
    "request_id":"sms_req_other_number_001",
    "conversation_id":"conv_manual_002",
    "current_call_number":"+79251130826",
    "phone_target":"+79050000001",
    "client_name":"Тест Клиент",
    "product":"LipoLong",
    "message_intent":"short_info"
  }'
```

## 7) Подключение в ElevenLabs

1. `Tools` -> `Add webhook tool`.
2. Name: `send_sms_info`.
3. Method: `POST`.
4. URL: `https://<YOUR_N8N_DOMAIN>/webhook/eleven/tool/send-sms`.
5. В body schema обязательным оставить только:
   - `message_intent`
6. Рекомендуется также добавить:
   - `current_call_number`
   - `phone_target`
   - `request_id`
   - `conversation_id`
   - `lead_id`
   - `client_name`
   - `company_name`
   - `product`
   - `material_url`
   - `reply_phone`
   - `callback_at`
   - `sms_text`
7. После привязки проверить, что старые live-tools (`context_fetch`, `call_log`, `end_call`) не пропали.

### Готовый body schema для ElevenLabs

```json
{
  "type": "object",
  "properties": {
    "request_id": {
      "type": "string",
      "description": "Уникальный id вызова tool для защиты от дублей"
    },
    "conversation_id": {
      "type": "string",
      "description": "ID разговора ElevenLabs"
    },
    "current_call_number": {
      "type": "string",
      "description": "Номер текущего звонка. Если клиент сказал На этот номер, используй именно его"
    },
    "lead_id": {
      "type": "string",
      "description": "ID лида или клиента"
    },
    "client_name": {
      "type": "string",
      "description": "Имя собеседника, если его удалось узнать"
    },
    "company_name": {
      "type": "string",
      "description": "Название компании или бренда"
    },
    "product": {
      "type": "string",
      "description": "Название продукта, например LipoLong"
    },
    "phone_target": {
      "type": "string",
      "description": "Номер для случая, когда клиент просит отправить SMS на другой номер"
    },
    "message_intent": {
      "type": "string",
      "enum": ["short_info", "offer", "callback_confirmation"],
      "description": "Тип SMS, который поможет n8n выбрать шаблон"
    },
    "material_url": {
      "type": "string",
      "description": "Ссылка на материалы или КП"
    },
    "reply_phone": {
      "type": "string",
      "description": "Номер для обратной связи"
    },
    "callback_at": {
      "type": "string",
      "description": "Когда удобно вернуться к разговору"
    },
    "sms_text": {
      "type": "string",
      "description": "Необязательный готовый текст SMS"
    }
  },
  "required": ["message_intent"]
}
```

## 8) Рекомендуемое правило для prompt

Агент должен вызывать `send_sms_info` только если:

- клиент явно попросил отправить SMS на телефон;
- если клиент сказал `на этот номер`, агент не просит диктовать номер и не собирает его из речи;
- если клиент сказал `на другой номер`, агент просит продиктовать номер, повторяет его и только после подтверждения вызывает tool;
- после вызова tool агент подтверждает отправку короткой фразой, без длинного чтения текста SMS.

### Готовый prompt-snippet для вставки в ElevenLabs

```text
Работа с SMS:
- Если клиент просит отправить информацию по SMS на этот номер, используй send_sms_info сразу с номером текущего звонка. Подтверждение номера нужно только если клиент просит отправить на другой номер.
- Если клиент говорит «на этот номер», никогда не проси диктовать или повторять номер и никогда не собирай его из речи. Сразу используй номер текущего звонка из system__called_number.
- Если клиент просит отправить на другой номер, только тогда попроси продиктовать номер, повтори его и после подтверждения вызывай send_sms_info.
- Для обычной отправки информации на телефон используй message_intent = short_info.
- После успешного send_sms_info коротко подтверди отправку, не читай клиенту полный текст SMS и верни разговор к согласованию follow-up.
```

## 9) Что уже было выявлено в live

- ошибка вида `phone_target: "+7"` приводит к `invalid_request`;
- ручная диктовка номера по голосу может дать ошибочный номер даже при живом разговоре;
- поэтому рабочее правило проекта: `на этот номер` -> только `system__called_number`;
- `call_log` должен принимать `preferred_channel = sms`.
