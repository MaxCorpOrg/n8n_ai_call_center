# 2026-06-05: один test-cycle по `row_5`, machine-path и partial traceability

## Сделано
- Выполнен следующий одиночный звонок по порядку:
  - `row_5`
  - `+79879860736`
  - `Анаит`
- Перед самим звонком найден и исправлен отдельный blocker публикации:
  - у `ELEVEN_OUTBOUND_CALL_BRIDGE`, `ELEVEN_TOOL_CALL_LOG_BRIDGE`, `ELEVEN_TOOL_CONTEXT_BRIDGE` был пустой `activeVersionId`;
  - из-за этого `n8n` отдавал `Active version not found for workflow with id "sHTbALayEZdy8Mzs"`;
  - `activeVersionId` проставлен равным `versionId`.
- После фикса вызов реально прошёл и создал:
  - `conv_1901ktbtzw94ek4rzngccvtqka9k`
- Линия оказалась машинной:
  - `Продолжаем дозваниваться. Оставайтесь на линии.`
  - затем `Абонент не берёт трубку...`
- Агент отработал правильно по machine-path:
  - `skip_turn`
  - `call_log`
  - silent `end_call`
- В `call_log` уже корректно доехали:
  - `lead_id = row_5`
  - `source_record_key = row_5`
  - `phone_primary = +79879860736`
- Запись ушла в live Sheet:
  - `'Лиды_обзвон'!A41:AM41`

## На чем остановились
- Минимальные workflow снова выключены.
- Звонковый контур снова стоит на паузе.
- Точный opener этим тестом не проверен, потому что human-answer path не случился.
- `eleven_conv_id` всё ещё битый:
  - в лог ушёл `conv_5`
  - вместо реального `conv_1901ktbtzw94ek4rzngccvtqka9k`

## Что делать дальше
- Не запускать новый цикл автоматически.
- Следующий шаг:
  1. добить реальный `eleven_conv_id` в `call_log`;
  2. потом сделать следующий одиночный тест по порядку уже на `row_6`;
  3. проверить либо точный opener на живом ответе, либо корректный `conv_*` на machine-path.
