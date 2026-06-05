# Контрольная точка: одиночный тест по `row_4` после schema-fix

Дата: `2026-06-05`

## Сделано

- После запрета повторять один и тот же номер следующий manual-call выполнен по:
  - `row_4`
  - `+79252149935`
  - `Алиса Широкова`
  - `request_id = manual.2026-06-05.143212.row_4.schemafix`
- Временно были подняты только:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
- Артефакты:
  - [request_payload.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_4_schema_fix_live/request_payload.json)
  - [outbound_headers.txt](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_4_schema_fix_live/outbound_headers.txt)
  - [outbound_body.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_4_schema_fix_live/outbound_body.json)
  - [conv_0601ktbrw785f03rvv0tket817tx.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_4_schema_fix_live/conv_0601ktbrw785f03rvv0tket817tx.json)
  - [live_sheet_report.txt](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_4_schema_fix_live/live_sheet_report.txt)
- Что произошло:
  - `POST /webhook/eleven/outbound-call` снова вернул `HTTP 200` с пустым body;
  - разговор реально был создан:
    - `conv_0601ktbrw785f03rvv0tket817tx`
    - `version_id = agtvrsn_6501ktbptasbfm2btq7dfq1mc16y`
  - transcript:
    - user: `Хорошо.`
    - agent: `Вам это в принципе интересно?`
    - user: `Такие вот истории, блин, зачем их найти?`
    - agent начинает product-pitch
    - после этого звонок завершается клиентом
- Итог:
  - `call_log` не был вызван;
  - новая строка в live Sheet не появилась;
  - schema-fix `phone_primary/source_record_key/eleven_conv_id` этим тестом не проверился.

## На чем остановились

- Все временно поднятые workflow снова выключены:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `inactive`
- Остальной контур тоже на паузе:
  - `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2` = `inactive`
  - `VOICE_INBOUND_AGENT (draft)` = `inactive`
  - `ELEVEN_TOOL_SEND_SMS_BRIDGE (draft)` = `inactive`
- `n8n-server-n8n-1` healthy.

## Что делать дальше

1. Следующий одиночный тест брать уже по `row_5`.
2. До этого решить, что важнее:
   - ловить voicemail/screening для проверки `call_log`;
   - или сначала смягчать слишком ранний follow-up после короткого ответа `Хорошо.`.
3. Новый цикл без команды пользователя не запускать.
