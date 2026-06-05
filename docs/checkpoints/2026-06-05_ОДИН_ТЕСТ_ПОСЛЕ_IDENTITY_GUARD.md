# Контрольная точка: один тест после identity guard

Дата: `2026-06-05`

## Сделано

- Для одного controlled test-cycle временно подняты только:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
- `AUTODIAL_DISPATCHER`, `VOICE_INBOUND_AGENT` и `ELEVEN_TOOL_SEND_SMS_BRIDGE` не включались.
- Сделан один manual-call по:
  - `row_3`
  - `+79657700655`
  - `Александр`
- Новый разговор:
  - `conv_0601ktbh7vvbf398yp0zbpw1me8d`
  - `status = done`
  - `summary = Voicemail Detected`
- Подтверждено, что voicemail больше не получает spoken-farewell:
  - `end_call` ушёл с пустым `system__message_to_speak`
  - фразы `Спасибо, перезвоним позже.` больше не было
- Одновременно подтверждено, что `call_log` всё ещё не даёт полный identity package:
  - tool-call ушёл с:
    - `lead_id = row_3`
    - `caller = +79657700655`
    - `phone_primary = +79657700655`
    - `source_record_key = row_3`
    - `eleven_conv_id = system__conversation_id`
  - но в Google Sheet строка `A40:AM40` записалась как:
    - `lead_id = row_3`
    - `source_record_key = 79657700655`
    - `phone_primary = 79657700655`
    - `eleven_conv_id = ''`
    - `notes_short = Голосовая почта, сообщение не оставлено.`
- После теста три временно поднятых workflow снова выключены.

## Артефакты

- каталог теста:
  - [single_call_2026-06-05_row_3_guard_check](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_guard_check)
- разговор:
  - [conv_0601ktbh7vvbf398yp0zbpw1me8d.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_guard_check/conv_0601ktbh7vvbf398yp0zbpw1me8d.json)
- список свежих разговоров:
  - [eleven_recent_conversations_after_test.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_guard_check/eleven_recent_conversations_after_test.json)
- outbound-ответ:
  - [outbound_headers.txt](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_guard_check/outbound_headers.txt)
  - [outbound_body.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_guard_check/outbound_body.json)
- request payload:
  - [request_payload.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-05_row_3_guard_check/request_payload.json)

## На чем остановились

- Весь звонковый контур снова на паузе:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `inactive`
  - `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2` = `inactive`
  - `VOICE_INBOUND_AGENT (draft)` = `inactive`
  - `ELEVEN_TOOL_SEND_SMS_BRIDGE (draft)` = `inactive`
- `n8n-server-n8n-1` healthy.
- Реальный статус после теста:
  1. voicemail without spoken-farewell = уже работает;
  2. `call_log` identity package = всё ещё не закрыт;
  3. вероятная зона бага = published/runtime-версия `ELEVEN_TOOL_CALL_LOG_BRIDGE` после re-activation.

## Что делать дальше

1. Не включать звонки автоматически.
2. Следующий шаг:
   - разбирать published/runtime-слой `ELEVEN_TOOL_CALL_LOG_BRIDGE`.
3. Перед следующим звонком нужно добиться, чтобы после re-activation bridge реально обслуживал patched version с identity guard.
4. Следующий тест делать снова одиночным и снова на voicemail-case.
5. Цель следующего теста:
   - `spoken-farewell` отсутствует;
   - `source_record_key = row_3`;
   - `eleven_conv_id = conv_*`.
