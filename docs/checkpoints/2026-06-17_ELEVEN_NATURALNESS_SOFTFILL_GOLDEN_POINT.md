# Контрольная точка — 2026-06-17

## Обновление 2026-06-17: prompt-only cleanup-серия не выбила дубль close и lab возвращён на softfill-линию

### Сделано

- После золотой V3 softfill-линии были проверены три узких cleanup-кандидата:
  - `agtvrsn_5701kvaaanp8feqvj6s1hrcw2mp0`
  - `agtvrsn_4701kvaafxaket0rtt3y5hnt9q14`
  - `agtvrsn_9501kvaapngkexzr5964jhvbh4zw`
- Их цель была очень узкая:
  - убрать line-check после осмысленного post-opener ответа;
  - убрать filler во время финализации;
  - убрать двойной spoken close перед `call_log` и внутри `end_call`.
- Что реально подтвердили контрольные звонки:
  - `conv_7001kvaa3cv7emkbw8ztmn9tyg95`
  - `conv_4601kvaabcqaf37tw4tbr87y8s28`
  - `conv_1701kvaaqez7ehyv5d39m3egvwx4`
- Итог по серии:
  - prompt-only ужесточения не выбили устойчиво ни duplicate close, ни повторные line-check хвосты;
  - в одном из циклов всё ещё звучали:
    - `Поняла, спасибо. Хорошего дня.` как обычная реплика до `call_log`
    - затем тот же close повторно через `end_call`
  - в другом цикле всё ещё вылезали:
    - `Так...`
    - `Вы на линии?`
    внутри уже финализируемого отказа.
- После этого lab-ветка возвращена обратно на проверенную softfill-линию.
- Новый текущий branch-head после возврата:
  - `agtvrsn_1201kvaavm18fe8b4sgw5vxt7tqy`
- По смыслу это возврат к той же рабочей золотой конфигурации:
  - `gpt-5-mini + eleven_v3_conversational + soft timeout`

### На чем остановились

- Текущим source-of-truth для lab снова считается именно softfill-линия, а не cleanup-кандидаты.
- Важный практический вывод:
  - следующий шаг уже не в том, чтобы просто дописывать ещё один запрет в prompt;
  - prompt-only путь для `duplicate close / late line-check / finalization filler` уже показал слабый эффект.

### Что делать дальше

1. Следующий цикл снова начинать от:
   - `agtvrsn_1201kvaavm18fe8b4sgw5vxt7tqy`
2. Не продолжать бесконечную серию текстовых запретов в prompt.
3. Следующий реальный фронт делать уже более структурно:
   - отдельный harness именно под `finalization`;
   - или более жёсткий контроль ветки `call_log -> end_call`;
   - или изоляция SMS-path от общего final-close режима.

## Обновление 2026-06-17: зафиксирована текущая золотая точка naturalness-lab на `GPT-5 Mini + Eleven v3 Conversational + soft timeout`

### Сделано

- После серии lab-экспериментов и возвратов зафиксирована текущая лучшая рабочая линия для naturalness-теста:
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - текущий верхний `version_id`:
    - `agtvrsn_1101kva7s8drfz4r26j2ymbt9r9j`
- Это именно возврат на удачную softfill-конфигурацию, а не новый рискованный эксперимент:
  - `llm = gpt-5-mini`
  - `tts.model_id = eleven_v3_conversational`
  - `soft_timeout_config.timeout_seconds = 2.8`
  - fallback filler:
    - `Так...`
- Лучший подтверждённый self-test этой линии:
  - `conv_0501kva6snynemktpje537318ep5`
- Что по нему подтверждено:
  - opener стартует быстро и чисто;
  - agent держит живой бизнес-разговор лучше, чем многие предыдущие V3-кандидаты;
  - `send_sms_info`, `call_log` и `end_call` проходят успешно;
  - overall naturalness субъективно сильная и уже годится как эталон для следующего узкого цикла.
- Дополнительно зафиксировано ограничение:
  - branch-level `soft timeout` закрепляется нормально;
  - branch-level `tool_call_sound` для shared tools через `Update agent` в нашем контуре не закрепился;
  - значит shared tool patch без отдельного решения сейчас небезопасен.
- Отдельно проверен узкий кандидат:
  - `SMS fastlane`
  - `version_id = agtvrsn_3501kva75b4qf6htw6qkys1j1q6b`
- Итог по fastlane:
  - честного выигрыша не дал;
  - словил лишние line-check хвосты;
  - новой нормой не признан.

### На чем остановились

- Live `Main` не менялся и не должен использоваться для naturalness-экспериментов.
- Текущий source-of-truth для lab:
  - `agtvrsn_1101kva7s8drfz4r26j2ymbt9r9j`
- Главная нерешённая проблема уже локализована:
  - не сам SMS-tool;
  - не TTS;
  - а длинная пауза в ветке:
    - `попросили SMS -> LLM думает -> send_sms_info`
- По лучшему подтверждённому звонку эта пауза зафиксирована как:
  - `convai_llm_service_ttfb ≈ 4.41s`
- То есть на сегодня главная цель уже не “сделать агент хоть как-то живым”.
- Главная цель уже уже:
  - сохранить этот хороший разговор;
  - и отдельно срезать только SMS decision-gap без регресса по opener, line-check и close.

### Что делать дальше

1. Сделать ещё один подтверждающий self-test именно на:
   - `agtvrsn_1101kva7s8drfz4r26j2ymbt9r9j`
2. На этом звонке проверить:
   - сохраняется ли хороший opener;
   - не деградировал ли naturalness;
   - повторяется ли тот же длинный хвост перед `send_sms_info`.
3. После этого делать только один узкий цикл правки:
   - сокращать SMS decision-gap;
   - не трогать весь стиль разговора;
   - не менять live `Main`.
4. Если новая узкая правка ухудшит разговор хотя бы по одному из пунктов:
   - opener;
   - лишние line-check;
   - ранний hangup;
   - грязный финальный close;
   сразу возвращаться на:
   - `agtvrsn_1101kva7s8drfz4r26j2ymbt9r9j`

## Артефакты

- Payload softfill-линии:
  - `.runtime/eleven_lab_gpt5mini_v3_softfill_2026-06-17/payload.json`
- Ответ применения:
  - `.runtime/eleven_lab_gpt5mini_v3_softfill_2026-06-17/apply_result/response.json`
- Лучший self-test:
  - `.runtime/eleven_lab_gpt5mini_v3_softfill_2026-06-17/call_01_selftest/`
- Отклонённый fastlane-кандидат:
  - `.runtime/eleven_lab_gpt5mini_v3_sms_fastlane_2026-06-17/`
