# 2026-06-12: `row_11` accepted на входе, но не дал нового live-trace

## Сделано

- Выполнен следующий номер по порядку:
  - `row_11`
  - `Cosmetology Sl, кабинет косметолога`
  - `+79163021253`
  - `request_id = manual.2026-06-12.ROW11.followupcheck`
- Перед звонком временно были подняты только:
  - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
  - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
  - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
- Внешний webhook ответил:
  - `HTTP 200`
  - `content-type: application/json`
  - body пустой
- Затем дважды снят live Sheet `Лиды_обзвон`:
  - сразу после звонка;
  - и повторно после короткого ожидания.

## Что показал звонок

- Новый `call_log` по:
  - `request_id = manual.2026-06-12.ROW11.followupcheck`
  - `phone_primary = +79163021253`
  - `company_name = Cosmetology Sl, кабинет косметолога`
  не появился.
- В хвосте live Sheet осталась только старая июньская строка другого `row_11` из прежней базы:
  - `Татьяна Голубева Косметология, бьюти услуги`
  - `+79533940071`
- Значит этот цикл пока нельзя честно классифицировать как:
  - human-case;
  - machine-case;
  - secretary-case.
- На текущем наборе доступных live-следов это выглядит как технически accepted webhook без нового боевого materialized trace.

## На чем остановились

- `row_10` уже подтвердил полезный machine-stop без оставленного сообщения.
- `row_11` не дал нового `call_log`, поэтому это уже не prompt-вывод, а инфраструктурная зона:
  - outbound accepted снаружи;
  - но нового итога в Sheet нет.
- После цикла все три workflow снова выключены:
  - `active = false`
  - `activeVersionId = null`

## Что делать дальше

1. Не делать выводы о refusal/dozhim по `row_11`.
2. Следующий практический шаг:
   - либо сразу идти на `row_12`, если цель сейчас именно speech-поведение;
   - либо отдельно добрать technical trace по `row_11` через relay-host / Eleven detail.
3. Если идём дальше именно по звонкам, следующий номер по порядку уже `row_12`.

## Артефакты

- `.runtime/single_call_2026-06-12_row_11_followup_check/request_payload.json`
- `.runtime/single_call_2026-06-12_row_11_followup_check/outbound_headers.txt`
- `.runtime/single_call_2026-06-12_row_11_followup_check/outbound_body.txt`
- `.runtime/single_call_2026-06-12_row_11_followup_check/http_status.txt`
- `.runtime/single_call_2026-06-12_row_11_followup_check/live_sheet_values.json`
- `.runtime/single_call_2026-06-12_row_11_followup_check/live_sheet_values_after_wait.json`
