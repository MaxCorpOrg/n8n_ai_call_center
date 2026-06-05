# Контрольная точка: один тест после `call_log` schema-fix

Дата: `2026-06-05`

## Сделано

- После live patch `Main` с version `agtvrsn_6501ktbptasbfm2btq7dfq1mc16y` был поднят только минимальный набор workflow:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
- Сделан один manual-call по:
  - `row_3`
  - `+79657700655`
  - `Александр`
  - `request_id = manual.2026-06-05.141131.row_3.schemafix`
- Артефакты:
  - [request_payload.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_schema_fix_live/request_payload.json)
  - [outbound_headers.txt](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_schema_fix_live/outbound_headers.txt)
  - [outbound_body.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_schema_fix_live/outbound_body.json)
  - [eleven_recent_conversations.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_schema_fix_live/eleven_recent_conversations.json)
  - [conv_7901ktbqpbewfksb5d807a721v3v.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_schema_fix_live/conv_7901ktbqpbewfksb5d807a721v3v.json)
  - [live_sheet_report.txt](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_schema_fix_live/live_sheet_report.txt)
- Что произошло:
  - webhook `POST /webhook/eleven/outbound-call` снова ответил `HTTP 200` с пустым body;
  - реальный разговор всё равно был создан:
    - `conv_7901ktbqpbewfksb5d807a721v3v`
  - conversation уже шёл на новой live version:
    - `agtvrsn_6501ktbptasbfm2btq7dfq1mc16y`
- Но тест не дошёл до нужной ветки:
  - transcript содержит только:
    - `Трехэтажный дом.`
  - termination:
    - `Client disconnected: 1000`
  - agent не вызвал:
    - `call_log`
    - `end_call`
- Поэтому этот тест:
  - не подтвердил,
  - и не опроверг
  корректность новой `call_log` schema.

## На чем остановились

- Все временно поднятые workflow снова выключены:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `inactive`
- Остальной звонковый контур тоже на паузе:
  - `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2` = `inactive`
  - `VOICE_INBOUND_AGENT (draft)` = `inactive`
  - `ELEVEN_TOOL_SEND_SMS_BRIDGE (draft)` = `inactive`
- `n8n-server-n8n-1` healthy.
- Live Sheet report за `2026-06-05` после этого теста новых строк от этого разговора не показал.

## Что делать дальше

1. Не включать весь контур автоматически.
2. Сделать ещё один одиночный тест.
3. Но выбирать сценарий, где выше шанс дойти до `call_log`:
   - voicemail
   - screening
   - machine / no_answer
4. Если на следующем тесте `call_log` будет вызван, проверить:
   - есть ли `phone_primary`;
   - есть ли `source_record_key`;
   - пришёл ли `eleven_conv_id` как `conv_*`.
