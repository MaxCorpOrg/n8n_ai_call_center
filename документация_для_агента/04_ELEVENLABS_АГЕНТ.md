# ElevenLabs агент

## Обновление 2026-07-09 13:48 MSK: lab fast-path `send_sms_and_log`, current head `9301...`

### Сделано
- Создан n8n lab workflow:
  - `ELEVEN_TOOL_SEND_SMS_AND_LOG_BRIDGE_LAB`
  - workflow ID: `LVYvGh5luQunORKh`
  - webhook: `https://www.n-8-n.site/webhook/eleven/tool/send-sms-and-log`
- Назначение:
  - заменить SMS-consent хвост `send_sms_info -> call_log` на один backend tool;
  - уменьшить мёртвую паузу после фразы клиента `да, отправьте SMS`.
- Smoke-test endpoint:
  - `dry_run=true`
  - `log_dry_run=true`
  - ответ `200 OK`
  - identity complete.
- Через официальный ElevenLabs Tools API создан global webhook tool:
  - `send_sms_and_log`
  - `tool_5701kx37g3qpf6caa4f09c9bfm8n`
- В lab branch добавлен `tool_id` нового tool:
  - current head: `agtvrsn_9301kx37gy6zft3te55dangks99m`
- Добавлен prompt guard:
  - никогда не произносить `call_log with`, `send_sms_and_log with`, JSON, `params_as_json`, `silent`, `skip_turn`.

### Проверки
- `conv_3401kx373nysfxzvf5qdx2nzmy2e` на `3001...`:
  - плохой результат;
  - agent произнёс `call_log with {...}`.
- `conv_5201kx37hp0heyjab4rgkvszgw2f` на `9301...`:
  - spoken tool text ушёл;
  - `call_log` и `end_call` прошли успешно;
  - но SMS-consent не было, поэтому `send_sms_and_log` ещё не проверен разговором.
- `conv_8901kx37myfdef39cqh2n53bqnpf`:
  - polling timeout;
  - transcript пустой;
  - не использовать для behavioral выводов.

### На чем остановились
- Current lab:
  - branch: `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - head: `agtvrsn_9301kx37gy6zft3te55dangks99m`
- Новый tool прикреплён и виден в response:
  - `send_sms_and_log`
- Боевой `Main` не трогался.

### Что делать дальше
1. Провести один self-test с явным SMS consent:
   - клиент: `да, отправьте SMS`;
   - ожидание: spoken ack -> `send_sms_and_log` -> one `end_call`.
2. Если проходит:
   - сравнить задержку с прежним SMS-tail `10-13s`.
3. Если не проходит:
   - не переносить в live;
   - откатываться на `4701...` / payload-class `6201...`.

## Обновление 2026-07-09 13:18 MSK: текущий lab head `4701...`

### Сделано
- Проверен `5701...`:
  - `conv_4201kx356xmveetawnn4zfjdxcwf`
  - opener был правильный;
  - SMS отправилась;
  - но `pre_tool_speech` на webhook-tool не дал spoken ack;
  - SMS/tool-tail около `10s`.
- Сверка с docs ElevenLabs:
  - `soft_timeout` можно использовать для словесного filler при долгой генерации;
  - default `-1`, recommended около `3.0s`;
  - `pre_tool_speech` documented как MCP/tool configuration override, поэтому для текущих webhook tools не считать это гарантированным решением.
- Проверен `1801...`:
  - `conv_9901kx35dfzrfz9vzw5z41gn1wpv`
  - плохой результат: первый `Нет, не интересно` сразу ушёл в `not_target`.
- Проверен `5401...`:
  - `conv_5301kx35hp58f75b17e5dbn0ww77`
  - soft-refusal rescue сработал;
  - плохой pre-opener: `Алло?` и spoken `skip_turn({...})`.
- Проверен `6201...`:
  - `conv_9801kx35ydp7f4wa48nca6284e7b`
  - хороший текущий behavioral candidate:
    - opener first;
    - нет spoken tool pseudo-code;
    - первый `Нет` дожимается;
    - SMS отправляется.
  - remaining defect: SMS/tool-tail около `13s`.
- Проверен `6701...`:
  - `conv_4201kx3635jneqtap5sz4g5dfewh`
  - попытка `soft_timeout=3.0` отклонена: agent сделал silent `skip_turn` вместо opener.
- Lab откатан на payload-класс `6201...`:
  - current head: `agtvrsn_4701kx3652j2fcvt96htmxfp81h3`

### На чем остановились
- Current lab head:
  - `agtvrsn_4701kx3652j2fcvt96htmxfp81h3`
- Это не идеал, но лучший безопасный текущий кандидат.
- Не использовать:
  - `agtvrsn_1801kx35czwsevk89sb016dthhjt`
  - `agtvrsn_5401kx35h6wge41sm97fs0vpr79e`
  - `agtvrsn_6701kx362nj4et2s1vpya63vzkht`
- Боевой `Main` не трогался.

### Что делать дальше
1. Не возвращать global soft-timeout как быстрый фикс: он может сломать opener.
2. Следующий реальный узел:
   - SMS/tool-tail.
3. Вероятные правильные направления:
   - объединить `send_sms_info` и `call_log` на backend/workflow уровне;
   - сделать быстрый SMS-finalization endpoint;
   - либо переводить relevant tools на MCP/config override, если нужен гарантированный `pre_tool_speech`.
4. После этого снова прогнать:
   - SMS consent;
   - machine/`абонент`;
   - confused user.

## Обновление 2026-07-09 12:58 MSK: lab head `5701...`, opener без global softfill

### Сделано
- Ветка работы:
  - Git: `codex/eleven-naturalness-lab`
  - ElevenLabs lab branch: `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - боевой `Main` не трогался.
- Проверка `7901...` показала, что global `soft_timeout_config` может вставить filler до opener:
  - `conv_2901kx34bnwfesm8t15t0232tj6e`
  - agent начал с `...`;
  - затем был `Здравствуйте,...`.
- Опубликован и валидно проверен `2001...`:
  - version: `agtvrsn_2001kx34hhssf7zbe84p3k9y53z6`
  - `soft_timeout_config.timeout_seconds = -1`
  - opener первым прошёл в `conv_5801kx34j2x5ea08nxyqa3tkenbe`.
- На `2001...` выявлен длинный SMS-tail:
  - после согласия на SMS около `12s` до финальной spoken-фразы;
  - `send_sms_info`, `call_log`, `end_call` реально отработали.
- Опубликован текущий lab head:
  - `agtvrsn_5701kx34qma3em39qcqzyrjjjba3`
  - добавлено immediate SMS acknowledgement: `Да, отправляю.`
  - порядок: `send_sms_info` -> silent `call_log` -> один `end_call`.
- `call_20` на `5701...` невалиден:
  - `conv_7701kx34r36je1vt5wqskthe2tst`
  - `sip_pending_no_media`
  - transcript пустой.
- Advisor исправлен:
  - no transcript / no timing / no termination reason = `no_behavioral_transcript`, не success.

### На чем остановились
- Current lab head:
  - `agtvrsn_5701kx34qma3em39qcqzyrjjjba3`
- Подтверждённый baseline:
  - `agtvrsn_2001kx34hhssf7zbe84p3k9y53z6`
- Правило:
  - global softfill сейчас выключен, потому что ломал pre-opener.
  - Fillers можно возвращать только после прохождения opener/SMS/machine gates и только post-opener.

### Что делать дальше
1. Повторить один валидный self-test на `5701...`.
2. Проверить SMS consent:
   - first spoken opener полный;
   - после SMS consent сразу `Да, отправляю.`;
   - после `call_log` нет обычной речи;
   - final close один.
3. Потом проверить:
   - machine/`абонент`;
   - confused user.
4. В live не переносить, пока gates не пройдены.

## Обновление 2026-06-18: что сейчас реально мешает naturalness даже без новых звонков

- Новый стабильный short-entrypoint без привязки к дате:
  - [.runtime/eleven_control_tower_latest/operational_brief.md](/home/max/n8n_ai_call_center/.runtime/eleven_control_tower_latest/operational_brief.md:1)
- Новый companion-file для выбора следующего кандидата:
  - [.runtime/eleven_control_tower_latest/next_variant_advisor.md](/home/max/n8n_ai_call_center/.runtime/eleven_control_tower_latest/next_variant_advisor.md:1)
- Важно понимать:
  - этот файл в `latest` без audit-входа показывает baseline post-quota порядок;
  - targeted recommendation по конкретному звонку появляется либо:
    - в run-папке как `next_variant_advice.md`,
    - либо через helper `recommend_next_variant.sh` с audit/run-dir.
- Свежий advisory:
  - `.runtime/eleven_docs_alignment_2026-06-18.json`
- Свежая перепроверка live readiness:
  - `.runtime/eleven_live_readiness_2026-06-18_check_now/live_readiness_summary.json`
- Главный operational факт:
  - новые self-test/live calls до пополнения квоты не запускать;
  - blocker сейчас именно quota, а не relay/n8n route.
- Главный product/UX факт по current published `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`:
  - `turn_timeout = 1.78`
  - `turn_eagerness = eager`
  - `client_events` без `interruption`
  - `soft_timeout_seconds = 1.9`
  - filler prompt содержит пример `Секунду...`
- Что это значит простыми словами:
  - агент сейчас может казаться “ботом” не только из-за голоса;
  - он слишком быстро перехватывает ход;
  - не даёт человеку нормально вклиниться;
  - и может слишком рано вставлять filler, который звучит как обещание времени.
- Поэтому первый живой цикл после возврата квоты вести так:
  1. published current `9601...`;
  2. `interruptible_balanced` variant;
  3. если barge-in уже лучше, но fillers всё ещё звучат слишком по-ботски:
     - `interruptible_softfill` variant;
  4. при необходимости repeatable fallback `0901...`.
- И отдельно помнить:
  - после квоты мы тестируем не только голос и LLM;
  - мы обязательно тестируем:
    - interruptions;
    - turn timeout;
    - turn eagerness;
    - soft-timeout filler behavior.
- Новый payload для этого уже собран:
  - [.runtime/eleven_interruptible_softfill_variant_2026-06-18.json](/home/max/n8n_ai_call_center/.runtime/eleven_interruptible_softfill_variant_2026-06-18.json:1)
- Его смысл:
  - не трогать live prompt-state сильнее, чем нужно;
  - оставить interruptible / more-human turn-taking;
  - убрать из filler guidance time-promise лексику вроде `Секунду...`;
  - поднять soft-timeout чуть выше до `2.4`, чтобы filler не выстреливал слишком рано.
- Дополнительно уже собран и следующий узкий кандидат:
  - [.runtime/eleven_interruptible_latefill_variant_2026-06-18.json](/home/max/n8n_ai_call_center/.runtime/eleven_interruptible_latefill_variant_2026-06-18.json:1)
- Его смысл:
  - сохранить тот же interruptible / softfill-подход;
  - но отложить старт filler masking ещё немного дальше;
  - использовать `soft_timeout = 3.0` как более близкий к official-doc starting point для следующего A/B-шага.
- Для быстрой offline-проверки этого слоя теперь есть:
  - [scripts/check_eleven_turn_variant_invariants.py](/home/max/n8n_ai_call_center/scripts/check_eleven_turn_variant_invariants.py:1)
  - [scripts/report_eleven_turn_variant_matrix.py](/home/max/n8n_ai_call_center/scripts/report_eleven_turn_variant_matrix.py:1)
- Готовый matrix-output:
  - [.runtime/eleven_turn_variant_checks_2026-06-18/variant_matrix.json](/home/max/n8n_ai_call_center/.runtime/eleven_turn_variant_checks_2026-06-18/variant_matrix.json:1)
- Его короткое практическое чтение:
  - `interruptible_balanced` лучше для первого barge-in теста;
  - `interruptible_softfill` лучше для второго теста, если проблема уже сместилась с “не даёт говорить” на “слишком ботские fillers”.
  - `interruptible_latefill` лучше для третьего теста, если fillers уже хорошие по лексике, но всё ещё стартуют чуть раньше, чем нужно.
- В post-quota pack это уже встроено:
  - [.runtime/eleven_post_quota_test_pack_2026-06-18/validate_variants.sh](/home/max/n8n_ai_call_center/.runtime/eleven_post_quota_test_pack_2026-06-18/validate_variants.sh:1)
- И там же лежит короткий status brief:
  - [.runtime/eleven_control_tower_latest/operational_brief.md](/home/max/n8n_ai_call_center/.runtime/eleven_control_tower_latest/operational_brief.md:1)
- Если нужен один файл, с которого начать после паузы или в новом чате, это сейчас лучший short entrypoint.
- Если нужен не просто status, а быстрый выбор следующего variant по типу жалобы:
  - использовать:
    - `next_variant_advisor.md`
- Advisor теперь понимает не только свободный текст жалобы, но и:
  - `finalization_audit.json`
  - или целую run-папку, внутри которой уже лежит `finalization_audit.json`
- Это значит:
  - после первого post-quota self-test можно не гадать вручную;
  - можно сразу прогнать advisor по audit и получить следующий разумный variant-order.
- Теперь это уже умеет и сам:
  - [scripts/run_eleven_selftest_audit.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_selftest_audit.sh:1)
- После `--audit-only` или полного self-test цикла он теперь пишет рядом:
  - `finalization_audit.json`
  - `next_variant_advice.json`
  - `next_variant_advice.md`
- И сразу печатает короткую summary-подсказку по следующему variant прямо в консоль.
- Важно:
  - advisor теперь умеет честно ставить:
    - `ready_for_variant_testing = false`
  - это значит:
    - сначала нужен fix-before-variant шаг;
    - и только потом уже новый A/B звонок.
- Типичные fix-before-variant кейсы:
  - `single_close_only`
  - `hard_stop_machine_transfer`
  - `fix_tool_identity_binding`
- Если нужен не только status, но и полный инженерный refresh одной командой:
  - [scripts/refresh_eleven_control_tower.sh](/home/max/n8n_ai_call_center/scripts/refresh_eleven_control_tower.sh:1)
- Поэтому следующий практический запуск должен начинаться так:
  1. `validate_variants.sh`
  2. readiness
  3. published self-test
  4. только потом lab-payload apply/self-test

## Обновление 2026-06-18: как теперь выбирать рабочую версию после quota-blocker

- Пока live/self-test заблокирован квотой, не выбирать “лучшую версию” по памяти или по одному понравившемуся разговору.
- Источник выбора сейчас:
  - `.runtime/eleven_lab_version_leaderboard_2026-06-18.json`
- Новое правило:
  1. `best_repeatable_candidates` важнее, чем `best_single_run_candidates`;
  2. хороший один разговор ещё не делает версию основной рабочей базой;
  3. текущую published version всегда проверять первой после снятия квоты;
  4. если published version слаба, fallback брать из `best_repeatable_candidates`, а не из красивого одиночного случая.
- На текущий момент:
  - лучший repeatable-кандидат:
    - `agtvrsn_0901kva21515f08v6xn9w3v05zg3`
  - лучший single-run-кандидат:
    - `agtvrsn_5501kv8bkjkffjna37fq79vd5c7j`
  - текущая опубликованная версия:
    - `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`

## Обновление 2026-06-18: official docs указывают на turn-taking, а не только на голос

- Локальный advisory по current published snapshot:
  - `.runtime/eleven_docs_alignment_2026-06-18.json`
- Главный вывод:
  - у текущей published version нет `interruption` в `client_events`;
  - при этом стоит:
    - `turn_eagerness = eager`
    - `turn_timeout = 1.78`
- Для user-perceived naturalness это сильный сигнал, что проблема может быть не только в voice/LLM, а в том, что агент слишком рано забирает ход и не пускает человека в ответ.
- Под этот сценарий уже подготовлен lab-only payload:
  - `.runtime/eleven_interruptible_balanced_variant_2026-06-18.json`
- Его смысл:
  - включить interruptions;
  - ослабить агрессивность turn-taking;
  - не трогать лишний раз текущий prompt и voice stack.

## Обновление 2026-06-18: post-quota pack уже собран

- Готовый execution pack:
  - `.runtime/eleven_post_quota_test_pack_2026-06-18/`
- В нём уже лежат:
  - `payload_interruptible_balanced.json`
  - `payload_repeatable_fallback.json`
  - `manifest.json`
  - `run_commands.sh`
- Практический смысл:
  - после пополнения квоты следующий цикл запускается уже не “по памяти”, а через один готовый пакет;
  - `run_commands.sh` сначала делает readiness и сам останавливается, если quota blocker ещё активен.

## Обновление 2026-06-18: batch-layer уже показывает статистический backlog по серии self-test разговоров

- Для серии разговоров теперь есть и batch-layer:
  - [scripts/analyze_eleven_conversation_batch.py](/home/max/n8n_ai_call_center/scripts/analyze_eleven_conversation_batch.py:1)
- Он позволяет видеть не только один кейс, а статистический backlog по группе разговоров.
- Готовый пример:
  - [.runtime/eleven_lab_golden_confirm_2026-06-17/batch_audit_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_golden_confirm_2026-06-17/batch_audit_summary.json:1)
- На этой серии уже видно:
  - `turn_taking_or_dialogue_flow = 15`
  - `tool_path = 2`
  - `llm_generation = 1`
- На более широком lab-summary:
  - [.runtime/eleven_all_lab_batch_summary_2026-06-18.json](/home/max/n8n_ai_call_center/.runtime/eleven_all_lab_batch_summary_2026-06-18.json:1)
  картина ещё жёстче:
  - `turn_taking_or_dialogue_flow = 185`
  - `tool_path = 16`
  - `llm_generation = 6`
- То есть следующий цикл должен начинаться не с косметического voice-polish, а с:
  - `focus_turn_taking`
  - `single_close_only`
  - `fix_tool_identity_binding`
  - `no_normal_speech_after_call_log`
  - `remove_late_line_checks`

## Обновление 2026-06-18: локальный audit разговора теперь меряет и задержки, а не только хвосты финализации

- Усилен:
  - [scripts/analyze_eleven_conversation.py](/home/max/n8n_ai_call_center/scripts/analyze_eleven_conversation.py:1)
- Теперь он ловит не только structural issues вроде:
  - `duplicate_close_before_end_call`
  - `placeholder_conversation_id_in_tool_call`
  - `context_fetch_before_opener`
  но и timing/flow problems:
  - `long_user_to_agent_gap`
  - `consecutive_agent_speech_without_user_reply`
  - `repeated_line_check_self_talk`
  - `machine_transfer_phrase_reached_agent_dialogue`
- Он также считает timing-summary:
  - `first_user_to_agent_gap_secs`
  - `user_to_agent_gap_stats_secs`
  - `known_path_stats_secs`
  - `unexplained_overhead_stats_secs`
  - `primary_bottleneck_counts`
  - `llm_ttfb_stats_secs`
  - `llm_ttf_sentence_stats_secs`
  - `llm_last_sentence_stats_secs`
  - `tts_ttfb_stats_secs`
- Wrapper:
  - [scripts/run_eleven_selftest_audit.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_selftest_audit.sh:1)
  теперь выводит timing-summary прямо в коротком summary без ручного `jq`.
- И теперь же выводит короткий top-list рекомендаций:
  - какие именно фиксы приоритетнее на этом разговоре.
- Практический смысл:
  - если `llm_ttfb` и `tts_ttfb` сами по себе нормальные, а user-facing gap остаётся длинным,
    значит узкое место уже не в raw модели/голосе, а в:
    - turn-taking;
    - лишнем rescue;
    - позднем финальном close;
    - лишнем tool-step;
    - dialogue-flow.
- Теперь это видно и машинно:
  - когда classifier даёт `tool_path`, имеет смысл смотреть в `call_log/send_sms_info/context_fetch`;
  - когда даёт `turn_taking_or_dialogue_flow`, следующий fix искать уже в правилах разговора и sequencing, а не в одной только модели.
- А recommendation-layer превращает это в готовый следующий ход:
  - например `focus_turn_taking`, `remove_late_line_checks`, `single_close_only`.

## Обновление 2026-06-18: текущая опубликованная ветка перепроверена и совпадает с нашей живой нормой

- Для быстрой и повторяемой проверки добавлен helper:
  - [scripts/fetch_eleven_agent_snapshot_via_server_env.sh](/home/max/n8n_ai_call_center/scripts/fetch_eleven_agent_snapshot_via_server_env.sh:1)
- Свежий snapshot текущей опубликованной ветки:
  - [.runtime/eleven_current_branch_snapshot_2026-06-18_now/summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_current_branch_snapshot_2026-06-18_now/summary.json:1)
- На 2026-06-18 сейчас подтверждено:
  - `agent_id = agent_8801kgybyekned2a8yae6rp8hk3q`
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - `version_id = agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
  - `llm = gpt-5-mini`
  - `tts.model_id = eleven_v3_conversational`
  - `first_message = ""`
  - `turn_timeout = 1.78`
  - `soft_timeout_seconds = 1.9`
- Активные tools в текущем published snapshot:
  - `context_fetch`
  - `call_log`
  - `send_sms_info`
  - `end_call`
  - `skip_turn`
  - `voicemail_detection`
- Локальный инвариант-checker:
  - [scripts/check_eleven_prompt_invariants.py](/home/max/n8n_ai_call_center/scripts/check_eleven_prompt_invariants.py:1)
  синхронизирован с этой фактической нормой.
- Свежая проверка опубликованной ветки:
  - [.runtime/eleven_current_branch_snapshot_2026-06-18_now/invariants.json](/home/max/n8n_ai_call_center/.runtime/eleven_current_branch_snapshot_2026-06-18_now/invariants.json:1)
  показывает:
  - `43/43 ok`
  - `checks_failed = 0`
- Это означает, что на текущий момент опубликованная ветка не “уплыла” от нашей контрольной логики по:
  - exact opener;
  - hard-stop по `абонент` / machine;
  - strict silence;
  - one-rescue rule;
  - price-answer anchor;
  - soft-timeout filler.
- Важно:
  - если звонки снова fail сейчас, нельзя автоматически считать, что уехал prompt;
  - свежий live readiness по-прежнему показывает внешний blocker:
    - `overall_diagnosis = quota_blocker_active`
  - то есть текущий стоп сейчас не в drift этой ветки, а в квоте Eleven.

## Обновление 2026-06-17: отдельный system-binding цикл дал частичную победу, но жёсткая `v2` отклонена

- Для отдельного technical-шага добавлен helper:
  - [scripts/prepare_eleven_system_binding_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_system_binding_variant.sh:1)
- Его смысл:
  - не менять live `Main`;
  - не менять voice-stack;
  - только аккуратно проверить, можно ли прибить:
    - `context_fetch` до opener
    - и фальшивые `conv_*` в drafted tool-call
- Что проверено:
  - `agtvrsn_1101kvabn43mfeztaavzxwcbtxyn`
    - звонок:
      - `conv_3001kvabnww3f878kczd95zcndkz`
    - результат:
      - `context_fetch_before_opener` ушёл;
      - фактический webhook body по `call_log` уже продолжил получать правильный live `conv_*`;
      - но draft `params_as_json` ещё содержал fake `conv_abcdef...`
  - `agtvrsn_7501kvabt8d8ewcrmxmnrcrmtn42`
    - звонок:
      - `conv_6901kvabtxcrezm8y19zcyctde1f`
    - результат:
      - placeholder issue из audit исчез;
      - но разговор деградировал:
        - stage tags `[calm]`
        - поздние `Алло?`
        - повторные confused loops
- Поэтому:
  - `agtvrsn_7501kvabt8d8ewcrmxmnrcrmtn42` не считать текущей рабочей точкой;
  - после этого lab-ветка возвращена на более безопасную линию;
  - новый branch-head после отката:
    - `agtvrsn_0101kvac144tfsb88f32crqgbmvq`
- Важная интерпретация:
  - этот binding-cycle показал, что issue `context_fetch_before_opener` решаем;
  - но placeholder `conv_*` дальше нужно добивать отдельно от общей разговорной naturalness-логики.
- Отдельный checkpoint по этому циклу:
  - [docs/checkpoints/2026-06-17_ELEVEN_SYSTEM_BINDING_FIX.md](/home/max/n8n_ai_call_center/docs/checkpoints/2026-06-17_ELEVEN_SYSTEM_BINDING_FIX.md:1)

## Обновление 2026-06-17: tool-layer patch по `call_log/end_call` уже проверен и отклонён

- Для отдельной structural-пробы добавлен helper:
  - [scripts/prepare_eleven_finalization_tool_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_finalization_tool_variant.sh:1)
- Его идея была понятной:
  - не переписывать весь prompt;
  - а сделать жёстче сами описания tools:
    - `call_log`
    - `end_call`
  - чтобы assistant закрывал звонок только как:
    - silent `call_log`
    - один spoken `end_call`
- Выпущенный кандидат:
  - `agtvrsn_9001kvac85yzfhgv8fx3tgqnvn7b`
- Контрольный звонок:
  - `conv_1101kvac8w32fjdtvay58v040esw`
- Что важно:
  - сначала могло показаться, что duplicate close ушёл;
  - но после усиления analyzer стало видно, что он просто маскировался stage tag'ом:
    - обычная реплика:
      - `Я уже отправила SMS на этот номер. Хорошего дня. [calm]`
    - затем тот же close шёл в `end_call.system__message_to_speak`
- Плюс сам разговор регрессировал:
  - `[calm]`
  - поздние `Алло?`
  - повторные SMS-loop ветки
- Поэтому:
  - `agtvrsn_9001kvac85yzfhgv8fx3tgqnvn7b` не считать рабочей точкой;
  - после отката текущий branch-head:
    - `agtvrsn_7301kvacfzesee19rmc9fs22m49e`
- Отдельный практический вывод:
  - structural tool-layer patch в одиночку пока не лечит финализацию без побочных регрессий;
  - следующий цикл по duplicate close надо держать отдельно от line-check и bracket-tag проблемы.

## Обновление 2026-06-17: price-answer anchor добавлен как отдельный micro-patch

- Для реплики пользователя про цену добавлен отдельный helper:
  - [scripts/prepare_eleven_price_anchor_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_price_anchor_variant.sh:1)
- Чтобы не держать цену и условия в хардкоде по нескольким файлам, добавлен отдельный машинно-читаемый anchor:
  - [docs/agent_kb_lipolong/10_COMMERCIAL_ANCHOR_RU.json](/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/10_COMMERCIAL_ANCHOR_RU.json:1)
- Он добавляет только один узкий разговорный anchor:
  - если человек спрашивает цену / стоимость / бесплатна ли тестовая упаковка,
    агент должен ответить прямо и коротко.
- Если человек цену не спрашивал:
  - агент не должен сам вставлять стоимость в opener, обычную презентацию или value-turn.
- Зафиксированный текущий anchor:
  - `от 19 000 руб.`
  - старт от `1 шт.`
  - тестовая упаковка не бесплатная
- Короткие дополнительные факты, которые допустимо упомянуть:
  - доставка `3-4 дня`
  - оплата: безнал, полная предоплата
- После price-answer agent не должен застревать в длинном споре о цене.
- Он должен:
  - коротко ответить
  - и перевести в один next step:
    - SMS
    - или callback менеджера
- Новый current branch-head после этого патча:
  - `agtvrsn_9201kvaeewdnerjvyrcb2ykkhz5g`
- Затем дополнительно очищен сам prompt:
  - повторный второй `Price-answer anchor override` удалён;
  - оставлен один канонический price-блок без дублирования.
- Для этой текущей вершины добавлен локальный preflight-check:
  - [scripts/check_eleven_prompt_invariants.py](/home/max/n8n_ai_call_center/scripts/check_eleven_prompt_invariants.py:1)
- Что он сейчас проверяет автоматически:
  - ровно один `Price-answer anchor override`;
  - цена не озвучивается инициативно;
  - цена даётся только по прямому вопросу;
  - exact opener присутствует ровно один раз;
  - `one rescue` правило на месте;
  - hard-stop по `абонент` и `МТС Защитник` на месте;
  - machine-path требует `call_log` и silent end.
- Текущий прогон на:
  - `agtvrsn_6701kvadx4z9f60a639v3h02dgmy`
  дал:
  - `13/13 ok`
- Отдельно уже собран JSON-driven payload от:
  - `10_COMMERCIAL_ANCHOR_RU.json`
  и локально проверен на:
  - `15/15 ok`
- Этот JSON-driven payload уже реально опубликован в текущую lab-ветку:
  - `agtvrsn_9201kvaeewdnerjvyrcb2ykkhz5g`
- Проверка опубликованного ответа Eleven тоже уже зелёная:
  - `15/15 ok`
  - [prompt_invariants_applied.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_price_anchor_jsonized_2026-06-17/apply_result/prompt_invariants_applied.json)
- Дополнительно добавлен cross-doc consistency-check:
  - [scripts/check_commercial_anchor_consistency.py](/home/max/n8n_ai_call_center/scripts/check_commercial_anchor_consistency.py:1)
- Он проверяет, что коммерческий anchor не разошёлся между:
  - `10_COMMERCIAL_ANCHOR_RU.json`
  - `01_PRODUCT_PROFILE_RU.md`
  - `09_ELEVEN_TOOL_SEND_SMS_RU.md`
- Текущий прогон уже зелёный:
  - `11/11 ok`
  - артефакт:
    - [.runtime/eleven_lab_price_anchor_jsonized_2026-06-17/commercial_anchor_consistency.json](/home/max/n8n_ai_call_center/.runtime/eleven_lab_price_anchor_jsonized_2026-06-17/commercial_anchor_consistency.json)
- Практический смысл:
  - если цена, минимальный вход, доставка или оплата меняются,
    дальше лучше менять их сначала в `10_COMMERCIAL_ANCHOR_RU.json`,
    а не вручную по разным prompt-кускам.
- Для следующего живого теста добавлен и специальный price-wrapper:
  - [scripts/run_eleven_price_selftest_audit.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_price_selftest_audit.sh:1)
- Он поверх обычного self-test цикла отдельно проверяет:
  - спросил ли пользователь цену;
  - не назвал ли агент цену раньше времени;
  - был ли после price-answer нормальный next step.
- Уже есть и историческое доказательство пользы этого check:
  - на старом звонке
    - `conv_3001kvaddyrwe50tdpf91vwwpsv7`
    он поймал:
    - `price_mentioned_before_user_asked`
    - `no_price_question_detected`

## Обновление 2026-06-17: добавлен локальный audit для хвостов финализации

- Для разговора с ElevenLabs теперь есть не только ручное прослушивание, но и локальный JSON-audit:
  - [scripts/analyze_eleven_conversation.py](/home/max/n8n_ai_call_center/scripts/analyze_eleven_conversation.py:1)
- Для удобного повседневного цикла сверху добавлен wrapper:
  - [scripts/run_eleven_selftest_audit.sh](/home/max/n8n_ai_call_center/scripts/run_eleven_selftest_audit.sh:1)
- Он нужен именно для тех хвостов, которые не удалось добить одними prompt-only правками:
  - duplicate close;
  - late line-check;
  - filler в finalization;
  - placeholder `conv_*` в tool-call;
  - `context_fetch` до opener;
  - bracket-style spoken tags.
- Отдельный checkpoint по его результатам:
  - [docs/checkpoints/2026-06-17_ELEVEN_FINALIZATION_AUDIT.md](/home/max/n8n_ai_call_center/docs/checkpoints/2026-06-17_ELEVEN_FINALIZATION_AUDIT.md:1)
- Практическое правило на сейчас:
  - после каждого self-test по naturalness сначала смотреть transcript и слухом;
  - потом обязательно прогонять audit:
    - либо через `scripts/run_eleven_selftest_audit.sh`
    - либо через `scripts/analyze_eleven_conversation.py` по готовому `conversation_poll_final.json`;
  - и только потом считать, стала ли версия реально лучше.

## Обновление 2026-06-17: cleanup-серия поверх V3 softfill не стала новым winner и lab возвращён на softfill

- После подтверждения сильной softfill-линии были проверены ещё три узких prompt-only cleanup-кандидата:
  - `agtvrsn_5701kvaaanp8feqvj6s1hrcw2mp0`
  - `agtvrsn_4701kvaafxaket0rtt3y5hnt9q14`
  - `agtvrsn_9501kvaapngkexzr5964jhvbh4zw`
- Их задача была локальной:
  - прибить line-check после осмысленного post-opener ответа;
  - убрать filler в финализации;
  - убрать duplicate close между обычной репликой и `end_call`.
- Контрольные звонки:
  - `conv_7001kvaa3cv7emkbw8ztmn9tyg95`
  - `conv_4601kvaabcqaf37tw4tbr87y8s28`
  - `conv_1701kvaaqez7ehyv5d39m3egvwx4`
  показали:
  - prompt-only серия не дала устойчивой победы;
  - duplicate close всё ещё встречается;
  - line-check хвосты всё ещё встречаются;
  - filler / лишняя речь в finalization тоже ещё прорывается.
- Поэтому эта серия не признана новой верхней нормой.
- Lab-ветка возвращена обратно на проверенную softfill-линию.
- Новый branch-head после возврата:
  - `agtvrsn_1201kvaavm18fe8b4sgw5vxt7tqy`
- Практический вывод:
  - V3 softfill остаётся лучшей текущей точкой;
  - следующий прогресс по `duplicate close / finalization filler` уже лучше искать не через ещё один текстовый запрет, а через более структурный контроль финализации.

## Обновление 2026-06-17 по `GPT-5 Mini + Eleven v3 Conversational`: включён lab-only `soft timeout`, а `tool_call_sound` через branch patch не закрепился

- После разбора docs ElevenLabs и последних V3 self-test зафиксирован следующий практический план:
  - `soft timeout` использовать именно для задержки LLM;
  - `tool call sounds` использовать только для реальной задержки tools;
  - не смешивать эти два механизма в одну "магическую" настройку.
- Для выбранной пользователем связки
  - `gpt-5-mini + eleven_v3_conversational`
  собран отдельный lab-only payload:
  - `.runtime/eleven_lab_gpt5mini_v3_softfill_2026-06-17/payload.json`
- Для этого payload добавлен локальный helper:
  - [scripts/prepare_eleven_softfill_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_softfill_variant.sh:1)
- Что этот helper делает:
  - берёт проверенный snapshot V3-линии;
  - оставляет тот же `llm` и тот же `tts.model_id`;
  - включает `soft_timeout_config` как мягкое заполнение тишины при долгом LLM-ответе;
  - пробует повесить `typing` только на `send_sms_info`.
- Выпущенная lab-версия:
  - `agtvrsn_6101kva6gy9vfssvk495wkznmh4c`
- Что реально подтвердилось после `apply_result`:
  - `llm = gpt-5-mini`
  - `tts.model_id = eleven_v3_conversational`
  - `soft_timeout_config.timeout_seconds = 2.8`
  - fallback message:
    - `Так...`
  - `use_llm_generated_message = true`
  - filler prompt override теперь требует:
    - очень короткий natural thinking filler;
    - без вопроса к пользователю;
    - без проверки линии;
    - без обещания времени ожидания.
- Что не закрепилось:
  - `tool_call_sound` для `send_sms_info` через `Update agent` не сохранился;
  - после ответа ElevenLabs tool по-прежнему вернулся к:
    - `tool_call_sound = null`
    - `tool_call_sound_behavior = auto`
- Практический вывод:
  - branch-level patch над agent-конфигом для `soft timeout` работает;
  - branch-level patch для `tool_call_sound` на shared webhook tools в нашем контуре пока не доказан.
- Важное ограничение:
  - прямой `PATCH /tools/:tool_id` сейчас нельзя делать бездумно,
    потому что `context_fetch`, `call_log`, `send_sms_info` у lab и live общие по `tool_id`;
  - такой шаг уже может поменять поведение боевого контура, а не только lab.
- Поэтому безопасная следующая линия:
  1. протестировать новую lab-version
     - `agtvrsn_6101kva6gy9vfssvk495wkznmh4c`
     именно на слух:
     - не вставляет ли filler слишком рано;
     - не путается ли filler с line-check;
     - не делает ли V3 разговор ещё более вязким;
  2. если filler полезен, оставить `soft timeout`;
  3. если всё ещё нужен audio-mask на SMS-path,
     делать уже отдельный safe-cycle:
     - либо через lab-only duplicate tool,
     - либо через отдельный branch-safe способ переопределения tools,
     а не через глобальный shared tool patch.

### Self-test на новой softfill-версии

- Проведён branch-targeted self-test:
  - `conv_0501kva6snynemktpje537318ep5`
  - `version_id = agtvrsn_6101kva6gy9vfssvk495wkznmh4c`
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - transport:
    - `relay_via_server`
- Подтверждено:
  - звонок действительно прошёл на ожидаемой V3 softfill-версии;
  - opener стартовал чисто:
    - `Алло!` в `1s`
    - exact opener уже в `3s`
  - дальнейший диалог шёл живо и по смыслу:
    - user подтвердил интерес;
    - agent нормально объяснил продукт;
    - на неуместные личные реплики agent не развалился и вернул разговор в business-flow;
    - `send_sms_info` и `call_log` прошли успешно;
  - финализация по SMS-path тоже завершилась корректно:
    - `send_sms_info latency ≈ 1.05s`
    - `call_log latency ≈ 1.75s`
    - `end_call latency ≈ 0.50s`
- Что реально стало ясно по `soft timeout`:
  - filler действительно сработал;
  - но сработал слишком поздно для этой конкретной ветки:
    - после user-реплики с просьбой отправить SMS в `104s`
    - filler `Так...` прозвучал только в `123s`
  - то есть субъективно диалог получился хорошим,
    но технически именно перед SMS всё ещё висит слишком длинная пауза.
- Точный технический разбор хвоста:
  - перед `send_sms_info` зафиксирован
    - `convai_llm_service_ttfb ≈ 4.41s`
  - затем уже сам tool отработал быстро
    - `≈ 1.05s`
  - значит главный остаточный хвост в этой ветке сейчас не в SMS webhook,
    а в позднем решении LLM перед tool-call.
- Практический вывод:
  - эта версия уже сильная по naturalness и удержанию живого разговора;
  - следующий узкий шаг теперь не про общий стиль,
    а именно про сокращение паузы в ветке:
    - `попросили SMS -> send_sms_info`
  - `soft timeout` не надо сразу выкидывать,
    но его одного недостаточно, чтобы скрыть такой длинный decision-gap.

### Попытка `SMS fastlane` поверх удачной V3-версии

- Для точечной подрезки SMS decision-gap собран отдельный prompt-only patch:
  - [scripts/prepare_eleven_sms_fastlane_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_sms_fastlane_variant.sh:1)
- Смысл patch:
  - если в реплике уже есть явная просьба отправить SMS,
    agent должен идти в `send_sms_info` сразу,
    не пересказывать и не зависать.
- Этот кандидат был опубликован как:
  - `agtvrsn_3501kva75b4qf6htw6qkys1j1q6b`
- Контрольный self-test:
  - `conv_0901kva76300ebcvv2rvr2ybpb6z`
- Что этим тестом подтверждено:
  - версия подхватилась правильно;
  - но звонок ушёл не в SMS-ветку, а в ветку:
    - `интересно -> не работаем -> до свидания`
  - поэтому честного сравнения SMS decision-gap этот звонок не дал.
- Что при этом всплыло плохого:
  - после уже фактически завершённого `not_target` agent снова полез с лишними line-check фразами:
    - `Вы ещё на линии?`
    - `Алло?`
  - такой хвост для хорошей outbound-версии нам не нужен.
- Поэтому этот `SMS fastlane` пока не принят как новая рабочая вершина.
- Lab-ветка после этого возвращена обратно на softfill-линию:
  - новая branch-head после отката:
    - `agtvrsn_1101kva7s8drfz4r26j2ymbt9r9j`
  - по сути это возврат к удачной конфигурации
    - `GPT-5 Mini + Eleven v3 Conversational + soft timeout`
    без неподтверждённого fastlane-патча.
- Практический вывод:
  - `SMS fastlane` остаётся как кандидат, но не как текущий winner;
  - текущий source-of-truth в lab лучше считать именно softfill-линию,
    потому что на ней уже был подтверждён реально удачный разговор.

## Обновление 2026-06-17 по официальной документации ElevenLabs: что сильнее всего влияет на быстрый отклик

- По docs ElevenLabs для низкой задержки надо смотреть не на один параметр, а сразу на 5 слоёв:
  - LLM;
  - TTS-модель;
  - `turn_timeout`;
  - `turn_eagerness`;
  - внешние tool-вызовы.
- Практический вывод для нашего проекта:
  - `eleven_flash_v2_5` остаётся главным быстрым TTS-кандидатом;
  - `eleven_v3_conversational` можно использовать ради более богатого звучания,
    но он чаще делает разговор вязким.
- По docs `Conversation flow`:
  - `turn_timeout` отвечает за то, когда agent забирает ход после тишины;
  - `soft timeout` нужен, чтобы замаскировать реальное ожидание LLM;
  - `turn_eagerness = eager` даёт более быстрый старт ответа, но повышает риск перебивания;
  - лишние interruption-механики могут как помочь opener, так и замедлить objection-flow.
- По docs `Speed control`:
  - допустимый диапазон `speed = 0.7–1.2`;
  - экстремальные значения могут ухудшать качество речи;
  - для нашего контура разумно держаться рядом с `1.0–1.1`, а не пытаться “ускорить всё” любой ценой.
- По docs `Tools` и `Tool Call Sounds`:
  - быстрые tool-вызовы лучше оставлять тихими или с очень лёгким маскированием;
  - длинные tool-вызовы можно прикрывать коротким pre-speech или ambient sound;
  - но если tool быстрый, звук и pre-speech могут сами сделать ответ более тормозным на слух.
- По docs `Optimizing LLM costs`:
  - краткий prompt и точные tool-вызовы уменьшают не только стоимость,
    но и задержку;
  - большие куски ненужного контекста в system prompt и истории разговора вредят и скорости, и управляемости.

### Что это значит именно для нас

- Если нужно ускорить реакцию live-агента:
  1. сначала сокращать prompt и фиксировать длину ответов;
  2. потом подбирать быстрый LLM;
  3. потом поджимать `turn_timeout` и `turn_eagerness`;
  4. только потом трогать маскировку ожиданий через `soft timeout` или tool-sounds.
- Если agent звучит “слишком ботом”, это не значит, что надо сразу ставить самую тяжёлую voice-модель.
- Для телефонного sales-контура лучший баланс обычно получается не у самой “красивой” модели,
  а у той, которая:
  - быстро начинает говорить;
  - не жует слова;
  - не висит с длинным молчанием после ответа человека.

## Обновление 2026-06-17 по tuned `GPT-5 Mini + Eleven v3 Conversational`

- На сырой связке
  - `GPT-5 Mini + Eleven v3 Conversational`
  был явный регресс по длине и вязкости.
- После этого выпущен targeted tuning-patch:
  - без раннего `call_log`;
  - с короткими sales-turns;
  - с жёстким post-SMS close;
  - без продолжения разговора после SMS.
- Тuned-версия:
  - `agtvrsn_3201kva3xjj1fxr959jzkymjk038`
  - звонок:
    - `conv_4101kva3y9agf5yrp04g78m87wk0`
- Что стало лучше:
  - разговор стал заметно короче;
  - early `call_log` исчез;
  - после SMS agent уже не раскрывает новый длинный блок диалога;
  - clean-close стал правильнее.
- Что ещё осталось:
  - местами перебивает и не даёт достаточно пространства пользователю;
  - повторный rescue всё ещё бывает;
  - в transcript `params_as_json` tool-call всё ещё содержит placeholder-like значения, хотя реальный webhook body уже нормальный.
- Практически:
  - эту связку уже стоит не выбрасывать, а дотачивать дальше;
  - текущий lab-кандидат теперь именно она:
    - `gpt-5-mini + eleven_v3_conversational`
    - `agtvrsn_3201kva3xjj1fxr959jzkymjk038`

## Обновление 2026-06-17 по `tuned2`, `tuned3` и `tuned1b`

- После первой удачной tuned-версии были проверены ещё три узких варианта:
  - `tuned2`
  - `tuned3`
  - `tuned1b`
- Итог по ним общий:
  - ни один не стал лучше исходной tuned1-линии.
- `tuned2`:
  - короче, но вернул сервисный хвост и плохие close-фразы.
- `tuned3`:
  - ещё короче, но снова вылезли
    - `Вы на линии?`
    - `Чем могу помочь ещё?`
  - этот вариант признан регрессивным.
- `tuned1b`:
  - идея замаскировать SMS-латентность была нормальной;
  - но реальный self-test не дал нового качественного улучшения относительно tuned1.
- Поэтому текущая восстановленная лучшая версия на сегодня:
  - `agtvrsn_0301kva4xj1vers8ry3evaf4q0jp`
  - фактически это возврат к tuned1-линии:
    - `gpt-5-mini + eleven_v3_conversational`

## Обновление 2026-06-17 по `Gemini + V3` и `GPT-5 Mini + V3`

- Отдельно проверена связка:
  - `Gemini 2.5 Flash + Eleven v3 Conversational`
  - `agtvrsn_5201kva3dwhyf0xrm8wjdz7xnykc`
  - звонок:
    - `conv_2801kva3emkdf0p9dd2jk0s38agv`
  - итог:
    - сценарий не развалился;
    - not-target финализация чистая;
    - но темп всё ещё тяжеловат.
- Затем проверена связка:
  - `GPT-5 Mini + Eleven v3 Conversational`
  - `agtvrsn_9401kva3jyk3eyja2v0manq9r8mk`
  - звонок:
    - `conv_7301kva3kn56ep7b4esk2qqvcdd5`
  - итог:
    - слишком длинный и вязкий разговор;
    - ранний `call_log` ещё до opener;
    - после SMS agent продолжил разговор вместо короткого clean-close;
    - для live-style телефонного контура это регресс.
- После этих тестов lab снова возвращён на:
  - `agtvrsn_0201kva3t7vyexzvv7prj3z7wbef`
  - `gemini-2.5-flash + eleven_flash_v2_5`

## Обновление 2026-06-17 по `GPT-5`, `GPT-5 Mini`, `GPT-5 Nano`

- В отдельном lab-cycle были проверены три OpenAI-кандидата:
  - `gpt-5-mini`
  - `gpt-5-nano`
  - `gpt-5`
- `GPT-5 Mini`:
  - `agtvrsn_0101kva2ts7ee57r5b86vqts64me`
  - звонок:
    - `conv_4901kva2vhn5fx4s3gtxjj5vcptr`
  - итог:
    - лучше, чем `GPT-4o Mini`;
    - чисто доходит до `call_log` и `end_call`;
    - но говорит длиннее нужного и всё ещё тяжело заходит после `нет`;
    - в transcript есть странность в `params_as_json` tool-call, хотя реальный webhook body уже правильный.
- `GPT-5 Nano`:
  - `agtvrsn_2401kva2zfqdegt8wam2nhyqx3k1`
  - звонок:
    - `conv_8601kva308pbf8bvc7bd1pservfe`
  - итог:
    - слишком слабый для нашего sales-сценария;
    - повторяет opener и держится хуже.
- `GPT-5`:
  - `agtvrsn_4901kva34bqhf8ybm1zcm04h6bbf`
  - звонок:
    - `conv_6201kva352w6fe4ajzyntq6p46x3`
  - итог:
    - держит сценарий уже прилично;
    - clean finalization есть;
    - но ответы длиннее, паузы после возражения всё ещё не идеальны, и цена выше всех.
- Практический вывод:
  - из OpenAI-проверок на сегодня самый живой кандидат — `GPT-5 Mini` или `GPT-5`, но ни один из них пока не выбил текущий Gemini-баланс;
  - lab после сравнения возвращён обратно на:
    - `gemini-2.5-flash + eleven_flash_v2_5`
  - актуальная восстановленная версия:
    - `agtvrsn_4401kva39np7e8hbze7anrs0565y`

## Обновление 2026-06-17 по `GPT-4o Mini` в naturalness-lab

- От текущей лучшей Gemini-версии был собран отдельный compare-payload только со сменой LLM:
  - `gpt-4o-mini`
  - без изменений TTS, prompt, `client_events` и `turn_eagerness`
- Новый lab-кандидат был опубликован как:
  - `agtvrsn_5201kva2hgb6ezxayw69t4qkzrpf`
- Реальный self-test:
  - `conv_1801kva2jcc7e9rtkcvj95jz1k63`
- По нему подтверждено:
  - opener сам по себе стартует нормально;
  - но objection-turn тяжёлый:
    - `нет` в `11s`
    - следующий вопрос agent только в `15s`
  - agent хуже держит сценарий и уходит в semantic drift:
    - вместо короткого sales-flow начинает объяснять, кто такие косметологи;
  - final close деградировал:
    - `Поняла, спасибо. Хорошего дня.` прозвучало дважды;
    - после этого agent снова вернулся в разговор, вместо чистого завершения.
- Итог:
  - `GPT-4o Mini` для нашего телефонного сценария сейчас регрессивен.
- Поэтому lab-ветка сразу возвращена обратно на Gemini:
  - `agtvrsn_3901kva2qtdhe0ebbrgv2ck1gv5g`
  - `llm = gemini-2.5-flash`
  - `tts.model_id = eleven_flash_v2_5`
- Практический вывод:
  - `GPT-4o Mini` сейчас не новый top candidate;
  - текущая верхняя линия для lab остаётся:
    - `Gemini 2.5 Flash + Eleven Flash v2.5`

## Обновление 2026-06-16 по реальному LLM compare-cycle в lab

- Фаза теоретической подготовки уже закончена: теперь есть реальные self-test звонки на альтернативных LLM, а не только payload и publish.
- Отдельно исправлен сам test harness:
  - `scripts/run_eleven_branch_selftest.sh`
  - теперь он:
    - сохраняет отдельные артефакты по `webhook`, `relay`, `relay_via_server`;
    - не затирает полезный 404/response пустым файлом;
    - умеет реально уходить в `relay_via_server`;
    - корректно переносит payload на сервер через SSH.
- Это важно, потому что live webhook всё ещё отвечает:
  - `404 Active version not found for workflow with id "sHTbALayEZdy8Mzs"`
  - а рабочий путь для lab self-test сейчас фактически:
    - `relay_via_server`
- Реально подтверждённый Claude self-test:
  - `conv_8601kv8bgf72fdrtgq4ez8w30yd0`
  - `version_id = agtvrsn_8301kv8adscff0sb23dwjcmvcxb1`
  - вывод:
    - opener чище;
    - но objection-turn медленный:
      - `А вы вообще с липолитиками работаете?`
      - `LLM TTFB ≈ 2.84s`
- Реально подтверждённый Gemini self-test:
  - `conv_3901kv8bm93tfdas3dqtnykzcnh6`
  - `version_id = agtvrsn_5501kv8bkjkffjna37fq79vd5c7j`
  - вывод:
    - objection-flow заметно быстрее:
      - `Вы вообще с липолитиками работаете?`
      - `LLM TTFB ≈ 1.06s`
    - value-follow-up тоже быстрее, чем у Claude;
    - но на первом ходе словлен opener-fragment:
      - `Здравствуйте,...`
- После этого был проверен отдельный prompt-patch именно под opener-fragment:
  - `version_id = agtvrsn_7301kv8bs45tfryst3c38jcpy0za`
  - контрольный звонок:
    - `conv_0401kv8bsthdfyvt0d6bp0fjjfe9`
  - итог:
    - стало хуже;
    - agent повторял opener несколько раз;
    - этот patch признан регрессивным.
- После этого отдельно проверена чисто platform-level гипотеза:
  - убрать `interruption` из `client_events`
  - не переписывая prompt
- Контрольный звонок:
  - `conv_7501kv8c555zetvbbxe74205zdwg`
  - `version_id = agtvrsn_9401kv8c4ebrec8b9xqxceqygqtk`
- По нему подтверждено:
  - opener прошёл чисто, без `Здравствуйте,...`;
  - но objection-turn стал тяжелее:
    - `LLM TTFB ≈ 2.25s`
  - final close тоже замедлился:
    - `LLM TTFB ≈ 2.63s`
- Затем проверена гипотеза через `interruption_ignore_terms`:
  - `version_id = agtvrsn_2201kv8c97stfsdrakry2k06ej7p`
  - звонок:
    - `conv_3501kv8c9xkfffsb4kbm9ay4bf5m`
  - итог:
    - agent вообще не дошёл до opener;
    - этот вариант признан неудачным.
- Потом подготовлен кандидат:
  - `no-interruption + turn_eagerness = eager`
  - `version_id = agtvrsn_5801kv8cd9cgffpvbspsyqby8k6j`
- После повторного цикла eager теперь уже есть answered self-test:
  - `conv_1901kva1cvmcf19rkxvk4xfcvh4g`
  - `version_id = agtvrsn_8901kva1a0pyexwan9hzkhmf832c`
- По нему подтверждено:
  - opener остался чистым, без `Здравствуйте,...`;
  - objection-turn стал быстрее, чем на `no-interruption + normal`:
    - `~2.25s -> ~1.98s`
  - value-turn
    - `интересно -> пока не используем -> SMS`
    идёт заметно живее:
    - `LLM TTFB ≈ 1.64s`
  - после `send_sms_info` финальный close стартует быстро:
    - `LLM TTFB ≈ 0.48s`
- Остаток, который ещё виден:
  - spoken-tail после SMS местами обрывается как:
    - `Я уже отправила СМС на этот номер. Хорошего дня...`
- Поэтому текущая подтверждённая верхняя lab-version сейчас уже:
  - `agtvrsn_8901kva1a0pyexwan9hzkhmf832c`
  - стек:
    - `llm = gemini-2.5-flash`
    - `tts.model_id = eleven_flash_v2_5`
    - `client_events` без `interruption`
    - `turn_eagerness = eager`
- Сверху дополнительно проверен общий `tool-only final close` patch:
  - `version_id = agtvrsn_0901kva21515f08v6xn9w3v05zg3`
  - контрольный звонок:
    - `conv_4301kva21wg8ets9xf29cbz0y0yf`
  - итог:
    - duplicate refusal close ушёл;
    - теперь на refusal path agent не говорит:
      - одну и ту же фразу до `call_log`
      - и потом ещё раз перед `end_call`
    - подтверждённая последовательность стала:
      - silent `call_log`
      - один spoken close
      - `end_call`
- Поэтому текущая верхняя lab-version теперь уже:
  - `agtvrsn_0901kva21515f08v6xn9w3v05zg3`
- Практический вывод на сейчас:
  - если приоритет — скорость живого разговора, `Gemini 2.5 Flash` выглядит сильнее;
  - если приоритет — более чистый старт без overlap-fragment, `Claude` пока аккуратнее;
  - если нужен лучший подтверждённый баланс внутри Gemini на сегодня, это уже:
    - `Gemini + no interruption + eager + tool-only final close`
  - следующий шаг теперь ещё уже:
    - не в refusal close;
    - а в подтверждение post-SMS финального close без `Хорошего дня...` и без spoken-дубля.

## Обновление 2026-06-16 по LLM shortlist для lab

- Важно не путать два разных слоя:
  - `LLM` — это мозг агента, который думает и выбирает, что сказать и какой tool вызвать;
  - `TTS model` — это голосовой движок, который уже озвучивает готовый текст.
- По свежим lab-артефактам подтверждено:
  - текущий рабочий lab tip:
    - `agtvrsn_4901kv88ns5pfgvbqbg3n42he4rp`
  - использует:
    - `llm = gpt-4.1`
    - `tts.model_id = eleven_flash_v2_5`
- Это важно, потому что последние циклы сравнивали в основном:
  - `eleven_v3_conversational`
  - против `eleven_flash_v2_5`
  как голосовые модели, а не как разные LLM.
- Следующий отдельный lab-cycle теперь нужно делать уже по мозгу агента, не меняя голосовой слой:
  - baseline:
    - `gpt-4.1`
  - кандидат на скорость:
    - `gemini-2.5-flash`
  - кандидат на более мягкий conversational style:
    - `claude-sonnet-4.5`
- Правило для такого сравнения:
  - голос, prompt и tool_ids должны быть одинаковыми;
  - `tts.model_id` оставить:
    - `eleven_flash_v2_5`
  - менять только `llm`.
- На следующем цикле сравнивать не “на слух вообще”, а по фиксированным критериям:
  - время до первого осмысленного ответа;
  - перебивает ли пользователя;
  - не схлопывает ли ветку
    - `интересно -> пока не используем`;
  - как ведёт себя на просьбе объяснить подробнее;
  - насколько чисто проходит `send_sms_info`, `call_log` и финальный close.
- Для подготовки payload под новый LLM без ручного редактирования большого JSON теперь добавлен локальный helper:
  - `scripts/prepare_eleven_llm_variant.sh`
- Для быстрой подготовки полного compare-набора добавлен wrapper:
  - `scripts/prepare_eleven_llm_compare_variants.sh`
- Для безопасного применения payload в lab branch добавлен helper:
  - `scripts/apply_eleven_agent_payload.sh`
- Для применения payload через рабочий `ssh ai-core-prod-147` и чтение ключа из серверного `.env.callcenter` добавлен helper:
  - `scripts/apply_eleven_agent_payload_via_server_env.sh`
- Он берёт текущий `response.json`/snapshot branch-а и собирает минимальный Update Agent payload:
  - сохраняет существующие:
    - `conversation_config`
    - `platform_settings`
    - `workflow`
  - меняет только:
    - `conversation_config.agent.prompt.llm`
    - `version_description` при необходимости.
  - дополнительно автоматически удаляет:
    - `conversation_config.agent.prompt.tools`
    потому что ElevenLabs `Update agent` отвергает payload, где одновременно есть и:
    - `tool_ids`
    - `tools`
- Пример:
  - `scripts/prepare_eleven_llm_variant.sh .runtime/eleven_lab_flash_return_2026-06-16/response.json gemini-2.5-flash .runtime/eleven_lab_llm_compare_gemini_2026-06-16/payload.json "Lab LLM compare: GPT-4.1 -> Gemini 2.5 Flash"`
- Дальше этот payload нужно отправлять в ElevenLabs через:
  - `Update agent`
  - с `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - не в live `Main`, а только в lab-ветку.
- Отдельный runbook для этого цикла:
  - `docs/checkpoints/2026-06-16_ELEVEN_NATURALNESS_LLM_COMPARE_RUNBOOK.md`
- Важная защита:
  - helper по умолчанию целится в `lab_naturalness_2026_06`;
  - apply в live `Main` он блокирует, если явно не выставлен:
    - `ALLOW_MAIN_BRANCH_APPLY=1`
- Практический путь на сейчас:
  - локально выпускать PATCH;
  - ключ аккуратно читать с сервера из `.env.callcenter` через SSH alias, а не копировать руками в команды.
- Дополнительная защита от тихих фейлов:
  - если ElevenLabs отвечает ошибкой уровня:
    - `unprocessable_entity`
  helper `scripts/apply_eleven_agent_payload.sh` теперь завершает команду с ошибкой и печатает короткий `detail`, вместо ложного `success`.
- Текущее состояние LLM compare-cycle:
  - baseline:
    - `gpt-4.1 + eleven_flash_v2_5`
  - Gemini lab-version уже опубликована:
    - `agtvrsn_3901kv89xcg3fnntrp2zwbjt0xcb`
  - Claude lab-version тоже уже опубликована:
    - `agtvrsn_8301kv8adscff0sb23dwjcmvcxb1`
  - следующий шаг:
    - одинаковый branch-targeted self-test на обеих версиях

## Обновление 2026-06-16 по V3-balance cycle в lab

- После первого V3-теста стало ясно, что проблема не в том, что `eleven_v3_conversational` вообще непригоден, а в том, что его нужно отдельно балансировать под наш телефонный сценарий.
- На compact-prompt lab-state сначала был V3 self-test:
  - `conv_2601kv7yka71f5qan6hczca1ttj1`
  - version:
    - `agtvrsn_5401kv7yk01zertthrww7x0jt5n3`
- Он показал:
  - opener уже правильный;
  - но первый ответ после `Алло!` шёл слишком долго:
    - `LLM TTFB ≈ 3.07s`
- После этого в lab внесён balance-patch:
  - version:
    - `agtvrsn_1301kv7ywxgffw3sjg90zfd283av`
  - настройки:
    - `tts.model_id = eleven_v3_conversational`
    - `speed = 1.08`
    - `turn_timeout = 1.4`
    - `turn_eagerness = normal`
    - в `client_events` добавлен `interruption`
- Контрольный manual self-test:
  - `conv_7601kv7yxe4zfb5tbkbh5hwp53ky`
- По нему подтверждено:
  - первый agent-turn ускорился резко:
    - `~3.07s -> ~0.53s`
  - обычные средние ходы держались примерно в окне:
    - `~0.54–0.60s`
  - agent стало легче перебивать живым голосом;
  - V3 стал звучать живее без мгновенного развала логики.
- Одновременно найден новый остаток:
  - agent всё ещё мог слишком растягивать explain-turn;
  - после `send_sms_info` пытался сказать лишний хвост:
    - `Могу чем-то ещё...`
- Поэтому сверху внесён ещё один prompt-follow-up:
  - текущая верхняя lab-version:
    - `agtvrsn_8501kv7z35n9eggamnvq4qe8ygwe`
  - в ней закреплено:
    - после `send_sms_info` только короткое подтверждение и закрытие;
    - без `Могу чем-то ещё...`;
    - explain-turn максимум `2` коротких предложения и `1` короткий вопрос.
- Практически это значит:
  - лучший текущий lab-кандидат теперь уже не softened Flash, а новый V3-balance state;
  - но tiny canary ещё нельзя включать без ещё одного self-test именно на version:
    - `agtvrsn_8501kv7z35n9eggamnvq4qe8ygwe`

## Обновление 2026-06-16 по continuity-validation

- После stress-test и continuity-fix текущая верхняя lab-version теперь:
  - `agtvrsn_8701kv8113z8ebps89308e2yfe8h`
- Проверочный длинный self-test:
  - `conv_8801kv813p1qetr8n3tbcw0cfz4e`
- По нему подтверждено:
  - stale `no_answer` больше не ломает длинный живой разговор;
  - repeated-detail ветка уже не скатывается в тупой SMS-loop;
  - разговор дошёл до нормального человеческого исхода:
    - `manager_call`
    - `call_manager`
  - `call_log` уже пишет корректный текущий `conv_*`.
- Что осталось:
  - если user перебивает самый первый кусок opener в самом начале звонка, agent всё ещё может начать с короткого fragment `Здравствуйте, я...`, а потом уже дать полный fixed opener;
  - это не критический развал, но следующий точечный фронт теперь именно этот early-opener interrupt case.

## Обновление 2026-06-16 по early-opener interrupt fix

- После continuity-validation в lab дополнительно включена конфигурация:
  - `disable_first_message_interruptions = true`
- Новая верхняя lab-version:
  - `agtvrsn_3601kv81fnbbf4rvz38gy18czswx`
- Проверочный test-call:
  - `conv_1201kv81g2tgfpfr2ge32khc5qg2`
- По нему подтверждено:
  - ранний opener-fragment на первом ходе ушёл;
  - agent сразу дал полный fixed opener;
  - стартовый double-`Алло?` сценарий уже не ломает вход в разговор.
- Что осталось теперь:
  - mid-turn interruption polishing:
    - иногда в середине разговора ещё появляются короткие fragments вроде `Вам...` или `Липолонг — это оригинальный...`;
  - это уже не поломка сценария, а следующий слой качества речи.

## Обновление 2026-06-16 по отдельной ветке naturalness-lab

- Для настройки более “человечного” разговора теперь выделен отдельный контур, чтобы не ломать боевой `Main`.
- Рабочая экспериментальная ветка в ElevenLabs:
  - `lab_naturalness_2026_06`
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
  - стартовая version:
    - `agtvrsn_0401kv7waz0sfae92b77pgjhmcqf`
- Она создана от текущего live `Main`:
  - `Main branch_id = agtbrch_7801kgybyg9nesrbv64y078pazq0`
  - source live version:
    - `agtvrsn_9001kv0k051efpr84vwwttz6kthj`
- Текущее правило работы:
  - naturalness / voice / turn-taking эксперименты делать только в `lab_naturalness_2026_06`;
  - боевой `Main` считать read-only, кроме emergency-fix;
  - сначала manual self-tests на себе;
  - tiny canary только после self-tests без регрессий по:
    - exact opener;
    - `абонент` hard-stop;
    - single rescue;
    - premature hangup.
- Уже выполнен первый реальный lab-cycle:
  - baseline:
    - `conv_1201kv7wpw78e53s5mgkc8rcwpa6`
  - после turn patch:
    - `conv_7701kv7wwz1yesgvhynmn6b5tpb2`
  - после prompt naturalness patch:
    - `conv_7701kv7x2m70f5fata09r7rcx6et`
- Текущая lab version после этого цикла:
  - `agtvrsn_7001kv7x1ztdfpnth8rw6rjmjbnh`
- Что уже улучшилось в lab:
  - средние ответные паузы стали короче;
  - второй ход agent стал менее скриптовым;
  - `not_target` ветка проходит чище.
- Следующий lab-фокус:
  - voice/TTS naturalness, а не новый большой prompt-перепис.
- Этот voice-cycle уже проведён:
  - V3 test:
    - `conv_0001kv7xbt11em1akwnvn60g1w52`
    - version:
      - `agtvrsn_7501kv7xb334emqtt4rvz06wq4zm`
  - Flash recovery:
    - `conv_6701kv7xf23aevv9ehmw2w5ns2b5`
    - version:
      - `agtvrsn_5001kv7xeea2ef7smebsma02kaek`
- Практический вывод после фактических self-tests:
  - `eleven_v3_conversational` в текущем контуре дал поведенческий регресс;
  - лучший текущий lab-state после voice-cycle — softened `eleven_flash_v2_5`, а не V3.

## Обновление 2026-06-12 по дожиму после короткого отказа

- live-логика после фраз
  - `нет`
  - `не надо`
  - `не нужно`
  - `неинтересно`
  развёрнута обратно в режим дожима, а не мгновенного завершения.
- текущая live version:
  - `agtvrsn_0901ktxsrethemqr4prhkw701wr2`
- теперь правило такое:
  - такой ответ не финальный по умолчанию;
  - сначала один короткий уточняющий вопрос;
  - если контакт релевантный — один rescue-move:
    - SMS,
    - callback менеджера,
    - или одна короткая value-line;
  - если это вообще не их направление — `not_target`;
  - если после уточнения и одного rescue-move всё равно отказ — `refusal_soft`, короткое закрытие, без третьего круга.
- это изменение внесено по прямой обратной связи от live-продажи.
- новый test-call на этой версии ещё не запускался.
- локальная точка отката для этой версии сохранена в:
  - `/home/max/n8n_ai_call_center/backup/2026-06-12_live_agent_restore_point`

## Обновление 2026-06-12 по `row_9` и refusal-fix

- одиночный live-call по `row_9` подтвердил, что opener уже звучит именно так:
  - `Здравствуйте. Мы официальный представитель липолитика ЛипоЛонг, звоним по поводу сотрудничества для косметологов. Вам это в принципе интересно?`
- conversation:
  - `conv_8601ktxqpc9ten2br2wktr460qbb`
- что показал звонок:
  - раннего rescue до opener нет;
  - opener стартует быстро и в нужной wording-форме;
  - но на короткое `Нет` агент ещё сделал лишний follow-up:
    - `Поняла, уточню — вы не работаете с инъекционной косметологией или просто сейчас не актуально?`
  - после второго `Нет` agent ещё попытался сказать spoken-closing line.
- после этого поверх live внесён новый refusal-fix:
  - промежуточная version:
    - `agtvrsn_5001ktxqwz6jer28593yds2asped`
  - она была слишком жёсткой и потом отменена по обратной связи.
- актуальная текущая live version выше:
  - `agtvrsn_0901ktxsrethemqr4prhkw701wr2`
- значит этот блок важен как история причины, но не как текущая цель поведения.

## Обновление 2026-06-12 по wording opener и compact second-turn

- текущая live version:
  - `agtvrsn_6301ktxp7b4cezb8mc8pba7fxyq9`
- fixed opener теперь закреплён в точной формулировке:
  - `Здравствуйте. Мы официальный представитель липолитика ЛипоЛонг, звоним по поводу сотрудничества для косметологов. Вам это в принципе интересно?`
- после opener в prompt добавлен отдельный compact-guard:
  - второй ход максимум `2` коротких предложения;
  - максимум `1` простой вопрос;
  - вместо абстрактного правила теперь даны короткие живые шаблоны для:
    - нейтрального/мягко-позитивного ответа;
    - вопроса `о чём звонок`;
    - занятости;
    - живого посредника.
- то есть следующий слой теперь должен звучать не как длинное объяснение, а как короткий перевод к следующему шагу.
- патч подтверждён обратным `GET` live-агента через relay-host.
- новый одиночный test-call после этой конкретной правки ещё не запускался.

## Обновление 2026-06-12 по `row_8`

- одиночный human-case на `row_8` подтвердил текущую live version:
  - `agtvrsn_8901ktxmrb3afycrp3qt18caaz4y`
- transcript:
  - user:
    - `Добрый день, клиника «Леса мечты». Меня зовут Екатерина.`
  - agent:
    - `Здравствуйте. Мы официальный представитель ЛипоЛонг, звоним по поводу сотрудничества для косметологов. Вам это в принципе интересно?`
- это значит:
  - ранний rescue до opener больше не вылез;
  - короткий opener стартует как нужно после живого ответа.
- то есть текущий вход в human-dialogue на этом слое подтверждён.

## Обновление 2026-06-12 по pre-opener rescue guard

- текущая live version:
  - `agtvrsn_8901ktxmrb3afycrp3qt18caaz4y`
- в prompt закреплено правило:
  - `Алло, меня слышно? Вы тут?` нельзя использовать до fixed opener вообще;
  - даже если до этого слышны `...`, шум, короткая пауза или слабый ASR-фрагмент.
- одиночный test-call по `row_7` показал:
  - voicemail отработан молча;
  - `call_log` + `end_call` прошли без spoken-message;
  - ранний rescue не появился.
- что ещё не подтверждено:
  - human-case на этой новой version;
  - его нужно добрать следующим одиночным звонком по следующему номеру по порядку.

## Обновление 2026-06-12 по короткому opener

- текущая live version:
  - `agtvrsn_4501ktxm8jppehds9her8yamry5n`
- fixed opener укорочен до:
  - `Здравствуйте. Мы официальный представитель ЛипоЛонг, звоним по поводу сотрудничества для косметологов. Вам это в принципе интересно?`
- одиночный test-call по `row_6` подтвердил:
  - новый opener реально звучит в live transcript;
  - мгновенного перебивания, как на `row_5`, уже не произошло.
- но проявился смежный дефект:
  - если первая реплика клиента распознаётся как `...`,
  - агент до opener всё ещё может выдать `Алло, меня слышно? Вы тут?`,
  - а уже потом перейти к opener.
- значит короткий opener оставляем, а следующий фокус — отсечь ранний rescue до opener.

## Обновление 2026-06-12 по одиночному `row_5`

- на version `agtvrsn_5001ktxj73befn6bgdqbd9sckd9s` сделан один новый одиночный live-call:
  - `conversation_id = conv_0401ktxjmstcfzvs23vga1ah97h5`
  - `user_id = row_5`
  - `request_id = manual.2026-06-12.ROW5.turn1_0`
- технические метрики на первом ответе хорошие:
  - `convai_asr_trailing_service_latency = 0.071s`
  - `convai_llm_service_ttfb = 0.489s`
  - `convai_tts_service_ttfb = 0.124s`
  - `convai_llm_service_ttf_sentence = 0.678s`
- это подтверждает, что сам turn-taking после ответа человека уже ускорен достаточно сильно.
- но сам opener остаётся тяжёлым:
  - агент заходит сразу длинным двухфразным продажным блоком;
  - собеседник перебивает его ещё до нормального развития разговора.
- практический вывод:
  - следующий шаг уже не ещё сильнее душить `turn_timeout`,
  - а укорачивать и упрощать первый spoken block.

## Обновление 2026-06-12 по human-answer latency

- текущая live version:
  - `agtvrsn_5001ktxj73befn6bgdqbd9sckd9s`
- сначала live был поджат с консервативного turn-taking до:
  - `turn_timeout = 1.2`
  - `turn_eagerness = eager`
  - `speculative_turn = true`
- затем отдельно проверен нижний предел `turn_timeout`:
  - попытка поставить `< 1.0` отвергается самим Eleven API;
  - зафиксирован системный лимит:
    - `turn timeout must be -1 or between 1 and 300 seconds`
- поэтому текущая нижняя живая граница теперь такая:
  - `turn_timeout = 1.0`
  - `turn_eagerness = eager`
  - `speculative_turn = true`
- это нужно считать текущим live baseline по скорости ответа после человеческой реплики.

## Обновление 2026-06-06 после `row_11`

- текущая live version:
  - `agtvrsn_7601ktec2xpde6sbn0s4t2heszyz`
- после конфликта на `row_11` global `soft_timeout` больше не используется как активный разговорный rescue-механизм:
  - `turn_timeout = 2.0`
  - `soft_timeout_config.timeout_seconds = -1.0`
  - `soft_timeout_config.message = "Алло, меня слышно? Вы тут?"`
- это сделано специально, чтобы rescue-вопрос не выстреливал в pre-human фазе и не ломал `human-answer gate`
- rescue-вопрос теперь должен жить только как prompt-правило:
  - после явного живого ответа;
  - после уже сказанного opener;
  - при следующем ходе с `...`/тишиной без осмысленного ответа
- в live tool schema `call_log` добавлено каноническое поле:
  - `conversation_id`
- и `conversation_id`, и `eleven_conv_id` теперь привязаны к:
  - `system__conversation_id`
- параллельно live workflow `kZSdJrsAHWWIC2l6 | ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` синхронизирован с локальной нормализацией malformed `conv_*`
- новый разговор после этих правок ещё не запускался; подтверждение нужно получить на следующем одиночном тесте по `row_12`.

## Обновление 2026-06-06 по слову `абонент`

- текущая live version после этой hardening-правки:
  - `agtvrsn_4301ktee0x3kf8es9y3f950rjzr8`
- в machine/message-service логике закреплено отдельное жёсткое правило:
  - любые сервисные фразы со словами
    - `абонент`
    - `абоненту`
    - `абонентам`
    нужно сразу трактовать как автоответчик / message-service
- примеры, зашитые в live prompt:
  - `что передать абоненту?`
  - `что бы вы хотели передать абоненту?`
  - `что сказать абоненту?`
  - `я передам абоненту`
  - `если абонент захочет с вами связаться`
- в этих кейсах agent не должен:
  - продавать;
  - уточнять;
  - оставлять callback message;
  - давать контакт менеджера;
  - продолжать разговор
- нужное поведение:
  - сразу `call_log(no_answer|busy)`
  - затем silent `end_call`
- новый звонок после этой правки ещё не запускался.

## 1. Что здесь важно

В ElevenLabs находится живая боевая личность агента.

Если задача связана с:
- темпом речи;
- задержками;
- перебиваниями;
- первой фразой;
- реакцией на `алло`, `не слышу`, `о чем звонок`;

то основной объект правки находится именно здесь.

## 2. Что трогать можно

Можно менять осторожно:
- system prompt;
- LLM-модель;
- TTS-модель;
- speed;
- turn timeout;
- turn eagerness;
- backup LLM configuration;
- правила перебивания.

Но безопасный порядок теперь такой:
- сначала делать правки на отдельной test/staging-ветке ElevenLabs;
- только после проверки переводить `Main` в live;
- не править `Main` напрямую, если задача затрагивает `tool_ids`, `call_log` или смешанное состояние `tool_ids + tools`.

## 3. Что трогать нельзя без отдельного решения

- пустой `first_message`, если задача не про механику `human-answer gate`
- номер телефона
- SIP/provider bindings
- tool URL без необходимости
- `voice_id`, если нет отдельного указания

## 4. Что уже настроено

- stable live-ветка ElevenLabs: `Main` (`agtbrch_7801kgybyg9nesrbv64y078pazq0`) и сейчас она получает `100%` live traffic;
- отдельная test/staging-ветка для экспериментов: `staging-safe-test-2026-04-25` (`agtbrch_6001kq1w2xtkfp8sp9fgkxejm3t9`) и она держится на `0%` live traffic;
- live-agent работает через `human-answer gate`;
- `first_message = ""`;
- первая живая реплика агента должна сразу быть полным business-opener;
- до живого ответа человека продажный opener не запускается;
- после живого ответа человека текущий target-opener должен быть таким:
  - `Здравствуйте, наша компания является официальным представителем липолитика премиум класса ЛипоЛонг, предлагаем вам сотрудничество с нашей компанией на выгодных условиях. А еще, сотрудничая с нами, вы можете быть уверены на 100%, что получаете оригинальную продукцию и не рискуете попасть на подделку`
  - затем короткое:
    - `Вам это в принципе интересно?`
- включены built-in tools `skip_turn` и `voicemail_detection`;
- live-agent уже ужат по ожиданию:
  - `2026-05-26` live `Main` уже переведён на `turn_timeout = 4.0`;
  - целевое правило после машинной фразы / unavailable / message-service: ждать не дольше `5` секунд и завершать без spoken callback;
  - целевое правило на длинных гудках: обрывать примерно после `5` гудков без живого ответа;
  - после opener без ясного ответа ждать около `4` секунд
- добавлен absolute pre-human cap:
  - не держать линию дольше примерно `20` секунд до первой осмысленной человеческой реплики;
  - непрерывные гудки, queue-loop и hold music не продлевают это окно;
- consent/recording-фразы вида `Продолжая разговор, вы соглашаетесь...` считаются машинным приветствием и не должны запускать opener;
- фразы `абонент сейчас не может ответить / телефон занят / недоступен` считаются машинной недоступностью и не должны получать ответную речь;
- отдельное жёсткое правило: сервисная фраза со словом `абонент` = автоответчик/помощник; не анализировать как человека, сразу завершать после `call_log`;
- название клиники, компании, бренда, города или отдела само по себе не считается достаточным live-human сигналом;
- брендовые приветствия, слоганы и partial ASR fragments вроде `клиника ...`, `город Москва ...`, `спасибо за звонок ...` требуют ещё одного чистого человеческого ответа; если его нет, агент должен остаться в waiting mode и затем завершить `no_answer`;
- literal ASR-маркеры `музыка`, `music`, `...`, дыхание, одиночное ругательство после долгих гудков и другие non-directed fragments не считаются human-answer сигналом и не должны запускать opener;
- текущий LLM/TTS стек: `gpt-4.1 + eleven_flash_v2_5 + Elena Gromova`;
- отдельное latency-tuning состояние на `2026-05-26`:
  - `tts.optimize_streaming_latency = 2`
  - live prompt уплотнён с `~18.1k` до `~5.5k` символов
  - цель: сократить паузу после короткого живого ответа человека, не возвращая старые перебивания
- `2026-06-06` по живому human-answer кейсу `conv_2701ktdzmjz7fxqrmfczhea65r56` подтверждено:
  - основная видимая пауза шла не из LLM/TTS, а из turn-taking окна;
  - backend уже был быстрым:
    - `ASR trailing ~= 0.185s`
    - `LLM TTFB ~= 0.476s`
    - `LLM first sentence ~= 0.574s`
    - `TTS TTFB ~= 0.351s`
  - поэтому live `Main` поджат маленьким безопасным шагом:
    - `turn_timeout: 4.0 -> 3.2`
    - `turn_eagerness = normal`
    - `speculative_turn = false`
  - новая live version после этого:
    - `agtvrsn_4401kte0xffsfm1rnq9bbtajj65y`
  - цель этой правки: сократить ощущаемую задержку без возврата старого агрессивного режима с перебиваниями.
- `2026-06-06` следующий живой тест после этого trim уже подтвердил эффект:
  - разговор `conv_8401kte14mqmeetatxqfh40cqjqv`
  - user `Алло!` на `1s`
  - agent opener уже на `2s`
  - субъективная пауза после ответа сократилась примерно до `~1s`
- Но в той же ветке `human -> ... -> no_answer` всплыл новый traceability-regression:
  - `call_log` ушёл не с текущим `conv_8401...`, а с мусорным `conv_65e2e2e7e2e2e7e2e2e7e2e2e7e2e2e7`
  - значит следующий фронт уже не latency, а корректная сборка `eleven_conv_id` именно в human-silence ветке.
- `2026-06-06` по новой продуктовой правке логика human-silence изменена:
  - если после opener и уже подтверждённого live-human ответа около `3` секунд нет осмысленного ответа, agent должен один раз спросить:
    - `Алло, меня слышно? Вы тут?`
  - это сделано не только prompt-правилом, но и технически через:
    - `turn.soft_timeout_config.timeout_seconds = 3.0`
    - `turn.soft_timeout_config.message = "Алло, меня слышно? Вы тут?"`
    - `max_soft_timeouts_per_generation = 1`
  - исключение действует только для human-ветки после opener;
  - на machine/IVR/voicemail/screening/music/ringback этот rescue запрещён;
  - затем правило ужесточено ещё на один шаг:
    - после rescue-вопроса при новой тишине около `2` секунд agent обязан завершить звонок;
    - rescue-вопрос нельзя повторять второй раз и нельзя перефразировать повторно;
  - затем первое окно тишины тоже ужато с `~3` до `~2` секунд;
  - итоговая схема теперь:
    - `~2s silence after opener -> one rescue question -> ~2s silence -> call_log(no_answer) -> silent end_call`
  - новая live version после этой уточняющей правки:
    - `agtvrsn_9401kte963xcf2j87t1wervbdtv5`
- `2026-06-06` первый живой тест этой схемы по `row_11` показал важный нюанс:
  - разговор `conv_1301kte9dps8ejfvk7fzy4zstvxs`
  - rescue-вопрос действительно не повторяется;
  - но `soft_timeout_config` срабатывает глобально, а не только после opener;
  - из-за этого на первом user `...` rescue прозвучал слишком рано, ещё до нормального подтверждённого human-answer;
  - затем после `Алло?` agent уже дал opener и дальше после второго `...` корректно сделал:
    - `call_log(no_answer)`
    - silent `end_call`
  - вывод:
    - правило `one rescue only` работает,
    - но реализация через global `soft_timeout` конфликтует с `human-answer gate`
  - значит следующий шаг уже не новый звонок, а правка механики rescue так, чтобы она жила только в post-opener/human phase.
- В том же `row_11` снова подтвердился traceability-дефект в human-silence ветке:
  - в `call_log` ушёл не текущий `conv_1301kte9dps8ejfvk7fzy4zstvxs`,
  - а мусорный `conv_8e2e7e7e7e7e4e7e8e7e7e7e7e7e7e7e`.
- anti-repeat правила в prompt;
- реакция на `алло / не слышу / что / о чем звонок / кто вы / где вы`.
- жёсткий запрет на реплики:
  - `Здравствуйте. Чем могу быть полезна?`
  - `Я вас слушаю`
  - `Я вас слушаю, вы на связи? Чем могу помочь?`
  - `Вы на связи?`
  - `Извините, если не вовремя. Вам удобно сейчас поговорить?`
  - `Я вас слушаю, можете говорить. Чем могу помочь?`
  - `Продиктуйте, пожалуйста, почту`
  - `Готова записать почту`
  - `Отправим информацию на почту`
  - `Подскажите, вы принимаете решения по закупкам?`
  - `Вы занимаетесь закупками или могу поговорить с ответственным специалистом?`
  - `Абонент сейчас не может ответить. Попробую связаться позже.`
- правило по закупкам:
  - вопрос про ответственного за закупки допустим только если собеседник сам сказал, что он не принимает решения или просит связаться с тем, кто занимается закупками;
- правило по message-service:
  - фразы в стиле `Я передам это абоненту`, `Если абонент захочет с вами связаться`, `Какие-либо подробности желаете рассказать?`, `Что передать?`, `Это всё?` трактовать как auto-answer/message-service;
  - агент не должен оставлять callback-месседж, отвечать на уточнения электронного помощника, вести qualification или sales-pitch;
  - нужное поведение: сразу `call_log` с `call_result=no_answer`, `next_step=callback`, короткой пометкой `Автоответчик/электронный помощник: сообщение не оставляли, звонок завершен сразу`, затем `end_call`;
  - на `2026-05-22` прямой API-доступ к ElevenLabs из текущего окружения заблокирован `302/403`, поэтому эту правку нужно внести через доступный ElevenLabs UI/API и подтвердить ручным voicemail/SIP тестом;
- отдельное правило по intermediary-линии:
  - `я передам ответственному специалисту`, `оставьте контакт`, `мы передадим информацию`, `я только передам` считать полезным handoff-контактом только если это явно живой человек, а не screening/service-шаблон;
  - не превращать это в длинный sales-диалог;
  - оставлять один короткий контакт и логировать как `send_kp_pending_callback`.
  - если линия повторяет шаблонные service-фразы вроде `в течение какого времени нужно дать ответ`, `нужно передать ещё что-то`, `что-то хотите добавить`, `я всё передам абоненту`, `зафиксировал информацию`, это уже не полезный handoff, а screening/intermediary assistant; в таких кейсах agent должен не продолжать диалог, а быстро логировать `no_answer/busy` и завершать звонок.
- отдельное правило по тишине и `...`:
- если после соединения или после opener в transcript идут только `...`, silence markers или пустые non-semantic куски;
- agent не должен говорить длинные service-фразы вроде `Пожалуйста, подскажите, вы на связи? Могу продолжить разговор.` или `Вы меня слышите? Если удобно, дайте знать, чтобы я могла продолжить.`;
- новое исключение:
  - если это уже подтверждённый live-human после opener, допускается ровно один короткий rescue-вопрос:
    - `Алло, меня слышно? Вы тут?`
- если примерно через `2` секунды после opener нет осмысленного ответа, сначала задаётся этот rescue-вопрос;
- если после него ещё около `2` секунд всё ещё нет осмысленного ответа, нужное поведение:
  - `call_log(no_answer)`
  - silent `end_call`.
- rescue-вопрос нельзя задавать второй раз.
- обязательное уточнение имени собеседника после подтверждения релевантности;
- follow-up сценарий без почты и без `@username`;
- агент не должен собирать, диктовать или перепроверять email-адреса;
- если клиент просит `на почту`, live-flow должен переводить его в SMS/manager contact/callback, а не зависать на email-диктовке;
- правило `на этот номер` -> использовать `system__called_number`, не пересобирать номер из речи;
- активные live-tools: `context_fetch`, `call_log`, `send_sms_info`, `end_call`.
- stable live `call_log` сейчас привязан к валидному relaxed tool id `tool_2201ktbptaagfqxa8f713g76dd6q`;
- на stable live нельзя возвращать жёсткую dynamic-variable schema для `call_log`, пока ручные SIP/manual tests не гарантируют наличие `lead_id`, `request_id`, `source_record_key`, `phone_primary` и других runtime-полей уже на старте звонка;
- `2026-06-04` после реального voicemail-case `conv_3301kt8tj8vyftq97vwbc0jn7c96` live prompt дополнительно ужесточён:
  - bare `call_log` с одними `call_result / next_step / notes_short` теперь явно запрещён;
  - в финальном `call_log` на `voicemail / no_answer / busy / screening` обязательно должны быть:
    - `lead_id`
    - `caller`
    - `phone_primary`
    - `source_record_key`
    - `company_name` / `contact_name` при наличии
    - `eleven_conv_id` как реальный conversation id, а не literal `system__conversation_id`
  - если первая tool-попытка не содержит identity package, agent должен перегенерировать `call_log` правильно, а не завершать звонок с дырявой трассировкой;
  - после voicemail/message-service нельзя произносить `Спасибо, перезвоним позже.` и вообще нельзя оставлять spoken-farewell: только `call_log` и silent `end_call`.
- `2026-06-05` это уже подтверждено на новом live-тесте `conv_0601ktbh7vvbf398yp0zbpw1me8d`:
  - spoken-farewell действительно ушёл;
  - `end_call` был вызван с пустым `system__message_to_speak`.
- Но на том же тесте осталось расхождение по tool usage:
  - agent всё ещё передал `eleven_conv_id = system__conversation_id` literal-значением;
  - bridge после re-activation не отрезал это так жёстко, как ожидалось;
  - поэтому после теста был сделан ещё один live patch уже в `Main`:
    - в prompt отдельно зафиксировано, что `call_log` обязан включать `phone_primary` и `source_record_key`;
    - `eleven_conv_id` обязан быть реальным `conv_*`, а не literal `system__conversation_id`;
    - если literal `system__conversation_id` появляется в draft tool-call, agent должен перегенерировать `call_log` до корректного вида.
  - дополнительно в live tool-schema `call_log` добавлены отсутствовавшие поля:
    - `phone_primary`
    - `source_record_key`
  - новая live version после этого patch:
    - `agtvrsn_6501ktbptasbfm2btq7dfq1mc16y`
  - следующий шаг теперь уже не в новый prompt-патч, а в один одиночный live-test для проверки:
    - дошли ли `phone_primary` и `source_record_key` до webhook-body;
    - стал ли `eleven_conv_id` реальным `conv_*`.
- `2026-06-05` такой одиночный test действительно был выполнен, но оказался нерелевантным для проверки schema-fix:
  - разговор `conv_7901ktbqpbewfksb5d807a721v3v` уже шёл на новой live version `agtvrsn_6501ktbptasbfm2btq7dfq1mc16y`;
  - однако transcript состоял только из одной пользовательской фразы:
    - `Трехэтажный дом.`
  - затем линия завершилась как `Client disconnected: 1000`;
  - agent не дошёл до `call_log`, поэтому тест не подтвердил и не опроверг новую schema/tool-правку.
- Затем по `row_5` и `row_6` был добит именно `eleven_conv_id`:
  - на `row_5` machine-path уже корректно записал `lead_id`, `source_record_key` и `phone_primary`, но `eleven_conv_id` ещё ушёл как `conv_5`;
  - после этого live `Main` был дополнительно усилен антипримером:
    - запрещены `conv_5`, `conv_6` и любые сокращённые `conv_*`, собранные из `row_*` или номера;
    - `eleven_conv_id` нужно копировать verbatim из `system__conversation_id`;
  - новая live version после этого patch:
    - `agtvrsn_4801ktbw46wde348tvxnf4ewx54q`
  - следующий одиночный тест `row_6` подтвердил исправление:
    - `conversation_id = conv_5801ktbw5twre5a8srggqhzqh5yv`
    - в `call_log` записался уже правильный полный `eleven_conv_id = conv_5801ktbw5twre5a8srggqhzqh5yv`
    - вместе с ним корректно доехали `lead_id = row_6`, `source_record_key = row_6`, `phone_primary = +79182007944`
  - то есть traceability на machine-path теперь закрыта; незакрытым остаётся только live-human проверка точного двухфразного opener.
- `2026-06-05` следующий одиночный тест по `row_7` показал ещё один edge-case:
  - voicemail-path снова отработал корректно без opener и без spoken farewell;
  - но agent переиспользовал старый `conv_1901...` из prompt-примера вместо текущего `conv_2101...`;
  - после этого буквальный valid-example был убран из live prompt;
  - вместо него оставлено только общее правило формы текущего `conv_*` и отдельный запрет переиспользовать `conv_*` из прошлого звонка, примера, transcript или tool-result;
  - новая live version после этой де-копипаст правки:
    - `agtvrsn_1001ktbys8ftfpys5gykctxrqka5`
  - `2026-06-06` следующий живой тест по `row_8` уже подтвердил, что эта версия реально работает на human-answer кейсе:
    - разговор `conv_2701ktdzmjz7fxqrmfczhea65r56`
    - user: `«Лицо мечты», администратор Ольга, здравств`
    - agent стартовал ровно восстановленным opener-блоком без укорочения;
    - разговор оборвался слишком рано (`Client disconnected: 1000`), поэтому `call_log` этим кейсом не проверился, но human-opener подтверждён вживую.
- sales-логика усилена без изменения `first_message`:
  - `не интересно` и `перезвоните позже` не должны завершать разговор автоматически;
  - ближний callback фиксируется с уточнением `первая половина / вторая половина дня`;
  - агент старается закрывать базовые вопросы сам, а не уводить всё на менеджера;
  - при вопросе о противопоказаниях допускается только короткий безопасный ответ и перевод на специалиста при необходимости.
- voice-тюнинг тоже уже применялся точечно:
  - `voice_id` не менялся;
  - безопасно корректировались только `speed`, `stability` и `similarity_boost`;
  - если после такого тюнинга речь становится слишком медленной, сначала откатывать TTS-параметры назад, а не менять `voice_id`.
- текущий Eleven API-хвост:
  - agent-config хранится в смешанном виде `tool_ids + tools`;
  - из-за этого не каждый patch built-in tools проходит через API;
  - prompt и `turn_timeout` править можно, но tool-schema и built-in tool params нужно трогать очень осторожно.

## 5. Что проверять после любой правки

1. Не изменился ли `first_message`.
2. Не съехали ли `tool_ids`.
3. Не изменились ли `voice_id` и номер.
4. Не пропали ли `skip_turn` и `voicemail_detection`.
5. Не вернулись ли старые `turn_eagerness = eager`, `turn_timeout = 3`, `speculative_turn = true`.
6. Не пропали ли `context_fetch`, `call_log` и `send_sms_info` из active tools.
7. Не вернулась ли в prompt логика с `e-mail`, `telegram username` и вопросом про мессенджер в SMS-кейсе.
8. Не начал ли агент говорить поверх IVR, записи разговора, музыки ожидания или гудков.
9. Не отвечает ли агент машинными фразами на `абонент сейчас не может ответить` и похожие сообщения.
10. Не вернулись ли старые opener-фразы про закупки в первый или второй агентский ход.
11. Не уехал ли live traffic с `Main` на экспериментальную ветку.
12. Не появилась ли у `call_log` жёсткая dynamic-variable привязка, которая ломает ручной SIP/manual test ещё до `accepted_time`.
13. Есть ли свежий backup branch/config до live patch.
14. Не разговаривает ли agent с screening/intermediary шаблонами после фраз:
   - `в течение какого времени нужно дать ответ`
   - `нужно передать ещё что-то`
   - `что-то хотите добавить`
   - `я всё передам абоненту`
   - `зафиксировал информацию`
15. Не вернулись ли service-фразы на тишине и `...`:
   - `Пожалуйста, подскажите, вы на связи? Могу продолжить разговор.`
   - `Вы меня слышите? Если удобно, дайте знать, чтобы я могла продолжить.`
16. Не уходит ли voicemail/message-service в spoken-farewell после `call_log`, особенно в фразу `Спасибо, перезвоним позже.`.
17. Есть ли в финальном `call_log` полный identity package:
   - `lead_id`
   - `caller`
   - `phone_primary`
   - `source_record_key`
   - `eleven_conv_id`
18. После re-activation `ELEVEN_TOOL_CALL_LOG_BRIDGE` реально ли webhook обслуживает свежую patched/published version, а не старую runtime-копию.


## 6. Основной риск

Самая опасная ошибка — случайно снести `human-answer gate`, потерять `tool_ids`, сломать состав live-tools или включить на stable live слишком строгую dynamic-variable schema для `call_log`, после чего агент начнет снова говорить в автоответчики, перестанет писать `call_log`, потеряет `context_fetch`, перестанет корректно отправлять SMS через `send_sms_info` или вообще будет рваться сразу после ответа на manual/SIP test.
