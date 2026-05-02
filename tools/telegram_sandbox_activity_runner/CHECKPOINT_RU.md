# Checkpoint RU

Последнее обновление: 2026-05-02

Этот файл нужен как короткая контрольная точка именно по `telegram_sandbox_activity_runner`.

## Сделано

- Desktop-path `поиск -> профиль -> Add to contacts -> Done` доведен до рабочего baseline на actor `ak`.
- Для ambiguous username добавлен `search_result_index`, чтобы открывался именно нужный search result.
- Перед `Add to contacts` добавлен exact username guard по profile overlay.
- Submit `Готово` переведен с blind-click на `dialog_submit_click`, который считается от live-геометрии модалки `Новый контакт`.
- Clipboard path после вставки `Имя/Фамилия` теперь схлопывает выделение через `End`, чтобы следующий клик уходил в `Готово`, а не в снятие selection.
- Успешный live baseline:
  - run: [20260502T064226-de0a009a/run.json](/home/max/.local/share/telegram-sandbox-activity-runner/runs/20260502T064226-de0a009a/run.json)
  - smoke-target: `manual_super_pavlik`
  - username: `@super_pavlik`
  - `dialog_submit_click = { x_ratio: 0.5576, y_ratio: 0.7611 }`
  - итог: `ui_verify_contact_present`
  - strong signal: видны `Edit contact` и `Delete contact`, а `Add contact` исчез.
- Рядом с monolith runner добавлен отдельный allowlist-only Telethon CLI:
  - `allowlist_tool/*`
  - launcher: `bin/telegram-allowlist-tool`
- Для GitHub-ориентированного переиспользования добавлен отдельный wrapper-вход:
  - [tools/telegram_desktop_contact_tool](/home/max/n8n_ai_call_center/tools/telegram_desktop_contact_tool)

## На чем остановились

- Working baseline подтвержден на одном ручном smoke-case, но еще не превращен в полностью безкалибровочный массовый Desktop-flow на разных профилях.
- Самый важный следующий риск не в exact username guard, а в воспроизводимости `dialog_submit_click` на других контактах и других вариантах Telegram UI.
- В `n8n_ai_call_center` сам Telegram tool пока живет как отдельный локальный инструмент рядом с основным проектом, поэтому staging/commit надо делать только по его файлам, не захватывая unrelated email/voice изменения.

## Что делать дальше

- Если продолжаем Desktop-flow:
  - стартовать от `20260502T064226-de0a009a`, а не от новой ручной калибровки;
  - сравнивать новые кейсы с этим baseline;
  - подтверждать успех через `Edit contact / Delete contact`, а не только по факту клика.
- Если продолжаем API/allowlist CLI:
  - сначала `validate-allowlist`;
  - потом один controlled live smoke с ручным `YES`.
- Если готовим GitHub-публикацию:
  - использовать [tools/telegram_desktop_contact_tool](/home/max/n8n_ai_call_center/tools/telegram_desktop_contact_tool) как внешний entrypoint;
  - сохранять этот файл как первую точку handoff для следующего агента.
