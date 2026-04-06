# 11. Eleven Outbound Relay

## Назначение
- Обходит сетевой/geo-блок при исходящем вызове ElevenLabs из live `n8n`.
- `n8n` больше не бьет напрямую в `api.elevenlabs.io`.
- Вместо этого `n8n` вызывает relay через публичный HTTPS tunnel.
- Relay на локальной машине уже делает прямой `POST` в ElevenLabs API.

## Компоненты
- `scripts/eleven_outbound_relay_server.py`
- `scripts/localhost_run_tunnel_sync.py`

## Как это работает
1. Локальный relay слушает `127.0.0.1:8787`.
2. `localhost.run` дает внешний HTTPS URL на этот локальный relay.
3. `localhost_run_tunnel_sync.py` отслеживает текущий tunnel URL.
4. При каждом новом URL скрипт автоматически патчит live workflow `VOICE_INBOUND_AGENT (draft)`.
5. Нода `Eleven | Outbound HTTP` начинает ходить не в Eleven напрямую, а в relay.

## Безопасность
- Доступ к relay защищен заголовком `X-Relay-Token`.
- Токены и ключи не должны храниться в git.
- Для runtime использовать локальный env-файл вне репозитория.

## Проверка
- `GET /health` на relay должен отвечать `ok: true`.
- `POST /webhook/eleven/outbound-call` в live `n8n` должен перестать возвращать HTML/Cloudflare page.
- При upstream отказе Eleven должен возвращаться обычный JSON провайдера, а не `provider_rejected`.
