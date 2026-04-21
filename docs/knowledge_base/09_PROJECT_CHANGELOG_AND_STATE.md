# 09. Состояние проекта и последние изменения

## 1) Актуальное состояние (оперативный снимок)
- Проект: `n8n_ai_call_center`.
- Базовая инфраструктура: Ubuntu 24.04 + Docker + Traefik + HTTPS.
- Memory-слой: `postgres_memory` + `postgrest` + таблица `agent_memory`.
- DB UI: `adminer` (через Traefik на 443, с BasicAuth).
- Основной workspace: `media_orchestrator_v1`.
- Telegram-оркестратор: `C8Wmmjuv5hC425PM`.

## 2) Последние важные изменения

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
  - считает живой ответ человека отдельной аналитической метрикой, но не дневным стоп-фактором;
  - ограничивает дневной объем до `15` исходящих звонков;
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
- `2026-04-21`: автодозвон переведён на жёсткий дневной лимит `15` исходящих звонков, а не `15` живых успешных контактов. Лимит считается по lock-строкам `autodial_dispatcher / dialing`, то есть по фактически инициированным outbound-вызовам.
- `2026-04-21`: relay на сервере `151.241.228.232` обновлён до версии с узким retry для плавающих upstream-сбоев (`network exception`, `HTTP 5xx`, `max auth retry attemps reached`). Бэкап старого runtime-файла сохранён как `/opt/eleven_outbound_relay.py.bak-2026-04-21-091832`.
