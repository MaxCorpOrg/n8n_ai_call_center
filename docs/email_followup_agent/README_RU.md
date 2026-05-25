# Email Followup Agent (RU)

## Что это

Это отдельный production-контур для email-follow-up по таблицам обзвона.

Назначение:

- найти лиды, где по звонку нужно отправить информацию;
- найти или исправить email;
- отправить письмо с PDF-коммерческим предложением;
- обработать bounce;
- отчитаться в Telegram.

Контур работает отдельно от `ElevenLabs` и отдельно от `AUTODIAL_DISPATCHER`.

## Что читать в первую очередь

1. `01_ARCHITECTURE_AND_FLOW_RU.md`
2. `02_LIVE_CONFIG_AND_SCHEDULE_RU.md`
3. `03_SEARCH_RULES_AND_FILTERS_RU.md`
4. `04_RUNBOOK_AND_OPERATIONS_RU.md`
5. `06_CHECKPOINT_RU.md`

Если нужен фактологический отчёт по текущей проверке:

6. `05_TEST_REPORT_2026-04-29_RU.md`

## Структура пакета

- `README_RU.md`
  - индекс и порядок чтения
- `01_ARCHITECTURE_AND_FLOW_RU.md`
  - из чего состоит агент и как проходит один прогон
- `02_LIVE_CONFIG_AND_SCHEDULE_RU.md`
  - текущее prod-состояние, таблицы, сервисы, расписание
- `03_SEARCH_RULES_AND_FILTERS_RU.md`
  - как агент ищет email и какие адреса режет
- `04_RUNBOOK_AND_OPERATIONS_RU.md`
  - команды, проверки, деплой, диагностика
- `05_TEST_REPORT_2026-04-29_RU.md`
  - детальный отчёт по реальным тестам и live-прогонам
- `06_CHECKPOINT_RU.md`
  - обязательная контрольная точка для следующей сессии

## Связанные файлы в проекте

- сервис:
  - `scripts/email_followup_service.py`
- запускной скрипт:
  - `scripts/run_email_followup_service.sh`
- workflow draft:
  - `workflows/EMAIL_FOLLOWUP_AGENT_DRAFT.json`
  - `workflows/EMAIL_FOLLOWUP_AGENT_MANUAL_DRAFT.json`
- env template:
  - `.env.email_followup.example`
- systemd template:
  - `deploy/systemd/email_followup.service.example`

## Что обязательно обновлять после значимых изменений

- `06_CHECKPOINT_RU.md`
- `docs/knowledge_base/09_PROJECT_CHANGELOG_AND_STATE.md`
- если изменилось live-состояние:
  - `документация_для_агента/02_ТЕКУЩЕЕ_LIVE_СОСТОЯНИЕ.md`
