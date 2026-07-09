# 2026-07-09: Eleven voice switch matrix и текущий lab-статус

## Актуальное обновление `2026-07-09 12:07 MSK`

### Сделано
- Проверен опубликованный head `agtvrsn_7201kx313sejen482kcvss6vy781`.
  - self-test: `conv_0701kx31a1exfaz9v9scm1qt4v9r`
  - дефект: агент не сделал real tool call;
  - вместо этого он произнёс служебный текст вида `silent call_log with payload...`;
  - вывод: `7201...` нельзя считать рабочим кандидатом.
- Проверены две попытки исправить terminal path prompt-only способом.
  - `agtvrsn_5501kx31hea9ezzss60cwr6jb20y`
    - self-test: `conv_8101kx31jd28f0gtdvkbqwmrjzq9`
    - дефект: агент голосом произнёс `call_log({...})` и `end_call({...})`, real tool calls не появились.
  - `agtvrsn_7901kx31rzbqeva9gqqbrd69j3cf`
    - self-test: `conv_4701kx31sj7ffp4s2vkw0qw9pq80`
    - дефект: агент снова произнёс `call_log({...})` как обычную речь.
- Lab-ветка ElevenLabs откатана на actual-tool-call линию:
  - current lab head: `agtvrsn_7701kx31xdq3fnxvq5c2a8mwnxkj`
  - payload взят из `.runtime/eleven_voice_switch_matrix_2026-07-09/turn_latency_allo_recovery_patch/payload.json`
  - это та же линия, где в `conv_8401kx30vhakebh9ewa4xw5psnk2` реальные `call_log` и `end_call` были именно tool calls, а не spoken text.
- В анализатор добавлена защита от нового класса регрессии:
  - `spoken_tool_pseudocode`
  - ловит spoken `call_log(...)`, `end_call(...)`, `send_sms_info(...)`, JSON/payload/identity-поля в обычной реплике агента.
- Опасные экспериментальные helper-скрипты с prompt-only terminal pseudo-code не оставлены в проекте.

### На чем остановились
- Git branch:
  - `codex/eleven-naturalness-lab`
- ElevenLabs lab branch:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- Current lab head:
  - `agtvrsn_7701kx31xdq3fnxvq5c2a8mwnxkj`
- Боевой `Main` не трогался.
- Важный вывод:
  - prompt-only формулировки вокруг `call_log/end_call` опасны;
  - если модель начинает произносить tool syntax, это хуже duplicate close;
  - дальше нужно чинить финализацию структурно: через tool binding / workflow / platform tool behavior, а не через просьбы "напиши call_log".

### Что делать дальше
1. Следующий тест начинать только с current lab head:
   - `agtvrsn_7701kx31xdq3fnxvq5c2a8mwnxkj`
2. Первый gate перед любыми улучшениями:
   - real `tool_calls` populated;
   - assistant message для tool-path пустой или без служебного текста;
   - нет `spoken_tool_pseudocode`.
3. Если real tool calls сохранены:
   - отдельно добивать duplicate close / filler / ordinary speech after `call_log`.
4. Не продолжать линии:
   - `agtvrsn_7201kx313sejen482kcvss6vy781`
   - `agtvrsn_5501kx31hea9ezzss60cwr6jb20y`
   - `agtvrsn_7901kx31rzbqeva9gqqbrd69j3cf`
5. До ввода в live нельзя переносить lab-настройки в боевой `Main`.

## Сделано
- Продолжение `2026-07-09` после checkpoint:
  - self-test `4701...`:
    - conversation: `conv_4201kx30pqcjexgvgrp1ca9qxcfm`
    - single-close и `context_fetch_before_opener` ошибок не было;
    - главный remaining issue: turn-taking gaps.
  - опубликован faster turn-taking head:
    - `agtvrsn_4501kx30v13eftetr3ngdc9v0nzy`
    - `turn_timeout = 1.55`
    - `soft_timeout = 1.8`
  - self-test `4501...`:
    - conversation: `conv_8401kx30vhakebh9ewa4xw5psnk2`
    - первый ответ улучшился до `2s`;
    - но вернулись:
      - filler `Да...` перед terminal finalization;
      - ordinary speech after `call_log`;
      - duplicate close.
  - усилен helper:
    - `scripts/prepare_eleven_terminal_tool_and_binding_variant.sh`
    - добавлен no-filler rule для terminal mode.
  - опубликован terminal no-filler head:
    - `agtvrsn_5601kx310j94f6s9ns1v48477v1w`
  - self-test `5601...`:
    - conversation: `conv_7201kx3112mkfhyt8fype6w392zk`
    - single-close/ordinary-after-call-log ошибок в этом прогоне не было;
    - но вернулся `context_fetch_before_opener`.
  - добавлен helper:
    - `scripts/prepare_eleven_context_fetch_after_opener_tool_variant.sh`
  - опубликован current lab head:
    - `agtvrsn_7201kx313sejen482kcvss6vy781`
  - важное ограничение:
    - Eleven Update Agent response не закрепил новое описание `context_fetch` tool;
    - tool description в response остался старым;
    - значит `7201...` сейчас держит no-context-before-opener только через prompt override, а не через tool-level description.

- Проверена официальная документация ElevenLabs по:
  - conversation flow;
  - expressive mode;
  - agent versioning / branches;
  - experiments;
  - agent testing;
  - real-time insights.
- Вывод по документации:
  - разделение `одна логика -> несколько voice/TTS вариантов` является правильным путём;
  - боевой `Main` трогать не нужно;
  - lab-ветка ElevenLabs должна использоваться как изолированный контур;
  - перед вводом в live нужно прогонять self-tests и только потом tiny canary.
- Добавлен helper:
  - `scripts/prepare_eleven_voice_only_variant.sh`
- Helper делает voice-only payload:
  - меняет `conversation_config.tts.model_id`;
  - опционально меняет `voice_id`, `speed`, `stability`, `similarity_boost`;
  - не меняет prompt, workflow, tools, `call_log`, `end_call`, machine rules или turn-taking.
- Собрана матрица payload-ов:
  - `.runtime/eleven_voice_switch_matrix_2026-07-09/payload_logic4401_v3.json`
  - `.runtime/eleven_voice_switch_matrix_2026-07-09/payload_logic4401_flash.json`
  - `.runtime/eleven_voice_switch_matrix_2026-07-09/payload_logic7701_v3_safe_fallback.json`
  - `.runtime/eleven_voice_switch_matrix_2026-07-09/payload_logic7701_flash_safe_fallback.json`
- В `Flash` payload теперь `expressive_mode=false`.
- В `v3` payload теперь `expressive_mode=true`.
- Опубликован и проверен через API lab head:
  - `agtvrsn_2601kx2zn4wvfrwtn5gazrvx329b`
  - база: `4401` logic
  - voice/TTS: `eleven_v3_conversational`
  - LLM: `gpt-5-mini`
- Проведён self-test `call_01_logic4401_v3_selftest`:
  - conversation: `conv_8101kx2zrkxre2mr11ssphh1tahn`
  - результат:
    - opener нормальный;
    - `[calm]` не всплыл;
    - но остались duplicate close и normal speech after `call_log`.
- Опубликован и проверен lab head:
  - `agtvrsn_3701kx2ztscwfvasrqnqq6x3wdbs`
  - база: `7701` safe fallback
  - voice/TTS: `eleven_v3_conversational`
- Проведён self-test `call_02_logic7701_v3_selftest`:
  - conversation: `conv_5001kx2zva0ffr0v9tsjsfr4sh4j`
  - результат:
    - `7701` хуже как текущая база;
    - вернулся `[calm]`;
    - duplicate close остался.
- Поверх `4401 + v3` опубликован узкий patch:
  - `agtvrsn_6001kx2zxygcezbtzzwebdf1z0nm`
  - смысл:
    - plain Russian text only;
    - static filler `Да...`;
    - single-close guard.
- Проведён self-test `call_03_logic4401_v3_singleclose_selftest`:
  - conversation: `conv_9601kx2zye96e4b9vp5epkhqpytk`
  - результат:
    - сценарий дошёл до SMS;
    - выявлен новый явный дефект: `context_fetch` до opener дал долгую задержку;
    - после `call_log` всё ещё была обычная речь перед `end_call`.
- Добавлен helper:
  - `scripts/prepare_eleven_preopener_and_sms_singleclose_variant.sh`
- Поверх `6001...` опубликован следующий lab head:
  - `agtvrsn_4701kx303bj4ftnrx6f7n4rdv9zn`
  - смысл:
    - запретить `context_fetch` до exact opener;
    - для SMS consent закрепить порядок:
      - короткое spoken acknowledgement до tools;
      - `send_sms_info`;
      - silent `call_log`;
      - spoken `end_call`;
      - stop.

## На чем остановились
- Git branch:
  - `codex/eleven-naturalness-lab`
- ElevenLabs lab branch:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- Current lab head:
  - `agtvrsn_7201kx313sejen482kcvss6vy781`
- Этот head опубликован, но ещё не проверен звонком.
- `7201...` содержит:
  - `gpt-5-mini`
  - `eleven_v3_conversational`
  - `turn_timeout = 1.55`
  - `soft_timeout = 1.8`
  - terminal no-filler / single-close prompt guard
  - prompt-only `context_fetch` after opener guard
- Боевой `Main` не трогался.
- Текущий рабочий подход:
  - базовая логика: `4401` family;
  - голос: `Eleven v3 Conversational`;
  - не использовать `7701` как текущую base для v3, потому что он вернул `[calm]`.

## Что делать дальше
1. Сделать один self-test уже на:
   - `agtvrsn_7201kx313sejen482kcvss6vy781`
2. Проверить только 4 gate:
   - нет `context_fetch` до opener;
   - opener начинается сразу exact opener, без `Алло...`;
   - после SMS consent есть короткий acknowledgement до tool-path;
   - после `call_log` нет ordinary assistant speech, только `end_call`.
3. Если `4701...` проходит:
   - сделать один voice-only `Flash` вариант от этой же логики;
   - сравнить `v3` и `Flash` только по голосу/скорости, без изменения prompt.
4. Если `4701...` не проходит:
   - не делать новые voice experiments;
   - сначала добить finalization и pre-opener flow.
