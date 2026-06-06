# 2026-06-06: поджатие задержки после живого ответа

## Сделано
- Разобран свежий живой разговор:
  - `conv_2701ktdzmjz7fxqrmfczhea65r56`
- По метрикам подтверждено:
  - проблема не в “медленном GPT”;
  - backend уже отвечал быстро:
    - `ASR trailing ~= 0.185s`
    - `LLM TTFB ~= 0.476s`
    - `LLM first sentence ~= 0.574s`
    - `TTS TTFB ~= 0.351s`
- Основной хвост сидел в turn-taking ожидании перед стартом agent-реплики.
- Live `Main` поджат одним безопасным шагом:
  - `turn_timeout: 4.0 -> 3.2`
  - `turn_eagerness = normal` без изменений
  - `speculative_turn = false` без изменений
  - `turn_model = turn_v2` без изменений
- Новая live version:
  - `agtvrsn_4401kte0xffsfm1rnq9bbtajj65y`
- Артефакты:
  - `backups/2026-06-06_human_answer_latency_trim/current_ai_call_agent_1.before.json`
  - `backups/2026-06-06_human_answer_latency_trim/main_turn_timeout_3_2_payload.json`
  - `backups/2026-06-06_human_answer_latency_trim/current_ai_call_agent_1.after_patch.json`

## На чем остановились
- После этой правки новый звонок ещё не запускался.
- Поэтому сама настройка уже в live, но эффект на слух пока не подтверждён следующим тестом.
- Контур остаётся на паузе между одиночными циклами.

## Что делать дальше
1. Следующий одиночный тест делать уже после этого latency-trim.
2. Проверять три вещи:
   - сократилась ли пауза после живого ответа;
   - не стало ли больше ранних перебиваний;
   - не сломалось ли machine/call_log поведение.
3. После теста снова сразу ставить контур на паузу и фиксировать результат.
