# MANGO ВАТС: быстрый запуск маршрутизации в n8n

Документ для запуска связки MANGO -> n8n с проверкой подписи и командой маршрутизации `route`.

## Что уже подготовлено

- Готовый workflow для импорта:
  - `/home/max/AI_CORE/Agent/MANGO_INBOUND_ROUTE_DRAFT.json`
- Внутри workflow:
  - `POST /webhook/mango/events/call` — прием события вызова, проверка подписи, отправка `commands/route`;
  - `POST /webhook/mango/events/summary` — прием финального события вызова;
  - `POST /webhook/mango/events/recording` — прием события записи.

## Ключевые правила API MANGO

По документации `MangoOffice_VPBX_API_v1.9.pdf`:

- Подпись считается так:
  - `sign = sha256(vpbx_api_key + json + vpbx_api_salt)`
- Подписываются все запросы в обе стороны.
- Команда маршрутизации:
  - `POST https://app.mango-office.ru/vpbx/commands/route`

## Переменные окружения для workflow

Перед активацией workflow задайте переменные в окружении n8n:

- `MANGO_API_KEY` — ваш `vpbx_api_key` из API-коннектора MANGO;
- `MANGO_API_SALT` — ваш `vpbx_api_salt`;
- `MANGO_ROUTE_TO_NUMBER` — куда переводить вызов (`sip:...` / внутренний номер / PSTN);
- `MANGO_ROUTE_ON_STATES` — список состояний через запятую, по умолчанию `Appeared,Ringing`.

Примечание: если `MANGO_API_SALT` пустой, workflow не будет отправлять route-команду и вернет причину `MANGO_API_SALT is empty`.

## Что указать в личном кабинете MANGO

В разделе интеграции/webhook событий:

- `events/call` -> `https://<ВАШ_ДОМЕН>/webhook/mango/events/call`
- `events/summary` -> `https://<ВАШ_ДОМЕН>/webhook/mango/events/summary`
- `events/recording` -> `https://<ВАШ_ДОМЕН>/webhook/mango/events/recording`

## Быстрая проверка

1. Импортируйте workflow `MANGO_INBOUND_ROUTE_DRAFT.json`.
2. Заполните переменные окружения (`MANGO_*`).
3. Активируйте workflow.
4. Позвоните на номер ВАТС и проверьте execution в n8n:
   - если все ок, в ответе webhook будет `action = route_sent`;
   - если нет, `action = skipped` с `reason`.

## Подсказка по `MANGO_ROUTE_TO_NUMBER`

- Для SIP-направления используйте номер/адрес в формате, допустимом MANGO (`sip:...`),
  либо внутренний номер сотрудника/группы.
- Для сценария с внешним AI/SIP endpoint сначала убедитесь, что SIP Trunk и маршрутизация
  в MANGO настроены (см. `MO_SIP_Trunk.pdf`).
