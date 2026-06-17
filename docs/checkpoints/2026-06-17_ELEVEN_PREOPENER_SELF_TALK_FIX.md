# 2026-06-17 — Eleven naturalness lab: pre-opener self-talk fix

## Сделано
- Подтверждён проблемный self-talk кейс на разговоре:
  - `conv_0301kvafajs9ekwt3zw5n94p8dx4`
- По transcript видно, что агент:
  - получил короткие фрагменты `Алло? / Что? / Нет.`
  - начал opener с префикса `Так...`
  - затем ушёл в ложную классификацию `not_target`
  - потом ещё дал поздний line-check.
- Это зафиксировано как смесь двух проблем:
  - слишком мягкий pre-opener gate;
  - soft-timeout filler мог префиксовать opener.
- Усилен helper:
  - [scripts/prepare_eleven_false_positive_asr_gate_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_false_positive_asr_gate_variant.sh:1)
- В нём теперь:
  - одинокий короткий токен вроде `алло / да / угу / ага / что` до opener считается неоднозначным;
  - без второго ясного человеческого сигнала opener не должен стартовать;
  - в такой ситуации agent должен молча ждать и при необходимости использовать `skip_turn`, а не открывать sales-диалог;
  - `not_target` запрещён по одному голому `Нет`;
  - `soft_timeout_config.timeout_seconds` поднят до `3.2`;
  - статический `soft_timeout` filler заменён с `Так...` на технический placeholder `...`;
  - LLM soft-timeout prompt теперь явно разрешает filler только после полного opener.
- Новый опубликованный lab version:
  - `agtvrsn_8101kvaftfcjejjrebsswskw52h3`
- Верификация после публикации:
  - `.runtime/eleven_lab_preopener_gate_hardening_2026-06-17/apply_result/response.json`
  - `26/26 ok` через:
    - [scripts/check_eleven_prompt_invariants.py](/home/max/n8n_ai_call_center/scripts/check_eleven_prompt_invariants.py:1)

## На чем остановились
- Технически новый anti-self-talk patch уже опубликован в `lab_naturalness_2026_06`.
- Пока ещё не снят новый живой self-test именно на сценарий:
  - пользователь молчит;
  - или на линии только шум / слабый pickup.
- Значит сам фикс уже применён, но его нужно подтвердить одним коротким ручным звонком.

## Что делать дальше
1. Сделать один ручной self-test на свой номер с полным молчанием после поднятия трубки.
2. Проверить:
  - не стартует ли opener сам по себе;
  - не вылезает ли больше `Так...` перед opener;
  - не появляется ли ложный `not_target` по одному короткому фрагменту.
3. Если self-talk ушёл:
  - оставить `agtvrsn_8101kvaftfcjejjrebsswskw52h3` как новую рабочую вершину lab.
4. Если self-talk всё ещё останется:
  - следующий шаг уже не prompt-only, а дополнительное ужесточение opening-gate логики.
