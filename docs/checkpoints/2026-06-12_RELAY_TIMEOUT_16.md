# 2026-06-12: relay timeout поднят до `16` секунд

## Сделано
- По отдельной пользовательской команде live relay переведён на:
  - `RELAY_TIMEOUT=16`
- Предыдущее значение было:
  - `RELAY_TIMEOUT=14`
- Backup env:
  - `/root/.eleven_outbound_relay.env.bak-2026-06-12_09-47-52`
- Сохранены без изменений:
  - `RELAY_RETRY_COUNT=0`
  - `RELAY_RETRY_DELAY_MS=500`
- `eleven-outbound-relay.service` успешно перезапущен.
- Проверка `http://151.241.228.232:8787/health` прошла штатно.
- Локальный source-of-truth синхронизирован:
  - `scripts/eleven_outbound_relay_server.py`

## На чем остановились
- Это только инфраструктурный шаг.
- Новый одиночный звонок после перехода на `16s` ещё не запускался.
- Поэтому пока мы не знаем, спасёт ли это длинные upstream-case вроде `row_17`.

## Что делать дальше
1. Поднять только:
   - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
   - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
   - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
2. Сделать один новый одиночный test call.
3. Сразу снять:
   - relay journal;
   - webhook response;
   - свежий detail из Eleven Conversations API.
