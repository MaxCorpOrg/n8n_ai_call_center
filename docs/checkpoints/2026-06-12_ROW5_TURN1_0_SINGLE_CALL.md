# 2026-06-12: одиночный `row_5` на минимальном `turn_timeout = 1.0`

## Сделано
- Поднят только минимальный outbound-контур:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
- Отправлен один одиночный test-call:
  - `row_5`
  - `company_name = Анаит`
  - `contact_name = Анаит`
  - `phone_primary = +79879860736`
  - `request_id = manual.2026-06-12.ROW5.turn1_0`
- Relay дал accepted-path:
  - `Upstream 200 (15701ms, 139 bytes)`
  - `conversation_id = conv_0401ktxjmstcfzvs23vga1ah97h5`
- Eleven detail подтвердил:
  - `version_id = agtvrsn_5001ktxj73befn6bgdqbd9sckd9s`
  - `user_id = row_5`
  - `external_number = +79879860736`
  - `status = done`
  - `call_duration_secs = 12`

## Что показал звонок
- Первая реплика человека:
  - `Алло!`
- Агент начал opener на `2s`.
- Сырые технические метрики именно на старте ответа:
  - `convai_asr_trailing_service_latency = 0.071s`
  - `convai_llm_service_ttfb = 0.489s`
  - `convai_tts_service_ttfb = 0.124s`
  - `convai_llm_service_ttf_sentence = 0.678s`
- Значит техническая задержка после ответа человека уже короткая.
- Но сам opener перегружен:
  - длинный;
  - рекламный;
  - человек не дослушал и перебил агента:
    - `Я тебе говорю,`

## На чем остановились
- Вопрос `turn_timeout` на сейчас практически закрыт:
  - live уже стоит на минимально допустимом `1.0s`;
  - ниже API не разрешает.
- Следующий реальный дефект уже не latency engine, а неудачная первая spoken-фраза.

## Что делать дальше
1. Упростить opener.
2. Сохранить быстрый старт ответа без отката `eager/speculative`.
3. Сделать следующий одиночный тест по следующему номеру по порядку.
4. Проверить, стало ли меньше перебиваний и замешательства в первые секунды.

## Артефакты
- `.runtime/single_call_2026-06-12_row_5_turn1_0_check/request_payload.json`
- `.runtime/single_call_2026-06-12_row_5_turn1_0_check/outbound_headers.txt`
- `.runtime/single_call_2026-06-12_row_5_turn1_0_check/outbound_body.txt`
- `.runtime/single_call_2026-06-12_row_5_turn1_0_check/relay_logs.txt`
- `.runtime/single_call_2026-06-12_row_5_turn1_0_check/eleven_recent_conversations.json`
- `.runtime/single_call_2026-06-12_row_5_turn1_0_check/conv_0401ktxjmstcfzvs23vga1ah97h5.json`
