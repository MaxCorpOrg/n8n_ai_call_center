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

## Как использовать

1. Загрузить `.md` файлы в ElevenLabs Knowledge Base (`Add Files`).
2. Оставить `context_fetch` подключенным к агенту.
3. Выполнить `sql/005_seed_lipolong_kb_pack.sql` в `postgres_memory`, чтобы контекст возвращался из Postgres.
4. Создать Google Sheet скриптом `scripts/create_google_sheet_callcenter.py`.
