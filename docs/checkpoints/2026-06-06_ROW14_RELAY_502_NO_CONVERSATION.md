# 2026-06-06: `row_14` тоже не дошёл до разговора, снова relay `502`

## Сделано
- После жёсткого правила по `абонент / абоненту / абонентам` выполнен следующий одиночный цикл.
- Следующий callable номер по порядку:
  - `row_14`
  - `+79963649952`
  - `Mila Fon`
- Перед тестом были подняты только:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
- Для всех трёх workflow подтверждено:
  - `active = true`
  - `activeVersionId = versionId`
- `n8n` был перезапущен, webhook-и поднялись штатно.
- Отправлен один manual `POST /webhook/eleven/outbound-call`:
  - `request_id = manual.2026-06-06.ROW14.after_abonent_rule`
- Внешний webhook ответил:
  - `HTTP 200`
  - `content-type: application/json`
  - body пустой
- Дальше сняты live-логи:
  - в Eleven не появился ни один conversation с:
    - `user_id = row_14`
    - или `request_id = manual.2026-06-06.ROW14.after_abonent_rule`
  - relay-host `151.241.228.232` записал:
    - `Relaying to https://api.elevenlabs.io/v1/convai/sip-trunk/outbound-call (546 bytes)`
    - затем:
      - `POST /eleven/outbound-call HTTP/1.1 502`
- Значит это снова был не speech-case, а технический upstream failure до создания разговора.
- После цикла минимальные workflow снова выключены:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `false`
  - у всех трёх `activeVersionId = null`
- `n8n-server-n8n-1` после остановки снова `healthy`.

## На чем остановились
- Новый `абонент`-hard-rule этим циклом не проверился, потому что разговора вообще не было.
- Уже второй подряд одиночный цикл (`row_13`, `row_14`) ломается на одном и том же слое:
  - relay / outbound-call upstream `502`
- Это уже похоже не на случайный номер, а на повторяемую техническую проблему relay/provider path.

## Что делать дальше
1. Не делать выводов о речи агента по `row_14`.
2. Следующий шаг уже не новый prompt-patch.
3. Перед следующим звонком отдельно проверить и стабилизировать outbound relay path:
   - почему relay отдаёт `502` без создания conversation;
   - нужно ли поднимать timeout ещё на маленький шаг;
   - не изменился ли upstream response format или SIP acceptance path.
4. Только после этого снова делать следующий одиночный звонок по очереди.
