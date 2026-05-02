# Telegram Desktop Contact Tool

Отдельная GitHub-ready папка для использования Desktop contact-flow как самостоятельного инструмента поверх `telegram_sandbox_activity_runner`.

## Что это такое

Это не второй независимый engine, а удобная внешняя точка входа для сценариев:

- импорт approved `@username` в allowlist;
- одиночный `Add to contacts` через Telegram Desktop portable;
- дозированный batch `Add to contacts`;
- предварительный `api-scan-contacts`, если нужно отделить реальные user-аккаунты от `not_found` и non-user сущностей.

Вся основная логика живет в соседнем каталоге:

- core runner: [../telegram_sandbox_activity_runner](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner)
- baseline checkpoint: [../telegram_sandbox_activity_runner/CHECKPOINT_RU.md](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/CHECKPOINT_RU.md)
- Desktop helper dependency: [telegram_portable.py](/home/max/site-control-kit/scripts/telegram_portable.py)

## Что принципиально не поддерживается

- обход ограничений Telegram;
- ротация аккаунтов для увеличения лимитов;
- proxy-эвейжн;
- скрытые массовые действия без ручного контроля.

## Содержимое папки

- launcher: [bin/telegram-desktop-contact-tool](/home/max/n8n_ai_call_center/tools/telegram_desktop_contact_tool/bin/telegram-desktop-contact-tool)
- пример approved-list: [examples/usernames.example.txt](/home/max/n8n_ai_call_center/tools/telegram_desktop_contact_tool/examples/usernames.example.txt)
- агентские правила: [AGENTS.md](/home/max/n8n_ai_call_center/tools/telegram_desktop_contact_tool/AGENTS.md)

## Быстрый старт

Импорт approved username-списка:

```bash
tools/telegram_desktop_contact_tool/bin/telegram-desktop-contact-tool import-usernames \
  --config /path/to/ak.local.json \
  --usernames-file tools/telegram_desktop_contact_tool/examples/usernames.example.txt
```

Открыть один контакт и пройти `Add to contacts -> Done`:

```bash
tools/telegram_desktop_contact_tool/bin/telegram-desktop-contact-tool add-one \
  --config /path/to/ak.local.json \
  --actor-id ak \
  --contact-id owner_main \
  --execute \
  --launch-if-needed \
  --confirm-add \
  --verify-profile-reopen
```

Запустить batch по заранее подготовленному списку `contact_id`:

```bash
tools/telegram_desktop_contact_tool/bin/telegram-desktop-contact-tool batch-add \
  --config /path/to/ak.local.json \
  --state-file /path/to/ak.state.json \
  --actor-id ak \
  --contact-id-file /path/to/contact_ids.txt \
  --execute
```

Прогнать API scan до Desktop-flow:

```bash
tools/telegram_desktop_contact_tool/bin/telegram-desktop-contact-tool api-scan \
  --config /path/to/ak.local.json \
  --actor-id ak \
  --contact-id-file /path/to/contact_ids.txt \
  --write-valid-contact-id-file /tmp/valid_contact_ids.txt
```

## Важное operational правило

Если контакт-flow начинает расходиться с baseline, первым делом сверяйся с:

- [../telegram_sandbox_activity_runner/CHECKPOINT_RU.md](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/CHECKPOINT_RU.md)
- [run.json baseline](/home/max/.local/share/telegram-sandbox-activity-runner/runs/20260502T064226-de0a009a/run.json)

Не начинай новую ручную калибровку, пока не понял, чем конкретный кейс отличается от baseline.
