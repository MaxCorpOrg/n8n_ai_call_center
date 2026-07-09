# 2026-07-09: Eleven voice switch matrix и текущий lab-статус

## Сделано
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
  - `agtvrsn_4701kx303bj4ftnrx6f7n4rdv9zn`
- Этот head уже опубликован, но ещё не проверен звонком.
- Боевой `Main` не трогался.
- Текущий рабочий подход:
  - базовая логика: `4401` family;
  - голос: `Eleven v3 Conversational`;
  - не использовать `7701` как текущую base для v3, потому что он вернул `[calm]`.

## Что делать дальше
1. Сделать один self-test уже на:
   - `agtvrsn_4701kx303bj4ftnrx6f7n4rdv9zn`
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
