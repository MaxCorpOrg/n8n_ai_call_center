# 2026-06-12: pre-opener rescue guard и `row_7`

## Сделано
- В live prompt добавлен отдельный запрет на rescue до opener.
- Новая live version:
  - `agtvrsn_8901ktxmrb3afycrp3qt18caaz4y`
- Затем выполнен один одиночный звонок:
  - `row_7`
  - `Евгения Волкова`
  - `+79627956556`
  - `request_id = manual.2026-06-12.ROW7.preopenerguard`
  - `conversation_id = conv_3701ktxmtdh8f10ae63mzf63mj7f`

## Что показал звонок
- Кейс оказался voicemail:
  - `Мой абонент не отвечает... Вы можете оставить сообщение после звукового сигнала.`
- Агент:
  - не сказал rescue-фразу;
  - не сказал opener;
  - не оставил spoken-message;
  - сделал `call_log`;
  - затем `end_call`.

## На чем остановились
- Новый pre-opener guard voicemail-ветку не ломает.
- На этом тесте он сработал корректно: раннего `Алло, меня слышно? Вы тут?` не было.
- Но это ещё не human-case подтверждение, потому что звонок ушёл в голосовую почту.

## Что делать дальше
1. Оставить текущую version как есть.
2. Сделать следующий одиночный звонок по следующему номеру по порядку.
3. Проверить уже именно живого человека:
   - нет ли раннего rescue до opener;
   - стартует ли сразу короткий opener после `алло/да/говорите`.

## Артефакты
- `backups/2026-06-12_preopener_rescue_block/current_ai_call_agent_1.before_preopener_rescue_block.json`
- `backups/2026-06-12_preopener_rescue_block/main_preopener_rescue_block_payload.json`
- `backups/2026-06-12_preopener_rescue_block/current_ai_call_agent_1.after_preopener_rescue_block.json`
- `.runtime/single_call_2026-06-12_row_7_preopener_guard_check/request_payload.json`
- `.runtime/single_call_2026-06-12_row_7_preopener_guard_check/outbound_headers.txt`
- `.runtime/single_call_2026-06-12_row_7_preopener_guard_check/outbound_body.txt`
- `.runtime/single_call_2026-06-12_row_7_preopener_guard_check/relay_logs.txt`
- `.runtime/single_call_2026-06-12_row_7_preopener_guard_check/eleven_recent_conversations.json`
- `.runtime/single_call_2026-06-12_row_7_preopener_guard_check/conv_3701ktxmtdh8f10ae63mzf63mj7f.json`
