# 2026-06-06: `row_9` подтвердил ускорение, но открыл новый баг `eleven_conv_id`

## Сделано
- Выполнен следующий одиночный звонок по:
  - `row_9`
  - `+79255138351`
  - `Татьяна`
  - `request_id = manual.2026-06-06.ROW9.latencycheck`
- Новый разговор:
  - `conversation_id = conv_8401kte14mqmeetatxqfh40cqjqv`
  - `version_id = agtvrsn_4401kte0xffsfm1rnq9bbtajj65y`
- Главная цель этого цикла подтверждена:
  - после live trim `turn_timeout: 4.0 -> 3.2` пауза после живого ответа реально сократилась;
  - user `Алло!` был на `1s`
  - agent opener уже стартовал на `2s`
- Метрики:
  - `ASR trailing ~= 0.162s`
  - `LLM TTFB ~= 0.410s`
  - `LLM first sentence ~= 0.516s`
  - `TTS TTFB ~= 0.182s`
- Дальше человек не продолжил разговор:
  - user: `...`
- Agent корректно отработал финал:
  - `call_log`
  - silent `end_call`
  - `termination_reason = end_call tool was called.`

## На чем остановились
- На этом же тесте появился новый регресс в traceability:
  - вместо текущего `conv_8401kte14mqmeetatxqfh40cqjqv`
  - в `call_log` ушёл:
    - `conv_65e2e2e7e2e2e7e2e2e7e2e2e7e2e2e7`
- То есть скорость уже улучшена, но корректная сборка `eleven_conv_id` снова сломалась, на этот раз именно в ветке:
  - `human answer -> opener -> ... -> no_answer`
- После теста минимальные workflow снова выключены:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `false`
- `n8n-server-n8n-1` снова `running|healthy`.

## Что делать дальше
1. Не запускать новый звонок автоматически.
2. Сначала разобрать, откуда именно agent взял `conv_65e2...`.
3. Починить `eleven_conv_id` в human-silence ветке, не откатывая `turn_timeout = 3.2`.
4. Только потом делать следующий одиночный тест по `row_10`.
