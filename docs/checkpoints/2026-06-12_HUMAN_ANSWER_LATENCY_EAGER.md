# 2026-06-12: live human-answer latency поджата через `eager + speculative + 1.2s`

## Сделано
- Снят актуальный live agent config и подтверждено текущее до-правки состояние:
  - `version_id = agtvrsn_8801ktxhmnyaeqcr6wwjh3k4m6tp`
  - `turn_timeout = 2.0`
  - `turn_eagerness = normal`
  - `speculative_turn = false`
- Сохранён backup:
  - `backups/2026-06-12_human_answer_latency_eager/current_ai_call_agent_1.before.json`
- Применён patch:
  - `backups/2026-06-12_human_answer_latency_eager/main_human_answer_latency_eager_payload.json`
- Новая live version:
  - `agtvrsn_0401ktxhpa5rfw39gs2evg7cqja3`
- Новые live turn-параметры:
  - `turn_timeout = 1.2`
  - `turn_eagerness = eager`
  - `speculative_turn = true`

## Проверка

### Тест 1: `row_3`
- `conversation_id = conv_6501ktxhr0vre8580xw18xfg0eg8`
- `request_id = manual.2026-06-12.ROW3.latency.eager`
- opener metrics:
  - `convai_asr_trailing_service_latency = 0.048s`
  - `convai_llm_service_ttfb = 0.555s`
  - `convai_tts_service_ttfb = 0.111s`

### Тест 2: `row_4`
- `conversation_id = conv_4601ktxhxdjzf90shjjb1faw4dg9`
- `request_id = manual.2026-06-12.ROW4.latency.eager`
- opener metrics:
  - `convai_asr_trailing_service_latency = 0.128s`
  - `convai_llm_service_ttfb = 0.375s`
  - `convai_tts_service_ttfb = 0.117s`

## На чем остановились
- После patch raw техническая задержка после финализации человеческой реплики уже короткая.
- Визуально transcript всё ещё может показывать разрыв в несколько секунд, но это уже не чистая LLM/TTS latency.
- Следующий проблемный слой теперь не “медленный старт ответа”, а логика разговора:
  - intermediary vs screening;
  - лишняя длина реплик;
  - корректный `call_log` на human/intermediary ветке.

## Что делать дальше
1. Считать latency patch рабочим baseline.
2. Следующий одиночный тест делать уже под задачу:
   - сокращать лишнюю разговорность;
   - не тратить токены на ложные intermediary / screening кейсы;
   - проверять `call_log` на живой ветке.
