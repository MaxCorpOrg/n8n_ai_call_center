# 06. ElevenLabs Tool -> n8n Context Bridge

Этот сценарий добавляет tool/webhook для ElevenLabs, чтобы агент мог запрашивать расширенный контекст из нашей базы.

## 1) Что создано

- Workflow: `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
- n8n workflow id: `tdiAEZM9FZDEP7k4`
- Endpoint:
  - `POST https://www.n-8-n.site/webhook/eleven/tool/context`

Экспорт workflow:
- `workflows/ELEVEN_TOOL_CONTEXT_BRIDGE_DRAFT.json`

## 2) Формат запроса от Eleven Tool

```json
{
  "session_id": "test-memory-002",
  "client_ref": "cli_...",
  "caller": "+7999...",
  "query": "что важно сказать про доставку",
  "top_k": 6
}
```

## 3) Формат ответа

```json
{
  "ok": true,
  "tool": "context_fetch",
  "source": "postgres|fallback",
  "context": {
    "session_id": "...",
    "client_ref": "...",
    "caller": "...",
    "query": "...",
    "history": [],
    "memory_facts": [],
    "source_links": [],
    "knowledge_chunks": [],
    "script_steps": []
  },
  "warning": "...",
  "error_info": {},
  "hint": "PII хранится во внешнем источнике..."
}
```

## 4) Текущий статус

- Endpoint активен и отвечает.
- Runtime-проверка: `source=postgres` (контекст читается из PostgreSQL).
- Fallback-режим сохранен как защитный механизм: при временной недоступности Postgres endpoint все равно вернет валидный JSON.

## 5) Что нужно для полноценного режима `source=postgres`

1. Держать поднятыми сервисы `postgres_memory` и `postgrest` в docker compose.
2. Проверять credential `Postgres Memory Agent (ssl disable v2)` при изменениях инфраструктуры.
3. Endpoint отдает данные из:
- `agent_memory` (история),
- `memory_facts`,
- `client_source_links`,
- `knowledge_chunks`,
- `script_steps`.

## 6) Подключение в ElevenLabs

В агенте ElevenLabs добавь Tool (HTTP):
- Method: `POST`
- URL: `https://www.n-8-n.site/webhook/eleven/tool/context`
- Body: передавать `session_id`, `client_ref`, `caller`, `query`, `top_k`

Рекомендация:
- хранить в Eleven только компактное ядро KB,
- расширенный контекст получать этим tool из нашей инфраструктуры.

## 7) Финальная проверка в проде (чек-лист)

Проверка на дату: `2026-02-25`.

1. В ElevenLabs -> `Conversations` открыть успешный звонок агента `AI_CALL_AGENT_1`.
2. Во вкладке `Transcription` убедиться, что есть событие:
   - `Tool succeeded: context_fetch`.
3. В n8n открыть workflow `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` -> `Executions`.
4. Открыть execution, совпадающий по времени со звонком, и проверить в `Tool | Respond`:
   - `"ok": true`
   - `"source": "postgres"`
   - `"warning": ""`

Если пункты выше выполняются, то цепочка `Eleven Tool -> n8n webhook -> Postgres context` работает корректно.
