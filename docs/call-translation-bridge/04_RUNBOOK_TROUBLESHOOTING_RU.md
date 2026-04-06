# 04. Runbook и диагностика

## 1) Быстрая диагностика по симптомам

### Симптом: `connect ETIMEDOUT 151.241.228.232:8787`
Причина: live `n8n` не достукивается до server relay для outbound ElevenLabs.  
Что делать:
- проверить, что `eleven-outbound-relay.service` жив на relay-сервере;
- проверить firewall-правило на `8787/tcp`;
- убедиться, что доступ открыт именно от IP live `n8n` (`147.45.213.87`).

### Симптом: `max auth retry attempts reached`
Причина: новый source IP у Eleven не матчит endpoint в Asterisk.  
Что делать: обновить `identify`/`match` в `pjsip.conf`, reload PJSIP.

### Симптом: `403 Forbidden` при звонке
Чаще всего причина не в n8n, а в ограничениях Mango/тарифа/биллинга.  
Проверить `disconnect_reason` в статистике Mango API.

### Симптом: звонки "на самого себя"
Причина: неверная переадресация (API-loop или маршрут на SIP сотрудника).  
Проверить `Mango | Verify Call Final` и фильтр по `command_id`.

## 2) Команды на VPS

```bash
asterisk -rx "pjsip show endpoints"
asterisk -rx "dialplan show from-mango"
asterisk -rx "dialplan show from-eleven"
asterisk -rvvv
# в CLI:
pjsip set logger on
core set verbose 5
```

## 3) Что смотреть в n8n

1. Execution status для `VOICE_INBOUND_AGENT (draft)`.
2. Последняя нода выполнения (`lastNodeExecuted`).
3. JSON ответа:
- `action=route_sent` или `action=skipped`;
- `reason` для skipped;
- `key_ok` / `sign_ok`.
- Для outbound webhook `POST /webhook/eleven/outbound-call` нормальным успехом считается только валидный accepted payload от ElevenLabs.
- Если в `Eleven | Outbound HTTP` пришел HTML, `Cloudflare`, `Just a moment`, `help.elevenlabs.io` или `action=provider_rejected`, это не успешный звонок, а блок/ошибка upstream-провайдера.
- Если в `Eleven | Outbound HTTP` ошибка `ETIMEDOUT` на `151.241.228.232:8787`, проблема уже не в ElevenLabs, а в маршруте live `n8n` -> relay.

## 4) Обязательный пакет для поддержки Mango

При эскалации отправлять:
1. 3-4 примера за последние 48 часов:
- Номер A / Номер B / Время вызова.
2. Скрин схемы переадресации и SIP trunk.
3. При необходимости pcap с VPS.

## 5) Мини-чеклист перед релизом

1. Inbound event -> `route_sent`.
2. Outbound/internal event -> `skipped`.
3. Eleven outbound webhook -> `call_requested` только при валидном accepted payload; `provider_rejected` считать сбоем провайдера.
4. Нет хардкода новых тестовых номеров в workflow.
5. Ключи и токены не публикуются в документах и чате.
