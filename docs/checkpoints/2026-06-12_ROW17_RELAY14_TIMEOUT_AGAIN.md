# 2026-06-12: повторный `row_17` всё ещё умирает на `RELAY_TIMEOUT=14`

## Сделано
- Выполнен новый одиночный test call по:
  - `row_17`
  - `+79012091111`
  - `request_id = manual.2026-06-12.ROW17.relay14.recheck`
- Для цикла были подняты только три минимальных workflow:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
- Relay journal с enriched logging подтвердил точный payload:
  - `to_number = +79012091111`
  - `user_id = row_17`
  - `lead_id = row_17`
  - `source_record_key = row_17`
  - `request_id = manual.2026-06-12.ROW17.relay14.recheck`
- Внешний webhook ответил:
  - `HTTP 200`
  - body пустой
- Relay завершился timeout-path:
  - `Upstream failed (14034ms): The read operation timed out`
  - `POST /eleven/outbound-call HTTP/1.1 502`
- После цикла новый conversation по `row_17` в свежем списке Eleven не обнаружен.
- Все три workflow снова выключены.

## На чем остановились
- `RELAY_TIMEOUT=14` уже даёт хороший результат для быстрых кейсов типа `row_18`, где upstream успевает вернуть JSON.
- Но для `row_17` этого окна всё ещё недостаточно.
- Значит сейчас у нас есть по крайней мере два разных типа outbound-case:
  - быстрый provider reject;
  - долгий upstream timeout без materialized conversation.

## Что делать дальше
1. Держать контур на паузе.
2. Не трогать prompt/автоответчики на этом шаге.
3. Решить, нужен ли ещё один маленький шаг по relay: `14 -> 16`.
4. Подготовить следующую пригодную базу/номер для новых одиночных тестов, потому что первая таблица практически исчерпана.
