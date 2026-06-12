# 2026-06-11: одиночный цикл `row_17` после `RELAY_TIMEOUT=12`

## Сделано
- После live-правки `RELAY_TIMEOUT: 10 -> 12` выполнен один новый одиночный test call.
- Для цикла были подняты только:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` `sHTbALayEZdy8Mzs`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` `tdiAEZM9FZDEP7k4`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` `kZSdJrsAHWWIC2l6`
- Перед вызовом у всех трёх было подтверждено:
  - `active = true`
  - `activeVersionId = versionId`
- После рестарта `n8n-server-n8n-1` логи подтвердили реальную активацию этих workflow.
- Отправлен один manual webhook:
  - `lead_id = row_17`
  - `to_number = +79012091111`
  - `request_id = manual.2026-06-11.ROW17.relay12check`
- Внешний webhook ответил:
  - `HTTP 200`
  - body пустой
- Relay-host `151.241.228.232` записал:
  - `Relaying ... (574 bytes)`
  - `Upstream failed (12052ms): The read operation timed out`
  - `POST /eleven/outbound-call HTTP/1.1 502`
- Через Eleven Conversations API найден свежий failed conversation:
  - `conversation_id = conv_1901kteg8mpwe7har7hxep69cf56`
  - `status = failed`
  - `error.code = 1011`
  - `error.reason = sip request timed out`
  - `call_duration_secs = 0`
- После цикла все три workflow снова выключены:
  - `active = false`
  - `activeVersionId = null`

## На чем остановились
- Relay timeout `12s` всё ещё недостаточен.
- Но теперь видно, что upstream уже успевает создать failed conversation до того, как relay сдаётся по timeout.
- Дополнительно появился новый риск трассировки:
  - detail по `conv_1901kteg8mpwe7har7hxep69cf56` вернулся с:
    - `user_id = row_14`
    - `request_id = manual.2026-06-06.ROW14.after_abonent_rule`
  хотя этот тестовый webhook отправлялся как `row_17`.
- Значит нужно проверить не только timeout, но и соответствие входного payload фактической identity в Eleven.

## Что делать дальше
1. Не запускать следующий звонок подряд сразу.
2. Сначала сделать два точечных шага:
   - поднять relay timeout ещё на маленький шаг: `12 -> 14`;
   - проверить, откуда берётся identity-расхождение `row_17 -> row_14`.
3. Только потом запускать следующий одиночный тест.
