# Telegram Sandbox Activity Runner

Отдельный инструмент для безопасной активности только внутри ваших собственных Telegram-аккаунтов, allowlist-чатов и allowlist-контактов.

## Что умеет

- планировать и запускать `send_message`, `open_chat`, `idle_scroll` только в allowlist;
- работать через `SiteControlKit` и его browser client;
- вести `state.json` с дневными лимитами, cooldown и историей;
- подготавливать invite flow для allowlist-контакта в allowlist-чат;
- подготавливать join flow для allowlist-чата;
- подготавливать `Add to contacts` flow по allowlist-`@username` через Telegram Desktop portable;
- запускать batch `Add to contacts` по списку `contact_id` с рандомными паузами;
- использовать optional `Telegram API sidecar` для быстрого `resolve/add`, а при недоступной API-сессии уходить в `portable/UI` fallback;
- по умолчанию останавливаться на ручном подтверждении в чувствительных шагах.

## Что принципиально запрещено

- внешние чаты вне `allowlist_chats`;
- внешние контакты вне `allowlist_contacts`;
- случайные ссылки в сообщениях, если включён `block_external_links`;
- скрытая автоприглашалка без отдельного allowlist и без ручного финального подтверждения.

## Структура

- launcher: [bin/telegram-sandbox-activity-runner](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner)
- основной код: [telegram_sandbox_activity_runner.py](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/telegram_sandbox_activity_runner.py)
- пример конфига: [config.example.json](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/config.example.json)
- агентские правила: [AGENTS.md](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/AGENTS.md)
- короткий checkpoint: [CHECKPOINT_RU.md](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/CHECKPOINT_RU.md)

## GitHub-ready Wrapper

Для переиспользования этого contact-flow как отдельного внешнего инструмента добавлена отдельная папка-обертка:

- [tools/telegram_desktop_contact_tool](/home/max/n8n_ai_call_center/tools/telegram_desktop_contact_tool)

Она не дублирует core runner, а дает:

- отдельный launcher для `import-usernames / add-one / batch-add / api-scan`;
- собственный `README_RU.md`;
- отдельный `AGENTS.md` для следующего агента;
- более короткий GitHub-friendly entrypoint поверх текущего инструмента.

## Новый modular allowlist CLI

Рядом с текущим monolith runner теперь есть отдельный комплаентный CLI на `Telethon` для легитимных allowlist-only задач:

- launcher: [bin/telegram-allowlist-tool](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/bin/telegram-allowlist-tool)
- package root: [allowlist_tool](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/allowlist_tool)
- example CSV files: [examples/allowlist_tool](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/examples/allowlist_tool)

Его архитектура разделена на отдельные модули:

- [validator.py](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/allowlist_tool/validator.py)
- [queue_manager.py](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/allowlist_tool/queue_manager.py)
- [executor.py](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/allowlist_tool/executor.py)
- [safety.py](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/allowlist_tool/safety.py)
- [audit_log.py](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/allowlist_tool/audit_log.py)
- [report.py](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/allowlist_tool/report.py)

Этот CLI специально ограничен:

- только `allowlist.csv`;
- только `validate`, `send_message`, `add_to_group`;
- ручной `YES` confirm перед `send_message` и `add_to_group`;
- локальный лимит `20` действий в час на аккаунт;
- задержка `5` секунд между API-запросами;
- backoff на `FloodWaitError`;
- жёсткая остановка аккаунта на `PeerFloodError` и похожих suspicious ответах.

Быстрый старт:

```bash
cd /home/max/n8n_ai_call_center

tools/telegram_sandbox_activity_runner/bin/telegram-allowlist-tool sample-files \
  --output-dir /tmp/telegram-allowlist-samples

tools/telegram_sandbox_activity_runner/bin/telegram-allowlist-tool validate-allowlist \
  --accounts-csv /tmp/telegram-allowlist-samples/accounts.example.csv \
  --allowlist-csv /tmp/telegram-allowlist-samples/allowlist.example.csv \
  --account-id main_admin
```

Построить очередь без API-вызовов:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-allowlist-tool build-queue \
  --accounts-csv /tmp/telegram-allowlist-samples/accounts.example.csv \
  --allowlist-csv /tmp/telegram-allowlist-samples/allowlist.example.csv \
  --actions-csv /tmp/telegram-allowlist-samples/actions.example.csv
```

Запустить действия с ручным подтверждением:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-allowlist-tool run-actions \
  --accounts-csv /tmp/telegram-allowlist-samples/accounts.example.csv \
  --allowlist-csv /tmp/telegram-allowlist-samples/allowlist.example.csv \
  --actions-csv /tmp/telegram-allowlist-samples/actions.example.csv \
  --account-id main_admin
```

Инструмент не делает массовые действия сам по себе и не пытается обходить ограничения Telegram.

## Быстрый старт

```bash
cd /home/max/n8n_ai_call_center

tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner init \
  --config tools/telegram_sandbox_activity_runner/config.example.json

tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner plan \
  --config tools/telegram_sandbox_activity_runner/config.example.json \
  --iterations 3

tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner run \
  --config tools/telegram_sandbox_activity_runner/config.example.json \
  --iterations 2
```

`run` без `--execute` остаётся в dry-run.

## Импорт approved username-списка

Если у вас уже есть подтверждённый список `@username`, его можно штатно загрузить в `allowlist_contacts`.

Из файла:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner import-contacts \
  --config /path/to/config.json \
  --usernames-file /path/to/usernames.txt
```

Через stdin:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner import-contacts \
  --config /path/to/config.json <<'EOF'
@user_one
@user_two
EOF
```

Importer:

- нормализует `@username`;
- убирает дубликаты;
- пропускает мусорные строки;
- создаёт `contact_id` автоматически;
- не запускает никаких действий сам по себе, только пополняет allowlist.

## Telegram API Sidecar

Для ускорения `resolve/add` можно включить optional sidecar на `Telethon`.

Что для этого нужно:

- локальный Python или `vendor`-каталог, где установлен `telethon`;
- `api_id` и `api_hash` в env vars;
- session file для конкретного `actor`.

Проверка статуса sidecar-сессии:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner api-status \
  --config /path/to/config.json \
  --actor-id account_01
```

Если у `actor` уже есть рабочий `Telegram Desktop portable`, session можно поднять прямо из `tdata` без ручного ввода кода:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner api-import-tdata-session \
  --config /path/to/config.json \
  --actor-id account_01
```

При необходимости можно указать `tdata` явно:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner api-import-tdata-session \
  --config /path/to/config.json \
  --actor-id account_01 \
  --tdata-dir /home/max/TelegramPortable-AK2/TelegramForcePortable/tdata
```

Если у desktop-профиля включён local passcode, добавь:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner api-import-tdata-session \
  --config /path/to/config.json \
  --actor-id account_01 \
  --desktop-passcode 'your-passcode'
```

Если session ещё не авторизована, sidecar можно поднять вручную:

```bash
/path/to/venv/bin/python tools/telegram_sandbox_activity_runner/telegram_api_sidecar.py \
  --api-id-env TG_API_ID \
  --api-hash-env TG_API_HASH \
  --session-file /path/to/account_01.session \
  interactive-login
```

Чтобы заранее отфильтровать stale / invalid `@username` и оставить только реально резолвящиеся user-аккаунты:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner api-scan-contacts \
  --config /path/to/config.json \
  --actor-id account_01 \
  --contact-id-file /path/to/contact_ids.txt \
  --write-valid-contact-id-file /tmp/valid_contact_ids.txt
```

Если `telethon` ставится не в system Python и не в venv, можно использовать `api_sidecar.python_path` и запускать sidecar через обычный `python3`.

## Боевой запуск allowlist-активности

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner run \
  --config /path/to/config.json \
  --state-file /path/to/state.json \
  --iterations 2 \
  --execute \
  --respect-delays
```

## Operator-assisted invite

Инструмент сам:

1. открывает allowlist-чат;
2. открывает sidebar;
3. открывает `Add members`;
4. вводит allowlist-контакт в поиск;
5. выбирает кандидата;
6. открывает Telegram confirmation popup.

По умолчанию он останавливается здесь, и пользователь вручную подтверждает финальный `Add`.

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner prepare-invite \
  --config /path/to/config.json \
  --actor-id account_01 \
  --chat-id ops_room \
  --contact-id qa_friend \
  --execute
```

Если нужен полный клик финального `Add`, он вынесен в явный флаг:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner prepare-invite \
  --config /path/to/config.json \
  --actor-id account_01 \
  --chat-id ops_room \
  --contact-id qa_friend \
  --execute \
  --confirm-final
```

## Operator-assisted join

Инструмент открывает allowlist-чат и проверяет, видна ли кнопка `Join`.

Без `--confirm-join` он только доводит экран до ручного подтверждения:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner prepare-join \
  --config /path/to/config.json \
  --actor-id account_01 \
  --chat-id ops_room \
  --execute
```

С явным подтверждением можно разрешить автоматический клик по `Join`:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner prepare-join \
  --config /path/to/config.json \
  --actor-id account_01 \
  --chat-id ops_room \
  --execute \
  --confirm-join
```

## Operator-assisted Add To Contacts By Username

Для сценария “есть список `@username`, нужно аккуратно занести их в свои контакты” добавлен отдельный desktop path через `telegram_portable.py` из `site-control-kit`.

В конфиге для нужного `actor` должен быть настроен `portable_profile_dir` или `portable_profile_name`.

Dry-run:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner prepare-add-contact-profile \
  --config /path/to/config.json \
  --actor-id account_01 \
  --contact-id qa_friend
```

Открыть профиль allowlist-контакта без финального добавления:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner prepare-add-contact-profile \
  --config /path/to/config.json \
  --actor-id account_01 \
  --contact-id qa_friend \
  --execute \
  --launch-if-needed
```

Пройти `Add to contacts -> Done` автоматически:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner prepare-add-contact-profile \
  --config /path/to/config.json \
  --actor-id account_01 \
  --contact-id qa_friend \
  --execute \
  --launch-if-needed \
  --confirm-add \
  --verify-profile-reopen
```

Если Telegram UI у конкретного portable-профиля чуть смещён, можно подстроить ratio-флаги:

- `--add-click-x-ratio`
- `--add-click-y-ratio`
- `--done-click-x-ratio`
- `--done-click-y-ratio`
- `--done-click-repeat`

## Контрольная Точка Для Агента

По состоянию на `2026-05-02` desktop-path `поиск -> профиль -> Add to contacts -> Done` уже подтверждён как рабочий на actor `ak` с portable-профилем `/home/max/TelegramPortableAK`.

Что зафиксировано как working baseline:

- smoke-target: `manual_super_pavlik`
- username: `@super_pavlik`
- search result: `search_result_index = 2`
- успешный live-run: [run.json](/home/max/.local/share/telegram-sandbox-activity-runner/runs/20260502T064226-de0a009a/run.json)
- итоговый submit-click для модалки `Новый контакт`:
  - `dialog_submit_click = { x_ratio: 0.5576, y_ratio: 0.7611 }`
- итоговая verify-статистика:
  - `status = ui_verify_contact_present`
  - `add_button_visible = false`
  - `edit_button_visible = true`
  - `delete_button_visible = true`

Что уже важно не ломать:

- перед `Add to contacts` tool обязан проверить exact username guard в profile overlay;
- submit `Готово` должен считаться от геометрии самой dialog-модалки, а не от слепой точки под окном;
- после clipboard-вставки `Имя/Фамилия` helper должен схлопывать выделение через `End`, иначе следующий клик может уйти в снятие selection вместо `Готово`.

Если следующий агент продолжает этот путь:

- начинать не с новой калибровки, а с артефакта `20260502T064226-de0a009a`;
- сравнивать новые случаи с этим baseline;
- считать сильным сигналом успеха именно `Edit contact / Delete contact`, а не только факт клика по `Done`.

## Batch Add To Contacts

Для дозированного добавления сразу нескольких allowlisted `contact_id` есть отдельный batch-runner.

Dry-run:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner batch-add-contacts \
  --config /path/to/config.json \
  --actor-id account_01 \
  --contact-id qa_friend
```

Execute:

```bash
tools/telegram_sandbox_activity_runner/bin/telegram-sandbox-activity-runner batch-add-contacts \
  --config /path/to/config.json \
  --actor-id account_01 \
  --contact-id-file /path/to/contact_ids.txt \
  --execute
```

## Практические замечания

- Для `prepare-invite` и `prepare-join` лучше оставлять ручной финальный confirm, если нет отдельного внутреннего процесса согласования.
- Для Desktop-flow лучше держать один активный portable actor за раз, чтобы не смешивать окна и AT-SPI контекст.
- Для API-sidecar сначала полезно прогнать `api-scan-contacts`, чтобы отделить реальные user-аккаунты от stale / invalid username.
