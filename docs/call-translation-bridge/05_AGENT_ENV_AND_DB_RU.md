# 05. Долговременная память агента (PostgreSQL) + внешние данные клиентов

Документ фиксирует рабочую модель для `VOICE_INBOUND_AGENT (draft)`:
- PostgreSQL хранит только долговременную память, правила, обезличенные логи и аудит действий.
- Персональные данные клиентов (телефоны, ФИО, карточки) остаются во внешнем хранилище (Google Drive/Sheets/CRM).

## 1) Что добавлено в репозиторий

- `sql/003_call_agent_pro.sql` — схема памяти агента без хранения PII.
- `sql/004_seed_lipolong.sql` — стартовый профиль, скрипты, playbook и compliance.
- `.env.agent.example` — env под LLM, политику памяти и внешний источник.
- `scripts/apply_agent_schema.sh` — применяет схему и seed в `postgres_memory`.
- `scripts/import_leads_lipolong.sh` — регистрирует только `client_ref` + ссылки на внешний источник.

## 2) Ключевые таблицы памяти (non-PII)

- `agent_profiles` — профиль агента и system prompt.
- `knowledge_sources`, `knowledge_chunks` — база инструкций/скриптов.
- `script_templates`, `script_steps`, `objection_playbook`, `compliance_rules` — управляемый сценарий разговора.
- `client_memory_refs`, `client_source_links` — обезличенный `client_ref` и где лежат исходные клиентские данные.
- `call_sessions`, `call_turns` — сессии и реплики (только `utterance_redacted`).
- `assistant_action_log` — полный аудит действий ассистента.
- `memory_facts`, `call_quality_reviews`, `training_samples` — обучение и QA-цикл.

## 3) Применение схемы

```bash
cd ~/AI_CORE/n8n-server
cp .env.agent.example .env.agent
source .env.agent
scripts/apply_agent_schema.sh
```

## 4) Регистрация внешних клиентских источников

Пример (Google Sheets / Google Drive):

```bash
cd ~/AI_CORE/n8n-server
source .env.agent
scripts/import_leads_lipolong.sh '/home/max/AI_CORE/колл_центр_доки /Обзвон Воронин Г.П..xlsx' 'gdrive://<sheet_or_file_id>'
```

В Postgres попадут только:
- `client_ref` (обезличенный идентификатор),
- `external_locator` + `record_key` (где взять клиента),
- служебные теги.

## 5) Как подключить к `VOICE_INBOUND_AGENT (draft)`

1. В `ГОЛОСОВОЙ АГЕНТ` добавить/оставить `Postgres Chat Memory` и подключить в порт `ai_memory`.
2. Перед вызовом LLM добавить шаг redaction (скрыть PII в реплике) и писать в `call_turns.utterance_redacted`.
3. Для загрузки/обновления клиентских данных использовать Google Drive/Sheets node (или HTTP к вашему коннектору), а не Postgres.
4. Каждое действие агента писать в `assistant_action_log` (`action_type`, `action_payload`, `status`).

## 6) Обучение без деградации

Правильный цикл:
1. Сессия звонка -> `call_sessions`, `call_turns`, `assistant_action_log`.
2. QA-разбор -> `call_quality_reviews`.
3. Выделение хороших/ошибочных ответов -> `training_samples`.
4. В рабочую память попадают только `approved=true` примеры.

Итог: агент обучается по теме и ведет диалог стабильнее, без хранения PII в PostgreSQL.
