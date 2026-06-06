# 2026-06-06: `row_10` не дошёл до речи, rescue пока не проверен

## Сделано
- Выполнен следующий одиночный звонок по:
  - `row_10`
  - `+77077080155`
  - `svetlayaa73`
  - `request_id = manual.2026-06-06.ROW10.humansilence`
- После включения минимальных workflow outbound-запрос ушёл в Eleven.
- По Eleven API найден новый разговор:
  - `conversation_id = conv_4301kte251sdef79z7m4345qs744`
  - `status = failed`
  - `version_id = null`
- Причина провала:
  - `INVITE failed: sip status: 480: Temporarily Unavailable (SIP 480)`
- Transcript пустой, до речи дело не дошло.

## На чем остановились
- Новый `human-silence rescue` этим тестом не проверился.
- Причина не в prompt, а в телефонии/provider path на этом конкретном номере.
- После теста минимальные workflow снова выключены:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `false`
- `n8n-server-n8n-1` снова `running|healthy`.

## Что делать дальше
1. Не запускать новый цикл автоматически.
2. Следующий speech-тест делать уже по `row_11`.
3. Если цель именно проверка голосовой логики, международные или нестабильные номера вроде `+7707...` лучше заранее фильтровать из такого тестового цикла.
