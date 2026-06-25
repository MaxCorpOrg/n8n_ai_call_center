# Контрольная точка — 2026-06-18

## Обновление `2026-06-18 15:55 MSK`: quota guard теперь жёстко останавливает цикл до звонка

### Сделано

- Усилены:
  - [scripts/report_eleven_quota_preflight.sh](/home/max/n8n_ai_call_center/scripts/report_eleven_quota_preflight.sh:1)
  - [scripts/report_eleven_live_readiness.sh](/home/max/n8n_ai_call_center/scripts/report_eleven_live_readiness.sh:1)
  - [scripts/run_eleven_live_cycle.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_live_cycle.sh:1)
- Теперь они явно показывают:
  - что последний conversation сам по себе уже quota-fail;
  - что `call_attempt_recommendation = do_not_call_until_quota_is_restored`;
  - что `calls_should_be_blocked_now = true`.

### Подтверждение

- Свежий preflight:
  - [.runtime/eleven_quota_preflight_2026-06-18_now_guard/eleven_quota_preflight_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_quota_preflight_2026-06-18_now_guard/eleven_quota_preflight_summary.json:1)
  показывает последний quota-hit:
  - `conv_1201kvdae8fxf779k0deagwst8b6`
  - `termination_reason = This request exceeds your quota limit.`
  - `start_time_utc = 2026-06-18T12:14:23Z`
- Свежий readiness:
  - [.runtime/eleven_live_readiness_2026-06-18_guard/live_readiness_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_live_readiness_2026-06-18_guard/live_readiness_summary.json:1)
  подтверждает:
  - route жив;
  - stack жив;
  - но `calls_should_be_blocked_now = true`.
- Свежий guard-run:
  - [.runtime/eleven_live_cycle_quota_guard_2026-06-18/live_cycle_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_live_cycle_quota_guard_2026-06-18/live_cycle_summary.json:1)
  подтверждает:
  - `action = stopped_before_call`
  - `reason = quota_pressure_guard`

### Практический смысл

- Теперь новый агент или оператор не должен путать это состояние с broken webhook или broken prompt.
- Live-контур не “сломался”; он сознательно должен стоять, пока не восстановят квоту Eleven.

## Обновление `2026-06-18 16:02 MSK`: batch-аудит закрепил приоритеты следующего цикла

### Сделано

- Добавлен batch-анализатор:
  - [scripts/analyze_eleven_conversation_batch.py](/home/max/n8n_ai_call_center/scripts/analyze_eleven_conversation_batch.py:1)
- На серии `golden_confirm` уже собран summary:
  - [.runtime/eleven_lab_golden_confirm_2026-06-17/batch_audit_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_golden_confirm_2026-06-17/batch_audit_summary.json:1)

### Что он показал

- `conversations_analyzed = 5`
- top issue counts:
  - `long_user_to_agent_gap = 18`
  - `duplicate_close_before_end_call = 7`
  - `placeholder_conversation_id_in_tool_call = 6`
  - `final_close_spoken_before_call_log = 5`
- top bottleneck counts:
  - `turn_taking_or_dialogue_flow = 15`
  - `mixed_or_small_gap = 3`
  - `tool_path = 2`
  - `llm_generation = 1`
- timing rollup:
  - `gap_avg_of_avgs_secs = 7.84`
  - `known_path_avg_of_avgs_secs = 1.57`
  - `unexplained_overhead_avg_of_avgs_secs = 6.27`

### Что делать дальше

1. Считать доказанным, что следующий цикл после снятия квоты должен идти сначала в:
   - `focus_turn_taking`
   - `single_close_only`
   - `fix_tool_identity_binding`
   - `no_normal_speech_after_call_log`
   - `remove_late_line_checks`
2. Не тратить первый следующий live цикл на косметическую смену модели/голоса, пока это не перестанет доминировать в batch-аудите.

### Более широкий lab-срез

- Дополнительно снят общий summary:
  - [.runtime/eleven_all_lab_batch_summary_2026-06-18.json](/home/max/n8n_ai_call_center/.runtime/eleven_all_lab_batch_summary_2026-06-18.json:1)
- По `49` lab-разговорам там уже видно:
  - `turn_taking_or_dialogue_flow = 185`
  - `tool_path = 16`
  - `llm_generation = 6`
- Значит даже на широком наборе следующий живой цикл нельзя честно начинать с “поменяем модель и голос”.

## Обновление `2026-06-18 15:44 MSK`: offline-аудит задержек усилен, следующий live цикл можно мерить точнее

### Сделано

- Усилен локальный разборщик разговоров:
  - [scripts/analyze_eleven_conversation.py](/home/max/n8n_ai_call_center/scripts/analyze_eleven_conversation.py:1)
- Теперь он меряет не только хвосты финализации, но и timing-layer:
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
- Добавлена и автоматическая классификация primary bottleneck по каждому gap.
- Добавлен и recommendation-layer поверх audit JSON.
- Усилен и wrapper:
  - [scripts/run_eleven_selftest_audit.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_selftest_audit.sh:1)
  - теперь короткий summary сразу печатает timing-summary без ручного `jq`.
- Уже получены полезные офлайн-факты:
  - opener-кейс:
    - [.runtime/single_call_2026-06-06_row_8_opener_or_conv_check/conv_2701ktdzmjz7fxqrmfczhea65r56.json](/home/max/n8n_ai_call_center/.runtime/single_call_2026-06-06_row_8_opener_or_conv_check/conv_2701ktdzmjz7fxqrmfczhea65r56.json:1)
    показывает:
    - `first_user_to_agent_gap_secs = 4.0`
    - но raw stack там быстрее:
      - `llm_ttfb ≈ 0.476s`
      - `tts_ttfb ≈ 0.351s`
  - длинный lab-кейс:
    - [.runtime/eleven_lab_mid_dialogue_reassurance_trim_2026-06-17/call_01_verify/conversation_poll_final.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_mid_dialogue_reassurance_trim_2026-06-17/call_01_verify/conversation_poll_final.json:1)
    показывает:
    - `user_to_agent_gap_stats_secs.max = 12.0`
    - `user_to_agent_gap_stats_secs.avg = 6.5`
    - `known_path_stats_secs.avg = 1.818`
    - `unexplained_overhead_stats_secs.avg = 4.682`
    - `unexplained_overhead_stats_secs.max = 10.907`
    - `primary_bottleneck_counts`:
      - `turn_taking_or_dialogue_flow = 5`
      - `tool_path = 1`
    - при среднем:
      - `llm_ttfb ≈ 0.809s`
      - `tts_ttfb ≈ 0.342s`
- top recommendations на этом кейсе уже выходят автоматически:
  - `focus_turn_taking`
  - `remove_late_line_checks`
  - `single_close_only`
- На другом audit-only кейсе wrapper тоже уже печатает короткий приоритетный список.
- На другом audit-only self-test:
  - `.runtime/eleven_lab_golden_confirm_2026-06-17/call_02_confirm/finalization_audit.json`
  summary уже показывает:
  - `known_path_stats_secs.avg = 1.288`
  - `unexplained_overhead_stats_secs.avg = 5.312`
  - `unexplained_overhead_stats_secs.max = 12.502`

### На чем остановились

- Теперь даже при внешнем quota-blocker у нас есть более точный offline-инструмент для следующего цикла.
- Это означает:
  - если после снятия лимита user-facing пауза снова будет длинной,
    мы сможем доказать, это:
    - медленный LLM/TTS;
    - или лишняя логика turn-taking / финализации / tool-path.

### Что делать дальше

1. После восстановления квоты первым коротким self-test сразу сохранять:
   - `finalization_audit.json`
2. Сравнивать:
   - `first_user_to_agent_gap_secs`
   - `user_to_agent_gap_stats_secs.max`
   - `llm_ttfb_stats_secs.avg`
   - `tts_ttfb_stats_secs.avg`
3. Если raw `llm/tts` быстрые, а gap всё равно длинный, следующий fix делать уже в:
   - turn-taking;
   - rescue logic;
   - finalization sequencing;
   - лишних tool transitions.

## Обновление `2026-06-18 15:27 MSK`: текущая ветка агента перепроверена, route жив, blocker всё ещё квота Eleven

### Сделано

- Повторно снят свежий snapshot текущей ветки агента через новый helper:
  - [scripts/fetch_eleven_agent_snapshot_via_server_env.sh](/home/max/n8n_ai_call_center/scripts/fetch_eleven_agent_snapshot_via_server_env.sh:1)
- Актуальный артефакт:
  - [.runtime/eleven_current_branch_snapshot_2026-06-18_now/summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_current_branch_snapshot_2026-06-18_now/summary.json:1)
- По нему сейчас подтверждено:
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
- Обновлён и синхронизирован локальный checker:
  - [scripts/check_eleven_prompt_invariants.py](/home/max/n8n_ai_call_center/scripts/check_eleven_prompt_invariants.py:1)
- Теперь он проверяет текущую живую норму:
  - `soft_timeout = 1.9`
  - актуальную формулировку soft-timeout prompt:
    - `only after the exact opener has already finished`
- Свежая проверка опубликованного branch snapshot уже зелёная:
  - [.runtime/eleven_current_branch_snapshot_2026-06-18_now/invariants.json](/home/max/n8n_ai_call_center/.runtime/eleven_current_branch_snapshot_2026-06-18_now/invariants.json:1)
  - итог:
    - `43/43 ok`
    - `checks_failed = 0`
- Параллельно повторно снят readiness:
  - [.runtime/eleven_live_readiness_2026-06-18_now/live_readiness_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_live_readiness_2026-06-18_now/live_readiness_summary.json:1)
  и он снова показывает:
  - `public_health_ok = true`
  - `local_stack_running = true`
  - `workflow_matches_state = true`
  - `alternate_named_eleven_credential_detected = false`
  - `quota_fail_count = 13`
  - `overall_diagnosis = quota_blocker_active`

### На чем остановились

- Сейчас уже подтверждены сразу две независимые вещи:
  1. инфраструктура жива:
     - local relay;
     - public tunnel;
     - live workflow URL;
     - detached launcher;
  2. текущая ветка агента тоже в порядке по своему prompt-state:
     - exact opener;
     - hard-stop по `абонент`;
     - strict silence;
     - soft-timeout/filler слой;
     - price-anchor guard.
- Значит текущий стоп не в route и не в drift prompt-конфигурации.
- Главный blocker на данный момент всё ещё внешний:
  - свежий readiness продолжает показывать quota-pressure на стороне Eleven.

### Что делать дальше

1. Не запускать новые live self-test как будто проблема в prompt, пока не снят quota blocker.
2. Первый тест после восстановления лимита делать коротким и только через:
  - `scripts/run_eleven_branch_selftest.sh`
  где `local_relay` уже стоит первым transport.
3. Если понадобится снова быстро доказать, что опубликованная ветка не “уплыла”, использовать связку:
  - `fetch_eleven_agent_snapshot_via_server_env.sh`
  - `check_eleven_prompt_invariants.py`
  вместо ручного чтения длинного prompt JSON.

## Обновление `2026-06-18 15:12 MSK`: live route снова зелёный, а квота подтверждена уже на прямом local relay

### Сделано

- Поднят живой local relay на:
  - `127.0.0.1:18787`
- Поднят живой `localhost.run` tunnel и live workflow снова переведён на новый URL:
  - `https://29d29137388b89.lhr.life/eleven/outbound-call`
- Новый readiness snapshot:
  - [.runtime/eleven_live_readiness_2026-06-18_live_sessions/live_readiness_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_live_readiness_2026-06-18_live_sessions/live_readiness_summary.json:1)
  уже показывает:
  - `workflow_matches_state = true`
  - `public_health_ok = true`
  - `overall_diagnosis = quota_blocker_active`
- То есть route, tunnel и live workflow сейчас между собой согласованы и снаружи реально отвечают.
- После этого снят принудительный self-test:
  - `.runtime/eleven_live_cycle_forced_2026-06-18_onecall/`
  и он показал важное разделение путей:
  - `relay_via_server` упирается в `cloudflare_challenge` / help-page;
  - но это уже не единственный сигнал.
- Затем выполнен прямой POST в локальный relay тем же `request.json`, и он вернул:
  - `success = true`
  - `message = Outbound call initiated`
  - `conversation_id = conv_9801kvda6zckfmp9jds52x52yp9w`
- После этого разговор отдельно дочитан через Eleven API, и там уже честно подтверждено:
  - `termination_reason = This request exceeds your quota limit.`
  - `error.code = 1002`
  - `status = failed`
- Значит текущий stop теперь подтверждён уже не только preflight-ом по истории, а и новым живым conversation после успешного outbound-init через local egress.
- Дополнительно исправлен self-test tooling:
  - [scripts/run_eleven_branch_selftest.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_branch_selftest.sh:1)
  теперь по умолчанию пробует transport order:
  - `local_relay -> relay_via_server -> relay -> webhook`
  вместо старого server-first порядка.

### На чем остановились

- Живой инфраструктурный маршрут снова в порядке:
  - local relay отвечает;
  - public tunnel отвечает;
  - live workflow смотрит в текущий tunnel;
  - state file совпадает с live workflow.
- Server-side relay path по-прежнему может ловить Cloudflare/help block.
- Но более важный и более близкий к реальному live path факт уже подтверждён:
  - local relay реально инициирует звонок,
  - а потом Eleven обрывает его именно по quota limit.
- То есть сейчас главный блокер снова внешний:
  - квота Eleven,
  а не `n8n`, не tunnel и не prompt агента.

### Что делать дальше

1. Не тратить новые отладочные циклы на tunnel и dispatcher, пока не снят quota blocker Eleven.
2. После восстановления лимита повторить один короткий self-test уже через `local_relay` как основной transport.
3. Только после этого возвращаться к:
  - паузам;
  - naturalness;
  - автоответчикам;
  - диалоговой логике.

## Обновление `2026-06-18 15:17 MSK`: detached launcher восстановлен, stack теперь поднимается без живых exec-сессий

### Сделано

- Подтверждено, что `selftest` после правки действительно идёт через:
  - `transport = local_relay`
  а не через старый server-first порядок.
- Подтверждённый run:
  - [.runtime/eleven_localrelay_first_2026-06-18/runtime_diagnosis.json](/home/max/n8n_ai_call_center/.runtime/eleven_localrelay_first_2026-06-18/runtime_diagnosis.json:1)
  показал:
  - `diagnosis = provider_quota_limit`
  - `conversation_id = conv_1201kvdae8fxf779k0deagwst8b6`
  - `version_matches_expected = true`
- Отдельно проверен новый practical fix для runtime stack:
  - [scripts/start_eleven_local_relay_stack.sh](/home/max/n8n_ai_call_center/scripts/start_eleven_local_relay_stack.sh:1)
  переведён с хрупкого `nohup`-подхода на устойчивый `setsid` запуск:
  - relay теперь стартует detached как отдельный `python3`;
  - tunnel теперь стартует detached как `script -qefc ...`, сохраняя PTY для `localhost.run`.
- После этого штатный launcher снова реально работает сам по себе:
  - `relay_pid = 238388`
  - `tunnel_pid = 238395`
  - listener держится на:
    - `127.0.0.1:18787`
  - public health отвечает `200 OK`
- Новый живой public URL после detached-launch:
  - `https://0087b8fcfbdd94.lhr.life/eleven/outbound-call`
- Подтверждённый readiness snapshot:
  - [.runtime/eleven_live_readiness_2026-06-18_detached_launcher/live_readiness_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_live_readiness_2026-06-18_detached_launcher/live_readiness_summary.json:1)
  уже показывает:
  - `workflow_matches_state = true`
  - `public_health_ok = true`
  - `quota_fail_count = 13`
  - `overall_diagnosis = quota_blocker_active`

### На чем остановились

- Теперь восстановлены обе части operational path:
  - live route работает;
  - launcher работает;
  - selftest говорит правду и идёт через `local_relay`.
- Главный живой блокер остался тем же:
  - Eleven создаёт разговор,
  - но завершает его по quota limit.

### Что делать дальше

1. Считать `n8n/tunnel/launcher` восстановленными и не тратить следующий цикл на эту инфраструктуру.
2. Следующий рабочий цикл начинать уже после восстановления лимита Eleven.
3. Первый тест после восстановления лимита снова запускать через:
  - `scripts/run_eleven_branch_selftest.sh`
  где `local_relay` уже стоит первым transport.

## Обновление `2026-06-18 15:20 MSK`: readiness-report теперь сам показывает inventory Eleven и живость локального stack

### Сделано

- Усилен:
  - [scripts/report_eleven_live_readiness.sh](/home/max/n8n_ai_call_center/scripts/report_eleven_live_readiness.sh:1)
- Теперь он собирает не только:
  - quota preflight;
  - state file;
  - public health;
  - live workflow URL;
  но ещё и:
  - inventory по `Eleven`-конфигу;
  - состояние локального runtime stack.
- Новый подтверждённый snapshot:
  - [.runtime/eleven_live_readiness_2026-06-18_inventory/live_readiness_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_live_readiness_2026-06-18_inventory/live_readiness_summary.json:1)
  показывает:
  - `public_health_ok = true`
  - `local_stack_running = true`
  - `workflow_matches_state = true`
  - `overall_diagnosis = quota_blocker_active`
- По `config_inventory` теперь прямо видно:
  - обе server env mirror-конфигурации содержат `ELEVENLABS_API_KEY` и `ELEVEN_OUTBOUND_RELAY_TOKEN`;
  - в `n8n` найден только один named Eleven credential:
    - `ElevenLabs XI API`
  - `alternate_named_eleven_credential_detected = false`
- Текущий живой tunnel на момент этого снимка:
  - `https://96e9645631456d.lhr.life/eleven/outbound-call`

### На чем остановились

- Теперь readiness-файл сам отвечает на три ключевых operational-вопроса:
  1. жив ли public route;
  2. жив ли локальный stack;
  3. найден ли альтернативный named Eleven credential.
- По текущим данным:
  - route жив;
  - stack жив;
  - запасного named credential не видно;
  - основной стоп по-прежнему квота Eleven.

### Что делать дальше

1. Если снова появится ощущение, что “сломался tunnel/dispatcher”, первым делом смотреть именно `live_readiness_summary.json`.
2. Не искать hidden second-key в `n8n`, пока не появится новый источник фактов: сейчас inventory этого не подтверждает.
3. Следующий полезный цикл начинать уже с восстановления лимита Eleven или с осознанного переключения на новый внешний credential/source, если он появится отдельно.

## Обновление `2026-06-18 12:48 MSK`: live webhook переведён на новый local tunnel, helper recovery добит до branch-history fallback

### Сделано

- Подтверждено, что прежний public tunnel:
  - `https://077b96f77ded60.lhr.life/eleven/outbound-call`
  устарел и live workflow снова смотрел в мёртвый URL.
- Локальный relay при этом жив и продолжает работать:
  - `http://127.0.0.1:18787/health`
- Новый рабочий public tunnel сейчас:
  - `https://fd7bdf984512a5.lhr.life/eleven/outbound-call`
- Для `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`:
  - `sHTbALayEZdy8Mzs`
  выполнен точечный live SQL-fix:
  - `workflow_entity.nodes`
  - активная `workflow_history.versionId = 0e21f126-db50-4500-b74f-3df4e9891d51`
  переведены со старого `077b...` URL на новый `fd7b...`.
- После этого live webhook снова реально доходит до local relay:
  - relay зафиксировал успешный upstream `200 Outbound call initiated`
  - пример:
    - `conv_6501kvd1t042ent9vznzex9g0y7t`
- Дополнительно добит helper:
  - [scripts/run_eleven_branch_selftest.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_branch_selftest.sh:1)
  теперь:
  - сначала пытается восстановить разговор через `user_id + branch_id`;
  - затем через recent branch history;
  - делает короткие retry, потому что Eleven показывает разговор в списке не мгновенно.
- Это уже подтверждено новым self-test:
  - `.runtime/eleven_local_tunnel_cutover_2026-06-18_resume/call_07_webhook_tunnel_branch_retry/`
  - helper сам восстановил:
    - `conversation_id = conv_9501kvd22c3hfrn9nqry1cg6t8sc`
    - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
    - `version_id = agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
    - `version_matches_expected = true`

### На чем остановились

- Сетевой обход через local relay + public tunnel снова рабочий.
- Live webhook снова умеет доходить до Eleven через этот обход.
- Self-test helper больше не слепнет на пустом webhook body.
- Новый прогон:
  - `.runtime/eleven_local_tunnel_cutover_2026-06-18_resume/call_08_quota_surface/`
  уже подтверждает это end-to-end:
  - helper сам восстановил `conv_7901kvd29vy1fxq835szb2wvj89f`;
  - `runtime_diagnosis.json` теперь явно пишет:
    - `diagnosis = provider_quota_limit`
    - `note = This request exceeds your quota limit.`
- Но текущий runtime-финиш по-прежнему нестабилен на стороне Eleven:
  - list API уже прямо показывает quota-hit:
    - `conv_1601kvd1wrdhf89beweq56y0v3pq`
    - `conv_5301kvd1zyb2emgtk2p7g5jbezhj`
    - `conv_7901kvd29vy1fxq835szb2wvj89f`
    - `conv_9501kvd22c3hfrn9nqry1cg6t8sc`
    завершились как:
    - `termination_reason = This request exceeds your quota limit.`
  - часть разговоров создаётся и видна в branch/version, но финальная карточка разговора остаётся обрезанной (`status=failed`, без полной telephony metadata).
- То есть текущий блок уже не в tunnel cutover и не в recovery логике.

### Что делать дальше

1. Держать в уме, что текущий live URL больше не `077b...`, а:
   - `https://fd7bdf984512a5.lhr.life/eleven/outbound-call`
2. Если tunnel снова переподнимется и сменит домен, первым делом обновлять этот URL в:
   - `workflow_entity`
   - active `workflow_history`
3. Следующий узкий цикл вести уже вокруг финального состояния conversation в Eleven:
   - почему после `Outbound call initiated` часть разговоров приходит как `failed`;
   - где именно обрезается telephony metadata;
   - остается ли это квотой, provider policy или post-init runtime noise.

## Обновление `2026-06-18 12:57 MSK`: добавлен quota preflight перед self-test

### Сделано

- Добавлен новый helper:
  - [scripts/report_eleven_quota_preflight.sh](/home/max/n8n_ai_call_center/scripts/report_eleven_quota_preflight.sh:1)
- Он без звонка снимает два слоя диагностики:
  - raw snapshot:
    - `GET /v1/user/subscription`
  - recent branch history:
    - `GET /v1/convai/conversations?branch_id=...`
- И собирает короткую итоговую сводку:
  - `eleven_quota_preflight_summary.json`
- Отдельно выяснено важное ограничение live API key:
  - subscription endpoint отвечает:
    - `missing_permissions`
    - `The API key you used is missing the permission user_read`
  - то есть прямой subscription snapshot для этого ключа частично закрыт правами.
- Несмотря на это, helper всё равно даёт полезный сигнал через recent branch history.
- Подтверждённый standalone-артефакт:
  - [.runtime/eleven_quota_preflight_2026-06-18/eleven_quota_preflight_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_quota_preflight_2026-06-18/eleven_quota_preflight_summary.json:1)
  - в нём уже видно:
    - `diagnosis = provider_quota_limit_observed_recently`
    - `quota_fail_count = 10`
    - warning про отсутствие `user_read`
- Этот preflight уже подключён внутрь:
  - [scripts/run_eleven_branch_selftest.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_branch_selftest.sh:1)
  - теперь каждый новый self-test кладёт в свой run-dir подпапку:
    - `preflight/`
- Подтверждённый интеграционный прогон:
  - `.runtime/eleven_local_tunnel_cutover_2026-06-18_resume/call_09_preflight_integration/`
  - внутри уже есть:
    - `preflight/eleven_quota_preflight_summary.json`
    - `runtime_diagnosis.json`
  - причём оба артефакта согласованы:
    - preflight:
      - `provider_quota_limit_observed_recently`
    - post-call:
      - `provider_quota_limit`

### На чем остановились

- Теперь перед каждым live self-test есть отдельный early signal:
  - если ветка уже засыпана quota-fail, мы видим это до звонка.
- Это не устраняет сам quota limit, но перестаёт маскировать проблему под webhook/agent/runtime regression.

### Что делать дальше

1. Перед следующими живыми прогонами первым делом смотреть:
   - `preflight/eleven_quota_preflight_summary.json`
2. Если там уже:
   - `provider_quota_limit_observed_recently`
   не тратить цикл на agent-prompt diagnosis до восстановления лимита.
3. После восстановления квоты первым же коротким self-test проверить:
   - что preflight перестал предупреждать о quota-fail;
   - и что звонок доходит до реального разговорного runtime.

## Обновление `2026-06-18 13:04 MSK`: live tunnel sync доведён до server-postgres режима

### Сделано

- Старый helper:
  - [scripts/localhost_run_tunnel_sync.py](/home/max/n8n_ai_call_center/scripts/localhost_run_tunnel_sync.py:1)
  существовал, но был привязан к старому workflow id и опирался на patch только через n8n API.
- Это было хрупко для нашего реального live-кейса, потому что исторически у нас ломался не только `workflow_entity`, но и active snapshot в `workflow_history`.
- Поэтому helper переписан под текущий live-контур:
  - default workflow:
    - `sHTbALayEZdy8Mzs`
  - target node:
    - `Eleven | Outbound HTTP`
  - mode:
    - `server_postgres`
- Теперь при появлении нового `localhost.run` домена helper:
  1. поднимает tunnel;
  2. через `ssh` идёт на `ai-core-prod-147`;
  3. берёт DB credentials из live `n8n` container;
  4. патчит URL сразу в:
     - `workflow_entity`
     - active `workflow_history`
  5. сохраняет локальный state file:
     - `/home/max/.config/lipolong-eleven-relay-state.json`
- Важное отличие:
  - helper больше не цепляется по ошибке к `postgrest` / `call_center`;
  - он теперь целится именно в:
    - `n8n-server-postgres-1`
    - database `n8n_prod`
    - user `n8n`
- Проверка уже выполнена безопасным no-op патчем на текущий URL:
  - `https://fd7bdf984512a5.lhr.life/eleven/outbound-call`
  - helper вернул:
    - `ok = true`
    - `active_version_id = 0e21f126-db50-4500-b74f-3df4e9891d51`
- Независимая readback-проверка из live Postgres после этого подтвердила тот же URL в `workflow_entity`.

### На чем остановились

- Теперь у live outbound path есть рабочий автоматизируемый helper на случай новой смены `localhost.run` домена.
- Это не решает quota limit Eleven, но сильно снижает риск повторно потерять live route просто из-за устаревшего tunnel URL.

### Что делать дальше

1. При следующем реальном re-open tunnel использовать уже этот helper, а не ручной SQL patch.
2. Если снова сменится public домен, первым делом проверить:
   - `/home/max/.config/lipolong-eleven-relay-state.json`
   - readback URL из live `workflow_entity`
3. После восстановления квоты Eleven этот helper использовать как штатную часть live tunnel cutover перед следующими self-tests.

## Обновление `2026-06-18 13:12 MSK`: появился единый guard-cycle для live self-test

### Сделано

- Добавлен верхнеуровневый orchestration-скрипт:
  - [scripts/run_eleven_live_cycle.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_live_cycle.sh:1)
- Он собирает в один controlled entrypoint:
  1. `report_eleven_quota_preflight.sh`
  2. repatch текущего relay URL из state file
  3. `run_eleven_branch_selftest.sh`
- Логика по умолчанию теперь безопасная:
  - если preflight уже показывает:
    - `provider_quota_limit_observed_recently`
  скрипт **не делает звонок**, а останавливается до вызова.
- Для этого он пишет:
  - `live_cycle_summary.json`
  со статусом:
    - `action = stopped_before_call`
    - `reason = quota_pressure_guard`
- Отдельно он всё равно успевает сделать полезные вещи до стопа:
  - снять `preflight_gate/*`
  - переподтвердить текущий relay URL через `state_repatch_result.json`
- Подтверждённый run:
  - [.runtime/eleven_live_cycle_guard_2026-06-18](/home/max/n8n_ai_call_center/.runtime/eleven_live_cycle_guard_2026-06-18:1)
  - там уже лежат:
    - `live_cycle_summary.json`
    - `preflight_gate/eleven_quota_preflight_summary.json`
    - `state_repatch_result.json`
  - и нет следов реального selftest-call, потому что guard остановил цикл до звонка.

### На чем остановились

- Теперь у нас уже есть не просто набор отдельных helper-ов, а один безопасный вход в live self-test цикл.
- В текущем состоянии он правильно защищает базу и лимиты:
  - при свежем quota pressure звонок не совершается.

### Что делать дальше

1. После восстановления лимита Eleven использовать уже не голый `run_eleven_branch_selftest.sh`, а:
   - `run_eleven_live_cycle.sh`
2. В обычном режиме держать `quota_pressure_guard` включённым.
3. Только для осознанного принудительного прогона использовать:
   - `--allow-quota-pressure`

## Обновление `2026-06-18 14:56 MSK`: readiness-report теперь показывает не только квоту, но и смерть public tunnel

### Сделано

- Добавлен ещё один operational helper:
  - [scripts/report_eleven_live_readiness.sh](/home/max/n8n_ai_call_center/scripts/report_eleven_live_readiness.sh:1)
- Он собирает в один отчёт:
  - quota preflight;
  - state file последнего `localhost.run` tunnel;
  - health текущего public relay URL;
  - readback URL из live workflow `sHTbALayEZdy8Mzs`.
- Это особенно полезно после того, как временные процессы tunnel/relay уже исчезли из runtime:
  - старые process ids больше не живы;
  - значит нам нужен был не memory-based status, а реальный readiness snapshot.
- Подтверждённый артефакт:
  - [.runtime/eleven_live_readiness_2026-06-18/live_readiness_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_live_readiness_2026-06-18/live_readiness_summary.json:1)
- Текущее состояние по этому отчёту:
  - `quota_preflight.diagnosis = provider_quota_limit_observed_recently`
  - `quota_fail_count = 11`
  - `live_workflow.current_url = https://fd7bdf984512a5.lhr.life/eleven/outbound-call`
  - `workflow_matches_state = true`
  - но `public_relay_health.http_code = 503`
  - и body:
    - `<h1>no tunnel here :(</h1>`
- Практический вывод:
  - live workflow всё ещё смотрит в последний сохранённый tunnel URL;
  - state file тоже с ним согласован;
  - но сам public tunnel уже умер;
  - при этом до нового звонка всё равно нельзя идти ещё и из-за quota blocker.

### На чем остановились

- Контур диагностически уже “в порядке”:
  - мы видим quota pressure;
  - видим состояние state file;
  - видим текущий URL в live workflow;
  - видим, что public tunnel мёртв.
- То есть следующая реальная работа уже не в поиске причины, а в восстановлении внешних условий.

### Что делать дальше

1. Сначала восстановить рабочую квоту Eleven.
2. Затем поднять новый `localhost.run` tunnel через:
   - `scripts/localhost_run_tunnel_sync.py`
3. После этого первым делом снова снять:
   - `scripts/report_eleven_live_readiness.sh`
4. И только если readiness-report даст:
   - живой public relay
   - и отсутствие quota guard
   запускать controlled call cycle.

## Обновление `2026-06-18 13:05 MSK`: маскировка dead air усилена, tool-sounds переведены с `typing` на `elevator3`

### Сделано

- По новой жалобе на "мертвую тишину" собран и опубликован отдельный lab-cycle:
  - версия:
    - `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
  - branch:
    - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- Для этого добавлен новый helper:
  - [scripts/prepare_eleven_gap_masking_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_gap_masking_variant.sh:1)
- В новой lab-версии зафиксировано:
  - `soft_timeout_config.timeout_seconds = 1.9`
  - `soft_timeout_config.message = "..."`
  - `use_llm_generated_message = true`
  - `randomize_fillers = false`
  - `max_soft_timeouts_per_generation = 1`
  - filler ограничен prompt override:
    - только после завершённого opener;
    - только как сверхкороткая thinking-вставка;
    - не line-check;
    - не support phrase;
    - не продажная фраза.
- Отдельно tool-level masking реально усилен на active tools:
  - `context_fetch`
    - `tool_1601km62rxpqegqr52m9gk9sftr3`
  - `call_log`
    - `tool_5701ktec2x6wfnj8t5b1rwhtw51p`
  - `send_sms_info`
    - `tool_1701km86jmcpek4rj2j1rbhxqtfr`
- Для этого расширен helper:
  - [scripts/patch_eleven_tool_call_sounds_via_server_env.sh](/home/max/n8n_ai_call_center/scripts/patch_eleven_tool_call_sounds_via_server_env.sh:1)
  - теперь он поддерживает настраиваемые:
    - `TOOL_CALL_SOUND`
    - `TOOL_CALL_SOUND_BEHAVIOR`
- Реальный tool-level patch уже выполнен:
  - `typing/always -> elevator3/always`
  для всех трёх active tools.
- Артефакты:
  - [.runtime/eleven_lab_gap_masking_2026-06-18](/home/max/n8n_ai_call_center/.runtime/eleven_lab_gap_masking_2026-06-18:1)
  - [.runtime/eleven_tool_sound_patch_2026-06-18_elevator3](/home/max/n8n_ai_call_center/.runtime/eleven_tool_sound_patch_2026-06-18_elevator3:1)

### На чем остановились

- Теперь предусмотрены оба слоя маскировки:
  - thinking pause:
    - через `soft_timeout`
  - tool pause:
    - через реальные tool sounds на `elevator3 / always`
- То есть проблема "мы же это предусматривали" теперь закрыта не только на уровне идеи и payload, но и на уровне реальных active tools.
- Живой слуховой self-test именно на `agtvrsn_9601...` в этом ходе ещё не снят.

### Что делать дальше

1. Снять один короткий self-test именно на:
   - `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
2. Отдельно проверить на слух:
   - исчезла ли голая пауза на `context_fetch`;
   - исчезла ли голая пауза на `send_sms_info`;
   - не стало ли `soft_timeout` слишком ранним и назойливым.
3. Если `elevator3` окажется слишком заметным, следующий узкий цикл делать не через rollback всей логики, а только заменой:
   - `elevator3 -> elevator1/2`

## Обновление `2026-06-18 12:26 UTC / 15:26 MSK`: текущий live-блокер подтверждён как страновое ограничение Eleven по серверной локации

### Сделано

- После публикации `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k` выполнены два runtime-прогона:
  - `.runtime/eleven_lab_gap_masking_2026-06-18/call_01_selftest/`
  - `.runtime/eleven_lab_gap_masking_2026-06-18/call_02_selftest_webhook/`
- Первый прогон через:
  - `relay_via_server`
  дал:
  - `relay_upstream_failed`
  - `The read operation timed out`
- Второй прогон через:
  - `webhook`
  дал уже явный provider ответ:
  - `status = sanctioned_country`
  - `message = This functionality is not available in your location.`
- Затем отдельно выполнен прямой probe с live-сервера `ai-core-prod-147` в Eleven endpoint:
  - `POST https://api.elevenlabs.io/v1/convai/sip-trunk/outbound-call`
- И он вернул точный HTTP-ответ:
  - `HTTP/2 302`
  - `location: https://help.elevenlabs.io/hc/en-us/articles/22497891312401-Do-you-restrict-access-to-the-service-and-platform-for-any-specific-countries-add`
- Это уже прямое доказательство, что текущий блок находится не в prompt, не в voice-настройках, не в n8n-ветке и не в самой логике агента, а в server-side доступности outbound-call по текущей серверной локации/IP.
- Под этот кейс усилена диагностика:
  - [scripts/eleven_outbound_relay_server.py](/home/max/n8n_ai_call_center/scripts/eleven_outbound_relay_server.py:1)
    теперь умеет распознавать redirect на help-статью Eleven и возвращать структурированный:
    - `status = sanctioned_country`
    - `error = provider_restricted_country`
  - [scripts/run_eleven_branch_selftest.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_branch_selftest.sh:1)
    теперь умеет классифицировать такой ответ как:
    - `reason = sanctioned_country`
    вместо немого общего фейла.

### На чем остановились

- Agent-side работа по тишине продвинута:
  - `soft_timeout + elevator3/always` уже опубликованы.
- Но живой звонок с этой версией сейчас не может быть честно подтверждён с текущего server path, потому что Eleven режет outbound-call по server-side location.
- Значит текущий практический стопор уже не разговорный, а инфраструктурный.

### Что делать дальше

1. Для реального следующего live-test нужен не новый prompt, а новый разрешённый outbound path:
   - другой сервер/IP;
   - или другой разрешённый relay location.
2. До смены outbound location не тратить циклы на новые voice/prompt-тонкости как на "основную причину".
3. После появления разрешённого outbound path первым же звонком проверять уже именно:
   - исчезновение dead air на `9601...`
   - а не снова перепроверять старую prompt-гипотезу.

## Обновление `2026-06-18 11:40 MSK`: conversation создаётся на masking-версии, но media так и не стартует

### Сделано

- После tool-level patch на active tools снят новый живой self-test:
  - `.runtime/eleven_toolmask_livecheck_2026-06-18/call_02_selftest/`
- Разговор реально создан в Eleven:
  - `conversation_id = conv_2101kvcxvfsrfyz92cr40t8nhfh2`
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - `version_id = agtvrsn_6801kvcx5jcvf6n88sd9yv86nx5v`
- То есть branch/version уже точно правильные, и masking-версия реально стартует как запись в Eleven.
- Но по итоговому poll за `180s` получилось:
  - `status = in-progress`
  - `has_audio = false`
  - `has_user_audio = false`
  - `has_response_audio = false`
  - `transcript_count = 0`
  - `call_duration_secs = 0`
- Дополнительно подтверждено через Eleven API:
  - `GET /v1/convai/conversations/:conversation_id/sip-messages`
  вернул:
  - `count = 0`
- Но отдельный запрос по самому phone number:
  - `GET /v1/convai/phone-numbers/phnum_8501khxz93vnfnnsvdjqn1g92yfs/sip-messages`
  показал свежие SIP-события:
  - `183 Session Progress`
  - `200 OK`
  - `BYE`
  - `ACK`
  по `TCP` через trunk `147.45.213.87`
- Это важная развилка:
  - conversation создаётся;
  - но как artifact самой conversation не появляются:
    - SIP trace;
    - audio;
    - transcript.
- Для этого же цикла helper усилен ещё раз:
  - [scripts/run_eleven_branch_selftest.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_branch_selftest.sh:1)
  - теперь он:
    - классифицирует Cloudflare/help page как `selftest_blocked`;
    - пишет runtime diagnosis:
      - `sip_pending_no_media`
- Артефакты:
  - `.runtime/eleven_toolmask_livecheck_2026-06-18/call_02_selftest/conversation_poll_final.json`
  - `.runtime/eleven_toolmask_livecheck_2026-06-18/call_02_selftest/runtime_diagnosis.json`
  - `.runtime/eleven_toolmask_livecheck_2026-06-18/call_02_selftest/sip_messages.json`

### На чем остановились

- Tool-level masking уже реально включён.
- Но слухом проверить его пока нельзя, потому что звонок не дошёл до стадии медиа.
- Текущий блок теперь точнее локализован:
  - не prompt;
  - не tool-level sound config;
  - не branch/version routing;
  - и не полный dead-state phone number;
  - а linkage между созданной conversation и её реальным media/SIP artifact.

### Что делать дальше

1. Следующий цикл переводить на уровень SIP/runtime.
2. Разбирать:
   - почему после создания `conversation_id` у conversation нет ни одного SIP message,
     хотя у phone number есть свежий `183/200/BYE`;
   - почему разговор зависает `in-progress` с `call_duration_secs = 0`.
3. Только после восстановления media-start снова проверять:
   - ушла ли пустая тишина;
   - исчез ли self-talk после молчания.

## Обновление `2026-06-18 12:05 MSK`: masking тишины добит на уровне реальных tools

### Сделано

- Подтверждено, что в lab-версии `agtvrsn_6801kvcx5jcvf6n88sd9yv86nx5v`
  настройка masking была добавлена в agent payload, но этого было недостаточно для фактического tool-level применения.
- Поэтому выполнен прямой patch через Eleven Tools API на реальные active tools текущей lab-ветки:
  - `context_fetch`:
    - `tool_1601km62rxpqegqr52m9gk9sftr3`
  - `call_log`:
    - `tool_5701ktec2x6wfnj8t5b1rwhtw51p`
  - `send_sms_info`:
    - `tool_1701km86jmcpek4rj2j1rbhxqtfr`
- На все три инструмента реально записано:
  - `tool_call_sound = typing`
  - `tool_call_sound_behavior = always`
- Для этого добавлен отдельный служебный helper:
  - [scripts/patch_eleven_tool_call_sounds_via_server_env.sh](/home/max/n8n_ai_call_center/scripts/patch_eleven_tool_call_sounds_via_server_env.sh:1)
- Backup и verify сохранены в:
  - [.runtime/eleven_tool_sound_patch_2026-06-18](/home/max/n8n_ai_call_center/.runtime/eleven_tool_sound_patch_2026-06-18:1)
- Проверка `before -> after` уже подтверждена:
  - `call_log`: `null/auto -> typing/always`
  - `send_sms_info`: `null/auto -> typing/always`
  - `context_fetch`: уже стал `typing/always`, повторный patch оставил состояние без изменений.

### На чем остановились

- Теперь masking тишины для tool execution уже реально включён на active tools, а не только "описан" в payload.
- Следующий блок проверки уже не API-конфигурационный, а живой слуховой:
  - слышно ли `typing` на линии;
  - ушло ли ощущение голой тишины между ответами.
- Отдельно помнить:
  - этот шаг закрывает именно tool-паузы;
  - для чистой LLM-паузы всё ещё работает отдельная линия через `soft_timeout`.

### Что делать дальше

1. Снять один короткий self-test на текущем repaired tool-level masking.
2. На слух и по transcript отделить:
   - tool-pause;
   - thinking pause;
   - terminal-finalization хвост.
3. Если "мертвая" пауза останется вне tool execution, следующий узкий цикл делать уже через:
   - `soft_timeout`;
   - turn-taking;
   - prompt trim перед tool вызовом.

## Обновление `2026-06-18 11:35 MSK`: пойман и локализован terminal-finalization регресс, начат отдельный latency-masking цикл

### Сделано

- После repaired webhook-path снят реальный speech-test:
  - `conv_0601kvcwg3nyf7hstxwyksj0nxvn`
  - branch:
    - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - version:
    - `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
- По transcript подтверждено уже не инфраструктурное, а разговорное нарушение:
  - агент сказал нормальный spoken close слишком рано;
  - затем на `...` и молчание снова открывал диалог;
  - после `call_log` снова говорил как обычный собеседник;
  - `end_call` вообще не был вызван.
- Для этого усилен локальный audit:
  - [scripts/analyze_eleven_conversation.py](/home/max/n8n_ai_call_center/scripts/analyze_eleven_conversation.py:1)
- Новый audit теперь ловит:
  - `normal_assistant_speech_after_call_log`
  - `final_close_spoken_before_call_log`
  - `call_log_without_end_call`
  - `helpdesk_tail_in_outbound_close`
- На том же разговоре это уже подтверждено автоматически.
- Затем опубликован узкий lab-only patch:
  - terminal finalization gate
  - версия:
    - `agtvrsn_9101kvcwr2keeet9ye7q33e7qg2x`
- Повторный звонок:
  - `conv_9601kvcwrnv2e5yrdn3h0w7y7zs8`
  показал частичный прогресс:
  - `end_call` уже реально вызвался;
  - бесконечный self-talk после `call_log` ушёл;
  - но остались:
    - duplicate close;
    - spoken close до `call_log`;
    - placeholder `conv_abcdef...` в drafted `call_log.params_as_json`.
- Под это выпущен ещё один узкий patch:
  - terminal tool sequencing + binding
  - версия:
    - `agtvrsn_2201kvcwwby6f3r803sqkrawzqn0`
- Затем отдельным циклом учтена жалоба на пустую тишину между ответами:
  - опубликована версия:
    - `agtvrsn_6801kvcx5jcvf6n88sd9yv86nx5v`
  - что в ней изменено:
    - `soft_timeout_config.timeout_seconds = 2.4`
    - `tool_call_sound = typing`
    - `tool_call_sound_behavior = always`
    для:
      - `context_fetch`
      - `call_log`
      - `send_sms_info`
- Это соответствует текущей документации ElevenLabs:
  - `soft timeout` нужен для LLM-thinking delay;
  - `tool call sounds` нужны для маскировки тишины во время tool execution;
  - для slower tool paths допустим режим `Always play`.

### На чем остановились

- Разговорный дефект уже хорошо локализован:
  - корень не только в silence-after-opener,
    а в terminal-finalization окне после отказа.
- По факту сейчас есть три последних lab-ступени:
  - `agtvrsn_9101...`
    - добавил `end_call`, убрал тяжёлый self-talk после `call_log`;
  - `agtvrsn_2201...`
    - добавил tool-sequencing и binding hardening;
  - `agtvrsn_6801...`
    - добавил masking пустой тишины через tool-call sounds + faster soft-timeout.
- Но последняя live-проверка `6801...` не завершилась верификацией из-за внешнего состояния outbound:
  - один запуск поймал Cloudflare `Just a moment...`;
  - следующий relay-path вернул:
    - `status = sanctioned_country`
- То есть на этом шаге блокер снова внешний:
  - не prompt;
  - не tool_call_sound config;
  - а нестабильный upstream/provider access.

### Что делать дальше

1. Следующий короткий test-call на версии:
   - `agtvrsn_6801kvcx5jcvf6n88sd9yv86nx5v`
   проводить через первый доступный non-blocked transport.
2. Снимать именно два типа доказательств:
   - transcript;
   - слышна ли теперь audio-mask маскировка на `call_log/send_sms_info`.
3. Если `duplicate close` останется и на `2201/6801`-линии, следующий узкий цикл делать уже не prompt-only, а разбирать:
   - почему модель всё ещё произносит close как normal assistant turn до `end_call`.
4. Новый analyzer теперь считать обязательным источником истины после каждого self-test.

## Обновление `2026-06-18 11:07 MSK`: live outbound branch-fix реально применён и webhook снова честно создаёт lab-разговор

### Сделано

- Для live workflow:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` (`sHTbALayEZdy8Mzs`)
  подтверждено, что одного `publish:workflow` было недостаточно:
  - `workflow_entity` обновлялся,
  - но live runtime продолжал отвечать по старому snapshot из `workflow_history`.
- Перед точечной правкой сняты backup-файлы:
  - `backups/2026-06-18_eleven_outbound_call_bridge_before_branch_fix_fresh.json`
  - `backups/2026-06-18_eleven_outbound_call_bridge_after_branch_fix.json`
- В live вручную применён узкий branch-fix:
  - в `workflow_entity` обновлены `nodes / connections / settings`;
  - затем создан новый published snapshot в `workflow_history`;
  - `workflow_entity.activeVersionId` переведён на новый snapshot:
    - `0e21f126-db50-4500-b74f-3df4e9891d51`
- После этого выполнен точечный рестарт только контейнера:
  - `n8n-server-n8n-1`
- Сразу после рестарта live validation снова отвечает штатно:
  - `POST https://www.n-8-n.site/webhook/eleven/outbound-call`
  - HTTP `200`
  - `action=validation_failed` для пустого `to_number`
- Затем выполнен branch-targeted webhook probe в lab:
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - expected `version_id = agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
- Теперь webhook уже вернул правильный top-level accepted response:
  - `success = true`
  - `conversation_id = conv_0801kvcw73eaeqf8t1pjy9p0y8kf`
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - `environment = production`
- По API Eleven дополнительно подтверждено, что разговор реально создан именно в lab:
  - conversation:
    - `conv_0801kvcw73eaeqf8t1pjy9p0y8kf`
  - branch:
    - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - version:
    - `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
- Артефакты этого цикла:
  - `.runtime/eleven_webhook_branch_fix_probe_2026-06-18_01/request.json`
  - `.runtime/eleven_webhook_branch_fix_probe_2026-06-18_01/conversation_details.json`
  - `.runtime/eleven_outbound_call_bridge_branch_fix_2026-06-18/apply_live.sql`
  - `.runtime/eleven_outbound_call_bridge_branch_fix_2026-06-18/publish_active_history.sql`
- Заодно подчищен служебный helper:
  - `scripts/run_eleven_branch_selftest.sh`
  - теперь при пустом теле ответа он сохраняет понятный JSON `selftest_failed`,
    а не падает вторичной ошибкой `sed: can't read outbound_response.json`.

### На чем остановились

- Главная structural-проблема webhook-path закрыта:
  - live `eleven/outbound-call` снова сохраняет `branch_id`;
  - webhook-path снова отдаёт top-level `success/conversation_id`;
  - lab self-test больше не уезжает в `Main` из-за потери branch-targeting.
- Strict-silence lab-версия теперь подтверждена уже по двум разным путям:
  - direct/relay path:
    - `conv_4601kvct8fx4f6qs8nfb17vke8gh`
  - repaired webhook path:
    - `conv_0801kvcw73eaeqf8t1pjy9p0y8kf`
- При этом остался отдельный живой продуктовый хвост:
  - нужно снова проверять именно разговорную часть на линии:
    - silence-after-opener;
    - duplicate close;
    - machine/no-human handling.
- В логах `n8n-server-n8n-1` отдельно виден старый шумящий маршрут:
  - `VOICE_INBOUND_AGENT (draft)` (`bfNbTwtyXNSFzMc2`)
  - он inactive (`active=false`) и без `activeVersionId`,
    поэтому входящие `mango/events/*` до сих пор пишут ошибки `Active version not found`.
  - Это уже отдельный inbound-хвост, не блокер для repaired outbound bridge.

### Что делать дальше

1. Следующий голосовой цикл снова вести маленько и предметно:
   - один controlled call на silence-after-opener;
   - затем разбор transcript/audit.
2. Отдельно проверить, остался ли на линии хвост:
   - `duplicate_close_before_end_call`
   на lab-версии:
   - `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
3. Не смешивать этот цикл с новым переписыванием outbound bridge:
   - bridge сейчас уже рабочий.
4. Отдельным техциклом решить, нужно ли оживлять старый inbound draft:
   - `VOICE_INBOUND_AGENT (draft)` (`bfNbTwtyXNSFzMc2`)
   если `mango/events/*` всё ещё нужны live-контуру.

## Обновление `2026-06-18 10:22 MSK`: live outbound webhook восстановлен

### Сделано

- На live-сервере `ai-core-prod-147` подтверждено, что маршрут:
  - `https://www.n-8-n.site/webhook/eleven/outbound-call`
  был привязан к workflow:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` (`sHTbALayEZdy8Mzs`)
  но этот workflow оставался без опубликованной active version.
- Перед правкой снят точечный backup workflow:
  - `backups/2026-06-18_eleven_outbound_call_bridge_before_publish.json`
- На live выполнена публикация текущей версии workflow:
  - `n8n publish:workflow --id=sHTbALayEZdy8Mzs`
- После этого webhook-probe перестал отдавать:
  - `404 Active version not found for workflow with id "sHTbALayEZdy8Mzs"`
  и начал отвечать штатным validation JSON.
- Контрольный probe после восстановления:
  - `POST https://www.n-8-n.site/webhook/eleven/outbound-call`
  - ответ:
    - HTTP `200`
    - `{"ok":false,"action":"validation_failed",...}`
  Это правильный признак: маршрут жив, код workflow исполняется, дальше остаётся проверять уже сам outbound path.
- Сразу после этого снят один контролируемый self-test:
  - [.runtime/eleven_restore_probe_2026-06-18_01](/home/max/n8n_ai_call_center/.runtime/eleven_restore_probe_2026-06-18_01:1)
- По нему подтверждено:
  - `conversation_id` не создался;
  - `relay_via_server` вернул HTML-страницу `Just a moment...`;
  - это уже не ошибка webhook-регистрации, а upstream-block на стороне доступа к Eleven/API help path.
- Затем отдельно подтверждено с самого relay-хоста `151.241.228.232`:
  - прямой `POST https://api.elevenlabs.io/v1/convai/sip-trunk/outbound-call` с неполным payload даёт нормальный JSON `422`;
  - прямой `POST` с полным lab payload на тот же номер смог создать разговор:
    - `conv_4601kvct8fx4f6qs8nfb17vke8gh`
    - branch:
      - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
    - version:
      - `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
- Это доказало, что:
  - relay-сервис жив;
  - ключ валиден;
  - lab strict-silence версия реально может стартовать на линии;
  - проблема не в полном dead-state всего outbound, а в плавающем upstream поведении.
- По `conv_4601...` уже снят audit:
  - единственный остаточный issue:
    - `duplicate_close_before_end_call`
- Дополнительно подтверждено, что helper fallback через `webhook` сейчас искажает lab-диагностику:
  - в цикле `restore_probe_02` через webhook реально стартовал другой разговор:
    - `conv_6301kvctagp5e3vbsynr9jjkchyf`
  - но он ушёл не в lab, а в боевой `Main`:
    - branch:
      - `agtbrch_7801kgybyg9nesrbv64y078pazq0`
    - version:
      - `agtvrsn_9001kv0k051efpr84vwwttz6kthj`
  - значит текущий webhook-path не сохраняет branch-targeting из self-test payload и не годится как честный fallback для lab-ветки.
- Под это усилен локальный self-test helper:
  - [scripts/run_eleven_branch_selftest.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_branch_selftest.sh:1)
  - что теперь добавлено:
    - recovery через официальный `List conversations` API Eleven по `user_id + branch_id + call_start_after_unix`;
    - поддержка не только raw relay-ответа, но и wrapped webhook-формата;
    - защитный запрет на автоматический `webhook` fallback для non-live branch, чтобы lab self-test не уезжал в `Main`.
- Подготовлен и локально проверен reproducible patch-generator для live workflow:
  - [scripts/prepare_eleven_outbound_call_bridge_branch_fix.py](/home/max/n8n_ai_call_center/scripts/prepare_eleven_outbound_call_bridge_branch_fix.py:1)
- Им уже собран готовый patched export:
  - [.runtime/eleven_outbound_call_bridge_branch_fix_2026-06-18/workflow_patched.json](/home/max/n8n_ai_call_center/.runtime/eleven_outbound_call_bridge_branch_fix_2026-06-18/workflow_patched.json:1)
- Смысл патча для `ELEVEN_OUTBOUND_CALL_BRIDGE`:
  - не терять `conversation_initiation_client_data.branch_id`;
  - не терять `conversation_initiation_client_data.environment`;
  - пробрасывать существующие nested `dynamic_variables`, а не собирать их заново с потерей контекста;
  - возвращать top-level `success=true` и `conversation_id` на accepted path.

### На чем остановились

- Главный live-блокер "маршрут вообще не существует" снят.
- Теперь проблема уже не в публикации webhook, а в следующем слое:
  - реальный outbound request;
  - relay path;
  - фактический старт разговора в ElevenLabs.
- Контрольный self-test после восстановления webhook не дал `conversation_id`, потому что upstream вернул HTML challenge/page вместо JSON API payload.
- Strict-silence patch по-прежнему опубликован в lab, но ещё не подтверждён живым звонком после восстановления webhook.
- Но теперь есть более точная формулировка:
  - lab strict-silence версия уже подтверждена живым разговором:
    - `conv_4601kvct8fx4f6qs8nfb17vke8gh`
  - а вот штатный helper-path всё ещё не считается стабильным из-за плавающего upstream `403/html challenge` и из-за webhook fallback в `Main`.

### Что делать дальше

1. Следующий цикл вести по двум фронтам отдельно:
   - плавающий upstream `403/html challenge` на relay;
   - структурный разрыв webhook fallback -> `Main`.
2. Для lab проверки использовать как source-of-truth:
   - direct relay / direct API path,
   - а не webhook fallback.
3. Отдельно решить, надо ли live workflow `ELEVEN_OUTBOUND_CALL_BRIDGE` учить сохранять:
   - `branch_id`
   - `environment`
   - nested dynamic variables
   чтобы webhook-path мог честно работать и для branch-targeted self-tests.
   - Для этого уже готов локальный patched export и patch-generator, то есть следующий mutating шаг можно делать не с нуля.
4. Следующий speech-fix цикл по самой lab-версии держать узко:
   - убрать `duplicate_close_before_end_call` на линии `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`.

## Тема

Naturalness lab: strict-silence patch уже опубликован, но живой runtime-test заблокирован внешним outbound-ограничением.

## Сделано

- Подтверждено, что lab-версия:
  - `agtvrsn_1301kvagt880eg88y6kynrmyxzvx`
  даёт регрессию именно на тишине после opener:
  - repeated `Алло?`
  - `Да? Чем могу помочь?`
  - предложения `SMS / callback` внутри silence-state
- Подготовлен и опубликован узкий patch поверх более здоровой базы:
  - база:
    - `agtvrsn_2101kvag7mw1fpgv6y64jp58qk7j`
  - опубликованная версия:
    - `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
- По опубликованной версии уже локально подтверждено:
  - strict silence block на месте
  - запрет `Да? Чем могу помочь?` на месте
  - запрет `SMS / callback / manager` в silence-state на месте
  - усиленные инварианты payload зелёные:
    - `43/43 ok`
  - артефакт:
    - `.runtime/eleven_lab_strict_silence_window_2026-06-17/apply_result/prompt_invariants_43.json`
- Обновлены основные handoff-документы:
  - `docs/knowledge_base/09_PROJECT_CHANGELOG_AND_STATE.md`
  - `документация_для_агента/02_ТЕКУЩЕЕ_LIVE_СОСТОЯНИЕ.md`
 - Усилен локальный verifier:
   - `scripts/check_eleven_prompt_invariants.py`
   теперь дополнительно страхует:
   - strict silence block;
   - запрет helpdesk-фраз в silence-state;
   - запрет repeated `Алло?`;
   - single finalization path;
   - short rescue micro-cut;
   - single spoken close через `end_call`;
   - soft-timeout filler config.

## На чем остановились

- Prompt/config уже опубликованы в lab и подтверждены по структуре.
- Но живой проверочный звонок пока не дал нормального transcript из-за внешнего состояния outbound:
  - `status = sanctioned_country`
  - `message = This functionality is not available in your location.`
- Параллельно виден отдельный инфраструктурный хвост:
  - direct relay timeout
  - webhook отвечает:
    - `Active version not found for workflow with id "sHTbALayEZdy8Mzs"`
- Значит сейчас нельзя честно утверждать, что silence-fix уже доказан в живом звонке.
- Дополнительно на `2026-06-18` это перепроверено свежими probe:
  - `POST https://www.n-8-n.site/webhook/eleven/outbound-call` сейчас реально возвращает:
    - `404 Active version not found for workflow with id "sHTbALayEZdy8Mzs"`
  - direct probe с локальной машины в:
    - `http://151.241.228.232:8787/health`
    уходит в timeout;
  - но тот же health probe с live-сервера `ai-core-prod-147` возвращает:
    - `{"ok": true, "service": "eleven_outbound_relay", ...}`
- Значит для lab self-test сейчас канонический путь старта звонка:
  - `relay_via_server`
  а не live webhook и не прямой relay с локальной машины.

## Что делать дальше

1. Как только outbound снова станет доступен, снять один короткий self-test на сценарий:
   - подняли трубку
   - после opener молчим
2. Подтвердить, что в разговоре больше нет:
   - repeated `Алло?`
   - `Да? Чем могу помочь?`
   - `SMS / callback` внутри silence-state
3. Отдельно проверить, не нужно ли перевязать webhook вместо inactive workflow:
   - `sHTbALayEZdy8Mzs`
4. До runtime-подтверждения не объявлять `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz` окончательной победной вершиной.
5. Для branch self-test использовать текущий дефолт:
   - `relay_via_server -> relay -> webhook`
