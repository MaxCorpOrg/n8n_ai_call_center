# Контрольная точка: live `Main` усилен для `call_log`

Дата: `2026-06-05`

## Сделано

- Без включения звонков дополнительно пропатчен live `Main` у `AI_CALL_AGENT_1`.
- Перед правкой снят backup:
  - [current_ai_call_agent_1.before.json](/home/max/n8n_ai_call_center/backups/2026-06-05_eleven_call_log_schema_fix/current_ai_call_agent_1.before.json)
- После правки сохранены:
  - [main_call_log_schema_fix_payload.slim_v2.json](/home/max/n8n_ai_call_center/backups/2026-06-05_eleven_call_log_schema_fix/main_call_log_schema_fix_payload.slim_v2.json)
  - [patch_response_slim_v2.json](/home/max/n8n_ai_call_center/backups/2026-06-05_eleven_call_log_schema_fix/patch_response_slim_v2.json)
  - [current_ai_call_agent_1.after_patch.json](/home/max/n8n_ai_call_center/backups/2026-06-05_eleven_call_log_schema_fix/current_ai_call_agent_1.after_patch.json)
- Новая live version:
  - `agtvrsn_6501ktbptasbfm2btq7dfq1mc16y`
- Что изменено в live:
  - в prompt добавлено прямое правило:
    - `call_log` обязан включать `phone_primary` и `source_record_key`;
    - `eleven_conv_id` обязан быть реальным `conv_*`, а не literal `system__conversation_id`;
    - если в draft tool-call виден literal `system__conversation_id`, agent должен перегенерировать `call_log` перед завершением звонка.
  - в live tool-schema `call_log` добавлены отсутствовавшие свойства:
    - `phone_primary`
    - `source_record_key`
  - описание поля `eleven_conv_id` усилено:
    - использовать текущий реальный `conv_*` id этого звонка.
- Важное ограничение:
  - required-поля `call_log` не расширялись;
  - жёсткая dynamic-variable schema на stable live не включалась.

## На чем остановились

- Весь звонковый контур по-прежнему на паузе:
  - `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2` = `inactive`
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `inactive`
  - `VOICE_INBOUND_AGENT (draft)` = `inactive`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_SEND_SMS_BRIDGE (draft)` = `inactive`
- `n8n-server-n8n-1` healthy.
- Последний подтверждённый разговор до этой правки:
  - `conv_5001ktbjvcz2e43v32jrw4pdmscp`
  - silent voicemail exit уже работал;
  - `call_log` ещё не доносил правильный `eleven_conv_id`.
- После текущего patch новых звонков ещё не было.

## Что делать дальше

1. Не включать весь контур автоматически.
2. Поднять только минимальные workflow для одного manual-call теста.
3. Сделать один одиночный voicemail/screening test.
4. Проверить:
   - spoken-farewell по-прежнему отсутствует;
   - `phone_primary` и `source_record_key` реально дошли до webhook-body;
   - `eleven_conv_id` пришёл как `conv_*`, а не как literal `system__conversation_id`;
   - `call_log` записался в Sheet с полным identity package.
