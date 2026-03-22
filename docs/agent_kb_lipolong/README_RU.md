# База знаний агента LipoLong (RU)

Этот пакет подготовлен из материалов:
- `/home/max/AI_CORE/колл_центр_доки /Основные_параметры.txt`
- `/home/max/AI_CORE/колл_центр_доки /КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ (2).pdf`
- `/home/max/AI_CORE/колл_центр_доки /Скрипт созвона или посещения.pdf`

## Состав пакета

1. `01_PRODUCT_PROFILE_RU.md` — продукт, позиционирование, условия.
2. `02_CALL_SCRIPT_RU.md` — сценарий звонка по этапам.
3. `03_OBJECTIONS_RU.md` — карта возражений и короткие ответы.
4. `04_COMPLIANCE_RU.md` — ограничения формулировок.
5. `05_NEXT_STEP_MATRIX_RU.md` — матрица исходов звонка и follow-up.
6. `06_GOOGLE_SHEET_SCHEMA_RU.md` — структура таблицы фиксации звонков.
7. `07_GOOGLE_SHEET_CREATE_STEPS_RU.md` — запуск скрипта создания Google Sheet.
8. `08_ELEVENLABS_SYSTEM_PROMPT_RU.md` — рабочий system prompt для live-агента ElevenLabs.
9. `09_DIALOG_SCRIPTS_RU.md` — живые разговорные скрипты без “деревянного” шаблона.
10. `10_OBJECTION_PLAYBOOK_RU.md` — единая логика обработки мягких возражений и soft-refusal.

## Как использовать

1. Загрузить `.md` файлы в ElevenLabs Knowledge Base (`Add Files`).
2. Оставить `context_fetch` подключенным к агенту.
3. Выполнить `sql/005_seed_lipolong_kb_pack.sql` в `postgres_memory`, чтобы контекст возвращался из Postgres.
4. Создать Google Sheet скриптом `scripts/create_google_sheet_callcenter.py`.
5. Подключить webhook-логирование из Eleven в таблицу:
   - `docs/call-translation-bridge/07_ELEVEN_TOOL_CALL_LOG_RU.md`
6. Для live-настройки агента сверяться с:
   - `docs/call-translation-bridge/08_LIVE_ELEVEN_AGENT_RU.md`
