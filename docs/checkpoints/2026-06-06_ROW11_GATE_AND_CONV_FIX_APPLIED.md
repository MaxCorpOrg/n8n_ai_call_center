# 2026-06-06: применены fix после `row_11` без нового звонка

## Сделано
- После разговора `conv_1301kte9dps8ejfvk7fzy4zstvxs` не запускался новый тестовый звонок; сначала применены две точечные правки.
- Live `Main` в ElevenLabs обновлён через relay-host `151.241.228.232`:
  - новая live version:
    - `agtvrsn_7601ktec2xpde6sbn0s4t2heszyz`
  - `turn_timeout = 2.0`
  - `soft_timeout_config.timeout_seconds = -1.0`
  - `soft_timeout_config.message = "Алло, меня слышно? Вы тут?"`
- Это отключает глобальный rescue-таймер как технический механизм разговора и убирает конфликт с `human-answer gate`.
- Prompt одновременно усилен:
  - rescue-вопрос разрешён только после:
    1. явного живого ответа;
    2. уже сказанного opener;
    3. следующего хода с `...`/тишиной без осмысленного ответа.
- В live schema `call_log` добавлено поле:
  - `conversation_id`
- И `conversation_id`, и `eleven_conv_id` теперь привязаны к:
  - `system__conversation_id`
- Live workflow:
  - `kZSdJrsAHWWIC2l6 | ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
  импортирован заново из локального draft.
- В `Tool | Normalize Call Log` теперь реально исполняется новая нормализация:
  - placeholder-значения вроде `system__conversation_id` и `{{conversation_id}}` режутся;
  - кривые `conv_*` отбрасываются, если они слишком короткие, только цифровые или выглядят как byte/hex-мусор;
  - канонический `conversationId` читается из `body.conversation_id`;
  - `eleven_conv_id` использует `body.eleven_conv_id` с fallback в `body.conversation_id`.
- После импорта workflow остался выключенным:
  - `active = false`
- Новый звонковый цикл после этих fix не запускался; весь контур остаётся на паузе.

## На чем остановились
- Конфигурационно мы уже сделали всё, что нужно было после `row_11`:
  - убрали ранний global rescue;
  - довезли нормализацию malformed `conv_*` в live `call_log` bridge.
- Но эти fix пока подтверждены только:
  - export-ами live-конфига Eleven;
  - export-ом live workflow `ELEVEN_TOOL_CALL_LOG_BRIDGE`;
  - без нового реального звонка.

## Что делать дальше
1. Поднять только минимальные workflow для одного теста:
   - `ELEVEN_OUTBOUND_CALL_BRIDGE (draft)`
   - `ELEVEN_TOOL_CALL_LOG_BRIDGE (draft)`
   - `ELEVEN_TOOL_CONTEXT_BRIDGE (draft)`
2. Сделать один следующий последовательный звонок по:
   - `row_12`
3. Проверить два критерия:
   - rescue-вопрос не звучит слишком рано до post-opener human phase;
   - в ветке `human -> ... -> no_answer` в `call_log` доезжает нормальный текущий `eleven_conv_id`, а не byte-мусор.
4. После звонка снова выключить минимальные workflow и зафиксировать результат отдельным checkpoint.
