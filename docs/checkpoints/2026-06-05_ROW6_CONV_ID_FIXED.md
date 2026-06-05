# 2026-06-05: `row_6` подтвердил исправление `eleven_conv_id`

## Сделано
- После `row_5`, где `eleven_conv_id` ушёл как `conv_5`, live `Main` был ужесточён:
  - `eleven_conv_id` нужно копировать verbatim из `system__conversation_id`;
  - в prompt добавлены invalid examples:
    - `conv_5`
    - `conv_6`
  - добавлен valid example полного `conv_*`.
- Новая live version:
  - `agtvrsn_4801ktbw46wde348tvxnf4ewx54q`
- После этого выполнен следующий одиночный звонок по:
  - `row_6`
  - `+79182007944`
  - `Анна`
- Новый разговор:
  - `conv_5801ktbw5twre5a8srggqhzqh5yv`
- Это был machine/silence path:
  - user: `...`
  - agent: `call_log`
  - agent: silent `end_call`
- Важный результат:
  - `call_log` записал уже правильный полный:
    - `eleven_conv_id = conv_5801ktbw5twre5a8srggqhzqh5yv`
  - также доехали:
    - `lead_id = row_6`
    - `source_record_key = row_6`
    - `phone_primary = +79182007944`

## На чем остановились
- Минимальные workflow снова выключены.
- Контур на паузе.
- Traceability по `call_log` на machine-path теперь подтверждена.
- Точный двухфразный opener на живом человеке ещё не проверен.

## Что делать дальше
- Следующий одиночный тест делать по `row_7`.
- Цель:
  1. проверить first spoken opener на живом ответе человека;
  2. убедиться, что и human-path, и `call_log` теперь живут вместе без регрессии.
