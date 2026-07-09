# 2026-07-09: Eleven voice switch matrix и текущий lab-статус

## Актуальное обновление `2026-07-09 14:13 MSK`

### Сделано
- После checkpoint `13:48` повторно проверен последний пустой звонок:
  - `conv_8901kx37myfdef39cqh2n53bqnpf`
  - по direct Eleven API всё ещё:
    - `status = in-progress`
    - `transcript_len = 0`
    - `duration = 0`
    - `version_id = null`
    - `branch_id = null`
  - вывод: не behavioral test, а `sip_pending_no_media` / пустой SIP-хвост.
- Сделан ещё один одиночный SMS-consent self-test:
  - run dir: `.runtime/eleven_sms_log_fastpath_2026-07-09/call_04_sms_fastpath_consent_retry`
  - conversation: `conv_5801kx384fh2e1c9d4je6f4z6j3j`
  - expected version: `agtvrsn_9301kx37gy6zft3te55dangks99m`
  - runtime diagnosis:
    - `sip_pending_no_media`
    - transcript `0`
    - duration `0`
    - outbound request accepted, но media не пошло.
  - вывод: test не засчитывать как проверку агента.
- Сделан simulation probe без live-звонка:
  - run dir: `.runtime/eleven_sms_log_fastpath_2026-07-09/sim_sms_consent_probe`
  - first agent message был корректный opener.
  - tool calls в simulation:
    - `send_sms_info`
    - `call_log`
    - `end_call`
  - `branch_ids_seen = []`, `version_ids_seen = []`.
  - вывод: simulation helper не доказывает поведение lab head `9301`, потому что не подтверждает branch/version targeting; использовать только как слабый ориентир.

### На чем остановились
- Current lab head всё ещё:
  - `agtvrsn_9301kx37gy6zft3te55dangks99m`
- Новый tool прикреплён и виден в agent response:
  - `send_sms_and_log`
  - `tool_5701kx37g3qpf6caa4f09c9bfm8n`
- Backend endpoint жив:
  - `POST /webhook/eleven/tool/send-sms-and-log`
  - dry-run уже дал HTTP `200`.
- Не доказано:
  - реальный SMS-consent path на live media;
  - что при фразе `да, отправьте SMS` агент выбирает именно `send_sms_and_log`, а не старую пару `send_sms_info -> call_log`.

### Что делать дальше
1. Не делать вывод по `call_03` и `call_04`: оба пустые/no-media.
2. Следующий агент должен либо:
   - добиться валидного media self-test на `9301...`, где человек явно говорит `да, отправьте SMS`;
   - либо сначала починить/обойти причину повторяющегося `sip_pending_no_media` на ручных self-tests.
3. Если нужен non-call proof, доработать simulation helper так, чтобы он гарантированно таргетил branch/version `agtbrch_3701...` / `9301...`; текущий simulation без `branch_ids_seen` не годится как доказательство.
4. Live `Main` не трогать до прохождения gates:
   - SMS consent через `send_sms_and_log`;
   - machine/`абонент`;
   - confused user;
   - silence/no-answer.

## Актуальное обновление `2026-07-09 13:48 MSK`

### Сделано
- Создан новый n8n lab workflow для SMS-finalization:
  - file: `workflows/ELEVEN_TOOL_SEND_SMS_AND_LOG_BRIDGE_LAB_DRAFT.json`
  - live workflow ID: `LVYvGh5luQunORKh`
  - webhook: `POST https://www.n-8-n.site/webhook/eleven/tool/send-sms-and-log`
- Workflow делает один backend path:
  - normalize SMS request;
  - Mango SMS send/skip;
  - build call_log row;
  - validate identity;
  - append Google Sheet;
  - return one combined response.
- Перед import сделан backup n8n Postgres:
  - `/home/aicore/n8n-backups/manual/n8n_prod_before_sms_log_fastpath_2026-07-09_10-29-32.sql.gz`
- Local n8n API-key дал `401`, поэтому deployment выполнен через SSH/server CLI:
  - `n8n import:workflow`
  - `n8n publish:workflow`
  - `n8n update:workflow --active=true`
  - restart only `n8n-server-n8n-1`
- Dry-run smoke:
  - HTTP `200`
  - `dry_run=true`
  - `log_dry_run=true`
  - identity complete.
- Попытка добавить `send_sms_and_log` простым agent payload дала head:
  - `agtvrsn_3001kx372f1besksd0cy9t80bq8x`
  - но ElevenLabs не прикрепил новый tool в response.
- По official docs выбран правильный путь:
  - `POST /v1/convai/tools`
- Создан global tool:
  - `send_sms_and_log`
  - `tool_5701kx37g3qpf6caa4f09c9bfm8n`
- Lab branch обновлён через `tool_ids`:
  - current head: `agtvrsn_9301kx37gy6zft3te55dangks99m`
  - tool list теперь содержит `send_sms_and_log`.
- Добавлен hard-ban:
  - не произносить tool names, JSON, `call_log with`, `send_sms_and_log with`, `params_as_json`, `silent`, `skip_turn`.

### Проверки
- `call_01_sms_fastpath_selftest`
  - conversation: `conv_3401kx373nysfxzvf5qdx2nzmy2e`
  - version: `agtvrsn_3001kx372f1besksd0cy9t80bq8x`
  - дефект: spoken `call_log with {...}`.
- `call_02_sms_fastpath_tool_attached`
  - conversation: `conv_5201kx37hp0heyjab4rgkvszgw2f`
  - version: `agtvrsn_9301kx37gy6zft3te55dangks99m`
  - результат:
    - spoken tool text ушёл;
    - repeated refusal закрылся через `call_log` + `end_call`;
    - `call_log` записал строку `'Лиды_обзвон'!A174:AM174`;
    - SMS consent не было, `send_sms_and_log` разговором ещё не проверен.
- `call_03_sms_fastpath_consent`
  - conversation: `conv_8901kx37myfdef39cqh2n53bqnpf`
  - status: `in-progress` на polling timeout;
  - transcript пустой;
  - не засчитывать.

### На чем остановились
- Git branch:
  - `codex/eleven-naturalness-lab`
- ElevenLabs lab branch:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- Current lab head:
  - `agtvrsn_9301kx37gy6zft3te55dangks99m`
- Новый tool:
  - `send_sms_and_log`
  - `tool_5701kx37g3qpf6caa4f09c9bfm8n`
- Боевой `Main` не трогался.

### Что делать дальше
1. Следующий одинарный self-test должен быть только SMS-consent:
   - user: `да, отправьте SMS`;
   - expected: `Да, отправляю.` -> `send_sms_and_log` -> one `end_call`.
2. Если `send_sms_and_log` реально вызвался:
   - сравнить latency с прежним `send_sms_info -> call_log` tail `10-13s`.
3. Затем gates:
   - machine/`абонент`;
   - confused user;
   - silence/no-answer.
4. До прохождения gates не переносить в live `Main`.

## Актуальное обновление `2026-07-09 13:18 MSK`

### Сделано
- Валидно проверен `5701...` на SMS-сценарии:
  - version: `agtvrsn_5701kx34qma3em39qcqzyrjjjba3`
  - conversation: `conv_4201kx356xmveetawnn4zfjdxcwf`
  - opener правильный;
  - SMS отправилась;
  - `call_log` записался с реальным `conversation_id`;
  - дефект: перед `send_sms_info` не прозвучало `Да, отправляю.`;
  - tool-tail до финальной фразы около `10s`.
- Проверены документы ElevenLabs:
  - `soft_timeout` действительно предназначен для filler при долгой генерации;
  - рекомендуемый старт в docs: около `3.0s`;
  - `pre_tool_speech` documented для MCP/tool configuration overrides; для наших webhook-tools через branch payload его нельзя считать надёжным.
- Опубликован `1801...`:
  - version: `agtvrsn_1801kx35czwsevk89sb016dthhjt`
  - добавлены `post_tool_speech`, `pre_tool_speech=force`, system-bound ids.
  - conversation: `conv_9901kx35dfzrfz9vzw5z41gn1wpv`
  - результат плохой: на `Нет, не интересно` agent сразу сделал `call_log(not_target)` и закрыл.
- Опубликован `5401...`:
  - version: `agtvrsn_5401kx35h6wge41sm97fs0vpr79e`
  - восстановлен soft-refusal rescue.
  - conversation: `conv_5301kx35hp58f75b17e5dbn0ww77`
  - дожим после `Нет, не интересно` сработал;
  - дефект: до opener агент сказал `Алло?` и произнёс tool-pseudo text `skip_turn({...})`.
- Опубликован `6201...`:
  - version: `agtvrsn_6201kx35ptx2f7brc2b4dge4sjcv`
  - добавлен pre-opener no-linecheck/no-tooltext guard.
  - `call_24` был невалиден: `sip_pending/no media`.
  - валидный self-test:
    - conversation: `conv_9801kx35ydp7f4wa48nca6284e7b`
    - opener правильный;
    - spoken tool pseudo-code нет;
    - первый `Нет` не закрыл звонок, agent сделал SMS-rescue;
    - SMS отправилась;
    - call_log записался;
    - дефект остался: после SMS consent tool-tail около `13s`, pre-tool spoken ack всё ещё не сработал.
- Опубликован `6701...` с `soft_timeout=3.0`:
  - version: `agtvrsn_6701kx362nj4et2s1vpya63vzkht`
  - conversation: `conv_4201kx3635jneqtap5sz4g5dfewh`
  - результат плохой: agent сделал silent `skip_turn` вместо opener, клиент отключился.
- После регрессии `6701...` lab откатан на payload-класс `6201...`:
  - current lab head: `agtvrsn_4701kx3652j2fcvt96htmxfp81h3`
  - это payload-equivalent проверенного `6201...`.

### На чем остановились
- Current lab head:
  - `agtvrsn_4701kx3652j2fcvt96htmxfp81h3`
- Лучший подтверждённый behavioral candidate:
  - payload class `6201...`
  - подтверждён на `conv_9801kx35ydp7f4wa48nca6284e7b`.
- Что хорошо:
  - opener first;
  - нет spoken `skip_turn`;
  - первый мягкий отказ не закрывает звонок;
  - SMS реально отправляется;
  - `call_log` получает реальный `conversation_id` в body.
- Что плохо:
  - нет немедленного spoken ack перед `send_sms_info`;
  - SMS/tool-tail может быть около `13s`;
  - `soft_timeout=3.0` как быстрый фикс отклонён, потому что сломал opener.
- Боевой ElevenLabs `Main` не трогался.

### Что делать дальше
1. Не использовать:
   - `agtvrsn_1801kx35czwsevk89sb016dthhjt`
   - `agtvrsn_5401kx35h6wge41sm97fs0vpr79e`
   - `agtvrsn_6701kx362nj4et2s1vpya63vzkht`
2. Следующий шаг по SMS-tail:
   - не возвращать global soft-timeout вслепую;
   - искать структурное решение:
     - либо backend объединяет `send_sms_info + call_log`;
     - либо отдельная workflow/tool финализация делает логирование без второго LLM/tool-planning хвоста;
     - либо ElevenLabs MCP/config override, если перевод tools с webhook на MCP будет оправдан.
3. Следующие gates перед любым live merge:
   - machine/`абонент`;
   - confused user;
   - SMS consent без длинной мёртвой паузы.

## Актуальное обновление `2026-07-09 12:58 MSK`

### Сделано
- Зафиксирован и запушен checkpoint по `7901`:
  - commit: `bb5ff2b`
  - `agtvrsn_7901kx34220qfm4atb2vvagne10q`
  - pre-opener skip-turn gate убрал late line-check, но в следующем тесте проявил pre-opener filler.
- Self-test `call_18_sms_consent_gate`:
  - conversation: `conv_2901kx34bnwfesm8t15t0232tj6e`
  - результат: bad gate;
  - первое сообщение агента было `...`;
  - затем был micro-fragment `Здравствуйте,...`;
  - вывод: global `soft_timeout_config` может срабатывать до полного opener и ломает правило “opener первым”.
- Опубликован lab-вариант без global softfill:
  - version: `agtvrsn_2001kx34hhssf7zbe84p3k9y53z6`
  - `soft_timeout_config.timeout_seconds = -1`
  - prompt hard-off: до opener запрещены `...`, fillers, partial greeting, line-check.
- Self-test `call_19_no_global_softfill_opener_gate`:
  - conversation: `conv_5801kx34j2x5ea08nxyqa3tkenbe`
  - opener прошёл правильно первым сообщением;
  - pre-opener `...` и `Здравствуйте,...` ушли;
  - SMS consent дошёл до `send_sms_info`, `call_log`, `end_call`;
  - call_log body получил реальный `conversation_id`/`eleven_conv_id`;
  - остались проблемы:
    - tool draft всё ещё может содержать placeholder `conv_current_...`, хотя webhook body заменяет его на реальный id;
    - после согласия на SMS был длинный хвост около `12s` до финального spoken close.
- Опубликован следующий lab head для SMS-ветки:
  - version: `agtvrsn_5701kx34qma3em39qcqzyrjjjba3`
  - добавлено: после явного SMS consent сразу сказать `Да, отправляю.`;
  - затем `send_sms_info` -> silent `call_log` -> `end_call("SMS отправила, хорошего дня.")`;
  - global softfill остаётся выключенным.
- Self-test `call_20_sms_ack_singleclose_gate`:
  - conversation: `conv_7701kx34r36je1vt5wqskthe2tst`
  - невалиден для оценки агента;
  - диагноз: `sip_pending_no_media`;
  - transcript пустой, timing нет, звонок не подтверждает и не опровергает `5701`.
- `scripts/report_eleven_next_variant_advisor.py` исправлен:
  - пустой/in-progress звонок без transcript/timing теперь считается `no_behavioral_transcript`;
  - `ready_for_variant_testing=false`, чтобы не засчитывать SIP/no-media как успешный тест.

### На чем остановились
- Git branch:
  - `codex/eleven-naturalness-lab`
- ElevenLabs lab branch:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- Current lab head:
  - `agtvrsn_5701kx34qma3em39qcqzyrjjjba3`
- Лучший подтверждённый behavioral результат:
  - `agtvrsn_2001kx34hhssf7zbe84p3k9y53z6`
  - opener first стабилен в `call_19`;
  - но SMS-tail ещё был долгий.
- `5701` опубликован, но ещё ждёт валидного разговора, потому что `call_20` был SIP/no-media.
- Боевой ElevenLabs `Main` не трогался.

### Что делать дальше
1. Повторить один валидный self-test на `5701`:
   - сценарий: `Алло` -> интерес -> согласие на SMS;
   - проверить, что сразу звучит `Да, отправляю.`;
   - проверить, что нет обычной речи после `call_log`;
   - проверить, что final close только один.
2. Если `5701` проходит SMS gate:
   - проверить machine/`абонент`;
   - проверить confused user;
   - только потом думать о возвращении post-opener filler, но не global pre-opener softfill.
3. Если повторится `sip_pending_no_media`:
   - разбирать телефонию/SIP отдельно, не считать это prompt-регрессией.

## Актуальное обновление `2026-07-09 12:43 MSK`

### Сделано
- Mini-gate на восстановленном `2101/5301` показал реальный dialogue-flow дефект:
  - version: `agtvrsn_2101kx33s8ctfgwsx19m67hp3997`
  - self-test: `conv_5001kx33x5n9eaw9p5xryd0g4s80`
  - агент сказал pre-opener line-check `Вы на...` после первого `...`;
  - позже снова говорил `Алло?` / `Вы всё ещё на...` после осмысленных ответов;
  - audit: `opener_not_first_agent_message`, `line_check_after_meaningful_post_opener_reply`.
- Собран и опубликован pre-opener skip-turn hard gate:
  - version: `agtvrsn_7901kx34220qfm4atb2vvagne10q`
  - изменения:
    - усилено описание `skip_turn`;
    - добавлен prompt override: до opener любые `Вы на...`, `Алло?`, `Слышно?`, `Да?` запрещены;
    - при `...`, шуме, дыхании, обрывках — `skip_turn` / молчание вместо spoken line-check.
- Self-test:
  - `conv_9701kx342jkcf7tvq6reskjtf4p3`
  - результат:
    - pre-opener wrong-start ушёл;
    - late line-check ушёл;
    - `spoken_tool_pseudocode` нет;
    - real `call_log` / `end_call` есть;
    - `end_call tool was called`;
    - остались только two `long_user_to_agent_gap` по `4s`.
- Next-variant advisor усилен:
  - late line-check теперь blocking fix-before-variant item.

### На чем остановились
- Current lab head:
  - `agtvrsn_7901kx34220qfm4atb2vvagne10q`
- Это лучший текущий lab-кандидат:
  - `gpt-5-mini`
  - `eleven_v3_conversational`
  - `turn_timeout = 1.4`
  - `turn_eagerness = normal`
  - pre-opener skip-turn hard gate
- Не использовать:
  - `agtvrsn_6401kx32y00re3qsenk3ka8t1nea`
  - `agtvrsn_3601kx33n8wme3rs4hb4tn1h1xgn`
  - `agtvrsn_2101kx33s8ctfgwsx19m67hp3997`

### Что делать дальше
1. Не крутить raw timeout ниже `1.4`.
2. Mini test-set на `7901...`:
   - SMS consent;
   - machine/`абонент`;
   - confused user.
3. Если gates проходят:
   - отдельно работать над remaining `4s` long gaps без `eager` и без снижения timeout ниже `1.4`.

## Актуальное обновление `2026-07-09 12:37 MSK`

### Сделано
- Проверен следующий latency-шаг:
  - `turn_timeout = 1.3`
  - `turn_eagerness = normal`
  - version: `agtvrsn_3601kx33n8wme3rs4hb4tn1h1xgn`
  - self-test: `conv_1701kx33nysxez386skz1rmz005g`
- Результат плохой:
  - max gap вырос до `16s`;
  - avg gap вырос до `6.25s`;
  - агент произнёс pseudo-tool текст:
    - `(call_log with appropriate fields)...silent`
    - `(end_call) system__message_to_speak=...`
  - появился helpdesk tail:
    - `Поняла. Могу чем-то ещё помочь?`
- Audit усилен:
  - теперь ловит `call_log with appropriate fields`, `end_call) system__message_to_speak` и standalone `silent` как `spoken_tool_pseudocode`.
- Lab откатан на безопасный payload-класс `5301`:
  - current lab head after rollback: `agtvrsn_2101kx33s8ctfgwsx19m67hp3997`
  - это восстановленный `1.4/normal` payload.

### На чем остановились
- Current lab head:
  - `agtvrsn_2101kx33s8ctfgwsx19m67hp3997`
- Лучший проверенный вариант остаётся:
  - `turn_timeout = 1.4`
  - `turn_eagerness = normal`
  - `gpt-5-mini`
  - `eleven_v3_conversational`
- Не использовать:
  - `agtvrsn_6401kx32y00re3qsenk3ka8t1nea` (`eager`)
  - `agtvrsn_3601kx33n8wme3rs4hb4tn1h1xgn` (`1.3/normal`)

### Что делать дальше
1. Не продолжать уменьшать `turn_timeout` ниже `1.4` без другой защиты.
2. Следующий правильный шаг:
   - mini test-set на текущем `2101/5301`:
     - SMS consent;
     - machine/`абонент`;
     - confused user;
   - либо искать latency не в raw timeout, а в prompt/dialogue-flow для short negative.
3. В live не переносить до прохождения mini test-set.

## Актуальное обновление `2026-07-09 12:29 MSK`

### Сделано
- От безопасного rollback payload `6301/4001` собран controlled вариант:
  - `turn_timeout = 1.4`
  - `turn_eagerness = normal`
  - LLM/voice/prompt не менялись.
- Опубликован lab head:
  - `agtvrsn_5301kx337pqxf01s7m9jkfbspfhs`
- Self-test:
  - `conv_2401kx3387pvf3m9pc6kab9ndr42`
  - результат:
    - opener-first проходит;
    - `spoken_tool_pseudocode` нет;
    - real `call_log` / `end_call` есть;
    - `end_call tool was called`;
    - gap после short negative улучшился:
      - было на `4001`: max `6s`, avg `4.33s`;
      - стало на `5301`: max `4s`, avg `3.0s`.
- Transcript `5301`:
  - `Да.` -> exact opener через `2s`;
  - `Нет.` -> уточнение через `4s`;
  - `Совсем.` -> short filler `Да...`, затем `call_log`, close, `end_call`.

### На чем остановились
- Current lab head:
  - `agtvrsn_5301kx337pqxf01s7m9jkfbspfhs`
- Это лучший текущий lab-кандидат по сравнению с `4001/6301`:
  - latency лучше;
  - opener/tools не сломаны;
  - `eager`-регрессии нет.
- Всё ещё не live-ready:
  - gap после `Нет.` всё ещё `4s`, целимся ниже;
  - нужно проверить SMS consent и machine/`абонент`;
  - нужно на слух оценить, нормально ли воспринимается filler `Да...` перед terminal tool-path.

### Что делать дальше
1. Не трогать `turn_eagerness=eager`.
2. Следующий безопасный latency-шаг:
   - либо попробовать `turn_timeout = 1.3` с `turn_eagerness = normal`;
   - либо оставить `1.4` и проверять SMS/machine gates.
3. Перед переносом в live обязательно mini test-set:
   - hello/opener;
   - short negative;
   - SMS consent;
   - machine/`абонент`.

## Актуальное обновление `2026-07-09 12:24 MSK`

### Сделано
- Уточнён audit single-close:
  - Eleven может показывать `end_call.system__message_to_speak` как отдельную spoken-строку прямо перед `end_call`;
  - если spoken close совпадает с `end_call.system__message_to_speak` и относится к тому же end-call событию, это больше не считается `duplicate_close_before_end_call` и `normal_assistant_speech_after_call_log`.
- Повторно проверены audits:
  - `call_12_terminal_singleclose_from_3601`:
    - `conv_6201kx32j8gmec6t1k7bhbs3es8f`
    - после уточнения остались только long-gap issues;
    - `spoken_tool_pseudocode` нет;
    - opener-first проходит;
    - real `call_log` / `end_call` есть.
  - `call_11_opener_first_hard_gate`:
    - теперь корректно классифицируется как `opener_micro_fragment_before_full_opener`, а не semantic wrong-start.
  - `call_05_turn_latency_allo_recovery_selftest`:
    - single-close ложные флаги сняты;
    - остался latency issue.
- Проверен вариант `turn_eagerness=eager`:
  - version: `agtvrsn_6401kx32y00re3qsenk3ka8t1nea`
  - self-test: `conv_7101kx32yfjre6wr4r2me1sewdpm`
  - результат: регрессия;
  - вернулись `spoken_tool_pseudocode` и `opener_not_first_agent_message`;
  - этот head нельзя продолжать.
- Lab-ветка откатана на безопасный `4001`-payload:
  - current lab head after rollback: `agtvrsn_6301kx331akffqtvrkyfpgz2kq8k`
  - `gpt-5-mini`
  - `eleven_v3_conversational`
  - `turn_timeout = 1.55`
  - `turn_eagerness = normal`
  - `soft_timeout = 1.8`
- Исправлен helper:
  - `scripts/prepare_eleven_turn_latency_allo_recovery_variant.sh`
  - больше не срезает хвост prompt после блока `Turn latency and repeated allo recovery override`.
- Усилен next-variant advisor:
  - `spoken_tool_pseudocode` и `opener_not_first_agent_message` теперь блокируют дальнейшее A/B-тестирование ветки.

### На чем остановились
- Git branch:
  - `codex/eleven-naturalness-lab`
- ElevenLabs lab branch:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- Current lab head:
  - `agtvrsn_6301kx331akffqtvrkyfpgz2kq8k`
- Боевой `Main` не трогался.
- Лучший проверенный класс поведения остаётся `4001/6301`:
  - opener нормальный;
  - real tools есть;
  - pseudo-code в голосе нет;
  - остаток: long gaps / turn-taking overhead.

### Что делать дальше
1. Не использовать `agtvrsn_6401kx32y00re3qsenk3ka8t1nea`.
2. Не включать `turn_eagerness=eager` как быстрый фикс: он дал регрессию.
3. Следующий путь по latency:
   - искать не агрессивный eagerness, а причину, почему `turn_v2 + normal` ждёт до `6s` после короткого `Нет`;
   - рассмотреть `turn_timeout` маленьким шагом или prompt-level fast-path для short negative, но только без spoken pseudo-code.
4. Перед live нужен mini test-set:
   - opener;
   - short negative/refusal;
   - SMS consent;
   - machine/`абонент`.

## Актуальное обновление `2026-07-09 12:16 MSK`

### Сделано
- После восстановления на `agtvrsn_7701kx31xdq3fnxvq5c2a8mwnxkj` сделан self-test:
  - `conv_4201kx326rm4exdt6zb5b2hmj79h`
  - дефект: агент начал не с opener, а ответил на первое слово пользователя `Полная.`;
  - audit теперь ловит это как `opener_not_first_agent_message`.
- Добавлен новый audit gate:
  - `opener_not_first_agent_message`
  - `opener_micro_fragment_before_full_opener`
  - теперь semantic wrong-start и micro-cut opener не смешиваются в один дефект.
- Опубликован opener-first hard gate:
  - `agtvrsn_3601kx32d39nejw8t9jtkx510yve`
  - self-test: `conv_0301kx32djxxe6hregex42hjdzf9`
  - результат: агент начал opener, но первый turn был micro-cut, затем полный opener;
  - real `call_log` и `end_call` tool calls сработали;
  - остались duplicate close / normal speech after `call_log`.
- Поверх `3601...` применён terminal single-close binding helper.
- Current lab head:
  - `agtvrsn_4001kx32hsrbfxxtahfkabsd3a5w`
  - self-test: `conv_6201kx32j8gmec6t1k7bhbs3es8f`
  - результат:
    - `Да.` -> через 2s полный exact opener;
    - `spoken_tool_pseudocode` нет;
    - real `call_log` и `end_call` есть;
    - `eleven_conv_id` и `conversation_id` в call_log заполнены реальным `conv_6201kx32j8gmec6t1k7bhbs3es8f`;
    - остаются `duplicate_close_before_end_call`, `normal_assistant_speech_after_call_log`, long gaps.

### На чем остановились
- Git branch:
  - `codex/eleven-naturalness-lab`
- ElevenLabs lab branch:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- Current lab head:
  - `agtvrsn_4001kx32hsrbfxxtahfkabsd3a5w`
- Боевой `Main` не трогался.
- `4001...` лучше `7701...` по opener-first gate, но ещё не готов к live.

### Что делать дальше
1. Не трогать voice/LLM: оставить `gpt-5-mini + eleven_v3_conversational`.
2. Следующий фокус:
   - убрать normal assistant speech после `call_log`;
   - понять, является ли close перед `end_call` реальным дублем или особенностью отображения `end_call.system__message_to_speak`;
   - уменьшить long gaps / turn-taking overhead.
3. Перед live нужен ещё один test-set:
   - normal hello;
   - refusal/not_target;
   - SMS consent;
   - machine/`абонент`.

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
