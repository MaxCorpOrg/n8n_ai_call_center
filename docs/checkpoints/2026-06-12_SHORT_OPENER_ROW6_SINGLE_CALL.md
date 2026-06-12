# 2026-06-12: короткий opener и одиночный `row_6`

## Сделано
- В live `AI_CALL_AGENT_1` заменён opener на короткий fixed вариант:
  - `Здравствуйте. Мы официальный представитель ЛипоЛонг, звоним по поводу сотрудничества для косметологов. Вам это в принципе интересно?`
- Новая live version:
  - `agtvrsn_4501ktxm8jppehds9her8yamry5n`
- Затем выполнен один одиночный звонок:
  - `row_6`
  - `Анна`
  - `+79182007944`
  - `request_id = manual.2026-06-12.ROW6.shortopener`
  - `conversation_id = conv_8901ktxmazxpeyavvygxvzdkhgg3`
- Relay дал accepted-path:
  - `Upstream 200 (9989ms, 139 bytes)`

## Что показал звонок
- Новый короткий opener реально прозвучал в transcript.
- Но до него сработал rescue:
  1. user: `...`
  2. agent: `Алло, меня слышно? Вы тут?`
  3. user: `Говорите.`
  4. agent: новый короткий opener
- После opener разговор уже не сломался мгновенным перебиванием, как в `row_5`.

## На чем остановились
- Короткий opener удачный и его откатывать не нужно.
- Следующий дефект теперь точечный:
  - ранний rescue до opener всё ещё влезает, если первый ASR-кусок слабый.

## Что делать дальше
1. Оставить короткий opener в live.
2. Подправить правило rescue так, чтобы оно не стреляло до opener.
3. Сделать ещё один одиночный test-call по следующему номеру по порядку.

## Артефакты
- `backups/2026-06-12_short_opener_try/current_ai_call_agent_1.before_short_opener.json`
- `backups/2026-06-12_short_opener_try/main_short_opener_payload.json`
- `backups/2026-06-12_short_opener_try/current_ai_call_agent_1.after_short_opener_retry.json`
- `.runtime/single_call_2026-06-12_row_6_short_opener_check/request_payload.json`
- `.runtime/single_call_2026-06-12_row_6_short_opener_check/outbound_headers.txt`
- `.runtime/single_call_2026-06-12_row_6_short_opener_check/outbound_body.txt`
- `.runtime/single_call_2026-06-12_row_6_short_opener_check/relay_logs.txt`
- `.runtime/single_call_2026-06-12_row_6_short_opener_check/eleven_recent_conversations.json`
- `.runtime/single_call_2026-06-12_row_6_short_opener_check/conv_8901ktxmazxpeyavvygxvzdkhgg3.json`
