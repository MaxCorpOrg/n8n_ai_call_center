# 01. Архитектура системы трансляции звонка

## Цель

Система принимает звонок из Mango, безопасно маршрутизирует его через SIP-бридж и передает в AI-канал (Eleven/LLM), сохраняя управляемость через n8n.

## Состав

1. **Mango Office (ВАТС)**
- источник телефонных вызовов;
- SIP trunk к VPS;
- API события: `events/call`, `events/summary`, `events/recording`.

2. **VPS SIP Bridge (Asterisk)**
- транзит SIP между Mango и Eleven;
- контексты:
  - `from-mango` (Mango -> Eleven),
  - `from-eleven` (Eleven -> Mango).

3. **ElevenLabs SIP/Agent**
- голосовой AI endpoint;
- outbound test calls;
- голосовая логика агента.

4. **n8n workflow: `VOICE_INBOUND_AGENT (draft)`**
- проверка подписи Mango событий;
- решение по маршрутизации (`route`/`skip`);
- webhook для outbound-звонка через Eleven;
- LLM-агент (`ГОЛОСОВОЙ АГЕНТ`) для текстовой/диалоговой логики.

## Поток входящего звонка

1. Звонок приходит в Mango.
2. Mango отправляет `POST /webhook/mango/events/call`.
3. n8n проверяет `vpbx_api_key + sign`.
4. n8n отправляет `commands/route` **только если**:
- событие входящее,
- `call_state=Appeared`,
- нет признака API-loop (`command_id`).
5. Mango направляет звонок в SIP trunk.
6. Asterisk передает вызов в Eleven.

## Поток исходящего AI-звонка

1. Вызов `POST /webhook/eleven/outbound-call` с `to_number=+7...`.
2. n8n валидирует номер и параметры агента.
3. n8n вызывает Eleven `convai/sip-trunk/outbound-call`.
4. Eleven инициирует звонок через SIP-контур.

## Что означает "трансляция звонка"

В этом проекте трансляция = управляемый перенос вызова между системами:
- Телефония (Mango) <-> SIP proxy (Asterisk) <-> Voice AI (Eleven) <-> LLM логика.

Это не только SIP-переадресация, но и контроль маршрута через API-события/правила.

## Критичные инварианты

1. Нельзя делать `route` на исходящие/внутренние события.
2. Нельзя допускать API-loop по `command_id`.
3. Любое изменение LLM не должно менять SIP-маршрутизацию.
4. Все номера в исходящих сценариях храним в формате E.164 (`+7XXXXXXXXXX`).

