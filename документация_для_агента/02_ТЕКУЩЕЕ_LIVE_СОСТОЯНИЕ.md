# Текущее live-состояние

Обновление `2026-07-09 12:29 MSK` по текущему лучшему lab-кандидату:
- текущий Git branch:
  - `codex/eleven-naturalness-lab`
- текущая ElevenLabs lab branch:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- current lab head:
  - `agtvrsn_5301kx337pqxf01s7m9jkfbspfhs`
- боевой `Main` не трогался.

## Сделано
- Проверен мягкий latency patch:
  - `turn_timeout = 1.4`
  - `turn_eagerness = normal`
  - LLM/voice/prompt без изменений.
- Self-test:
  - `conv_2401kx3387pvf3m9pc6kab9ndr42`
- Результат:
  - opener-first работает;
  - `spoken_tool_pseudocode` нет;
  - real `call_log` и `end_call` есть;
  - `end_call tool was called`;
  - задержки лучше, чем на `4001`:
    - max gap: `6s -> 4s`
    - avg gap: `4.33s -> 3.0s`
- `turn_eagerness=eager` до этого проверен и отклонён:
  - `agtvrsn_6401kx32y00re3qsenk3ka8t1nea`
  - вернул `spoken_tool_pseudocode`.

## На чем остановились
- Лучший текущий lab-кандидат:
  - `agtvrsn_5301kx337pqxf01s7m9jkfbspfhs`
- Хорошо:
  - целевой стек `gpt-5-mini + eleven_v3_conversational`;
  - opener не сломан;
  - tools не сломаны;
  - latency стала лучше.
- Осталось:
  - после короткого `Нет.` всё ещё около `4s`;
  - нужно проверить SMS consent;
  - нужно проверить machine/`абонент`;
  - нужно решить, допустим ли filler `Да...` перед terminal close.

## Что делать дальше
1. Не использовать:
   - `agtvrsn_6401kx32y00re3qsenk3ka8t1nea`
2. Следующий вариант:
   - либо `turn_timeout = 1.3`, `turn_eagerness = normal`;
   - либо mini test-set на текущем `5301`.
3. В live не переносить до прохождения:
   - opener;
   - short negative;
   - SMS consent;
   - machine/`абонент`.

Обновление `2026-07-09 12:24 MSK` по текущей lab-ветке ElevenLabs:
- текущий Git branch:
  - `codex/eleven-naturalness-lab`
- текущая ElevenLabs lab branch:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- current lab head:
  - `agtvrsn_6301kx331akffqtvrkyfpgz2kq8k`
- боевой `Main` не трогался.

## Сделано
- Уточнён audit single-close:
  - spoken close перед `end_call` больше не считается дублем, если это отображение `end_call.system__message_to_speak`;
  - после этого `call_12` больше не ругается на duplicate close.
- Проверен вариант `turn_eagerness=eager`:
  - `agtvrsn_6401kx32y00re3qsenk3ka8t1nea`
  - `conv_7101kx32yfjre6wr4r2me1sewdpm`
  - результат плохой:
    - агент снова произнёс `silent call_log with payload...`;
    - opener снова сломался;
    - latency лучше не стала.
- Lab откатан на безопасный `4001`-payload:
  - current head после rollback: `agtvrsn_6301kx331akffqtvrkyfpgz2kq8k`
  - `turn_eagerness = normal`
  - `turn_timeout = 1.55`
  - `soft_timeout = 1.8`
- Исправлен helper:
  - `scripts/prepare_eleven_turn_latency_allo_recovery_variant.sh`
  - теперь он не срезает последующие prompt override-блоки.
- Усилен advisor:
  - `scripts/report_eleven_next_variant_advisor.py`
  - при `spoken_tool_pseudocode` или broken opener он блокирует variant testing.

## На чем остановились
- Лучший текущий lab-кандидат:
  - `agtvrsn_6301kx331akffqtvrkyfpgz2kq8k`
- Что в нём хорошо:
  - opener-first сохранён;
  - real `call_log/end_call` сохранены;
  - `spoken_tool_pseudocode` нет в проверенном `4001`-классе;
  - голос/модель остаются целевыми: `gpt-5-mini + eleven_v3_conversational`.
- Что плохо:
  - long gaps после коротких ответов;
  - `eager` это не чинит и ломает поведение.

## Что делать дальше
1. Не использовать:
   - `agtvrsn_6401kx32y00re3qsenk3ka8t1nea`
2. Следующий шаг:
   - работать от `agtvrsn_6301kx331akffqtvrkyfpgz2kq8k`;
   - искать способ уменьшить pause/turn-taking без `turn_eagerness=eager`;
   - после каждой правки проверять отсутствие `spoken_tool_pseudocode`.
3. В live не переносить до mini test-set:
   - opener;
   - short negative;
   - SMS consent;
   - machine/`абонент`.

Обновление `2026-07-09 12:16 MSK` по текущей ElevenLabs lab-ветке:
- текущий Git branch:
  - `codex/eleven-naturalness-lab`
- текущая ElevenLabs lab branch:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- current lab head:
  - `agtvrsn_4001kx32hsrbfxxtahfkabsd3a5w`
- боевой `Main` не трогался.

## Сделано
- Проверен `agtvrsn_7701kx31xdq3fnxvq5c2a8mwnxkj`:
  - `conv_4201kx326rm4exdt6zb5b2hmj79h`
  - проблема: агент ответил на первое слово пользователя `Полная.`, а не начал exact opener.
- В анализатор добавлены новые проверки:
  - `opener_not_first_agent_message`
  - `opener_micro_fragment_before_full_opener`
- Опубликован и проверен `agtvrsn_3601kx32d39nejw8t9jtkx510yve`:
  - opener-first hard gate;
  - real tool calls сохранились;
  - остались micro-cut и single-close проблемы.
- Опубликован и проверен `agtvrsn_4001kx32hsrbfxxtahfkabsd3a5w`:
  - `conv_6201kx32j8gmec6t1k7bhbs3es8f`
  - после `Да.` агент сказал полный exact opener;
  - `spoken_tool_pseudocode` нет;
  - real `call_log` и `end_call` есть;
  - `eleven_conv_id` / `conversation_id` заполнены реальным conversation id.

## На чем остановились
- Лучший текущий lab-кандидат:
  - `agtvrsn_4001kx32hsrbfxxtahfkabsd3a5w`
- Он пока не готов к live:
  - после `call_log` всё ещё появляется spoken close как обычная реплика;
  - audit видит `duplicate_close_before_end_call`;
  - есть long gaps / turn-taking overhead.

## Что делать дальше
1. Не менять сейчас голос и LLM:
   - `gpt-5-mini`
   - `eleven_v3_conversational`
2. Следующий фокус:
   - single-close / finalization;
   - проверить реальное аудио: close звучит один раз или дважды;
   - если звучит дважды, чинить tool finalization.
3. Потом прогнать маленький набор self-tests:
   - normal hello;
   - refusal / not_target;
   - SMS consent;
   - machine / `абонент`.
4. В боевой `Main` не переносить до прохождения test-set.

Обновление `2026-07-09 12:07 MSK` по восстановлению lab-контура после регрессии tool calls:
- Проверены версии:
  - `agtvrsn_7201kx313sejen482kcvss6vy781`
    - `conv_0701kx31a1exfaz9v9scm1qt4v9r`
    - регрессия: агент произнёс служебный текст `silent call_log with payload...`;
    - real `tool_calls` не было.
  - `agtvrsn_5501kx31hea9ezzss60cwr6jb20y`
    - `conv_8101kx31jd28f0gtdvkbqwmrjzq9`
    - регрессия: агент голосом произнёс `call_log({...})` / `end_call({...})`.
  - `agtvrsn_7901kx31rzbqeva9gqqbrd69j3cf`
    - `conv_4701kx31sj7ffp4s2vkw0qw9pq80`
    - регрессия: агент снова произнёс `call_log({...})` как обычный текст.
- Lab-ветка ElevenLabs откатана на actual-tool-call baseline:
  - current lab head: `agtvrsn_7701kx31xdq3fnxvq5c2a8mwnxkj`
  - branch: `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - Git branch: `codex/eleven-naturalness-lab`
- Боевой `Main` не трогался.
- Обновлён анализатор:
  - `scripts/analyze_eleven_conversation.py`
  - новый issue: `spoken_tool_pseudocode`
  - смысл: если агент произносит `call_log(...)`, `end_call(...)`, JSON/payload/identity-поля, audit сразу считает это дефектом.

## Сделано
- Lab-контур восстановлен на версию, где приоритетом являются реальные tool calls, а не prompt-only псевдокоманды.
- Неудачные prompt-only terminal helper-подходы не оставлены как рабочий путь.
- Документация закрепляет, что `7201...`, `5501...`, `7901...` не продолжать.

## На чем остановились
- Current lab head:
  - `agtvrsn_7701kx31xdq3fnxvq5c2a8mwnxkj`
- Это не финальная идеальная версия:
  - в её родственной проверке были duplicate close / filler / ordinary speech after `call_log`;
  - но в ней реальные `call_log` / `end_call` работают как platform tool calls.
- Следующий цикл должен начинаться с проверки именно real tool calls, а не с новых prompt-only формулировок.

## Что делать дальше
1. Один self-test на `agtvrsn_7701kx31xdq3fnxvq5c2a8mwnxkj`.
2. Gate:
   - `tool_calls` реально есть;
   - нет `spoken_tool_pseudocode`;
   - агент не произносит JSON, payload, `lead_id`, `phone_primary`, `eleven_conv_id`.
3. Если gate проходит:
   - точечно чинить duplicate close и filler в terminal path.
4. Если gate не проходит:
   - не продолжать prompt-only эксперименты;
   - искать причину в tool binding / workflow / platform-интеграции.

Обновление `2026-07-09 11:55 MSK` по продолжению lab-цикла:
- после `4701...` сделан self-test:
  - `conv_4201kx30pqcjexgvgrp1ca9qxcfm`
  - `context_fetch_before_opener` не было;
  - single-close ошибок не было;
  - проблема осталась в turn-taking gaps.
- опубликован fast-turn head:
  - `agtvrsn_4501kx30v13eftetr3ngdc9v0nzy`
  - `turn_timeout = 1.55`
  - `soft_timeout = 1.8`
- self-test `4501...`:
  - `conv_8401kx30vhakebh9ewa4xw5psnk2`
  - первый ответ стал около `2s`;
  - но вернулись:
    - terminal filler `Да...`;
    - ordinary speech after `call_log`;
    - duplicate close.
- усилен terminal tool helper:
  - `scripts/prepare_eleven_terminal_tool_and_binding_variant.sh`
  - terminal mode now forbids filler before `call_log` / `end_call`.
- опубликован:
  - `agtvrsn_5601kx310j94f6s9ns1v48477v1w`
- self-test `5601...`:
  - `conv_7201kx3112mkfhyt8fype6w392zk`
  - single-close ошибок в этом прогоне не было;
  - но снова появился `context_fetch_before_opener`.
- добавлен helper:
  - `scripts/prepare_eleven_context_fetch_after_opener_tool_variant.sh`
- current lab head now:
  - `agtvrsn_7201kx313sejen482kcvss6vy781`
- важное ограничение:
  - Eleven response не закрепил новое описание `context_fetch` tool;
  - tool description остался старым;
  - значит `7201...` сейчас держит no-context-before-opener через prompt override, а не через tool-level description.

## Сделано
- Быстрый turn-taking улучшил первый ответ до `2s` в одном тесте.
- Terminal no-filler patch убрал single-close ошибки в последнем прогоне.
- Current head `7201...` опубликован как следующий кандидат.

## На чем остановились
- `7201...` опубликован, но ещё не проверен звонком.
- Последний цикл из 3 звонков завершён:
  - `4701`
  - `4501`
  - `5601`
- Новый звонок делать уже следующим циклом.

## Что делать дальше
1. Один self-test на:
   - `agtvrsn_7201kx313sejen482kcvss6vy781`
2. Проверить:
   - не появился ли `context_fetch_before_opener`;
   - нет ли `Да...` перед terminal `call_log`;
   - нет ли ordinary speech after `call_log`;
   - первый ответ остаётся около `2s`.
3. Если `context_fetch_before_opener` снова появится:
   - prompt-only guard недостаточен;
   - tool-level правку планировать отдельно, потому что tool может быть shared между ветками.

Обновление `2026-07-09` по Eleven naturalness lab и voice-switch matrix:
- текущая Git-ветка:
  - `codex/eleven-naturalness-lab`
- боевой `Main` ElevenLabs не трогался.
- lab branch ElevenLabs:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- создан helper для чистого переключения голоса без изменения логики:
  - `scripts/prepare_eleven_voice_only_variant.sh`
- создан helper под найденные live-дефекты:
  - `scripts/prepare_eleven_preopener_and_sms_singleclose_variant.sh`
- собрана voice matrix:
  - `4401 logic + Eleven v3 Conversational`
  - `4401 logic + Eleven Flash v2.5`
  - `7701 fallback + Eleven v3 Conversational`
  - `7701 fallback + Eleven Flash v2.5`
- проведены 3 self-test:
  - `agtvrsn_2601kx2zn4wvfrwtn5gazrvx329b`:
    - `4401 + v3`;
    - opener нормальный;
    - остались duplicate close и speech after `call_log`.
  - `agtvrsn_3701kx2ztscwfvasrqnqq6x3wdbs`:
    - `7701 + v3`;
    - хуже как база;
    - вернул `[calm]`;
    - duplicate close остался.
  - `agtvrsn_6001kx2zxygcezbtzzwebdf1z0nm`:
    - `4401 + v3 + plaintext/single-close guard`;
    - дошёл до SMS;
    - выявил pre-opener `context_fetch`;
    - после `call_log` всё ещё была ordinary speech before `end_call`.
- current lab head now:
  - `agtvrsn_4701kx303bj4ftnrx6f7n4rdv9zn`
- смысл текущего `4701...`:
  - запрет `context_fetch` до exact opener;
  - SMS consent:
    - короткий spoken acknowledgement до tools;
    - `send_sms_info`;
    - silent `call_log`;
    - spoken `end_call`;
    - stop.
- подробный checkpoint:
  - `docs/checkpoints/2026-07-09_ELEVEN_VOICE_SWITCH_MATRIX_AND_LAB_STATUS.md`

## Сделано
- Разделили задачу на две части:
  - логика разговора;
  - voice/TTS слой.
- Подтверждено тестами, что просто взять `7701` как V3-базу нельзя:
  - он возвращает `[calm]`.
- Подтверждено тестами, что лучшая база сейчас:
  - `4401` family,
  - но с отдельным single-close/pre-opener hardening.
- Опубликован следующий lab candidate:
  - `agtvrsn_4701kx303bj4ftnrx6f7n4rdv9zn`

## На чем остановились
- `4701...` опубликован, но ещё не проверен звонком.
- Последний цикл звонков уже завершён:
  - 3 self-test сделаны;
  - новые звонки не запускать как продолжение этого же цикла без явной новой команды.

## Что делать дальше
1. Следующим циклом сделать один self-test на:
   - `agtvrsn_4701kx303bj4ftnrx6f7n4rdv9zn`
2. Проверить:
   - нет `context_fetch` до opener;
   - нет `Алло...` перед opener;
   - после `да, отправьте` есть короткое spoken acknowledgement;
   - после `call_log` нет ordinary assistant speech.
3. Если проходит:
   - собрать `Flash` voice-only вариант от той же логики;
   - сравнить с `v3` только по голосу/скорости.
4. Если не проходит:
   - сначала добить pre-opener и single-close finalization;
   - voice experiments не продолжать.

Обновление `2026-07-02` по циклу `1201... -> 5001... -> 0601... -> 6401...`:
- проведён self-test на:
  - `agtvrsn_1201kwh2kt2pfsna2qcrmv50svda`
- он показал, что lexical `not_target` patch не был по-настоящему проверен в isolation:
  - раньше него всплыли:
    - повтор opener,
    - late line-check,
    - helpdesk-tail.
- под это собран и опубликован новый head:
  - `agtvrsn_5001kwh30b0yfpdvjqk497p7pbj7`
  - builder:
    - `scripts/prepare_eleven_single_shot_opener_nottarget_variant.sh`
- смысл `5001...`:
  - `interruption` enabled;
  - `turn_timeout = 2.3`;
  - `turn_eagerness = normal`;
  - opener нельзя restart-ить после живого lexical reply;
  - после meaningful reply нельзя возвращаться в late rescue / `Вы на линии?`;
  - helpdesk-tail после terminal outcome запрещён.
- live self-test `5001...` показал:
  - стало лучше:
    - helpdesk-tail ушёл;
    - грубый multi-restart flow стал заметно лучше;
  - но осталось:
    - pre-opener `Алло?`;
    - duplicate close;
    - normal speech before/after `call_log`.
- под это опубликован следующий head:
  - `agtvrsn_0601kwh345rse22aztp6hezdkazt`
  - это комбинация:
    - `Plaintext terminal single-close`
    - `Non-interruptible finalization`
- live self-test `0601...` показал:
  - opener стартует быстро;
  - но duplicate close всё ещё остался;
  - opener всё ещё мог повторяться при повторном `Алло?`.
- под это опубликован ещё один micro-head:
  - `agtvrsn_6401kwh3889qfb6art4b4s2692fa`
  - builder:
    - `scripts/prepare_eleven_no_preopener_linecheck_variant.sh`
- live self-test `6401...` показал:
  - хороший gain:
    - pre-opener `Алло?` ушёл;
    - opener снова стартует сразу с первого живого `Алло!`;
  - remaining blocker:
    - в opener resurfaced `[calm]`;
    - duplicate close всё ещё есть;
    - normal speech after `call_log` всё ещё есть.
- значит текущая главная проблема уже сузилась:
  - не opener,
  - а refusal finalization path.
- current newest lab head now:
  - `agtvrsn_6401kwh3889qfb6art4b4s2692fa`
- next practical step now:
  - делать отдельный узкий patch только под `refusal_soft` finalization:
    - silent `call_log(refusal_soft)`
    - one spoken `end_call`
    - stop
  - и отдельно снова прибить `[calm]`.

Обновление `2026-07-02` по post-SMS spoken-ack и новой lab-версии `4801...`:
- по официальной документации ElevenLabs дополнительно подтверждено:
  - `soft timeout` маскирует ожидание именно LLM-ответа;
  - длинный tool-path сам по себе этим не закрывается;
  - для tool-gap у Eleven есть `pre_tool_speech`, но branch payload у нас держит его нестабильно;
  - музыку/tool-call sounds в lab по-прежнему не включаем.
- под этот gap добавлен новый узкий builder:
  - `scripts/prepare_eleven_post_sms_progress_ack_variant.sh`
- он публикует только lab-only правку:
  - `soft_timeout = 2.6`
  - fallback filler = `Да...`
  - новый prompt-блок `Post-SMS progress ack override`
- текущий lab head теперь:
  - `agtvrsn_4801kwh163xgfv08p39a52jq4mae`
- intended behavior теперь такой:
  - после явного `да, отправьте` агент не должен проваливаться в глухую паузу;
  - он должен быстро дать один очень короткий spoken-ack;
  - затем сразу вызвать `send_sms_info`;
  - потом silent `call_log`;
  - и только один финальный close внутри `end_call`.
- важное техническое ограничение прямо сейчас:
  - prompt-override в branch snapshot уже виден;
  - `soft_timeout = 2.6` тоже уже виден;
  - но `send_sms_info.pre_tool_speech` в branch snapshot снова остался `auto`, а не `force`;
  - значит tool-level `pre_tool_speech` через обычный branch payload всё ещё нельзя считать надёжно закреплённым.

## Сделано
- Собран и опубликован новый lab-only payload для SMS-consent path без музыки и без пустой паузы.
- Зафиксирован новый current lab head:
  - `agtvrsn_4801kwh163xgfv08p39a52jq4mae`
- Контрольные артефакты сохранены в:
  - `.runtime/eleven_post_sms_progress_ack_2026-07-02/`
- Обновлён project checkpoint с текущим practical read.

## На чем остановились
- Prompt-layer для быстрого spoken-ack уже опубликован.
- Более ранний filler `2.6s` тоже уже опубликован.
- Но branch snapshot не подтвердил жёсткую фиксацию `pre_tool_speech` на самом tool-уровне.
- Поэтому следующий шаг должен проверять не предположение, а реальный результат на одном controlled self-test.

## Что делать дальше
1. Один self-test на `SMS consent` уже на версии `4801...`.
2. Проверить:
  - есть ли быстрый spoken-ack сразу после `да, отправьте`;
  - ушла ли мёртвая пауза до `send_sms_info`;
  - не вернулся ли duplicate close;
  - остался ли финальный spoken close только внутри `end_call`.
3. Если этого всё ещё мало:
  - не трогать shared custom tool вслепую;
  - искать отдельный branch-safe способ для tool pre-speech.

Обновление `2026-07-02` по живому self-test `4801...` и новому lab-head `4601...`:
- выполнен один реальный self-test на:
  - `agtvrsn_4801kwh163xgfv08p39a52jq4mae`
- infrastructure path был clean:
  - transport = `relay_via_server`
  - branch/version matched expected
  - звонок завершился через `end_call`
- но transcript вскрыл более ранний и очень конкретный defect:
  - после user-фразы `Пока.` agent вслух проговорил внутренний meta-text:
    - `silent_call_log: call_log with ...`
  - затем user среагировал раздражённо;
  - после этого agent всё равно сделал:
    - `call_log`
    - spoken close
    - `end_call`
  - то есть duplicate close никуда не делся, а поверх него ещё и всплыл spoken tool-plan leak.
- плюс audit снова подтвердил большие паузы:
  - `М-м-м, нет.` -> ответ только через `5s`
  - `Алло!` -> `Да?` через `4s`
  - hostile final turn -> close только через `15s`
- под это собран новый узкий builder:
  - `scripts/prepare_eleven_terminal_meta_silence_variant.sh`
- он уже опубликован в lab:
  - current best lab head now:
    - `agtvrsn_4601kwh1fs4sfxb8ka9sba04r731`
- смысл нового patch:
  - запретить spoken leakage internal tool text;
  - считать `пока / до свидания / всего доброго` явным terminal close;
  - не задавать новый вопрос и не отвечать `Да?` после явного goodbye;
  - считать `м-м-м, нет` реальным refusal signal, а не зависшей hesitation-паузой.

## Сделано
- Проведён живой self-test `4801...` и собран полный audit.
- Под найденный live defect уже опубликован follow-up patch:
  - `agtvrsn_4601kwh1fs4sfxb8ka9sba04r731`
- Обновлены checkpoint-документы с новой practical control point.

## На чем остановились
- Current best lab head больше не `4801...`, а:
  - `agtvrsn_4601kwh1fs4sfxb8ka9sba04r731`
- Следующий важный gate теперь уже не только SMS-consent pause:
  - сначала нужно доказать, что ушли:
    - spoken `silent_call_log ...`
    - duplicate close
    - post-goodbye `Да?`

## Что делать дальше
1. Один следующий controlled self-test уже на `4601...`.
2. Проверить первым делом:
  - исчез ли spoken tool-plan leak;
  - исчез ли duplicate close;
  - перестал ли agent открывать мини-диалог после `Пока.`
3. Только после этого снова возвращаться к узкой проверке:
  - как ведёт себя SMS-consent ветка и ушла ли пауза после `да, отправьте`.

Дополнение `2026-07-02` по первому запуску self-test на `4601...`:
- сам patch уже опубликован;
- но первый контрольный звонок на:
  - `.runtime/eleven_terminal_meta_silence_2026-07-02/call_01_selftest/`
  не дошёл до разговора;
- transport picture:
  - `local_relay` -> timeout
  - `relay_via_server` -> `sanctioned_country`
  - `relay` -> timeout
- conversation id не был создан;
- значит этот конкретный run ничего не сказал о качестве prompt-а `4601...`;
- это testing-blocker по outbound path, а не подтверждение новой логической поломки агента.

Дополнение `2026-07-02` по восстановлению self-test transport и следующим lab-head:
- local self-test path восстановлен:
  - `scripts/start_eleven_local_relay_stack.sh`
  - `127.0.0.1:18787` снова healthy
  - tunnel обновлён через `localhost.run`
- после этого повторный self-test на `4601...` уже реально прошёл через `local_relay`:
  - `.runtime/eleven_terminal_meta_silence_2026-07-02/call_02_selftest_localrelay/`
- practical result `4601...`:
  - стало лучше:
    - `silent_call_log: ...` вслух больше не вылез;
    - старый post-goodbye `Да?` тоже не вылез;
  - но осталось:
    - обычная spoken close после `call_log`;
    - filler `Так...` перед callback-finalization;
    - заметные long gaps.
- под callback case выпущен новый узкий head:
  - `agtvrsn_1701kwh1wvgbfvz921cgf3t241v6`
  - builder:
    - `scripts/prepare_eleven_callback_terminal_fastpath_variant.sh`
- live self-test на `1701...`:
  - `.runtime/eleven_callback_terminal_fastpath_2026-07-02/call_01_selftest_localrelay/`
  показал:
  - `[calm]` снова surfaced;
  - duplicate close всё ещё остался;
  - normal speech after `call_log` тоже осталась.
- поэтому current best next candidate теперь уже не `1701...`, а:
  - `agtvrsn_0201kwh22m83faq98y8rexfcqgj1`
- он собран builder-ом:
  - `scripts/prepare_eleven_plaintext_terminal_singleclose_variant.sh`
- смысл нового `0201...`:
  - static filler `Да...` вместо LLM-generated filler;
  - global plain-text only;
  - stronger single-close path для terminal outcomes.

Дополнение `2026-07-02` по живому self-test `0201...` и новому head `2001...`:
- live self-test на:
  - `agtvrsn_0201kwh22m83faq98y8rexfcqgj1`
  - `.runtime/eleven_plaintext_terminal_singleclose_2026-07-02/call_01_selftest_localrelay/`
  показал важный structural gain:
  - `duplicate_close_before_end_call` больше не surfaced;
  - `normal_assistant_speech_after_call_log` больше не surfaced;
  - `[calm]` больше не surfaced;
- но при этом всплыл новый смысловой defect:
  - agent сам сформулировал forbidden negative-polarity qualification:
    - `Вы не работаете с липолитиками вообще?`
  - затем user дал двусмысленное `Да.`, потом уже явно:
    - `Не-не, мы не работаем.`
  - agent всё равно продолжил pitch и даже предложил SMS нецелевому контакту.
- под это выпущен следующий узкий head:
  - `agtvrsn_2001kwh296fwemca6fa5q2ctd78a`
  - builder:
    - `scripts/prepare_eleven_positive_polarity_qualification_variant.sh`
- смысл `2001...`:
  - разрешена только positive-polarity qualification:
    - `Вы вообще с липолитиками работаете?`
  - если в ответе есть ясная лексика:
    - `не работаем`
    - `не используем`
    - `не наш профиль`
    agent обязан верить этой лексике и закрывать `not_target`, а не продолжать sales pitch.
- live self-test на `2001...`:
  - `.runtime/eleven_positive_polarity_qualification_2026-07-02/call_01_selftest_localrelay/`
  показал:
  - good:
    - negative-polarity question реально ушёл;
    - agent использует:
      - `Вы вообще с липолитиками работаете?`
  - remaining:
    - после clear lexical answer:
      - `Нет, ещё не работаем.`
      agent всё ещё продолжает pitch и снова предлагает SMS;
    - то есть positive-polarity fix сработал, но immediate lexical `not_target` ещё не срабатывает.
- под это выпущен новый head:
  - `agtvrsn_1201kwh2kt2pfsna2qcrmv50svda`
  - builder:
    - `scripts/prepare_eleven_lexical_nottarget_terminal_variant.sh`
- смысл `1201...`:
  - lexical mismatch:
    - `не работаем`
    - `ещё не работаем`
    - `не используем`
    - `не наш профиль`
    должен сразу переводить звонок в `not_target`, без нового pitch, без SMS и без callback.

## Сделано
- Восстановлен local relay self-test path.
- Подтверждено живым тестом, что `4601...` убрал spoken `silent_call_log`.
- Выпущены follow-up head:
  - `1701...`
  - `0201...`
  - `2001...`
  - `1201...`
- Обновлены checkpoint-документы.

## На чем остановились
- Current best next candidate now:
  - `agtvrsn_1201kwh2kt2pfsna2qcrmv50svda`
- Его ещё не проверили живым self-test после публикации.

## Что делать дальше
1. Один следующий controlled self-test уже на `1201...` через `local_relay`.
2. Проверить:
  - схлопывается ли `Нет, ещё не работаем` сразу в `not_target`;
  - не продолжает ли agent pitch после lexical mismatch;
  - не вернулись ли `[calm]`, duplicate close и normal speech after `call_log`.

Обновление `2026-06-26` по live self-test `3301...` и новому lab-head `1401...`:
- второй реальный self-test на:
  - `agtvrsn_3301kw1qg4s4fwgvrt3zsrs46nxa`
  - не дал literal repeat прошлого contradiction-case, но вскрыл новый remaining defect layer:
    - `[calm]` снова попал в spoken text;
    - второй turn после vague / garbled ack слишком длинный;
    - после слабого `Ага` agent повторно спрашивал qualification;
    - long user-to-agent gap доходил до `10s`
- под это собран новый узкий builder:
  - `scripts/prepare_eleven_unclear_ack_short_question_variant.sh`
- его смысл:
  - после vague ack / garbled mixed reply:
    - не давать длинную value-реплику;
    - задавать только один короткий clarifying business question
  - плюс absolute ban на bracket tags:
    - `[calm]`
    - `[pause]`
    - `[thinking]`
- этот patch уже опубликован в lab:
  - current best lab head now:
    - `agtvrsn_1401kw1qv5dee36a8gyrvbqh72ws`
- verify:
  - `.runtime/eleven_unclear_ack_short_question_2026-06-26/verify/summary.json`
- practical next step now:
  - следующий real self-test уже нужно снимать на `1401...`
  - first gate:
    - no `[calm]`
    - shorter second turn after vague ack
    - no repeated qualification after weak `ага/угу`
  - only after that return to SMS-finalization validation.

Обновление `2026-06-26` по live self-test `0101...` и новому lab-head `3301...`:
- выполнен реальный branch-targeted self-test на:
  - `agtvrsn_0101kw1q5z84fky9nh654bzt6naq`
- результат инфраструктурно чистый:
  - transport = `local_relay`
  - branch/version matched expected
  - SIP/quota path не сломались
- но этот live call не дошёл до SMS-final-close, потому что раньше всплыл другой реальный defect:
  - user:
    - `Поздно.`
  - agent:
    - `Поняла, сейчас неудобно? Могу перезвонить...`
  - user:
    - `Я вообще этого не говорил. Вы чё?`
  - agent потом повёл себя неправильно:
    - `Поняла. Вы сейчас на линии?`
    - `Понялa. Вы вообще с липолитиками работаете?`
- это даёт новый confirmed reading:
  - текущая проблема здесь не в SMS-finalization как таковой;
  - проблема раньше:
    - contradiction reset after ambiguous / misheard cue
    - и неправильный переход в line-check + qualification
- под это собран новый узкий builder:
  - `scripts/prepare_eleven_asr_contradiction_reset_variant.sh`
- он уже опубликован только в lab:
  - current best lab head now:
    - `agtvrsn_3301kw1qg4s4fwgvrt3zsrs46nxa`
- verify:
  - `.runtime/eleven_asr_contradiction_reset_2026-06-26/verify/summary.json`
- practical next step now changed:
  - следующий real self-test надо делать уже не на `0101...`, а на `3301...`
  - first target:
    - contradiction-reset path
  - second target only after that:
    - SMS-final-close path

Обновление `2026-06-26` по SMS-finalization drift и новому lab-candidate:
- safe simulation на post-SMS path:
  - `.runtime/eleven_sim_sms_consent_2026-06-26/response.json`
  - показал текущий drift:
    - `send_sms_info`
    - потом обычная spoken confirmation:
      - `Информацию отправила в SMS...`
    - и только потом:
      - `call_log`
      - `end_call`
- это значит:
  - post-SMS path всё ещё может жить как обычный assistant turn перед backend finalization.
- под это собран отдельный узкий builder:
  - `scripts/prepare_eleven_post_sms_finalization_variant.sh`
- он добавляет специальный блок:
  - `Post-SMS finalization override`
  - который требует:
    1. `send_sms_info`
    2. silent `call_log`
    3. one short `end_call.system__message_to_speak`
    4. stop
- этот patch уже опубликован только в lab-ветку:
  - new lab head:
    - `agtvrsn_0101kw1q5z84fky9nh654bzt6naq`
- verify:
  - `.runtime/eleven_post_sms_finalization_2026-06-26/verify/summary.json`
- current practical read:
  - strongest next real test candidate now is already not `2201...`, but:
    - `0101...`
  - main live branch не трогался.

Обновление `2026-06-26` по safe simulation harness:
- подтверждена official schema через `https://api.elevenlabs.io/openapi.json` для:
  - `POST /v1/convai/agents/{agent_id}/simulate-conversation`
- practical schema result:
  - required tool-bound vars надо класть в:
    - `simulation_specification.dynamic_variables`
  - mocked webhook tools надо передавать в:
    - `simulation_specification.tool_mock_config`
    - как map по именам tools
- добавлен helper:
  - `scripts/run_eleven_simulation_probe_via_server_env.sh`
- helper уже умеет:
  - тянуть live Eleven API key с сервера;
  - принимать `PARTIAL_HISTORY_FILE`;
  - мокать `call_log`, `send_sms_info`, `context_fetch`;
  - сохранять `payload.json`, `response.json`, `summary.json`.
- первый рабочий probe:
  - `.runtime/sim_probe_attempt_2026-06-26_v2.json`
  - endpoint отработал валидно.
- затем поднят отдельный safe-case:
  - `.runtime/eleven_sim_post_opener_silence_2026-06-26/response.json`
- этот simulation показал:
  - после opener и `...` agent дал один rescue:
    - `Алло, вы на линии?`
  - потом:
    - `call_log(no_answer)`
    - silent `end_call(reason=no_answer)`
- это полезный вывод:
  - high-level silence logic в safe simulation сейчас выглядит правильно.
- но важное ограничение сохранилось:
  - `agent_metadata.branch_id = null`
  - `agent_metadata.version_id = null`
  - значит simulation всё ещё нельзя считать branch-specific truth для lab-ветки.
- ещё один полезный сигнал из simulation:
  - raw drafted `call_log` всё ещё может содержать placeholders:
    - `{{system__conversation_id}}`
    - `{{lead_id}}`
    - `{{caller}}`
  - поэтому simulation хорош для sequencing shape, но не заменяет live proof of fully bound tool payload.

Обновление `2026-06-26` по direct Tools API и `call_log.disable_interruptions`:
- добавлен helper:
  - `scripts/patch_eleven_tool_flags_via_server_env.sh`
- им был сделан прямой patch active shared custom tool:
  - `tool_5701ktec2x6wfnj8t5b1rwhtw51p`
  - это active `call_log`
- фактический результат direct tool patch:
  - до:
    - `disable_interruptions = false`
  - после:
    - `disable_interruptions = true`
- это важный practical вывод:
  - branch-level agent patch в нашем current branch ненадёжно удерживает этот флаг;
  - direct `PATCH /v1/convai/tools/{tool_id}` для custom webhook tool этот флаг удерживает.
- сразу после patch были два validation self-test:
  - `conv_8201kw1p0nvwef6b4ys9mm026gs3`
  - `conv_1101kw1p29btf0abz8q4ap17a604`
- оба failed до начала нормального transcript:
  - один на `SIP 404`
  - второй на `max auth retry attempts reached for SIP invite`
- значит:
  - tool-level patch подтверждён технически;
  - но его effect on `call_log -> end_call` sequencing пока ещё не доказан свежим живым transcript.
- current practical state now:
  - branch head всё ещё:
    - `agtvrsn_2201kw1nqdxdekhayx21qtwk6j7r`
  - active shared `call_log` уже patched direct-tool способом.

Обновление `2026-06-26` по manual disconnect, word-fill и finalclose lab-регрессии:
- уточнение по одному из последних спорных кейсов:
  - пользователь отдельно подтвердил, что тот конкретный ранний disconnect был ручным с его стороны, а не agent-side drop.
- после этого от strongest candidate `4401...` был сделан узкий pause-masking шаг:
  - helper:
    - `scripts/prepare_eleven_wordfill_pause_polish_variant.sh`
  - published version:
    - `agtvrsn_4701kw1naqy6f56vhp2n4949nf4w`
- что именно улучшали в `4701...`:
  - `soft_timeout_config.message = "Да..."`
  - filler override запрещает service-style fillers:
    - `Да, я на линии`
    - `Я на линии`
    - `Секунду...`
    - `Момент...`
    - любые line-check fillers
  - разрешены только короткие neutral fillers:
    - `Да...`
    - `Угу...`
    - `Так...`
- self-test `4701...`:
  - `conv_7401kw1ncgymfk4816sy0bjy6yep`
  - показал:
    - word-fill patch реально применился;
    - но главная проблема осталась уже не в музыке/тишине, а в finalization path:
      - `[calm]`
      - duplicate close
      - normal speech after `call_log`
      - длинный final tool-path gap
- затем был выпущен ещё один узкий patch:
  - published version:
    - `agtvrsn_2401kw1nhasnf6hv8nhf9t6keg32`
  - смысл:
    - plain-spoken final close
    - terminal gate after `call_log`
- self-test `2401...`:
  - `conv_6901kw1nhx5jf16rr02p7yefntmt`
  - показал уже явную lab-regression:
    - в transcript всплыл ранний `call_log` ещё до нормального opener path;
    - `[calm]` всё ещё не исчез;
    - `...` surfaced during finalization;
    - обычная spoken close после `call_log` всё ещё осталась.
- важный технический вывод:
  - payload builders для non-interruptible finalization реально выставляют:
    - `call_log.disable_interruptions = true`
    - `end_call.disable_interruptions = true`
  - но свежий live snapshot branch state по-прежнему показывает:
    - `disable_interruptions = false`
  - значит tool-level non-interruptibility пока не считается доказанно working в live branch.
- practical reading now:
  - `4701...` = полезный narrow gain по pause masking;
  - `2401...` = не safe winner, а regression candidate;
  - следующий цикл надо делать не по filler-лексике, а по раннему `call_log` и real finalization sequencing.
- после фиксации regression-run branch сразу возвращён назад на word-fill state:
  - current published lab head now:
    - `agtvrsn_2201kw1nqdxdekhayx21qtwk6j7r`
  - по содержанию это revert к `4701...`, а не продолжение `2401...`.

Обновление `2026-06-26` по turn-taking и terminal regression:
- после no-tool-music fix были проверены три версии:
  - `6201...` — убрали music-layer, включили spoken filler;
  - `4301...` — смягчили turn-taking;
  - `4501...` — пытались дожать terminal sequencing.
- `6201...` показал:
  - музыка уже не главный дефект;
  - главный defect теперь `turn_taking_or_dialogue_flow`.
- `4301...` показал:
  - opener path стал лучше;
  - появился более человеческий turn-taking:
    - `turn_timeout = 2.3`
    - `turn_eagerness = normal`
    - `interruption` есть в `client_events`
  - но не исчезли:
    - большие паузы после отказных ответов;
    - плохая finalization path.
- `4501...` признан плохой версией и больше не рабочая точка, потому что в live self-test он начал проговаривать tool-служебный текст:
  - `silent call_log with payload...`
- поэтому branch уже откатан обратно на safe head:
  - текущая безопасная published version:
    - `agtvrsn_6001kw1kg3d5fceajadfb0as0vnw`
- current safe head properties:
  - `gpt-5-mini`
  - `eleven_v3_conversational`
  - `turn_timeout = 2.3`
  - `turn_eagerness = normal`
  - `soft_timeout_seconds = 2.4`
  - spoken filler active
  - webhook tool-music disabled at shared-tool level
- важно для следующего агента:
  - `4501...` не использовать ни как rollback, ни как candidate winner;
  - следующий цикл делать только от `6001...`.

Дополнение `2026-06-26` по pre-opener / callback / single-close циклу:
- после `6001...` были сделаны ещё три узких шага:
  - `3501...` — pre-opener hard gate + negative fast-path
  - `9201...` — callback schedule gate
  - `1401...` — single-close refusal + no fake conv ids
- practical result:
  - `3501...` улучшил pre-opener path;
  - `9201...` дал лучший refusal-result этого цикла;
  - `1401...` не получил доказанного finished transcript и поэтому не принят как новая рабочая точка.
- поэтому текущий safe published head сейчас:
  - `agtvrsn_7701kw1mc5wzek0sddghnsta5cpv`
- по содержанию он равен последнему реально подтверждённому improved head `9201...`.
- что сейчас уже реально лучше по сравнению с предыдущими точками:
  - music/tool-sound слой убран;
  - turn-taking мягче;
  - `interruption` включён;
  - pre-opener `Алло?` стал лучше;
  - callback-ветка перестала так рано срываться в premature `call_log`.
- что осталось добить:
  - duplicate close перед `end_call`
  - normal speech after `call_log`
  - placeholder `conv_*` в drafted `call_log`
  - короткий final tool-path gap
- правило продолжения:
  - идти дальше только от `7701...`
  - не считать `1401...` рабочим head без подтверждённого finished live transcript.

Дополнение `2026-06-26` по refusal tool guard и non-interruptible finalization:
- после `7701...` были ещё два узких шага:
  1. `8701...`
     - убрал fake drafted `conv_*` из `call_log`
  2. `4401...`
     - сделал `call_log` и `end_call` non-interruptible
- factual result:
  - на `8701...` placeholder `conv_abcdef...` больше не всплыл;
  - на `4401...` analyzer в control run дал только `1` remaining issue:
    - `long_user_to_agent_gap`
  - при этом исчезли:
    - `duplicate_close_before_end_call`
    - `normal_assistant_speech_after_call_log`
    - `filler_during_finalization`
- current strongest candidate now:
  - `agtvrsn_4401kw1mty9qed7thk4bdwwnpetf`
- last fully proven safe fallback remains:
  - `agtvrsn_7701kw1mc5wzek0sddghnsta5cpv`
- важная оговорка:
  - `4401...` ещё нужно подтвердить отдельным finished-case на refusal/callback close,
  - потому что в текущем успешном run собеседник быстро оборвал разговор.
- practical continuation rule:
  - идти дальше уже от `4401...`
  - но safe rollback still keep at `7701...`

Обновление `2026-06-26` по паузам, музыке и spoken fillers:
- причина музыки найдена точно:
  - это был не фон TTS;
  - `background_sound = null`
  - музыка шла из webhook tool-layer:
    - `context_fetch`
    - `call_log`
    - `send_sms_info`
  - у них стояло:
    - `tool_call_sound = elevator3`
    - `tool_call_sound_behavior = always`
- одновременно было видно, что spoken filler по сути не работал как надо:
  - `soft_timeout_config.message = "Так..."`
  - `use_llm_generated_message = false`
- выпущен узкий patch:
  - `agtvrsn_6201kw1jmfrdejz8e0gk5b8x7xn5`
- в нём:
  - `gpt-5-mini`
  - `eleven_v3_conversational`
  - `turn_timeout = 1.78`
  - `soft_timeout_seconds = 2.4`
  - fallback filler теперь `Да...`
  - `use_llm_generated_message = true`
- отдельно shared tools пропатчены direct tool patch-ом:
  - `context_fetch`
  - `call_log`
  - `send_sms_info`
  теперь:
  - `tool_call_sound = null`
  - `tool_call_sound_behavior = auto`
- артефакты:
  - `.runtime/eleven_no_tool_music_2026-06-26/`
  - `.runtime/eleven_tool_sound_disable_2026-06-26/`
- важная тонкость для следующего агента:
  - общий agent snapshot после этого всё ещё может показывать старый embedded `elevator3`;
  - для sound-layer source-of-truth смотреть direct tool patch summary, а не только snapshot агента.
- practical meaning:
  - теперь длинные паузы должны закрываться коротким словом/filler-ом;
  - музыкальный tool-mask слой убран;
  - следующий шаг уже не поиск причины, а короткий self-test на реальном звонке.

Обновление `2026-06-25 12:05 MSK` по узкому callback-close patch:
- от safe-head `agtvrsn_0401kvyz7rxwek0ascbsx8det42f` выпущен отдельный очень узкий patch:
  - `agtvrsn_8601kvyzffdyf58bhf4knm6wk15m`
- для него добавлен отдельный builder:
  - `scripts/prepare_eleven_callback_close_override_variant.sh`
- смысл patch:
  - менять только helpdesk-tail на callback finalization;
  - не трогать opener, rescue, machine-stop и SMS-логику.
- проверочный звонок:
  - `conv_9401kvyzg726f6qvrk7vskh1vcpv`
- что он показал:
  - новая версия не свалилась в tool-speech regression;
  - `silent call_log ...` как spoken text не появился;
  - `[calm]` в этом тесте тоже не вылез;
  - но сам звонок ушёл в pronunciation-correction flow, а не в callback terminal flow.
- значит:
  - версия `8601...` пока выглядит безопасной;
  - но callback-tail `Могу чем-то ещё помочь?` именно на target-case ещё не подтверждён и не снят окончательно.
- практический следующий шаг теперь очень узкий:
  1. один controlled-звонок именно под реплики:
     - `перезвоните позже`
     - `сейчас неудобно`
     - `я занят, давайте потом`
  2. проверять только:
     - ушёл ли helpdesk-tail после callback finalization.

- дополнительный controlled test на `8601...` уже был:
  - `conv_6901kvz1bwyye11skyebrrj42w9p`
- он показал:
  - `8601...` не скатился в tool-speech regression;
  - но разговор снова ушёл в SMS-сценарий, а не в callback terminal path.
- значит:
  - сам callback-close patch пока не опровергнут;
  - но и не подтверждён на нужном target-case;
  - следующий тест должен быть именно callback-only по сценарию, без ухода в SMS.

Обновление `2026-06-25 11:50 MSK` по controlled cycle после возврата ключа:
- проведён короткий live-цикл с разбором нескольких controlled-звонков:
  - `conv_8901kvyyr24cee28s4zxwkwc3t24`
  - `conv_4501kvyyz89wfq88gyqrt833b5nm`
  - `conv_2201kvyz4kf6e9avc45fvqc7kxjr`
- для точечных published-правок добавлен builder:
  - `scripts/prepare_eleven_late_rescue_sms_fastlane_variant.sh`
- что проверили по факту:
  - старый published `9601...` реально снова звонит;
  - там подтверждены:
    - поздний `Алло?` после уже живого диалога;
    - spoken `Секунду...` перед `send_sms_info`;
    - дублирующийся SMS close tail.
- затем был выпущен узкий patch:
  - `agtvrsn_7601kvyyy5sce6xarqwa6nsj7kcy`
- его эффект:
  - поздний `Алло?` в SMS-сценарии ушёл;
  - explicit SMS-ветка стала лучше;
  - но остались:
    - `[calm]` в spoken text;
    - callback tail:
      - `Могу чем-то ещё помочь?`
- затем была сделана вторая, более жёсткая версия:
  - `agtvrsn_6501kvyz3x23f0ktzbjr2aw52g07`
- она признана плохой и больше не является рабочей точкой, потому что:
  - агент начал проговаривать tool-инструкции как обычную речь:
    - `silent call_log with refusal_soft ...`
- после этого выполнен safe revert.

- текущий безопасный published head сейчас:
  - `agtvrsn_0401kvyz7rxwek0ascbsx8det42f`
- подтверждение:
  - `.runtime/eleven_live_snapshot_2026-06-25_after_revert_safe/summary.json`
- текущее practical reading:
  - звонки снова можно делать в controlled-режиме;
  - quota уже не active blocker;
  - relay/webhook живы;
  - но следующий цикл надо вести очень узко, без агрессивного смешивания:
    - late rescue
    - callback close
    - terminal tool phrasing
    в одном patch.

- важное правило на сейчас:
  1. source-of-truth для safe live-head:
     - `agtvrsn_0401kvyz7rxwek0ascbsx8det42f`
  2. version `6501...` не использовать как rollback point;
  3. следующий цикл начинать только с одного controlled-звонка;
  4. править отдельно:
     - либо callback finalization tail,
     - либо bracketed stage directions,
     - но не всё сразу.

Обновление `2026-06-25 11:05 MSK` по возврату живого Eleven key:
- был выполнен один controlled live self-test через:
  - `scripts/run_eleven_live_cycle.sh`
- артефакты:
  - `.runtime/eleven_key_restore_probe_2026-06-25_call_01/selftest/`
- новый conversation реально создался и дошёл:
  - `conv_1701kvywnxy1fb9bm40n263y709v`
  - `status = done`
  - `call_successful = success`
  - `version_id = agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
  - `version_matches_expected = true`
- это подтверждает:
  - новый live key реально рабочий;
  - outbound через local relay снова проходит;
  - published branch реально исполняется.
- после этого был уточнён readiness-скрипт:
  - `scripts/report_eleven_live_readiness.sh`
- зачем:
  - раньше он продолжал писать `quota_blocker_active`, даже когда новый последний звонок уже был успешным;
  - это путало фактическое состояние с историческим следом старых quota-fail.
- теперь свежий readiness:
  - `.runtime/eleven_live_readiness_2026-06-25_latest_status/live_readiness_summary.json`
  показывает:
  - `latest_conversation = conv_1701kvywnxy1fb9bm40n263y709v`
  - `call_attempt_recommendation = quota_pressure_seen_verify_before_call`
  - `checks.calls_should_be_blocked_now = false`
  - `overall_diagnosis = quota_pressure_seen_history_only`
- practical meaning:
  - historical quota-pressure в истории branch ещё виден;
  - но это уже не active blocker;
  - live-контур снова годится для controlled calls.
- важное текущее правило:
  1. не переходить сразу в массовый дозвон;
  2. идти короткими циклами `1-3` звонка;
  3. после каждого звонка разбирать:
     - `runtime_diagnosis.json`
     - `conversation_poll_final.json`
     - свежий readiness
  4. дальше уже снова фокус на качество:
     - voicemail / machine stop;
     - задержка;
     - premature hangup;
     - turn-taking.

Обновление `2026-06-25 10:35 MSK` по свежему live refresh и восстановлению relay:
- сначала был снят новый полный refresh:
  - `bash scripts/refresh_eleven_control_tower.sh --with-fetch --date-tag 2026-06-25`
- он подтвердил, что current published branch всё ещё тот же:
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - `version_id = agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
  - `llm = gpt-5-mini`
  - `tts = eleven_v3_conversational`
  - `turn_timeout = 1.78`
  - `soft_timeout_seconds = 1.9`
- затем выявилось, что локальный relay runtime-контур был не в норме:
  - local stack был down;
  - public relay health отвечал `503`;
  - workflow URL отставал от текущего tunnel URL
- после этого relay был поднят заново через:
  - `bash scripts/start_eleven_local_relay_stack.sh`
- свежий state теперь такой:
  - `/home/max/.config/lipolong-eleven-relay-state.json`
  - `relay_url = https://08c619650e448a.lhr.life/eleven/outbound-call`
- свежий readiness после восстановления:
  - `2026-06-25_after_stack_recover_retry/live_readiness_summary.json`
  уже показывает:
  - `workflow_matches_state = true`
  - `public_health_ok = true`
  - `local_stack_running = true`
  - `calls_should_be_blocked_now = true`
  - `overall_diagnosis = quota_blocker_active`
- это значит:
  - webhook/relay-контур на `2026-06-25` уже снова исправен;
  - текущий настоящий блокер не tunnel, а именно квота ElevenLabs.
- свежий quota preflight:
  - `.runtime/eleven_quota_preflight_2026-06-25_check_now/eleven_quota_preflight_summary.json`
  подтверждает:
  - `call_attempt_recommendation = do_not_call_until_quota_is_restored`
  - последний blocking conversation всё ещё:
    - `conv_1201kvdae8fxf779k0deagwst8b6`
    - `termination_reason = This request exceeds your quota limit.`
    - `start_time_utc = 2026-06-18T12:14:23Z`
    - это `2026-06-18 15:14:23 MSK`
- subscription endpoint через текущий live key всё ещё не даёт billing-снимок:
  - `missing_permissions`
  - отсутствует право `user_read`
- practical rule на сейчас:
  1. не запускать новые live/self-test звонки;
  2. если снова покажется, что "обзвон не стартует", сначала смотреть readiness, а не сразу prompt;
  3. если relay опять упал:
     - `bash scripts/start_eleven_local_relay_stack.sh`
     - потом `bash scripts/report_eleven_live_readiness.sh <date_tag>`
  4. как только квота реально восстановится:
     - сначала `readiness`
     - потом `1` короткий self-test
     - и только потом следующий живой цикл.

Обновление `2026-06-18 16:15 MSK` по свежей перепроверке квоты и official-doc alignment:
- добавлен стабильный короткий вход в актуальное состояние без привязки к дате:
  - `.runtime/eleven_control_tower_latest/`
  - основной файл:
    - `.runtime/eleven_control_tower_latest/operational_brief.md`
  - новый быстрый файл именно для выбора следующего lab-кандидата:
    - `.runtime/eleven_control_tower_latest/next_variant_advisor.md`
- прямо сейчас quota blocker всё ещё активен:
  - `.runtime/eleven_quota_preflight_2026-06-18_check_now/eleven_quota_preflight_summary.json`
  - `.runtime/eleven_live_readiness_2026-06-18_check_now/live_readiness_summary.json`
- по факту:
  - `call_attempt_recommendation = do_not_call_until_quota_is_restored`
  - `overall_diagnosis = quota_blocker_active`
  - последний blocking call всё ещё:
    - `conv_1201kvdae8fxf779k0deagwst8b6`
    - `termination_reason = This request exceeds your quota limit.`
    - `start_time_utc = 2026-06-18T12:14:23Z`
    - это `2026-06-18 15:14:23 MSK`
- subscription billing endpoint через текущий ключ не читается из-за:
  - `missing_permissions`
  - отсутствует право `user_read`
- это не ломает вывод:
  - диагноз подтверждается историей реальных failed conversations, а не только billing endpoint.
- обновлён official-doc advisory:
  - `.runtime/eleven_docs_alignment_2026-06-18.json`
- что теперь важно держать в голове по current published `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`:
  - `turn_timeout = 1.78`
  - `turn_eagerness = eager`
  - `client_events` без `interruption`
  - `soft_timeout_seconds = 1.9`
  - filler prompt всё ещё содержит time-promise пример `Секунду...`
- practical meaning:
  - жалоба `она не даёт мне сказать` сейчас лучше всего объясняется не голосом как таковым, а комбинацией:
    - aggressive turn-taking;
    - выключенных interruptions;
    - слишком раннего filler masking.
- offline comparator тоже уже исправлен:
  - `scripts/compare_eleven_candidate_runs.py`
  - теперь он сначала предпочитает runs с полным `timing_summary`, и только потом сравнивает их score.
- дополнительно уже собран второй lab-вариант под следующий цикл:
  - `.runtime/eleven_interruptible_softfill_variant_2026-06-18.json`
  - он:
    - оставляет `turn_timeout = 2.3`
    - ставит `turn_eagerness = normal`
    - включает `interruption`
    - поднимает `soft_timeout` до `2.4`
    - убирает из filler prompt time-promise примеры вроде `Секунду...`
    - вместо этого ориентирует fillers на `Да... / Так... / Угу...`
- дополнительно уже собран и третий lab-вариант для более позднего filler-start:
  - `.runtime/eleven_interruptible_latefill_variant_2026-06-18.json`
  - он:
    - сохраняет `turn_timeout = 2.3`
    - сохраняет `turn_eagerness = normal`
    - включает `interruption`
    - поднимает `soft_timeout` до `3.0`
    - оставляет нейтральный filler `Да...`
    - тоже убирает time-promise лексику из filler prompt
- post-quota pack тоже уже пересобран под этот порядок:
  - `.runtime/eleven_post_quota_test_pack_2026-06-18/`
  - теперь там есть 4 осмысленных payload-кандидата:
    - `payload_interruptible_balanced.json`
    - `payload_interruptible_softfill.json`
    - `payload_interruptible_latefill.json`
    - `payload_repeatable_fallback.json`
  - и теперь же есть локальный self-check:
    - `validate_variants.sh`
    - `variant_checks/`
  - и уже вложен короткий общий бриф состояния:
    - `operational_brief.md`
    - `operational_brief.json`
- чтобы не проверять это вручную каждый раз, добавлены ещё 2 offline-helper'а:
  - `scripts/check_eleven_turn_variant_invariants.py`
  - `scripts/report_eleven_turn_variant_matrix.py`
- их свежие артефакты уже лежат в:
  - `.runtime/eleven_turn_variant_checks_2026-06-18/`
- practical reading по matrix:
  - `published_current`:
    - interruptions off
    - time-promise filler markers present
  - `interruptible_balanced`:
    - interruptions on
    - time-promise filler markers still present
  - `interruptible_softfill`:
    - interruptions on
    - time-promise filler markers removed
  - `interruptible_latefill`:
    - interruptions on
    - time-promise filler markers removed
    - filler masking starts later (`soft_timeout = 3.0`)
- practical rule после возврата квоты:
  1. сначала `validate_variants.sh`
  2. потом readiness
  3. только потом живой self-test
  4. если published current слаб по barge-in:
     - `interruptible_balanced`
  5. если barge-in уже лучше, но filler всё ещё звучит слишком рано:
     - `interruptible_softfill`
  6. если filler всё ещё стартует чуть рановато:
     - `interruptible_latefill`
- если нужен самый короткий вход в контекст без чтения длинных handoff-файлов:
  - сначала открыть:
    - `.runtime/eleven_control_tower_latest/operational_brief.md`
- если нужен быстрый ответ "что пробовать следующим по типу жалобы":
  - открыть:
    - `.runtime/eleven_control_tower_latest/next_variant_advisor.md`
  - но помнить:
    - этот `latest`-файл без audit-входа показывает baseline порядок;
    - targeted advice по конкретному звонку надо брать из run-папки или генерировать helper'ом
  - или запустить helper из pack:
    - `recommend_next_variant.sh`
  - он умеет принимать:
    - `finalization_audit.json`
    - run-папку с `finalization_audit.json`
    - или просто текст жалобы
- `run_eleven_selftest_audit.sh` теперь уже сам после аудита пишет:
  - `next_variant_advice.json`
  - `next_variant_advice.md`
  рядом с run-артефактами
- Если в advice стоит:
  - `ready_for_variant_testing = false`
  это означает:
  - не надо сразу крутить новый variant;
  - сначала надо выполнить fix-before-variant шаг из `action_plan`
- если нужен короткий checkpoint именно про новый entrypoint:
  - открыть:
    - `docs/checkpoints/2026-06-18_ELEVEN_CONTROL_TOWER_ENTRYPOINT.md`
- если нужен полный пересбор engineering-state одной командой:
  - `./scripts/refresh_eleven_control_tower.sh`
- если перед этим нужно ещё и снять свежий snapshot из live Eleven:
  - `./scripts/refresh_eleven_control_tower.sh --with-fetch`

Обновление `2026-06-18 15:55 MSK` по квоте Eleven и жёсткому guard:
- свежий preflight:
  - `.runtime/eleven_quota_preflight_2026-06-18_now_guard/eleven_quota_preflight_summary.json`
  показывает:
  - `diagnosis = provider_quota_limit_observed_recently`
  - `call_attempt_recommendation = do_not_call_until_quota_is_restored`
  - последний blocking call:
    - `conv_1201kvdae8fxf779k0deagwst8b6`
    - `version_id = agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
    - `termination_reason = This request exceeds your quota limit.`
    - `start_time_utc = 2026-06-18T12:14:23Z`
    - это `2026-06-18 15:14:23 MSK`
    - `age_minutes = 40` на момент отчёта
- свежий readiness:
  - `.runtime/eleven_live_readiness_2026-06-18_guard/live_readiness_summary.json`
  теперь прямо показывает:
  - `workflow_matches_state = true`
  - `public_health_ok = true`
  - `local_stack_running = true`
  - `calls_should_be_blocked_now = true`
  - `overall_diagnosis = quota_blocker_active`
- live-cycle guard тоже уже проверен:
  - `.runtime/eleven_live_cycle_quota_guard_2026-06-18/live_cycle_summary.json`
  - он завершает цикл до звонка с:
    - `action = stopped_before_call`
    - `reason = quota_pressure_guard`
- practical meaning:
  - инфраструктура сейчас живая;
  - звонки блокировать правильно;
  - до пополнения квоты новые outbound/self-test не запускать.

Обновление `2026-06-18 16:05 MSK` по выбору лучшей lab-базы после восстановления квоты:
- обновлён рейтинг версий:
  - `.runtime/eleven_lab_version_leaderboard_2026-06-18.json`
- теперь там есть не только общий список, но и отдельные блоки:
  - `best_repeatable_candidates`
  - `best_single_run_candidates`
- главный practical result:
  - лучший `repeatable` кандидат сейчас:
    - `agtvrsn_0901kva21515f08v6xn9w3v05zg3`
    - подтверждён `2` strong-разговорами
  - лучший `single-run` кандидат сейчас:
    - `agtvrsn_5501kv8bkjkffjna37fq79vd5c7j`
    - но он пока опирается только на `1` разговор
- current published version:
  - `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
  пока нельзя честно проверить новыми звонками из-за quota blocker.
- practical rule на следующий живой цикл:
  1. после пополнения квоты сначала один self-test на `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`;
  2. если published current даст слабый результат, основным fallback-кандидатом считать:
     - `agtvrsn_0901kva21515f08v6xn9w3v05zg3`
  3. `agtvrsn_5501kv8bkjkffjna37fq79vd5c7j` не считать главной базой без повторного подтверждения.

Обновление `2026-06-18 16:18 MSK` по official-doc alignment:
- свежий advisory:
  - `.runtime/eleven_docs_alignment_2026-06-18.json`
- он показал по текущей published version `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`:
  - `turn_timeout = 1.78`
  - `turn_eagerness = eager`
  - `client_events` без `interruption`
- practical meaning:
  - interruptions, вероятно, сейчас выключены;
  - при этом turn-taking очень агрессивный;
  - это хорошо объясняет жалобу:
    - `она не даёт мне сказать`
- voice layer при этом не выглядит главным виновником:
  - `stability = 0.42`
  - `similarity_boost = 0.78`
  - `speed = 1.08`
- уже подготовлен lab-only payload на следующий цикл:
  - `.runtime/eleven_interruptible_balanced_variant_2026-06-18.json`
  - там:
    - `turn_timeout = 2.3`
    - `turn_eagerness = normal`
    - `client_events` уже включают `interruption`
- practical rule:
  - после пополнения квоты первым тестом проверять именно этот human-barge-in / turn-taking variant против текущей published `9601...`, а не начинать с очередной косметики голоса.

Обновление `2026-06-18 16:27 MSK` по post-quota execution pack:
- собран готовый пакет:
  - `.runtime/eleven_post_quota_test_pack_2026-06-18/`
- ключевые файлы:
  - `manifest.json`
  - `run_commands.sh`
  - `payload_interruptible_balanced.json`
  - `payload_repeatable_fallback.json`
- логика этого пакета:
  1. readiness после пополнения квоты;
  2. self-test текущей published `9601...`;
  3. apply + self-test `interruptible_balanced`;
  4. при необходимости apply + self-test repeatable fallback `0901...`.
- важно:
  - `run_commands.sh` теперь сам останавливается, если readiness всё ещё показывает:
    - `overall_diagnosis = quota_blocker_active`
  - то есть случайно раньше времени он self-test не продолжит.
- practical meaning:
  - следующий живой инженерный цикл уже собран как готовый execution pack;
  - после восстановления квоты не нужно заново руками вспоминать порядок, payload и команды.

Обновление `2026-06-18 16:02 MSK` по batch-аудиту серии разговоров:
- добавлен:
  - `scripts/analyze_eleven_conversation_batch.py`
- готовый summary по серии:
  - `.runtime/eleven_lab_golden_confirm_2026-06-17/batch_audit_summary.json`
- по `5` разговорам уже видно:
  - `long_user_to_agent_gap = 18`
  - `duplicate_close_before_end_call = 7`
  - `placeholder_conversation_id_in_tool_call = 6`
  - `final_close_spoken_before_call_log = 5`
- а по bottleneck-слою:
  - `turn_taking_or_dialogue_flow = 15`
  - `tool_path = 2`
  - `llm_generation = 1`
- practical meaning:
  - следующий рабочий цикл после снятия квоты нужно вести сначала в:
    - `focus_turn_taking`
    - `single_close_only`
    - `fix_tool_identity_binding`
    - `no_normal_speech_after_call_log`
    - `remove_late_line_checks`
  - а не начинать с косметического voice-polish.
- на более широкой lab-серии:
  - `.runtime/eleven_all_lab_batch_summary_2026-06-18.json`
  уже видно:
  - `conversations_analyzed = 49`
  - `turn_taking_or_dialogue_flow = 185`
  - `tool_path = 16`
  - `llm_generation = 6`
  - это ещё сильнее подтверждает тот же порядок приоритетов.

Обновление `2026-06-18 15:44 MSK` по offline-аудиту задержек:
- пока live self-test всё ещё упирается в quota blocker Eleven, усилен локальный разбор сохранённых разговоров:
  - `scripts/analyze_eleven_conversation.py`
- теперь он показывает не только structural проблемы, но и timing-summary:
  - `first_user_to_agent_gap_secs`
  - `user_to_agent_gap_stats_secs`
  - `known_path_stats_secs`
  - `unexplained_overhead_stats_secs`
  - `primary_bottleneck_counts`
  - `llm_ttfb_stats_secs`
  - `tts_ttfb_stats_secs`
- wrapper:
  - `scripts/run_eleven_selftest_audit.sh`
  теперь тоже печатает эти цифры в коротком summary.
- и теперь же печатает:
  - `top_recommendations`
  то есть 2-3 главных инженерных следующих шага по конкретному разговору.
- уже есть практический вывод на сохранённых разговорах:
  - старый opener-кейс:
    - `.runtime/single_call_2026-06-06_row_8_opener_or_conv_check/conv_2701ktdzmjz7fxqrmfczhea65r56.json`
    дал:
    - `first_user_to_agent_gap_secs = 4.0`
    - при этом raw generation layer был заметно быстрее:
      - `llm_ttfb ≈ 0.476s`
      - `tts_ttfb ≈ 0.351s`
  - длинный lab-кейс:
    - `.runtime/eleven_lab_mid_dialogue_reassurance_trim_2026-06-17/call_01_verify/conversation_poll_final.json`
    дал:
    - `user_to_agent_gap_stats_secs.max = 12.0`
    - `user_to_agent_gap_stats_secs.avg = 6.5`
    - `known_path_stats_secs.avg = 1.818`
    - `unexplained_overhead_stats_secs.avg = 4.682`
    - `unexplained_overhead_stats_secs.max = 10.907`
    - `primary_bottleneck_counts`:
      - `turn_taking_or_dialogue_flow = 5`
      - `tool_path = 1`
    - при этом:
      - `llm_ttfb_stats_secs.avg ≈ 0.809`
      - `tts_ttfb_stats_secs.avg ≈ 0.342`
- top recommendations там уже получаются такими:
  - `focus_turn_taking`
  - `remove_late_line_checks`
  - `single_close_only`
- practical meaning:
  - даже когда LLM и TTS сами по себе не очень медленные, пользователь всё равно может слышать длинную паузу;
  - значит следующий target после восстановления квоты — это не только модель, а ещё:
    - turn-taking;
    - rescue logic;
    - финализационные хвосты;
    - лишние tool transitions.

Обновление `2026-06-18 15:27 MSK` по текущей ветке агента и реальному blocker:
- повторно снят свежий snapshot текущей ветки через:
  - `scripts/fetch_eleven_agent_snapshot_via_server_env.sh`
- актуальный артефакт:
  - `.runtime/eleven_current_branch_snapshot_2026-06-18_now/summary.json`
- по нему сейчас подтверждено:
  - `agent_id = agent_8801kgybyekned2a8yae6rp8hk3q`
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - `version_id = agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
  - `llm = gpt-5-mini`
  - `tts = eleven_v3_conversational`
  - `turn_timeout = 1.78`
  - `soft_timeout_seconds = 1.9`
  - tools:
    - `context_fetch`
    - `call_log`
    - `send_sms_info`
    - `end_call`
    - `skip_turn`
    - `voicemail_detection`
- локальный checker:
  - `scripts/check_eleven_prompt_invariants.py`
  синхронизирован с этой живой нормой;
- свежая проверка опубликованной ветки:
  - `.runtime/eleven_current_branch_snapshot_2026-06-18_now/invariants.json`
  показала:
  - `43/43 ok`
  - `checks_failed = 0`
- параллельно свежий readiness:
  - `.runtime/eleven_live_readiness_2026-06-18_now/live_readiness_summary.json`
  снова показывает:
  - `public_health_ok = true`
  - `local_stack_running = true`
  - `workflow_matches_state = true`
  - `alternate_named_eleven_credential_detected = false`
  - `quota_fail_count = 13`
  - `overall_diagnosis = quota_blocker_active`
- practical meaning:
  - route жив;
  - branch prompt-state жив;
  - главный стоп сейчас всё ещё именно внешняя квота Eleven.
- что делать дальше:
  1. не запускать новые live self-test как будто broken именно prompt;
  2. после восстановления лимита первым делать короткий `local_relay-first` self-test;
  3. если нужно быстро проверить, что ветка агента не “уплыла”, использовать:
     - `fetch_eleven_agent_snapshot_via_server_env.sh`
     - `check_eleven_prompt_invariants.py`
     вместо ручного чтения большого JSON.

Обновление `2026-06-18 15:12 MSK` по live route и квоте:
- сейчас живой local relay снова поднят на:
  - `127.0.0.1:18787`
- живой public tunnel на момент этой контрольной точки:
  - `https://29d29137388b89.lhr.life/eleven/outbound-call`
- live workflow:
  - `sHTbALayEZdy8Mzs`
  уже смотрит именно в этот URL;
- readiness snapshot:
  - `.runtime/eleven_live_readiness_2026-06-18_live_sessions/live_readiness_summary.json`
  показывает:
  - `workflow_matches_state = true`
  - `public_health_ok = true`
  - `overall_diagnosis = quota_blocker_active`
- practical meaning:
  - инфраструктурно live route сейчас собран;
  - это уже не проблема tunnel, не проблема `workflow_entity/history` и не проблема dispatcher-path.
- затем снят принудительный self-test:
  - `.runtime/eleven_live_cycle_forced_2026-06-18_onecall/`
  - там видно, что старый transport `relay_via_server` всё ещё может попадать в:
    - `cloudflare_challenge`
    - help-page вместо JSON.
- но более важный факт подтверждён отдельным direct probe в local relay:
  - POST на `127.0.0.1:18787/eleven/outbound-call`
  вернул:
  - `success = true`
  - `Outbound call initiated`
  - `conversation_id = conv_9801kvda6zckfmp9jds52x52yp9w`
- этот conversation затем дочитан через Eleven API и уже там видно:
  - `status = failed`
  - `termination_reason = This request exceeds your quota limit.`
  - `error.code = 1002`
- practical meaning:
  - local egress рабочий;
  - звонок инициируется;
  - но финальный live stop сейчас снова именно квота Eleven.
- дополнительно обновлён self-test script:
  - `scripts/run_eleven_branch_selftest.sh`
  теперь по умолчанию идёт так:
  - `local_relay -> relay_via_server -> relay -> webhook`
  а не server-first, чтобы тест отражал реальный текущий рабочий путь.
- что делать дальше:
  1. не тратить новые циклы на tunnel/draft dispatcher;
  2. сначала решить quota blocker Eleven;
  3. после восстановления лимита снова делать короткий self-test уже через `local_relay` как основной transport.

Обновление `2026-06-18 15:17 MSK` по launcher и self-test:
- теперь `scripts/run_eleven_branch_selftest.sh` по умолчанию идёт в порядке:
  - `local_relay -> relay_via_server -> relay -> webhook`
- подтверждённый run:
  - `.runtime/eleven_localrelay_first_2026-06-18/`
  уже реально прошёл через:
  - `transport = local_relay`
  и вернул честный итог:
  - `diagnosis = provider_quota_limit`
  - `conversation_id = conv_1201kvdae8fxf779k0deagwst8b6`
- это важно, потому что старый server-first путь мог уводить нас в:
  - `cloudflare_challenge`
  хотя основной local path уже был живой.
- отдельно восстановлен штатный launcher:
  - `scripts/start_eleven_local_relay_stack.sh`
- practical fix:
  - relay теперь стартует detached через `setsid python3 ...`
  - tunnel теперь стартует detached через `setsid script -qefc ...`
- после этого stack действительно остаётся жить после завершения стартовой команды.
- текущий живой public URL после launcher-подъёма:
  - `https://0087b8fcfbdd94.lhr.life/eleven/outbound-call`
- подтверждённый readiness:
  - `.runtime/eleven_live_readiness_2026-06-18_detached_launcher/live_readiness_summary.json`
  показывает:
  - `workflow_matches_state = true`
  - `public_health_ok = true`
  - `overall_diagnosis = quota_blocker_active`
- practical meaning:
  - live route восстановлен уже штатным способом;
  - self-test восстановлен и теперь честно смотрит в рабочий path;
  - главный внешний стоп по-прежнему только квота Eleven.

Обновление `2026-06-18 15:20 MSK` по readiness:
- `scripts/report_eleven_live_readiness.sh` теперь показывает не только route/health, но ещё:
  - `config_inventory`
  - `runtime_stack`
- подтверждённый snapshot:
  - `.runtime/eleven_live_readiness_2026-06-18_inventory/live_readiness_summary.json`
  сейчас показывает:
  - `public_health_ok = true`
  - `local_stack_running = true`
  - `workflow_matches_state = true`
  - `overall_diagnosis = quota_blocker_active`
- текущий живой tunnel на момент этого snapshot:
  - `https://96e9645631456d.lhr.life/eleven/outbound-call`
- по `config_inventory` теперь прямо видно:
  - обе server env mirror-конфигурации содержат `ELEVENLABS_API_KEY` и `ELEVEN_OUTBOUND_RELAY_TOKEN`
  - в `n8n` найден только один named Eleven credential:
    - `ElevenLabs XI API`
  - readiness отдельно фиксирует:
    - `alternate_named_eleven_credential_detected = false`
- practical meaning:
  - запасной named credential сейчас не подтверждён;
  - маршрут и локальный stack живы;
  - главный stop остаётся во внешней квоте Eleven, а не в маршруте и не в конфиге `n8n`.

Обновление `2026-06-18 12:48 MSK` по live tunnel и runtime recovery:
- local relay остаётся живым на:
  - `127.0.0.1:18787`
- public tunnel сменился:
  - старый:
    - `https://077b96f77ded60.lhr.life/eleven/outbound-call`
    уже мёртв;
  - новый рабочий:
    - `https://fd7bdf984512a5.lhr.life/eleven/outbound-call`
- live workflow:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `sHTbALayEZdy8Mzs`
  уже точечно переведён на новый `fd7b...` URL и в:
  - `workflow_entity`
  - и в active `workflow_history`
- после этого live webhook снова реально доходит до relay и создаёт outbound-init в Eleven;
- это уже подтверждено relay логом:
  - `Upstream 200`
  - `Outbound call initiated`
- отдельный важный практический шаг:
  - `scripts/run_eleven_branch_selftest.sh` теперь умеет восстанавливать разговор даже если webhook вернул пустое тело;
  - recovery теперь идёт:
    - сначала по `user_id + branch_id`;
    - затем по recent branch history;
    - с короткими retry.
- подтверждённый артефакт:
  - `.runtime/eleven_local_tunnel_cutover_2026-06-18_resume/call_07_webhook_tunnel_branch_retry/`
  - helper сам восстановил:
    - `conv_9501kvd22c3hfrn9nqry1cg6t8sc`
    - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
    - `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
- practical meaning:
  - текущий стоп уже не в старом tunnel URL;
  - не в том, что webhook route "не доходит";
  - и не в том, что helper "не видит" разговор;
  - текущий следующий узкий блок — уже post-init поведение самого Eleven после `Outbound call initiated`.
- отдельное важное уточнение:
  - по свежим lab-call list API уже прямо показывает:
    - `conv_1601kvd1wrdhf89beweq56y0v3pq`
    - `conv_5301kvd1zyb2emgtk2p7g5jbezhj`
    - `conv_7901kvd29vy1fxq835szb2wvj89f`
    - `conv_9501kvd22c3hfrn9nqry1cg6t8sc`
    завершились как:
    - `termination_reason = This request exceeds your quota limit.`
  - то есть текущий live-блок уже не route/tunnel, а упор в квоту Eleven после успешного outbound-init.
  - practical improvement:
    - `scripts/run_eleven_branch_selftest.sh` теперь сам выносит это в:
      - `runtime_diagnosis.json`
      как:
      - `diagnosis = provider_quota_limit`
    - свежий подтверждённый пример:
      - `.runtime/eleven_local_tunnel_cutover_2026-06-18_resume/call_08_quota_surface/`

Обновление `2026-06-18 12:57 MSK` по preflight-проверке квоты:
- добавлен новый helper:
  - `scripts/report_eleven_quota_preflight.sh`
- теперь перед live self-test можно отдельно, без звонка, снять:
  - raw `user/subscription` snapshot;
  - recent branch conversations;
  - итоговый `eleven_quota_preflight_summary.json`
- practical reality на текущем live key:
  - `GET /v1/user/subscription` не даёт полный subscription snapshot,
    потому что ключу не хватает:
    - `user_read`
  - но recent branch history при этом доступна и уже даёт честный сигнал:
    - `provider_quota_limit_observed_recently`
- подтверждённый standalone-артефакт:
  - `.runtime/eleven_quota_preflight_2026-06-18/eleven_quota_preflight_summary.json`
  - в нём видно:
    - `quota_fail_count = 10`
    - warning про `missing_permissions`
    - diagnosis про quota pressure
- helper уже встроен в:
  - `scripts/run_eleven_branch_selftest.sh`
  - теперь каждый run складывает в себя:
    - `preflight/`
- подтверждённый интеграционный run:
  - `.runtime/eleven_local_tunnel_cutover_2026-06-18_resume/call_09_preflight_integration/`
  - внутри одновременно есть:
    - `preflight/eleven_quota_preflight_summary.json`
    - `runtime_diagnosis.json`
  - и оба файла согласованно показывают quota issue.

Обновление `2026-06-18 13:04 MSK` по tunnel sync:
- helper `scripts/localhost_run_tunnel_sync.py` доведён до рабочего live-режима;
- теперь он не пытается патчить только через n8n API, а работает через:
  - `server_postgres`
- текущий target:
  - workflow:
    - `sHTbALayEZdy8Mzs`
  - node:
    - `Eleven | Outbound HTTP`
- practical behavior:
  - при новом домене `localhost.run` helper:
    - ловит новый public URL;
    - через `ssh` идёт на `ai-core-prod-147`;
    - берёт DB credentials из live `n8n-server-n8n-1`;
    - обновляет URL сразу в:
      - `workflow_entity`
      - active `workflow_history`
    - пишет state в:
      - `/home/max/.config/lipolong-eleven-relay-state.json`
- helper уже проверен no-op патчем на текущий live URL:
  - `https://fd7bdf984512a5.lhr.life/eleven/outbound-call`
  - он вернул `ok = true`
  - readback из live Postgres подтвердил тот же URL
- practical meaning:
  - следующий срыв из-за “tunnel сменился, а workflow смотрит в старый домен” теперь можно закрывать штатным helper-ом, а не ручным SQL.

Обновление `2026-06-18 13:12 MSK` по live-cycle guard:
- добавлен верхнеуровневый script:
  - `scripts/run_eleven_live_cycle.sh`
- он собирает в один controlled запуск:
  - `report_eleven_quota_preflight.sh`
  - repatch relay URL из state file
  - `run_eleven_branch_selftest.sh`
- default behavior теперь безопасный:
  - если preflight уже показывает
    - `provider_quota_limit_observed_recently`
  то script не делает звонок вообще
  и завершает цикл как:
    - `stopped_before_call`
    - `quota_pressure_guard`
- подтверждённый артефакт:
  - `.runtime/eleven_live_cycle_guard_2026-06-18/`
  - там есть:
    - `live_cycle_summary.json`
    - `preflight_gate/*`
    - `state_repatch_result.json`
  - и нет следов реального selftest-call
- practical meaning:
  - это уже штатный безопасный entrypoint для live self-test;
  - при текущей квоте он корректно удерживает нас от лишнего звонка;
  - после восстановления лимита именно его лучше использовать первым.

Обновление `2026-06-18 14:56 MSK` по readiness-report:
- добавлен новый operational script:
  - `scripts/report_eleven_live_readiness.sh`
- он снимает в один summary:
  - quota preflight;
  - текущий `localhost.run` state file;
  - health public relay URL;
  - текущий URL в live workflow `sHTbALayEZdy8Mzs`
- подтверждённый артефакт:
  - `.runtime/eleven_live_readiness_2026-06-18/live_readiness_summary.json`
- текущая реальность по этому report:
  - `quota_preflight.diagnosis = provider_quota_limit_observed_recently`
  - `quota_fail_count = 11`
  - `workflow_matches_state = true`
  - `live_workflow.current_url = https://fd7bdf984512a5.lhr.life/eleven/outbound-call`
  - но `public_relay_health.http_code = 503`
  - и raw body:
    - `no tunnel here :(`
- practical meaning:
  - workflow и state file между собой согласованы;
  - но сам public tunnel уже умер;
  - и даже если бы tunnel был жив, quota guard всё равно сейчас блокирует полезный звонок.
- это и есть текущее честное live-состояние:
  - квота не готова;
  - tunnel не готов;
  - разговорные проверки откладываем до восстановления этих двух внешних условий.

Обновление `2026-06-18 13:05 MSK` по маскировке тишины:
- по новой жалобе на пустую тишину между ответами выпущена ещё одна lab-версия:
  - `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
  - branch:
    - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- в ней уже собраны оба слоя anti-dead-air:
  - `soft_timeout_config.timeout_seconds = 1.9`
  - `use_llm_generated_message = true`
  - filler только как сверхкороткая thinking-вставка после завершённого opener;
  - `context_fetch/call_log/send_sms_info` в payload переведены на:
    - `tool_call_sound = elevator3`
    - `tool_call_sound_behavior = always`
- отдельно сделан прямой tool-level patch на реальные active tools:
  - `context_fetch`
    - `tool_1601km62rxpqegqr52m9gk9sftr3`
  - `call_log`
    - `tool_5701ktec2x6wfnj8t5b1rwhtw51p`
  - `send_sms_info`
    - `tool_1701km86jmcpek4rj2j1rbhxqtfr`
  - фактически:
    - `typing/always -> elevator3/always`
- practical meaning:
  - tool-пауза теперь должна маскироваться уже не печатанием, а заметным звуковым фоном;
  - thinking-пауза должна закрываться раньше, чем раньше;
  - это уже не "идея в документации", а опубликованная версия плюс реальный tool-level patch.
- артефакты:
  - `.runtime/eleven_lab_gap_masking_2026-06-18/`
  - `.runtime/eleven_tool_sound_patch_2026-06-18_elevator3/`
- текущий следующий шаг:
  - снять один короткий self-test именно на `agtvrsn_9601...` и отделить на слух:
    - tool masking;
    - soft-timeout filler.

Обновление `2026-06-18 15:26 MSK` по live outbound:
- короткий self-test на `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k` реально снят, но живого разговора не произошло:
  - `call_01_selftest` через `relay_via_server`:
    - `relay_upstream_failed`
    - `The read operation timed out`
  - `call_02_selftest_webhook` через `webhook`:
    - `status = sanctioned_country`
    - `message = This functionality is not available in your location.`
- затем выполнен прямой probe с live-сервера `ai-core-prod-147` в Eleven outbound endpoint;
- он вернул:
  - `HTTP/2 302`
  - redirect на help-статью ElevenLabs про ограничения по странам;
- practical meaning:
  - текущий стоп live-проверки уже не в agent-конфиге;
  - `soft_timeout + elevator3/always` уже опубликованы, но проверить их на слух с текущего server-side outbound path нельзя;
  - корневой блок сейчас:
    - server-side `sanctioned_country` / restricted location.
- под это локально усилена диагностика:
  - `scripts/eleven_outbound_relay_server.py` теперь умеет распознавать такой redirect и возвращать структурированный `sanctioned_country`;
  - `scripts/run_eleven_branch_selftest.sh` теперь умеет классифицировать этот кейс как `reason = sanctioned_country`, а не как безликий фейл.
- следующий реальный шаг теперь не новый prompt, а:
  - новый разрешённый outbound IP/path для live-теста.

Обновление `2026-06-18 11:40 MSK` по живому self-test после masking-fix:
- после tool-level patch на active tools выполнен новый self-test:
  - `.runtime/eleven_toolmask_livecheck_2026-06-18/call_02_selftest/`
- разговор реально создан в Eleven:
  - `conv_2101kvcxvfsrfyz92cr40t8nhfh2`
  - branch:
    - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - version:
    - `agtvrsn_6801kvcx5jcvf6n88sd9yv86nx5v`
- но дальше media не стартовало:
  - `status = in-progress`
  - `has_audio = false`
  - `has_user_audio = false`
  - `has_response_audio = false`
  - `transcript = []`
  - `call_duration_secs = 0`
- дополнительно через Eleven API:
  - `sip-messages` для этого conversation дали:
    - `count = 0`
- но по самому phone number:
  - `phnum_8501khxz93vnfnnsvdjqn1g92yfs`
  свежие SIP messages есть:
  - `183 Session Progress`
  - `200 OK`
  - `BYE`
  - `ACK`
  по `TCP` через trunk `147.45.213.87`
- practical meaning:
  - masking на tools уже применён и branch/version routing рабочие;
  - phone number как SIP endpoint живой;
  - но текущий блок живого теста теперь уже уже:
    - conversation создаётся,
    - а как artifact самой conversation не появляются
      - audio
      - transcript
      - conversation sip trace;
  - пока это не восстановлено, на слух проверить исчезновение пустой тишины нельзя.

Обновление `2026-06-18 12:05 MSK` по masking тишины:
- подтверждено, что ранее одного branch-payload было недостаточно:
  - `tool_call_sound` не применился автоматически на реальные workspace tools;
- поэтому выполнен прямой tool-level patch через Eleven Tools API на active tools текущей lab-ветки:
  - `context_fetch`:
    - `tool_1601km62rxpqegqr52m9gk9sftr3`
  - `call_log`:
    - `tool_5701ktec2x6wfnj8t5b1rwhtw51p`
  - `send_sms_info`:
    - `tool_1701km86jmcpek4rj2j1rbhxqtfr`
- на все три реально записано:
  - `tool_call_sound = typing`
  - `tool_call_sound_behavior = always`
- артефакты backup/verify:
  - `.runtime/eleven_tool_sound_patch_2026-06-18/`
- practical meaning:
  - пустая тишина во время webhook tool execution теперь должна маскироваться уже реальным звуком;
  - это закрывает именно tool-паузы, а не всю LLM-thinking паузу целиком;
  - чистая thinking pause отдельно всё ещё регулируется через:
    - `soft_timeout_config.timeout_seconds = 2.4`

Обновление `2026-06-18 11:35 MSK` по terminal-finalization и masking тишины:
- после repaired webhook-path уже снят реальный speech-test:
  - `conv_0601kvcwg3nyf7hstxwyksj0nxvn`
  - version:
    - `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
- по нему подтверждено:
  - agent говорил normal close до `call_log`;
  - потом на `...` и молчание снова открывал диалог;
  - после `call_log` ещё говорил как обычный собеседник;
  - `end_call` не вызывался;
- под это усилен локальный analyzer:
  - `scripts/analyze_eleven_conversation.py`
  - он теперь ловит:
    - `normal_assistant_speech_after_call_log`
    - `final_close_spoken_before_call_log`
    - `call_log_without_end_call`
    - `helpdesk_tail_in_outbound_close`
- затем опубликована lab-версия:
  - `agtvrsn_9101kvcwr2keeet9ye7q33e7qg2x`
  - она уже дала частичный прогресс:
    - `end_call` снова появился;
    - тяжёлый self-talk после `call_log` ушёл;
  - но остались:
    - duplicate close;
    - placeholder `conv_abcdef...` в drafted `call_log`.
- под это опубликована следующая lab-версия:
  - `agtvrsn_2201kvcwwby6f3r803sqkrawzqn0`
  - она усиливает:
    - terminal tool sequencing;
    - запрет normal close вокруг `call_log/end_call`;
    - binding discipline для `conversation_id / eleven_conv_id`.
- отдельно по жалобе на пустую тишину между ответами выпущен ещё один lab-only masking cycle:
  - версия:
    - `agtvrsn_6801kvcx5jcvf6n88sd9yv86nx5v`
  - что в ней теперь зафиксировано:
    - `soft_timeout_config.timeout_seconds = 2.4`
    - `tool_call_sound = typing`
    - `tool_call_sound_behavior = always`
    для:
      - `context_fetch`
      - `call_log`
      - `send_sms_info`
- practical meaning:
  - LLM-пауза теперь должна маскироваться раньше;
  - tool-пауза не должна висеть голой тишиной на этих webhook tools.
- но живая проверка именно этой masking-версии пока упёрлась во внешний outbound noise:
  - один запуск поймал Cloudflare `Just a moment...`;
  - второй запуск дал:
    - `status = sanctioned_country`
- значит сейчас текущий внешний блокер снова не в prompt/config агента, а в нестабильном outbound access до Eleven.

Обновление `2026-06-18 11:07 MSK` по live outbound branch-fix:
- structural repair для live webhook `https://www.n-8-n.site/webhook/eleven/outbound-call` уже реально доведён до рабочего рантайма;
- одного обновления `workflow_entity` и `publish:workflow` оказалось мало:
  - live n8n продолжал жить по старому snapshot в `workflow_history`;
- поэтому для:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` (`sHTbALayEZdy8Mzs`)
  был сделан полный узкий repair:
  - обновлены `nodes / connections / settings` в `workflow_entity`;
  - создан новый published snapshot в `workflow_history`;
  - `activeVersionId` переведён на:
    - `0e21f126-db50-4500-b74f-3df4e9891d51`
  - затем рестартован только контейнер:
    - `n8n-server-n8n-1`
- после этого live validation webhook снова отвечает штатно;
- главное подтверждение:
  - branch-targeted webhook probe теперь вернул:
    - `success = true`
    - `conversation_id = conv_0801kvcw73eaeqf8t1pjy9p0y8kf`
    - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
    - `environment = production`
- по API Eleven дополнительно подтверждено:
  - этот разговор реально создан именно в lab branch:
    - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - и именно на strict-silence version:
    - `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
- practical meaning:
  - repaired webhook-path снова годится для честного branch-targeted self-test;
  - lab self-test больше не должен уезжать в `Main` просто из-за потери `branch_id`;
  - outbound bridge сейчас не главный блокер.
- вспомогательный технический хвост:
  - `scripts/run_eleven_branch_selftest.sh`
  теперь не падает вторичной ошибкой на пустом теле ответа, а сохраняет JSON `selftest_failed`.
- отдельный шумящий хвост в логах:
  - `VOICE_INBOUND_AGENT (draft)` (`bfNbTwtyXNSFzMc2`)
  сейчас `active=false` и без `activeVersionId`;
  - поэтому старые `mango/events/*` продолжают сыпать `Active version not found`;
  - это отдельная inbound-тема, а не текущий outbound blocker.

Обновление `2026-06-18 10:22 MSK` по live outbound webhook:
- подтверждено, что проблема "сегодня не стартовал" была не в балансе ElevenLabs и не в самой lab-версии prompt, а в live webhook:
  - `https://www.n-8-n.site/webhook/eleven/outbound-call`
- этот маршрут был привязан к workflow:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` (`sHTbALayEZdy8Mzs`)
  у которого отсутствовала опубликованная active version;
- из-за этого route отдавал:
  - `404 Active version not found for workflow with id "sHTbALayEZdy8Mzs"`
- перед правкой снят backup:
  - `backups/2026-06-18_eleven_outbound_call_bridge_before_publish.json`
- затем на live выполнена публикация:
  - `n8n publish:workflow --id=sHTbALayEZdy8Mzs`
- после этого контрольный POST в webhook перестал отдавать `404` и вернул штатный validation JSON:
  - HTTP `200`
  - `{"ok":false,"action":"validation_failed",...}`
- это значит:
  - live outbound route снова существует;
  - код workflow исполняется;
  - следующий реальный блок проверки теперь уже не route registration, а:
    - relay path;
    - outbound request до Eleven;
    - создание разговора и поведение агента на линии.
- practical next step:
  - один контролируемый test-call уже был снят:
    - `.runtime/eleven_restore_probe_2026-06-18_01/`
  - результат этого теста:
    - старый `404` действительно ушёл;
    - но `conversation_id` не создался;
    - `relay_via_server` получил HTML `Just a moment...` вместо JSON от upstream;
    - значит текущий блок уже не в регистрации webhook, а выше:
      - relay/upstream/provider access.
  - следующий practical step теперь:
    - разбирать relay/upstream слой;
    - только потом повторять звонок и проверять strict-silence / machine-logic.
  - важное уточнение после следующего цикла:
    - прямой full-payload вызов с relay-хоста `151.241.228.232` уже смог создать разговор:
      - `conv_4601kvct8fx4f6qs8nfb17vke8gh`
    - это был именно lab-branch:
      - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
    - и именно strict-silence version:
      - `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
    - по audit там остался только один хвост:
      - `duplicate_close_before_end_call`
  - отдельно выяснилось:
    - helper fallback через `webhook` сейчас не сохраняет branch-targeting;
    - из-за этого `restore_probe_02` ушёл не в lab, а в live `Main`:
      - `conv_6301kvctagp5e3vbsynr9jjkchyf`
      - branch `agtbrch_7801kgybyg9nesrbv64y078pazq0`
      - version `agtvrsn_9001kv0k051efpr84vwwttz6kthj`
    - значит webhook fallback пока нельзя считать честной проверкой lab-ветки.
  - под это локальный helper уже усилен:
    - `scripts/run_eleven_branch_selftest.sh`
    - теперь он:
      - умеет восстанавливать `conversation_id` через `List conversations` API;
      - не делает auto-webhook fallback для non-live branch без явного override.
  - параллельно уже подготовлен локальный branch-safe patch для самого workflow:
    - `scripts/prepare_eleven_outbound_call_bridge_branch_fix.py`
    - готовый собранный export:
      - `.runtime/eleven_outbound_call_bridge_branch_fix_2026-06-18/workflow_patched.json`
    - смысл:
      - сохранить `branch_id` и `environment` в `conversation_initiation_client_data`;
      - не терять nested `dynamic_variables`;
      - возвращать top-level `conversation_id` на успешном accepted path.

Обновление `2026-06-18` по strict-silence patch:
- опубликованная lab-версия:
  - `agtvrsn_1301kvagt880eg88y6kynrmyxzvx`
  показала regression именно на тишине;
- контрольный звонок:
  - `conv_4701kvagtyy2f23sp134p47b0tp0`
  показал:
  - repeated `Алло?`
  - inbound-style `Да? Чем могу помочь?`
  - предложения `SMS / callback` прямо внутри silence-state;
- это признано неправильным поведением;
- под это собран отдельный patch:
  - `.runtime/eleven_lab_strict_silence_window_2026-06-17/payload.json`
- его база:
  - `agtvrsn_2101kvag7mw1fpgv6y64jp58qk7j`
- что он должен сделать:
  - silence после opener трактовать только как `no_answer`;
  - не уходить в discovery;
  - не предлагать SMS / callback / manager;
  - не говорить `Да? Чем могу помочь?`
  - разрешать только один rescue, затем silent end.
- patch уже опубликован:
  - `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
- но runtime test по звонку пока не подтверждён из-за внешнего outbound-ограничения:
  - `status = sanctioned_country`
  - `This functionality is not available in your location.`
- параллельно:
  - direct relay timeout
  - webhook указывает на inactive workflow `sHTbALayEZdy8Mzs`
- значит published lab-prompt по тишине уже обновлён, но phone runtime ещё не верифицирован живым разговором.
- локальный verifier по этой версии уже усилен и зелёный:
  - `43/43 ok`
  - артефакт:
    - `.runtime/eleven_lab_strict_silence_window_2026-06-17/apply_result/prompt_invariants_43.json`
- свежий probe `2026-06-18` подтвердил:
  - live webhook `https://www.n-8-n.site/webhook/eleven/outbound-call` сейчас реально отдаёт
    - `404 Active version not found for workflow with id "sHTbALayEZdy8Mzs"`
  - direct local probe в relay timeout-ится;
  - но с `ai-core-prod-147` relay health живой.
- practical rule:
  - для lab branch self-test канонический стартовый transport сейчас:
    - `relay_via_server`
- отдельная контрольная точка:
  - `docs/checkpoints/2026-06-18_STRICT_SILENCE_PUBLISHED_AND_RUNTIME_BLOCKED.md`

Обновление `2026-06-17` по mid-dialogue reassurance trim в naturalness-lab:
- live `Main` этим шагом не менялся;
- опубликована новая lab-only версия:
  - `agtvrsn_2101kvag7mw1fpgv6y64jp58qk7j`
- контрольный звонок:
  - `conv_3701kvag8d1wfvx9egszbbwj21zr`
- что этот шаг реально улучшил:
  - исчезло `Да, я тут`;
  - исчезли bracket tags вроде `[calm]`;
  - opener остался чистым и без префикса;
  - `call_log` и `end_call` не сломались.
- что ещё осталось:
  - late `Алло?` внутри уже активного разговора;
  - duplicate close перед `end_call`.
- practical state:
  - текущая lab-вершина уже заметно лучше по человеческому хвосту разговора;
  - но финализационный хвост всё ещё не считается закрытым.
- следующий безопасный шаг:
  - отдельный узкий цикл только по:
    - late `Алло?`
    - duplicate close

Обновление `2026-06-17` по self-talk fix в naturalness-lab:
- live `Main` этим шагом не менялся;
- правка опубликована только в:
  - `lab_naturalness_2026_06`
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- повод:
  - agent начал говорить сам с собой на коротких ложных фрагментах до нормального старта разговора;
  - контрольный кейс:
    - `conv_0301kvafajs9ekwt3zw5n94p8dx4`
- по нему было видно:
  - opener стартовал с `Так...`
  - одиночный `Нет.` схлопнулся в `not_target`
  - потом ещё пролез поздний line-check
- опубликован новый lab version:
  - `agtvrsn_8101kvaftfcjejjrebsswskw52h3`
- что именно ужесточено:
  - одинокий короткий pickup token вроде `алло / да / угу / ага / что` до opener считается неоднозначным;
  - без второго ясного человеческого сигнала agent не должен открывать sales-диалог;
  - в такой ситуации он должен молча ждать и при необходимости использовать `skip_turn`;
  - `not_target` запрещён по одному голому `Нет`;
  - `soft_timeout_config.timeout_seconds` поднят до `3.2`;
  - вместо старого filler `Так...` в config теперь placeholder:
    - `...`
  - filler разрешён только после полного opener.
- верификация опубликованной версии:
  - `26/26 ok`
  - артефакт:
    - `.runtime/eleven_lab_preopener_gate_hardening_2026-06-17/apply_result/response.json`
- что ещё не подтверждено:
  - пока нет нового живого self-test именно на сценарий:
    - подняли трубку и молчим.
- следующий безопасный шаг:
  - один короткий ручной test-call на полный silent pickup.

Обновление `2026-06-17` по system-binding циклу в naturalness-lab:
- live `Main` этим циклом не менялся;
- изменения были только в `lab_naturalness_2026_06`;
- первый binding-fix кандидат:
  - `agtvrsn_1101kvabn43mfeztaavzxwcbtxyn`
  подтвердил:
  - `context_fetch_before_opener` из self-test ушёл;
  - actual webhook body уже получает корректный live `conv_*`;
  - но draft `call_log.params_as_json` ещё мог содержать fake `conv_abcdef...`
- более жёсткий второй кандидат:
  - `agtvrsn_7501kvabt8d8ewcrmxmnrcrmtn42`
  убрал placeholder issue из audit,
  но одновременно испортил сам разговор:
  - вернул `[calm]`
  - вернул поздние `Алло?`
  - увёл диалог в регрессивный сценарий
- поэтому `v2` отклонена;
- текущий branch-head после отката теперь:
  - `agtvrsn_0101kvac144tfsb88f32crqgbmvq`
- важно:
  - это текущая безопасная рабочая точка lab-ветки после binding-эксперимента;
  - но лучший overall naturalness-winner всё ещё прежняя softfill-линия:
    - `agtvrsn_1201kvaavm18fe8b4sgw5vxt7tqy`
    - лучший разговор:
      - `conv_0501kva6snynemktpje537318ep5`

Обновление `2026-06-17` по structural finalization patch:
- live `Main` этим циклом не менялся;
- lab-only кандидат:
  - `agtvrsn_9001kvac85yzfhgv8fx3tgqnvn7b`
  тестировался только как отдельная узкая проба по `call_log -> end_call`
- контрольный звонок:
  - `conv_1101kvac8w32fjdtvay58v040esw`
  показал:
  - duplicate close по сути остался;
  - analyzer теперь это уже честно видит даже если обычная реплика была с `[calm]`;
  - сам разговор стал хуже:
    - множественные `[calm]`
    - поздние line-check
    - зацикливание SMS-ветки
- поэтому кандидат отклонён;
- после отката текущий branch-head теперь:
  - `agtvrsn_7301kvacfzesee19rmc9fs22m49e`
- practical rule:
  - не возвращать lab на `9001...`
  - использовать его только как доказательство, что чисто tool-layer patch финализацию пока не лечит без побочных регрессий

Обновление `2026-06-17` по price-answer ветке:
- после удачного живого разговора в lab добавлен отдельный узкий price-anchor patch;
- новый current branch-head:
  - `agtvrsn_9201kvaeewdnerjvyrcb2ykkhz5g`
- что теперь должно быть явно зафиксировано в ответе агента при вопросе о цене:
  - ориентир по стоимости:
    - `от 19 000 руб.`
  - старт:
    - `от 1 шт.`
  - тестовая упаковка:
    - не бесплатная
- важная граница:
  - агент не должен сам по себе вставлять цену в opener или в обычную короткую презентацию;
  - цена нужна как готовый anchor только на прямой вопрос клиента.
- при необходимости агент может коротко добавить:
  - доставка `3-4 дня`
  - оплата: безнал, полная предоплата
- после короткого ответа по цене агент должен вести дальше в:
  - SMS с точными условиями
  - или callback менеджера
- этот шаг пока ещё не проверен отдельным price-question self-test и ждёт следующего разговора
- техническое состояние на сейчас:
  - дублирующийся второй price-блок в prompt уже убран;
  - оставлен один канонический `Price-answer anchor override`.
  - текущая published lab-версия уже собрана от `10_COMMERCIAL_ANCHOR_RU.json`, а не от локального хардкода.

Обновление `2026-06-17` по текущей золотой точке naturalness-lab:
- live `Main` по-прежнему не трогали в рамках последнего naturalness-цикла;
- текущий рабочий source-of-truth для экспериментов теперь:
  - `lab_naturalness_2026_06`
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - текущий верхний `version_id`:
    - `agtvrsn_1201kvaavm18fe8b4sgw5vxt7tqy`
- это возврат на подтверждённую удачную V3 softfill-линию:
  - `llm = gpt-5-mini`
  - `tts.model_id = eleven_v3_conversational`
  - включён `soft timeout`
- лучший подтверждённый разговор на этой линии:
  - `conv_0501kva6snynemktpje537318ep5`
- что уже подтверждено этим звонком:
  - opener быстрый и чистый;
  - бизнес-диалог держится хорошо;
  - `send_sms_info`, `call_log` и `end_call` проходят успешно;
  - по ощущению это одна из лучших живых версий naturalness-lab на сегодня.
- что ещё не закрыто:
  - главный остаточный хвост находится не в SMS-tool и не в TTS;
  - длинная пауза возникает в ветке:
    - `попросили SMS -> LLM думает -> send_sms_info`
  - на этой линии это уже зафиксировано метрикой:
    - `convai_llm_service_ttfb ≈ 4.41s`
- важная граница:
  - экспериментальный `SMS fastlane`
    - `agtvrsn_3501kva75b4qf6htw6qkys1j1q6b`
    не принят как новая норма и считается регрессивным;
  - последующая cleanup-серия
    - `agtvrsn_5701kvaaanp8feqvj6s1hrcw2mp0`
    - `agtvrsn_4701kvaafxaket0rtt3y5hnt9q14`
    - `agtvrsn_9501kvaapngkexzr5964jhvbh4zw`
    тоже не стала новой нормой;
  - по реальным self-test она не выбила устойчиво:
    - duplicate final close;
    - late line-check;
    - filler внутри финализации;
  - значит все следующие точечные правки делать от:
    - `agtvrsn_1201kvaavm18fe8b4sgw5vxt7tqy`
  - а не от fastlane-ветки и не от cleanup-кандидатов.
- следующий безопасный шаг:
  - один подтверждающий self-test на текущей вершине;
  - затем только узкая правка на сокращение SMS decision-gap;
  - а фронт `duplicate close / finalization filler` дальше решать уже не бесконечными prompt-only запретами, а более структурным способом.

Обновление `2026-06-16` по выбору voice-модели в naturalness-lab:
- после отдельного возврата на `eleven_v3_conversational` и серии self-test зафиксирован практический вывод:
  - для нашего телефонного контура эта модель звучит местами богаче, но слишком часто ощущается вязкой;
  - для реального темпа звонка lab сейчас снова возвращён на:
    - `eleven_flash_v2_5`
- перед этим отдельно был закрыт product-case:
  - если человек говорит:
    - `да, интересно`
    - но потом:
      `нет`, в смысле пока не использует липолитики,
    agent больше не должен схлопывать такого контакта в ранний `not_target`.
- Для этого был выпущен lab-only patch:
  - `agtvrsn_1901kv88cahgfq1v7w6b7nvcme32`
- Контрольный звонок:
  - `conv_1001kv88d99xe8wsv2tsr3nvyvtv`
  подтвердил:
  - agent уже объясняет ценность ЛипоЛонг для такого контакта;
  - доходит до `send_sms_info` и `call_log`;
  - не бросает разговор сразу после `нет`.
- Затем был выпущен ещё один узкий patch:
  - `agtvrsn_3201kv88kyz1fdpazd8vvmdvjs80`
  - его задача:
    - убрать spoken-turn `...`
    - и обрубок `Я уже...` перед нормальным финальным SMS-close.
- После этого lab целенаправленно возвращён на Flash:
  - текущая верхняя lab-version:
    - `agtvrsn_4901kv88ns5pfgvbqbg3n42he4rp`
  - `tts.model_id = eleven_flash_v2_5`
  - `expressive_mode = false`
  - `speed = 1.08`
  - `stability = 0.46`
  - `similarity_boost = 0.80`
- Проверочный Flash self-test:
  - `conv_4601kv88pp5sephrzz0swv4nck21`
  подтвердил:
  - product-ветка `интересно, но пока не используем` остаётся рабочей;
  - SMS-path и `call_log` не сломались после возврата на Flash;
  - по ощущению и по скорости это пока лучший текущий кандидат для lab-контура.
- Остаток на сейчас:
  - в overlap-кейсах ещё могут мелькать микрофрагменты:
    - `...`
    - `Я уже...`
  - следующий шаг уже не в поиске другой модели, а в доводке поведения на Flash:
    - turn-taking
    - suppression позднего rescue
    - чистый одинарный финальный close

Обновление `2026-06-16` по новой product-ветке в naturalness-lab:
- выпущена новая верхняя lab-version:
  - `agtvrsn_9401kv883fg5fxxbsv2t231jctqc`
- в неё добавлены два новых блока:
  - `Warm line-check wording override`
  - `Interested-but-not-yet-using override`
- цель этого шага:
  - убрать сервисные фразы типа:
    - `Да, я на линии`
  - и перестать ронять разговор, если человек говорит:
    - `да, интересно`
    - но потом:
      `нет`, в смысле ещё не работает с липолитиками.
- уже есть подтверждающий звонок:
  - `conv_7201kv884a88eghv2r9zs9mgr85v`
- что он показал:
  - после `Да.` и потом `Нет.` agent не закрыл звонок и не дал `not_target`;
  - вместо этого продолжил объяснять ЛипоЛонг как релевантный продукт для косметолога, который пока не использует эту категорию;
  - фраза `Да, я на линии` в этом тесте не прозвучала.
- значит новый текущий фокус lab уже не в том, чтобы удержать ветку от раннего hangup — это получилось;
- следующий шаг:
  - провести эту же ветку дальше до SMS или callback и посмотреть, как agent её дожимает.

Обновление `2026-06-16` по текущему верхнему tip naturalness-lab:
- после проверки `SMS tool failure honesty` стало видно, что success-path ещё даёт один хвост:
  - agent может повторить финальную реплику:
    - `Я уже отправила SMS на этот номер. Хорошего дня.`
    второй раз уже после `call_log`.
- поэтому в lab выпущен следующий patch:
  - новая верхняя lab-version:
    - `agtvrsn_2501kv87p0d1e3r8wjpf7rn2mbra`
  - новые блоки:
    - `Single post-SMS spoken close override`
    - `Late rescue cancellation override`
- смысл:
  - после успешной SMS spoken close должна звучать только один раз;
  - backend-действия после неё не должны ещё раз озвучивать тот же текст;
  - если живой пользователь уже начал отвечать, rescue не должен проскальзывать как `...`.
- по новой вершине уже есть два self-test:
  - `conv_1301kv87q3h6e8p8apsf5zacq7v7`
  - `conv_6501kv87v0tgeg7bvvtyqt1zy5k7`
- что уже понятно:
  - not-target path на `2501` жив и пишет валидный `call_log`;
  - второй not-target звонок уже прошёл чисто, с одной финальной репликой;
  - но SMS-path на `2501` пока ещё не подтверждён отдельным answered звонком.
- значит текущий следующий шаг в lab всё ещё один:
  - довести answered self-test именно до `send_sms_info`
  - и проверить, исчез ли duplicate final close на новой вершине.

Обновление `2026-06-16` по текущей вершине naturalness-lab:
- подтверждён отдельный lab-only fix:
  - `No-thanks lead-in override`
- answered self-test:
  - `conv_1501kv86rfxse5d94vpk6bz03fek`
  - `version_id = agtvrsn_9501kv86kqvwegrr2h8rj157k6me`
  показал:
  - содержательная sales-реплика больше не стартует с:
    - `Спасибо, ЛипоЛонг — ...`
  - agent продолжает разговор сразу по сути:
    - `ЛипоЛонг — ...`
- но этот же звонок вскрыл новый более важный остаток:
  - `send_sms_info` получил provider failure:
    - Mango `429 Too Many Requests`
  - после этого agent всё равно ошибочно сказал:
    - `Я уже отправила SMS на этот номер. Хорошего дня.`
  - и повторил эту фразу дважды.
- поэтому в lab уже выпущен следующий micro-patch:
  - новая верхняя lab-version:
    - `agtvrsn_1101kv871mt1e699f6sq7x35epay`
  - новый блок:
    - `SMS tool failure honesty override`
- смысл:
  - если `send_sms_info` не подтвердил успешную отправку, agent не должен говорить, что SMS уже отправлена;
  - он должен закрывать разговор коротко и честно, с follow-up через менеджера, а не через ложный `sms_sent_and_close`.
- артефакты:
  - `.runtime/eleven_lab_sms_failure_honesty_2026-06-16/payload_minimal.json`
  - `.runtime/eleven_lab_sms_failure_honesty_2026-06-16/response.json`
- live `Main` при этом по-прежнему не менялся;
- следующий шаг делать только в lab:
  - один answered self-test на `agtvrsn_1101kv871mt1e699f6sq7x35epay`
  - проверить честность при SMS-failure и отсутствие дубля финального close.

Обновление `2026-06-16` по отдельному naturalness-lab контуру:
- для экспериментов по “живости” общения создан отдельный безопасный контур;
- новая рабочая Git-ветка:
  - `codex/eleven-naturalness-lab`
- новая ветка в ElevenLabs:
  - `lab_naturalness_2026_06`
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - `version_id = agtvrsn_0401kv7waz0sfae92b77pgjhmcqf`
- эта ветка создана от текущего подтверждённого live-состояния:
  - live `Main branch_id = agtbrch_7801kgybyg9nesrbv64y078pazq0`
  - live `version_id = agtvrsn_9001kv0k051efpr84vwwttz6kthj`
- важно:
  - live `Main` остаётся на `100%` трафика;
  - `lab_naturalness_2026_06` остаётся на `0%`;
  - боевой агент не переключался и не менялся ради naturalness-экспериментов.
- стартовый baseline для lab сейчас такой:
  - `tts.model_id = eleven_flash_v2_5`
  - `voice_id = 0ArNnoIAWKlT4WweaVMY`
  - `expressive_mode = false`
  - `speed = 1.08`
  - `stability = 0.46`
  - `similarity_boost = 0.82`
  - `optimize_streaming_latency = 2`
  - `turn_timeout = 1.75`
  - `turn_eagerness = normal`
  - `turn_model = turn_v2`
- baseline-снимки сохранены в:
  - `.runtime/eleven_lab_setup_2026-06-16/`
- дополнительно на этом же lab-контуре позже подтверждена текущая верхняя рабочая lab-version:
  - `agtvrsn_6601kv84qjbjetvaafn1t7yzkswh`
- в неё уже добавлен отдельный блок:
  - `Post-SMS no-dead-air override`
- смысл этого последнего lab-only шага:
  - убрать spoken-turn `...` после успешного `send_sms_info`;
  - не оставлять пустую паузу между SMS tool-result и коротким подтверждением;
  - line-check вида `алло?` сразу после SMS трактовать как реакцию на задержку, а не как новую тему.
- последний запущенный self-test на этой вершине:
  - `conv_7601kv84skecfh783bsw4hg5qzn9`
  уже завершился и подтвердил:
  - lab-ветка живая;
  - opener остался быстрым;
  - agent больше не дал старый spoken-turn `...`.
- но этим же звонком не удалось проверить именно post-SMS path:
  - разговор завершился по `refusal_soft`, не доходя до `send_sms_info`;
  - поэтому отдельная answered проверка на SMS-accept ветку всё ещё нужна.
- после этого в lab добавлен ещё один узкий блок:
  - `Final close clarity override`
- новая подтверждённая верхняя lab-version:
  - `agtvrsn_7801kv85988ee7t8jgdwzrsk1ry6`
- следующий answered self-test:
  - `conv_6801kv85a8wzfkx9kwj3qkksmgdx`
  подтвердил:
  - SMS-path уже проходит до конца;
  - после line-check:
    - `Алло!`
    agent корректно отвечает:
    - `Я уже отправила SMS на этот номер. Хорошего дня.`
  - роботская фраза про “зафиксировала отказ / информация сохранена” не вернулась.
- затем в lab отдельно ужат rescue-line:
  - новая верхняя lab-version:
    - `agtvrsn_5701kv85jqxefp78hnjgewa0mqbb`
  - rescue fallback стал:
    - `Алло?`
  - цель:
    - убрать длинный broken rescue вроде `Алло, вы на лин...`.
- answered self-test:
  - `conv_4801kv85k83afcvvrc44nw1wdem4`
  показал:
  - rescue уже стал короче:
    - `Алло?...`
  - SMS-path при этом не сломался.
- после этого найден ещё один хвост внутри активного диалога:
  - agent мог говорить:
    - `Да, я вас слышу. ...`
    или заходить в обрубок:
    - `Отлично! Мы...`
- поэтому сверху применён ещё один lab-only блок:
  - `Mid-dialogue line-check continuation override`
  - текущая верхняя lab-version теперь:
    - `agtvrsn_6901kv85rrfxesqab1q9mjhmmd8r`
- проверочный звонок на этой вершине:
  - `conv_1901kv85s843fcft09kfqz0q07c0`
  позже дал usable transcript и подтвердил:
  - хвост `Да, я вас слышу. ...` ушёл;
  - обрубок `Отлично! Мы...` тоже ушёл;
  - после mid-dialogue line-check агент продолжает разговор business-репликой по смыслу, а не сервисным подтверждением линии;
  - draft `call_log(no_answer)` внутри этого разговора не ушёл в таблицу, потому что tool был отменён новым user input;
  - SMS-path в конце снова завершился чистым:
    - `Я уже отправила SMS на этот номер. Хорошего дня.`
- новый тонкий residual хвост после этого:
  - одна из содержательных sales-реплик после возврата в диалог началась с:
    - `Спасибо, ЛипоЛонг — ...`
  - следующий шаг в lab:
    - убрать автоматическое `Спасибо` в начале смысловой продажной реплики.
- После этого в lab уже выпущен отдельный micro-patch:
  - новая верхняя lab-version:
    - `agtvrsn_9501kv86kqvwegrr2h8rj157k6me`
  - новый блок:
    - `No-thanks lead-in override`
  - смысл:
    - если диалог вернулся к содержательной sales-реплике, агент должен начинать сразу с сути, а не с
      `Спасибо, ...`.
- Артефакты:
  - `.runtime/eleven_lab_no_thanks_leadin_2026-06-16/payload_minimal.json`
  - `.runtime/eleven_lab_no_thanks_leadin_2026-06-16/response.json`
- этот шаг уже применён в lab, но ещё не проверен новым answered self-test.
- следующий этап делать только в lab:
  - baseline self-tests;
  - затем маленькие isolated changes:
    - voice/TTS;
    - turn-taking;
    - prompt naturalness.

Обновление `2026-06-15` по очистке диска и legacy-хвостов:
- на live-сервере `147.45.213.87` удалены raw SQLite-хвосты, оставшиеся после перехода `n8n` на `Postgres`;
- подтверждено, что live `n8n` уже работает на:
  - `DB_TYPE=postgresdb`
  - `DB_POSTGRESDB_HOST=n8n-server-postgres-1`
  - `DB_POSTGRESDB_DATABASE=n8n_prod`
- после очистки volume `n8n-server_n8n_data` уменьшился примерно до:
  - `38.77MB`
  и больше не содержит старый `database.sqlite`;
- очищены:
  - historical raw SQLite copies в `/home/aicore/backups/...` и `/home/aicore/safe-backups/...`;
  - docker log stopped-контейнера `madcore-app`;
  - `site-control-kit` runtime cache и `state.json`;
  - Docker build cache (`0B` после `buildx prune`);
- место на корневом разделе изменилось примерно так:
  - было:
    - `38G used / 39G avail / 50%`
  - стало:
    - `22G used / 56G avail / 28%`
- это не меняло текущий voice runtime:
  - `n8n`
  - `postgres`
  - `postgres_memory`
  - `postgrest`
  - `ElevenLabs`
  остались в рабочем состоянии;
- `site-control-kit` по-прежнему относится не к voice-call-center, а к `cosmetologist_hunter`;
  после очистки сейчас:
  - `connected_clients = 0`
  - browser client не поднят постоянно;
- главный оставшийся крупный логовый хвост:
  - `/var/log/asterisk` около `3.2G`
  - он продолжает расти из-за потока failed `REGISTER`.

Обновление `2026-06-13` по возврату точного opener и защите от недослушанного soft-refusal:
- по жалобе `начала вообще ни с того / опять не слушает` снят новый live-лог:
  - `conv_2501kv0jdj3nem583shqd89432xf`
- он подтвердил реальную поломку:
  - user начал с короткого живого сигнала:
    - `Ну а?`
  - agent пропустил обязательный opener и сразу ушёл во второй шаг:
    - `Это липолитик для косметологов, Липолонг...`
- после этого live prompt ужесточён обратно:
  - первый spoken ход после любого короткого живого ответа снова должен быть строго фиксированным;
  - фиксированный opener теперь такой:
    - `Здравствуйте, я официальный представитель липолитика Липолонг. Это липолитик для косметологов. Вам это интересно?`
  - отдельным жёстким правилом запрещён skip сразу в qualification до этого opener;
  - короткие живые сигналы вроде:
    - `алло`
    - `да`
    - `ну а?`
    - `чего?`
    всё равно считаются достаточными, чтобы сразу произнести именно этот opener.
- одновременно усилено правило rescue:
  - на весь звонок разрешён только `1` line-check;
  - после использования этого rescue-бюджет звонка считается исчерпанным;
  - второй `Алло? / Вы на линии?` в том же звонке больше быть не должен.
- первый контрольный звонок после этого патча:
  - `conv_0401kv0jw1xeetgt98bq2snpy0v5`
- по нему подтверждено:
  - opener уже вернулся в правильный exact-вид;
  - первый ход agent теперь снова начинается как надо;
  - один rescue был использован корректно;
  - но на мягком колеблющемся ответе user-реплика:
    - `М-м-м, неактуально, наверное.`
    пришла почти одновременно с началом финализации, то есть agent всё ещё недослушивал медленный soft-refusal.
- после этого сделан ещё один маленький live-шаг:
  - `turn_timeout` увеличен совсем чуть-чуть:
    - `1.65s -> 1.75s`
  - в prompt добавлено прямое правило:
    - колеблющиеся живые ответы вроде `м-м-м`, `ну`, `нет...`, `неактуально, наверное` нельзя трактовать как тишину;
    - нельзя запускать `call_log` и `end_call` поверх такого формирующегося ответа;
    - надо коротко дождаться завершения мысли и только потом отвечать по смыслу.
- текущая live version после второго шага:
  - `agtvrsn_9001kv0k051efpr84vwwttz6kthj`
- второй контрольный звонок:
  - `conv_8001kv0k0jbhewcajwcx2syq3xwr`
- по нему подтверждено:
  - opener стабильно правильный;
  - на простом отказе:
    - `Нет. -> Неактуально. -> Да не, не надо.`
    agent уже не уходит в хаотичный ранний сброс;
  - objection-flow проходит предсказуемо:
    - opener
    - уточнение причины
    - один value hook
    - отказ
    - корректное завершение.
- текущий живой остаток:
  - нужно отдельно проверить сценарий именно на confused human reply после pickup:
    - `Ну а?`
    - `Чего?`
    - `Что это?`
  - и отдельно перепроверить machine / voicemail, чтобы новый fixed opener не дал regression на автоответчиках.

Обновление `2026-06-13` по objection-test и колеблющимся ответам:
- проведён objection-test:
  - `conv_0301kv0j51x0eh6ae0p8y9n6qn4c`
- по нему подтверждено:
  - agent уже не сдаётся на `неактуально` сразу;
  - на второй objection-реплике он уже использует value hook:
    - `официальный канал`
    - `можно начать с одной тестовой упаковки`
  - и затем ведёт в `SMS`.
- одновременно вскрылся новый live-хвост:
  - после value hook пользователь дал живую колеблющуюся реплику:
    - `Да нет, наверное.`
  - но agent почти одновременно трактовал ветку как отсутствие ответа и закрыл разговор;
  - то есть objection-hesitation ветка ещё слишком легко схлопывалась в финализацию.
- после этого в live отдельно зашито правило:
  - колеблющиеся ответы вида
    - `да нет`
    - `ну нет`
    - `да нет, наверное`
    - `не знаю, наверное`
    - `ну, наверное нет`
    считаются живой репликой, а не тишиной;
  - на таких ответах нельзя закрывать звонок как на non-response;
  - их надо обрабатывать как продолжающийся отказ, а не как пустоту.
- в `interruption_ignore_terms` дополнительно добавлены:
  - `да нет`
  - `ну нет`
  - `наверное`
  - `наверное нет`
- `turn_timeout` после этого шага немного возвращён:
  - `1550 мс -> 1650 мс`
- текущая live version:
  - `agtvrsn_9601kv0j7x2cesd92ptgheq4pqyc`
- текущий live фронт:
  - objection-ветка уже стала лучше и более продающей;
  - следующий точечный тест нужен на сценарий:
    - `неактуально`
    - `value hook`
    - `да нет / наверное`
    - итоговый финальный ход.

Обновление `2026-06-13` по продающему дожиму на `не актуально / не интересно`:
- после нового фидбэка live-логика objection-handling усилена именно в продажную сторону;
- цель теперь не просто:
  - быстро увести в `SMS`
  - или `callback`
  а сначала коротко оживить интерес и только потом вести в следующий шаг;
- в live prompt добавлен новый блок:
  - `Persuasive objection recovery`
- теперь agent должен на cold objection:
  - коротко признать сопротивление;
  - понять причину;
  - дать `1-2` компактных продающих плюса;
  - затем уже просить следующий шаг:
    - `SMS`
    - или `callback`.
- разрешённые продающие hooks:
  - официальный канал поставки;
  - оригинальный продукт без серого риска;
  - низкий порог входа через тестовую упаковку / `1` упаковку;
  - релевантность для косметологов, работающих с коррекцией фигуры и инъекционными методиками;
  - возможность спокойно сравнить с текущими решениями без большого обязательства;
  - быстрый разбор входа, доставки и условий.
- отдельно в live закреплён запрет:
  - не выдумывать дикие истории успеха;
  - не давать ложные телесные/сексуальные/медицинские обещания;
  - не использовать абсурдные примеры ради продажи.
- то есть agent теперь должен быть более цепляющим, но при этом оставаться правдоподобным и продающим по делу.
- текущая live version после этого пакета:
  - `agtvrsn_6301kv0hrh7jexkafy17hat7nb92`
- следующий нужный тест:
  - короткий objection-case:
    - `не актуально`
    - `почему`
    - `плюс нашего продукта`
    - `SMS / callback`.

Обновление `2026-06-13` по `не актуально / не интересно`:
- после нового фидбэка подтверждено, что agent всё ещё слишком быстро сдавался на фразы:
  - `не актуально`
  - `не интересно`
  - `не надо`
  - короткое `нет`
- это противоречило целевой live-логике дожима:
  - сначала понять причину;
  - потом попробовать ещё один короткий hook;
  - и только потом закрывать разговор.
- в live prompt добавлен отдельный блок:
  - `Salvage not-relevant objection`
- теперь правило такое:
  - если человек говорит `не актуально / не интересно / не надо` без явного прощания, это не считать автоматическим финальным отказом;
  - сначала один короткий вопрос на причину;
  - затем ещё один короткий hook:
    - SMS,
    - callback,
    - low-friction entry вроде тестовой упаковки,
    - или проверка, что это действительно `not_target`, а не просто низкий приоритет;
  - wording не фиксирован одной фразой — agent должен делать это естественно, своими словами;
  - если после clarification + одного hook человек всё равно отказывает или явно завершает разговор (`до свидания`, `не звоните`, `неинтересно, до свидания`) — тогда уважительно закрывать.
- текущая live version после этого патча:
  - `agtvrsn_1701kv0hbgmeehkashe75vt32t3w`
- следующий нужный тест:
  - отдельный короткий кейс именно на сценарий:
    - `opener -> не актуально -> уточнение причины -> hook -> итог`.

Обновление `2026-06-13` по rescue-лексике и паузе после opener:
- после жалобы, что agent слишком жёстко зафиксирован на одной и той же фразе:
  - `Алло, меня слышно? Вы тут?`
  и звучит как скрипт, live rescue-логика была ослаблена;
- из prompt убран старый жёсткий блок:
  - `ask exactly once: "Алло, меня слышно? Вы тут?"`
- вместо этого в live теперь зашито:
  - один короткий rescue line-check;
  - только после opener;
  - только если после opener около `2.0-2.3` секунд нет внятного directed reply;
  - не фиксированной одной фразой, а коротким живым уточнением, тут ли человек на линии;
  - не повторять один и тот же line-check дважды подряд;
  - использовать rescue максимум один раз за звонок.
- дополнительно в `soft_timeout_config` включён LLM-generated line-check override:
  - цель: коротко и по-человечески проверить, на линии ли человек;
  - без роботного повторения одной и той же строки.
- текущая live version после этого шага:
  - `agtvrsn_1801kv0h5cvvfq2bjzxzev528wc6`
- контрольный звонок:
  - `conv_5101kv0h5xnjfp3sfpdbgh9f6h2y`
  не попал в rescue-ветку, потому что пользователь ответил по сути сразу:
  - `Нет.`
  - `Неактуально.`
  поэтому этот звонок подтвердил общую стабильность после патча, но не дал прямой проверки новой varied-rescue реплики;
- следующий нужный тест теперь отдельный:
  - сценарий `opener -> пауза около 2 секунд -> rescue -> ответ`.

Обновление `2026-06-13` по правилу первого `нет`:
- после regression-теста было подтверждено, что live-agent снова начал слишком рано завершать разговор:
  - на простое короткое `нет` после opener он уходил сразу в:
    - `call_log(refusal_soft)`
    - затем `end_call`
- это было подтверждено разговором:
  - `conv_7001kv0gp2fafvj8h6w0c2s80thz`
- после этого в live внесён отдельный override:
  - plain short `нет` сразу после opener не считается финальным отказом;
  - plain short `нет` после single rescue тоже не считается финальным отказом;
  - сначала agent обязан сделать один короткий уточняющий дожим;
  - только после повторного явного отказа или фразы с явным закрытием (`нет, спасибо`, `до свидания`, `всего доброго`) он закрывает разговор.
- одновременно `turn_timeout` немного возвращён из слишком резкого режима:
  - было `1450 мс`
  - стало `1550 мс`
- в `interruption_ignore_terms` дополнительно добавлены:
  - `не знаю`
  - `не очень`
- контрольный live-тест после правки:
  - `conv_1201kv0gtsxgeqvs7dba302d7p24`
- подтверждено:
  - после `Нет. Нет.` agent уже не бросает трубку сразу;
  - он корректно делает один дожим:
    - `Поняла. Это совсем не ваш профиль или просто сейчас неактуально?`
  - и только после второго ответа:
    - `Неактуально, наверное.`
    закрывает разговор как `refusal_soft`.
- текущая live version:
  - `agtvrsn_0601kv0gta7yekr93p8j4tgq4q0g`
- текущий `turn_timeout`:
  - `1550 мс`
- новый оставшийся live-хвост:
  - rescue-фраза `Алло, меня слышно? Вы тут?` всё ещё может вылезать после opener, если после вопроса идёт только `...`
  - следующий фронт теперь не ранний сброс на `нет`, а более аккуратное поведение на тишине между opener и первым внятным ответом.

Обновление `2026-06-13` по задержкам ответа и миллисекундной настройке:
- после жалобы на длинную паузу после коротких ответов и финального `спасибо / до свидания` сняты точные live-метрики по разговору:
  - `conv_4701kv0g5hkzemzthpg784a8td05`
- подтверждено:
  - LLM сам по себе отвечает быстро:
    - примерно `460-635 мс`
  - TTS стартует быстро:
    - примерно `87-113 мс`
  - основной хвост задержки давал не голос и не модель, а слишком разогнанный `turn_timeout = 2200 мс`
- дальше live был пошагово сдвинут:
  - сначала до `1650 мс`
  - затем до `1450 мс`
- параллельно добавлены новые human-hesitation ignore terms:
  - `э-э-э`
  - `эм`
  - `мм`
- в prompt добавлено правило:
  - если ответ начинается с колебания вроде `э-э-э, не надо` или `эм, нет`, это не конец реплики и нужно дождаться полного ответа;
  - явные финальные фразы человека (`спасибо, до свидания`, `не надо, спасибо`, `всего доброго`) считать завершёнными сразу, без лишнего ожидания.
- контрольный live-тест после этого:
  - `conv_7001kv0gp2fafvj8h6w0c2s80thz`
- по нему уже видно улучшение:
  - финальный tool-generation шаг после короткого отказа:
    - около `1128 мс`
  - финальная spoken closing фраза:
    - ещё около `701 мс`
  - то есть тяжелый хвост стал заметно короче, чем в старом режиме около `2129 мс`
- текущая live version:
  - `agtvrsn_0401kv0gngjqfqhreqh0sbjz5gnq`
- текущий live `turn_timeout`:
  - `1450 мс`
- артефакты:
  - `backups/2026-06-13_latency_goldilocks_1650ms/`
  - `backups/2026-06-13_latency_goldilocks_1450ms/`
  - `.runtime/elevenlabs_manual_test_call_2026-06-13_79251130826_retry10/`
  - `.runtime/elevenlabs_manual_test_call_2026-06-13_79251130826_retry11/`

Обновление `2026-06-13` по opener, `call_log` и праву пользователя договорить:
- после серии живых тестов на `+79251130826` подтверждено:
  - раньше agent слишком рано перехватывал ход;
  - `call_log` реально зависал из-за `404 Active version not found for workflow with id "kZSdJrsAHWWIC2l6"`;
  - из-за этого на human-refusal agent молчал, залипал и только потом завершал звонок.
- исправлено:
  - опубликованы и подняты в live `n8n` три bridge-workflow:
    - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` `kZSdJrsAHWWIC2l6`
    - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` `tdiAEZM9FZDEP7k4`
    - `ELEVEN_TOOL_SEND_SMS_BRIDGE (draft)` `AZMeHe0wrPs3wxYx`
  - `n8n-server-n8n-1` перезапущен, чтобы production webhooks реально поднялись;
  - live turn timeout увеличен до:
    - `turn_timeout = 2.2`
  - в live prompt добавлен absolute opener override:
    - `Здравствуйте, я официальный представитель липолитика Липолонг. Это липолитик для косметологов. Вам это интересно?`
  - закреплено правило:
    - после вопроса не лезть в ранний перехват;
    - пользователю нужно дать договорить;
    - rescue-фраза не должна повторно вылезать как line-check внутри уже живого разговора.
- подтверждено свежим live-тестом:
  - `conv_4701kv0g5hkzemzthpg784a8td05`
  - opener уже звучит в exact wording;
  - пользователь смог нормально ответить сразу после opener;
  - SMS-ветка отработала до конца без зависания на `call_log 404`.
- новый оставшийся хвост после этого теста:
  - после `send_sms_info` agent всё ещё сказал service-tail:
    - `Могу чем-то ещё помочь?`
- поэтому дополнительно уже внесён свежий live-patch:
  - после `send_sms_info` подтверждать SMS одной короткой фразой;
  - не задавать help-desk вопрос `Могу чем-то ещё помочь?`
- текущая live version после этого пакета:
  - `agtvrsn_2401kv0g9xtwf77tz4amn8pg8075`
- артефакты:
  - `backups/2026-06-13_exact_opener_and_more_user_space/`
  - `backups/2026-06-13_human_refusal_spoken_close/`
  - `backups/2026-06-13_single_rescue_whole_call/`
  - `backups/2026-06-13_sms_tail_ban_refresh/`
  - `.runtime/elevenlabs_manual_test_call_2026-06-13_79251130826_retry8/`
  - `.runtime/elevenlabs_manual_test_call_2026-06-13_79251130826_retry9/`

Обновление `2026-06-13` по агрессивному перебиванию:
- после разбора тестового звонка `conv_3501kv0ev6y2fb3r7hmvyyp5cayw` live turn-control смягчён;
- текущая live version:
  - `agtvrsn_1701kv0ezcqvejtaz1zpyjevmpqf`
- текущие live turn-настройки:
  - `turn_timeout = 1.6`
  - `turn_eagerness = normal`
  - `speculative_turn = false`
  - `retranscribe_on_turn_timeout = true`
- в `interruption_ignore_terms` добавлены:
  - `м-м-м`
  - `угу`
  - `ага`
  - `ну`
  - `секунду`
  - `подождите`
  - `сейчас`
- в live prompt зашито правило:
  - hesitation sounds и обрывки начала фразы вроде `ну, ва-` не считаются концом реплики;
  - агент должен ждать завершения мысли, а не лезть поверх.
- артефакты:
  - `backups/2026-06-13_interrupt_aggression_trim/`

Обновление `2026-06-13` после плохого тестового звонка `conv_7101kv0dzef5fp7sw6vff092xza7`:
- предыдущая голосовая попытка с `eleven_multilingual_v2` признана неудачной по живому тесту;
- live уже откатан на:
  - `eleven_flash_v2_5`
- текущая live version:
  - `agtvrsn_0401kv0e8v2ffad82f2r1pje6ef5`
- текущие voice-настройки теперь:
  - `expressive_mode = false`
  - `optimize_streaming_latency = 2`
  - `stability = 0.46`
  - `speed = 1.08`
  - `similarity_boost = 0.82`
- дополнительно в live prompt зашит жёсткий запрет:
  - не говорить
    - `Могу ли я помочь вам ещё чем-то?`
  - и вообще не добавлять spoken-tail в ветках:
    - `no_answer`
    - silence-after-opener
    - failed-dialogue
- отдельно этим же тестом снова подтверждено:
  - `call_log` падает в `404` на workflow `kZSdJrsAHWWIC2l6`
  - pre-opener rescue ещё не добит до конца
- артефакты:
  - `backups/2026-06-13_voice_revert_and_silent_noanswer_fix/`
  - `.runtime/conv_7101kv0dzef5fp7sw6vff092xza7_probe/`

Обновление `2026-06-13` по реалистичности голоса:
- live-агент переведен на новую голосовую version:
  - `agtvrsn_6501kv0dc11ceftbtjbmfang5ztq`
- текущий голос оставлен тот же:
  - `Elena Gromova — Podcasts & Conversation`
  - `voice_id = 0ArNnoIAWKlT4WweaVMY`
- TTS-модель теперь:
  - `eleven_multilingual_v2`
  - вместо прежнего `eleven_flash_v2_5`
- текущие live voice-настройки:
  - `expressive_mode = false`
  - `optimize_streaming_latency = 1`
  - `stability = 0.45`
  - `speed = 1.03`
  - `similarity_boost = 0.82`
- попытка включить официальный `Expressive TTS` была отдельно проверена и не прошла:
  - ElevenLabs API вернул:
    - `expressive_tts_not_allowed`
- значит интонацию усиливали не “магической галкой”, а через:
  - более качественную TTS-модель;
  - более естественную скорость;
  - чуть более живой диапазон стабильности;
  - чуть более высокий similarity.
- артефакты:
  - `backups/2026-06-13_voice_realism_tuning/`

Обновление `2026-06-12` по hard-rule `абонент / абоненту / абонентам`:
- после разбора live-кейса усилен именно live prompt агента;
- новая live version:
  - `agtvrsn_6701ktxx1b3efdca8r13zcj2sys2`
- теперь это правило закреплено как абсолютный override:
  - если в сервисной или message-transfer фразе звучит
    - `абонент`
    - `абоненту`
    - `абонентам`
  - это немедленно перебивает любую гипотезу про “живого администратора” или “полезного посредника”;
  - агент не должен продолжать продажный разговор вообще.
- дополнительные explicit trigger-фразы, уже вшитые в live:
  - `сейчас же отправлю её абоненту`
  - `что передать абоненту?`
  - `есть что сообщить дополнительно?`
  - `нужно передать ещё что-то абоненту?`
  - `что бы вы хотели сказать абоненту?`
- целевое действие:
  - `call_log(no_answer|busy)`
  - затем silent `end_call`
  - без SMS
  - без номера менеджера
  - без spoken callback-message
- артефакты:
  - `backups/2026-06-12_abonent_hard_override_refresh/`

Обновление `2026-06-12` по `conv_0401ktxtzpz2ftdv01cmb76c77ba`:
- полный разговор перечитан напрямую через `ElevenLabs Conversations API`;
- локальный JSON сохранён здесь:
  - `.runtime/conv_probe_0401ktxtzpz2ftdv01cmb76c77ba/body.json`
- это не автоответчик и не voicemail;
- по transcript это живой контакт / посредник:
  - `Слышно. Говорите.`
  - `Мне интересно, я слушаю.`
  - `Лучше я сначала всё подробно изучу и перезвоню, если что.`
  - `Спасибо, всё запомнила.`
- правильная трактовка такого кейса:
  - `send_kp_pending_callback`
  - а не `no_answer` и не machine-stop;
- одновременно этим же JSON подтвержден технический сбой:
  - `call_log` несколько раз падал в `404`
  - причина:
    - `Active version not found for workflow with id "kZSdJrsAHWWIC2l6"`
- также видно, что в разговоре преждевременно вылезал rescue:
  - `Алло, меня слышно? Вы тут?`
  - ещё до нормального старта основного разговора.

Обновление `2026-06-12` по `row_11`:
- выполнен следующий одиночный test-call:
  - `row_11`
  - `Cosmetology Sl, кабинет косметолога`
  - `+79163021253`
  - `request_id = manual.2026-06-12.ROW11.followupcheck`
- внешний webhook снова ответил `HTTP 200` с пустым body;
- live Sheet после этого перечитан дважды, но нового `call_log` по:
  - `request_id = manual.2026-06-12.ROW11.followupcheck`
  - `phone_primary = +79163021253`
  не появилось;
- значит этот цикл пока нельзя использовать как вывод о человеке, автоответчике или refusal-flow;
- минимальный outbound-контур после проверки снова выключен.

Обновление `2026-06-12` по `row_10`:
- сделан ещё один одиночный тест по следующему номеру:
  - `row_10`
  - `Bourbon, кабинет косметолога`
  - `+79152276263`
  - `request_id = manual.2026-06-12.ROW10.dozhimcheck`
- внешний webhook опять ответил `HTTP 200` с пустым body;
- но live Sheet уже подтвердил итог:
  - `call_result = no_answer`
  - `next_step = callback`
  - `notes_short = Автоответчик: абонент не отвечает, сообщение не оставлено.`
  - `eleven_conv_id = conv_8001ktxtjwrveja8e9kf6cqpxhs7`
- значит на этом machine-case агент уже не оставил spoken-message автоответчику;
- тестовый минимальный outbound-контур после проверки снова выключен.

Обновление `2026-06-12` по backup и точке отката:
- локальная restore-point папка создана здесь:
  - `/home/max/n8n_ai_call_center/backup/2026-06-12_live_agent_restore_point`
- это текущая опорная точка для rollback перед новыми live-правками;
- внутри уже сохранены:
  - live JSON агента;
  - payload-ы июньских patch-правок;
  - snapshot документации;
  - git state;
  - patch локальных изменений.

Обновление `2026-06-12` по дожиму после `нет / не надо / не нужно / неинтересно`:
- предыдущая слишком жёсткая refusal-логика отменена;
- текущая live version:
  - `agtvrsn_0901ktxsrethemqr4prhkw701wr2`
- новое live-правило:
  - короткий отказ сразу после opener больше не считаем финальным автоматически;
  - сначала агент должен понять:
    - это `not_target`
    - или просто низкий текущий интерес;
  - затем один короткий уточняющий вопрос;
  - если контакт релевантный, один rescue-move:
    - SMS,
    - callback менеджера,
    - или одна короткая value-line;
  - если это не их направление вообще — `not_target`;
  - если после уточнения и одного rescue-move отказ сохраняется — `refusal_soft`, короткое завершение, без третьего дожима.
- новый звонок после этой правки ещё не запускался;
- тестовый outbound-контур по-прежнему на паузе.
- артефакты:
  - `backups/2026-06-12_negative_recovery_dozhim/`

Обновление `2026-06-12` по `row_9` и refusal-fix:
- сделан одиночный live-тест:
  - `row_9`
  - `Татьяна`
  - `+79255138351`
  - `request_id = manual.2026-06-12.ROW9.openersecondturn`
  - `conversation_id = conv_8601ktxqpc9ten2br2wktr460qbb`
- подтверждено:
  - opener в live реально звучит в новой wording-форме:
    - `Здравствуйте. Мы официальный представитель липолитика ЛипоЛонг, звоним по поводу сотрудничества для косметологов. Вам это в принципе интересно?`
  - раннего rescue до opener не было;
  - `call_log` уже записал правильный `eleven_conv_id` через bridge-нормализацию.
- вскрытый дефект:
  - на короткое `Нет` агент всё ещё задал лишний уточняющий вопрос;
  - после второго `Нет` агент попытался сказать spoken-closing line.
- после разбора этого звонка была проверена слишком жёсткая промежуточная ветка:
  - `agtvrsn_5001ktxqwz6jer28593yds2asped`
  - она считала flat negative финальным слишком рано.
- эта промежуточная логика уже отменена и не является текущей live-целью;
- актуальная рабочая версия сейчас выше:
  - `agtvrsn_0901ktxsrethemqr4prhkw701wr2`
- тестовый outbound-контур снова снят с публикации;
- новый звонок уже нужно делать не на hard refusal-ветке, а на текущем аккуратном дожиме.
- артефакты:
  - `.runtime/single_call_2026-06-12_row_9_opener_second_turn_check/`
  - `backups/2026-06-12_row9_negative_refusal_trim/`

Обновление `2026-06-12` по wording opener и compact second-turn:
- текущая live version:
  - `agtvrsn_6301ktxp7b4cezb8mc8pba7fxyq9`
- fixed opener теперь такой:
  - `Здравствуйте. Мы официальный представитель липолитика ЛипоЛонг, звоним по поводу сотрудничества для косметологов. Вам это в принципе интересно?`
- второй ход после opener дополнительно ужат:
  - максимум `2` коротких предложения;
  - максимум `1` простой вопрос;
  - для нейтрального ответа, вопроса `о чём звонок`, занятости и живого посредника в prompt теперь даны короткие шаблоны, а не расплывчатое правило.
- патч подтверждён обратным чтением live-конфига через relay-host;
- новый тестовый звонок после этой конкретной правки ещё не запускался;
- тестовый outbound-контур остаётся на паузе.
- артефакты:
  - `backups/2026-06-12_opener_lipolitik_and_second_turn_trim/`

Обновление `2026-06-12` по human-case после pre-opener guard:
- сделан одиночный live-тест:
  - `row_8`
  - `Марина`
  - `+79217897373`
  - `request_id = manual.2026-06-12.ROW8.humanguard`
  - `conversation_id = conv_7701ktxn8n09edytw4rg9s6qcq8y`
- кейс оказался живым человеческим ответом:
  - user:
    - `Добрый день, клиника «Леса мечты». Меня зовут Екатерина.`
  - agent:
    - сразу короткий opener
- что подтверждено этим циклом:
  - ранний `Алло, меня слышно? Вы тут?` до opener больше не вылез;
  - short opener реально стартует сразу после живой реплики человека;
  - bundle `short opener + pre-opener guard` на human-case работает.
- при этом relay снаружи всё ещё может возвращать timeout, даже когда разговор в Eleven реально идёт и завершается;
- значит speech-логика на входе стала лучше, а следующий проблемный слой уже инфраструктурный и/или follow-up logic.
- артефакты:
  - `.runtime/single_call_2026-06-12_row_8_human_guard_check/`
- после цикла минимальный outbound-контур снова снят с публикации;
- тестовый контур снова на паузе.

Обновление `2026-06-12` по pre-opener guard:
- live-agent переведён на version:
  - `agtvrsn_8901ktxmrb3afycrp3qt18caaz4y`
- в prompt добавлен прямой запрет:
  - `Алло, меня слышно? Вы тут?` нельзя говорить до того, как уже прозвучал fixed opener.
- затем сделан одиночный тест:
  - `row_7`
  - `Евгения Волкова`
  - `+79627956556`
  - `request_id = manual.2026-06-12.ROW7.preopenerguard`
  - `conversation_id = conv_3701ktxmtdh8f10ae63mzf63mj7f`
- кейс оказался voicemail:
  - agent не сказал ни opener, ни rescue, ни voicemail-message;
  - agent молча вызвал `call_log`, затем `end_call`
- это хороший знак:
  - новый guard voicemail-ветку не ломает;
  - ранний rescue в этом тесте не вылез.
- но human-case этим циклом ещё не подтверждён, потому что номер ушёл в голосовую почту.
- артефакты:
  - `backups/2026-06-12_preopener_rescue_block/`
  - `.runtime/single_call_2026-06-12_row_7_preopener_guard_check/`
- после цикла минимальный outbound-контур снова снят с публикации;
- тестовый контур снова на паузе.

Обновление `2026-06-12` по короткому opener:
- live-agent переведён на новый короткий opener:
  - `Здравствуйте. Мы официальный представитель ЛипоЛонг, звоним по поводу сотрудничества для косметологов. Вам это в принципе интересно?`
- новая live version:
  - `agtvrsn_4501ktxm8jppehds9her8yamry5n`
- затем сделан одиночный live-тест:
  - `row_6`
  - `Анна`
  - `+79182007944`
  - `request_id = manual.2026-06-12.ROW6.shortopener`
  - `conversation_id = conv_8901ktxmazxpeyavvygxvzdkhgg3`
- короткий opener реально прозвучал в transcript.
- что важно:
  - мгновенного перебивания как на `row_5` уже не было;
  - но до opener снова прозвучал rescue-вопрос `Алло, меня слышно? Вы тут?`, потому что первая реплика распозналась как `...`
- значит:
  - сам новый opener оставляем;
  - следующий дефект уже не он, а слишком ранний rescue до opener.
- артефакты:
  - `backups/2026-06-12_short_opener_try/`
  - `.runtime/single_call_2026-06-12_row_6_short_opener_check/`
- после цикла минимальный outbound-контур снова снят с публикации;
- тестовый звонковый контур снова на паузе.

Обновление `2026-06-12` по одиночному `row_5` на `turn_timeout = 1.0`:
- сделан один новый одиночный тест:
  - `row_5`
  - `Анаит`
  - `+79879860736`
  - `request_id = manual.2026-06-12.ROW5.turn1_0`
- relay отработал штатно:
  - `Upstream 200 (15701ms, 139 bytes)`
  - `conversation_id = conv_0401ktxjmstcfzvs23vga1ah97h5`
- новый разговор действительно прошёл уже на текущей минимальной live version:
  - `agtvrsn_5001ktxj73befn6bgdqbd9sckd9s`
- по сырым turn-метрикам старт ответа после человеческой реплики быстрый:
  - `asr trailing = 0.071s`
  - `llm ttfb = 0.489s`
  - `tts ttfb = 0.124s`
  - `llm first sentence = 0.678s`
- transcript короткий:
  - user: `Алло!`
  - agent: fixed opener
  - user later перебивает: `Я тебе говорю,`
- вывод на сейчас:
  - raw latency уже не главный тормоз;
  - следующий дефект — слишком тяжёлый opener, который провоцирует перебивание и непонимание в начале разговора;
- артефакты:
  - `.runtime/single_call_2026-06-12_row_5_turn1_0_check/`
- после цикла минимальный контур снова снят с публикации; в последнем старте `n8n` строки `Start Active Workflows` уже нет;
- весь тестовый outbound-контур снова считается поставленным на паузу.

Обновление `2026-06-12` по минимальному `turn_timeout`:
- после предыдущего latency-патча live ещё работал на:
  - `turn_timeout = 1.2`
  - `turn_eagerness = eager`
  - `speculative_turn = true`
- дальше проверен нижний предел этого же регулятора;
- Eleven API вернул прямое ограничение:
  - `turn timeout` не может быть меньше `1.0` секунды
- затем live-agent успешно пропатчен на минимально допустимое значение:
  - `turn_timeout = 1.0`
  - `turn_eagerness = eager`
  - `speculative_turn = true`
- новая live version:
  - `agtvrsn_5001ktxj73befn6bgdqbd9sckd9s`
- сохранены артефакты:
  - `backups/2026-06-12_human_answer_latency_trim_07/main_turn_timeout_1_0_payload.json`
  - `backups/2026-06-12_human_answer_latency_trim_07/current_ai_call_agent_1.after_turn_1_0.json`
- это текущая боевая версия по latency на сейчас;
- новый проверочный звонок после этого патча ещё не запускался;
- весь звонковый контур всё ещё на паузе.

Обновление `2026-06-12` по human-answer latency:
- через Eleven API подтверждено, что до новой правки live реально работал на:
  - `turn_timeout = 2.0`
  - `turn_eagerness = normal`
  - `speculative_turn = false`
- затем live-agent пропатчен точечно:
  - `turn_timeout = 1.2`
  - `turn_eagerness = eager`
  - `speculative_turn = true`
- новая live version:
  - `agtvrsn_0401ktxhpa5rfw39gs2evg7cqja3`
- после этого сделаны два одиночных живых теста:
  - `conv_6501ktxhr0vre8580xw18xfg0eg8` (`row_3`)
  - `conv_4601ktxhxdjzf90shjjb1faw4dg9` (`row_4`)
- по техническим метрикам opener now starts much faster after finalized human speech:
  - `row_3 opener`:
    - `asr trailing = 0.048s`
    - `llm ttfb = 0.555s`
    - `tts ttfb = 0.111s`
  - `row_4 opener`:
    - `asr trailing = 0.128s`
    - `llm ttfb = 0.375s`
    - `tts ttfb = 0.117s`
- значит raw техническая задержка после human answer уже поджата;
- визуальный разрыв по `time_in_call_secs` в карточке всё ещё может казаться длиннее из-за округления секунд и длины самой реплики;
- после тестов минимальные workflow снова выключены;
- весь звонковый контур снова на паузе.

Обновление `2026-06-12` по `row_2` после `RELAY_TIMEOUT=20`:
- сделан один новый одиночный цикл по:
  - `row_2`
  - `+79299679869`
  - `Акимова Ксения Игоревна`
  - `request_id = manual.2026-06-12.ROW2.relay20.check`
- manual webhook вернул:
  - `HTTP 200`
  - `call_requested`
  - `conversation_id = conv_4401ktxeqcgpe849zebbr4w7hw82`
- relay journal впервые для этого слоя дал не timeout, а чистый accepted-path:
  - `Upstream 200 (6138ms, 139 bytes)`
  - `success = true`
  - `Outbound call initiated`
- detail по `conv_4401ktxeqcgpe849zebbr4w7hw82` совпал с outgoing identity полностью:
  - `user_id = row_2`
  - `external_number = +79299679869`
  - `request_id = manual.2026-06-12.ROW2.relay20.check`
  - `status = done`
  - `error = null`
- это был живой ответ, не machine-line:
  - user: `Клиника «Визави», меня зовут Марина. Добрый день.`
  - agent затем дал fixed opener
- но разговор завершился рано и до `call_log` этим циклом не дошёл:
  - `tool_names = null`
  - `transcript_count = 4`
- после проверки минимальные workflow снова выключены;
- весь звонковый контур снова на паузе.

Обновление `2026-06-12` по relay `20s`:
- live relay-host `151.241.228.232` поднят с:
  - `RELAY_TIMEOUT=16`
  на:
  - `RELAY_TIMEOUT=20`
- backup:
  - `/root/.eleven_outbound_relay.env.bak-2026-06-12_09-55-25`
- `eleven-outbound-relay.service` успешно перезапущен;
- `/health` отвечает штатно;
- локальный source-of-truth обновлён:
  - `scripts/eleven_outbound_relay_server.py`
  - default timeout теперь `20`
- отдельно перепроверено:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `active=false`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `active=false`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `active=false`
  - `VOICE_INBOUND_AGENT (draft)` = `active=false`
- новый звонок после этого шага ещё не запускался;
- весь звонковый контур всё ещё на паузе.

Обновление `2026-06-12` по `row_17` после `RELAY_TIMEOUT=16`:
- сделан ещё один одиночный техтест по:
  - `row_17`
  - `+79012091111`
  - `request_id = manual.2026-06-12.ROW17.relay16.check`
- relay journal подтвердил точный outgoing identity именно этого цикла;
- relay снова умер по timeout:
  - `Upstream failed (16064ms): The read operation timed out`
- но в отличие от цикла на `14s`, новый failed conversation уже появился в Eleven:
  - `conv_6001ktx8q4n6e5hsww1ssxdhvj7y`
  - `status = failed`
  - `error.reason = sip request timed out`
  - `user_id = row_17`
  - `external_number = +79012091111`
- значит `16s` уже лучше диагностически, чем `14s`: длинный upstream-case теперь хотя бы materialize-ится;
- отдельно зафиксировано тонкое provider-side расхождение:
  - detail по новому `conv_6001...` вернул старый `request_id` от предыдущего цикла по `row_17`,
  - хотя relay отправлял новый `request_id`;
- после проверки минимальные workflow снова выключены;
- весь звонковый контур снова на паузе.

Обновление `2026-06-12` по relay `16s`:
- live relay-host `151.241.228.232` поднят с:
  - `RELAY_TIMEOUT=14`
  на:
  - `RELAY_TIMEOUT=16`
- backup:
  - `/root/.eleven_outbound_relay.env.bak-2026-06-12_09-47-52`
- `eleven-outbound-relay.service` успешно перезапущен;
- `/health` отвечает штатно;
- локальный source-of-truth обновлён:
  - `scripts/eleven_outbound_relay_server.py`
  - default timeout теперь `16`
- новый звонок после этого шага ещё не запускался;
- весь звонковый контур всё ещё на паузе.

Обновление `2026-06-12` по повторному `row_17`:
- в первой таблице после `row_18` новых callable-строк уже нет, поэтому следующим техническим повторным кандидатом взят `row_17`;
- снова был поднят только минимальный outbound-контур;
- manual webhook отправлен на:
  - `row_17`
  - `+79012091111`
  - `request_id = manual.2026-06-12.ROW17.relay14.recheck`
- relay journal с enriched logging подтвердил точный identity payload:
  - `to_number = +79012091111`
  - `user_id = row_17`
  - `lead_id = row_17`
  - `source_record_key = row_17`
  - `request_id = manual.2026-06-12.ROW17.relay14.recheck`
- но upstream снова не успел ответить даже при `RELAY_TIMEOUT=14`:
  - `Upstream failed (14034ms): The read operation timed out`
- свежий список Conversations API не показал нового materialized conversation по этому циклу;
- значит `14s` уже помогает не для всех outbound-case;
- после проверки минимальные workflow снова выключены;
- весь звонковый контур снова на паузе.

Обновление `2026-06-11` по циклу `row_18` после `RELAY_TIMEOUT=14`:
- снова был поднят только минимальный outbound-контур;
- manual webhook ушёл на:
  - `row_18`
  - `+71660761251`
  - `request_id = manual.2026-06-11.ROW18.relay14.identitycheck`
- relay journal с новым identity summary подтвердил точный payload:
  - `to_number = +71660761251`
  - `user_id = row_18`
  - `lead_id = row_18`
  - `source_record_key = row_18`
  - `request_id = manual.2026-06-11.ROW18.relay14.identitycheck`
- на этот раз relay уже дождался upstream body:
  - `Upstream 200 (11575ms, 177 bytes)`
  - ответ содержал:
    - `success = false`
    - `SIP 403 Forbidden`
    - `conversation_id = conv_4001ktvcbehvedcvt5jfsq6b4d0b`
- detail по `conv_4001ktvcbehvedcvt5jfsq6b4d0b` совпал с relay identity полностью:
  - `user_id = row_18`
  - `external_number = +71660761251`
  - `request_id = manual.2026-06-11.ROW18.relay14.identitycheck`
- значит:
  - `RELAY_TIMEOUT=14` уже достаточно, чтобы дожидаться upstream JSON;
  - identity-trace на новом цикле совпадает end-to-end;
  - прошлый кейс `row_17 -> row_14` пока выглядит как единичная аномалия;
- после проверки минимальные workflow снова выключены;
- весь звонковый контур снова на паузе.

Обновление `2026-06-11` по relay `14s` и enriched logging:
- после цикла `row_17` live relay поднят ещё на один маленький шаг:
  - backup: `/root/.eleven_outbound_relay.env.bak-2026-06-11_14-58-10`
  - `RELAY_TIMEOUT=14`
  - `RELAY_RETRY_COUNT=0`
  - `RELAY_RETRY_DELAY_MS=500`
- runtime relay на сервере синхронизирован с локальным source-of-truth:
  - `/opt/eleven_outbound_relay.py`
- в relay-лог теперь перед каждым upstream-call пишется identity summary:
  - `to_number`
  - `user_id`
  - `lead_id`
  - `source_record_key`
  - `request_id`
- это нужно, чтобы на следующем одиночном вызове сразу увидеть, где ломается связка `row/request_id`;
- дополнительно проверено:
  - размер row14-payload = `546 bytes`
  - размер row17-payload = `574 bytes`
  - в последнем relay log было именно `574 bytes`
- значит relay реально отправлял `row_17`, а расхождение `row_17 -> row_14` рождается уже после relay;
- новый звонок после перехода на `14s` ещё не запускался;
- весь звонковый контур всё ещё на паузе.

Обновление `2026-06-11` по одиночному `row_17` циклу после `RELAY_TIMEOUT=12`:
- был поднят только минимальный outbound-контур:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
- после рестарта `n8n` эти три workflow реально активировались;
- отправлен один manual webhook на следующий номер по порядку:
  - тестовый lead: `row_17`
  - номер: `+79012091111`
  - `request_id = manual.2026-06-11.ROW17.relay12check`
- внешний webhook снова вернул:
  - `HTTP 200`
  - body пустой
- relay-host всё ещё упёрся в timeout:
  - `Upstream failed (12052ms): The read operation timed out`
- но теперь подтверждено, что Eleven всё же создаёт failed conversation:
  - `conv_1901kteg8mpwe7har7hxep69cf56`
  - `status = failed`
  - `error.reason = sip request timed out`
- значит `12` секунд всё ещё недостаточно для устойчивого accepted/rejected ответа upstream;
- отдельно всплыло расхождение identity-пакета:
  - detail этого failed conversation вернулся с `user_id = row_14`
  - и `request_id = manual.2026-06-06.ROW14.after_abonent_rule`
  хотя сам webhook цикла был отправлен как `row_17 / manual.2026-06-11.ROW17.relay12check`
- после проверки минимальные workflow снова выключены;
- весь звонковый контур снова на паузе.

Обновление `2026-06-11` по relay timeout:
- live relay-host `151.241.228.232` отдельно перепроверен;
- снят journal `eleven-outbound-relay.service` и подтверждено, что июньские `row_13` и `row_14` падали не из-за prompt, а из-за timeout-path:
  - `Upstream failed (~10025-10031 ms): The read operation timed out`
- это был повторяемый технический blocker до создания conversation;
- сделан минимальный live fix:
  - backup: `/root/.eleven_outbound_relay.env.bak-2026-06-11_14-38-48`
  - `RELAY_TIMEOUT=12`
  - `RELAY_RETRY_COUNT=0`
  - `RELAY_RETRY_DELAY_MS=500`
- `eleven-outbound-relay.service` успешно перезапущен;
- `/health` с prod-сервера отвечает штатно;
- новый звонок после этого таймаут-шага ещё не запускался;
- весь звонковый контур всё ещё на паузе до следующего одиночного теста.

Обновление `2026-06-06` по следующему одиночному циклу `row_14`:
- тест пошёл по:
  - `row_14`
  - `+79963649952`
  - `Mila Fon`
- три минимальных workflow временно поднимались и были в валидном состоянии:
  - `active = true`
  - `activeVersionId = versionId`
- manual `POST /webhook/eleven/outbound-call` снова ответил:
  - `HTTP 200`
  - body пустой
- но реальный разговор не создался:
  - в Eleven не появился `row_14`
  - relay-host записал:
    - `POST /eleven/outbound-call HTTP/1.1 502`
- значит это снова технический upstream failure до speech-stage и до `call_log`
- после цикла минимальные workflow снова выключены:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `false`
  - `activeVersionId = null`
- контур снова на паузе.

Обновление `2026-06-06` по жёсткому правилу `абонент`:
- live `Main` обновлён prompt-only patch:
  - `version_id = agtvrsn_4301ktee0x3kf8es9y3f950rjzr8`
- любое сервисное упоминание:
  - `абонент`
  - `абоненту`
  - `абонентам`
  теперь должно сразу трактоваться как автоответчик / message-service
- отдельные буквальные примеры тоже зашиты в live:
  - `что передать абоненту?`
  - `что бы вы хотели передать абоненту?`
  - `что сказать абоненту?`
  - `я передам абоненту`
  - `если абонент захочет с вами связаться`
- нужное поведение:
  - не продавать;
  - не уточнять;
  - не оставлять callback;
  - не давать контакт менеджера;
  - сразу `call_log` и silent `end_call`
- новый звонок после этой правки ещё не делался;
- весь контур всё ещё на паузе.

Обновление `2026-06-06` по следующему одиночному циклу после fix:
- `row_12` был пропущен:
  - `do_not_call = true`
  - причина: `похоже на организацию`
- следующий callable тест пошёл по:
  - `row_13`
  - `+79370639452`
  - `Врач-косметолог, трихолог Елена Николаевна Шишкина/Бренд «Доктор Шик»`
- три минимальных workflow временно поднимались и были в валидном состоянии:
  - `active = true`
  - `activeVersionId = versionId`
- manual `POST /webhook/eleven/outbound-call` ответил:
  - `HTTP 200`
  - body пустой
- но реальный разговор не создался:
  - в Eleven не появился `row_13`
  - relay-host записал:
    - `POST /eleven/outbound-call HTTP/1.1 502`
- значит это технический upstream failure до speech-stage и до `call_log`
- после цикла минимальные workflow снова выключены:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `false`
  - `activeVersionId = null`
- весь контур снова на паузе.

Обновление `2026-06-06` по точечным fix после `row_11`, без нового звонка:
- live `Main` в ElevenLabs обновлён:
  - `version_id = agtvrsn_7601ktec2xpde6sbn0s4t2heszyz`
- global rescue-таймер больше не должен конфликтовать с `human-answer gate`:
  - `turn_timeout = 2.0`
  - `soft_timeout_config.timeout_seconds = -1.0`
  - `soft_timeout_config.message = "Алло, меня слышно? Вы тут?"`
  - технически message оставлен непустым для валидности API, но сам global soft-timeout выключен
- rescue-вопрос теперь должен жить только как prompt-правило post-opener/human phase, а не как общий таймер разговора
- live schema `call_log` в Eleven теперь дополнена полем:
  - `conversation_id`
  - и `conversation_id`, и `eleven_conv_id` привязаны к `system__conversation_id`
- live `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` повторно импортирован из локального draft:
  - workflow id: `kZSdJrsAHWWIC2l6`
  - `Tool | Normalize Call Log` теперь реально умеет:
    - резать placeholder-значения;
    - отбрасывать сокращённые и byte-like `conv_*`;
    - брать канонический `conversationId` из `body.conversation_id`;
    - использовать его как fallback для `eleven_conv_id` и `source_record_key`
- новый live-звонок после этих fix ещё не запускался
- весь звонковый контур всё ещё на паузе.

Обновление `2026-06-06` по одиночному тесту `row_11`:
- сделан следующий последовательный звонок по:
  - `row_11`
  - `+79533940071`
  - `Татьяна Голубева Косметология, бьюти услуги`
- новый разговор:
  - `conv_1301kte9dps8ejfvk7fzy4zstvxs`
  - `version_id = agtvrsn_9401kte963xcf2j87t1wervbdtv5`
- выявлено реальное поведение новой схемы:
  - на первом `...` rescue прозвучал слишком рано, ещё до нормального human-answer:
    - `Алло, меня слышно? Вы тут?`
  - затем user ответил:
    - `Алло?`
  - потом agent уже дал полный opener;
  - позже после второго `...` agent корректно сделал:
    - `call_log(no_answer)`
    - silent `end_call`
- значит `one rescue only` работает, но есть конфликт:
  - global `soft_timeout_config` срабатывает до нужной пост-opener фазы;
  - это конфликтует с `human-answer gate`
- одновременно в `call_log` снова ушёл битый `eleven_conv_id`:
  - `conv_8e2e7e7e7e7e4e7e8e7e7e7e7e7e7e7e`
  - вместо `conv_1301kte9dps8ejfvk7fzy4zstvxs`
- после теста минимальные workflow снова выключены;
- весь контур опять на паузе.

Обновление `2026-06-06` по правилу тишины `2s -> rescue -> 2s -> hangup`:
- live-логика тишины после живого ответа ещё раз ужата:
  - после opener и уже подтверждённого live-human ответа;
  - если около `2` секунд нет осмысленного ответа;
  - agent один раз говорит:
    - `Алло, меня слышно? Вы тут?`
  - если после этого ещё около `2` секунд нет нормального ответа;
  - agent пишет `call_log(no_answer)` и молча кладёт трубку
- rescue-вопрос нельзя повторять второй раз;
- live-config теперь такой:
  - `turn_timeout = 3.2`
  - `soft_timeout_config.timeout_seconds = 2.0`
  - `soft_timeout_config.message = "Алло, меня слышно? Вы тут?"`
  - `max_soft_timeouts_per_generation = 1`
- новая live version:
  - `agtvrsn_9401kte963xcf2j87t1wervbdtv5`
- новый звонок после этой правки ещё не запускался;
- весь контур всё ещё на паузе.

Обновление `2026-06-06` по rescue-вопросу после тишины:
- правило уточнено ещё жёстче:
  - после opener и уже подтверждённого живого ответа agent может задать только один rescue-вопрос:
    - `Алло, меня слышно? Вы тут?`
  - если после него ещё около `2` секунд нет осмысленного ответа, agent должен сам завершить звонок;
  - повторять rescue-вопрос нельзя.
- live-config:
  - `turn_timeout = 3.2`
  - `soft_timeout_config.timeout_seconds = 2.0`
  - `soft_timeout_config.message = "Алло, меня слышно? Вы тут?"`
  - `max_soft_timeouts_per_generation = 1`
- новая live version:
  - `agtvrsn_9401kte963xcf2j87t1wervbdtv5`
- новый звонок после этой уточняющей правки ещё не запускался;
- контур всё ещё на паузе.

Обновление `2026-06-06` по одиночному тесту `row_10`:
- сделан следующий последовательный звонок по:
  - `row_10`
  - `+77077080155`
  - `svetlayaa73`
- новый разговор:
  - `conv_4301kte251sdef79z7m4345qs744`
  - `status = failed`
  - `version_id = null`
- реального разговора не было;
- причина:
  - `INVITE failed: sip status: 480: Temporarily Unavailable (SIP 480)`
- transcript пустой;
- значит новый `human-silence rescue` этим тестом не проверился;
- после теста минимальные workflow снова выключены и `n8n-server-n8n-1` снова `running|healthy`.

Обновление `2026-06-06` по тишине после opener:
- по новой пользовательской правке молчание после opener больше не должно сразу вести в silent finish;
- теперь если:
  - уже был подтверждён живой человек;
  - agent уже произнёс opener;
  - и затем около `3` секунд нет осмысленного ответа;
  agent должен один раз спросить:
  - `Алло, меня слышно? Вы тут?`
- это исключение действует только для human-ветки после opener;
- на IVR, voicemail, screening, message-service, ringback и music этот rescue-вопрос запрещён;
- live-config уже обновлён:
  - `turn_timeout = 3.2`
  - `soft_timeout_config.timeout_seconds = 3.0`
  - `soft_timeout_config.message = "Алло, меня слышно? Вы тут?"`
- новая live version:
  - `agtvrsn_0401kte1n4fhek8snba466ra39t0`
- новый звонок после этой правки ещё не запускался;
- весь контур всё ещё на паузе.

Обновление `2026-06-06` по одиночному тесту `row_9` после latency-trim:
- сделан следующий последовательный звонок по:
  - `row_9`
  - `+79255138351`
  - `Татьяна`
- новый разговор:
  - `conv_8401kte14mqmeetatxqfh40cqjqv`
  - `version_id = agtvrsn_4401kte0xffsfm1rnq9bbtajj65y`
- на живом ответе ускорение подтвердилось:
  - user `Алло!` на `time_in_call_secs = 1`
  - agent opener уже на `time_in_call_secs = 2`
- метрики старта:
  - `ASR trailing ~= 0.162s`
  - `LLM TTFB ~= 0.410s`
  - `LLM first sentence ~= 0.516s`
  - `TTS TTFB ~= 0.182s`
- дальше человек дал только:
  - `...`
- agent корректно отработал как no-answer после opener:
  - `call_log`
  - silent `end_call`
- но появился новый регресс в трассировке:
  - вместо текущего `conv_8401kte14mqmeetatxqfh40cqjqv`
  - в `call_log` ушёл мусорный `eleven_conv_id = conv_65e2e2e7e2e2e7e2e2e7e2e2e7e2e2e7`
- после теста минимальные workflow снова выключены и `n8n-server-n8n-1` снова `running|healthy`.

Обновление `2026-06-06` по задержке после живого ответа:
- по разговору `conv_2701ktdzmjz7fxqrmfczhea65r56` подтверждено, что почти вся заметная пауза была не в LLM/TTS, а в turn-taking ожидании;
- разбивка по метрикам:
  - `convai_asr_trailing_service_latency ~= 0.185s`
  - `convai_llm_service_ttfb ~= 0.476s`
  - `convai_llm_service_ttf_sentence ~= 0.574s`
  - `convai_tts_service_ttfb ~= 0.351s`
- чтобы сократить ощущаемую паузу, live `Main` поджат безопасным шагом:
  - `turn_timeout: 4.0 -> 3.2`
  - `turn_eagerness = normal` без изменений
  - `speculative_turn = false` без изменений
- новая live version:
  - `agtvrsn_4401kte0xffsfm1rnq9bbtajj65y`
- новый звонок после этой правки ещё не запускался;
- весь контур по-прежнему стоит на паузе между одиночными циклами.

Обновление `2026-06-06` по одиночному тесту `row_8`:
- сделан следующий последовательный звонок по:
  - `row_8`
  - `+79217897373`
  - `Марина`
- для теста временно поднимались только:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
- новый разговор:
  - `conv_2701ktdzmjz7fxqrmfczhea65r56`
  - `version_id = agtvrsn_1001ktbys8ftfpys5gykctxrqka5`
- это уже был живой ответ, а не voicemail:
  - user: `«Лицо мечты», администратор Ольга, здравств`
- главное подтверждение:
  - agent стартовал ровно фиксированным двухфразным opener-блоком;
  - в `original_message` зафиксирован полный opener:
    - `Здравствуйте, наша компания является официальным представителем липолитика премиум класса ЛипоЛонг, предлагаем вам сотрудничество с нашей компанией на выгодных условиях. А еще, сотрудничая с нами, вы можете быть уверены на сто процентов, что получаете оригинальную продукцию и не рискуете попасть на подделку.`
- собеседник оборвал звонок очень рано:
  - `termination_reason = Client disconnected: 1000`
- поэтому до `call_log` и `end_call` agent не дошёл;
- после теста минимальные workflow снова выключены и `n8n-server-n8n-1` снова `running|healthy`.

Обновление `2026-06-05` по одиночному тесту `row_7`:
- сделан следующий последовательный звонок по:
  - `row_7`
  - `+79627956556`
  - `Евгения Волкова`
- разговор:
  - `conv_2101ktbynrjkffsaw7ttmhvxjxcd`
  - `version_id = agtvrsn_4801ktbw46wde348tvxnf4ewx54q`
- линия ушла в voicemail:
  - `Сообщаем, что абонент не отвечает... голосовой почтовый ящик...`
- agent корректно не начал opener, а сделал:
  - `call_log`
  - silent `end_call`
- но в `call_log` обнаружился reuse-бағ:
  - вместо текущего `conv_2101ktbynrjkffsaw7ttmhvxjxcd` ушёл прошлый `conv_1901ktbtzw94ek4rzngccvtqka9k`
- после этого live `Main` ещё раз подправлен:
  - убран буквальный valid-example старого `conv_1901...`;
  - добавлено прямое правило не переиспользовать `conv_*` из прошлого звонка/примера/tool-result;
  - новая live version:
    - `agtvrsn_1001ktbys8ftfpys5gykctxrqka5`
- после теста минимальные workflow снова выключены.

Обновление `2026-06-05` по одиночному тесту `row_6`:
- после prompt-fix по `eleven_conv_id` был сделан следующий последовательный одиночный звонок по:
  - `row_6`
  - `+79182007944`
  - `Анна`
- новый разговор:
  - `conv_5801ktbw5twre5a8srggqhzqh5yv`
  - `version_id = agtvrsn_4801ktbw46wde348tvxnf4ewx54q`
- это снова был machine/silence path:
  - user: `...`
  - agent: `call_log`
  - agent: silent `end_call`
- главное исправление подтверждено:
  - в `call_log` теперь ушёл уже правильный полный `eleven_conv_id`:
    - `conv_5801ktbw5twre5a8srggqhzqh5yv`
  - вместе с ним корректно записались:
    - `lead_id = row_6`
    - `source_record_key = row_6`
    - `phone_primary = +79182007944`
- запись ушла в Sheet:
  - `'Лиды_обзвон'!A42:AM42`
- после теста минимальные workflow снова выключены.

Обновление `2026-06-05` по одиночному тесту `row_5`:
- после восстановления точного opener был сделан следующий последовательный одиночный звонок по:
  - `row_5`
  - `+79879860736`
  - `Анаит`
- во время старта найден отдельный technical blocker:
  - у минимальных workflow `ELEVEN_OUTBOUND_CALL_BRIDGE`, `ELEVEN_TOOL_CALL_LOG_BRIDGE`, `ELEVEN_TOOL_CONTEXT_BRIDGE` был пустой `activeVersionId`;
  - из-за этого webhook сначала не поднимался и отдавал `Active version not found`;
  - `activeVersionId` выровнен с `versionId`, после чего test-call реально пошёл.
- новый разговор:
  - `conv_1901ktbtzw94ek4rzngccvtqka9k`
  - `version_id = agtvrsn_7501ktbswz9aemy9xa71r5nnf0wt`
- это оказался machine/no-answer path:
  - линия сначала проговорила `Продолжаем дозваниваться. Оставайтесь на линии.`
  - потом `Абонент не берёт трубку...`
  - агент корректно сделал `skip_turn`, потом `call_log`, потом silent `end_call`
- что уже работает хорошо:
  - agent не начал sales opener на машинной линии;
  - agent не оставил spoken farewell;
  - в `call_log` реально доехали:
    - `lead_id = row_5`
    - `source_record_key = row_5`
    - `phone_primary = +79879860736`
- что ещё сломано:
  - `eleven_conv_id` ушёл как `conv_5`, а не как реальный `conv_1901ktbtzw94ek4rzngccvtqka9k`
- после теста минимальные workflow снова выключены.

Обновление `2026-06-05` по первому opener:
- live `Main` исправлен после регрессии укороченного opener;
- текущая первая живая реплика агента теперь снова должна идти ровно фиксированным двухфразным блоком:
  - `Здравствуйте, наша компания является официальным представителем липолитика премиум класса ЛипоЛонг, предлагаем вам сотрудничество с нашей компанией на выгодных условиях. А еще, сотрудничая с нами, вы можете быть уверены на 100%, что получаете оригинальную продукцию и не рискуете попасть на подделку`
- после этого блока агент должен остановиться и только следующим ходом, при необходимости, задать:
  - `Вам это в принципе интересно?`
- сам звонковый контур при этом остаётся на паузе.

## 1. Боевой контур

Сейчас боевой маршрут такой:
- `Mango -> Asterisk -> ElevenLabs -> n8n`

Что реально задействовано:
- Mango как телефония;
- Asterisk как SIP bridge;
- ElevenLabs как голосовой агент;
- n8n как webhook/tools/логика интеграции;
- `postgres_memory` как memory-слой;
- `call_center` Postgres как operational data layer;
- основной `n8n` database runtime теперь тоже на Postgres (`n8n_prod`), а не на локальном SQLite;
- `postgrest` и `adminer` как часть текущего серверного контура;
- Google Sheet как лог звонков через `call_log`.

## 2. Что работает сейчас

Работает:
- основной live `n8n` после миграции `SQLite -> Postgres`;
- live звонковый контур;
- `context_fetch`;
- `call_log`;
- `send_sms_info`;
- PostgreSQL memory stack;
- `call_center` Postgres;
- `postgrest`;
- `adminer`;
- knowledge chunks и script steps в памяти;
- логирование результатов разговора.

Обновление `2026-05-22` по live n8n:
- секреты звонкового контура больше не должны храниться в workflow JSON или execution payloads;
- серверные env-файлы с секретами:
  - `/home/aicore/n8n-ai-clean/.env.callcenter`;
  - `/home/aicore/n8n-server/.env.callcenter`;
- compose-файлы в `/home/aicore/n8n-ai-clean/` и `/home/aicore/n8n-server/` подключают эти env-файлы к n8n;
- workflow `VOICE_INBOUND_AGENT`, `ELEVEN_TOOL_CALL_LOG_BRIDGE`, `AUTODIAL_DISPATCHER`, `ELEVEN_TOOL_SEND_SMS_BRIDGE` читают ElevenLabs/Mango/Google секреты через `$env.*`;
- для этих workflow отключено сохранение success/error execution payloads;
- старые execution payloads с секретами очищены;
- контрольный `call_log` smoke после правки прошёл успешно и записал `smoke_secret_hardening_envflag` в Google Sheet, диапазон `'Лиды_обзвон'!A905:AM905`.

Обновление `2026-05-26` по основному `n8n`:
- основной live `n8n` переведён с SQLite на Postgres;
- новые БД:
  - `n8n_stage`
  - `n8n_prod`
- боевой контейнер читает дополнительный env-файл:
  - `/home/aicore/n8n-server/.env.n8n_postgres`
- owner/project/settings и active workflow state перенесены из live SQLite в `n8n_prod`;
- после cutover:
  - `https://www.n-8-n.site` отвечает `HTTP 200`;
  - контейнер `n8n-server-n8n-1` healthy;
  - в `n8n_prod` подтверждены `32` workflows, `13` credentials и `22` active workflow;
- старый SQLite snapshot оставлен как rollback-резерв:
  - `/var/lib/docker/volumes/n8n-server_n8n_data/_data/database.sqlite`
  - полный backup-пакет: `/home/aicore/backups/n8n/sqlite_to_postgres_2026-05-26/`
- После первого post-migration smoke найден и исправлен отдельный live-env дефект:
  - `docker-compose.yml` для `n8n` поначалу подключал `.env.n8n_postgres`, но не подключал `.env.callcenter`;
  - из-за этого внутри контейнера не было `ELEVENLABS_API_KEY` и `ELEVEN_OUTBOUND_RELAY_TOKEN`, и `eleven/outbound-call` сначала возвращал `provider_rejected / forbidden`;
  - compose обновлён, `n8n` пересоздан, secrets снова видны в runtime.
- После controlled re-activation/restarт smoke-проверки дали:
  - `voice-agent-inbound` -> `200 OK`
  - `eleven/tool/context` -> `200 OK`
  - `eleven/tool/send-sms` -> `200 OK`
  - `eleven/outbound-call` -> `ok=true`, `action=call_requested`, есть `conversation_id` и `sip_call_id`
  - `eleven/tool/call-log` -> `ok=true`, запись ушла в live Google Sheet
- Важное уточнение по инфраструктуре:
  - отдельного live MySQL/MariaDB слоя для основного `n8n` сейчас нет;
  - текущий live runtime = `Postgres` + `postgres_memory` + `call_center`.
- `2026-05-26` выполнен маленький ручной smoke на `2-3` outbound-звонка уже после migration fix:
  - `row_2` и `row_4` вернули `call_requested` с реальными `conversation_id` от Eleven;
  - `row_3` в live Sheet отразился как `send_kp_pending_callback / call_manager`;
  - в этом коротком прогоне не появилось новых `provider_rejected` / `outbound_request_failed`.
- `2026-05-26` по кейсу `conv_1201ksj4b9hnedrs3nphhjqjbmeq` добавлено новое screening-правило:
  - если линия только выясняет цель звонка, сроки ответа, предлагает manager callback/SMS и при этом звучит как шаблонный screening/auto-answer, это не считать полезным handoff;
  - такие кейсы больше не должны попадать в обычный полезный secretary/intermediary сценарий.
- `2026-06-01` после нового разбора live-conversations добавлены ещё более буквальные screening/auto-answer patterns:
  - `в течение какого времени нужно дать ответ`
  - `нужно передать ещё что-то`
  - `что-то хотите добавить`
  - `я всё передам абоненту`
  - `зафиксировал информацию`
  - такие фразы теперь считаются не полезным человеческим handoff, а screening/intermediary assistant pattern;
  - нужное поведение: не продолжать sales-диалог, не предлагать SMS/manager callback, быстро логировать `no_answer/busy` и завершать.
- `2026-06-01` отдельно подтверждён ещё один дефект live-поведения:
  - на тишине и transcript `...` agent всё ещё мог говорить service-фразы вида:
    - `Пожалуйста, подскажите, вы на связи? Могу продолжить разговор.`
    - `Вы меня слышите? Если удобно, дайте знать, чтобы я могла продолжить.`
  - после live patch это поведение должно считаться ошибочным и запрещённым: при `...` и пустой тишине нужен `call_log(no_answer)` и silent `end_call`.
- `2026-06-01` колл-центр принудительно поставлен на паузу:
  - `VOICE_INBOUND_AGENT (draft)` снят с публикации и выключен;
  - `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2` также выключен;
  - цель: не допускать новых звонков, пока не будет завершён разбор автоответчиков и screening-линий.
- `2026-06-04` выполнен один controlled manual cycle по новой базе частных косметологов:
  - временно включался только `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` (`sHTbALayEZdy8Mzs`);
  - тестовый лид: `row_3 / +79657700655 / Александр`;
  - первый запрос ушёл в relay-timeout `~10058 ms`, но затем подтвердилось, что реальный разговор всё равно произошёл:
    - `conversation_id = conv_3301kt8tj8vyftq97vwbc0jn7c96`
    - линия ушла на голосовую почту
    - agent залогировал `no_answer / callback`
    - строка в Google Sheet ушла без `lead_id / source_record_key / eleven_conv_id`
  - второй запрос по тому же лиду дал уже чистый provider/SIP reject:
    - `conversation_id = conv_7801kt8tnrkje75sydp92kfw06wj`
    - `error.reason = max auth retry attempts reached for SIP invite`
    - accepted-time не было
  - после этого live `Main` дополнительно ужесточён:
    - voicemail/message-service должен завершаться без spoken-farewell
    - `call_log` обязан включать identity package
  - по завершении цикла `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` снова выключен.
  - после отдельной команды пользователя `ПОКА ОСТАНОВИ ВСЕ` остановлены и tool-мосты:
    - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `inactive`
    - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `inactive`
    - `ELEVEN_TOOL_SEND_SMS_BRIDGE (draft)` = `inactive`
  - итог: весь звонковый контур сейчас полностью на паузе.
- `2026-06-05` на этой паузе отдельно ужесточён сам `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`:
  - добавлен identity guard перед записью в Google Sheet;
  - bare `call_log` без identity-пакета больше не должен append'иться в таблицу;
  - для `elevenlabs` теперь обязательны:
    - `lead_id`
    - `caller`
    - `phone_primary`
    - `source_record_key`
    - `eleven_conv_id`
  - для `autodial_dispatcher` оставлен мягкий режим:
    - `lead_id`
    - `phone_primary`
    - `source_record_key`
    - пустой `eleven_conv_id` допускается на lock / outbound-failure строках;
  - при ошибке identity workflow должен вернуть `warning = missing_identity_package` и не писать мусорную строку в Sheet.
- `2026-06-05` после этого выполнен один controlled voicemail-test по `row_3 / +79657700655 / Александр`:
  - временно включались только:
    - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
    - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
    - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
  - новый разговор:
    - `conv_0601ktbh7vvbf398yp0zbpw1me8d`
    - status `done`
    - summary `Voicemail Detected`
  - положительный результат:
    - voicemail больше не получает spoken-farewell;
    - `end_call` ушёл с пустым `system__message_to_speak`
  - незакрытая проблема:
    - agent всё ещё вызвал `call_log` с `eleven_conv_id = system__conversation_id`;
    - запись всё равно прошла в Sheet;
    - итоговая строка `A40:AM40` ушла с:
      - `lead_id = row_3`
      - `source_record_key = 79657700655`
      - `phone_primary = 79657700655`
      - `eleven_conv_id = ''`
    - значит published/runtime-версия `call_log` bridge после re-activation ещё не полностью совпадает с ожидаемым patched состоянием.
  - после этого теста три временно поднятых workflow снова выключены;
  - весь звонковый контур снова полностью на паузе.
- `2026-06-05` после разбора этого теста дополнительно пропатчен live `Main` у `AI_CALL_AGENT_1`, всё ещё без включения звонков:
  - новая live version:
    - `agtvrsn_6501ktbptasbfm2btq7dfq1mc16y`
  - backup до правки:
    - `/home/max/n8n_ai_call_center/backups/2026-06-05_eleven_call_log_schema_fix/current_ai_call_agent_1.before.json`
  - payload и ответ API:
    - `/home/max/n8n_ai_call_center/backups/2026-06-05_eleven_call_log_schema_fix/main_call_log_schema_fix_payload.slim_v2.json`
    - `/home/max/n8n_ai_call_center/backups/2026-06-05_eleven_call_log_schema_fix/current_ai_call_agent_1.after_patch.json`
  - что именно усилено:
    - в prompt зафиксировано, что `call_log` обязан включать `phone_primary` и `source_record_key`;
    - `eleven_conv_id` обязан быть реальным `conv_*`, а не literal `system__conversation_id`;
    - если в draft tool-call появляется literal `system__conversation_id`, agent должен перегенерировать `call_log` перед `end_call`;
    - в live tool-schema `call_log` добавлены недостающие свойства:
      - `phone_primary`
      - `source_record_key`
    - описание `eleven_conv_id` в schema усилено:
      - использовать текущий реальный `conv_*` id этого звонка.
  - важное ограничение:
    - required-поля `call_log` не расширялись;
    - жёсткую dynamic-variable schema на stable live не возвращали.
- `2026-06-05` после этого schema-fix выполнен ещё один одиночный live-test:
  - временно поднимались только:
    - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
    - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
    - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
  - request:
    - `row_3 / +79657700655 / Александр`
    - `request_id = manual.2026-06-05.141131.row_3.schemafix`
  - новый разговор:
    - `conv_7901ktbqpbewfksb5d807a721v3v`
    - `version_id = agtvrsn_6501ktbptasbfm2btq7dfq1mc16y`
  - важный результат:
    - это оказался не voicemail-case и не screening-case;
    - transcript содержит только:
      - `Трехэтажный дом.`
    - дальше линия ушла в `Client disconnected: 1000`
  - из-за этого:
    - agent не вызвал `call_log`;
    - agent не вызвал `end_call`;
    - новая schema `call_log` и новое правило по `eleven_conv_id = conv_*` на этом звонке не были реально проверены.
  - live Sheet за `2026-06-05` после этого теста не получил новой строки от этого вызова.
  - после цикла три временно поднятых workflow снова выключены;
  - весь звонковый контур опять полностью на паузе.
- `2026-06-05` следующий одиночный test-cycle выполнен уже по следующему номеру, без повтора `row_3`:
  - `row_4 / +79252149935 / Алиса Широкова`
  - `request_id = manual.2026-06-05.143212.row_4.schemafix`
  - разговор:
    - `conv_0601ktbrw785f03rvv0tket817tx`
    - `version_id = agtvrsn_6501ktbptasbfm2btq7dfq1mc16y`
  - transcript:
    - user: `Хорошо.`
    - agent: `Вам это в принципе интересно?`
    - user: `Такие вот истории, блин, зачем их найти?`
    - agent начинает: `Мы предлагаем официальные поставки липолитика lipolong ...`
    - затем линия завершает звонок: `Client disconnected: 1000`
  - из-за этого:
    - `call_log` снова не был вызван;
    - live Sheet новой строки не получил;
    - новый schema-fix опять не был проверен до конца.
  - surfaced отдельный риск live-логики:
    - очень короткий ранний ответ типа `Хорошо.` всё ещё считается достаточным live-signal;
    - после этого agent слишком рано переходит в follow-up/pitch path и может терять собеседника до `call_log`.
  - после цикла три временно поднятых workflow снова выключены;
  - весь контур снова на паузе.
- `2026-05-26` применён отдельный latency trim в live `Eleven Main`:
  - `turn_timeout = 4.0`
  - `tts.optimize_streaming_latency = 2`
  - live prompt ужат примерно с `18.1k` до `5.5k` символов, чтобы снизить паузу после живого ответа человека;
  - backup и payload лежат в:
    - `/home/max/n8n_ai_call_center/backups/2026-05-26_eleven_latency_trim/`
  - актуальная live version после правки:
    - `agtvrsn_3501ksj5y73qevps47674t661c6g`
- Для следующего входа добавлена локальная графическая схема live-контура:
  - `/home/max/n8n_ai_call_center/docs/architecture/callcenter_live_architecture.svg`
- Обновление `2026-05-27` по recovery dispatcher:
  - после входа в окно обзвона confirmed, что `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2` стартует каждую минуту и доходит до `Dispatcher | Finish Exhausted`;
  - старый битый `jsCode` в `workflow_entity` был заменён на валидный код из локального draft;
  - backup перед правкой:
    - `/home/max/n8n_ai_call_center/backups/2026-05-27_10-35-49_fix_finish_exhausted/AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2.before.json`
  - `n8n-server-n8n-1` после правки перезапущен и healthy;
  - дальше было подтверждено, что live `n8n` уже работает через `publish/unpublish` слой, поэтому одних SQL-правок `active=true` и `workflow_entity` было недостаточно;
  - через controlled re-import / publish восстановлена свежая published version dispatcher;
  - отдельно найден и исправлен Google OAuth дефект:
    - `Google | Build Sheet Payload` раньше отдавал literal `{{GOOGLE_CLIENT_ID}} / {{GOOGLE_CLIENT_SECRET}} / {{GOOGLE_REFRESH_TOKEN}}`;
    - теперь `Google | Refresh Access Token` берёт эти значения из `$env.*`, без хранения секретов в code node;
  - отдельно найден и исправлен stale active-dial lock bug:
    - dispatcher раньше держал историческую строку `dialing` как вечный активный lock даже после более свежего `elevenlabs`-результата по тому же номеру;
    - теперь active-lock считается только по самому свежему статусу номера.
  - controlled live cycle после этих правок:
    - `row_14` -> `dialing`, затем `elevenlabs / no_answer`, note: `МТС Защитник, сообщение не оставлено`;
    - `row_15` -> `dialing`, затем `autodial_dispatcher / outbound_request_failed`;
  - после короткого цикла dispatcher снова остановлен по правилу `короткий прогон -> стоп -> анализ`:
    - `workflow_entity.active = false`
    - `activeVersionId = null`
  - значит recovery dispatcher уже не “мертвый”, но текущий live-cycle завершён вручную, и перед следующим запуском нужно отдельно разобрать `outbound_request_failed` по `row_15`.
  - отдельно после этого выполнен ручной mini-cycle на `3` вызова через боевой webhook `eleven/outbound-call`, уже вне окна автодозвона:
    - артефакты: `/home/max/n8n_ai_call_center/.runtime/manual_call_cycle_2026-05-27/`;
    - перед циклом на relay поднят `RELAY_TIMEOUT` с `8` до `10`, без возврата retries;
    - `row_15` был принят Eleven за `~9.3s`, `conversation_id = conv_1801ksmm8dp0f15ar3tkyjx9x51e`;
    - `row_16` снова упёрся в `relay_upstream_failed / The read operation timed out` уже около `10.0s`;
    - `row_17` был принят Eleven за `~7.5s`, `conversation_id = conv_0101ksmm95xmf2p9e0rvfvhgpz9n`;
    - в Google Sheet после этого появился как минимум один новый итог `elevenlabs / no_answer` с note `Нет ответа, не оставляю сообщение.`;
    - но `lead_id/source_record_key/eleven_conv_id` в итоге опять не доехали как надо: свежая строка видна как `lead=unknown`.

Отдельно в live работает и email-followup контур:

- `email_followup.service`;
- `EMAIL_FOLLOWUP_AGENT_LIVE`;
- `EMAIL_FOLLOWUP_AGENT_MANUAL_LIVE`;
- SMTP-отправка писем с PDF-вложением;
- IMAP bounce-обработка;
- `firecrawl`-усиление поиска email;
- Telegram-отчёты в личный чат `@M_a_x_i_m_M_i_k_h_a_i_l_o_v`.

Обновление `2026-05-25` по Telegram media-ботам:
- `@PostMaker_ElixirPeptide_bot` = credential `Telegram Bot MMS_MMM` = workflow `C8Wmmjuv5hC425PM` (`MEDIA_AGENT_1 | Master Orchestrator TG (draft)`).
- Для этого бота подтвержден внутренний вызов `LG1KGfhnNCICjNra` (`MEDIA_AGENT_5 | Gemini Nano Banana Image (draft)`), где зашиты:
  - `gen-lang-client-0571009024`;
  - `aiplatform.googleapis.com`;
  - `gemini-3-pro-image-preview`;
  - `gemini-2.5-flash-image`.
- Статистика `workflow_statistics` по `PostMaker`:
  - `C8Wmmjuv5hC425PM`: `316 success`, `9 error`, последний event `2026-02-15 18:24:05`;
  - `LG1KGfhnNCICjNra`: `49 success`, последний event `2026-02-15 18:22:41`;
  - `KFWMYCaEpWAdVIn3` (`Pollinations` fallback): `24 success`, последний event `2026-02-15 18:24:04`.
- На `2026-05-25` `PostMaker` отключен:
  - workflow `C8Wmmjuv5hC425PM` переведен в `inactive`;
  - backup перед отключением: `/home/aicore/backups/n8n/C8Wmmjuv5hC425PM_2026-05-25_091327.json`;
  - Telegram webhook удален, текущий webhook URL пустой.
- `@MaxCorp_VideoGENai_bot` как Telegram-бот существует, но не найден как текущий workflow в этом live `n8n`.
- Telegram API на `2026-05-25` для него показывает:
  - `first_name = VideoGEN`;
  - `webhook_url = ""`;
  - `pending_update_count = 0`.
- Исторический подтвержденный runtime этого бота найден вне `n8n`, в локальном Telegram export `2026-03-07`:
  - проект `projects/veobot`;
  - стек `Python/aiogram`;
  - entrypoint `python -m veobot.main`;
  - затем user-service `~/.config/systemd/user/veobot.service`;
  - прямой вызов Vertex/Veo в проект `gen-lang-client-0571009024`;
  - bucket `gs://maxcorp-veo-output/video`.
- Практический вывод по `@MaxCorp_VideoGENai_bot`:
  - это не текущий `telegramTrigger`-контур в этом `n8n`;
  - если бот сейчас отвечает, он почти наверняка работает через отдельный `long polling` runner вне `n8n`.
- Ближайший текущий media-бот внутри этого `n8n`:
  - `@M_A_X_B_O_T_bot`;
  - workflow `ft03yrDgJJweqcVP` (`MEDIA_AGENT | Telegram + Memory + Flow + Kling (draft)`);
  - состояние: `inactive`, webhook пустой, `production_error = 3`, успешных production-запусков не видно.
- Отдельный `@PeptideExpert_Bot` активен и живет в другом workflow:
  - `YJdwp45LI1dmrsLy` (`Peptide_Expert`);
  - `340 success`, `36 error`, последний event `2026-05-11 08:25:17`.
- Практический вывод:
  - эти media-боты использовали `Nanobanana` исторически;
  - но текущий майский billing Google Cloud по `NANO BANA` не подтверждается их live-активностью внутри этого `n8n`, потому что все найденные `Gemini Nano Banana` события здесь закончились `2026-02-15`;
  - отдельно нужно иметь в виду внешний `veobot`-контур `@MaxCorp_VideoGENai_bot`, который исторически тоже бил в `gen-lang-client-0571009024`.

## 3. Что не считать главным боевым контуром

Не считать основой текущего боевого маршрута:
- локальные untracked backup/runtime-артефакты в `/home/max/n8n_ai_call_center`;
- любые draft-файлы, не подтвержденные на live-сервере или в live n8n.

## 4. Текущий live-агент ElevenLabs

- Agent name: `AI_CALL_AGENT_1`
- Agent ID: `agent_8801kgybyekned2a8yae6rp8hk3q`
- Stable live branch: `Main` -> `agtbrch_7801kgybyg9nesrbv64y078pazq0`
- Stable live version: `agtvrsn_1001ktbys8ftfpys5gykctxrqka5`
- Test branch: `staging-safe-test-2026-04-25` -> `agtbrch_6001kq1w2xtkfp8sp9fgkxejm3t9`
- Test branch current version: `agtvrsn_3401kqf1jbzbfx18x4n43jvhjwt9`

Текущая конфигурация:
- `LLM = gpt-4.1`
- `system prompt language = en`
- `spoken client language = ru`
- `TTS = eleven_flash_v2_5`
- `voice = Elena Gromova`
- `voice_id = 0ArNnoIAWKlT4WweaVMY`
- `speed = 1.16`
- `stability = 0.5`
- `similarity_boost = 0.78`
- `turn_eagerness = normal`
- `turn_timeout = 4.0`
- `speculative_turn = false`
- `tts.optimize_streaming_latency = 2`
- built-in tools: `end_call`, `skip_turn`, `voicemail_detection`
- active tools: `context_fetch`, `call_log`, `send_sms_info`, `end_call`
- `tool_ids`:
  - `tool_1601km62rxpqegqr52m9gk9sftr3`
  - `tool_2201ktbptaagfqxa8f713g76dd6q`
  - `tool_1701km86jmcpek4rj2j1rbhxqtfr`

Дополнительно подключено:
- pronunciation dictionary: `NnZrxd6lJkbHKqW6w04N`
- version id: `agtvrsn_1001ktbys8ftfpys5gykctxrqka5`
- базовая нормализация бренда: `ЛипоЛонг / LipoLong / lipolong -> липолонг`

## 5. Текущий старт разговора

Сейчас live-agent работает через `human-answer gate`:
- `first_message = ""`
- до живого ответа человека pitch не начинается;
- первая живая реплика агента после ответа человека должна сразу быть полным business-opener.

Текущий business-opener:
- `Здравствуйте, наша компания является официальным представителем липолитика премиум класса ЛипоЛонг, предлагаем вам сотрудничество с нашей компанией на выгодных условиях. А еще, сотрудничая с нами, вы можете быть уверены на 100%, что получаете оригинальную продукцию и не рискуете попасть на подделку`
- следующим коротким вопросом после opener должно быть:
  - `Вам это в принципе интересно?`
- после этого opener нельзя добавлять третью фразу, хвост или вопрос в том же самом ходе.

## 6. Что зафиксировано по поведению агента

- агент стал живее после перехода на Flash-модель;
- основная проблема теперь смещена в качество самого opener и дальнейшего pitch, а не в мгновенный автозапуск;
- автоответчики и IVR обрабатываются лучше за счёт `skip_turn`, `voicemail_detection` и ожидания живого ответа, но на `2026-05-22` найден конфликт старого правила message-service: агент всё ещё может оставить callback-сообщение электронному помощнику;
- `2026-05-25 11:34 MSK`: подтверждён отдельный live-источник длинной паузы до реального дозвона:
  - `n8nEventLog` показал, что longest node latency сидела в `AUTODIAL_DISPATCHER -> Dispatcher | Request Outbound Call` и `VOICE_INBOUND_AGENT -> Eleven | Outbound HTTP`, а не в Code node/Sheet;
  - прямой probe relay с live-сервера дал `HTTP 502` только через `41703 ms`;
  - это совпадает с текущей relay-схемой `20s timeout + 1 retry + 1500ms delay`.
- `2026-05-25 11:34 MSK`: в live workflow `VOICE_INBOUND_AGENT (draft)` для ноды `Eleven | Outbound HTTP` добавлен `options.timeout = 10000`, чтобы `n8n` не висел на relay около `40s` при upstream-сбое.
- Контрольный probe после этой правки: `POST /webhook/eleven/outbound-call` вернулся примерно за `10180 ms`, то есть длинный хвост на этапе outbound-call уже подрезан на стороне live `n8n`.
- `2026-05-25 11:45 MSK`: такой же hardening применён и на реальном relay-хосте `151.241.228.232`:
  - runtime `/opt/eleven_outbound_relay.py` обновлён;
  - сначала live relay работал с:
    - `RELAY_TIMEOUT=10`
    - `RELAY_RETRY_COUNT=0`
    - `RELAY_RETRY_DELAY_MS=500`
  - после повторяемых июньских timeout-case live relay поднят ещё на один маленький шаг:
    - `RELAY_TIMEOUT=12`
    - `RELAY_RETRY_COUNT=0`
    - `RELAY_RETRY_DELAY_MS=500`
  - `eleven-outbound-relay.service` перезапущен успешно.
- Контрольный probe после live relay-патча: `provider_rejected` path теперь возвращается примерно за `8367 ms`, а не за `~41.7s`.
- окно ожидания после последней машинной фразы/музыки/гудка ужато до `10` секунд;
- добавлен абсолютный потолок до первой осмысленной живой реплики: около `20` секунд после соединения; непрерывные гудки, queue-loop и hold music не должны держать линию минутами;
- после собственного opener без ясного словесного ответа агент должен завершать звонок примерно через `4` секунды;
- consent/recording-фразы вида `Продолжая разговор, вы соглашаетесь на запись данного звонка...` должны трактоваться как машинный пролог, а не как человек;
- фразы `абонент сейчас не может ответить / телефон занят / недоступен` должны завершаться без ответной речи, с логикой `busy/no_answer + callback`;
- музыка ожидания, рекламные объявления клиники и повторяющиеся брендовые приветствия тоже нужно считать waiting mode, а не живым диалогом;
- literal ASR-маркеры `музыка`, `music`, `...`, дыхание, отдельный слог или одиночное ругательство после долгих гудков не считаются human-answer сигналом и не должны запускать opener;
- название клиники, компании, бренда, города или отдела само по себе больше не считается достаточным human-answer сигналом для старта opener;
- брендовые приветствия, слоганы, partial ASR fragments вроде `клиника ...`, `город Москва ...`, `спасибо за звонок ...` требуют ещё одного чистого человеческого ответа; если его нет, агент должен молчать и завершать `no_answer`, а не открываться сам;
- новое целевое правило для message-service: электронный помощник, автоответчик и фразы вида `Если абонент захочет с вами связаться`, `Что передать?`, `Какие-либо подробности желаете рассказать?`, `Это всё?` должны завершаться сразу, без callback-сообщения, без ответов на уточнения и без sales-pitch;
- message-service фраза `Если абонент захочет с вами связаться, как ему это лучше всего сделать?` должна считаться автоответчиком, а не живым диалогом; результат нужно логировать как `no_answer + callback` и завершать через `end_call`;
- `2026-05-25 10:48 MSK`: после кейса `conv_1901ksezar1jezbsve31c4qr83rw` правило ужесточено в локальном source-of-truth prompt: machine/unavailable/message-service signal должен закрываться максимум за `5` секунд, без оставления callback-сообщения автоответчику.
- `2026-05-25 12:36-12:40 MSK`: live `ElevenLabs Main` уже обновлён через relay-хост `151.241.228.232`, у которого есть рабочий доступ к Eleven API:
  - backup до правки: `/home/max/n8n_ai_call_center/backups/2026-05-25_live_main_canary_refresh/current_ai_call_agent_1.before.json`;
  - live agent после правки: `/home/max/n8n_ai_call_center/backups/2026-05-25_live_main_canary_refresh/current_ai_call_agent_1.after_patch.json`;
  - рабочий PATCH payload: `/home/max/n8n_ai_call_center/backups/2026-05-25_live_main_canary_refresh/main_minimal_patch_payload.json`;
  - сохранены `first_message=""`, `voice_id=0ArNnoIAWKlT4WweaVMY`, `tool_ids`, `phone_ids`;
  - в live `Main` теперь реально стоят `turn_timeout = 5.0` и `voicemail_message = null`;
  - в live prompt закреплены `MTS Defender`, `МТС Защитник`, `это рекламный звонок`, `звонок записывается сервисом защиты` как machine/screening-service сигналы.
- в outbound-контур теперь прокидываются runtime-идентификаторы звонка через `conversation_initiation_client_data`: `lead_id`, `caller`, `phone_primary`, `source_record_key`, `company_name`, `contact_name`, `request_id`;
- `call_log` должен писать именно эти реальные значения, а не буквальные строки `system__called_number`, `system__conversation_id` или `{{lead_id}}`;
- `ELEVEN_TOOL_CALL_LOG_BRIDGE` теперь дополнительно вычищает такие буквальные плейсхолдеры и не даёт им попасть в Sheet как будто это реальные идентификаторы;
- `2026-06-04` live prompt отдельно ужесточён на одном реальном voicemail-case:
  - agent больше не должен отправлять bare `call_log` только с `call_result / next_step / notes_short`;
  - на `voicemail / no_answer / busy / screening` он обязан передавать identity package:
    - `lead_id`
    - `caller`
    - `phone_primary`
    - `source_record_key`
    - `company_name` / `contact_name` при наличии
    - `eleven_conv_id` как реальный conversation id
  - после voicemail и machine-case нельзя говорить:
    - `Спасибо, перезвоним позже.`
    - любой другой farewell после `call_log`
  - нужная последовательность: `call_log` -> silent `end_call`.
- на stable live `Main` `call_log` держится на relaxed tool-schema без жёсткой dynamic-variable привязки, чтобы manual/SIP test не падал ещё до старта разговора;
- любые эксперименты с dynamic-variable schema теперь только на отдельной test/staging-ветке ElevenLabs;
- follow-up переведен на сценарий без почты: агент должен собирать имя, номер и удобный канал связи;
- агент не должен просить диктовать email, повторять email или зависать на линии, пока администратор ищет почту;
- если собеседник просит `отправить на почту`, live-flow должен уводить в SMS на текущий номер, короткий контакт менеджера или callback, а не в email-диктовку;
- `call_log` и `context_fetch` были восстановлены через валидные `tool_ids` после очистки битых tool-ссылок;
- словарь произношения собран по живым звонкам и текущему prompt, чтобы выровнять бренд `липолонг` и частые термины;
- live system prompt переведен на английский, но сам агент продолжает говорить с клиентом только по-русски;
- остаточная задержка может появляться на нечетких репликах клиента и в LLM-ходе, а не только в TTS;
- главный текущий фронт улучшения: логика звонка после открытия, value reveal, дожим после возражений, работа с автоответчиками и полурелевантными ответами;
- в prompt запрещены реплики `Здравствуйте. Чем могу быть полезна?`, `Я вас слушаю`, `Вы на связи?` и повтор машинной фразы про недоступного абонента.
- в prompt отдельно запрещена комбинированная rescue-фраза `Я вас слушаю, вы на связи? Чем могу помочь?`;
- в prompt отдельно запрещены email-фразы `Продиктуйте, пожалуйста, почту`, `Готова записать почту`, `Отправим информацию на почту`, `Вы на связи? Готова записать...`;
- в prompt отдельно запрещены probing-фразы на неясной линии:
  - `Извините, если не вовремя. Вам удобно сейчас поговорить?`
  - `Я вас слушаю, можете говорить. Чем могу помочь?`
- если после полного opener клиент не даёт ясного словесного ответа примерно `4` секунды, агент должен завершать звонок как `no_answer`, а не дожимать через `вы на связи?` или `вы меня слышите?`.
- в prompt также запрещены ранние закупочные вопросы:
  - `Подскажите, вы принимаете решения по закупкам?`
  - `Вы занимаетесь закупками или могу поговорить с ответственным специалистом?`
  Эти фразы допустимы только если собеседник сам сказал, что он не ЛПР.

Ограничение на `2026-05-22`:
- прямой ElevenLabs API из текущего окружения `147.45.213.87` по-прежнему возвращает restricted/help page (`302/403`);
- но `2026-05-25` подтверждено, что relay-хост `151.241.228.232` может читать и patch'ить live agent через Eleven API, и именно через него live `Main` уже обновлён.
- `2026-05-25`: после свежих кейсов `conv_6801ksf4n22efwqvcthy3b19531b` и `conv_2801ksf596bneyxa9r1crt9b7fpc` целевое live-поведение дополнительно ужесточено:
  - machine / unavailable / message-service -> не ждать дольше `5` секунд;
  - voicemail -> не оставлять spoken callback message вообще;
  - long ring / no human -> завершать примерно после `5` гудков;
  - готовые payload-артефакты лежат в `/home/max/n8n_ai_call_center/backups/2026-05-25_machine_fast_hangup_refresh/`.

## 7. Автодозвон

- Текущая привязанная таблица для следующего цикла обзвона:
  - `https://docs.google.com/spreadsheets/d/1SyoGWXrvLNevGzjWQjfSP7eRqVCMOzR0MzXeWSL7HOo/edit?gid=199760593#gid=199760593`
  - Drive name: `Первая таблица частных косметологов`
  - локальная копия: `/home/max/n8n_ai_call_center/ Таблицы_контактов /Первая таблица частных косметологов.xlsx`
  - preview: `/home/max/n8n_ai_call_center/.runtime/contact_imports/Первая таблица частных косметологов.preview.json`
- В таблице `37` строк импорта:
  - `13` строк оставлены callable;
  - `24` строки сразу помечены `do_not_call=true`, чтобы не звонить в форумные/чатовые и явно шумные записи.
- На `2026-06-03` live-связка выровнена так:
  - `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2` читает эту новую таблицу;
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` пишет в эту же новую таблицу;
  - `VOICE_INBOUND_AGENT (draft)` по-прежнему выключен;
  - `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2` после перепривязки снова выключен.
- `2026-05-25 10:41 MSK`: после остановки, переключения и повторного включения dispatcher уже записал первую lock-строку `autodial_dispatcher / dialing` по `row_2` в эту таблицу.
- `2026-05-25 11:12 MSK`: по прямой команде пользователя `AUTODIAL_DISPATCHER` снова включен (`active=true`). После включения dispatcher записал новые строки в `_50`: `row_3` взят в `dialing`, затем обработан, далее `row_4` взят в `dialing`.
- `2026-05-25 11:39 MSK`: свежая диагностика показала, что текущая причина паузы автодозвона не `exhausted`, а `provider_circuit_breaker`:
  - `recent_provider_failure_count = 3`
  - `today_provider_failure_count = 5`
  - seed-лиды в `_50` физически не закончились: в таблице подтверждены `50` строк `xlsx_import`.
- `2026-05-25 11:51-11:58 MSK`: после выхода старых technical failures из окна breaker dispatcher действительно ожил сам:
  - в `_50` появились новые `dialing/outbound_request_failed` записи по `row_7`, `row_8`, `row_9`, `row_10`;
  - это подтвердило, что проблема не в пустой базе и не в сломанном cron, а в том, что upstream outbound всё ещё даёт технический reject, только уже быстрее.
- `2026-05-25 11:59 MSK`: чтобы не сжигать оставшиеся лиды на технических `outbound_request_failed`, live `AUTODIAL_DISPATCHER` снова остановлен вручную (`active=false`) до следующего цикла live-фикса.
- `2026-05-25 12:41-12:43 MSK`: для канарейки dispatcher был кратко включён через n8n API, но новых live-строк не создал, потому что уже сработал внутренний дневной стоп `daily_provider_failure_limit_reached`.
- Подтверждённая текущая причина, почему база "встала":
  - `provider_failures_today = 8`;
  - автодозвон остановлен не из-за пустой таблицы и не из-за cron, а из-за достигнутого лимита технических outbound-фейлов.
- Вместо массового старта выполнена ручная канарейка через `POST https://www.n-8-n.site/webhook/eleven/outbound-call` по `row_11`, `row_12`, `row_13`:
  - все `3/3` попытки вернули `provider_rejected -> relay_upstream_failed -> The read operation timed out`;
  - relay journal на `151.241.228.232` подтвердил три подряд upstream timeout примерно по `8015-8025 ms`;
  - значит, главный текущий blocker уже не prompt, а нестабильность upstream outbound/SIP trunk path.
- При этом первый положительный эффект нового `Main` уже появился в live Sheet:
  - по `row_11` записано `call_result = no_answer`;
  - note: `Обнаружен голосовой ассистент, сообщение не оставлено.`
  - это подтверждает, что новый live prompt уже перестал оставлять spoken callback хотя бы на одном machine/assistant кейсе.
- Отдельный незакрытый лог-долг:
  - `eleven_conv_id` в свежих строках всё ещё пустой;
  - текущий live `call_log` tool-schema остаётся relaxed и не прокидывает `system conversation id` автоматически.
- `2026-05-25 14:11-14:14 MSK`: после кейса `conv_8801ksfbpec2fz5bcvn6wt9h05p1` live `Main` дополнительно ужесточён против intermediary/message-transfer линий:
  - `я передам ответственному специалисту`, `оставьте контакт`, `мы передадим информацию`, `я только передам` теперь в prompt трактуются как blocked direct-contact, а не как полезный human handoff;
  - такие кейсы больше не должны логироваться как `send_kp_pending_callback` только потому, что линия согласилась что-то передать;
  - live patch применён снова через `151.241.228.232` и подтверждён GET-проверкой: `turn_timeout = 5.0`, новый intermediary block присутствует в prompt.
- `2026-05-25 14:16+ MSK`: после кейса `conv_6201ksfbnq77echv3j7e4j2h8qha` введено ещё более жёсткое правило:
  - сервисная фраза со словом `абонент` автоматически считается автоответчиком/помощником;
  - не анализировать такую линию как человека вообще;
  - сразу `call_log`, потом молчаливый `end_call`;
  - правило внесено и в source-of-truth prompt, и в live `Main`, patch снова прошёл через `151.241.228.232`.
- `2026-05-25 15:30+ MSK`: по прямому решению пользователя policy для secretary/intermediary handoff изменена обратно:
  - `я передам ответственному специалисту`, `оставьте контакт`, `мы передадим информацию` теперь снова считаются полезным handoff-контактом;
  - такие кейсы нужно логировать как `send_kp_pending_callback`, но без длинного sales-диалога;
  - live `Main` обновлён повторным patch через `151.241.228.232`.
- Окно обзвона:
  - `10:00–14:00 MSK`
- Текущие ограничения:
  - максимум `15` живых диалогов в день;
  - максимум `30` попыток автодозвона в день;
  - максимум `2` попытки на номер в день, если клиент сам не просил перезвон;
  - недоступный номер после `3` общих недоступностей выводится из работы.
- lock активного `dialing` теперь держится `5` минут, чтобы длинный ringback/hold вызов не допускал повторный autodial того же лида через `1` минуту.
- Важно по live-классификации outbound-фейлов:
  - `SIP 486 Busy Here` теперь считается обычным `busy`, а не техническим `outbound_request_failed`;
  - такие busy-отказы не должны больше сами по себе включать `provider_circuit_breaker`;
  - live dispatcher теперь для этого читает и вложенный `response_body.note / eleven_response.message`, а не только верхний `action`;
  - только реальные технические outbound reject/timeout должны копиться в дневной provider-failure лимит.
- 2026-04-13 был исправлен critical баг: dispatcher не мог читать Google Sheet из-за сломанной live-публикации OAuth placeholder-ов. Сейчас это уже исправлено, и autodial снова стартует.
- Для нового цикла диагностики таймингов добавлен локальный инструмент:
  - `/home/max/n8n_ai_call_center/scripts/report_n8n_eventlog_timings.py`
  - он нужен для чтения `n8nEventLog*.log` и сравнения длительностей workflow/node до и после правок.
- `2026-05-25 13:05 MSK`: live relay `151.241.228.232` дополнительно обновлён для более подробной диагностики:
  - `scripts/eleven_outbound_relay_server.py` теперь логирует краткий summary тела ответа ElevenLabs даже при `HTTP 200`;
  - это нужно, чтобы в следующем тесте отличить настоящий accepted outbound от "формально 200, но по смыслу не принят".
- `2026-05-25 12:18 MSK`: для постоянного мониторинга live Sheet добавлен отдельный локальный отчёт:
  - `/home/max/n8n_ai_call_center/scripts/report_live_call_log_sheet.py`
  - первый прогон по `2026-05-25` показал `xlsx_import=50`, `autodial_dispatcher=23`, `elevenlabs=5`, `outbound_request_failed=8`, `send_kp_pending_callback=4`, `no_answer=1`;
  - после live patch и ручной канарейки свежий срез показал `elevenlabs=6`, `outbound_request_failed=8`, `send_kp_pending_callback=4`, `no_answer=2`, `rows_with_conv_id=0`.
- `2026-05-25 13:55-14:00 MSK`: в live `AUTODIAL_DISPATCHER` исправлен ложный подсчёт provider failures:
  - раньше dispatcher считал любой `autodial_dispatcher / outbound_request_failed` техническим провалом, даже если через несколько секунд по тому же `lead_id` уже приходил реальный `elevenlabs`-итог;
  - по живому срезу это подтвердилось минимум для `row_3`, `row_5`, `row_10`;
  - новая live-логика теперь исключает такие resolved failures из `recent_provider_failure_count`, `today_provider_failure_count` и `today_technical_waste_count`.
- После этого обновления live workflow снова активирован:
  - `AUTODIAL_DISPATCHER = active=true`;
  - на `2026-05-25 14:00+ MSK` это уже вне окна обзвона, поэтому новых строк немедленно не появилось, но следующий рабочий тик будет идти уже без старого false-breaker по resolved timeout-кейсам.
- Локальный отчёт тоже обновлён под ту же логику:
  - теперь он показывает не только `provider_failures_raw`, но и отдельно:
    - `provider_failures_resolved`
    - `provider_failures_unresolved`
  - свежий срез после правки:
    - `provider_failures_raw = 8`
    - `provider_failures_resolved = 3`
    - `provider_failures_unresolved = 5`
- Тот же прогон подтвердил два практических live-дефекта:
  - `row_10`: note `Оставлено короткое сообщение для абонента через МТС Защитник, передан контакт менеджера.` — это противоречит новому правилу `machine -> silent end`;
  - в свежих `elevenlabs`-строках `eleven_conv_id` пустой, из-за чего трассировка разговоров в Google Sheet пока неполная.
- `2026-05-25`: кейс `conv_2601ksf5p04zfnzr3w1ec85aj9kk` отдельно закреплён как source-of-truth:
  - `МТС Защитник / MTS Defender / это рекламный звонок / звонок записывается сервисом защиты` считать автоответчиком или screening-service;
  - агент не должен вести диалог с такой линией и не должен оставлять ей сообщение.
- `2026-05-26`: recovery по остановке autodial показал, что проблема уже не в одном старом workflow ID:
  - fresh-import recovery клоны `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26` (`vIXJSsiKh2R4jsWG`) и `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2` (`70B9BSNOu0LXPBqe`) были реально активированы на старте `n8n`;
  - при этом и recovery execution внутри live `n8n` всё равно приходят в `Dispatcher | Finish Exhausted`, хотя standalone-прогон того же `Parse Sheet Rows` JS на тех же live Sheet данных выбирает `action = dial`, `reason = candidate_selected`, `eligible_count = 46`;
  - это сместило основную гипотезу с “битый старый dispatcher” на “runtime/versioning рассинхрон текущего `n8n` на SQLite”.
- На конец `2026-05-26 14:00 MSK` окно обзвона уже закрыто, а live recovery V2 уходит в `Dispatcher | Finish Outside Window`.
- Текущий активный recovery dispatcher в `n8n`:
  - `AUTODIAL_DISPATCHER_RECOVERY_2026-05-26_V2`
  - workflow id: `70B9BSNOu0LXPBqe`
- Практический статус прямо сейчас:
  - боевой обзвон **ещё не перепроверен новым полноценным циклом dispatcher уже после миграции на Postgres**;
  - `VOICE_INBOUND_AGENT` и `ELEVEN_TOOL_CALL_LOG_BRIDGE` активны;
  - `eleven/outbound-call` и `eleven/tool/call-log` уже подтверждены ручными live smoke-тестами после migration fix;
  - маленький ручной smoke после migration уже показал минимум один полезный business-case без технического reject (`row_3 -> send_kp_pending_callback`);
  - старый корень подозрения был в published/cached execution representation `n8n` на SQLite;
  - после миграции на Postgres это нужно перепроверить уже новым live tick.

## 8. Email-followup live контур

- контур отдельный, от `ElevenLabs` не зависит;
- живой workflow идёт по расписанию:
  - `09:00 MSK`
  - `15:00 MSK`
- ручной webhook:
  - `email-followup-live/run`
- текущие таблицы в проде:
  - `контакты_косметологов_москва_1`
  - `контакты_косметологов_москва_2`
  - `контакты_косметологов_москва_47`
- письмо уходит с обязательным PDF:
  - `КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ (2).pdf`
- Telegram recipient уже исправлен на актуальный личный чат владельца.

Если задача связана с этим контуром, основной пакет читать в:

- `../docs/email_followup_agent/README_RU.md`

## 9. Cosmetologist Hunter / поиск контактов

- Live service: `cosmetologist_hunter.service` на `ai-core-prod-147`.
- Live URL: `http://127.0.0.1:8787` на сервере.
- Код: `/home/aicore/n8n-server/scripts/cosmetologist_hunter_service.py`.
- Локальная копия кода: `/home/max/n8n_ai_call_center/scripts/cosmetologist_hunter_service.py`.
- Локальная папка контактов:
  - `/home/max/n8n_ai_call_center/ Таблицы_контактов /`
- Важные файлы после прогона `2026-05-25`:
  - `/home/max/n8n_ai_call_center/ Таблицы_контактов /контакты_косметологов_москва_50.xlsx`;
  - `/home/max/n8n_ai_call_center/.runtime/cosmetologist_hunter/previews/контакты_косметологов_москва_50.json`;
  - `/home/max/n8n_ai_call_center/.runtime/cosmetologist_hunter/logs/2026-05-25_private_cosmetologists_50_build.log`;
  - `/home/max/n8n_ai_call_center/ Таблицы_контактов /контакты_косметологов_москва_49.xlsx`;
  - `/home/max/n8n_ai_call_center/.runtime/cosmetologist_hunter/previews/контакты_косметологов_москва_49.json`;
  - `/home/max/n8n_ai_call_center/.runtime/cosmetologist_hunter/logs/2026-05-25_private_cosmetologists_run.log`.
- Google Sheet `_50` для live-обзвона:
  - `https://docs.google.com/spreadsheets/d/1kAXIwaa_-rC4MO5vV3mFV-Geha08iL_6pJNCNxlQPAU/edit?gid=199760593#gid=199760593`;
  - workflow `AUTODIAL_DISPATCHER` и `ELEVEN_TOOL_CALL_LOG_BRIDGE` переключены на этот `spreadsheet_id`.
- Google Sheet результата:
  - `https://docs.google.com/spreadsheets/d/14X6j699O5J_RtjfUZ4JDddugisbIV0XdAr3HFP5a2kg/edit`
- Текущий режим отбора после `2026-05-25`:
  - private-only;
  - приоритет `Prodoctorov` doctor profiles;
  - затем private-запросы Yandex;
  - затем 2GIS как fallback;
  - клиники, центры, салоны, студии и организации отсекаются до записи результата.
- Файл `_50.xlsx` собран как private-practice кандидатная база на 50 строк: явные `clinic/center/salon/medical/lab/shop/agency` исключены, но нижние строки из-за live-блокировок Prodoctorov требуют ручной QA, если нужен строго формат “только ФИО частного специалиста”.
- Ошибка бота `Permission denied` была связана с root-owned preview-файлом `.runtime/cosmetologist_hunter/previews/контакты_косметологов_москва_49.json`; права исправлены на `aicore:aicore`.
- Осторожно: live workflow `COSMETOLOGIST_HUNTER_TELEGRAM_LIVE` ещё хранит Telegram/Mistral/hunter token в Code node. Это нужно вынести в env/credentials отдельной правкой.
