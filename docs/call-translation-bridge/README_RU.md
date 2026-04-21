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

7. `07_ELEVEN_TOOL_CALL_LOG_RU.md`  
   Подключение Tool/Webhook `call_log` для автозаписи результатов звонка в Google Sheet.

8. `08_LIVE_ELEVEN_AGENT_RU.md`
   Текущая live-конфигурация ElevenLabs-агента: LLM, voice, human-answer gate, turn-taking, `skip_turn` / `voicemail_detection` и практические замечания по тестам.

9. `09_ELEVEN_TOOL_SEND_SMS_RU.md`
   Подключение Tool/Webhook `send_sms_info` для отправки SMS через Mango direct API из ElevenLabs через n8n, включая правило `на этот номер` -> `system__called_number`.

10. `10_AUTODIAL_DISPATCHER_RU.md`
   Автодозвон по таблице `Лиды_обзвон`: окно `10:00–14:00` МСК, лимит `15` исходящих звонков в день, не более `2` автодозвонов на номер в день и остановка кампании после исчерпания списка.

11. `../agent_kb_lipolong/README_RU.md`  
   Готовый KB-пакет для агента (контент + схема Google Sheet + шаги создания таблицы).

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
