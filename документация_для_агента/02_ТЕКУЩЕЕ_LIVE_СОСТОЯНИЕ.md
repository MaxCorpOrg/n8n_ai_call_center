# Текущее live-состояние

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
- Stable live version: `agtvrsn_3301ksfb9p4xf68s90k3by9y677a`
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
  - `tool_8601km62h97qft5b3nfprvxnvdkd`
  - `tool_1701km86jmcpek4rj2j1rbhxqtfr`

Дополнительно подключено:
- pronunciation dictionary: `NnZrxd6lJkbHKqW6w04N`
- version id: `agtvrsn_3301ksfb9p4xf68s90k3by9y677a`
- базовая нормализация бренда: `ЛипоЛонг / LipoLong / lipolong -> липолонг`

## 5. Текущий старт разговора

Сейчас live-agent работает через `human-answer gate`:
- `first_message = ""`
- до живого ответа человека pitch не начинается;
- первая живая реплика агента после ответа человека должна сразу быть полным business-opener.

Текущий business-opener:
- `Здравствуйте, наша компания является официальным представителем липолитика премиум класса lipolong, предлагаем вам сотрудничество с нашей компанией на выгодных условиях.`
- следующим коротким вопросом после opener должно быть:
  - `Вам это в принципе интересно?`
- дополнительный крючок про оригинальность и официальный канал поставки допустим только следующим ходом, а не вместо opener.

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
  - `RELAY_TIMEOUT=8`, `RELAY_RETRY_COUNT=0`, `RELAY_RETRY_DELAY_MS=500` добавлены в `/root/.eleven_outbound_relay.env`;
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

- Live `AUTODIAL_DISPATCHER` читает таблицу:
  - `https://docs.google.com/spreadsheets/d/1kAXIwaa_-rC4MO5vV3mFV-Geha08iL_6pJNCNxlQPAU/edit?gid=199760593#gid=199760593`
  - Drive name: `контакты_косметологов_москва_50`
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
