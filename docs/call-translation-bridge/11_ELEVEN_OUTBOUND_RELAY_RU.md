# 11. Eleven Outbound Relay

## Назначение
- Обходит сетевой и geo-блок при исходящем вызове ElevenLabs из live `n8n`.
- `n8n` больше не ходит напрямую в `api.elevenlabs.io` для outbound-call.
- Вместо этого live workflow вызывает отдельный relay на сервере с не-RU egress IP.

## Текущее live-решение
- Relay поднят на отдельном сервере `151.241.228.232`.
- Relay слушает `0.0.0.0:8787`.
- Live workflow `VOICE_INBOUND_AGENT (draft)` вызывает:
  - `http://151.241.228.232:8787/eleven/outbound-call`
- Доступ к relay защищен заголовком `X-Relay-Token`.
- На firewall открыт только `8787/tcp` от IP live `n8n`:
  - `147.45.213.87`

## Почему так сделано
- Direct outbound из live `n8n` мог получать не JSON от ElevenLabs, а HTML block/challenge page.
- Локальный relay через ноутбук работал как временный обход, но был неприемлем для боевого контура.
- Server relay убирает зависимость от ноутбука и позволяет держать стабильный 24/7 runtime.

## Компоненты
- Репозиторий:
  - `scripts/eleven_outbound_relay_server.py`
- Runtime на сервере:
  - `/opt/eleven_outbound_relay.py`
  - `/root/.eleven_outbound_relay.env`
  - `/etc/systemd/system/eleven-outbound-relay.service`

## Как это работает
1. Live `n8n` принимает `POST /webhook/eleven/outbound-call`.
2. Нода `Eleven | Outbound HTTP` отправляет JSON не в Eleven напрямую, а в server relay.
3. Relay проверяет `X-Relay-Token`.
4. Relay уже сам делает `POST` в:
   - `https://api.elevenlabs.io/v1/convai/sip-trunk/outbound-call`
5. Ответ ElevenLabs возвращается обратно в `n8n` как обычный JSON.

## Текущее поведение retry
- С `2026-04-21` relay делает очень узкий безопасный retry для плавающих upstream-сбоев.
- Retry срабатывает только в трёх случаях:
  - network exception при запросе в upstream;
  - HTTP `5xx` от upstream;
  - JSON-ответ ElevenLabs с сообщением:
    - `max auth retry attemps reached`
    - `max auth retry attempts reached`
- Параметры по умолчанию:
  - `RELAY_RETRY_COUNT=1`
  - `RELAY_RETRY_DELAY_MS=1500`
- Это не меняет бизнес-логику автодозвона и не трогает `n8n`.
- Relay просто делает ещё одну быструю попытку пережить короткий upstream-сбой, а если не помогло, возвращает ошибку как раньше.

## Важный сетевой нюанс
- Live `n8n` находится не на relay-сервере.
- `n-8-n.site` резолвится в `147.45.213.87`, а relay живет на `151.241.228.232`.
- Если не открыть `8787/tcp` на relay-сервере для IP `147.45.213.87`, outbound-call будет падать с:
  - `connect ETIMEDOUT 151.241.228.232:8787`

## Проверка
- На relay-сервере:
```bash
systemctl status eleven-outbound-relay.service
curl http://127.0.0.1:8787/health
```

- В live `n8n`:
  - `POST /webhook/eleven/outbound-call` с невалидным номером должен быстро вернуть нормальный JSON ElevenLabs, например `SIP 403`, а не HTML block page.
  - Если relay недоступен по сети, в execution будет:
    - `NodeApiError`
    - `connect ETIMEDOUT 151.241.228.232:8787`

## Безопасность
- Ключ ElevenLabs и relay token не хранятся в git.
- Порт `8787` не открыт публично для всех, а только для IP live `n8n`.
- Если IP live `n8n` изменится, firewall-правило на relay-сервере нужно обновить.
