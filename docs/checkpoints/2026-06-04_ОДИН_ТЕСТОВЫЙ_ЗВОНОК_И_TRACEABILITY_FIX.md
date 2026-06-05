# Контрольная точка: один тестовый звонок и traceability fix

Дата: `2026-06-04`

## Сделано

- Выполнен один controlled manual cycle по новой таблице:
  - таблица: `Первая таблица частных косметологов`
  - лид: `row_3`
  - номер: `+79657700655`
  - имя/контакт: `Александр`
- Для этого временно включался только:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` (`sHTbALayEZdy8Mzs`)
- Первый запрос в `POST /webhook/eleven/outbound-call` ушёл в relay-timeout:
  - relay-host: `151.241.228.232`
  - лог relay:
    - `Upstream failed (10058ms): The read operation timed out`
- Но затем подтвердилось, что этот же первый запрос всё-таки привёл к реальному звонку:
  - `conversation_id = conv_3301kt8tj8vyftq97vwbc0jn7c96`
  - статус в Eleven: `done`
  - линия: голосовая почта
  - итог по смыслу:
    - `no_answer`
    - `callback`
    - сообщение не оставлялось
- Одновременно найден дефект:
  - строка `call_log` в Google Sheet ушла без `lead_id`, `source_record_key`, `eleven_conv_id`
  - то есть traceability по voicemail-case оказалась дырявой
- Второй запрос по тому же лиду дал уже чистый технический отказ:
  - `conversation_id = conv_7801kt8tnrkje75sydp92kfw06wj`
  - статус: `failed`
  - причина:
    - `max auth retry attempts reached for SIP invite`
- По итогам этого одного цикла live `Main` в ElevenLabs дополнительно пропатчен:
  - добавлен блок `Traceability and silent machine exit`
  - теперь в финальном `call_log` обязательны:
    - `lead_id`
    - `caller`
    - `phone_primary`
    - `source_record_key`
    - `company_name` / `contact_name` при наличии
    - `eleven_conv_id` как реальный conversation id
  - после voicemail/message-service нельзя говорить:
    - `Спасибо, перезвоним позже.`
    - любой другой spoken-farewell
  - нужное поведение:
    - `call_log`
    - затем silent `end_call`
- Новый live version id:
  - `agtvrsn_4901kt8tykm7fk8t5z9d1s6xe767`
- После цикла outbound-мост снова выключен.

## Артефакты

- backup outbound bridge до временного включения:
  - `/home/max/n8n_ai_call_center/backups/2026-06-04_single_call_cycle/ELEVEN_OUTBOUND_CALL_BRIDGE_before_publish.json`
- payload live patch:
  - `/home/max/n8n_ai_call_center/backups/2026-06-04_single_call_cycle/main_prompt_traceability_voicemail_patch_payload.json`
- backup агента до правки:
  - `/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-04_row_3/current_ai_call_agent_1.before.json`
- backup агента после правки:
  - `/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-04_row_3/current_ai_call_agent_1.after.json`
- headers/body HTTP-ответа outbound bridge:
  - `/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-04_row_3/outbound_headers_retry1.txt`
  - `/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-04_row_3/outbound_body_retry1.json`
- детали разговоров Eleven:
  - `/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-04_row_3/conv_3301kt8tj8vyftq97vwbc0jn7c96.json`
  - `/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-04_row_3/conv_7801kt8tnrkje75sydp92kfw06wj.json`
- сводка последних разговоров:
  - `/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-04_row_3/eleven_recent_conversations.json`

## На чем остановились

- После отдельной команды пользователя `ПОКА ОСТАНОВИ ВСЕ` весь звонковый контур остановлен:
  - `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2` = `inactive`
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `inactive`
  - `VOICE_INBOUND_AGENT (draft)` = `inactive`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `inactive`
  - `ELEVEN_TOOL_SEND_SMS_BRIDGE (draft)` = `inactive`
- Главные открытые проблемы:
  1. relay-timeout может скрыть уже начавшийся реальный звонок;
  2. SIP/outbound может отдельно падать в `max auth retry attempts reached for SIP invite`;
  3. нужно подтвердить, что после свежего prompt-patch traceability в `call_log` реально починилась.

## Что делать дальше

1. Ничего не включать автоматически.
2. Следующий шаг — только новый одиночный звонок по явной команде пользователя.
3. Перед следующим звонком поднять только минимум нужных workflow, а не весь контур.
4. На следующем звонке проверить ровно два пункта:
   - ушла ли spoken-фраза после voicemail/message-service;
   - доехали ли в `call_log` `lead_id / source_record_key / eleven_conv_id`.
5. Если снова придёт `max auth retry attempts reached for SIP invite`, дальше копать уже не prompt, а SIP/outbound-auth слой.
