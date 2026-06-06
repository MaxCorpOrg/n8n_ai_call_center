# 2026-06-06: `row_11` показал конфликт global `soft_timeout` с `human-answer gate`

## Сделано
- Выполнен следующий одиночный тест по:
  - `row_11`
  - `+79533940071`
  - `Татьяна Голубева Косметология, бьюти услуги`
- Для теста временно поднимались только:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
- Новый разговор:
  - `conversation_id = conv_1301kte9dps8ejfvk7fzy4zstvxs`
  - `version_id = agtvrsn_9401kte963xcf2j87t1wervbdtv5`
- По transcript зафиксировано:
  1. на `3s` user дал только `...`
  2. agent сразу сказал:
     - `Алло, меня слышно? Вы тут?`
  3. на `6s` user ответил:
     - `Алло?`
  4. на `8s` agent произнёс полный business-opener
  5. позже user сказал:
     - `Продолжайте, я слушаю.`
  6. agent задал follow-up:
     - `Вам это в принципе интересно?`
  7. после второго `...` agent корректно сделал:
     - `call_log(no_answer)`
     - silent `end_call`
- Rescue-вопрос второй раз не повторялся.
- `call_log` дошёл до live Sheet:
  - `updated_range = 'Лиды_обзвон'!A45:AM45`

## На чем остановились
- Подтверждено, что схема `one rescue only` сама по себе работает.
- Но подтверждён конфликт:
  - `soft_timeout_config` в текущем виде глобальный;
  - из-за этого rescue срабатывает слишком рано, ещё до нормального human-answer после первого `...`
- Это означает логическую несовместимость текущей реализации с `human-answer gate`.
- Параллельно не закрыт traceability-дефект:
  - вместо текущего `conv_1301kte9dps8ejfvk7fzy4zstvxs`
  - в `call_log` ушёл мусорный `eleven_conv_id = conv_8e2e7e7e7e7e4e7e8e7e7e7e7e7e7e7e`
- После теста минимальные workflow снова выключены, контур возвращён в паузу.

## Что делать дальше
1. Не запускать новый speech-тест сразу.
2. Сначала убрать зависимость от global `soft_timeout_config`:
   - rescue должен жить только после opener и только после явного human-answer.
3. Отдельно починить `eleven_conv_id` в ветке `human -> ... -> no_answer`.
4. Только после этих двух правок делать следующий одиночный звонок уже по `row_12`.
