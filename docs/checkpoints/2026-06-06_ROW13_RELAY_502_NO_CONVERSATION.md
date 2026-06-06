# 2026-06-06: `row_13` не дошёл до разговора, relay вернул `502`

## Сделано
- После fix по `human-gate` и `call_log` traceability выполнен следующий одиночный цикл.
- `row_12` был **не прозван**:
  - `do_not_call = true`
  - причина в preview базы: `похоже на организацию`
- Поэтому для безопасного последовательного теста был взят следующий callable номер:
  - `row_13`
  - `+79370639452`
  - `Врач-косметолог, трихолог Елена Николаевна Шишкина/Бренд «Доктор Шик»`
- Перед тестом были подняты только:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
- Для всех трёх workflow подтверждено:
  - `active = true`
  - `activeVersionId = versionId`
- `n8n` был перезапущен после publish, чтобы webhook-и точно поднялись.
- Отправлен один manual `POST /webhook/eleven/outbound-call`:
  - `request_id = manual.2026-06-06.ROW13.gateconv`
  - HTTP-ответ от webhook:
    - `200`
    - body пустой
- Дальше сняты live-логи:
  - в Eleven за цикл ожидания не появился ни один разговор с:
    - `user_id = row_13`
    - или `request_id = manual.2026-06-06.ROW13.gateconv`
  - relay-host `151.241.228.232` записал:
    - `Relaying to https://api.elevenlabs.io/v1/convai/sip-trunk/outbound-call (778 bytes)`
    - затем:
      - `"POST /eleven/outbound-call HTTP/1.1" 502 -`
- Значит реального разговора не было и до `call_log` дело не дошло.
- После цикла минимальные workflow снова выключены:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)` = `false`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)` = `false`
  - у всех трёх `activeVersionId = null`
- `n8n-server-n8n-1` после остановки снова `healthy`.

## На чем остановились
- Новый fix по `human-gate` и по нормализации `conv_*` этим циклом **не проверился**, потому что разговор вообще не создался.
- Текущий результат цикла — чистый технический upstream failure на relay / outbound-call path.
- Это не speech-case и не подтверждение prompt-регресса.

## Что делать дальше
1. Не делать выводов о речи агента по `row_13`.
2. Следующий одиночный тест делать уже по следующему callable номеру:
   - `row_14`
3. Перед следующим звонком ничего нового в prompt не менять.
4. На следующем цикле проверять уже ту же цель:
   - не срабатывает ли rescue слишком рано;
   - доезжает ли нормальный текущий `eleven_conv_id`.
