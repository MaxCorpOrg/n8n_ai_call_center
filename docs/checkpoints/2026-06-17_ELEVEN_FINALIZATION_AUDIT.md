# Контрольная точка — 2026-06-17

## Обновление 2026-06-17: добавлен локальный auditor для хвостов финализации в Eleven conversation JSON

### Сделано

- Добавлен новый локальный analyzer:
  - [scripts/analyze_eleven_conversation.py](/home/max/n8n_ai_call_center/scripts/analyze_eleven_conversation.py:1)
- Добавлен wrapper для повторяемого цикла:
  - [scripts/run_eleven_selftest_audit.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_selftest_audit.sh:1)
- Он разбирает `conversation_poll_final.json` и автоматически ловит типовые хвосты:
  - `duplicate_close_before_end_call`
  - `line_check_after_meaningful_post_opener_reply`
  - `filler_during_finalization`
  - `placeholder_conversation_id_in_tool_call`
  - `bracketed_stage_direction`
  - `context_fetch_before_opener`
- На его основе собран audit-файл:
  - `.runtime/eleven_lab_golden_confirm_2026-06-17/finalization_audit.json`
- Wrapper поддерживает два режима:
  - полный цикл:
    - self-test -> final JSON -> audit
  - audit-only:
    - взять уже готовую папку звонка и сразу получить `finalization_audit.json`
- Отдельно усилена нормализация close-сравнения:
  - analyzer теперь убирает bracket stage tags вроде `[calm]` перед сравнением закрывающей реплики с `end_call.system__message_to_speak`
  - это нужно, потому что раньше дубликат close мог ложно не считаться дублем, если первая обычная реплика шла как:
    - `Я уже отправила SMS на этот номер. Хорошего дня. [calm]`
    а `end_call` нёс тот же текст уже без тега.

### Что проверили

- Проверены реальные self-test разговоры:
  - `conv_1701kva89ph3fke81jyw9c54zzk2`
    - `agtvrsn_1101kva7s8drfz4r26j2ymbt9r9j`
  - `conv_7001kvaa3cv7emkbw8ztmn9tyg95`
    - `agtvrsn_1101kva7s8drfz4r26j2ymbt9r9j`
  - `conv_4601kvaabcqaf37tw4tbr87y8s28`
    - `agtvrsn_5701kvaaanp8feqvj6s1hrcw2mp0`
  - `conv_5001kvaagqr5edrabknwftdw5dz1`
    - `agtvrsn_4701kvaafxaket0rtt3y5hnt9q14`
  - `conv_1701kvaaqez7ehyv5d39m3egvwx4`
    - `agtvrsn_9501kvaapngkexzr5964jhvbh4zw`

### Что показал audit

- Базовая золотая версия не всегда ломается одинаково:
  - один контрольный звонок прошёл без найденных финализационных хвостов;
  - другой на той же версии уже дал:
    - `duplicate_close_before_end_call`
    - `line_check_after_meaningful_post_opener_reply`
    - `placeholder_conversation_id_in_tool_call`
    - `bracketed_stage_direction`
- Cleanup-серия не стала лучше:
  - один кандидат добавил `filler_during_finalization`;
  - другой всё ещё оставил duplicate close и late line-check;
  - третий снова дал duplicate close и placeholder-хвосты.
- Отдельно проверен сильный SMS self-test:
  - `conv_0501kva6snynemktpje537318ep5`
  - даже он показал:
    - `duplicate_close_before_end_call`
    - множественные `bracketed_stage_direction`
  - это важно: даже хороший по ощущению разговор ещё не означает чистую финализацию.

### На чем остановились

- Теперь есть воспроизводимый локальный способ проверять хвосты по JSON, а не только слушать звонки руками.
- Это меняет следующий фронт работы:
  - больше не гадать, “кажется, стало лучше или хуже”;
  - запускать self-test;
  - затем прогонять `analyze_eleven_conversation.py`;
  - и принимать решение по фактическим issue types.

### Что делать дальше

1. Следующий цикл вести от текущей softfill-линии:
   - `agtvrsn_1201kvaavm18fe8b4sgw5vxt7tqy`
2. После каждого нового self-test использовать уже готовый рабочий цикл:
   - `scripts/run_eleven_selftest_audit.sh OUTPUT_DIR TO_NUMBER TEST_KEY BRANCH_ID EXPECTED_VERSION_ID`
   - или:
   - `scripts/run_eleven_selftest_audit.sh --audit-only OUTPUT_DIR`
3. Следующий инженерный шаг уже не в новом prompt-only запрете, а в более жёстком контуре финализации:
   - отдельно прибить `duplicate_close_before_end_call`;
   - отдельно прибить `placeholder_conversation_id_in_tool_call`;
   - отдельно решить, нужен ли `context_fetch` до opener.

## Обновление 2026-06-17: tool-layer finalization patch не принят как новый winner

### Сделано

- Для отдельной structural-пробы добавлен helper:
  - [scripts/prepare_eleven_finalization_tool_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_finalization_tool_variant.sh:1)
- Его задача была узкой:
  - не трогать opener и objection-flow;
  - усилить именно tool-layer описание:
    - `call_log`
    - `end_call`
  - и заставить модель проходить финализацию только как:
    - silent `call_log`
    - один spoken `end_call`
- Выпущен кандидат:
  - `agtvrsn_9001kvac85yzfhgv8fx3tgqnvn7b`
- Контрольный звонок:
  - `conv_1101kvac8w32fjdtvay58v040esw`

### Что показал audit

- После улучшения analyzer стало видно, что duplicate close на этом звонке никуда не исчез:
  - обычная реплика:
    - `Я уже отправила SMS на этот номер. Хорошего дня. [calm]`
  - затем повтор того же close в:
    - `end_call.system__message_to_speak`
- Дополнительно вылезла сильная регрессия разговора:
  - массовые `[calm]`
  - повторные поздние line-check
  - зацикливание SMS-ветки

### На чем остановились

- Этот tool-layer patch не принят как новая рабочая точка.
- После него lab-ветка уже возвращена на безопасную линию.
- Новый branch-head после отката:
  - `agtvrsn_7301kvacfzesee19rmc9fs22m49e`

### Что делать дальше

1. Не возвращаться на:
   - `agtvrsn_9001kvac85yzfhgv8fx3tgqnvn7b`
2. Считать доказанным только одно:
   - tool-layer patch сам по себе не решает duplicate close без регрессии naturalness
3. Следующий цикл по финализации делать уже отдельно от line-check / stage-tag проблемы.
