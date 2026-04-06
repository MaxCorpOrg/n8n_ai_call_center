# 09. Состояние проекта и последние изменения

## 1) Актуальное состояние (оперативный снимок)
- Проект: `n8n_ai_call_center`.
- Базовая инфраструктура: Ubuntu 24.04 + Docker + Traefik + HTTPS.
- Memory-слой: `postgres_memory` + `postgrest` + таблица `agent_memory`.
- DB UI: `adminer` (через Traefik на 443, с BasicAuth).
- Основной workspace: `media_orchestrator_v1`.
- Telegram-оркестратор: `C8Wmmjuv5hC425PM`.

## 2) Последние важные изменения

### 2026-04-06 — Исправлен критичный рассинхрон таблиц для автодозвона
- Найден и исправлен баг в `AUTODIAL_DISPATCHER`: workflow читал старый `spreadsheet_id` `1E-VCKAv4vF_SFLY8DgW0UC80FvAC_DDIxbSbi8GC8kU`, тогда как live `call_log` и рабочая таблица уже были переведены на `1pLrCNeQ_thipr5-fajPusgNZZSd5NHEZFmGkegfpIqI`.
- Из-за этого dispatcher мог корректно стартовать по расписанию, но смотреть не в ту таблицу и не видеть актуальную очередь обзвона.
- Репозиторный draft и документация приведены к одному источнику истины:
  - `https://docs.google.com/spreadsheets/d/1pLrCNeQ_thipr5-fajPusgNZZSd5NHEZFmGkegfpIqI/edit`
- Дополнительно dispatcher переведен на выбор целевой вкладки по `gid = 199760593`, чтобы ссылка на нужный таб была достаточной для настройки.

### 2026-04-05 — Автодозвон переведен на sheet-first runtime и активирован в live n8n
- Live workflow `AUTODIAL_DISPATCHER` переведен на Google Sheet-only контур:
  - источник истины: `Лиды_обзвон`;
  - state/runtime хранится прямо в той же таблице через append-only lock и outcome rows;
  - Postgres-схема `sql/005_autodial_dispatcher.sql` осталась как исторический draft и в live не используется.
- Логика диспетчера:
  - запускается каждые 5 минут;
  - звонит только в окне `10:00–14:00` по МСК;
  - считает успехом только живой ответ человека и начатый диалог;
  - ограничивает дневной объем до `15` живых контактов;
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
