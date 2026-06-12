# 2026-06-12: `row_8` подтвердил human-entry после pre-opener guard

## Сделано
- После версии `agtvrsn_8901ktxmrb3afycrp3qt18caaz4y` выполнен один одиночный звонок:
  - `row_8`
  - `Марина`
  - `+79217897373`
  - `request_id = manual.2026-06-12.ROW8.humanguard`
  - `conversation_id = conv_7701ktxn8n09edytw4rg9s6qcq8y`

## Что показал звонок
- Это был живой human-case.
- Transcript:
  - user:
    - `Добрый день, клиника «Леса мечты». Меня зовут Екатерина.`
  - agent:
    - `Здравствуйте. Мы официальный представитель ЛипоЛонг, звоним по поводу сотрудничества для косметологов. Вам это в принципе интересно?`
- Раннего `Алло, меня слышно? Вы тут?` до opener не было.

## На чем остановились
- Bundle из двух правок подтверждён:
  1. короткий opener;
  2. запрет раннего rescue до opener.
- Это уже не гипотеза, а подтверждённый live-human результат.

## Что делать дальше
1. Не откатывать эти две правки.
2. Следующий фокус перенести на второй ход после opener.
3. Отдельно разбирать relay timeout noise, который остаётся внешне даже при реальном разговоре.

## Артефакты
- `.runtime/single_call_2026-06-12_row_8_human_guard_check/request_payload.json`
- `.runtime/single_call_2026-06-12_row_8_human_guard_check/outbound_headers.txt`
- `.runtime/single_call_2026-06-12_row_8_human_guard_check/outbound_body.txt`
- `.runtime/single_call_2026-06-12_row_8_human_guard_check/relay_logs.txt`
- `.runtime/single_call_2026-06-12_row_8_human_guard_check/eleven_recent_conversations.json`
- `.runtime/single_call_2026-06-12_row_8_human_guard_check/conv_7701ktxn8n09edytw4rg9s6qcq8y.json`
