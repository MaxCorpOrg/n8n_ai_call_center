# Контрольная точка: relay timeout `16 -> 20`

Дата: `2026-06-12`

## Сделано
- На relay-host `151.241.228.232` поднят:
  - `RELAY_TIMEOUT=20`
- Сохранён backup env:
  - `/root/.eleven_outbound_relay.env.bak-2026-06-12_09-55-25`
- Сервис:
  - `eleven-outbound-relay.service`
  успешно перезапущен.
- `/health` после рестарта отвечает штатно.
- Локальный source-of-truth синхронизирован:
  - `scripts/eleven_outbound_relay_server.py`
  - default timeout = `20`
- Дополнительно перепроверено, что минимальные workflow сейчас выключены:
  - `sHTbALayEZdy8Mzs`
  - `tdiAEZM9FZDEP7k4`
  - `kZSdJrsAHWWIC2l6`
  - `bfNbTwtyXNSFzMc2`

## На чем остановились
- На `RELAY_TIMEOUT=16` relay отрезал запрос примерно на `16064ms`.
- Значит это был именно технический потолок ожидания ответа от Eleven/SIP path.
- После подъёма до `20s` уже сделан один новый одиночный тест по:
  - `row_2`
  - `+79299679869`
  - `request_id = manual.2026-06-12.ROW2.relay20.check`
- Результат этого цикла:
  - webhook `HTTP 200`
  - relay `Upstream 200 (6138ms)`
  - `conversation_id = conv_4401ktxeqcgpe849zebbr4w7hw82`
  - detail совпал по `row_2 / phone / request_id`
- Значит `RELAY_TIMEOUT=20` уже достаточен как минимум для нормального accepted-path.
- Но этот разговор завершился рано и до `call_log` не дошёл.

## Что делать дальше
1. Оставить `RELAY_TIMEOUT=20` текущим рабочим baseline.
2. На следующем одиночном цикле проверять уже не сам relay-timeout, а следующий слой:
   - дойдёт ли разговор до `call_log`;
   - не рвётся ли живая линия слишком рано;
   - сохраняется ли полный identity package в логировании.

## Что важно запомнить
- После этого цикла три минимальных workflow снова выключены:
  - `sHTbALayEZdy8Mzs`
  - `tdiAEZM9FZDEP7k4`
  - `kZSdJrsAHWWIC2l6`
- `n8n-server-n8n-1` после финального рестарта снова `healthy`.
