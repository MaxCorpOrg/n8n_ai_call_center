# 02. Маршрутизация: Mango, Asterisk, n8n

## 1) Mango

### SIP trunk
- Адрес trunk: публичный IP VPS и порт `5060`.
- Кодек: `G.711A`.
- DTMF: `RFC2833`.
- Транспорт: тот, который используется в Asterisk-конфиге (обычно UDP для Mango-сегмента).

### API callbacks
- `https://www.n-8-n.site/webhook/mango/events/call`
- `https://www.n-8-n.site/webhook/mango/events/summary`
- `https://www.n-8-n.site/webhook/mango/events/recording`

### Что важно
- В схемах переадресации не смешивать SIP сотрудника и trunk-маршрут в одном эксперименте.
- Для диагностики всегда фиксировать: номер A, номер B, время вызова.

## 2) Asterisk (VPS bridge)

Рабочие блоки находятся в `sip-bridge/asterisk`:
- `templates/pjsip.conf.template`
- `templates/extensions.conf.template`
- `bootstrap_ubuntu.sh`

### Логика dialplan
- `from-mango`: принимает вызов от Mango и отправляет в Eleven endpoint.
- `from-eleven`: принимает вызов от Eleven и отправляет в Mango endpoint.

### Базовая проверка
```bash
asterisk -rx "pjsip show endpoints"
asterisk -rx "dialplan show from-mango"
asterisk -rx "dialplan show from-eleven"
```

## 3) n8n workflow `VOICE_INBOUND_AGENT (draft)`

### Ключевые ноды Mango
- `Mango | Verify Call`
- `Mango | Verify Call SHA256`
- `Mango | Verify Call Final`
- `Mango | Route Decision`
- `Mango | Build Route Command`
- `Mango | Route HTTP`

### Ключевые ноды Eleven
- `Eleven | Webhook Outbound Call`
- `Eleven | Validate Request`
- `Eleven | Outbound HTTP`
- `Eleven | Build Success Response`

## 4) Защитные правила маршрутизации

`route` отправляется только если:
1. Подпись Mango валидна.
2. Событие входящее (по типу/направлению/структуре события).
3. `call_state=Appeared`.
4. Нет `command_id` во входящем событии (защита от loop).

Во всех других случаях ответ: `action=skipped`.

## 5) Контрольные API-тесты

### Mango call event
```bash
curl -X POST 'https://www.n-8-n.site/webhook/mango/events/call' \
  --data-urlencode 'vpbx_api_key=***' \
  --data-urlencode 'sign=***' \
  --data-urlencode 'json={...}'
```

Ожидание:
- inbound Appeared -> `route_sent`
- outbound/internal -> `skipped`

### Eleven outbound
```bash
curl -X POST 'https://www.n-8-n.site/webhook/eleven/outbound-call' \
  --data-urlencode 'to_number=+79991234567'
```

Ожидание:
- `call_requested`

