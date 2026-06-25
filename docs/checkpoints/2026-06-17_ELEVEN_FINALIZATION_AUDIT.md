# Контрольная точка — 2026-06-17

## Обновление 2026-06-18: появился batch-аудит по серии разговоров, и он уже дал приоритетный backlog

### Сделано

- Добавлен batch-анализатор:
  - [scripts/analyze_eleven_conversation_batch.py](/home/max/n8n_ai_call_center/scripts/analyze_eleven_conversation_batch.py:1)
- Он прогоняет серию `conversation_poll_final.json` и собирает:
  - `issue_type_counts`
  - `primary_bottleneck_counts`
  - `top_recommendation_counts`
  - `timing_rollup`
- Сохранён артефакт по golden-confirm серии:
  - [.runtime/eleven_lab_golden_confirm_2026-06-17/batch_audit_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_golden_confirm_2026-06-17/batch_audit_summary.json:1)

### Что показал batch-аудит

- По серии из `5` разговоров главные repeating issues сейчас такие:
  - `long_user_to_agent_gap = 18`
  - `duplicate_close_before_end_call = 7`
  - `placeholder_conversation_id_in_tool_call = 6`
  - `final_close_spoken_before_call_log = 5`
  - `line_check_after_meaningful_post_opener_reply = 4`
  - `normal_assistant_speech_after_call_log = 4`
- По bottleneck-слою картина ещё яснее:
  - `turn_taking_or_dialogue_flow = 15`
  - `mixed_or_small_gap = 3`
  - `tool_path = 2`
  - `llm_generation = 1`
- Это уже очень сильный сигнал:
  - проблема в первую очередь не в raw модели и не в raw voice speed,
  - а в flow/sequencing.

### Главный backlog по batch-статистике

1. `focus_turn_taking`
2. `single_close_only`
3. `fix_tool_identity_binding`
4. `no_normal_speech_after_call_log`
5. `remove_late_line_checks`

### Что делать дальше

1. Следующий live цикл после снятия квоты вести уже по этому backlog, а не по разрозненным ощущениям.
2. Batch-аудит повторять после заметной правки prompt/flow, чтобы видеть, реально ли уходит топ проблем.
3. Если после правок `turn_taking_or_dialogue_flow` перестанет доминировать, тогда уже возвращаться к более тонкому voice/LLM polishing.

### Более широкий lab-срез

- Дополнительно снят summary по всем доступным `.runtime/eleven_lab_*` разговорам:
  - [.runtime/eleven_all_lab_batch_summary_2026-06-18.json](/home/max/n8n_ai_call_center/.runtime/eleven_all_lab_batch_summary_2026-06-18.json:1)
- Там уже:
  - `conversations_analyzed = 49`
  - `long_user_to_agent_gap = 208`
  - `normal_assistant_speech_after_call_log = 45`
  - `duplicate_close_before_end_call = 41`
  - `line_check_after_meaningful_post_opener_reply = 38`
  - `turn_taking_or_dialogue_flow = 185`
  - `tool_path = 16`
  - `llm_generation = 6`
- То есть даже на более широкой серии проблема всё равно остаётся flow-first.

## Обновление 2026-06-18: auditor теперь считает реальные паузы и разделяет задержку модели от задержки диалога

### Сделано

- Усилен локальный analyzer:
  - [scripts/analyze_eleven_conversation.py](/home/max/n8n_ai_call_center/scripts/analyze_eleven_conversation.py:1)
- Теперь он считает не только structural issues, но и timing-layer:
  - `first_user_to_agent_gap_secs`
  - `user_to_agent_gap_stats_secs`
  - `known_path_stats_secs`
  - `unexplained_overhead_stats_secs`
  - `llm_ttfb_stats_secs`
  - `llm_ttf_sentence_stats_secs`
  - `llm_last_sentence_stats_secs`
  - `tts_ttfb_stats_secs`
- Добавлены новые issue types:
  - `long_user_to_agent_gap`
  - `consecutive_agent_speech_without_user_reply`
  - `repeated_line_check_self_talk`
  - `machine_transfer_phrase_reached_agent_dialogue`
- Добавлена и автоматическая классификация primary bottleneck по каждому gap:
  - `turn_taking_or_dialogue_flow`
  - `tool_path`
  - `llm_generation`
  - `tts_start`
  - `mixed_known_path_and_flow`
  - `mixed_or_small_gap`
- Добавлен и слой автоматических рекомендаций:
  - analyzer теперь пишет `recommendations`
  - wrapper печатает `top_recommendations`
- Усилен и wrapper:
  - [scripts/run_eleven_selftest_audit.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_selftest_audit.sh:1)
- Теперь его короткий summary сразу печатает:
  - порог long-gap;
  - первый gap;
  - aggregate gap stats;
  - `llm_ttfb`;
  - `tts_ttfb`.

### Что проверили

- На старом opener-кейсе:
  - [.runtime/single_call_2026-06-06_row_8_opener_or_conv_check/conv_2701ktdzmjz7fxqrmfczhea65r56.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-06_row_8_opener_or_conv_check/conv_2701ktdzmjz7fxqrmfczhea65r56.json:1)
  analyzer теперь прямо показывает:
  - `first_user_to_agent_gap_secs = 4.0`
  - при этом сам стек генерации был заметно быстрее:
    - `llm_ttfb ≈ 0.476s`
    - `tts_ttfb ≈ 0.351s`
- На более длинном lab-разговоре:
  - [.runtime/eleven_lab_mid_dialogue_reassurance_trim_2026-06-17/call_01_verify/conversation_poll_final.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_mid_dialogue_reassurance_trim_2026-06-17/call_01_verify/conversation_poll_final.json:1)
  analyzer уже показывает полезную operational картину:
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
- Тот же analyzer теперь сразу предлагает верхние инженерные ходы:
  - `focus_turn_taking`
  - `remove_late_line_checks`
  - `single_close_only`
  - затем уже:
    - `focus_tool_path`
    - `no_normal_speech_after_call_log`
- Это важно, потому что теперь видно:
  - где реально медлит модель/TTS;
  - а где уже медлит сам dialogue-flow / turn-taking / финализация.
- Особенно полезен финальный close-кейс:
  - там `intermediate_tool_names = ["call_log"]`
  - и большая часть gap уже объясняется известным путём:
    - silent `call_log`
    - webhook latency
    - затем spoken close.
- А вот почти все средние business-turn в этом конкретном разговоре classifier уже относит к:
  - `turn_taking_or_dialogue_flow`
  а не к `llm_generation`.
- Это удобно тем, что следующий цикл уже можно строить не вручную по ощущениям, а по `top_recommendations` из audit JSON.
- В ранних и средних бизнес-turn это не так:
  - known path там маленький,
  - а основной хвост остаётся именно unexplained overhead.

### На чем остановились

- Теперь offline audit умеет отвечать не только на вопрос:
  - “был ли duplicate close?”
  но и на вопрос:
  - “это длинная пауза из-за модели или из-за логики разговора?”
- Это особенно полезно сейчас, пока live self-test упирается во внешнюю квоту Eleven.

### Что делать дальше

1. После восстановления квоты на каждом коротком self-test обязательно сохранять:
   - `finalization_audit.json`
2. Сравнивать не только issue types, но и:
   - `first_user_to_agent_gap_secs`
   - `user_to_agent_gap_stats_secs.max`
   - `llm_ttfb_stats_secs.avg`
   - `tts_ttfb_stats_secs.avg`
3. Если `llm/tts` остаются быстрыми, а gap всё равно длинный, следующий fix искать уже не в модели, а в:
   - turn-taking;
   - rescue logic;
   - финализационных хвостах;
   - лишних tool-path шагах.

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
