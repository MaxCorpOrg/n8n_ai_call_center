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
- Сейчас `source=fallback`, потому что Postgres credential недоступен из n8n runtime (ошибка DNS/host).

Это безопасный режим: звонки не падают, tool возвращает валидную структуру ответа.

## 5) Что нужно для полноценного режима `source=postgres`

1. Исправить доступность Postgres credential `Postgres Memory Agent (ssl disable v2)` для workflow runtime.
2. После восстановления подключения tool автоматически начнет отдавать данные из:
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
