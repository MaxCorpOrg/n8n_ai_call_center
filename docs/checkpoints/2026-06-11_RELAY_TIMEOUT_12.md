# 2026-06-11: relay timeout поднят до `12` секунд

## Сделано
- Перепроверен live relay-host outbound-звонков:
  - `151.241.228.232`
  - сервис: `eleven-outbound-relay.service`
- Подтверждено по journal, что последние июньские `502` были timeout-кейсами:
  - `row_13` -> `Upstream failed (10031ms): The read operation timed out`
  - `row_14` -> `Upstream failed (10025ms): The read operation timed out`
- Значит повторяемый blocker был не в prompt и не в `call_log`, а в слишком узком окне ожидания relay.
- На live relay сделан минимальный safe fix:
  - backup env: `/root/.eleven_outbound_relay.env.bak-2026-06-11_14-38-48`
  - `RELAY_TIMEOUT: 10 -> 12`
  - `RELAY_RETRY_COUNT=0`
  - `RELAY_RETRY_DELAY_MS=500`
- `eleven-outbound-relay.service` перезапущен успешно.
- Проверка с prod-сервера прошла:
  - `curl http://151.241.228.232:8787/health`
  - ответ: `{"ok": true, "service": "eleven_outbound_relay", ...}`
- Локальный source-of-truth синхронизирован:
  - `scripts/eleven_outbound_relay_server.py`
  - default `RELAY_TIMEOUT` теперь `12`

## На чем остановились
- Relay уже не работает на заведомо тесном `10s` окне.
- Но фактического нового outbound-call после этого изменения ещё не было.
- Поэтому пока нельзя честно сказать, что live dialing восстановлен полностью.

## Что делать дальше
1. Поднять только минимальные workflow:
   - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
   - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
   - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
2. Сделать один одиночный test call по следующему номеру по порядку.
3. Сразу после него снять:
   - webhook response;
   - relay journal;
   - факт создания conversation в Eleven.
4. Если разговор создастся, отдельно проверить:
   - нет ли снова spoken-message на автоответчик;
   - доехал ли нормальный `eleven_conv_id`;
   - доехали ли `lead_id` и `source_record_key` в `call_log`.
