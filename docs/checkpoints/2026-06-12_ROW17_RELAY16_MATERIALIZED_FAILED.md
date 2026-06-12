# 2026-06-12: `row_17` на `RELAY_TIMEOUT=16` уже materialize-ится как failed conversation

## Сделано
- Выполнен новый одиночный test call по:
  - `row_17`
  - `+79012091111`
  - `request_id = manual.2026-06-12.ROW17.relay16.check`
- Для цикла были подняты только:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
- Relay journal подтвердил точный outgoing payload:
  - `to_number = +79012091111`
  - `user_id = row_17`
  - `lead_id = row_17`
  - `source_record_key = row_17`
  - `request_id = manual.2026-06-12.ROW17.relay16.check`
- Relay всё ещё отдал timeout:
  - `Upstream failed (16064ms): The read operation timed out`
  - `POST /eleven/outbound-call HTTP/1.1 502`
- Но новый failed conversation уже появился в Eleven:
  - `conversation_id = conv_6001ktx8q4n6e5hsww1ssxdhvj7y`
  - `status = failed`
  - `error.reason = sip request timed out`
  - `user_id = row_17`
  - `external_number = +79012091111`
- После цикла три минимальных workflow снова выключены.

## На чем остановились
- `RELAY_TIMEOUT=16` уже лучше `14` для длинных upstream-case:
  - conversation стал materialize-иться в Eleven.
- Но сам SIP timeout по `row_17` никуда не делся.
- Detail по новому conversation вернул старый `request_id` от предыдущего `row_17`-цикла, хотя relay отправлял новый.

## Что делать дальше
1. Оставить `RELAY_TIMEOUT=16` как текущий рабочий baseline.
2. Не гонять дальше `row_17` по кругу.
3. Следующий одиночный тест делать уже на новом пригодном номере из следующей базы.
4. Считать расхождение `request_id` на повторных циклах одного и того же lead provider-side аномалией, а не локальной relay-подменой.
