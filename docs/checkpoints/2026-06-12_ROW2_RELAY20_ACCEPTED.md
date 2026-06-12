# 2026-06-12: `row_2` на `RELAY_TIMEOUT=20` прошёл accepted-path

## Сделано
- Подняты только три минимальных workflow:
  - `sHTbALayEZdy8Mzs`
  - `tdiAEZM9FZDEP7k4`
  - `kZSdJrsAHWWIC2l6`
- Выполнен один manual webhook на:
  - `row_2`
  - `+79299679869`
  - `Акимова Ксения Игоревна`
  - `request_id = manual.2026-06-12.ROW2.relay20.check`
- Webhook вернул:
  - `HTTP 200`
  - `call_requested`
  - `conversation_id = conv_4401ktxeqcgpe849zebbr4w7hw82`
  - `sip_call_id = SCL_NBjVPo55YEmj`
- Relay journal:
  - outgoing payload совпал по `row_2 / phone / request_id`
  - upstream вернул:
    - `Upstream 200 (6138ms, 139 bytes)`
    - `success = true`
    - `Outbound call initiated`
- Detail по `conv_4401ktxeqcgpe849zebbr4w7hw82`:
  - `user_id = row_2`
  - `external_number = +79299679869`
  - `request_id = manual.2026-06-12.ROW2.relay20.check`
  - `status = done`
  - `error = null`
- Transcript:
  - `user @1s = "...""`
  - `agent @3s = "Алло, меня слышно? Вы тут?"`
  - `user @6s = "Клиника «Визави», меня зовут Марина. Добрый день."`
  - `agent @10s = fixed opener`

## На чем остановились
- `RELAY_TIMEOUT=20` подтвердился как рабочий для accepted outbound-case.
- Это уже не relay-timeout, а нормальный исходящий старт разговора.
- Но этот конкретный разговор не дошёл до `call_log`:
  - `tool_names = null`
  - `transcript_count = 4`
- Значит call-log слой этим тестом ещё не проверен.

## Что делать дальше
1. Снова держать минимальный контур выключенным между циклами.
2. Следующий одиночный тест делать по следующему живому лиду.
3. Цель следующего цикла:
   - не проверять relay повторно ради самого relay;
   - проверить, доезжает ли живой разговор до `call_log` и полного `eleven_conv_id`.
