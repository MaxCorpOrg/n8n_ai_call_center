# Media Orchestrator Workspace (n8n)

Пакет переносит рабочее пространство из 8 связанных workflow:
- Agent 1: менеджер и диалог в Telegram (оркестратор)
- Router: Intent Router (Code + Switch маршрутизация)
- Agent 2: сценарий и промпты
- Agent 3: генерация изображения через Pollinations (fallback)
- Agent 5: генерация изображения через Gemini/Flow (Vertex)
- Agent 4: генерация/проверка видео в Kling
- KB Sync Agent: автообновление changelog базы знаний + проверка свежести KB
- Memory Neuro Agent: долговременная память в GitHub Markdown + поиск + архив + compact + cloud connector
  - Подключён как tool в Agent 1 (`memoryNeuroAgent`).

## Выбор генератора изображений
В Agent 1 доступны команды:
- `/engine pollinations`
- `/engine gemini`
Если движок не указан, по умолчанию используется Pollinations.

## Router-first архитектура
- В мастере добавлен инструмент `intentRouterTool`.
- Центральный агент сначала вызывает роутер, а потом выбирает нужный инструмент по `route/next_action`.
- Логика интентов вынесена из большого промпта в отдельный workflow `MEDIA_AGENT_ROUTER | Intent Router (draft)`.
- В роутере используется `Switch` для маршрутизации (greeting, engine_select, config_update, confirm_photo, regenerate, confirm_video, image_request, fallback).
- Ошибки обрабатываются на уровне мастера через вторую ветку выхода агента (`Set Error Reply`) и fallback-вопрос.

## KB Sync Agent
- Workflow: `KB_SYNC_AGENT | Knowledge Base Sync (draft)`.
- Функции:
  - проверяет свежесть `docs/knowledge_base` по последним коммитам;
  - добавляет автоматическую запись в `docs/knowledge_base/09_PROJECT_CHANGELOG_AND_STATE.md` (через GitHub API);
  - отправляет статус в Telegram.
- Требует переменную окружения `KB_GITHUB_TOKEN` внутри n8n.
- Опционально использует `N8N_PUBLIC_API_KEY` для краткой статистики по workflow.

## Memory Neuro Agent
- Workflow: `MEMORY_NEURO_AGENT | GitHub Markdown Memory (draft)`.
- Базовый backend: GitHub repo (`MaxCorpOrg/memory` по умолчанию).
- Поддерживаемые actions:
  - `upsert` / `write` / `append` — запись и обновление `.md` памяти;
  - `search` / `find` — поиск по ключам/датам/тексту;
  - `list_files`, `get_file`;
  - `archive_weekly` — еженедельные архивные snapshot;
  - `compact` — compact больших файлов;
  - `sync` / `health_check` — heartbeat и контроль актуальности.
- Есть connector-режим для `gdrive`, `dropbox`, `s3` через внешние endpoint URL.
- Требует env `MEMORY_GITHUB_TOKEN` (для backend `github`).

## Структура
- `workflows/raw/` — полные выгрузки с исходного инстанса
- `workflows/portable/` — минимальные JSON (`name/nodes/connections/settings`)
- `workflows/portable_no_credentials/` — portable JSON без credentials
- `workspace.manifest.json` — описание workspace и зависимостей
- `config/credentials.template.json` — какие credentials нужны
- `config/.env.example` — переменные для скрипта импорта
- `scripts/import_workspace.sh` — автоимпорт и автосвязка ID внутренних агентов

## Быстрый запуск в новом n8n
1. Создайте API key в n8n (`Settings -> n8n API`).
2. Экспортируйте переменные:
```bash
export N8N_BASE_URL="https://your-n8n-domain"
export N8N_API_KEY="your_public_api_key"
export ACTIVATE_MASTER=true
export ACTIVATE_KB_SYNC=false
export ACTIVATE_MEMORY_AGENT=false
```
3. Запустите:
```bash
./scripts/import_workspace.sh
```

## Что сделать после импорта
1. Назначить credentials в UI:
- `telegramApi` для `Telegram Trigger` и `Telegram Reply` в Agent 1
- `openAiApi` (OpenAI-compatible/Mistral) в Agents 1,2,4,5
2. Заменить плейсхолдеры:
- `REPLACE_KLING_API_KEY` в Agent 4
- `REPLACE_TAVILY_API_KEY` в Agent 1
- `REPLACE_GEMINI_API_KEY` в Agent 5
3. Для Memory Neuro Agent задайте env:
- `MEMORY_GITHUB_TOKEN` (обязательно для GitHub backend)
- `MEMORY_CONNECTOR_GDRIVE_URL` / `MEMORY_CONNECTOR_DROPBOX_URL` / `MEMORY_CONNECTOR_S3_URL` (опционально, для connector-режима)

## Важное
- Agent 3 не требует API-ключа (Pollinations URL).
- Agent 5 может упираться в geo/quota ограничения Gemini API.
- Для переносимости роутер импортируется отдельно и автоматически подставляется в мастер скриптом `import_workspace.sh`.
- Для KB Sync Agent добавьте env в n8n: `KB_GITHUB_TOKEN` (scope `repo` на нужный репозиторий).
- Memory Neuro Agent создан отдельным workflow и может подключаться к любым агентам через `Tool Workflow` (`When Executed by Another Workflow`).
