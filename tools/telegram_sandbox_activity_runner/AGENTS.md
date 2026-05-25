# AGENTS.md

Этот файл задает правила для агентов, которые продолжают работу по `telegram_sandbox_activity_runner`.

## Что прочитать сначала

1. [CHECKPOINT_RU.md](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/CHECKPOINT_RU.md)
2. [README_RU.md](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/README_RU.md)
3. [09_PROJECT_CHANGELOG_AND_STATE.md](/home/max/n8n_ai_call_center/docs/knowledge_base/09_PROJECT_CHANGELOG_AND_STATE.md)
4. [PROJECT_STATUS_RU.md](/home/max/site-control-kit/docs/PROJECT_STATUS_RU.md)

## Границы этого инструмента

- Это комплаентный инструмент для operator-assisted Telegram Desktop и allowlist-only Telegram API сценариев.
- Не расширять его в сторону обхода ограничений Telegram, массовой автоматизации без подтверждения, proxy-эвейжна или ротации аккаунтов для увеличения лимитов.
- Для Desktop-контура считать `site-control-kit` обязательной зависимостью, а не копировать его функции в этот каталог.

## Что считать источником истины

- Основной runner: [telegram_sandbox_activity_runner.py](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/telegram_sandbox_activity_runner.py)
- Optional API sidecar: [telegram_api_sidecar.py](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/telegram_api_sidecar.py)
- Desktop helper: [telegram_portable.py](/home/max/site-control-kit/scripts/telegram_portable.py)
- Текущий рабочий baseline: [CHECKPOINT_RU.md](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/CHECKPOINT_RU.md)

## Перед правками

1. Посмотреть `git -C /home/max/n8n_ai_call_center status --short`.
2. Посмотреть `git -C /home/max/site-control-kit status --short`, если меняется Desktop helper.
3. Для contact-flow сначала открыть live baseline run `20260502T064226-de0a009a`.
4. Не начинать новую калибровку кликов, пока не сравнены текущие изменения с этим baseline.

## После правок

- Обновить [README_RU.md](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/README_RU.md), если меняется поведение или UX команды.
- Обновить [CHECKPOINT_RU.md](/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/CHECKPOINT_RU.md) после каждого значимого live или flow-изменения.
- Обновить [09_PROJECT_CHANGELOG_AND_STATE.md](/home/max/n8n_ai_call_center/docs/knowledge_base/09_PROJECT_CHANGELOG_AND_STATE.md).
- Если менялся `telegram_portable.py`, обновить и [PROJECT_STATUS_RU.md](/home/max/site-control-kit/docs/PROJECT_STATUS_RU.md).

## Минимальные проверки

- `python3 -m py_compile /home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner/telegram_sandbox_activity_runner.py`
- `python3 -m py_compile /home/max/site-control-kit/scripts/telegram_portable.py`
- `python3 -m unittest discover -s /home/max/n8n_ai_call_center/tests -p 'test_telegram_sandbox_activity_runner.py'`
- `python3 -m unittest discover -s /home/max/n8n_ai_call_center/tests -p 'test_telegram_allowlist_tool.py'`
- `PYTHONPATH="/home/max/site-control-kit" python3 -m unittest discover -s /home/max/site-control-kit/tests -p 'test_*.py'`
- `git -C /home/max/n8n_ai_call_center diff --check`
- `git -C /home/max/site-control-kit diff --check`
