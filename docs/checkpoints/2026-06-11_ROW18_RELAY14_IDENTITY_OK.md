# 2026-06-11: `row_18` подтвердил `RELAY_TIMEOUT=14` и корректный identity trace

## Сделано
- После перехода relay на `14s` и включения enriched logging выполнен новый одиночный test call.
- Для цикла поднимались только:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
- Manual webhook отправлен на:
  - `row_18`
  - `+71660761251`
  - `request_id = manual.2026-06-11.ROW18.relay14.identitycheck`
- Relay log подтвердил identity до upstream:
  - `to_number = +71660761251`
  - `user_id = row_18`
  - `lead_id = row_18`
  - `source_record_key = row_18`
  - `request_id = manual.2026-06-11.ROW18.relay14.identitycheck`
- Relay уже не умер по timeout:
  - upstream вернул `HTTP 200`
  - через `11575 ms`
  - с body:
    - `success = false`
    - `message = unexpected status from INVITE response: sip status: 403: Forbidden (SIP 403)`
    - `conversation_id = conv_4001ktvcbehvedcvt5jfsq6b4d0b`
- Detail по `conv_4001ktvcbehvedcvt5jfsq6b4d0b` совпал с тем, что ушло из relay:
  - `user_id = row_18`
  - `external_number = +71660761251`
  - `request_id = manual.2026-06-11.ROW18.relay14.identitycheck`
- После цикла минимальные workflow снова выключены.

## На чем остановились
- `RELAY_TIMEOUT=14` выглядит как рабочее значение: relay дождался upstream JSON-ответа.
- Identity trace на новом цикле совпал end-to-end.
- Текущий блокер этого конкретного номера — не relay, а provider-side `SIP 403 Forbidden`.

## Что делать дальше
1. Оставить `RELAY_TIMEOUT=14` как текущее live значение.
2. Не трогать relay дальше без необходимости.
3. Следующий одиночный тест делать уже по следующему пригодному номеру, чтобы проверить обычный accepted/failed path без странного номера `row_18`.
4. Если identity trace и дальше будет совпадать, считать старое расхождение `row_17 -> row_14` разовым кейсом.
