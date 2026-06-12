# 2026-06-11: relay `14s` и трассировка identity после `row_17`

## Сделано
- Live relay-host `151.241.228.232` переведён с:
  - `RELAY_TIMEOUT=12`
  на:
  - `RELAY_TIMEOUT=14`
- Backup env:
  - `/root/.eleven_outbound_relay.env.bak-2026-06-11_14-58-10`
- `eleven-outbound-relay.service` успешно перезапущен.
- Локальный source-of-truth тоже синхронизирован:
  - `scripts/eleven_outbound_relay_server.py`
  - default timeout теперь `14`
- В relay добавлено enriched logging перед отправкой upstream:
  - `to_number`
  - `user_id`
  - `lead_id`
  - `source_record_key`
  - `request_id`
- Runtime-файл на сервере обновлён:
  - `/opt/eleven_outbound_relay.py`
- Дополнительно проверено сравнение payload size:
  - `row_14` payload = `546 bytes`
  - `row_17` payload = `574 bytes`
  - последний relay log из одиночного цикла был `574 bytes`

## На чем остановились
- Это уже подтверждает, что relay действительно отправил `row_17`, а не старый `row_14`.
- Значит identity mismatch локализован уже после relay.
- Новый звонок после `RELAY_TIMEOUT=14` и после включения enriched logging ещё не выполнялся.

## Что делать дальше
1. Поднять только:
   - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
   - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
   - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
2. Сделать один новый одиночный test call.
3. Сразу снять:
   - relay journal с новым identity summary;
   - webhook response;
   - detail по новому `conversation_id`.
4. Сравнить:
   - что реально ушло из relay;
   - что реально появилось в Eleven detail.
