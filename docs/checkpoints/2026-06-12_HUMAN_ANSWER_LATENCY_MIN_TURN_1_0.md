# Контрольная точка: 2026-06-12 human-answer latency минимальный turn timeout

## Сделано
- Проверен текущий live latency baseline после патча `eager + speculative + 1.2s`.
- Подтверждено, что active live version до этой правки была:
  - `agtvrsn_0401ktxhpa5rfw39gs2evg7cqja3`
- Подтверждено, что на ней стояли:
  - `turn_timeout = 1.2`
  - `turn_eagerness = eager`
  - `speculative_turn = true`
- Проверена попытка ужать `turn_timeout` ниже секунды.
- Eleven API вернул валидационное ограничение:
  - `Turn timeout must be -1 or between 1 and 300 seconds`
- После этого применён корректный partial patch только по блоку:
  - `conversation_config.turn`
- Live успешно переведён на:
  - `turn_timeout = 1.0`
  - `turn_eagerness = eager`
  - `speculative_turn = true`
- Новая live version:
  - `agtvrsn_5001ktxj73befn6bgdqbd9sckd9s`

## Артефакты
- `backups/2026-06-12_human_answer_latency_trim_07/current_ai_call_agent_1.before_turn_0_7.json`
- `backups/2026-06-12_human_answer_latency_trim_07/main_turn_timeout_0_7_payload.json`
- `backups/2026-06-12_human_answer_latency_trim_07/main_turn_timeout_1_0_payload.json`
- `backups/2026-06-12_human_answer_latency_trim_07/current_ai_call_agent_1.after_turn_1_0.json`

## На чем остановились
- Со стороны параметра `turn_timeout` ниже опускаться уже нельзя: это hard-limit самого Eleven API.
- Значит текущая живая настройка уже упёрлась в минимально допустимый таймаут.
- Новый одиночный live-звонок после этой правки ещё не сделан.

## Что делать дальше
1. Поднять только минимальный outbound-контур.
2. Выполнить один одиночный тестовый звонок на новой версии `agtvrsn_5001ktxj73befn6bgdqbd9sckd9s`.
3. Снять transcript и внутренние latency-метрики opener.
4. Сравнить субъективную паузу до/после.
5. Если пауза всё ещё ощущается длинной, править уже не `turn_timeout`, а логику post-opener silence/handoff.
