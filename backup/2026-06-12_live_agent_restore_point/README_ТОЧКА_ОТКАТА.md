# Точка отката live-агента от 2026-06-12

## Что это

Это локальный backup-пакет состояния проекта и live-настроек агента на момент, когда:

- opener уже закреплен в форме:
  - `Здравствуйте. Мы официальный представитель липолитика ЛипоЛонг, звоним по поводу сотрудничества для косметологов. Вам это в принципе интересно?`
- жёсткая промежуточная refusal-логика отменена;
- текущая подтвержденная live version:
  - `agtvrsn_0901ktxsrethemqr4prhkw701wr2`

## Где лежит

- папка:
  - `/home/max/n8n_ai_call_center/backup/2026-06-12_live_agent_restore_point`

## Что внутри

- `agent_live/`
  - текущие JSON-снимки live-конфига агента;
- `payloads/`
  - payload-ы ключевых июньских patch-шагов;
- `docs_snapshot/`
  - копии актуальной документации и checkpoint-файлов;
- `git_state/`
  - ветка, commit, status и короткий log перед фиксацией;
- `diffs/current_uncommitted_changes.patch`
  - patch по несохраненным изменениям на момент сборки backup;
- `workflow_runtime_state.txt`
  - состояние минимальных workflow в `n8n` на момент точки отката.

## Как использовать для отката

1. Сначала смотреть:
   - `agent_live/current_ai_call_agent_1.after_negative_recovery_dozhim_confirmed.json`
   - `docs_snapshot/02_ТЕКУЩЕЕ_LIVE_СОСТОЯНИЕ.md`
   - `docs_snapshot/04_ELEVENLABS_АГЕНТ.md`
2. Если нужно вернуть prompt-логику:
   - брать payload из `payloads/`
   - сверять его с текущим live GET
   - применять точечно, не меняя лишние `tool_ids`, `voice_id`, `first_message`
3. Если нужно вернуть локальную рабочую точку:
   - сверять `git_state/head_before_commit.txt`
   - сверять `diffs/current_uncommitted_changes.patch`
4. Перед любым новым risky patch:
   - делать новый backup рядом, не перетирать этот.

## Что считается эталоном этой точки

- ветка:
  - `codex/email-followup-agent-live`
- live-агент:
  - `AI_CALL_AGENT_1`
- agent id:
  - `agent_8801kgybyekned2a8yae6rp8hk3q`
- live version:
  - `agtvrsn_0901ktxsrethemqr4prhkw701wr2`

## На чем остановились

- refusal-логика после короткого `нет` возвращена из слишком жёсткого режима в аккуратный дожим;
- тестовый outbound-контур снова поставлен на паузу;
- следующий шаг уже не backup, а новый одиночный тест на этой live version.

## Что делать дальше

1. Поднимать только минимальный тестовый контур.
2. Делать один одиночный звонок по следующему номеру по порядку.
3. Проверять:
   - нет ли раннего rescue до opener;
   - нет ли длинного spoken-closing после отказа;
   - есть ли ровно один короткий дожим вместо жёсткого обрыва.
