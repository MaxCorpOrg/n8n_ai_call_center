# Трансляция звонка: Mango -> SIP Bridge -> Eleven -> LLM

Этот раздел описывает текущую рабочую схему телефонии и правила безопасного расширения под любую LLM.

## Что внутри

1. `01_SYSTEM_OVERVIEW_RU.md`  
   Архитектура, потоки входящих/исходящих и роли каждого компонента.

2. `02_ROUTING_AND_WORKFLOWS_RU.md`  
   Практическая настройка маршрутизации в Mango, Asterisk и n8n.

3. `03_ANY_LLM_INTEGRATION_RU.md`  
   Как подключать любую LLM (OpenAI-совместимую и не только) без поломки телефонии.

4. `04_RUNBOOK_TROUBLESHOOTING_RU.md`  
   Диагностика, типовые ошибки, что проверять в первую очередь.

5. `05_AGENT_ENV_AND_DB_RU.md`  
   Готовое окружение и база данных для обучаемого агента обзвона (non-PII память в Postgres + внешние данные клиентов).

6. `06_ELEVEN_TOOL_CONTEXT_RU.md`  
   Подключение Tool/Webhook из ElevenLabs в n8n для догрузки расширенного контекста + прод-чеклист проверки `context_fetch`.

## Границы системы

- Этот контур отвечает за **маршрутизацию SIP-звонка** и передачу вызова в AI-агента.
- LLM-часть может быть заменена без изменения SIP-бриджа, если соблюден контракт запроса/ответа.
- Нода `ГОЛОСОВОЙ АГЕНТ` в workflow `VOICE_INBOUND_AGENT (draft)` сохраняется как основная точка LLM-логики.

## Быстрый старт проверки

1. Убедиться, что workflow `VOICE_INBOUND_AGENT (draft)` активен.
2. Проверить `POST /webhook/mango/events/call`:
   - исходящий/внутренний звонок -> `action=skipped`;
   - входящий `Appeared` -> `action=route_sent`.
3. Проверить `POST /webhook/eleven/outbound-call` с `to_number=+7...` -> `action=call_requested`.
