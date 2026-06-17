# Контрольная точка — 2026-06-17

## Обновление 2026-06-17: зафиксирована текущая lab-точка с price-anchor

### Сделано

- После удачного живого разговора в текущую naturalness-lab ветку добавлен отдельный узкий price-answer patch.
- Новый helper:
  - [scripts/prepare_eleven_price_anchor_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_price_anchor_variant.sh:1)
- Отдельно вынесен машинно-читаемый source-of-truth для price-answer ветки:
  - [docs/agent_kb_lipolong/10_COMMERCIAL_ANCHOR_RU.json](/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/10_COMMERCIAL_ANCHOR_RU.json:1)
- Этот patch не трогает:
  - opener
  - rescue
  - tool sequencing
  - voice stack
- Он добавляет только одно разговорное правило:
  - если пользователь спрашивает цену / стоимость / бесплатна ли тестовая упаковка,
    агент отвечает коротко и прямо по зафиксированному anchor.
  - если цену не спрашивали,
    агент сам её не озвучивает.

### Текущая точка

- `branch_id`:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- `version_id`:
  - `agtvrsn_9201kvaeewdnerjvyrcb2ykkhz5g`
- стек:
  - `llm = gpt-5-mini`
  - `tts.model_id = eleven_v3_conversational`

### Что именно теперь зафиксировано в prompt

- ориентир по стоимости:
  - `от 19 000 руб.`
- старт:
  - `от 1 шт.`
- тестовая упаковка:
  - не бесплатная
- допустимые короткие дополнительные факты:
  - доставка обычно `3-4 дня`
  - оплата: безнал, полная предоплата

### Как агент должен отвечать

- если спрашивают цену:
  - ответить коротко, в `1-2` коротких предложениях
  - не уходить в спор о цене на много ходов
  - потом перевести в один next step:
    - SMS
    - или callback менеджера
- если цену не спрашивали:
  - не вставлять стоимость в opener
  - не вставлять стоимость в обычную презентацию
  - держать цену как knowledge-anchor на случай прямого вопроса

### На чем остановились

- Price-anchor уже применён в текущую lab-ветку и подтверждён по тексту самого live prompt.
- После этого отдельно убран технический дубликат второго price-блока в prompt.
- Текущая чистая lab-вершина после cleanup:
  - `agtvrsn_6701kvadx4z9f60a639v3h02dgmy`
- Для этой вершины уже прогнан локальный invariant-check prompt:
  - [scripts/check_eleven_prompt_invariants.py](/home/max/n8n_ai_call_center/scripts/check_eleven_prompt_invariants.py:1)
  - результат:
    - [prompt_invariants.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_price_on_ask_only_cleanup_2026-06-17/prompt_invariants.json)
  - статус:
    - `13/13 ok`
- Дополнительно прогнан JSON-driven preflight уже на новом payload от commercial-anchor файла:
  - [prompt_invariants.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_price_anchor_jsonized_2026-06-17/prompt_invariants.json)
  - статус:
    - `15/15 ok`
- После этого JSON-driven payload уже реально опубликован в lab-ветку:
  - `agtvrsn_9201kvaeewdnerjvyrcb2ykkhz5g`
- И отдельная проверка уже прогнана на опубликованном ответе Eleven:
  - [prompt_invariants_applied.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_price_anchor_jsonized_2026-06-17/apply_result/prompt_invariants_applied.json)
  - статус:
    - `15/15 ok`
- Поверх этого прогнана и отдельная проверка согласованности коммерческого anchor между:
  - `10_COMMERCIAL_ANCHOR_RU.json`
  - `01_PRODUCT_PROFILE_RU.md`
  - `09_ELEVEN_TOOL_SEND_SMS_RU.md`
  - артефакт:
    - [commercial_anchor_consistency.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_price_anchor_jsonized_2026-06-17/commercial_anchor_consistency.json)
  - статус:
    - `11/11 ok`
- Отдельного speech-test именно на сценарий:
  - `Сколько стоит?`
  - `Тестовая упаковка бесплатная?`
  ещё не было.

### Что делать дальше

1. Следующий живой self-test строить именно на вопросе о цене.
2. Проверить три вещи:
   - агент называет `от 19 000 руб.`
   - говорит это коротко и уверенно
   - потом ведёт либо в SMS, либо в callback менеджера.
3. Точный ручной сценарий для следующего теста:
   - ответить на звонок коротко:
     - `Алло`
   - дождаться opener
   - после opener сказать:
     - `Да, интересно. А сколько стоит?`
   - затем уточнить:
     - `Тестовая упаковка бесплатная?`
   - целевое поведение:
     - агент сам не вбрасывает цену до вопроса;
     - после вопроса коротко называет anchor;
     - не уходит в длинный прайс-монолог;
     - затем переводит в SMS или callback.
4. Dry-run request уже подготовлен:
   - [request.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_price_selftest_ready_2026-06-17/call_01_price_dry_run/request.json)
5. Для следующего живого цикла уже есть отдельный wrapper именно под price-сценарий:
   - [scripts/run_eleven_price_selftest_audit.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_price_selftest_audit.sh:1)
   - он после звонка даёт:
     - обычный finalization audit
     - и отдельный `price_scenario_audit.json`
6. Историческая проверка старой версии уже показала полезный анти-паттерн:
   - [price_scenario_audit.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_price_anchor_fix_2026-06-17/call_01_selftest/price_scenario_audit.json)
   - там было подтверждено:
     - `price_mentioned_before_user_asked`
     - `no_price_question_detected`
   - это важное доказательство, зачем вообще понадобилось правило `price only on direct ask`.
