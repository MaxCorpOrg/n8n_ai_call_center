# Media Orchestrator Workspace (n8n)

Этот пакет переносит рабочее пространство из 4 связанных workflow:
- Agent 1: менеджер и диалог в Telegram
- Agent 2: сценарий и промпты
- Agent 3: генерация изображения (fallback через Pollinations URL)
- Agent 4: генерация/проверка видео в Kling

## Структура
- `workflows/raw/` — полные выгрузки с исходного инстанса (для аудита)
- `workflows/portable/` — минимальные JSON (`name/nodes/connections/settings`)
- `workflows/portable_no_credentials/` — portable JSON без credentials (для переноса в новый n8n)
- `workspace.manifest.json` — описание workspace, зависимостей и порядка импорта
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
```
3. Запустите:
```bash
./scripts/import_workspace.sh
```

## Что сделать после импорта
1. Назначить credentials в UI:
- `telegramApi` для `Telegram Trigger` и `Telegram Reply` в Agent 1
- `openAiApi` (OpenAI-compatible/Mistral) в Agents 1,2,4
2. Заменить плейсхолдеры:
- `REPLACE_KLING_API_KEY` в Agent 4
- `REPLACE_TAVILY_API_KEY` в Agent 1

## Важное
- Agent 3 сейчас в fallback-режиме: возвращает рабочий URL генерации изображения через Pollinations.
- Для production можно позже вернуть Agent 3 на Gemini/другой провайдер.
