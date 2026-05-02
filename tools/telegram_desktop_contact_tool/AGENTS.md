# AGENTS.md

Этот каталог — GitHub-ready wrapper вокруг `telegram_sandbox_activity_runner` для Desktop contact-flow.

## Что читать сначала

1. [README_RU.md](/home/max/n8n_ai_call_center/tools/telegram_desktop_contact_tool/README_RU.md)
2. [../telegram_sandbox_activity_runner/AGENTS.md](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/AGENTS.md)
3. [../telegram_sandbox_activity_runner/CHECKPOINT_RU.md](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/CHECKPOINT_RU.md)

## Граница ответственности

- Здесь лежат docs и launcher-обертки.
- Бизнес-логика остается в `../telegram_sandbox_activity_runner/`.
- Не дублировать здесь runner-код без необходимости.

## После изменений

- Обновить этот `README_RU.md`, если меняется входной UX wrapper-команды.
- Если меняется реальный flow, обновить checkpoint в `../telegram_sandbox_activity_runner/CHECKPOINT_RU.md`.
