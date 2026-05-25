# 09. Состояние проекта и последние изменения

## 1) Актуальное состояние (оперативный снимок)
- Проект: `n8n_ai_call_center`.
- Базовая инфраструктура: Ubuntu 24.04 + Docker + Traefik + HTTPS.
- Memory-слой: `postgres_memory` + `postgrest` + таблица `agent_memory`.
- DB UI: `adminer` (через Traefik на 443, с BasicAuth).
- Основной workspace: `media_orchestrator_v1`.
- Telegram media-оркестратор `C8Wmmjuv5hC425PM` для `@PostMaker_ElixirPeptide_bot` отключен `2026-05-25`:
  - workflow переведен в `inactive`;
  - входящий Telegram webhook удален;
  - server backup сохранен в `/home/aicore/backups/n8n/C8Wmmjuv5hC425PM_2026-05-25_091327.json`.
- Отдельный Telegram-бот `@PeptideExpert_Bot` (`YJdwp45LI1dmrsLy`) остается активным и не является тем же самым контуром, что `PostMaker`.

## 1.1) Обновление 2026-05-25: Nanobanana и Telegram media-боты

### Что подтверждено
- `@PostMaker_ElixirPeptide_bot` сейчас привязан к credential `Telegram Bot MMS_MMM` и workflow `C8Wmmjuv5hC425PM` (`MEDIA_AGENT_1 | Master Orchestrator TG (draft)`).
- Этот же credential используется в:
  - `LG1KGfhnNCICjNra` (`MEDIA_AGENT_5 | Gemini Nano Banana Image (draft)`);
  - `K5es5hBE05LEeB1j` (`KB_SYNC_AGENT | Knowledge Base Sync (draft)`).
- Единственный текущий workflow в live `n8n`, где прямо зашиты `gen-lang-client-0571009024`, `aiplatform.googleapis.com`, `gemini-3-pro-image-preview` и `gemini-2.5-flash-image`, это `LG1KGfhnNCICjNra`.
- `LG1KGfhnNCICjNra` вызывается только из `C8Wmmjuv5hC425PM`:
  - через `Agent 5 | Gemini Nano Banana`;
  - через `Execute Flow Direct`.

### Статистика по `@PostMaker_ElixirPeptide_bot`
- Корневой bot-workflow `C8Wmmjuv5hC425PM`:
  - `production_success = 316`;
  - `production_error = 9`;
  - последний зафиксированный event: `2026-02-15 18:24:05`.
- Внутренний image-workflow `LG1KGfhnNCICjNra`:
  - `production_success = 49`;
  - `rootCount = 0`, то есть это не самостоятельный бот, а внутренний вызов;
  - последний зафиксированный event: `2026-02-15 18:22:41`.
- Внутренний fallback `KFWMYCaEpWAdVIn3` (`Agent 3 | Pollinations`):
  - `production_success = 24`;
  - последний зафиксированный event: `2026-02-15 18:24:04`.

### Что сделано по отключению `PostMaker`
- workflow `C8Wmmjuv5hC425PM` переведен в `inactive` в live-базе `n8n`;
- Telegram webhook у `@PostMaker_ElixirPeptide_bot` удален с `drop_pending_updates=true`;
- после удаления webhook:
  - `before_url = https://www.n-8-n.site/webhook/11765d1c-73a2-4b14-8ce9-bb31dbbb403e/webhook`;
  - `after_url = ""`;
  - `pending_update_count = 0`.

### Что найдено по второму media-боту
- Важное уточнение после дополнительной проверки:
  - `@MaxCorp_VideoGENai_bot` как Telegram-бот существует и сейчас;
  - но в текущем live `n8n` instance он не найден ни в `telegram` credentials, ни в workflow, ни в `workflow_history`.
- Telegram API на `2026-05-25` подтверждает:
  - `username = @MaxCorp_VideoGENai_bot`;
  - `first_name = VideoGEN`;
  - `webhook_url = ""`;
  - `pending_update_count = 0`.
- Пустой webhook означает, что текущая рабочая связка этого бота не похожа на `telegramTrigger`/webhook в нынешнем `n8n`.
- Наиболее вероятный текущий режим, если бот реально отвечает пользователям:
  - отдельный `long polling` runner вне `n8n`.
- Исторический подтвержденный контур найден в локальном Telegram export `2026-03-07`:
  - проект: `projects/veobot`;
  - стек: `Python/aiogram`;
  - entrypoint: `python -m veobot.main`;
  - ранний запуск: `nohup env PYTHONPATH=src .venv/bin/python -m veobot.main > bot.log 2>&1 &`;
  - затем перевод в user-service `~/.config/systemd/user/veobot.service`;
  - рабочая модель: `veo-3.1-fast-generate-001`;
  - тот же Google project: `gen-lang-client-0571009024`;
  - output bucket: `gs://maxcorp-veo-output/video`.
- То есть `@MaxCorp_VideoGENai_bot` подтвержден как отдельный Telegram/Veo/Vertex-контур, а не как текущий media-workflow внутри этого `n8n`.
- Ближайший текущий кандидат внутри самого `n8n` на второй media-бот:
  - username: `@M_A_X_B_O_T_bot`;
  - credential: `Telegram Bot Main`;
  - workflow: `ft03yrDgJJweqcVP` (`MEDIA_AGENT | Telegram + Memory + Flow + Kling (draft)`).
- Состояние `@M_A_X_B_O_T_bot`:
  - workflow уже `inactive`;
  - входящий Telegram webhook пустой;
  - `workflow_statistics`: `production_error = 3`, успешных production-запусков не зафиксировано;
  - внутри workflow есть old-school узлы `FLOW | Nano Banana | Generate Image` и `KLING`, но в текущем live-состоянии это не активный бот.

### Отдельно важно
- Активный `@PeptideExpert_Bot` живет отдельно:
  - workflow `YJdwp45LI1dmrsLy` (`Peptide_Expert`);
  - `production_success = 340`;
  - `production_error = 36`;
  - последний event: `2026-05-11 08:25:17`;
  - он не использует `gen-lang-client-0571009024`.
- По состоянию live `n8n` на `2026-05-25` майский billing Google Cloud по `NANO BANA` не объясняется найденными workflow внутри этого `n8n`:
  - вся подтвержденная activity по `Gemini Nano Banana` в текущем `n8n` обрывается на `2026-02-15`;
  - в мае из media/Nanobanana-контуров здесь живого трафика не видно.
- Но отдельно подтверждено, что `@MaxCorp_VideoGENai_bot` исторически ходил в тот же Google project `gen-lang-client-0571009024` уже вне этого `n8n`, через отдельный `veobot`-сервис.

## 1.2) Обновление 2026-05-25: Cosmetologist Hunter private-only fix

### Сделано
- Проверен live `cosmetologist_hunter.service` на `ai-core-prod-147`: сервис активен на `0.0.0.0:8787`, `Firecrawl` и `site-control-kit` включены.
- Найдена причина ошибки в Telegram-боте/агенте: preview-файл `.runtime/cosmetologist_hunter/previews/контакты_косметологов_москва_49.json` был создан от `root`, из-за чего сервис под пользователем `aicore` получал `Permission denied`.
- Исправлены права runtime-папки: `.runtime/cosmetologist_hunter` теперь принадлежит `aicore:aicore`.
- В `scripts/cosmetologist_hunter_service.py` включён private-only режим отбора:
  - сначала собираются врачебные профили `Prodoctorov`;
  - затем private-запросы Yandex;
  - 2GIS используется только после этого;
  - клиники, центры, салоны, студии и прочие организации отсекаются до записи результата;
  - в preview добавляется `private_match_reason`, чтобы было видно, почему контакт прошёл фильтр.
- Включён полноценный fetch fallback для `2GIS`, `Yandex` и `Prodoctorov`: `direct -> Firecrawl -> site-control-kit`.
- Добавлены короткие timeout-ы, общий search time budget и live `fetch_attempt`-логи в `journalctl`, чтобы бот не висел молча.
- Реальный прогон `2026-05-25` создал таблицу частных косметологов Москвы:
  - Google Sheet: `https://docs.google.com/spreadsheets/d/14X6j699O5J_RtjfUZ4JDddugisbIV0XdAr3HFP5a2kg/edit`;
  - server xlsx: `/home/aicore/n8n-server/ Таблицы_контактов /контакты_косметологов_москва_49.xlsx`;
  - local xlsx: `/home/max/n8n_ai_call_center/ Таблицы_контактов /контакты_косметологов_москва_49.xlsx`;
  - preview: `/home/max/n8n_ai_call_center/.runtime/cosmetologist_hunter/previews/контакты_косметологов_москва_49.json`;
  - run log: `/home/max/n8n_ai_call_center/.runtime/cosmetologist_hunter/logs/2026-05-25_private_cosmetologists_run.log`.
- По запросу на `50` контактов создан отдельный локальный и серверный файл:
  - local xlsx: `/home/max/n8n_ai_call_center/ Таблицы_контактов /контакты_косметологов_москва_50.xlsx`;
  - server xlsx: `/home/aicore/n8n-server/ Таблицы_контактов /контакты_косметологов_москва_50.xlsx`;
  - preview: `/home/max/n8n_ai_call_center/.runtime/cosmetologist_hunter/previews/контакты_косметологов_москва_50.json`;
  - build log: `/home/max/n8n_ai_call_center/.runtime/cosmetologist_hunter/logs/2026-05-25_private_cosmetologists_50_build.log`;
  - отбор сделан как `private-practice/cabinet candidates`: исключены явные `clinic/center/salon/medical/lab/shop/agency` keywords, но последние строки в пачке требуют ручной проверки, потому что это малые практики/бренды без явного ФИО.
- Таблица `_50` загружена в Google Drive в папку контактных таблиц:
  - Google Sheet: `https://docs.google.com/spreadsheets/d/1kAXIwaa_-rC4MO5vV3mFV-Geha08iL_6pJNCNxlQPAU/edit?gid=199760593#gid=199760593`;
  - rows written: `50`;
  - `AUTODIAL_DISPATCHER` и `ELEVEN_TOOL_CALL_LOG_BRIDGE` переключены на этот `spreadsheet_id`, чтобы dispatcher читал и `call_log` писал в одну таблицу.
- Перед переключением `AUTODIAL_DISPATCHER` был остановлен через n8n API, затем после синхронного обновления `AUTODIAL_DISPATCHER` и `ELEVEN_TOOL_CALL_LOG_BRIDGE` снова активирован.
- Backup live workflow перед переключением сохранен локально:
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_10-39-58_switch_autodial_to_contacts_50/`.
- После старта dispatcher уже записал в новую таблицу первую lock-строку `autodial_dispatcher / dialing` по `row_2`, что подтверждает старт обзвона именно с `_50`.

### На чем остановились
- Агент в текущем режиме надёжно выдаёт малые пачки private doctor profiles; тестовый production run на `5` контактов успешен.
- Запрос на `10` контактов вернул управляемую ошибку `найдено 5, нужно 10`, не подвисая и не подмешивая клиники.
- Live-сервер после серии прогонов временно начал получать от `Prodoctorov` страницу ограничения доступа; локальная машина ещё смогла снять часть данных, но strict-new режим на `50` без повторов сейчас не набирается.
- На `2026-05-25 10:41 MSK` live-обзвон включен и смотрит на `контакты_косметологов_москва_50`; первая строка взята в работу как `dialing`.
- В live workflow `COSMETOLOGIST_HUNTER_TELEGRAM_LIVE` всё ещё есть секреты прямо в Code node; это старый долг, отдельно требующий env-переноса для Telegram/Mistral/hunter token без поломки n8n Code node.

### Что делать дальше
- Наблюдать новую таблицу `_50` в течение ближайших минут/звонков: после lock-строки должен появиться итог от `ELEVEN_TOOL_CALL_LOG_BRIDGE` с `eleven_conv_id` или retry-исходом.
- Для массового сбора запускать private-only агент пачками по `5-10` и проверять preview перед добавлением в обзвон.
- Следующий hardening: вынести секреты `COSMETOLOGIST_HUNTER_TELEGRAM_LIVE` из live workflow в env/credentials и после этого перепривязать n8n nodes.
- Если нужно больше частных косметологов за один запуск, расширить Prodoctorov pagination и поднять `COSMETOLOGIST_HUNTER_SEARCH_TIMEOUT_SECONDS`, но не возвращать clinic/core-запросы в верх приоритета.

## 1.3) Обновление 2026-05-25: voicemail/message-service fast hangup

### Сделано
- По свежему кейсу `conv_1901ksezar1jezbsve31c4qr83rw` подтверждён старый конфликт prompt: live-правила всё ещё разрешали автоответчику/message-service получить короткое callback-сообщение, из-за чего агент мог слушать и отвечать машинному помощнику.
- Чтобы не продолжать обзвон на старом поведении, live workflow `AUTODIAL_DISPATCHER` остановлен через n8n API: `active=false`.
- Локальный source-of-truth prompt обновлён в `docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_EN.md`:
  - machine/unavailable/message-service signal закрывать максимум за `5` секунд;
  - не ждать, пока автоответчик договорит длинный скрипт;
  - не оставлять callback-сообщение электронному помощнику;
  - сначала `call_log` с `call_result=no_answer` или `busy`, `next_step=callback`, затем silent `end_call`.
- Подготовлен prompt-only payload для ElevenLabs Main:
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_10-48-19_voicemail_fast_hangup_prompt_patch/main_prompt_only_payload.json`.
- Попытка применить patch из текущей сети зафиксирована в:
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_10-48-19_voicemail_fast_hangup_prompt_patch/patch_attempt_result.json`.

### На чем остановились
- Прямой ElevenLabs API из локальной сети и с `ai-core-prod-147` возвращает `302` на restricted/help page, поэтому live prompt `Main` не был изменён программно.
- `2026-05-25 11:12 MSK`: по прямой команде пользователя `AUTODIAL_DISPATCHER` снова включён (`active=true`) до применения ElevenLabs prompt-fix.
- После включения `_50` получил новые строки: `row_3` был взят в `dialing`, затем появился результат, далее `row_4` взят в `dialing`.
- Риск старого поведения на автоответчике сохраняется до применения prepared prompt payload через ElevenLabs UI/API из разрешённой сети.

### Что делать дальше
- Зайти в ElevenLabs UI/API из разрешённой сети и применить payload `main_prompt_only_payload.json` к branch `Main` / `agtbrch_7801kgybyg9nesrbv64y078pazq0`.
- Проверить, что после patch сохранились `first_message=""`, `turn_timeout=10.0`, `voice_id=0ArNnoIAWKlT4WweaVMY`, `tool_ids`, `skip_turn`, `voicemail_detection`, `context_fetch`, `call_log`, `send_sms_info`, `end_call`.
- Прогнать manual voicemail/SIP test: на фразах `абонент сейчас не может ответить`, `если абонент захочет связаться`, `что передать` агент должен завершить звонок без spoken callback максимум за `5` секунд.
- После применения prompt-fix ещё раз проверить live звонок на автоответчик/message-service и убедиться, что hangup происходит максимум за `5` секунд.

## 1.4) Обновление 2026-05-25: разбор задержки outbound-call и тайминги n8n

### Сделано
- Добавлен локальный диагностический скрипт:
  - `/home/max/n8n_ai_call_center/scripts/report_n8n_eventlog_timings.py`
  - он разбирает `n8nEventLog*.log`, считает длительности workflow/node и `runner task requested -> response received`.
- Снят свежий live-срез `n8nEventLog` с сервера и подтверждено:
  - основной длинный хвост не в Code nodes и не в Google Sheet;
  - самые долгие узлы сейчас:
    - `AUTODIAL_DISPATCHER -> Dispatcher | Request Outbound Call`
    - `VOICE_INBOUND_AGENT -> Eleven | Outbound HTTP`
  - их длительность до правки была порядка `33–42s`.
- Прямой probe с live-сервера `147.45.213.87` в relay `http://151.241.228.232:8787/eleven/outbound-call` подтвердил причину:
  - при upstream-сбое relay отвечал только через `41703 ms` с `HTTP 502`;
  - это совпало с его текущей retry-схемой `20s timeout + 1 retry + 1500ms delay`.
- Live workflow `VOICE_INBOUND_AGENT (draft)` обновлён через `n8n API`:
  - в ноде `Eleven | Outbound HTTP` добавлен `options.timeout = 10000`;
  - backup сохранён в:
    - `/home/max/n8n_ai_call_center/backups/2026-05-25_outbound_timeout_trim/VOICE_INBOUND_AGENT_before.json`
    - `/home/max/n8n_ai_call_center/backups/2026-05-25_outbound_timeout_trim/VOICE_INBOUND_AGENT_after_timeout_patch.json`
- Live workflow `AUTODIAL_DISPATCHER (sheet-first draft)` обновлён через `n8n API`:
  - в ноде `Dispatcher | Request Outbound Call` добавлен `options.timeout = 12000`;
  - backup сохранён в:
    - `/home/max/n8n_ai_call_center/backups/2026-05-25_autodial_timeout_trim/AUTODIAL_before.json`
    - `/home/max/n8n_ai_call_center/backups/2026-05-25_autodial_timeout_trim/AUTODIAL_after.json`
- Проверка после live-патча:
  - тот же webhook `POST https://www.n-8-n.site/webhook/eleven/outbound-call` теперь отвечает примерно за `10180 ms`, а не за `~41.7s`.
- Исходник relay в репозитории приведён к более безопасным дефолтам для будущего deploy:
  - `scripts/eleven_outbound_relay_server.py`
  - новые defaults: `RELAY_TIMEOUT=8`, `RELAY_RETRY_COUNT=0`, `RELAY_RETRY_DELAY_MS=500`.
- Отдельно внесена та же правка в реальный live relay на `151.241.228.232`:
  - backup runtime сохранён на relay-сервере:
    - `/root/backups/eleven_relay_2026-05-25_11-45-10`
  - обновлён `/opt/eleven_outbound_relay.py`;
  - в `/root/.eleven_outbound_relay.env` добавлены:
    - `RELAY_TIMEOUT=8`
    - `RELAY_RETRY_COUNT=0`
    - `RELAY_RETRY_DELAY_MS=500`
  - сервис `eleven-outbound-relay.service` перезапущен успешно.
- Проверка после live relay-патча:
  - `POST https://www.n-8-n.site/webhook/eleven/outbound-call` с probe-payload теперь даёт `provider_rejected` примерно за `8367 ms`;
  - до этого тот же failure path занимал `~41.7s`.
- Дополнительная диагностика sheet-first dispatcher показала, что текущая причина остановки не `exhausted`, а именно:
  - `reason = provider_circuit_breaker`
  - `recent_provider_failure_count = 3`
  - `today_provider_failure_count = 5`
  - в Google Sheet `_50` при этом подтверждены все `50` seed-строк (`source_system = xlsx_import`), то есть база физически не исчерпана.
- После выхода старых technical failures из окна `15 минут` dispatcher действительно ожил автоматически:
  - в live Google Sheet `_50` появились новые строки `dialing/outbound_request_failed` по `row_7`, `row_8`, `row_9`, `row_10`;
  - это подтвердило, что `cron`, due-логика и breaker reset работают, а текущий стоп вызван именно upstream outbound reject path.
- Чтобы не продолжать тратить базу на технические фейлы, live `AUTODIAL_DISPATCHER` после этой проверки снова остановлен вручную через `n8n API`:
  - workflow `iZ8OaN4xW0ZtxaCJ`
  - итоговое состояние после деактивации: `active=false`.
- Для следующего цикла диагностики дополнительно усилен live relay-лог:
  - `scripts/eleven_outbound_relay_server.py` теперь пишет краткий summary тела ответа ElevenLabs и при `HTTP 200`;
  - обновлён реальный `/opt/eleven_outbound_relay.py` на `151.241.228.232`, сервис перезапущен успешно;
  - это нужно, чтобы следующий тест сразу показал разницу между accepted outbound и "200, но по сути не принят/не дошёл".

### На чем остановились
- Длинная пауза на старте outbound теперь локализована и частично срезана на live со стороны `n8n` timeout.
- Та же пауза дополнительно срезана на реальном relay-хосте `151.241.228.232`: старый retry/path больше не должен держать `~41s`.
- Это не чинит сам live ElevenLabs prompt: автоответчик по-прежнему может быть разговорно обработан до применения prepared prompt patch через разрешённую сеть/UI.
- Автодозвон уже подтвердил, что умеет сам выходить из `provider_circuit_breaker`, но upstream outbound всё ещё возвращает технический отказ. Поэтому dispatcher сейчас остановлен вручную, чтобы не сжигать лиды до следующей live-правки.
- Наблюдаемость relay усилена: на следующем probe/реальном звонке можно будет увидеть не только время и статус, но и краткий смысл тела ответа ElevenLabs.
- На сервере `n8n` отдельно зафиксированы системные сигналы деградации:
  - `database.sqlite` внутри `n8n` уже около `2.7G`;
  - в docker logs есть `SqliteWriteConnectionMutex` timeout'ы;
  - есть `Task ... Offer expired - not accepted within validity window`.
- По свежему тайминг-срезу эти runner/sqlite проблемы сейчас не были главным источником `40s` outbound delay, но остаются отдельным operational риском.

### Что делать дальше
- Разобрать, почему upstream outbound по-прежнему возвращает технический reject даже после срезания timeout/retry path до `~8.3s`, и только после этого снова включать `AUTODIAL_DISPATCHER`.
- Повторить живой/тестовый звонок после timeout-патча и снять новый `n8nEventLog` report: должен исчезнуть `33–42s` хвост на `Eleven | Outbound HTTP`.
- Зайти в ElevenLabs через разрешённую сеть/UI и применить уже подготовленный voicemail/message-service patch на `Main`.
- Отдельным следующим циклом решить runtime-долг `n8n`:
  - либо уменьшить pressure на SQLite;
  - либо переводить основной `n8n` off SQLite;
  - отдельно проверить, почему на сервере продолжают приходить `POST mango/result/route` в несуществующий webhook.

## 1.5) Обновление 2026-05-25: live Main patch через relay и ручная канарейка

### Сделано
- Подтверждено, что прямой ElevenLabs API из `147.45.213.87` по-прежнему прикрыт `302/403`, но relay-хост `151.241.228.232` имеет рабочий доступ к `api.elevenlabs.io`.
- Через relay-хост снят live backup `AI_CALL_AGENT_1 / Main`:
  - локальная копия до правки:
    - `/home/max/n8n_ai_call_center/backups/2026-05-25_live_main_canary_refresh/current_ai_call_agent_1.before.json`
  - remote backup:
    - `/root/current_ai_call_agent_1.json`
- Подготовлены два patch-артефакта:
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_live_main_canary_refresh/main_patch_payload.json`
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_live_main_canary_refresh/main_minimal_patch_payload.json`
- Первый полный patch был отклонён Eleven API с `400 both_tools_and_tool_ids_provided`, поэтому применён минимальный безопасный PATCH без миграции `tool_ids`.
- Успешно применён live patch в `Main`:
  - `turn_timeout` снижен до `5.0`;
  - `voicemail_detection.params.voicemail_message = null`;
  - live prompt заменён на актуальный source-of-truth с жёстким machine fast-hangup;
  - сохранены `first_message=""`, `voice_id=0ArNnoIAWKlT4WweaVMY`, `tool_ids`, `phone_ids`.
- Ответ и свежий agent snapshot сохранены в:
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_live_main_canary_refresh/current_ai_call_agent_1.after_patch.json`
  - `/root/main_patch_response_2026-05-25.json`
- По итоговому GET после patch подтверждено:
  - branch `Main = agtbrch_7801kgybyg9nesrbv64y078pazq0`;
  - новая live version:
    - `agtvrsn_3301ksfb9p4xf68s90k3by9y677a`.
- Для живой проверки возвращения обзвона включен канареечный режим:
  - `AUTODIAL_DISPATCHER` был кратко активирован через n8n API;
  - затем выяснилось, что dispatcher уже упёрся во внутренний стоп `daily_provider_failure_limit_reached`, поэтому канарейка продолжена вручную через `POST /webhook/eleven/outbound-call`.
- Ручная канарейка прогнана по трём лидам:
  - `row_11`
  - `row_12`
  - `row_13`
- Все `3/3` ручных canary-call вернули один и тот же техисход:
  - `provider_rejected`
  - `relay_upstream_failed`
  - `The read operation timed out`
- Relay journal на `151.241.228.232` подтвердил три подряд upstream timeout примерно по `8015-8025 ms`.
- При этом live Sheet показал первый положительный эффект нового prompt:
  - по `row_11` появилась `elevenlabs`-строка с `call_result = no_answer`;
  - note: `Обнаружен голосовой ассистент, сообщение не оставлено.`
  - это первый подтверждённый live-кейс, где после patch spoken callback автоответчику уже не был оставлен.

### На чем остановились
- Главный live-blocker сместился:
  - machine/message-service prompt уже реально обновлён;
  - но outbound SIP trunk path всё ещё нестабилен и даёт технический timeout ещё до полноценной серии канареечных разговоров.
- `AUTODIAL_DISPATCHER` сейчас снова оставлен в `inactive`, потому что:
  - текущий `provider_failures_today = 8`;
  - live logic уже считает, что дневной лимит технических outbound-фейлов достигнут.
- `eleven_conv_id` в свежих строках Sheet всё ещё пустой:
  - call_log bridge теперь чистит плейсхолдеры корректно;
  - но live `call_log` tool-schema в `Main` остаётся relaxed и не прокидывает conversation id автоматически.

### Что делать дальше
- Не включать массовый обзвон, пока не разобран текущий `relay_upstream_failed` path.
- Следующим техническим циклом:
  - сравнить успешные и тайм-аутные outbound payload на relay;
  - подтвердить, нет ли специфического reject pattern по отдельным номерам/полям payload;
  - после этого повторить manual canary `3-5` звонков.
- Отдельным маленьким шагом добить `eleven_conv_id`:
  - попробовать точечный patch только `call_log` tool-schema через relay-host;
  - не трогать `tool_ids`, `first_message`, `voice_id` и phone bindings.

## 1.6) Обновление 2026-05-25: false provider-failure fix в autodial

### Сделано
- По свежему live Sheet разбору найден ещё один корневой дефект dispatcher-логики:
  - `autodial_dispatcher` считал `outbound_request_failed` как технический provider-failure сразу и безоговорочно;
  - но по тем же лидам позже уже приходил реальный `elevenlabs`-результат, то есть часть таких timeout'ов была ложной.
- Это подтверждено живыми строками как минимум для:
  - `row_3`
  - `row_5`
  - `row_10`
- Логика `Dispatcher | Parse Sheet Rows` обновлена:
  - если по тому же `lead_id`/`lead_key` позже в тот же день пришёл `elevenlabs`-итог, ранний `outbound_request_failed` считается `resolved provider failure`;
  - такие строки больше не входят в:
    - `recent_provider_failure_count`
    - `today_provider_failure_count`
    - `today_technical_waste_count`
- Обновлён source workflow в репозитории:
  - `/home/max/n8n_ai_call_center/scripts/build_autodial_sheet_workflow.py`
  - `/home/max/n8n_ai_call_center/workflows/AUTODIAL_DISPATCHER_DRAFT.json`
- Live workflow `iZ8OaN4xW0ZtxaCJ` обновлён через `n8n API`.
- Backup live workflow перед этим шагом:
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_13-58-54_autodial_false_provider_failure_fix/AUTODIAL_live_before.json`
- Ответ после live PUT:
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_13-58-54_autodial_false_provider_failure_fix/AUTODIAL_live_after_put_response.json`
- Локальный live-отчёт тоже обновлён, чтобы показывать ту же картину, что и dispatcher:
  - `/home/max/n8n_ai_call_center/scripts/report_live_call_log_sheet.py`
  - теперь он отдельно считает:
    - `provider_failures_raw`
    - `provider_failures_resolved`
    - `provider_failures_unresolved`
- Контрольный срез после этой правки:
  - `provider_failures_raw = 8`
  - `provider_failures_resolved = 3`
  - `provider_failures_unresolved = 5`

### На чем остановились
- После фикса `AUTODIAL_DISPATCHER` снова активирован, но это произошло уже на границе/после `14:00 MSK`, то есть вне окна обзвона.
- Поэтому немедленного нового live-вызова после этой правки ещё не было; но следующий рабочий tick уже пойдёт без старого false-breaker по resolved timeout-кейсам.
- Проблема upstream timeout при этом не исчезла полностью:
  - unresolved technical failures по `row_7`, `row_8`, `row_9` ещё остаются;
  - outbound timeout path всё ещё требует отдельного добивания.

### Что делать дальше
- На следующем рабочем окне `10:00-14:00 MSK` снять первый tick/первую новую попытку уже после false-failure fix и проверить:
  - ушёл ли прежний `daily_provider_failure_limit_reached`;
  - не уходит ли dispatcher снова в ложный breaker;
  - как меняется доля `resolved` vs `unresolved` provider-failures.
- Затем продолжить canary только по `3-5` попыткам и смотреть одновременно:
  - relay journal;
  - `report_live_call_log_sheet.py`;
  - machine-like notes;
  - наличие или отсутствие `eleven_conv_id`.
- Для ручной работы без раскопок по репозиторию собран отдельный операторский пакет в текстовых файлах:
  - `/home/max/n8n_ai_call_center/docs/checkpoints/2026-05-25_callcenter_operator_pack/`
  - внутри есть:
    - `00_README.txt`
    - `01_CURRENT_STATE.txt`
    - `02_WHAT_TO_WRITE_AND_WHERE.txt`
    - `03_NEXT_CALL_WINDOW_CHECKLIST.txt`
    - `04_PATHS_AND_FILES.txt`
- Для отдельного техцикла по инфраструктуре собран и пакет миграции `n8n: SQLite -> Postgres`:
  - `/home/max/n8n_ai_call_center/docs/checkpoints/2026-05-25_n8n_postgres_migration_pack/`
  - внутри:
    - `00_README.txt`
    - `01_MIGRATION_PLAN.txt`
    - `02_CUTOVER_CHECKLIST.txt`
    - `03_ROLLBACK_PLAN.txt`
    - `04_CURRENT_RISKS.txt`

## 1.7) Обновление 2026-05-25: intermediary/message-transfer block в live Main

### Сделано
- По кейсу `conv_8801ksfbpec2fz5bcvn6wt9h05p1` подтверждено, что текущая кампания не должна считать `я передам ответственному специалисту` полезным контактом.
- Найден конфликт в source-of-truth prompt:
  - там всё ещё оставалась старая логика `send_kp_pending_callback` для secretary/operator/message-transfer сценариев.
- Локальные prompt-источники обновлены:
  - `/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_EN.md`
  - `/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_RU.md`
  - `/home/max/n8n_ai_call_center/документация_для_агента/04_ELEVENLABS_АГЕНТ.md`
- Новое правило:
  - secretary / intermediary / assistant / screening-service / defender-service, которые только обещают что-то передать дальше, не считаются полезным human contact;
  - не оставлять pitch;
  - не оставлять manager contact;
  - не логировать это как `send_kp_pending_callback` только из-за согласия что-то передать.
- Live `Main` перепатчен через relay-host `151.241.228.232`.
- Артефакты:
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_intermediary_block_refresh/main_intermediary_block_payload.json`
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_intermediary_block_refresh/main_intermediary_block_payload_v2.json`
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_intermediary_block_refresh/main_intermediary_block_payload_applied.json`
- Live GET после patch подтвердил:
  - `turn_timeout = 5.0`;
  - prompt содержит новые intermediary-block формулировки;
  - `MTS Defender` и machine fast-hangup правила сохранились.

### На чем остановились
- Live rule уже обновлено, но end-to-end новый звонок именно на intermediary-линию после этого patch ещё не снят.
- Поэтому следующий живой similar-case нужно использовать как проверку, что `send_kp_pending_callback` больше не появляется на таких линиях.

### Что делать дальше
- При первом следующем похожем звонке проверить:
  - нет ли `send_kp_pending_callback` на intermediary/message-transfer линии;
  - нет ли spoken callback или контакта менеджера;
  - завершает ли агент такой кейс как `no_answer` / blocked non-human outcome.

## 1.8) Обновление 2026-05-25: жёсткое правило по слову `абонент`

### Сделано
- По кейсу `conv_6201ksfbnq77echv3j7e4j2h8qha` пользователь зафиксировал более жёсткое боевое правило:
  - если линия произносит слово `абонент` в сервисной фразе, это надо считать автоответчиком без дальнейшего анализа.
- Это правило добавлено в:
  - `/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_EN.md`
  - `/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_RU.md`
  - `/home/max/n8n_ai_call_center/документация_для_агента/04_ELEVENLABS_АГЕНТ.md`
- Подготовлен и применён новый live patch:
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_abonent_hard_rule_refresh/main_abonent_hard_rule_payload.json`
- Patch снова применён в live `Main` через relay-host `151.241.228.232`.
- Практический смысл:
  - `абонент сейчас не может ответить`
  - `если абонент захочет связаться`
  - `абонент использует защиту/помощника`
  - и любые похожие service-line конструкции со словом `абонент`
  теперь должны сразу идти в `machine -> call_log -> silent end_call`.

### На чем остановились
- Live rule уже применено, но новый end-to-end звонок именно после этого последнего patch ещё не снят.

### Что делать дальше
- На следующем похожем кейсе проверить, что агент:
  - не говорит в ответ вообще;
  - не оставляет callback message;
  - не уходит в qualification;
  - завершает звонок сразу после `call_log`.

## 1.9) Обновление 2026-05-25: secretary handoff снова полезный + daily dialing limit = 30

### Сделано
- Пользователь явно переопределил политику по intermediary/message-transfer линиям:
  - `я передам ответственному специалисту`
  - `оставьте контакт`
  - `мы передадим информацию`
  теперь снова считаются полезным handoff-контактом, а не blocked outcome.
- Source-of-truth prompt обновлён:
  - `/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_EN.md`
  - `/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_RU.md`
  - `/home/max/n8n_ai_call_center/документация_для_агента/04_ELEVENLABS_АГЕНТ.md`
- Live `Main` перепатчен через relay-host `151.241.228.232`:
  - payload: `/home/max/n8n_ai_call_center/backups/2026-05-25_secretary_useful_handoff_refresh/main_secretary_useful_handoff_payload.json`
- Практическое правило теперь такое:
  - автоответчики по `абонент`/machine-service всё ещё режем сразу;
  - но живой secretary/intermediary, который реально готов передать контакт ответственному специалисту, считается полезным handoff и логируется как `send_kp_pending_callback`.
- Одновременно пользователь снизил дневной лимит попыток автодозвона:
  - `daily_dialing_limit: 50 -> 30`
- Это обновлено:
  - в генераторе `/home/max/n8n_ai_call_center/scripts/build_autodial_sheet_workflow.py`
  - в source workflow `/home/max/n8n_ai_call_center/workflows/AUTODIAL_DISPATCHER_DRAFT.json`
  - в live workflow `iZ8OaN4xW0ZtxaCJ`
- Backup live workflow перед этим шагом:
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_15-29-59_autodial_daily_limit_30/AUTODIAL_live_before.json`
  - `/home/max/n8n_ai_call_center/backups/2026-05-25_15-29-59_autodial_daily_limit_30/AUTODIAL_live_after_put_response.json`

### На чем остановились
- Live policy теперь смешанная, как и хотел пользователь:
  - machine/service phrase with `абонент` -> сразу hangup;
  - полезный secretary/intermediary handoff -> `send_kp_pending_callback`.
- Новый дневной предел попыток уже равен `30`, но новый рабочий день после этой правки ещё не прошёл.

### Что делать дальше
- В следующее окно `10:00-14:00 MSK` проверить:
  - что autodial реально останавливается на `30`, а не на старом `50`;
  - что полезные secretary handoff-кейсы пишутся как `send_kp_pending_callback`;
  - что service-line фразы со словом `абонент` по-прежнему режутся как автоответчик.

## 1.10) Обновление 2026-05-25: main синхронизирован с рабочей веткой, серверный clean-clone обновлен

### Сделано
- Рабочая ветка `codex/email-followup-agent-live` дополнительно зафиксирована коммитом:
  - `01d28bc` — `Sync live handoff policy and migration pack`
- Этот коммит запушен в `origin/codex/email-followup-agent-live`.
- GitHub `main` приведен в актуальное состояние через отдельный чистый worktree:
  - merge commit в `main`: `a3837a6` — `Merge branch codex/email-followup-agent-live into main`
- Серверный clean deploy-клон `/home/aicore/n8n-ai-clean` обновлен до нового `origin/main`.
- Перед server sync локальные tracked-правки clean-clone не потеряны:
  - они сохранены в `git stash` на сервере как `pre-main-sync-2026-05-25`.

### На чем остановились
- Локальный рабочий каталог `/home/max/n8n_ai_call_center` по-прежнему остается грязным по unrelated/runtime-файлам; это сознательно не чистилось.
- Боевой каталог `/home/aicore/n8n-server` на сервере остается operational dirty и не приводился к git-clean состоянию, чтобы не задеть рабочий runtime.
- После синхронизации `main` следующим правильным шагом является отдельная новая ветка под следующий техцикл, без смешивания с уже стабилизированной live-веткой.

### Что делать дальше
- Продолжать следующую большую работу уже из новой ветки от обновленного `main`.
- Если потребуется полноценный server deploy из clean-clone, сначала отдельно проверить содержимое `stash pre-main-sync-2026-05-25` и решить, какие server-specific правки вернуть осознанно.
- Не использовать `/home/aicore/n8n-server` как “чистый git-источник истины”; для git-синхронизации опираться на `origin/main` и `/home/aicore/n8n-ai-clean`.

## 2) Контрольная точка проекта (2026-05-22)

### Сделано
- `2026-05-22` снят live-срез звонкового контура на `ai-core-prod-147`:
  - n8n, Postgres, PostgREST, Redis, Traefik и связанные контейнеры подняты;
  - активны workflow `VOICE_INBOUND_AGENT`, `ELEVEN_TOOL_CALL_LOG_BRIDGE`, `AUTODIAL_DISPATCHER`, `ELEVEN_TOOL_SEND_SMS_BRIDGE`;
  - `call_center.call_sessions / call_events / call_turns` на момент проверки пустые, рабочие события звонков фактически лежат в n8n executions и Google Sheet через `call_log`;
  - по окну `2026-05-22 10:00-11:35 MSK` найдено `27` outbound-попыток: `13` запросов приняты ElevenLabs, `6` получили `SIP 486 Busy Here`, `8` дали relay/provider timeout;
  - dispatcher остановил обзвон по `daily_provider_failure_limit_reached` из-за `today_provider_failure_count = 8`;
  - по содержимому сегодняшних payload точного совпадения `LabLabStation / Lab Lab / lablab` не найдено.
- `2026-05-22` выполнено live-hardening секретов n8n:
  - backup перед правками сохранён на сервере в `/home/aicore/safe-backups/2026-05-22_13-56-42_secrets_autovoicemail_fix`;
  - ElevenLabs API key, outbound relay token, Mango API key/salt и Google OAuth client/refresh-secret вынесены из workflow JSON и execution data в env-файлы:
    - `/home/aicore/n8n-ai-clean/.env.callcenter`;
    - `/home/aicore/n8n-server/.env.callcenter`;
  - compose-файлы `/home/aicore/n8n-ai-clean/docker-compose*.yml` и `/home/aicore/n8n-server/docker-compose*.yml` подключают эти env-файлы к n8n;
  - workflow `VOICE_INBOUND_AGENT`, `ELEVEN_TOOL_CALL_LOG_BRIDGE`, `AUTODIAL_DISPATCHER`, `ELEVEN_TOOL_SEND_SMS_BRIDGE` переведены на `$env.*` вместо hardcoded secrets;
  - для этих workflow отключено сохранение success/error execution payloads, старые execution/history payloads с секретами удалены;
  - контрольный secret-scan по `workflow_entity.nodes` и `execution_data` не нашёл старые маркеры `sk_...`, `GOCSPX-`, `1//...`, Mango secrets и `ya29.`;
  - smoke `call_log` после перевода на env прошёл успешно и добавил строку `smoke_secret_hardening_envflag` в Google Sheet, диапазон `'Лиды_обзвон'!A905:AM905`.
- По автоответчику найден важный текущий конфликт в правилах агента:
  - старое правило message-service разрешало оставить короткое callback-сообщение и завершить звонок;
  - это объясняет кейсы, где агент продолжает говорить с электронным помощником вместо немедленного завершения.
- Зафиксировано новое обязательное правило для следующей правки live ElevenLabs prompt:
  - voicemail, IVR, электронный помощник, message-service, фразы `что передать`, `если абонент захочет связаться`, `какие подробности желаете рассказать`, `это всё?` должны завершаться сразу;
  - агент не должен оставлять callback-сообщение, отвечать на уточнения электронного помощника или вести qualification/sales-pitch;
  - результат логировать как `no_answer` или `busy/no_answer` с `next_step=callback`, затем вызывать `end_call`.
- Важно: live ElevenLabs prompt в этот проход не изменён, потому что прямой ElevenLabs API из текущей сети возвращает restricted/help page (`302/403`). Нужна правка через доступный ElevenLabs UI/API с разрешённой сети.
- Email-followup агент доведен до production-режима как отдельный контур без зависимости от `ElevenLabs`.
- Для email-агента подняты и подтверждены:
  - `email_followup.service`
  - `EMAIL_FOLLOWUP_AGENT_LIVE`
  - `EMAIL_FOLLOWUP_AGENT_MANUAL_LIVE`
- Live-расписание email-агента переведено на `09:00` и `15:00` по Москве, чтобы не пересекаться с обзвоном.
- В письма добавлено обязательное PDF-вложение с коммерческим предложением.
- В проде закреплены рабочие таблицы `москва_1`, `москва_2`, `москва_47`.
- Включены и проверены:
  - SMTP-отправка;
  - IMAP bounce-обработка;
  - Telegram-отчёты;
  - `firecrawl`-усиление web-resolver;
  - blacklist доменов.
- Исправлены реальные operational дефекты email-контура:
  - ложные каталожные и платформенные email;
  - неверный Telegram recipient;
  - утечка seed email из старых `xlsx_import` строк в merged context.
- Создан корневой `AGENTS.md` и отдельный пакет документации по email-агенту с checkpoint/runbook/test-report.
- По live-звонкам снят свежий срез `2026-04-30`:
  - агент реально работает на stable version `agtvrsn_5801kqc3ayw9fk38qqypkgzaj0dh`;
  - подтверждены свежие `done` разговоры и voicemail-cases на текущем prompt;
  - anti-IVR/human-gate и запрет на возврат в email-flow в новых разговорах не сломались.
- Найден и исправлен live-defect в autodial:
  - обычный `SIP 486 Busy Here` ошибочно попадал в `outbound_request_failed`;
  - из-за этого `AUTODIAL_DISPATCHER` включал `provider_circuit_breaker` после серии занятых линий, хотя это не был инфраструктурный сбой;
  - теперь `SIP 486 Busy Here` классифицируется как `busy` с обычным retry, а не как технический provider-failure.
  - затем найден второй слой того же дефекта: в реальном live-маршруте `Busy Here` лежал внутри `response_body.note / response_body.eleven_response.message`, из-за чего первая правка не дошла до конечного payload `call_log`;
  - live dispatcher доработан повторно: теперь он распаковывает вложенный outbound-response и корректно видит `Busy Here` end-to-end.
- Найден и исправлен второй live-defect по длинному ожиданию гудков:
  - `conv_9601kqf0hx99f2j9dr7y69qvc2e0` на stable version `agtvrsn_5801kqc3ayw9fk38qqypkgzaj0dh` провисел `4m25s` до первой осмысленной живой реплики;
  - по свежим логам агент местами всё ещё открывался на literal ASR-маркеры `...` и `музыка`, а также на запрещённые service-style probing фразы;
  - отдельным слоем `AUTODIAL_DISPATCHER` держал lock только `1` минуту, из-за чего тот же `row_27` был задвоен двумя `dialing`-строками через минуту, пока первый длинный звонок ещё висел на линии.
- Локально собран отдельный инструмент `tools/telegram_sandbox_activity_runner/` для внутреннего Telegram sandbox-контура:
  - standalone CLI + launcher;
  - allowlist-only activity runner для `send_message / open_chat / idle_scroll`;
  - operator-assisted `prepare-invite` и `prepare-join` с ручным финальным подтверждением по умолчанию;
  - operator-assisted `prepare-add-contact-profile` для добавления allowlist-`@username` в свои контакты через Telegram Desktop portable;
  - `import-contacts` для bulk approved `@username` -> `allowlist_contacts`;
  - `batch-add-contacts` по списку `contact_id` с random pauses;
  - optional `Telegram API sidecar` (`Telethon`) с режимами `api-status / check-contact / add-contact / interactive-login`;
  - пример конфига, README, systemd example units и базовые unit/smoke проверки;
  - отдельные `AGENTS.md` и `CHECKPOINT_RU.md` внутри tool-папки;
  - отдельную GitHub-ready wrapper-папку `tools/telegram_desktop_contact_tool/` с собственным launcher и README.

### На чем остановились
- Секреты звонкового n8n-контура вынесены из workflow/execution payloads в серверные env-файлы, smoke `call_log` после этого зелёный.
- Прямой API-доступ к ElevenLabs из текущего окружения заблокирован, поэтому prompt-правка по немедленному завершению автоответчиков пока не применена на live `Main`.
- Следующая точка продолжения по звонкам: зайти в ElevenLabs из разрешённой сети/UI и заменить старое правило message-service “оставить короткий callback-месседж” на “ничего не оставлять, сразу `call_log` + `end_call`”.
- Основной live-контур звонков стабилен, но следующий контрольный шаг уже смещён в post-fix наблюдение за двумя свежими правками:
  - `SIP 486 -> busy` больше не должен включать ложный `provider_circuit_breaker`;
  - агент больше не должен висеть по несколько минут на ringback/hold и не должен открываться на `музыка`, `...` или сервисные probing-реплики.
- Prompt-only refresh и новый autodial lock уже выложены в live, но после них ещё не было нового рабочего окна `10:00–14:00 MSK`, поэтому end-to-end подтверждение следующими живыми звонками пока не снято.
- Email-агент уже рабочий, но часть лидов закономерно остаётся в `manual_review`, потому что:
  - email не найден;
  - домен не существует;
  - контекст строки слабый;
  - строка выглядит подозрительно.
- Telegram sandbox tool пока не привязывался к реальным live browser clients и не проходил живой Telegram smoke:
  - локально подтверждены `py_compile`, unit tests, dry-run CLI, одиночные live smokes и один live batch;
  - для actor `AK2` уже есть локальные runtime-файлы:
    - config: `~/.config/telegram-sandbox-activity-runner/ak2.local.json`;
    - state: `~/.local/share/telegram-sandbox-activity-runner/ak2.state.json`;
    - API env: `~/.config/telegram-sandbox-activity-runner/ak2.api.env`;
    - Telethon vendor path: `~/.local/share/telegram-sandbox-activity-runner/vendor`;
    - session file: `~/.local/share/telegram-sandbox-activity-runner/api_sessions/ak2.session`.
  - через `AK2` подтверждено:
    - `prepare-add-contact-profile` точно открывает карточку по `tg://resolve?...&profile`;
    - для `import_a1exyc` полный `Add to contacts -> Done -> reopen` реально сработал;
    - `AK2` API session на `2026-05-01` уже успешно поднимается напрямую из `TelegramPortable-AK2/TelegramForcePortable/tdata` через новый `api-import-tdata-session` / `import-tdata-session`;
    - `api-status` теперь показывает `authorized` для `@S_e_r_a_p_h_i_na`, то есть sidecar больше не упирается в `unauthorized`.
  - уже был прогнан старый live batch на `20` импортированных `contact_id`:
    - batch run: `~/.local/share/telegram-sandbox-activity-runner/runs/20260430T134737-2b8ab872/`;
    - на уровне UI flow `successful_count = 20`;
    - но `verified_count = 0`, потому что API session не авторизована и автоматической MTProto-проверки пока нет.
  - на `2026-05-01` уже после успешного API bootstrap сделана честная MTProto-проверка approved-list:
    - `batch-add-contacts --backend api_only` на первых `30` импортированных `contact_id` дал `successful_count = 0`;
    - затем отдельный одноразовый API scan прошёл все `562` импортированных `@username` из локального `AK2` allowlist;
    - итог scan: `0 / 562` резолвящихся обычных user-аккаунтов;
    - типовой ответ Telegram API: `No user has "<username>" as username`;
    - полный scan-артефакт: `~/.local/share/telegram-sandbox-activity-runner/runs/20260501T133700-ak2-api-full-scan/ak2_api_full_scan.json`.
  - важный остаточный gap теперь уже уточнён:
    - проблема больше не в `AK2`, не в `Telethon` и не в portable/UI path;
    - проблема в самом imported dataset: текущий approved-list на `2026-05-01` выглядит как stale/invalid для Telegram username resolution;
    - пока не будет свежего валидного списка `@username`, реальные массовые `Add to contacts` дальше не пойдут ни через API, ни через UI.
  - дополнительно на `2026-05-01`:
    - пользователь сообщил, что `AK2` аккаунт заблокирован;
    - активных процессов `telegram_sandbox_activity_runner / telegram_api_sidecar / telegram_portable.py` уже нет;
    - user-level `systemd` service/timer для этого инструмента не активны;
    - локальный actor `ak2` в `~/.config/telegram-sandbox-activity-runner/ak2.local.json` переведён в `active: false`, а `plan/run` теперь реально уважают флаг `active`.
    - затем пользователь уточнил, что переходим на другой portable-профиль `/home/max/TelegramPortableAK`;
    - для него уже подготовлены отдельные local runtime-файлы:
      - config: `~/.config/telegram-sandbox-activity-runner/ak.local.json`;
      - state: `~/.local/share/telegram-sandbox-activity-runner/ak.state.json`;
      - API env: `~/.config/telegram-sandbox-activity-runner/ak.api.env`.
    - новый actor:
      - `actor_id = ak`;
      - `portable_profile_dir = /home/max/TelegramPortableAK`;
      - `portable_account_username = @M_a_g_g_i_e`;
      - `api_sidecar.preferred_mode = portable_only`, чтобы этот профиль по умолчанию шёл через `SiteControl / Telegram Desktop`.
    - dry-run `prepare-add-contact-profile` для `actor_id=ak` уже проходит корректно, то есть новый actor подцеплен без смешивания с `AK2`.
    - на `2026-05-01` desktop helper и standalone tool уже частично переведены с `tg://resolve?...&profile` на новый входной маршрут:
      - `поиск username -> открыть первый chat result -> снять фокус с поиска -> дальше работать из открытого чата`;
      - в `/home/max/site-control-kit/scripts/telegram_portable.py` добавлены state-aware accessibility filters (`showing`) для `dump/click/type`;
      - локальные unit tests `site-control-kit` и `telegram_sandbox_activity_runner` после этого зелёные.
    - честный текущий live-result по новому `ak` route на `2026-05-01`:
      - search/open-chat path теперь реально проходит и сохраняет run artifacts:
        - `~/.local/share/telegram-sandbox-activity-runner/runs/20260501T163315-27fbb620/`;
      - статус этого smoke: `search_chat_opened_manual_review`;
      - то есть инструмент уже надёжно открывает внутренний чат через поиск, но следующий desktop-step (`Информация` / `Меню чата` / `Добавить в контакты`) ещё не подтверждён как реально меняющий UI-состояние Telegram на `AK`.
    - дополнительный прогресс на `2026-05-02` по `ak` desktop-only path:
      - `_normalize_contact` теперь сохраняет `search_result_index`, поэтому для ambiguous username можно жёстко зафиксировать нужную строку поиска в local config;
      - `prepare-add-contact-profile` больше не печатает username в placeholder search-node: порядок ввода через accessibility теперь `index=0 -> index=1`, а не наоборот;
      - после открытия профиля tool теперь проверяет exact username guard:
        - он ищет в profile overlay видимый `label @username` и не продолжает blind-add, если точное совпадение не найдено;
      - новый live smoke на `manual_super_pavlik`:
        - run: `~/.local/share/telegram-sandbox-activity-runner/runs/20260502T054306-8c3daf4f/`;
        - `search_result_target.index = 2`;
        - `profile_open_route = chat_header_click_fallback`;
        - `profile_username_exact_match_visible = true` для `@super_pavlik`;
        - verify тоже видит exact `@super_pavlik`, то есть баг "открыли не тот username и молча пошли дальше" закрыт;
      - остаточный локальный gap:
        - клик по `ДОБАВИТЬ КОНТАКТ` в profile overlay всё ещё не переводит UI в stable `Новый контакт -> Готово` в этом автоматическом run, хотя exact profile уже подтверждён и ручной live-path для этой кнопки отдельно воспроизводился.
      - затем этот gap был закрыт на том же `ak` actor:
        - submit `Готово` переведён с blind window-point на `dialog_submit_click`, вычисляемый от live-геометрии самой модалки `Новый контакт`;
        - clipboard path в `telegram_portable.py` после `Ctrl+V` теперь отправляет `End`, чтобы следующий click по `Готово` не тратился на снятие выделения текста;
        - после нескольких live-калибровок на `manual_super_pavlik` рабочая submit-точка зафиксировалась как:
          - `dialog_submit_click = { x_ratio: 0.5576, y_ratio: 0.7611 }`;
        - успешный live-run:
          - `~/.local/share/telegram-sandbox-activity-runner/runs/20260502T064226-de0a009a/`;
          - итоговый verify state: `ui_verify_contact_present`;
          - в profile verify уже видны `Edit contact` и `Delete contact`, а `Add contact` исчез.
  - дополнительно локально собран отдельный modular allowlist CLI на `Telethon`, не завязанный на `SiteControl` и portable UI:
    - launcher: `tools/telegram_sandbox_activity_runner/bin/telegram-allowlist-tool`;
    - package: `tools/telegram_sandbox_activity_runner/allowlist_tool/*`;
    - архитектура разложена на `validator.py`, `queue_manager.py`, `executor.py`, `safety.py`, `audit_log.py`, `report.py`;
    - режим только комплаентный: `allowlist.csv`, `actions.csv`, ручной `YES` confirm перед `send_message` и `add_to_group`, локальный лимит `20` действий в час, `5s` delay между API request, backoff на `FloodWaitError`, stop-account на `PeerFloodError`;
    - локально подтверждены:
      - `python3 -m py_compile tools/telegram_sandbox_activity_runner/allowlist_tool/*.py`;
      - `python3 -m unittest discover -s tests -p 'test_telegram_allowlist_tool.py'`;
      - `python3 -m unittest discover -s tests -p 'test_telegram_sandbox_activity_runner.py'`;
    - live Telegram calls этим новым CLI ещё не выполнялись; это пока локальный безопасный слой для allowlist-only сценариев.
- В репозитории остаётся много unrelated modified/untracked материалов; их нельзя автоматически считать мусором и нельзя откатывать без разбора.

### Что делать дальше
- Для звонкового контура:
  - применить в live ElevenLabs prompt новое правило автоответчика: не оставлять сообщение электронному помощнику, не отвечать на его уточнения, сразу логировать `no_answer + callback` и завершать звонок;
  - после правки прогнать ручной SIP/voicemail тест и проверить, что в transcript нет диалога с автоответчиком после первого machine/message-service сигнала;
  - проверить, что built-in `voicemail_detection` не проговаривает callback-текст; если ElevenLabs не допускает пустой voicemail message, не опираться на него для message-service и завершать через `end_call`;
  - в ближайшее рабочее окно проверить, что новые busy-отказы пишутся как `busy`, а не как `outbound_request_failed`;
  - отдельно проверить, что после свежего prompt-fix агент больше не ждёт ringback/hold по несколько минут и не говорит на literal ASR `музыка` / `...`;
  - подтвердить, что `dial_timeout_minutes = 5` больше не допускает повторный autodial того же лида через `1` минуту, пока предыдущий длинный вызов ещё активен;
  - если `provider_circuit_breaker` после этого всё ещё срабатывает, разбирать уже только реальные technical rejects/relay timeouts.
- Для email-контура:
  - пройти backlog `manual_review`;
  - решить, какие кейсы можно ещё автоматизировать, а какие оставлять только на ручную проверку;
  - периодически аудитить старые `sent`, если всплывут ещё исторические каталожные адреса.
- Для Telegram sandbox tool:
  - `AK2` API session уже авторизована через импорт из `tdata`, этот шаг больше не блокер;
  - но сам `AK2` как аккаунт сейчас уже не рабочая боевая цель из-за блокировки, поэтому его нужно считать frozen actor до ручного recovery;
  - рабочая локальная точка продолжения сейчас смещена на новый actor `ak` с portable-профилем `/home/max/TelegramPortableAK`;
  - ближайший практический приоритет для `ak` уже не в поиске контакта, а в последнем desktop transition:
    - `открытый chat -> Информация / Меню чата -> Показать профиль -> Добавить контакт`;
    - search/open-chat слой уже проходит и не должен больше переписываться обратно на `tg://resolve`;
  - этот переход уже подтверждён как рабочий минимум на `manual_super_pavlik`, поэтому следующий приоритет смещён:
    - убрать per-contact ручную калибровку submit-point;
    - проверить, что тот же dialog-submit path воспроизводится на других allowlist-профилях, а не только на одном smoke-case;
  - если продолжаем именно через `SiteControl`, использовать `ak.local.json`, а не старый `AK2` config;
  - следующий первый приоритет: получить новый рабочий source-of-truth для контактов, потому что текущие `562` imported `@username` не резолвятся в Telegram API как user-аккаунты;
  - для локального `owner_main` путь через поиск уже даёт chat window `Макс Михайлов`, так что это сейчас основной smoke-target для desktop route debugging;
  - отдельно полезно использовать новую команду `api-scan-contacts`, чтобы перед любым add сразу отделять live `types.User` от `not_found / non_user`;
  - после получения свежего списка сначала прогнать API scan/filter и сохранить только реально существующие `types.User`;
  - только потом повторно запускать `batch-add-contacts` уже по очищенному allowlist с реальной API-верификацией `check-contact`;
  - не пытаться лечить текущий stale dataset новыми blind UI-кликами: это больше не инструментальная проблема;
  - portable fallback можно улучшать отдельно, но он не должен подменять собой источник истины, когда API уже говорит `No user has "<username>" as username`.
  - для нового modular allowlist CLI ближайший следующий шаг не в массовых действиях, а в безопасном first live smoke:
    - взять один тестовый `accounts.csv`, один `allowlist.csv` с явно согласованным пользователем и один `actions.csv`;
    - сначала прогнать `validate-allowlist`;
    - затем один `send_message` или один `add_to_group` только с ручным `YES` confirm;
    - сохранить `audit.log.jsonl` и `telegram_allowlist_report.json` как новый source-of-truth по этому CLI;
    - не подключать его к сомнительным imported username-спискам до отдельной очистки allowlist через `api-scan-contacts`.
- Для документации:
  - после каждой значимой live-правки обновлять этот файл и модульный checkpoint соответствующего агента.

## 3) Последние важные изменения

### 2026-05-02 — Добавлен отдельный modular allowlist-only Telethon CLI для комплаентных Telegram-действий
- Рядом с существующим `telegram_sandbox_activity_runner.py` добавлен новый package:
  - `tools/telegram_sandbox_activity_runner/allowlist_tool/__init__.py`
  - `tools/telegram_sandbox_activity_runner/allowlist_tool/models.py`
  - `tools/telegram_sandbox_activity_runner/allowlist_tool/csv_loader.py`
  - `tools/telegram_sandbox_activity_runner/allowlist_tool/validator.py`
  - `tools/telegram_sandbox_activity_runner/allowlist_tool/queue_manager.py`
  - `tools/telegram_sandbox_activity_runner/allowlist_tool/executor.py`
  - `tools/telegram_sandbox_activity_runner/allowlist_tool/safety.py`
  - `tools/telegram_sandbox_activity_runner/allowlist_tool/audit_log.py`
  - `tools/telegram_sandbox_activity_runner/allowlist_tool/report.py`
  - `tools/telegram_sandbox_activity_runner/allowlist_tool/telethon_client.py`
  - `tools/telegram_sandbox_activity_runner/allowlist_tool/cli.py`
- Добавлен отдельный launcher:
  - `tools/telegram_sandbox_activity_runner/bin/telegram-allowlist-tool`
- Добавлены example CSV templates:
  - `tools/telegram_sandbox_activity_runner/examples/allowlist_tool/accounts.example.csv`
  - `tools/telegram_sandbox_activity_runner/examples/allowlist_tool/allowlist.example.csv`
  - `tools/telegram_sandbox_activity_runner/examples/allowlist_tool/actions.example.csv`
- Добавлен unit coverage:
  - `tests/test_telegram_allowlist_tool.py`
- Что умеет этот новый CLI:
  - импортировать `accounts.csv`, `allowlist.csv`, `actions.csv`;
  - валидировать allowlist usernames через `Telethon`;
  - строить preflight queue и блокировать действия вне allowlist или без `consent_confirmed=yes`;
  - выполнять только `validate`, `send_message`, `add_to_group`;
  - требовать ручной `YES` confirm перед `send_message` и `add_to_group`;
  - писать JSONL audit log и итоговый JSON report;
  - автоматически делать backoff на `FloodWaitError` и останавливать аккаунт на `PeerFloodError` / suspicious banned-response.
- Что принципиально не делает:
  - не использует ротацию аккаунтов для обхода лимитов;
  - не использует proxy-эвейжн;
  - не запускает массовые действия без ручного подтверждения;
  - не работает по данным вне `allowlist.csv`.
- Что уже проверено локально:
  - `python3 -m py_compile tools/telegram_sandbox_activity_runner/allowlist_tool/*.py`
  - `python3 -m unittest discover -s tests -p 'test_telegram_allowlist_tool.py'`
  - `python3 -m unittest discover -s tests -p 'test_telegram_sandbox_activity_runner.py'`
  - `PYTHONPATH="tools/telegram_sandbox_activity_runner" python3 -m allowlist_tool.cli --help`
- Live Telegram API/MTProto действия этим новым CLI пока не запускались; он добавлен как локальный комплаентный слой, который можно отдельно довести через controlled smoke.

### 2026-05-02 — Оформлен agent-ready handoff и отдельный GitHub-ready wrapper для Desktop contact-flow
- Внутри core tool добавлены:
  - `tools/telegram_sandbox_activity_runner/AGENTS.md`
  - `tools/telegram_sandbox_activity_runner/CHECKPOINT_RU.md`
- В `README_RU.md` самого runner добавлен отдельный вход для следующего агента и ссылка на внешний wrapper.
- Рядом с core tool добавлена отдельная папка:
  - `tools/telegram_desktop_contact_tool/`
- В нее вынесены:
  - `AGENTS.md`
  - `README_RU.md`
  - `bin/telegram-desktop-contact-tool`
  - `examples/usernames.example.txt`
- Этот wrapper не дублирует бизнес-логику runner, а дает короткий GitHub-friendly entrypoint для `import-usernames`, `add-one`, `batch-add`, `api-scan`.

### 2026-04-30 — Собран отдельный Telegram Sandbox Activity Runner для внутренних allowlist-чатов
- Добавлен standalone tool:
  - `tools/telegram_sandbox_activity_runner/telegram_sandbox_activity_runner.py`
  - `tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner`
  - `tools/telegram_sandbox_activity_runner/config.example.json`
  - `tools/telegram_sandbox_activity_runner/README_RU.md`
- Что умеет локально:
  - планировать и запускать `send_message`, `open_chat`, `idle_scroll` только в `allowlist_chats`;
  - проверять открытый Telegram chat по fragment/title перед любым действием;
  - вести `state.json` с cooldown, дневными лимитами и history;
  - импортировать подтверждённый список `@username` в `allowlist_contacts` через команду `import-contacts` с нормализацией, dedupe и отбрасыванием мусорных строк;
  - готовить operator-assisted `prepare-invite` для `allowlist_contacts` с остановкой перед финальным Telegram confirm по умолчанию;
  - готовить operator-assisted `prepare-join` с ручным финальным подтверждением по умолчанию;
  - готовить operator-assisted `prepare-add-contact-profile` для allowlist-`@username` через `telegram_portable.py` / Telegram Desktop portable.
- Добавлены operational обвязки:
  - systemd examples:
    - `deploy/systemd/telegram-sandbox-activity-runner.service.example`
    - `deploy/systemd/telegram-sandbox-activity-runner.timer.example`
  - unit tests:
    - `tests/test_telegram_sandbox_activity_runner.py`
- Что уже проверено локально:
  - `python3 -m py_compile tools/telegram_sandbox_activity_runner/telegram_sandbox_activity_runner.py`
  - `python3 -m unittest tests/test_telegram_sandbox_activity_runner.py`
  - dry-run smoke:
    - `plan`
    - `prepare-join`
    - `prepare-invite`
    - `prepare-add-contact-profile`
- Что дополнительно проверено live на локальной машине:
  - создан локальный config/state для actor `AK2`:
    - config: `~/.config/telegram-sandbox-activity-runner/ak2.local.json`
    - state: `~/.local/share/telegram-sandbox-activity-runner/ak2.state.json`
  - `prepare-add-contact-profile --execute --launch-if-needed` успешно:
    - поднял `TelegramPortable-AK2`;
    - открыл Telegram окно;
    - сохранил screenshot-артефакты в `~/.local/share/telegram-sandbox-activity-runner/runs/20260430T130300-fcf8c655/`.
  - Но screenshot показал важный остаточный gap:
    - сначала экран был в `Loading...`;
    - после дополнительной паузы chat list загрузился;
    - целевой профиль по `tg://resolve?...&profile` ещё не был подтверждён визуально, поэтому статус contact-path ужесточён до `profile_open_requested_manual_review`, а не `profile_opened_manual_review`.
  - После этого добавлен bulk-import approved username-list в локальный `AK2` config:
    - команда `import-contacts` загрузила `562` новых `@username` в `~/.config/telegram-sandbox-activity-runner/ak2.local.json`;
    - одна markdown-строка была корректно отброшена как invalid input;
    - общий локальный allowlist контактов стал `563` записей вместе с `owner_main`.
  - Дополнительный live smoke на импортированном `contact_id=import_a1exyc` показал:
    - `prepare-add-contact-profile --execute --launch-if-needed` уже открывает карточку профиля `@a1exyc`;
    - на screenshot видна кнопка `ADD TO CONTACTS`, то есть связка `AK2 + tg://resolve + portable` доходит до правильного UI-экрана;
    - при этом статус команды пока остаётся `profile_open_requested_manual_review`, потому что в коде ещё нет более сильной автоматической верификации открытого профиля.
  - Следующий controlled smoke с `--confirm-add --verify-profile-reopen` для `import_a1exyc` завершился успешно:
    - run artifacts: `~/.local/share/telegram-sandbox-activity-runner/runs/20260430T131751-b77b9175/`;
    - после `Add to contacts -> Done` повторное открытие профиля уже показывает `Edit contact` и `Delete contact`;
    - это подтверждает, что полный путь добавления контакта на `AK2` сейчас рабочий хотя бы для одного реального approved `@username`.
  - После этого tool расширен:
    - добавлен `api-status` для optional `Telethon` sidecar;
    - добавлен отдельный `telegram_api_sidecar.py` с командами `status`, `check-contact`, `add-contact`, `interactive-login`;
    - добавлен `batch-add-contacts` по списку `contact_id` с random pauses и `api_first -> portable fallback`;
    - локальный `AK2` config переведён в `api_first`, а секреты вынесены в локальный env-file `~/.config/telegram-sandbox-activity-runner/ak2.api.env`.
  - На `2026-05-01` tool дополнительно усилен:
    - в `telegram_api_sidecar.py` добавлена команда `import-tdata-session`;
    - в основном CLI добавлена команда `api-import-tdata-session`;
    - добавлена команда `api-scan-contacts` для формального API-resolve scan по allowlist `contact_id`;
    - добавлен совместимый `tgcrypto` shim через Telethon AES-IGE fallback;
    - добавлен relaxed reader для `opentele`, чтобы старый parser `map` не ломался на новых ключах Telegram Desktop (`lskCustomEmojiKeys = 0x17` и т.д.), пока `MTP authorization` всё ещё читается корректно.
    - `batch-add-contacts` теперь не уходит в `portable/UI` fallback, если API preflight уже вернул `not_found` или `resolved_non_user`;
    - `plan/run` теперь реально пропускают actors с `active: false`.
  - Новый live probe sidecar на `AK2` показал:
    - `api_id/api_hash` подключены;
    - `api-import-tdata-session` успешно поднимает Telethon session из `~/TelegramPortable-AK2/TelegramForcePortable/tdata` без ручного login code;
    - `api-status` после этого показывает `authorized` для `@S_e_r_a_p_h_i_na`.
  - Первый live batch на `20` импортированных `contact_id` уже прогнан:
    - batch run: `~/.local/share/telegram-sandbox-activity-runner/runs/20260430T134737-2b8ab872/`;
    - `successful_count = 20` на уровне UI flow;
    - но `verified_count = 0`, потому что API-session не авторизована и batch не может автоматически подтвердить сохранение контакта через MTProto.
  - После авторизации API уже снят более сильный технический диагноз:
    - `batch-add-contacts --backend api_only` на первых `30` импортированных `contact_id` дал `0` успешных add;
    - затем отдельный API scan добрал все `562` imported username и тоже дал `0` валидных `types.User`;
    - значит imported allowlist на `2026-05-01` практически целиком stale/invalid для Telegram username resolution, а не просто mixed по типам.
    - затем новая штатная команда `api-scan-contacts` на пользовательской выборке из `30` username снова показала `valid_user = 0`, `invalid_not_found = 30`, `resolved_non_user = 0`, `failed = 0`;
    - valid output file оказался пустым: `/tmp/ak2_valid_contact_ids_from_first30.txt`.
  - Контур по-прежнему усилен accessibility-веткой:
    - после `Add to contacts` tool теперь пытается заполнять `First name` / `Last name` и жать `Done` через AT-SPI accessibility, а координаты оставлены как fallback;
    - это устранило техническую ошибку выбора label-вместо-editable-field, но уже не является главным блокером после API-диагностики списка.
  - Важно:
    - инструмент пока не деплоился в live и не подключался к реальным internal Telegram browser sessions;
    - следующий шаг для него — получить свежий валидный username source и уже потом повторить API filter/add cycle;
    - `AK2` до ручного recovery лучше не размораживать и не использовать в новых add/activity попытках;
    - новый локальный portable actor `ak` уже подготовлен отдельно и может использоваться как новая desktop/site-control точка продолжения.

### 2026-04-30 — Исправлены длинные ожидания гудков и повторный autodial на тот же лид
- По live-логам `2026-04-30` подтверждено, что проблема была составной, а не одной:
  - `conv_9601kqf0hx99f2j9dr7y69qvc2e0` провисел `265` секунд (`4m25s`) до первой осмысленной живой реплики;
  - в transcript сначала были только `...`, потом спустя `225s` единичная раздражённая реплика, после чего агент выдал мягкий probing opener `Извините, если не вовремя. Вам удобно сейчас поговорить?`, чего в live быть не должно;
  - `conv_9401kqf0g2hjem8brcdnc1kgmt76` показал ещё один запретный хвост: `Я вас слушаю, можете говорить. Чем могу помочь?`;
  - `conv_3001kqf03876eap9m1qme74s431h` и `conv_4301kqf052y7f4sv7h1vtz0g18md` показали ранний opener на literal ASR `музыка`.
- Параллельно найден второй operational defect в dispatcher:
  - `row_27` был взят в работу дважды подряд;
  - `VOICE_INBOUND_AGENT` execution `46276` (`2026-04-30 13:56:01 MSK`) и `46281` (`2026-04-30 13:57:02 MSK`) создали два исходящих запроса на один и тот же лид;
  - в live Sheet этому соответствовали две `dialing`-строки подряд (`A198` и `A199`);
  - причина: `dial_timeout_minutes = 1`, поэтому длинный звонок ещё шёл, а dispatcher уже считал лид свободным.
- Исправление в live `AUTODIAL_DISPATCHER`:
  - `dial_timeout_minutes` увеличен с `1` до `5`;
  - это же значение теперь зашито в локальный сборщик `scripts/build_autodial_sheet_workflow.py` и в `workflows/AUTODIAL_DISPATCHER_DRAFT.json`;
  - запасные fallback-дефолты для `dial_timeout_minutes` внутри JS-логики тоже подняты до `5`, чтобы при потере поля run-context баг не вернулся тихо через старое `|| 1`;
  - цель правки: не давать новому autodial стартовать на тот же лид, пока предыдущий длинный ringback/hold вызов ещё жив.
- Исправление в live `Main` и `staging` ветках ElevenLabs:
  - prompt обновлён prompt-only patch'ем, без трогания `tool_ids` и tool-schema;
  - добавлен абсолютный pre-human cap: не висеть на линии дольше примерно `20s` до первой осмысленной человеческой реплики;
  - continuous ringback, queue-loops и hold music больше не должны продлевать ожидание;
  - literal ASR-маркеры `музыка`, `music`, `...`, дыхание, одиночное ругательство после долгих гудков и прочие non-directed fragments теперь явно запрещены как сигнал старта;
  - отдельно запрещены probing openers на неясной линии, включая:
    - `Извините, если не вовремя. Вам удобно сейчас поговорить?`
    - `Я вас слушаю, можете говорить. Чем могу помочь?`
- Новый live state после patch:
  - `Main` branch `agtbrch_7801kgybyg9nesrbv64y078pazq0` -> version `agtvrsn_7001kqf1jkffff0rrsk0yyfa62tt`
  - `staging-safe-test-2026-04-25` -> version `agtvrsn_3401kqf1jbzbfx18x4n43jvhjwt9`
  - `turn_timeout = 10.0`, `first_message = ""` сохранены.
- Backup и проверка:
  - `backups/2026-04-30_14-14-08_autodial_busy_reject_fix/`
  - `backups/2026-04-30_14-18-06_autodial_busy_reject_fix/`
  - `backups/2026-04-30_14-14-43_ringback_wait_fix/`
- После выкладки prompt-fix новых live-звонков ещё не было: рабочее окно уже закрылось, поэтому end-to-end подтверждение остаётся на следующее окно `10:00–14:00 MSK`.

### 2026-04-30 — Исправлена ложная provider-failure классификация для `SIP 486 Busy Here`
- По свежим live-логам `2026-04-30` подтверждено, что сам агент работает на текущей stable version `agtvrsn_5801kqc3ayw9fk38qqypkgzaj0dh`:
  - есть новые `done` разговоры;
  - `conv_9801kqek78p5entrmze88pydyhxt` показал корректное ожидание конца длинного IVR-пролога и старт opener только после живого ответа администратора;
  - запрещённый email-flow в свежих успешных разговорах не всплыл.
- Одновременно найдены `failed` conversation без `branch_id/version_id`, например:
  - `conv_4301kqem0wwtey9sxjkc62d8agwy`
  - `conv_7301kqekz2dme1vtr75ny9jbx65x`
- Разбор связанных `VOICE_INBOUND_AGENT` execution показал реальную причину:
  - webhook и runtime-поля приходили корректно;
  - `Eleven | Outbound HTTP` возвращал `INVITE failed: sip status: 486: Busy Here (SIP 486)`;
  - но dispatcher downstream всё равно писал `call_result = outbound_request_failed`.
- Из-за этого в том же окне live `AUTODIAL_DISPATCHER` ушёл в:
  - `reason = provider_circuit_breaker`
  - `message = Автодозвон поставлен на паузу: подряд накопились технические outbound-фейлы.`
- Исправление:
  - в live `AUTODIAL_DISPATCHER` логика `Postgres | Mark Outbound Failure` обновлена;
  - `SIP 486 Busy Here` теперь маппится в `call_result = busy`, `next_step = retry_busy`;
  - retry для такого busy идёт через `30 минут` либо на следующий день `10:15`, если дневной лимит попыток уже выбран;
  - только реальные технические upstream/provider rejects остаются `outbound_request_failed` и продолжают влиять на `provider_circuit_breaker`.
- На втором проходе в тот же день найден реальный runtime-нюанс:
  - dispatcher в бою получал не плоский ответ webhook, а envelope с `response_body`;
  - из-за этого строки `row_2` и `row_18` в `10:33` и `10:35 MSK` всё ещё записались как `outbound_request_failed`, хотя upstream уже вернул `Busy Here`.
- Финальный live-fix:
  - `Postgres | Mark Outbound Failure` теперь берёт `failureReason` из `response_body.note`, `response_body.eleven_response.message` и смежных вложенных полей;
  - первый новый живой кейс после правки подтвердил результат:
    - `VOICE_INBOUND_AGENT` execution `46152` (`2026-04-30 13:37:02 MSK`) получил `INVITE failed: sip status: 486: Busy Here (SIP 486)`;
    - `ELEVEN_TOOL_CALL_LOG_BRIDGE` execution `46156` (`2026-04-30 13:37:19 MSK`) уже записал `lead_id = row_17`, `call_result = busy`, `next_step = retry_busy`.
- Для восстановления текущего дня вручную исправлены четыре исторически ошибочные строки в live Sheet:
  - `A168`
  - `A170`
  - `A174`
  - `A177`
  Они были подтверждены как `Busy Here` по исходным `VOICE_INBOUND_AGENT` execution и переведены из `outbound_request_failed` в `busy`.
- После ручной переклассификации и повторного тика live `AUTODIAL_DISPATCHER` execution `46150` (`2026-04-30 13:37:01 MSK`) снова перешёл в `action = dial`, то есть автодозвон был реально выведен из дневного ложного стопа.
- Backup live workflow сохранён в:
  - `backups/2026-04-30_10-29-33_autodial_busy_reject_fix/`
  - `backups/2026-04-30_13-33-50_autodial_busy_reject_fix/`
  - `backups/2026-04-30_13-36-26_sheet_busy_reclassify/`

### 2026-04-29 — Email-followup агент доведен до рабочего production-контура и задокументирован
- Email-followup контур выделен как самостоятельный production-компонент:
  - service: `email_followup.service`;
  - scheduled workflow: `EMAIL_FOLLOWUP_AGENT_LIVE`;
  - manual workflow: `EMAIL_FOLLOWUP_AGENT_MANUAL_LIVE`.
- Для live закреплено безопасное расписание:
  - `09:00 MSK`
  - `15:00 MSK`
  чтобы не пересекаться с окном автодозвона.
- В письма добавлено обязательное PDF-вложение:
  - `КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ (2).pdf`
- В проде закреплены целевые таблицы:
  - `контакты_косметологов_москва_1`
  - `контакты_косметологов_москва_2`
  - `контакты_косметологов_москва_47`
- Подтверждены рабочие прод-компоненты email-контура:
  - SMTP;
  - IMAP bounce watcher;
  - Telegram reports;
  - `firecrawl-compat-bridge` для web-resolver.
- Исправлены реальные defects:
  - бот отчётов был привязан к чужому `chat_id`, теперь отчёты идут в `@M_a_x_i_m_M_i_k_h_a_i_l_o_v`;
  - добавлены фильтры платформенных доменов (`hh`, `zarplata`, `dreamjob`, `taplink`, `yclients`, `doct` и др.);
  - исправлена утечка старого seed email из `xlsx_import` строк в merged context;
  - исторические ложные кейсы на каталожные email переведены на переоценку.
- По факту live-проверки и отправок подтверждены рабочие кейсы:
  - `clinic@mesoreal.ru`
  - `medsi_beauty@medsigroup.ru`
  - `info@freshnail.online`
- Для будущих сессий создан подробный пакет документации:
  - `AGENTS.md`
  - `docs/email_followup_agent/README_RU.md`
  - `docs/email_followup_agent/01_ARCHITECTURE_AND_FLOW_RU.md`
  - `docs/email_followup_agent/02_LIVE_CONFIG_AND_SCHEDULE_RU.md`
  - `docs/email_followup_agent/03_SEARCH_RULES_AND_FILTERS_RU.md`
  - `docs/email_followup_agent/04_RUNBOOK_AND_OPERATIONS_RU.md`
  - `docs/email_followup_agent/05_TEST_REPORT_2026-04-29_RU.md`
  - `docs/email_followup_agent/06_CHECKPOINT_RU.md`

### 2026-04-29 — Из live prompt убран возврат в email-flow и ужаты паузы в живом разговоре
- По свежим live-разговорам после вчерашнего anti-IVR фикса подтверждено, что machine/welcome handling стало лучше:
  - `conv_5301kqc0wctkffvvecan8vn5kz8v` корректно дождался живого администратора после длинного welcome-скрипта и не открылся поверх записи;
  - `conv_4301kqc1b10ped08m5ft7jatgdbk` после длинного branded intro вообще не стартовал sales-opener, что соответствует новому human-gate.
- Но всплыл другой остаточный дефект в старом sales-flow:
  - `conv_0501kqc0y89tf9rv7enx7xmbgyeh` агент снова ушёл в сбор email, произнёс `Вы на связи? Готова записать почту...` и растянул звонок на паузах;
  - `conv_5001kqc2hg01e1sr3vker1yy4h9y` и summary `Lipolong Offer Email` показали возврат к почтовому сценарию, хотя live follow-up уже давно переведён на SMS / callback / manager contact.
- Причина:
  - в live prompt было достаточно запретов на IVR и opener noise, но не было жёсткого запрета на email-follow-up и на зависание в mid-call паузах ради диктовки почты.
- Исправление:
  - в live prompt добавлен прямой запрет на сбор, диктовку, повтор и проверку email-адресов;
  - если собеседник просит `отправить на почту`, агент теперь должен предлагать только SMS на текущий номер, короткий контакт менеджера или callback;
  - если администратор настаивает только на почте и не принимает другие варианты, агент оставляет короткий callback-контакт, логирует `send_kp_pending_callback` и завершает разговор;
  - отдельно запрещены реплики `Продиктуйте, пожалуйста, почту`, `Готова записать почту`, `Отправим информацию на почту`, `Вы на связи? Готова записать...`;
  - на паузах вида `сейчас, одну минуту` агент может коротко подождать один раз, но не должен сервисно перепроверять линию и не должен висеть на звонке ради записи email.

### 2026-04-28 — Ужесточён human-answer gate против раннего старта на брендовых приветствиях и шуме
- По свежим live-логам `Main` найдены реальные ложные старты на текущей stable version `agtvrsn_3201kq1w28bnf00rhgss8kkt9j3c`:
  - `conv_7101kq9fb4fzfkjstzk96wj1dy0k` — после `...` агент выдал запрещённую rescue-фразу `Я вас слушаю, вы на связи? Чем могу помочь?`;
  - `conv_5001kq9g15gvfa6r7d5j45vha4b4` — opener стартовал на garbled branded fragment;
  - `conv_3901kq9fd02kek59xsve5j7y1zty` — opener стартовал на сомнительном intro-фрагменте;
  - `conv_6901kq9f05p3fhv8pkf8sebqy1bs`, `conv_6601kq9ehhc6f03b01ddqzegf2yn` — opener уходил после длинного брендового welcome/hold сценария вместо тихого `no_answer`.
- Корень найден в самом live prompt:
  - в `Critical opening mode` всё ещё было правило `a clinic name` как достаточный human-signal;
  - этого оказалось достаточно, чтобы модель местами принимала брендовый/клинический intro, partial ASR и garbled fragments за живой старт.
- Live fix применён prompt-only patch через Eleven API:
  - сначала на test/staging branch `agtbrch_6001kq1w2xtkfp8sp9fgkxejm3t9`;
  - затем на stable `Main` `agtbrch_7801kgybyg9nesrbv64y078pazq0`.
- Что именно изменено:
  - убрано правило `a clinic name` как достаточный live-human trigger;
  - явно закреплено, что название клиники/компании/бренда/города/отдела само по себе не считается human-answer;
  - брендовые приветствия, слоганы, `спасибо за звонок`, partial ASR fragments и garbled intros теперь требуют ещё одного чистого человеческого ответа;
  - если после такого intro ответа нет, агент должен молчать и завершать `no_answer`, а не открываться сам;
  - отдельно запрещена точная rescue-фраза `Я вас слушаю, вы на связи? Чем могу помочь?`.
- Важная техническая деталь:
  - полный `PATCH conversation_config` снова упёрся в известный хвост Eleven API `Cannot specify both tools and tool IDs`;
  - рабочим способом оказался узкий prompt-only patch, который не трогает tool-schema.
- После live patch проверено:
  - `Main` перешёл на новую stable version `agtvrsn_3501kq9py63pexhr2th2w1v9ewv2`;
  - `turn_timeout = 10.0` сохранился;
  - `first_message = ""` сохранился;
  - `tool_ids` остались теми же: `tool_1601km62rxpqegqr52m9gk9sftr3`, `tool_8601km62h97qft5b3nfprvxnvdkd`, `tool_1701km86jmcpek4rj2j1rbhxqtfr`;
  - active `tools` не пропали;
  - backup и кейсы сохранены в `backups/2026-04-28_12-31-36_human_gate_early_start_fix/`.

### 2026-04-27 — Live автодозвон и call_log переключены на новую рабочую Google Sheet
- Текущая рабочая таблица для live-call-center переключена на:
  - `https://docs.google.com/spreadsheets/d/1t0FtCL84l0QJvL9_7XDnmafJS1NHUSdiVyKgqNWOVmA/edit?gid=199760593#gid=199760593`
- Важно, что сохранён тот же целевой `gid = 199760593`, а реальное имя вкладки подтверждено как `Лиды_обзвон`.
- Переключение сделано синхронно в двух live workflow:
  - `AUTODIAL_DISPATCHER`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE`
- Это важно, потому что dispatcher и `call_log` должны смотреть в один и тот же `spreadsheet_id`; если переключить только один из них, агент снова начнёт читать и писать в разные таблицы.

### 2026-04-25 — Восстановлен stable live Main, возвращён tightened prompt и введена безопасная branch-дисциплина
- После серии test-звонков с instant drop подтверждено, что причина была не в самом prompt:
  - сначала live-agent ссылался на удалённый `call_log` tool id и часть звонков вообще не доходила до нормальной agent-version/branch;
  - затем временная замена на новый `call_log` с жёсткой dynamic-variable schema ломала manual/SIP test на старте разговора с ошибкой `Missing required dynamic variables in tools`, ещё до полноценного `accepted_time`.
- В результате stable live был собран заново на `Main`:
  - branch `Main` `agtbrch_7801kgybyg9nesrbv64y078pazq0` снова получает `100%` live traffic;
  - опубликована новая stable version `agtvrsn_3201kq1w28bnf00rhgss8kkt9j3c`;
  - в `Main` возвращён последний tightened prompt до rollback:
    - `turn_timeout = 10.0`;
    - ожидание после machine/hold/ringback = `10` секунд;
    - ожидание после opener без ясного ответа = `4` секунды;
    - короткий voicemail/message-service callback сохранён.
- При этом live `call_log` переведён на валидный relaxed tool:
  - `tool_8601km62h97qft5b3nfprvxnvdkd` -> `call_log`;
  - на stable live убрана жёсткая dynamic-variable schema у `call_log`, чтобы manual/SIP test не падал ещё до начала разговора;
  - runtime-идентификаторы по-прежнему передаются и должны использоваться агентом, но schema-level enforcement теперь не включается напрямую на `Main`.
- Для будущих безопасных тестов заведена отдельная ветка ElevenLabs:
  - `staging-safe-test-2026-04-25` -> `agtbrch_6001kq1w2xtkfp8sp9fgkxejm3t9`;
  - она держится на `0%` live traffic и предназначена для prompt/tool experiments без риска для продового обзвона.
- На стороне GitHub тоже разведены роли веток:
  - `origin/main` остаётся продовой базой;
  - создана отдельная staging-ветка `origin/codex/eleven-agent-staging` для будущих безопасных изменений и PR-потока.
- Новое операционное правило:
  - backup перед live patch обязателен;
  - любые risky-изменения `tool_ids`, `call_log`, built-in tools и dynamic-variable schema сначала делать только на Eleven staging-ветке;
  - в live `Main` продвигать только уже проверенную конфигурацию.

### 2026-04-21 — В автодозвоне убран холостой цикл с пустыми номерами
- По live-логам обнаружено, что часть `outbound_request_failed` рождалась не из-за разговора и не из-за лимитов, а из-за строк без нормального `E.164` номера.
- Это приводило к пустому `to_number`, после чего `VOICE_INBOUND_AGENT` завершался на `validation_failed` ещё до реального outbound-вызова.
- В `AUTODIAL_DISPATCHER` добавлен safe-фильтр:
  - кандидат должен иметь валидный dialable phone;
  - в outbound теперь уходит только нормализованный `E.164` номер;
  - пустые и кривые номера исключаются до звонка.
- Эффект:
  - меньше бессмысленных execution'ов;
  - меньше шума в `call_log`;
  - меньше технического цикла, который не даёт живого разговора и не приносит пользы.
- В тот же день дополнительно усилены защитные правила:
  - после `3` подряд свежих `outbound_request_failed` dispatcher уходит в `provider_circuit_breaker`;
  - если накопилось слишком много чисто технических исходов без живых разговоров, dispatcher завершает с причиной `tech_waste_limit_reached`;
  - в execution output теперь возвращается человеческое `message`, чтобы было понятнее, почему autodial встал;
  - таблица обзвона по-прежнему live-привязана к:
    `https://docs.google.com/spreadsheets/d/1FUHh8lS8pEx58eRK2Rt6AYn3cy6ogWSO32vZWqYw_Fc/edit?gid=199760593#gid=199760593`

### 2026-04-23 — Усилена трассируемость `call_log` и исправлен реальный live-кейс без идентификаторов
- Найден разговор `conv_3401kptc3wxcerrtqt28nam3hfxf`, который записался в Sheet без `lead_id`, `phone_primary`, `source_record_key` и `eleven_conv_id`.
- Причина: live-агент вызвал `call_log` почти пустым payload'ом, передав только `interest_level`, `call_result`, `next_step` и `notes_short`.
- После этого добавлены два слоя защиты:
  - в live prompt агент теперь обязан всегда передавать минимальный паспорт звонка в `call_log`;
  - в `ELEVEN_TOOL_CALL_LOG_BRIDGE` усилены fallback-правила нормализации, чтобы частично заполненный payload не терял номер и conversation id, если они есть.
- Следом найден второй live-дефект: модель местами начала буквально отправлять строки `system__called_number` и `system__conversation_id` вместо реальных значений.
- Live prompt дополнительно ужесточён: теперь прямо запрещено передавать буквальные имена системных переменных в `call_log`.
- Поверх этого добавлен более структурный fix:
  - в outbound-запуск разговора прокидываются runtime-идентификаторы через `conversation_initiation_client_data`;
  - `call_log` bridge теперь вычищает буквальные плейсхолдеры (`system__called_number`, `system__conversation_id`, `{{lead_id}}` и т.п.) и не пишет их в Sheet как будто это реальные значения.
- На этом же этапе найден более глубокий корень проблемы:
  - часть appended outcome-строк в Google Sheet уже хранила `lead_id/source_record_key` как номер телефона, а не как стабильный `row_*`;
  - из-за этого `AUTODIAL_DISPATCHER` местами начинал передавать в outbound номер как identity лида, и traceability снова ломалась уже до `call_log`;
  - live parser dispatcher обновлён: теперь он канонизирует историю по `phone_primary` обратно к seed-строке `xlsx_import` и восстанавливает `canonical lead_key`, `source_record_key` и `sheet_row_number`;
  - после этого в свежих execution исторические `elevenlabs/autodial_dispatcher` outcome-строки снова резолвятся к `row_*`, а не к телефону.
- Дополнительно ужесточён сам счётчик живых разговоров:
  - в дневной live-limit теперь попадают только строки `elevenlabs` с валидным `eleven_conv_id` формата `conv_...`;
  - мусорные строки вида `system__conversation_id`, `Алло!` и похожие псевдо-идентификаторы больше не считаются живым разговором.
- После анализа перерасхода лимитов и токенов добавлен отдельный anti-waste слой в autodial:
  - дневной лимит `dialing` снижен до `50`;
  - введён жёсткий дневной стоп по коротким non-human разговорам (`busy`, `no_answer`, `send_kp_pending_callback` с валидным `conv_...`) на уровне `10`;
  - введён дневной стоп по `outbound_request_failed` на уровне `8`;
  - это нужно, чтобы автодозвон не сжигал ресурсы на коротких машинных, секретарских и технических сессиях даже в те дни, когда живых продажных разговоров мало.
- Live-agent дополнительно ужат по wait-логике:
  - `turn_timeout` в ElevenLabs live снижен до `10.0`;
  - окно ожидания после машинной фразы / музыки / ringback ужато до `10` секунд;
  - окно ожидания ясного ответа после opener ужато до `4` секунд.
- Ограничение этого шага:
  - сам built-in `voicemail_message` через Eleven API отдельно не переписался из-за конфликта `tool_ids/tools`;
  - но live prompt уже обновлён, а текущее voicemail-сообщение и так остаётся коротким.
- Важное ограничение:
  - попытка жёстко привязать live `call_log` tool-schema к Eleven dynamic variables через API на этом шаге не была успешно завершена;
  - поэтому рабочий live-фикс сейчас опирается на runtime-идентификаторы в outbound, очистку плейсхолдеров в bridge и canonicalization внутри dispatcher, а не на автоматически пересобранную tool-schema.

### 2026-04-13 — Автодозвон и call_log переведены на новую рабочую таблицу обзвона
- Для live-обзвона и live `call_log` источник переключён на новую Google Sheet:
  - `https://docs.google.com/spreadsheets/d/1FUHh8lS8pEx58eRK2Rt6AYn3cy6ogWSO32vZWqYw_Fc/edit?gid=199760593#gid=199760593`
- Сохранён прежний `gid = 199760593`, поэтому логика выбора вкладки по `gid` осталась валидной.
- Синхронизированы:
  - `AUTODIAL_DISPATCHER`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE`
  - draft-файлы workflow в репозитории
  - документация по `call_log` и автодозвону
- Важное правило сохранено:
  - dispatcher и `call_log` должны смотреть в один и тот же `spreadsheet_id`, иначе автодозвон снова начнёт читать не ту очередь.

### 2026-04-11 — По логам `8–9 апреля` усилены machine-handling и ограничения автодозвона
- Сняты и перепроверены разговоры ElevenLabs за `2026-04-08` и `2026-04-09`.
- Подтверждены проблемные паттерны:
  - consent/recording-фразы вроде `Продолжая разговор, вы соглашаетесь...` местами принимались за живой ответ;
  - часть busy/unavailable-машинных реплик провоцировала ответную речь агента;
  - message-service в ряде кейсов нужно было завершать без qualification и без sales-pitch.
- На основе этих логов обновлён live prompt `AI_CALL_AGENT_1`:
  - consent/recording и transfer/hold/ringback переведены в жёсткий режим ожидания;
  - машинные фразы `абонент сейчас не может ответить / телефон занят / недоступен` теперь описаны как immediate `busy/no_answer`, без ответной речи;
  - message-service ограничен одним коротким callback-сообщением с номером менеджера;
  - запрещены реплики `Здравствуйте. Чем могу быть полезна?`, `Я вас слушаю`, `Вы на связи?`, а также повтор машинной фразы про недоступного абонента;
  - если клиент говорит `не звоните нам больше`, разговор должен фиксироваться как `dnc`.
- Для live `AUTODIAL_DISPATCHER` добавлено и синхронизировано:
  - `daily_attempt_limit_per_lead = 2`
  - `monthly_touch_limit_per_phone = 1` для нового cold-touch в пределах месяца
  - исключение для явного клиентского callback
  - сохранён `max_unreachable_total = 3`
- Обновлены:
  - `docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_EN.md`
  - `docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_RU.md`
  - `docs/call-translation-bridge/08_LIVE_ELEVEN_AGENT_RU.md`
  - `docs/call-translation-bridge/10_AUTODIAL_DISPATCHER_RU.md`
  - `документация_для_агента/04_ELEVENLABS_АГЕНТ.md`
  - `документация_для_агента/02_ТЕКУЩЕЕ_LIVE_СОСТОЯНИЕ.md`

### 2026-04-11 — Проверены локальные рабочие материалы и правила обращения с ними
- Отдельно перепроверены untracked-материалы в repo-root, чтобы не путать рабочие артефакты с техническим мусором.
- Подтверждено как рабочие материалы:
  - `agent_contact_parser_docs/`
  - `MANGO_отчеты/`
  - `Документация по скриптам `
  - ` Таблицы_контактов `
  - `workflows/Peptide_Expert_YJdwp45LI1dmrsLy_runtime_2026-03-02.json`
- Подтверждено, что `Peptide_Expert_YJdwp45LI1dmrsLy_runtime_2026-03-02.json` — это валидный экспорт активного workflow, а не случайный runtime-мусор.
- Для следующих сессий добавлен отдельный справочник:
  - `docs/knowledge_base/11_LOCAL_WORKING_MATERIALS.md`
- В `.gitignore` добавлены только безопасные локальные ignore-правила:
  - `Postgres/key.txt`
  - `__pycache__/`
  - `*.pyc`
- Важное ограничение:
  - каталоги `Документация по скриптам ` и ` Таблицы_контактов ` имеют реальные пробелы в именах;
  - не переименовывать их без coordinated update документации и ссылок.

### 2026-04-11 — Зафиксирован runbook по прод-серверу `147.45.213.87` и clean deploy
- По локальной проверке подтверждено, что текущий `HEAD` репозитория: `7c27614`, а в коде реально присутствуют server-side артефакты из прод-отчёта:
  - `scripts/n8n-autodeploy-clean.sh`
  - `scripts/backup_n8n.sh`
  - `scripts/restore_n8n.sh`
  - `scripts/validate_env.sh`
  - `sql/006_observability.sql`
- Создан отдельный handoff/runbook для будущих LLM/AI-сессий:
  - `docs/knowledge_base/10_SERVER_ACCESS_147_45_213_87.md`
- В нём зафиксированы:
  - канонические адреса и рабочие пути сервера `147.45.213.87`;
  - различие между `рабочим продом` `/home/aicore/n8n-server` и `clean deploy clone` `/home/aicore/n8n-ai-clean`;
  - рекомендуемая cron-команда для `/usr/local/bin/n8n-autodeploy-clean`;
  - правило не хранить root-пароль в репозитории;
  - чеклист для следующей live-сессии по SSH, git, Docker и backup-проверке.
- Обновлены связанные документы:
  - `01_INFRASTRUCTURE_AND_WORKSPACES.md`
  - `03_AUTOMATION_BACKUP_RESTORE.md`
  - `05_SECURITY_ACCESS_POLICIES.md`
  - `README.md` в `docs/knowledge_base`
- Важное ограничение:
  - live-доступ на `147.45.213.87` из текущей локальной сессии не подтверждён;
  - SSH-проверка с `BatchMode=yes` вернула `Permission denied (publickey,password,keyboard-interactive)`;
  - значит состояние сервера пока частично подтверждено отчётом предыдущей сессии и кодом, но не прямой live-проверкой через shell.

### 2026-04-11 — Доукомплектован прод-пакет: clean autodeploy, backup `call_center`, фиксы docs
- Исправлен важный хвост в репозитории:
  - из `docker-compose.memory.yml` удалён `postgrest` healthcheck, который ломал clean deploy из-за отсутствия `/bin/sh` в образе `postgrest/postgrest:latest`.
- Усилен `scripts/n8n-autodeploy-clean.sh`:
  - добавлена проверка обязательных файлов;
  - добавлен вызов `validate_env.sh`;
  - добавлен `up -d --remove-orphans`;
  - добавлен пост-деплой `healthcheck_all.sh`;
  - сохранено идемпотентное применение `sql/006_observability.sql`.
- Добавлены новые operational-скрипты:
  - `scripts/backup_call_center_postgres.sh` — отдельный dump `call_center` Postgres с gzip, checksum, retention и lock;
  - `scripts/install_n8n_autodeploy_cron.sh` — установка `/etc/cron.d/n8n-autodeploy-clean`.
  - `scripts/install_prod_ssh_key_147.sh` — helper для установки выделенного SSH-ключа на `147.45.213.87` при наличии разового парольного доступа.
- Для будущих сессий подготовлен выделенный SSH-ключ и alias на машине `max`:
  - `~/.ssh/n8n_ai_call_center_prod_147_ed25519`
  - alias `ai-core-prod-147`
- Но это только подготовка клиента:
  - сам публичный ключ ещё нужно установить на сервер `147.45.213.87`;
  - до этого момента безпарольный вход остаётся неподтверждённым.
- Обновлены серверные docs:
  - `03_AUTOMATION_BACKUP_RESTORE.md`
  - `10_SERVER_ACCESS_147_45_213_87.md`
- Ограничение остаётся прежним:
  - без рабочего доступа на `147.45.213.87` эти изменения пока подготовлены в git, но не подтверждены live-запуском на сервере.

### 2026-04-11 — Live `147.45.213.87` нормализован: SSH, clean deploy, cron, backup
- На сервер `147.45.213.87` установлен выделенный публичный SSH-ключ для машины `max`.
- Рабочий вход теперь подтверждён:
  - `ssh ai-core-prod-147`
- На live-сервере подтверждены каталоги:
  - рабочий прод: `/home/aicore/n8n-server`
  - clean deploy: `/home/aicore/n8n-ai-clean`
- Clean deploy-клон приведён к чистому `origin/main` и больше не держит вечные локальные diff по compose-файлам.
- В `.env.https` clean-клона установлен:
  - `SERVER_RUNTIME_ROOT=/home/aicore/n8n-server`
- Обновлён live wrapper:
  - `/usr/local/bin/n8n-autodeploy-clean`
- Подтверждено, что cron автодеплоя уже включён и сейчас работает:
  - `/etc/cron.d/n8n-autodeploy-clean`
  - `*/5 * * * * root /usr/local/bin/n8n-autodeploy-clean`
- Отдельно включён backup `call_center` Postgres:
  - ручной smoke-test `scripts/backup_call_center_postgres.sh` прошёл успешно;
  - создан dump `call_center_2026-04-11_07-09-19.sql.gz`
  - установлен cron:
    - `/etc/cron.d/n8n-callcenter-backup`
    - `10 3 * * * root cd /home/aicore/n8n-ai-clean && ./scripts/backup_call_center_postgres.sh >> /home/aicore/n8n-backups/postgres/call_center_backup.log 2>&1`
- Ручной compose smoke-test из clean-клона прошёл:
  - подняты `postgres`, `postgres_memory`, `postgrest`, `adminer`
  - `n8n`, `traefik`, `redis` остались healthy
- Выявлены и закрыты два operational хвоста:
  - `postgrest` healthcheck в репозитории удалён;
  - `healthcheck_all.sh` исправлен, чтобы не путать `postgrest` с `postgres` и не проверять `n8n` через несуществующий `node` binary.

### 2026-04-07 — Live-autodial обновлён под rule set `2/day + 3 unreachable` и включён human-answer gate
- Для live workflow `AUTODIAL_DISPATCHER (sheet-first draft)` найден и использован рабочий путь сохранения через публичный `n8n` API с минимальным телом `name + nodes + connections + settings`.
- Live dispatcher обновлён без пересоздания workflow:
  - `cron = */1 * * * *`
  - окно обзвона `10:00–14:00` МСК
  - `daily_attempt_limit_per_lead = 2`
  - `max_unreachable_total = 3`
  - добавлена ветка `Retire` для архивирования номера как нерабочего после третьей недоступности
  - для одинакового номера больше не допускается более `2` автодозвонов в день, если нет явного клиентского callback
- Для `AI_CALL_AGENT_1` обновлено live-поведение старта разговора:
  - `first_message = ""`
  - первая живая реплика агента после подтвержденного человеческого ответа: `Здравствуйте.`
  - `turn_timeout = 15.0`
  - `turn_eagerness = normal`
  - `speculative_turn = false`
  - включены built-in tools `skip_turn` и `voicemail_detection`
  - prompt переведен в режим `human-answer gate`: `IVR/hold/ringback -> wait`, `voicemail -> short callback message`, `temporarily unavailable -> no_answer`
  - после просмотра первого live-диалога opener скорректирован на более понятный business-entry:
    - убрана формулировка `у вас это направление уже в работе или пока только смотрите`
    - новый opener идёт через `официальный представитель + сотрудничество + вам это интересно`
  - возвращён `pronunciation_dictionary_locators`, который был временно потерян при patch-обновлении `conversation_config`
- Сняты backup-файлы:
  - `backups/2026-04-07_human_gate_autodial_refresh/autodial_live_before_put.json`
  - `backups/2026-04-07_human_gate_autodial_refresh/autodial_live_after_put.json`
  - `backups/2026-04-07_ivr_human_gate_live_refresh/eleven_agent_before.json`
  - `backups/2026-04-07_ivr_human_gate_live_refresh/eleven_agent_after.json`

### 2026-04-06 — Relay для outbound ElevenLabs вынесен на отдельный сервер
- Первичный локальный relay через ноутбук использовался только как временный обход и выведен из live-контура.
- Финальная рабочая схема на сегодня:
  - live `n8n` на `147.45.213.87`
  - relay на отдельном сервере `151.241.228.232`
  - live `VOICE_INBOUND_AGENT (draft)` ходит в:
    - `http://151.241.228.232:8787/eleven/outbound-call`
- На relay-сервере поднят systemd-сервис:
  - `/opt/eleven_outbound_relay.py`
  - `/root/.eleven_outbound_relay.env`
  - `/etc/systemd/system/eleven-outbound-relay.service`
- Найдена и исправлена причина таймаута live outbound:
  - `n8n` работал не на relay-сервере;
  - firewall relay-сервера не пускал трафик на `8787/tcp`;
  - добавлено правило доступа только от IP live `n8n`:
    - `147.45.213.87 -> 151.241.228.232:8787/tcp`
- После исправления:
  - invalid test number -> корректный `provider_rejected` с JSON `SIP 403`;
  - route `n8n -> server relay -> ElevenLabs` подтвержден живым smoke-test.
- В live workflow `VOICE_INBOUND_AGENT (draft)` сохранена логика:
  - HTML/challenge response -> `provider_rejected`;
  - `success=false` от Eleven -> `provider_rejected` даже если есть `conversation_id`;
  - `success=true` и валидный payload -> `call_requested`.
- Документация по актуальной relay-схеме:
  - `docs/call-translation-bridge/11_ELEVEN_OUTBOUND_RELAY_RU.md`

### 2026-04-06 — Проведен live smoke-test outbound-call и исправлена ложная success-ветка
- Выполнен live-тест `5` исходящих запросов по первым строкам рабочей таблицы `Лиды_обзвон`.
- Результат теста:
  - `n8n` принимал webhook-запросы успешно;
  - сами outbound-вызовы не подтверждались реальным API-ответом ElevenLabs;
  - вместо JSON API upstream возвращал HTML challenge/block page (`Cloudflare / help.elevenlabs.io`), поэтому реальные звонки из этого контура не подтвердились.
- Из-за этого старый outbound bridge ошибочно возвращал `action = call_requested`, хотя провайдер фактически не дал валидный ответ на создание звонка.
- Live workflow `VOICE_INBOUND_AGENT (draft)` обновлен:
  - `Eleven | Build Success Response` теперь проверяет, что upstream-ответ похож на валидный accepted payload;
  - HTML / challenge / block page теперь помечаются как `ok = false`, `action = provider_rejected`;
  - это позволяет `AUTODIAL_DISPATCHER` корректно видеть отказ провайдера и не считать такой запрос успешным.
- Для live снят backup перед правкой:
  - `backups/2026-04-06_outbound_provider_fix/VOICE_INBOUND_AGENT_before_provider_fix.json`

### 2026-04-06 — Исправлен критичный рассинхрон таблиц для автодозвона
- Найден и исправлен баг в `AUTODIAL_DISPATCHER`: workflow читал старый `spreadsheet_id` `1E-VCKAv4vF_SFLY8DgW0UC80FvAC_DDIxbSbi8GC8kU`, тогда как live `call_log` и рабочая таблица уже были переведены на тогдашнюю рабочую Google Sheet `1pLrCNeQ_thipr5-fajPusgNZZSd5NHEZFmGkegfpIqI`.
- Из-за этого dispatcher мог корректно стартовать по расписанию, но смотреть не в ту таблицу и не видеть актуальную очередь обзвона.
- Репозиторный draft и документация приведены к одному источнику истины:
  - `https://docs.google.com/spreadsheets/d/1pLrCNeQ_thipr5-fajPusgNZZSd5NHEZFmGkegfpIqI/edit`
- Дополнительно dispatcher переведен на выбор целевой вкладки по `gid = 199760593`, чтобы ссылка на нужный таб была достаточной для настройки.
- Отдельно исправлен критичный routing-bug: у `Dispatcher | Exhaustion Switch` были перепутаны выходы, из-за чего ветка `dial` уходила в `Finish Exhausted` вместо `Claim Next Lead`. Live workflow обновлен и активен на версии `72288ab6-a401-4f16-90b2-a8ec3a8a8bc7`.

### 2026-04-05 — Автодозвон переведен на sheet-first runtime и активирован в live n8n
- Live workflow `AUTODIAL_DISPATCHER` переведен на Google Sheet-only контур:
  - источник истины: `Лиды_обзвон`;
  - state/runtime хранится прямо в той же таблице через append-only lock и outcome rows;
  - Postgres-схема `sql/005_autodial_dispatcher.sql` осталась как исторический draft и в live не используется.
- Логика диспетчера:
  - запускается каждые 5 минут;
  - звонит только в окне `10:00–14:00` по МСК;
  - считает дневной лимит только по живым разговорам;
  - ограничивает дневной объем до `15` живых разговоров;
  - держит максимум `3` попытки на контакт в одном цикле;
  - при исчерпании списка переводит кампанию в `exhausted` и не запускает ее заново автоматически.
- Runtime теперь работает через:
  - `call_log` как lock/history append-only webhook;
  - `source_system = autodial_dispatcher` для lock-строк;
  - `source_system = elevenlabs` для фактических live call-log строк;
  - `POST /webhook/eleven/outbound-call` для outbound-звонка.
- Подробное описание актуального sheet-first контура вынесено в `docs/call-translation-bridge/10_AUTODIAL_DISPATCHER_RU.md`.

### 2026-04-04 — Live system prompt переведен на английский при сохранении русского диалога
- Для `AI_CALL_AGENT_1` live system prompt переведен на английский, но язык разговора с клиентом сохранен русским.
- Важно:
  - `first_message` не менялась;
  - `voice_id`, `speed`, `stability`, `similarity_boost` не менялись;
  - spoken language в агенте остается `ru`.
- Причины переключения подтвердились на последних live-звонках:
  - агент иногда слишком рано уходил в квалификацию, хотя клиент еще не понял кто звонит и что предлагается;
  - при растерянности клиента агент местами соединял длинное объяснение, предложение SMS и новый вопрос в одном ходе;
  - при слабом ответе или `...` мог повторить почти тот же вопрос, вместо более простой переформулировки.
- В английскую версию prompt отдельно добавлены правила:
  - всегда говорить с клиентом только по-русски;
  - если клиент запутался, сначала коротко восстановить контекст (`кто вы / что предлагаете`), а уже потом возвращаться к квалификации;
  - не складывать объяснение продукта, SMS и новый qualifying question в один перегруженный ход.
- Следующим refresh-блоком prompt дополнительно усилен под краткую выгодную презентацию:
  - если клиент подтверждает релевантность коррекции фигуры или инъекционных методик, агент должен в ближайшие 1-2 хода дать короткий `value reveal`, а не только продолжать диагностику;
  - добавлены внутренние правила `status-oriented framing`, `low-risk entry` и `news-style pitch`;
  - разрешено мягко говорить про расширение линейки услуг, рост среднего чека, дополнительный повод для возврата клиентов и сравнение экономики процедуры, но без гарантий результата.
- После первых live-звонков обновление было дополнительно сокращено по размеру:
  - длинный prompt давал более сильный sales-tonality, но увеличивал латентность и местами приводил к перегруженным концовкам;
  - live-версия ужата примерно с `15.6k` до `6.8k` символов;
  - сохранены только правила, которые напрямую влияют на скорость, value reveal, objection handling и следующий шаг.
- Файлы:
  - `docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_EN.md`
  - `backups/2026-04-04_english_prompt_switch/`
  - `backups/2026-04-04_value_reveal_prompt_refresh/`
  - `backups/2026-04-04_short_prompt_refresh/`

### 2026-04-04 — Добавлен corpus-based pronunciation dictionary для live-агента
- Для `AI_CALL_AGENT_1` создан и подключён отдельный pronunciation dictionary в ElevenLabs:
  - `dictionary_id = NnZrxd6lJkbHKqW6w04N`
  - `version_id = 8SrjbTKmOZjOnHxLQrxE`
- Словарь построен по реальному корпусу:
  - `100` последних live-звонков;
  - текущий live-prompt;
  - локальная русская knowledge base.
- В словарь включены только реально встречающиеся и важные для live-диалога слова:
  - `ЛипоЛонг / LipoLong / lipolong -> липолонг`
  - частые продуктовые слова: `липолитик`, `липолитиками`, `коррекция`, `инъекционные`, `консультация`, `процедуры`
  - клиентские каналы: `Telegram`, `WhatsApp`, `MAX`
- Специально не добавлялись `Mango` и `n8n`, потому что они не являются рабочими словами клиентского разговора.
- Важно:
  - голос, `voice_id`, `speed`, `stability` и `similarity_boost` при подключении словаря не менялись;
  - словарь подключён только через `pronunciation_dictionary_locators`.
- Для репозитория сохранены исходники и backup:
  - `docs/call-translation-bridge/pronunciation/lipolong_agent_base_2026-04-04.rules.json`
  - `docs/call-translation-bridge/pronunciation/README_RU.md`
  - `backups/2026-04-04_11-49-17_pronunciation_dict_attach/`
- Отдельным hotfix обновлены самые частые проблемные ударения:
  - `липолонг`
  - `липолитиками`

### 2026-04-04 — Усилен sales-prompt агента без изменения `first_message`
- В локальных KB-документах и live-prompt для `AI_CALL_AGENT_1` усилена логика уверенного B2B-продажника без правки стартовой фразы.
- Добавлены и зафиксированы правила:
  - после первого мягкого отказа агент не сворачивается сразу, а делает один управляемый rescue-ход;
  - размытое `перезвоните позже` переводится в конкретный коридор `через 2-3 дня / на следующей неделе`;
  - для перезвона в пределах `48 часов` агент обязан уточнять `первая половина дня / вторая половина дня`;
  - базовые продуктовые вопросы агент сначала закрывает сам коротким ответом, а не переводит на менеджера автоматически;
  - усилена выгодная подача LipoLong через официальный канал, тестовый вход, расширение практики и сравнение экономики процедуры;
  - обновлены playbook и диалоговые скрипты по веткам `не интересно`, `не используем инъекции`, `перезвоните позже`, `кто вы такие`, `что это такое`.
- Для вопроса о противопоказаниях зафиксирован короткий безопасный ответ с переводом на специалиста при необходимости.
- Снят свежий backup live-конфигурации:
  - `backups/2026-04-04_09-48-29_live_sales_prompt_refresh/eleven_agent_live_before_changes.json`

### 2026-04-04 — Выполнен и затем откатан voice-tuning live-агента
- В live-конфигурации `AI_CALL_AGENT_1` пробовался безопасный TTS-тюнинг без смены `voice_id` и без изменения `first_message`.
- Тестировались параметры:
  - `speed: 1.16 -> 1.08`
  - `stability: 0.5 -> 0.62`
  - `similarity_boost: 0.78 -> 0.80`
- По результату живого прослушивания tuning был откатан:
  - голос стал слишком медленным;
  - паузы начали восприниматься как лишнее ожидание ответа;
  - live возвращен к исходным значениям `1.16 / 0.5 / 0.78`.
- Сняты backup-файлы:
  - `backups/2026-04-04_10-30-27_voice_tuning/eleven_agent_before_voice_tuning.json`
  - `backups/2026-04-04_10-44-52_voice_revert/eleven_agent_before_revert.json`
  - `backups/2026-04-04_10-44-52_voice_revert/eleven_agent_after_revert.json`

### 2026-03-22 — Усилен live-prompt агента и добавлен второй SMS-сценарий `product_intro`
- В live-агенте `AI_CALL_AGENT_1` обновлен system prompt без изменения `first_message`.
- В prompt зафиксированы новые правила:
  - `не интересно` больше не является автоматическим завершением;
  - `не работаем с липолитиками` и `не используем инъекционные методики` сначала переводятся в проверку релевантности направления;
  - если направление коррекции фигуры релевантно, но инъекционные методики не используются, агент предлагает `product_intro` SMS и follow-up;
  - агенту запрещены сервисные концовки `Могу ли я чем-то еще помочь?` и `Тогда наше предложение вам не подходит`;
  - добавлено правило вариативных коротких связок, чтобы убрать повторяющееся `Поняла / Приняла`.
- В live-tool `send_sms_info` обновлена schema:
  - `message_intent` теперь поддерживает `short_info`, `product_intro`, `offer`, `callback_confirmation`;
  - `short_info` используется для контактов менеджеров и связи;
  - `product_intro` используется для краткого объяснения, что такое LipoLong, преимуществ, цены, условий входа и контактов менеджеров для консультации.
- В live `n8n` workflow `ELEVEN_TOOL_SEND_SMS_BRIDGE (draft)` обновлен шаблон `product_intro`.
- Сняты локальные backup-файлы live-конфигураций:
  - `backups/live_2026-03-22_objection_sms_refresh/n8n_workflow_before.json`
  - `backups/live_2026-03-22_objection_sms_refresh/eleven_send_sms_tool_before.json`
  - `backups/live_2026-03-22_objection_sms_refresh/eleven_agent_before.json`

### 2026-03-21 — Введен live-сценарий отправки SMS через `send_sms_info` и синхронизирована документация
- В live-агент `AI_CALL_AGENT_1` добавлен webhook tool:
  - `tool_1701km86jmcpek4rj2j1rbhxqtfr` -> `send_sms_info`
- В `n8n` активирован workflow:
  - `ELEVEN_TOOL_SEND_SMS_BRIDGE (draft)`
  - webhook `POST /webhook/eleven/tool/send-sms`
- В workflow зафиксирован рабочий SMS-пакет с контактами и условиями сотрудничества.
- В live-prompt зафиксированы правила:
  - если клиент говорит `на этот номер`, агент сразу использует `system__called_number`;
  - агент не спрашивает про мессенджер и не собирает номер заново из речи;
  - диктовка номера допускается только если клиент просит отправить SMS на другой номер.
- Исправлен риск ложной отправки на неверный номер после ASR-нормализации цифр:
  - при пустом или битом `phone_target` используется `current_call_number`.
- Практический результат:
  - SMS успешно отправляется и на номер текущего звонка, и на отдельно указанный номер;
  - рабочая документация и папка `документация_для_агента` обновлены под SMS-сценарий.

### 2026-03-20 — Зафиксировано актуальное live-состояние ElevenLabs агента и восстановлен `call_log`
- Актуальный live-агент:
  - `AI_CALL_AGENT_1`
  - `agent_8801kgybyekned2a8yae6rp8hk3q`
  - `agtvrsn_7701km62tyq2eg9ax5tmkq8727tt`
- Актуальные параметры:
  - `LLM = gpt-4.1`
  - `TTS = eleven_flash_v2_5`
  - `voice_id = 0ArNnoIAWKlT4WweaVMY` (`Elena Gromova`)
  - `speed = 1.16`
  - `stability = 0.5`
  - `similarity_boost = 0.78`
  - `turn_eagerness = eager`
  - `turn_timeout = 3.0`
  - `disable_first_message_interruptions = true`
- Зафиксирована обязательная `first_message` с завершающим вопросом о текущей работе с липолитиками.
- В prompt зафиксированы:
  - обязательное уточнение имени собеседника;
  - follow-up без `e-mail` и без `telegram username`;
  - сценарий отправки контактов только через номер и привязанный к нему канал связи.
- Удалены битые `tool_ids`, после чего восстановлены валидные live-tools:
  - `tool_1601km62rxpqegqr52m9gk9sftr3` -> `context_fetch`
  - `tool_0901km62rxpre578kd1zvd7q7g04` -> `call_log`
- Подтверждено по live-логам:
  - `call_log` вызывается успешно;
  - `end_call` завершает звонок штатно;
  - связка `context_fetch` / `call_log` / `end_call` снова работает.

### 2026-03-20 — Зафиксировано live-состояние ElevenLabs агента LipoLong
- Актуальный live-агент:
  - `AI_CALL_AGENT_1`
  - `agent_8801kgybyekned2a8yae6rp8hk3q`
- Зафиксированы текущие параметры:
  - `LLM = gemini-2.5-flash`
  - `TTS = eleven_flash_v2_5`
  - `speed = 1.2`
  - `turn_eagerness = eager`
  - `turn_timeout = 4.0`
- Для стартовой и обычных реплик отключено прерывание пользователем:
  - `disable_first_message_interruptions = true`
  - из `client_events` удалено `interruption`
- Обновлены документы:
  - `docs/call-translation-bridge/08_LIVE_ELEVEN_AGENT_RU.md`
  - `docs/agent_kb_lipolong/08_ELEVENLABS_SYSTEM_PROMPT_RU.md`
  - `docs/agent_kb_lipolong/09_DIALOG_SCRIPTS_RU.md`

### 2026-03-19 — Включен и стабилизирован memory/live bridge для call center
- Поднят memory-контур:
  - `postgres_memory`
  - `postgrest`
- Исправлен `ELEVEN_TOOL_CONTEXT_BRIDGE`, чтобы `context_fetch` возвращал `source=postgres`, а не `fallback`.
- В `VOICE_INBOUND_AGENT` зафиксирована принудительная стартовая фраза для входа в разговор.
- Практический эффект:
  - контекст агента теперь может читаться из Postgres;
  - стартовая подача в n8n и ElevenLabs синхронизирована.

### 2026-02-12 — Postgres Memory stack + API
- Добавлены файлы:
  - `docker-compose.memory.yml`,
  - `.env.memory.example`,
  - `sql/002_agent_memory.sql`.
- Поднят отдельный memory-контур:
  - `postgres_memory` (`postgres:16-alpine`),
  - `postgrest` (`postgrest/postgrest:latest`).
- В SQL-инициализации добавлены:
  - таблица `agent_memory`,
  - индексы по `session_id`/`agent_id`,
  - trigger `updated_at`,
  - роль `web_anon` для PostgREST.

### 2026-02-12 — Adminer UI через HTTPS (Traefik)
- Добавлен `docker-compose.adminer.yml`.
- Добавлены env в `.env.https.example`:
  - `ADMINER_DOMAIN`,
  - `ADMINER_BASICAUTH`.
- Цель: визуальный доступ к PostgreSQL в браузере без работы из CLI.

### 2026-02-12 — Стабилизация Master агента
- В `C8Wmmjuv5hC425PM`:
  - убран `Window Buffer Memory`,
  - добавлен `Postgres Chat Memory` (таблица `agent_memory`, `contextWindowLength=20`),
  - добавлен встроенный `Router | Intent Parse` перед `AGENT 1 | Manager`,
  - добавлен `Reply Guardrail` для rewrite отказов и цикловых ответов,
  - подключён tool `Memory Neuro Agent`,
  - удалён внешний `Intent Router | Tool` из цепочки мастера.
- Эффект:
  - меньше “залипаний” в уточнениях,
  - устойчивее обработка прямых image/video запросов,
  - контекст диалога хранится в PostgreSQL.

### 2026-02-11 — Добавлен Memory Neuro Agent
- Создан workflow: `kcH2rlqr8aZoOPiO` (`MEMORY_NEURO_AGENT | GitHub Markdown Memory (draft)`).
- Назначение:
  - долговременная память в markdown-файлах GitHub-репозитория `MaxCorpOrg/memory`;
  - действия `upsert/read/search/list_files/archive_weekly/compact/sync/health_check`;
  - еженедельное архивирование и compact-режим при превышении лимитов;
  - connector-режим для `gdrive/dropbox/s3` через внешние endpoint URL.
- Требуемые env для n8n:
  - `MEMORY_GITHUB_TOKEN` (required для backend `github`),
  - `MEMORY_CONNECTOR_GDRIVE_URL` / `MEMORY_CONNECTOR_DROPBOX_URL` / `MEMORY_CONNECTOR_S3_URL` (optional),
  - `MEMORY_CONNECTOR_AUTH_TOKEN` (optional).

### 2026-02-11 — Memory Brain (intent/router слой в memory workflow)
- В `kcH2rlqr8aZoOPiO` добавлен узел `Memory Brain` между `Set Config` и `Validate Config`.
- Что делает:
  - нормализует действие (`upsert/search/get_file/list_files/archive_weekly/compact/sync`);
  - определяет backend (`github/gdrive/dropbox/s3`) по явному параметру и по тексту;
  - формирует `memory_key`, priority и confidence;
  - добавляет мягкие guardrails (например, small-talk не пишет в память как `upsert`).
- В ответ добавлены поля `brain`, `brain_confidence`, `brain_priority`, `brain_warnings` для отладки и контроля в Agent 1.

### 2026-02-10 — Добавлен KB Sync Agent
- Создан workflow: `K5es5hBE05LEeB1j` (`KB_SYNC_AGENT | Knowledge Base Sync (draft)`).
- Функции:
  - проверка свежести `docs/knowledge_base` по git-коммитам;
  - автообновление `docs/knowledge_base/09_PROJECT_CHANGELOG_AND_STATE.md` через GitHub API;
  - Telegram-уведомление о результате синхронизации.
- Требуемые env для n8n:
  - `KB_GITHUB_TOKEN` (required),
  - `N8N_PUBLIC_API_KEY` (optional, для статистики workflow).

### 2026-02-10 — Рефактор архитектуры агента (база для текущего роутинга)
- Добавлен workflow `ABnHZb9Ee2YOtfr2` (`MEDIA_AGENT_ROUTER | Intent Router (draft)`).
- Логика интентов вынесена из монолитного промпта в отдельный модуль (Code + Switch).
- Позже часть логики была встроена обратно в Master (`Router | Intent Parse`) для линейной и детерминированной обработки.

### 2026-02-10 — Доступ к Telegram-боту ограничен
- В `C8Wmmjuv5hC425PM` добавлены узлы:
  - `Access Control`
  - `Access Switch`
  - `Set Unauthorized Reply`
- Политика: owner-only доступ (по chat_id/user_id).

### 2026-02-10 — Улучшен pipeline генерации
- Agent 5 переведён на надёжный сценарий отправки фото в Telegram (`sendPhoto` через ноду Telegram).
- Поддержка Flow/Vertex-конфигурации и fallback на Pollinations.

### 2026-02-10 — Диалоговый режим и video-first
- Agent 1: поддержка guided + prompt-ready режима.
- Agent 2: усилен image->video planning.
- Приоритет конечной цели: создание видео, а не только изображения.

## 3) Последние коммиты (из git log)
| Commit | Сообщение |
|---|---|
| `9e3b8bb` | feat: add postgres memory stack, adminer access, and media-agent stability updates |
| `49f69ed` | Переведен мастер-агент в свободный режим диалога и усилена устойчивость |
| `3522fd9` | Добавлен KB Sync Agent и обновлено рабочее пространство медиа-оркестратора |
| `f13e4a6` | Рефактор n8n-агента: Intent Router, маршрутизация и обновление workspace |
| `8616d93` | Добавлен переносимый workspace для медиа-оркестратора n8n |

## 4) Текущие риски / TODO
- [ ] Заполнить реальные характеристики железа сервера.
- [ ] Зафиксировать финальные каналы алертов и SLA.
- [ ] Настроить регулярные учебные тесты восстановления backup.
- [ ] Поддерживать owner ID list в Access Control при смене админов.
- [ ] Проверить и зачистить workflow JSON от тестовых/временных API-ключей перед внешними публикациями.
- [ ] Принять финальное решение по внешней доступности `5432/3000` (закрыть UFW или оставить только internal).

## 5) Шаблон журналирования изменений
```md
### YYYY-MM-DD HH:MM UTC — Изменение
- Что изменено:
- Какие файлы/workflow:
- Риски:
- Проверка:
- Следующие шаги:
```
### 2026-04-05 — Переключение call_log на новую таблицу контактов

- Для рабочей таблицы `контакты_косметологов_москва_47.xlsx` создана native Google Sheet-копия:
  - `1pLrCNeQ_thipr5-fajPusgNZZSd5NHEZFmGkegfpIqI`
- Причина: исходный файл был в формате `.xlsx`, и текущий `call_log` через Google Sheets API не может писать напрямую в Excel-файл на Google Drive.
- Live workflow `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` переведен на новую Google Sheet.
- Целевой лист сохранен прежним: `Лиды_обзвон`.

### 2026-04-13 — Исправлен live AUTODIAL_DISPATCHER после переключения таблицы

- Найдена и исправлена причина, по которой автодозвон не стартовал в окне `10:00-14:00 MSK`.
- Root cause: live workflow `AUTODIAL_DISPATCHER (sheet-first draft)` публиковался с буквальными placeholder-строками `{{GOOGLE_CLIENT_ID}}`, `{{GOOGLE_CLIENT_SECRET}}`, `{{GOOGLE_REFRESH_TOKEN}}` в ноде `Google | Build Sheet Payload`.
- Из-за этого шаг `Google | Refresh Access Token` возвращал `invalid_client`, чтение таблицы падало, а dispatcher ошибочно завершал цикл как `exhausted` с `total_leads = 0`.
- Исправлен генератор [build_autodial_sheet_workflow.py](/home/max/n8n_ai_call_center/scripts/build_autodial_sheet_workflow.py):
  - live-публикация теперь берёт Google OAuth из рабочего live `ELEVEN_TOOL_CALL_LOG_BRIDGE`,
  - в git-репозитории по-прежнему сохраняется санитизированный draft без секретов,
  - live workflow больше не затирается санитизированной версией.
- Проверка после фикса:
  - `Google | Refresh Access Token` вернул `access_token`,
  - `Google | Fetch Sheet Rows` прочитал новую таблицу `1FUHh8lS8pEx58eRK2Rt6AYn3cy6ogWSO32vZWqYw_Fc`,
  - `Dispatcher | Parse Sheet Rows` увидел `46` лидов и `45` eligible,
  - `Postgres | Claim Next Lead` поставил `row_2` в `dialing`,
  - `Dispatcher | Request Outbound Call` успешно инициировал звонок в ElevenLabs (`conversation_id` выдан).

### 2026-04-13 — Уточнён live opener и убраны ранние закупочные вопросы

- По логам звонков за `2026-04-13` подтверждены 2 слабых паттерна раннего старта:
  - старый opener в стиле `вы занимаетесь закупками / вы принимаете решения по закупкам`;
  - fallback в ресепшен-стиль `Я вас слушаю / Чем могу помочь` на неясном ответе.
- Live prompt обновлён:
  - первая живая реплика после ответа человека теперь должна сразу быть полным business-opener;
  - отдельное standalone `Здравствуйте.` как самостоятельный ход убрано;
  - целевой opener:
    `Здравствуйте, наша компания является официальным представителем липолитика премиум класса lipolong, предлагаем вам сотрудничество с нашей компанией на выгодных условиях.`
  - следующий короткий вопрос:
    `Вам это в принципе интересно?`
  - вопрос про закупки или ответственного специалиста теперь допустим только после явного сигнала, что собеседник не ЛПР;
  - message-service фраза `Если абонент захочет с вами связаться...` закреплена как автоответчик, без продолжения sales-диалога.
- Live agent обновлён через ElevenLabs API, backup сохранён в:
  - `backups/2026-04-13_opening_cleanup_refresh/`

### 2026-05-25 — Новый целевой fast-hangup режим для machine/unavailable/ringback

- По свежим кейсам:
  - `conv_6801ksf4n22efwqvcthy3b19531b` — автоуведомление `абонент отключен / вне зоны / voicemail disabled`, которое агент не должен дослушивать до конца;
  - `conv_2801ksf596bneyxa9r1crt9b7fpc` — long ring / no interaction, который должен завершаться примерно после `5` гудков, а не висеть почти до полного окна ожидания;
- Зафиксирован новый source-of-truth режим:
  - machine / unavailable / message-service -> максимум `5` секунд, затем `call_log` и молчаливый `end_call`;
  - voicemail -> без spoken callback-message и без диктовки номера менеджера;
  - long ring / no human -> завершение примерно после `5` гудков;
- Подготовлен новый комплект артефактов для точечного patch в Eleven `Main`:
  - `backups/2026-05-25_machine_fast_hangup_refresh/main_prompt_only_payload.json`
  - `backups/2026-05-25_machine_fast_hangup_refresh/main_prompt_plus_turn_timeout_5_payload.json`
  - `backups/2026-05-25_machine_fast_hangup_refresh/README.md`

### 2026-05-25 — Добавлен live-отчёт по Google Sheet call_log

- Для постоянного цикла `звонок -> лог -> анализ` добавлен новый локальный инструмент:
  - `scripts/report_live_call_log_sheet.py`
- Скрипт:
  - берёт OAuth credentials из `.env.callcenter`;
  - читает боевой лист `Лиды_обзвон`;
  - строит сводку по `source_system`, `call_result`, provider failures и machine-like notes;
  - отдельно показывает короткие timeline по lead'ам, чтобы видеть последовательность `dialing -> outbound_request_failed -> elevenlabs result`.
- Первый живой прогон по `2026-05-25` подтвердил:
  - `source_system`: `xlsx_import=50`, `autodial_dispatcher=23`, `elevenlabs=5`;
  - `call_result`: `dialing=15`, `outbound_request_failed=8`, `send_kp_pending_callback=4`, `no_answer=1`;
  - `row_10` зафиксирован как плохой live-кейс: `no_answer` с note `Оставлено короткое сообщение для абонента через МТС Защитник, передан контакт менеджера.`;
  - `row_5` и `row_3` зафиксировали machine-like message-transfer notes, хотя целевой режим уже требует быстрее и строже отсекать такие сценарии;
  - во всех свежих `elevenlabs`-строках `eleven_conv_id` пустой, то есть текущая sheet-трассировка разговоров неполная и это отдельный лог-долг.
- По следующему живому кейсу `conv_2601ksf5p04zfnzr3w1ec85aj9kk` отдельно зафиксировано:
  - `MTS Defender / МТС Защитник / это рекламный звонок / звонок записывается сервисом защиты` нужно трактовать как автоответчик или screening-service;
  - агент не должен оставлять сообщение такому сервису и не должен считать его живым человеком;
  - этот паттерн добавлен в source-of-truth prompt и в machine-like keywords локального sheet-отчёта.

### 2026-04-14 — Усилена логика music/hold и тишины после opener

- По логам `2026-04-14` подтверждены два проблемных паттерна:
  - музыка ожидания и рекламная петля клиники иногда всё ещё воспринимались как продолжение разговора;
  - после полного opener при ответе клиента `...` агент мог слишком долго ждать и начинал переспрашивать.
- На основе звонков:
  - `conv_4001kp5dnerpfvfrss68xxemh0x4`
  - `conv_4201kp5ebd64fqaaw80b99y8m6yc`
  - `conv_5101kp5cvsgdejmt05xa01v1vpa3`
  обновлён live prompt:
  - музыка ожидания, рекламные объявления и повторяющиеся брендовые приветствия закреплены как `waiting mode`;
  - после собственного opener, если нет ясного словесного ответа примерно `15` секунд, звонок должен завершаться как `no_answer`;
  - `...`, дыхание, шорох, неразборчивый шум и line artifacts не считаются живым ответом;
  - запрещены rescue-реплики после пустоты вроде `вы на связи?`, `вы меня слышите?`, `если удобно, дайте знать...`
- Live agent обновлён через ElevenLabs API, backup сохранён в:
  - `backups/2026-04-14_music_silence_fix/`
- `2026-04-21`: автодозвон считает дневной лимит только по живым разговорам, а не по всем исходящим попыткам. Технические и машинные звонки в этот лимит не входят.
- `2026-04-21`: relay на сервере `151.241.228.232` обновлён до версии с узким retry для плавающих upstream-сбоев (`network exception`, `HTTP 5xx`, `max auth retry attemps reached`). Бэкап старого runtime-файла сохранён как `/opt/eleven_outbound_relay.py.bak-2026-04-21-091832`.
- `2026-04-21`: по свежим живым диалогам (`conv_6201kpqfpratfstv115h8rek0k14`, `conv_7901kpqfmy2sfhcat516s1pr58qk`, `conv_7301kpqfrk46fbvahv3xynygj2bg`) уточнён live-opener:
  - вопрос `Вам это в принципе интересно?` больше не должен приклеиваться к первой business-реплике;
  - generic-ответы `алло`, `слушаю вас`, приветствие клиники и подтверждение имени не считаются interest/qualification-сигналом;
  - если секретарь или администратор принял сообщение для передачи, это должно логироваться как `send_kp_pending_callback`, а не как `no_answer`.
- `2026-04-21`: по следующему срезу (`conv_6601kpqggcfjeqtajh58psqq0p0w`, `conv_5001kpqgej9sfertpfjmxp8jeats`) sequence ужесточён ещё сильнее:
  - первая business-реплика должна быть ровно standalone opener без добавленного вопроса;
  - qualification запрещена после generic-ответов вроде `слушаю вас`;
  - qualification допускается только после явного смыслового сигнала интереса, любопытства или релевантности.
- `2026-04-21`: по следующему срезу (`conv_7901kpqgqqmdedkvpwt2nz2w750h`, `conv_0201kpqgnw9dfpcat0gw2ed1eve0`, `conv_6901kpqgm2ehf5nv9dest2xxdwb5`) добавлено дополнительное hardening:
  - machine/IVR-реплика с хвостом `алло` всё равно трактуется как машинная;
  - меню, очереди и рекламные машинные реплики не должны запускать sales-opener даже при смешанном ASR-куске;
  - после `voicemail_detection` агент обязан сразу оставить callback-message и завершить звонок;
  - на тишине и шуме полностью запрещены fallback-фразы `Я вас не услышала`, `Вы на связи?`, `Могу ли я чем-то помочь?`, `Спасибо за внимание...`.
- `2026-04-21`: по следующему срезу (`conv_2301kpqh1h2tf57az9bq8fq1rxga`, `conv_1601kpqgz1ddf4wanc9fgj9eaxv8`, `conv_9301kpqgvcdqeh9sn7sk043fphh3`) добавлено финальное ужесточение:
  - первая live business-response должна быть ровно одной фразой без второго предложения и без приклеенного вопроса;
  - приветствие клиники или generic-реплика `слушаю вас` не считаются интересом и не дают права продолжать тот же ход вторым предложением;
  - на машинной недоступности агент должен завершать звонок молча, без собственной проговариваемой фразы.
- `2026-04-21`: по следующему срезу (`conv_8101kpqjm4fbf8pste21wfdsdv29`, `conv_2301kpqjja23e7n8zbx9cw59r927`, `conv_0301kpqjgf8de76r1gxy8p8cbqh9`) добавлено ещё одно ужесточение:
  - после opener агент обязан немедленно отдать ход и не продолжать тот же turn ни при каких условиях;
  - в `no_answer` после тишины агент должен логировать звонок и завершать его молча, без сервисной финальной фразы.
- `2026-04-21`: по кейсу `conv_6701kpqh6en5fs79gx5eze93bp2y` обнаружено, что одного prompt-правила для автоответчика недостаточно: `voicemail_detection` срабатывал, но callback-message не проговаривался. После этого в live built-in tool `voicemail_detection` установлен явный `voicemail_message` с callback-текстом.
