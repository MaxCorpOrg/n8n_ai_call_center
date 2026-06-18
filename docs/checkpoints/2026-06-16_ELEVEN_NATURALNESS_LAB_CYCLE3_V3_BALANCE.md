# Контрольная точка — 2026-06-16

## Обновление 2026-06-16: branch с `eleven_v3_conversational` признан слишком вязким, lab возвращён на `eleven_flash_v2_5`

### Сделано

- После серии self-test на `eleven_v3_conversational` стало видно, что по naturalness он местами звучит интересно, но для нашего телефонного контура слишком часто даёт ощущение вязкости:
  - дольше думает перед ответом;
  - тяжелее выходит из overlap;
  - хуже ощущается в живом темпе звонка.
- На этом фоне был выпущен промежуточный lab-only patch:
  - `agtvrsn_1901kv88cahgfq1v7w6b7nvcme32`
- Его задача была не про голосовую модель, а про продуктовую ветку:
  - если человек говорит, что ему интересно, но он пока не использует липолитики,
    agent не должен бросать разговор, а должен коротко объяснить ценность ЛипоЛонг и довести до SMS/callback.
- Проверочный звонок:
  - `conv_1001kv88d99xe8wsv2tsr3nvyvtv`
  - `version_id = agtvrsn_1901kv88cahgfq1v7w6b7nvcme32`
  подтвердил:
  - ветка `интересно -> нет, пока не используем` теперь действительно дожимается дальше;
  - agent уже не схлопывает такой контакт в ранний `not_target`;
  - вместо этого даёт конкретную ценность:
    - официальный оригинальный продукт;
    - можно начать с теста;
    - многие косметологи уже используют;
  - и в этом звонке дошёл до:
    - `send_sms_info`
    - `call_log`
- На том же звонке остался узкий остаток:
  - rescue и финальный close местами вылезали микрофрагментами:
    - `...`
    - `Я уже...`
- Для этого сверху был выпущен ещё один lab-only patch:
  - `agtvrsn_3201kv88kyz1fdpazd8vvmdvjs80`
  - смысл:
    - не выпускать punctuation-only spoken turns;
    - не выпускать обрубок `Я уже...` перед нормальной финальной SMS-фразой.
- Затем по документации ElevenLabs и по собственным self-test принято решение вернуться на Flash как на основной low-latency вариант для lab:
  - новая текущая верхняя lab-version:
    - `agtvrsn_4901kv88ns5pfgvbqbg3n42he4rp`
  - `tts.model_id = eleven_flash_v2_5`
  - `expressive_mode = false`
  - `speed = 1.08`
  - `stability = 0.46`
  - `similarity_boost = 0.80`
- Артефакты возврата на Flash:
  - `.runtime/eleven_lab_flash_return_2026-06-16/payload_minimal.json`
  - `.runtime/eleven_lab_flash_return_2026-06-16/response.json`
- Проверочный Flash self-test:
  - `conv_4601kv88pp5sephrzz0swv4nck21`
  - `version_id = agtvrsn_4901kv88ns5pfgvbqbg3n42he4rp`
  подтвердил:
  - звонок снова живо доходит до SMS-path;
  - product-ветка `интересно, но пока не используем` остаётся рабочей и не ломается после возврата на Flash;
  - `send_sms_info` и `call_log` снова проходят;
  - по ощущениям и по времени ответов Flash подходит под наш real-time контур лучше, чем `eleven_v3_conversational`.
- По этому звонку агрегированная `convai_llm_service_ttfb` была:
  - `count = 14`
  - `avg ≈ 0.80s`
  - `min ≈ 0.43s`
  - `max ≈ 1.95s`

### На чем остановились

- Live `Main` не менялся.
- Текущий lab tip теперь:
  - `agtvrsn_4901kv88ns5pfgvbqbg3n42he4rp`
- Зафиксирован рабочий вывод по моделям:
  - для нашего call-center `eleven_flash_v2_5` сейчас лучше `eleven_v3_conversational`;
  - `v3_conversational` можно считать интересным лабораторным вариантом, но не текущим кандидатом на боевой naturalness-контур.
- Уже подтверждено:
  - ветка `интересно -> нет, пока не используем` теперь умеет объяснять ценность и доводить до SMS;
  - возврат на Flash эту ветку не сломал.
- Ещё не закрыто:
  - в сложных overlap-кейсах всё ещё могут мелькать микрофрагменты:
    - `...`
    - `Я уже...`
  - rescue местами всё ещё ощущается слишком навязчивым, если пользователь даёт шумный или неполный ответ.

### Что делать дальше

1. Продолжать уже не подбор модели, а точечную доводку поведения на Flash:
   - `turn-taking`
   - post-tool final close
   - late rescue suppression
2. Сделать следующий self-test на:
   - `agtvrsn_4901kv88ns5pfgvbqbg3n42he4rp`
3. Проверить три вещи сразу:
   - не вылезает ли `...` после overlap;
   - не остаётся ли микрофрагмент `Я уже...` перед чистым финальным close;
   - сохраняется ли живая product-ветка до SMS, если человек говорит:
     - `да, интересно`
     - `нет, пока не используем`

## Обновление 2026-06-16: зафиксирован текущий LLM в lab и shortlist на следующий цикл сравнения

### Сделано

- Дополнительно проверены свежие lab-артефакты напрямую через:
  - `.runtime/eleven_lab_flash_return_2026-06-16/response.json`
  - `.runtime/eleven_lab_novice_branch_value_push_2026-06-16/response.json`
- Это подтвердило, что и на V3-ветке, и на текущем Flash-tip в качестве LLM сейчас используется один и тот же мозг:
  - `llm = gpt-4.1`
- То есть последние циклы сравнивали в основном:
  - TTS/voice-модель;
  - turn-taking;
  - prompt-поведение;
  а не разные LLM между собой.
- Для следующего отдельного цикла теперь зафиксирован shortlist кандидатов на сравнение уже именно по LLM:
  - текущий baseline:
    - `gpt-4.1`
  - быстрый альтернативный кандидат:
    - `gemini-2.5-flash`
  - кандидат на более мягкий conversational style:
    - `claude-sonnet-4.5`
- Отдельно зафиксировано правило этого следующего шага:
  - TTS оставить одинаковым:
    - `eleven_flash_v2_5`
  - voice оставить одинаковым:
    - `0ArNnoIAWKlT4WweaVMY`
  - сравнивать только LLM, а не всё сразу.

### На чем остановились

- Текущий lab tip:
  - `agtvrsn_4901kv88ns5pfgvbqbg3n42he4rp`
- Его фактический стек сейчас:
  - `llm = gpt-4.1`
  - `tts.model_id = eleven_flash_v2_5`
- Значит текущий baseline для LLM-сравнения уже понятен и зафиксирован.

### Что делать дальше

1. Подготовить отдельный LLM-cycle без изменения voice и TTS.
2. Сравнивать только три варианта:
   - `gpt-4.1`
   - `gemini-2.5-flash`
   - `claude-sonnet-4.5`
3. Один и тот же self-test сценарий гонять на всех трёх:
   - `Алло!`
   - `Что это?`
   - `Да, интересно`
   - `Нет, пока не используем`
   - запросить детали
   - согласиться на SMS
4. На каждом варианте фиксировать:
   - `convai_llm_service_ttfb`
   - перебивания / недослушивание
   - product-value branch
   - лишние fragment-хвосты
   - чистоту финального close
5. Для подготовки payload использовать локальный helper:
   - `scripts/prepare_eleven_llm_variant.sh`
   - source snapshot для текущего baseline:
     - `.runtime/eleven_lab_flash_return_2026-06-16/response.json`
6. Первый compare-кандидат уже опубликован в lab:
   - `agtvrsn_3901kv89xcg3fnntrp2zwbjt0xcb`
   - `llm = gemini-2.5-flash`
   - `tts.model_id = eleven_flash_v2_5`
7. Следующий практический шаг:
   - self-test именно на Gemini-версии выше
   - затем publish Claude-кандидата и симметричный self-test

## Обновление 2026-06-16: подтверждён fix для ветки `интересно -> нет, не работаем с липолитиками`

### Сделано

- По запросу на более живую логику и без раннего сброса выпущен ещё один lab-only patch:
  - новая текущая верхняя lab-version:
    - `agtvrsn_9401kv883fg5fxxbsv2t231jctqc`
  - новые блоки:
    - `Warm line-check wording override`
    - `Interested-but-not-yet-using override`
- Смысл этого шага:
  - убрать сервисные формулы вроде:
    - `Да, я на линии`
    - `Я на линии`
  - разрешить более короткие живые формы подтверждения линии;
  - главное — больше не считать bare `нет` на вопрос
    - `Вы уже используете липолитики?`
    автоматическим `not_target`, если человек уже проявил интерес и релевантен как косметолог.
- Контрольный звонок на этой вершине:
  - `conv_7201kv884a88eghv2r9zs9mgr85v`
  - `version_id = agtvrsn_9401kv883fg5fxxbsv2t231jctqc`
- Что этим звонком подтверждено:
  - сценарий:
    - `Да.` -> интерес есть
    - `Нет.` -> липолитики пока не используют
    больше не приводит к мгновенному сбросу;
  - agent продолжает разговор содержательно:
    - `ЛипоЛонг подходит для косметологов, кто хочет попробовать ...`
  - то есть ветка `интересно, но пока не используют` уже переведена из раннего `not_target` в нормальное sales-объяснение;
  - нежелательная фраза:
    - `Да, я на линии`
    в этом звонке не появилась.
- Ограничение текущего теста:
  - пользователь завершил звонок сам до полного дожатия в SMS/callback;
  - значит следующий шаг теперь не про ранний hangup, а про продолжение этой ветки до следующего business-step.

### На чем остановились

- Live `Main` не менялся.
- Текущий lab tip:
  - `agtvrsn_9401kv883fg5fxxbsv2t231jctqc`
- Уже подтверждено:
  - `нет` после вопроса про липолитики больше не схлопывает релевантный заинтересованный контакт в моментальный `not_target`;
  - agent продолжает объяснять продукт.
- Ещё не подтверждено:
  - как именно эта новая ветка доходит до SMS/callback;
  - исчезла ли полностью фраза `Да, я на линии` во всех overlap-кейсах.

### Что делать дальше

1. Сделать один answered self-test ещё раз на:
   - `agtvrsn_9401kv883fg5fxxbsv2t231jctqc`
2. Провести его по сценарию:
   - `да, интересно`
   - `нет, липолитики пока не используем`
   - затем дослушать, как agent объясняет ценность ЛипоЛонг
   - и довести до SMS или callback.

## Обновление 2026-06-16: выпущен post-SMS single-close patch, но SMS-path на новой вершине ещё не подтверждён

### Сделано

- После SMS self-test на:
  - `conv_8701kv87hq5de3y9gdj0emtg06be`
  - `version_id = agtvrsn_1101kv871mt1e699f6sq7x35epay`
  подтверждено:
  - successful `send_sms_info` по-прежнему работает;
  - agent корректно говорит:
    - `Я уже отправила SMS на этот номер. Хорошего дня.`
    на success-path.
- Но тем же звонком зафиксирован новый остаток:
  - после `call_log` agent всё ещё повторяет ту же финальную SMS-фразу второй раз;
  - значит duplicate final close на success-path ещё оставался.
- Поэтому сверху выпущен ещё один lab-only patch:
  - новая текущая верхняя lab-version:
    - `agtvrsn_2501kv87p0d1e3r8wjpf7rn2mbra`
  - новые блоки:
    - `Single post-SMS spoken close override`
    - `Late rescue cancellation override`
- Смысл:
  - после успешной SMS не повторять spoken close второй раз;
  - backend `call_log` и `end_call` после уже произнесённой финальной реплики должны завершаться тихо;
  - если живой lexical reply уже начался, rescue не должен проскакивать как `...`.
- Артефакты этого шага:
  - `.runtime/eleven_lab_single_close_and_rescue_cancel_2026-06-16/payload_minimal.json`
  - `.runtime/eleven_lab_single_close_and_rescue_cancel_2026-06-16/response.json`
- После этого проведены два branch-targeted self-test уже на:
  - `agtvrsn_2501kv87p0d1e3r8wjpf7rn2mbra`
- Первый:
  - `conv_1301kv87q3h6e8p8apsf5zacq7v7`
  показал:
  - not-target path формально жив;
  - но при шумном ответе пользователя всё ещё возможен race:
    - rescue уходит в `...`
    - первый close/tool draft может быть отменён новым user input;
  - значит `Late rescue cancellation override` пока не доказан как окончательное решение.
- Второй:
  - `conv_6501kv87v0tgeg7bvvtyqt1zy5k7`
  показал более чистую not-target ветку:
  - полноценный exact opener;
  - одна содержательная business-реплика без filler;
  - корректный `call_log(not_target)` с полным identity-пакетом;
  - один чистый spoken close:
    - `Поняла, спасибо. Хорошего дня.`
  - без повторного spoken хвоста.

### На чем остановились

- Live `Main` не менялся.
- Текущая верхняя lab-version:
  - `agtvrsn_2501kv87p0d1e3r8wjpf7rn2mbra`
- Что уже доказано:
  - `No-thanks lead-in` fix работает;
  - `SMS tool failure honesty` patch опубликован;
  - not-target path на новой вершине может проходить чисто.
- Что ещё не доказано:
  - исчез ли duplicate post-SMS close именно на success-path новой вершины `2501`;
  - исчез ли late-rescue `...` в более сложном overlap-кейсе окончательно.

### Что делать дальше

1. Сделать ещё один answered self-test на:
   - `agtvrsn_2501kv87p0d1e3r8wjpf7rn2mbra`
2. Обязательно провести его через SMS-path.
3. На нём проверить сразу два пункта:
   - spoken `Я уже отправила SMS...` звучит только один раз;
   - после живого ответа не проскакивает rescue в виде `...`.

## Обновление 2026-06-16: подтверждён запрет на `Спасибо, ...`, найден SMS-honesty дефект, выпущен новый lab-fix

### Сделано

- На answered self-test:
  - `conv_1501kv86rfxse5d94vpk6bz03fek`
  - `version_id = agtvrsn_9501kv86kqvwegrr2h8rj157k6me`
  подтверждено, что micro-patch:
  - `No-thanks lead-in override`
  реально сработал.
- Что этим звонком подтверждено:
  - больше нет старта содержательной sales-реплики с:
    - `Спасибо, ЛипоЛонг — ...`
  - вместо этого agent продолжает разговор сразу по сути:
    - `ЛипоЛонг — ...`
  - старые хвосты:
    - `Да, я вас слышу. ...`
    - `Отлично! Мы...`
    не вернулись.
- Этим же звонком выявлен новый, уже более важный дефект:
  - `send_sms_info` вернул provider failure:
    - `status = send_error`
    - Mango `429 Too Many Requests`
  - но agent после этого всё равно сказал:
    - `Я уже отправила SMS на этот номер. Хорошего дня.`
  - затем ещё и продублировал эту же финальную реплику второй раз.
- Чтобы закрыть именно этот риск, поверх текущего branch tip выпущен ещё один lab-only patch:
  - новая текущая верхняя lab-version:
    - `agtvrsn_1101kv871mt1e699f6sq7x35epay`
  - новый блок:
    - `SMS tool failure honesty override`
- Смысл нового блока:
  - если `send_sms_info` не подтвердил явный успешный send, считать, что SMS не отправлена;
  - не говорить:
    - `Я уже отправила SMS...`
    если tool вернул `ok:false`, `send_error`, rate limit или другой provider failure;
  - вместо этого закрывать разговор короткой честной репликой и переводить кейс в manager follow-up path;
  - не зацикливать SMS retry в рамках того же звонка.
- Артефакты этого шага сохранены в:
  - `.runtime/eleven_lab_sms_failure_honesty_2026-06-16/payload_minimal.json`
  - `.runtime/eleven_lab_sms_failure_honesty_2026-06-16/response.json`

### На чем остановились

- Live `Main` не менялся.
- В lab текущая верхняя версия теперь:
  - `agtvrsn_1101kv871mt1e699f6sq7x35epay`
- Последний answered звонок, на котором подтверждён `No-thanks lead-in` fix:
  - `conv_1501kv86rfxse5d94vpk6bz03fek`
  - `version_id = agtvrsn_9501kv86kqvwegrr2h8rj157k6me`
- Главный открытый остаток теперь уже не про opener и не про line-check, а про честное завершение SMS-path при ошибке провайдера.

### Что делать дальше

1. Сделать один новый answered self-test уже на:
   - `agtvrsn_1101kv871mt1e699f6sq7x35epay`
2. На нём проверить:
   - если `send_sms_info` снова провалится, agent не должен говорить:
     - `Я уже отправила SMS...`
   - должен ли он вместо этого дать короткую честную failure-close реплику;
   - не остался ли duplicate final close;
   - не вернулся ли filler-хвост `Спасибо, ...`.

## Тема

Третий lab-cycle: возврат на `eleven_v3_conversational`, затем балансировка скорости речи, turn-taking и прерываний для уменьшения задержки и чтобы агент лучше давал человеку сказать.

## Ветка

- текущая рабочая Git-ветка:
  - `codex/eleven-naturalness-lab`

## Lab-ветка ElevenLabs

- `branch_id`:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`

## Сделано

- Дополнительно сверено текущее состояние lab-ветки не по старым локальным артефактам, а прямым `GET` по:
  - `agent_id = agent_8801kgybyekned2a8yae6rp8hk3q`
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- Это подтвердило, что перед новым шагом source-of-truth для lab был:
  - `version_id = agtvrsn_3201kv84a0rkej9tkfg78zz20vvv`
  - `tts.model_id = eleven_v3_conversational`
  - `speed = 1.10`
  - `turn_timeout = 1.78`
  - `disable_first_message_interruptions = true`
- После этого разобран последний завершённый SMS self-test:
  - `conv_3001kv84ehhsererapaa6226mhwv`
- Что по нему подтвердилось:
  - opener уже был быстрым и чистым:
    - `convai_llm_service_ttfb ≈ 0.41s`
  - `send_sms_info` действительно ушёл по явному согласию;
  - `call_log` уже ушёл с полным identity-пакетом и реальным `conv_*`.
- Но этим же звонком вскрылся новый очень узкий хвост:
  - после успешного `send_sms_info` agent дал плохой промежуточный spoken-turn:
    - `...`
  - из-за этого пользователь дал line-check:
    - `Алло!`
    - `Алло! Алло!`
  - то есть проблема теперь была не в opener и не в SMS fast-path, а в post-SMS dead air / punctuation-only response.
- Поэтому поверх текущего verified lab-state внесён ещё один очень маленький patch:
  - новая верхняя lab-version:
    - `agtvrsn_6601kv84qjbjetvaafn1t7yzkswh`
  - новый блок в prompt:
    - `Post-SMS no-dead-air override`
  - смысл:
    - после успешного `send_sms_info` не разрешать spoken-turn вида `...`;
    - не оставлять dead air между tool-result и коротким подтверждением;
    - line-check вроде `алло?` после SMS трактовать как реакцию на задержку, а не как новую тему;
    - в таком кейсе говорить одну короткую фразу про уже отправленную SMS и завершать звонок.
- Артефакты этого шага сохранены в:
  - `.runtime/eleven_lab_post_sms_no_dead_air_2026-06-16/payload.json`
  - `.runtime/eleven_lab_post_sms_no_dead_air_2026-06-16/response.json`
- После применения patch запущен новый branch-targeted self-test:
  - `conv_7601kv84skecfh783bsw4hg5qzn9`
  - version:
    - `agtvrsn_6601kv84qjbjetvaafn1t7yzkswh`
- Что этим звонком удалось подтвердить:
  - branch/version реально совпали:
    - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
    - `agtvrsn_6601kv84qjbjetvaafn1t7yzkswh`
  - opener остался быстрым:
    - `convai_llm_service_ttfb ≈ 0.58s`
  - agent больше не дал старый плохой промежуточный spoken-turn `...`;
  - звонок корректно дошёл до `refusal_soft`.
- Что этим звонком не удалось подтвердить:
  - разговор не дошёл до `send_sms_info`, потому что пользователь отказался от SMS;
  - значит новый `Post-SMS no-dead-air override` уже применён и косвенно выглядит здоровым, но ещё ждёт отдельной answered проверки именно на SMS-accept path.
- После этого поверх текущего verified lab-state внесён ещё один узкий patch:
  - новая верхняя lab-version:
    - `agtvrsn_7801kv85988ee7t8jgdwzrsk1ry6`
  - новый блок:
    - `Final close clarity override`
  - смысл:
    - в финальном live-human close не оставлять обрубки вроде `Поняла, спасибо...`;
    - не говорить канцелярщину вроде `Я уже зафиксировала ваш отказ` и `информация сохранена`;
    - если пользователь даёт короткий line-check во время close, повторять короткую человеческую финальную фразу, а не уходить в CRM-style объяснение.
- Артефакты этого шага сохранены в:
  - `.runtime/eleven_lab_final_close_clarity_2026-06-16/payload.json`
  - `.runtime/eleven_lab_final_close_clarity_2026-06-16/response.json`
- На этой версии сделан следующий answered self-test:
  - `conv_6801kv85a8wzfkx9kwj3qkksmgdx`
  - version:
    - `agtvrsn_7801kv85988ee7t8jgdwzrsk1ry6`
- Что он подтвердил:
  - SMS-path уже реально прошёл до конца;
  - `send_sms_info` отработал по живому согласию;
  - после line-check:
    - `Алло!`
    agent дал именно короткое человеческое подтверждение:
    - `Я уже отправила SMS на этот номер. Хорошего дня.`
  - старый плохой хвост:
    - `...`
    не появился;
  - старая роботская фраза:
    - `Я уже зафиксировала ваш отказ, информация сохранена.`
    тоже не вернулась;
  - `call_log` снова ушёл с полным identity-пакетом и правильным:
    - `conversation_id = conv_6801kv85a8wzfkx9kwj3qkksmgdx`
    - `eleven_conv_id = conv_6801kv85a8wzfkx9kwj3qkksmgdx`
- После этого поверх текущего verified lab-state внесён ещё один узкий patch:
  - новая верхняя lab-version:
    - `agtvrsn_5701kv85jqxefp78hnjgewa0mqbb`
  - изменения:
    - `soft_timeout_config.message = "Алло?"`
    - `soft_timeout_config.llm_generated_message_prompt_override` ужат до line-check длиной максимум `1-2` слова
  - новый блок:
    - `Rescue micro-cut override`
  - смысл:
    - rescue-line должна быть ультракороткой;
    - даже при перебивании она должна звучать завершённо;
    - уйти от длинной формы вроде:
      - `Алло, вы на линии?`
- Артефакты этого шага сохранены в:
  - `.runtime/eleven_lab_rescue_microcut_2026-06-16/payload.json`
  - `.runtime/eleven_lab_rescue_microcut_2026-06-16/response.json`
- На этой версии сделан answered self-test:
  - `conv_4801kv85k83afcvvrc44nw1wdem4`
  - version:
    - `agtvrsn_5701kv85jqxefp78hnjgewa0mqbb`
- Что он подтвердил:
  - rescue стал короче:
    - вместо старого длинного обрывающегося
      `Алло, вы на лин...`
      теперь прошёл короткий interrupted line-check:
      `Алло?...`
  - SMS-path по-прежнему проходит до конца;
  - post-SMS close сохранился чистым:
    - `Я уже отправила SMS на этот номер. Хорошего дня.`
- Но этот же звонок вскрыл следующий тонкий хвост:
  - в середине активного диалога после line-check agent всё ещё мог уйти в support-style ход:
    - `Да, я вас слышу. Мы предлагаем ...`
  - а перед этим оставался обрубок:
    - `Отлично! Мы...`
- Поэтому сверху внесён ещё один узкий patch:
  - новая текущая верхняя lab-version:
    - `agtvrsn_6901kv85rrfxesqab1q9mjhmmd8r`
  - новый блок:
    - `Mid-dialogue line-check continuation override`
  - смысл:
    - если короткий `алло` приходит уже внутри живого разговора, не отвечать support-фразой
      `Да, я вас слышу`;
    - не продолжать обрубок вроде `Отлично! Мы...`;
    - продолжать с одной свежей короткой business-реплики по смыслу.
- Артефакты этого шага сохранены в:
  - `.runtime/eleven_lab_mid_dialogue_linecheck_2026-06-16/payload.json`
  - `.runtime/eleven_lab_mid_dialogue_linecheck_2026-06-16/response.json`
- После применения patch запущен следующий self-test:
  - `conv_1901kv85s843fcft09kfqz0q07c0`
  - version:
    - `agtvrsn_6901kv85rrfxesqab1q9mjhmmd8r`
- Позже по этому звонку уже получен полный usable transcript и он подтвердил effect patch:
  - support-style хвост:
    - `Да, я вас слышу. ...`
    больше не появился;
  - обрубок:
    - `Отлично! Мы...`
    тоже не вернулся;
  - после mid-dialogue line-check agent продолжил разговор уже нормальной business-репликой по смыслу, а не сервисным подтверждением линии;
  - draft `call_log(no_answer)` внутри этого звонка не ушёл в таблицу:
    - tool-result явно вернул:
      `Tool execution was abandoned due to user input`
    - значит ложный `no_answer` не зафиксировался и активный диалог корректно продолжился;
  - SMS-path в конце звонка снова дошёл до чистого финала:
    - `Я уже отправила SMS на этот номер. Хорошего дня.`
- Этим же answered логом вскрылся уже не аварийный, а косметический хвост:
  - одна из смысловых business-реплик после возобновления диалога началась с:
    - `Спасибо, ЛипоЛонг — ...`
  - то есть следующий тонкий naturalness-шаг теперь уже не про machine / rescue / SMS-close, а про запрет автоматического `Спасибо` в начале смысловой продажной реплики.
- После этого выпущен ещё один lab-only micro-patch поверх текущего branch tip:
  - новая текущая верхняя lab-version:
    - `agtvrsn_9501kv86kqvwegrr2h8rj157k6me`
  - новый блок:
    - `No-thanks lead-in override`
  - смысл:
    - запретить автоматическое `Спасибо` в начале содержательной sales-реплики;
    - после возврата в живой диалог заходить сразу с сути:
      `ЛипоЛонг — ...`,
      а не с filler-вступления.
- Артефакты этого шага сохранены в:
  - `.runtime/eleven_lab_no_thanks_leadin_2026-06-16/payload_minimal.json`
  - `.runtime/eleven_lab_no_thanks_leadin_2026-06-16/response.json`
- Техническая заметка по доставке patch:
  - прямой PATCH с сервера `ai-core-prod-147` снова уткнулся в `302 Moved` на help-статью ElevenLabs;
  - сам patch успешно выпущен локально с рабочим `xi-api-key`, аккуратно полученным из серверного `.env.callcenter`, без вывода секрета в лог.

- Дополнительно проверен официальный ElevenLabs simulation endpoint как возможный branch-specific gate для lab-ветки.
- Что для этого было сделано:
  - simulation-запрос собран с mocked tools;
  - добавлены обязательные dynamic variables:
    - `system__called_number`
    - `system__conversation_id`
  - в запрос передан:
    - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- Что показал probe:
  - endpoint выполнился;
  - но в transcript `agent_metadata` вернулись:
    - `branch_id = null`
    - `version_id = null`
  - и по фактическому поведению ответ ушёл не в текущий lab-state, а в generic/helpdesk-like ветку с финальным хвостом:
    - `Чем-то ещё могу быть полезна?`
- Практический вывод:
  - в текущем виде simulation API нельзя считать надёжной branch-specific проверкой для `lab_naturalness_2026_06`;
  - для этой ветки source-of-truth остаются только branch-targeted outbound self-tests.
- После этого поверх текущего верхнего lab-state внесён ещё один маленький patch на баланс скорости и терпения:
  - новая version:
    - `agtvrsn_2601kv834er0fk8vj7y274cgbwrz`
  - изменения:
    - `turn_timeout: 1.55 -> 1.68`
    - `speed: 1.08 -> 1.10`
    - в `interruption_ignore_terms` добавлены:
      - `так`
      - `ну вот`
      - `одну секунду`
      - `подождите секунду`
      - `сейчас секунду`
    - в prompt добавлен блок:
      - `Fine patience-speed override`
  - смысл:
    - говорить чуть быстрее;
    - но давать человеку чуть больше воздуха после короткого вопроса;
    - не врезаться в живой старт ответа на fillers и коротких hold-signals.
- На этой версии сделан branch-targeted self-test:
  - `conv_1601kv839wdwes8ahy26xhhfxn4q`
  - version:
    - `agtvrsn_2601kv834er0fk8vj7y274cgbwrz`
- Что подтвердилось:
  - opener остался быстрым:
    - `convai_llm_service_ttfb ≈ 0.62s`
  - live branch/version в разговоре совпали:
    - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
    - `agtvrsn_2601kv834er0fk8vj7y274cgbwrz`
  - post-SMS helpdesk-tail вида:
    - `Могу чем-то ещё помочь?`
    действительно не прозвучал.
- Но по этому же тесту вскрылись новые хвосты:
  - после вопроса про официальный канал всё ещё был cut/recovery эпизод с лишним:
    - `Да, я на линии`
  - при явном согласии на SMS:
    - `М-м-м, д-д-да, ну- Да-да, давайте`
    agent слишком долго тянул до реального `send_sms_info`:
    - user-turn на `73s`
    - `send_sms_info` только на `93s`
- Поэтому сверху внесён ещё один узкий patch:
  - новая version:
    - `agtvrsn_2801kv83g2e2etzshp45kttfs7g2`
  - добавлен блок:
    - `Explicit consent fast-path override`
  - смысл:
    - явное согласие на SMS трактовать как финальное permission сразу;
    - не ждать более чистой фразы;
    - trailing `алло?` после согласия не должен ломать отправку SMS;
    - после interrupted explanation не уходить в support-style `Да, я на линии`.
- На этой версии сделан следующий branch-targeted self-test:
  - `conv_6101kv83gpnhfvrvkdq2jmba0q4m`
  - version:
    - `agtvrsn_2801kv83g2e2etzshp45kttfs7g2`
- Что он показал:
  - opener снова быстрый:
    - `convai_llm_service_ttfb ≈ 0.63s`
  - post-SMS fast-path этим звонком не проверился, потому что разговор ушёл в `not_target`;
  - но зато обнаружился следующий устойчивый хвост:
    - после ясного ответа:
      - `Нет, не использую`
    agent всё ещё ушёл в лишнее support-like завершение:
      - `Да, я вас слышу. Если что-то понадобится...`
  - плюс qualification-turn после opener всё ещё был перегружен:
    - два вопроса в одном turn.
- Поэтому сверху внесён ещё один точечный patch:
  - новая текущая верхняя lab-version:
    - `agtvrsn_0801kv83n73eeaqs89n9d672dntv`
  - добавлен блок:
    - `Clear not-target close override`
  - смысл:
    - ясное `не использую / не наш профиль` сразу считать финальным `not_target`;
    - trailing `алло` после такого ответа не должен переоткрывать разговор;
    - support-style `Да, я вас слышу` запрещён на clear `not_target`;
    - после opener на qualification-ходе задавать только один простой вопрос.
- На этой версии сделан следующий branch-targeted self-test:
  - `conv_9501kv83tn2yfcjvbdk17gwn8g2b`
  - version:
    - `agtvrsn_0801kv83n73eeaqs89n9d672dntv`
- Что он подтвердил:
  - `not_target`-хвост `Да, я вас слышу...` действительно ушёл;
  - qualification-turn после opener стал проще:
    - `Поняла, а вы вообще с липолитиками работаете?`
- Но именно этот тест вскрыл регресс в opener:
  - первая реплика снова развалилась на:
    - `Здравствуйте, я официальный ...`
    - потом отдельно:
      - `Это липолитик для косметологов. Вам это интересно?`
- Поэтому сверху внесён ещё один узкий patch:
  - новая version:
    - `agtvrsn_9101kv83y38jfcs95sqg87qtxwk0`
  - добавлен блок:
    - `Absolute opener integrity override`
  - смысл:
    - при срезе opener в начале не переходить сразу ко второй половине, а повторять весь opener целиком.
- На этой версии сделан следующий branch-targeted self-test:
  - `conv_3801kv83ynrxfszvvbfyzry92pkx`
  - version:
    - `agtvrsn_9101kv83y38jfcs95sqg87qtxwk0`
- Что он подтвердил:
  - opener уже не развалился на отдельные половины;
  - после микрообрыва:
    - `Здравств...`
    agent действительно дал полный exact opener заново;
  - `not_target`-закрытие осталось чистым;
  - qualification-turn остался коротким и с одним вопросом.
- Что ещё осталось после этого:
  - standalone micro-fragment `Здравств...` всё ещё успел прозвучать как отдельный tiny-turn до полного opener restart;
  - в drafted `call_log` всё ещё появились literal placeholders:
    - `conversation_id = system__conversation_id`
    - `eleven_conv_id = system__conversation_id`
    хотя downstream `call_log` нормализовал их в правильный текущий `conv_*`.
- Поэтому сверху внесён ещё один текущий polish-patch:
  - новая текущая верхняя lab-version:
    - `agtvrsn_4701kv842k7we7w9hzq0frfhejj4`
  - добавлены блоки:
    - `Opener micro-cut polish override`
    - `Final call_log payload override`
  - смысл:
    - не оставлять самостоятельный opener-обрубок вроде `Здравств...`;
    - не оставлять literal placeholder-id в финальном draft tool-call;
    - на `not_target` явно драфтить `next_step=archive`.

- На compact-prompt lab-state выполнен возврат voice-layer на:
  - `eleven_v3_conversational`
  - `expressive_mode = true`
  - `speed = 1.02`
  - `stability = 0.42`
  - `similarity_boost = 0.78`
- После этого сделан manual self-test:
  - `conv_2601kv7yka71f5qan6hczca1ttj1`
- Что он показал:
  - opener прошёл правильно;
  - первый ответ после `Алло!` был слишком медленным:
    - `convai_llm_service_ttfb ≈ 3.07s`
  - дальше ответы шли уже заметно быстрее;
  - rescue отработал нормально;
  - звонок корректно закрылся как `not_target`.
- Затем выполнен отдельный balance-patch для V3:
  - новая version:
    - `agtvrsn_1301kv7ywxgffw3sjg90zfd283av`
  - изменения:
    - `speed: 1.02 -> 1.08`
    - `turn_timeout: 1.25 -> 1.4`
    - `turn_eagerness: eager -> normal`
    - в `client_events` и `monitoring_events` добавлен:
      - `interruption`
- На этом состоянии выполнен новый manual self-test:
  - `conv_7601kv7yxe4zfb5tbkbh5hwp53ky`
- Что подтвердилось по этому тесту:
  - первый ответ ускорился резко:
    - было:
      - `convai_llm_service_ttfb ≈ 3.07s`
    - стало:
      - `convai_llm_service_ttfb ≈ 0.53s`
  - opener начал приходить почти сразу после первого `Алло!`;
  - средние ответные задержки на обычных ходах держались в районе:
    - `~0.54–0.60s`
  - прерывание агента человеком теперь реально сработало:
    - длинный agent-turn на `91s` был отмечен как `interrupted = true`
  - значит lab-комбинация стала заметно живее и лучше слушает пользователя.
- По факту этого же теста найден новый остаток:
  - agent всё ещё может уходить в слишком длинную explain-реплику;
  - после `send_sms_info` он попытался сказать лишний хвост:
    - `Я отправила вам СМС ... Могу чем-то ещё...`
- Поэтому сверху внесён ещё один маленький prompt-fix:
  - новая version:
    - `agtvrsn_8501kv7z35n9eggamnvq4qe8ygwe`
  - добавлены правила:
    - после `send_sms_info` только одна короткая подтверждающая фраза и закрытие;
    - не говорить `Могу чем-то ещё...`;
    - explain-turn по запросу подробностей держать максимум в `2` коротких предложениях и `1` коротком вопросе;
    - не начинать substantive turn с `Спасибо за интерес`.
- После этого сделан подтверждающий self-test:
  - `conv_7301kv80fj49ehctrxt75jhh3661`
- Что он подтвердил:
  - SMS-tail действительно ушёл;
  - финальное закрытие стало чистым:
    - `Поняла, спасибо. Хорошего дня.`
  - первый ответ остался быстрым:
    - `convai_llm_service_ttfb ≈ 0.47s`
- По этому тесту обнаружились ещё два маленьких остатка:
  - agent всё ещё мог начинать substantive turn с:
    - `Спасибо за уточнение`
  - после подтверждения `Да, работаем` он слишком быстро прыгал прямо в `SMS`
- Поэтому сверху внесён ещё один polish-follow-up:
  - новая version:
    - `agtvrsn_8601kv80kmqze13v7t7vyxjcmz44`
  - дополнительно закреплено:
    - не начинать содержательный ход с `Спасибо за уточнение`
    - после подтверждения, что контакт работает с липолитиками, не прыгать сразу в `SMS`, а сначала дать короткий value-line и один короткий вопрос
    - literal `system__conversation_id` запрещён как финальное значение tool-call и при появлении должен вести к регенерации tool-call
- После этого сделан длинный стресс-тест:
  - `conv_4201kv80r134fcybkwxa41477d52`
  - version:
    - `agtvrsn_8601kv80kmqze13v7t7vyxjcmz44`
- Что он подтвердил:
  - `Спасибо за уточнение` действительно ушло;
  - после `Да, работаем` agent уже не прыгал мгновенно в `SMS`, а сначала дал короткий value-line;
  - первый ответ остался быстрым:
    - `convai_llm_service_ttfb ≈ 0.55s`
- Но этот же stress-test вскрыл следующий более глубокий хвост:
  - в длинном live-диалоге agent всё ещё мог слишком рано драфтить `call_log(no_answer)`;
  - если человек после этого снова говорил, agent мог продолжить разговор не с текущего состояния, а с кривым финализационным хвостом;
  - в самом плохом кейсе он даже перезапустил exact opener внутри того же звонка.
- Поэтому сверху внесён ещё один continuity-fix:
  - новая верхняя version:
    - `agtvrsn_8701kv8113z8ebps89308e2yfe8h`
  - в ней дополнительно закреплено:
    - при новом живом слове (`что?`, `алло`, `секунду`, формирующийся вопрос и т.п.) отменять pending `no_answer` финализацию;
    - не перезапускать exact opener второй раз в пределах того же звонка;
    - повторная просьба объяснить подробнее должна вести к ещё одному короткому содержательному ответу, а не к циклу одного и того же SMS-offer;
    - если пользователь заговорил во время draft `call_log/end_call`, нужно продолжить диалог, а не закрываться по старому плану.
- После этого сделан continuity-validation self-test:
  - `conv_8801kv813p1qetr8n3tbcw0cfz4e`
  - version:
    - `agtvrsn_8701kv8113z8ebps89308e2yfe8h`
- Что подтвердилось:
  - stale `no_answer` финализация больше не ломает длинный живой разговор;
  - repeated-detail ветка больше не скатывается в тупой цикл одного и того же SMS-offer;
  - разговор дошёл до нормального человеческого исхода:
    - `call_result = manager_call`
    - `next_step = call_manager`
  - `call_log` ушёл с корректным текущим:
    - `conversation_id = conv_8801kv813p1qetr8n3tbcw0cfz4e`
    - `eleven_conv_id = conv_8801kv813p1qetr8n3tbcw0cfz4e`
  - финальное завершение прошло штатно:
    - менеджер свяжется, затем `end_call`
- Что ещё осталось:
  - на самом раннем старте user успел перебить самый первый кусок opener (`Здравствуйте, я...`), после чего agent уже выдал полный fixed opener;
  - это уже не старый catastrophic opener-restart, но раннюю opener-fragment ветку ещё стоит сделать аккуратнее.
- После этого сделан отдельный early-opener validation test:
  - `conv_1201kv81g2tgfpfr2ge32khc5qg2`
  - version:
    - `agtvrsn_3601kv81fnbbf4rvz38gy18czswx`
- Для этого слоя отдельно включено:
  - `disable_first_message_interruptions = true`
- Что подтвердилось:
  - самый ранний opener-fragment на первом ходе ушёл;
  - agent сразу дал полный fixed opener:
    - `Здравствуйте, я официальный представитель липолитика Липолонг...`
  - ранний double-`Алло?` сценарий уже не ломает старт разговора;
  - дальше звонок дошёл до нормального `refusal_soft` закрытия.
- Что ещё осталось после этого:
  - в середине разговора при перебивании agent всё ещё может начинать короткие обрывки вроде:
    - `Вам...`
    - `Липолонг — это оригинальный...`
  - это уже не критический сбой сценария, а следующий уровень polish для mid-turn interruption handling.
- После этого применён ещё один mid-turn polish:
  - version:
    - `agtvrsn_1001kv81rpcpf4v9a615gmx1fan5`
  - изменения:
    - `turn_timeout: 1.4 -> 1.55`
    - добавлено правило не возобновлять обрубленный fragment, а отвечать заново по смыслу
- Тест:
  - `conv_4001kv81s2m9enyvnwkz8feyga45`
- Что он показал:
  - часть mid-turn поведения стала мягче;
  - но после сорванного закрытия agent всё ещё проваливался в helpdesk-хвост:
    - `Могу чем-то ещё помочь?`
- Поэтому сверху внесён ещё один отдельный fix только для post-SMS/final-close ветки:
  - новая текущая верхняя lab-version:
    - `agtvrsn_5701kv824nz2ew6bbzeekap0wgsb`
  - логика:
    - после `send_sms_info` считать звонок в режиме final-close;
    - не задавать `Могу чем-то ещё помочь?`;
    - не открывать заново discovery;
    - если user говорит короткое `алло?`, только коротко подтвердить, что SMS уже отправлена, и закрыть.
- Важно:
  - этот post-SMS final-close fix пока ещё не доказан на целевом живом сценарии;
  - два подряд проверочных звонка:
    - `conv_8301kv826ce3f9tt4vdr65qnc41c`
    - `conv_2601kv8292ttfasbyt85rd46b03n`
    не дошли до ветки `send_sms_info -> interrupted close`, потому что пользователь отказался от SMS раньше.

## Артефакты

- `.runtime/eleven_lab_compact_prompt_cycle_2026-06-16/`
- `.runtime/eleven_lab_fine_patience_speed_2026-06-16/`
- `.runtime/eleven_lab_sms_consent_fastpath_2026-06-16/`
- `.runtime/eleven_lab_not_target_close_2026-06-16/`
- `.runtime/eleven_lab_opener_integrity_2026-06-16/`
- `.runtime/eleven_lab_opener_microcut_calllog_2026-06-16/`

## На чем остановились

- Live `Main` по-прежнему не тронут.
- Текущая верхняя lab-version по прямой branch-проверке теперь:
  - `agtvrsn_9501kv86kqvwegrr2h8rj157k6me`
- Последняя полностью подтверждённая answered вершина теперь:
  - `agtvrsn_6901kv85rrfxesqab1q9mjhmmd8r`
  - звонок:
    - `conv_1901kv85s843fcft09kfqz0q07c0`
- Последняя подтверждённая SMS close-path вершина:
  - `agtvrsn_7801kv85988ee7t8jgdwzrsk1ry6`
  - звонок:
    - `conv_6801kv85a8wzfkx9kwj3qkksmgdx`
- Текущий остаточный фронт:
  - mid-dialogue continuity уже подтверждена answered логом;
  - ложный `call_log(no_answer)` внутри активного диалога не фиксируется, если user успел заговорить;
  - новый micro-patch на `Спасибо, ...` уже выпущен, но ещё не проверен answered звонком;
  - дополнительный хвост второго порядка:
    - rescue всё ещё может транскрибироваться как `Алло?...`, хотя уже заметно короче и чище, чем раньше.

## Что делать дальше

1. Оставить live `Main` без изменений.
2. Сделать один короткий answered self-test на текущей вершине:
   - `agtvrsn_9501kv86kqvwegrr2h8rj157k6me`
3. На этом звонке проверить:
   - исчезло ли `Спасибо, ЛипоЛонг — ...`;
   - не вернулись ли `Да, я вас слышу. ...` и `Отлично! Мы...`;
   - сохранились ли быстрый opener и чистый SMS-close.
4. Если это проходит без регрессии, можно считать lab-контур зрелым кандидатом для очень маленькой канарейки.
