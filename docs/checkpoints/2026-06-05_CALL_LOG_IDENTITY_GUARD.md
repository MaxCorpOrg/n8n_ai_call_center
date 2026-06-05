# Контрольная точка: identity guard для `call_log` на паузе

Дата: `2026-06-05`

## Сделано

- Не поднимая звонки, разобрали последнюю traceability-проблему по кейсу `conv_3301kt8tj8vyftq97vwbc0jn7c96`.
- Подтверждено:
  - в сам разговор уже приезжали правильные runtime-идентификаторы:
    - `lead_id = row_3`
    - `source_record_key = row_3`
    - `phone_primary = +79657700655`
    - `eleven_conv_id = conv_3301kt8tj8vyftq97vwbc0jn7c96`
  - но старый `call_log` всё равно принял пустой payload только с:
    - `call_result`
    - `next_step`
    - `notes_short`
- На паузе пропатчен `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` (`kZSdJrsAHWWIC2l6`):
  - добавлен `Tool | Validate Identity`;
  - добавлен `Tool | Identity Switch`;
  - bare `call_log` без identity-пакета теперь не должен записываться в Google Sheet;
  - вместо этого workflow возвращает:
    - `ok = false`
    - `warning = missing_identity_package`
    - список недостающих полей.
- Для `elevenlabs` теперь считаются обязательными:
  - `lead_id`
  - `caller`
  - `phone_primary`
  - `source_record_key`
  - `eleven_conv_id`
- Для `autodial_dispatcher` guard мягче:
  - `lead_id`
  - `phone_primary`
  - `source_record_key`
  - `eleven_conv_id` может быть пустым.
- Патч применён и в live, и в локальный файл:
  - [workflows/ELEVEN_TOOL_CALL_LOG_BRIDGE_DRAFT.json](/home/max/n8n_ai_call_center/workflows/ELEVEN_TOOL_CALL_LOG_BRIDGE_DRAFT.json)
- Backup-артефакты:
  - [ELEVEN_TOOL_CALL_LOG_BRIDGE.live_before.json](/home/max/n8n_ai_call_center/backups/2026-06-05_call_log_identity_guard/ELEVEN_TOOL_CALL_LOG_BRIDGE.live_before.json)
  - [ELEVEN_TOOL_CALL_LOG_BRIDGE.live_after.json](/home/max/n8n_ai_call_center/backups/2026-06-05_call_log_identity_guard/ELEVEN_TOOL_CALL_LOG_BRIDGE.live_after.json)
  - [ELEVEN_TOOL_CALL_LOG_BRIDGE.local_before.json](/home/max/n8n_ai_call_center/backups/2026-06-05_call_log_identity_guard/ELEVEN_TOOL_CALL_LOG_BRIDGE.local_before.json)

## На чем остановились

- Весь звонковый контур всё ещё на паузе:
  - `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2` = `inactive`
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `inactive`
  - `VOICE_INBOUND_AGENT (draft)` = `inactive`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_SEND_SMS_BRIDGE (draft)` = `inactive`
- `n8n-server-n8n-1` healthy.
- Сухая проверка пройдена:
  - bare agent payload режется;
  - валидный `autodial_dispatcher` payload проходит;
  - валидный agent payload с `row_* + conv_*` проходит.

## Что делать дальше

1. Ничего не включать автоматически.
2. Следующий шаг только по явной команде пользователя.
3. На следующем одиночном тесте проверить:
   - не вернулся ли spoken-farewell после voicemail;
   - пришёл ли `call_log` уже с полным identity-пакетом;
   - не вернул ли bridge `missing_identity_package`.
4. Если следующий звонок снова упирается в `missing_identity_package`, дальше править уже не bridge, а live-tool usage/schema в ElevenLabs.
