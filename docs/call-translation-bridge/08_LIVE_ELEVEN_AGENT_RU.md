# Live-настройка ElevenLabs агента (RU)

## Назначение

Этот документ фиксирует текущее рабочее состояние live-агента ElevenLabs для телефонии LipoLong.

Актуальность снимка: `2026-04-07`.

## Идентификаторы

- Agent name: `AI_CALL_AGENT_1`
- Agent ID: `agent_8801kgybyekned2a8yae6rp8hk3q`
- Branch ID: `agtbrch_7801kgybyg9nesrbv64y078pazq0`

## Что подключено

- Телефонный номер: `+79923298897`
- Provider: `sip_trunk`
- Inbound: `true`
- Outbound: `true`
- Webhook tools:
  - `context_fetch`
  - `call_log`
  - `send_sms_info`
- Built-in tools:
  - `end_call`
  - `skip_turn`
  - `voicemail_detection`
- Tool IDs:
  - `tool_1601km62rxpqegqr52m9gk9sftr3` -> `context_fetch`
  - `tool_0901km62rxpre578kd1zvd7q7g04` -> `call_log`
  - `tool_1701km86jmcpek4rj2j1rbhxqtfr` -> `send_sms_info`

## Текущий старт разговора

С `2026-04-07` live-агент работает в режиме `human-answer gate`.

Текущее состояние:
- `first_message = ""`
- до явного живого ответа агент не начинает продажный opener
- первая фраза агента после живого ответа человека должна быть только: `Здравствуйте.`
- после `Здравствуйте.` агент ждёт ещё один короткий живой ответ (`да`, `слушаю`, `добрый день`) и только потом переходит к бизнес-опенеру

## Текущая voice/LLM-конфигурация

- LLM: `gpt-4.1`
- System prompt language: `en`
- Spoken client language: `ru`
- TTS model: `eleven_flash_v2_5`
- Voice: `Elena Gromova — Podcasts & Conversation`
- Voice ID: `0ArNnoIAWKlT4WweaVMY`
- Speed: `1.16`
- Stability: `0.5`
- Similarity boost: `0.78`
- Turn eagerness: `normal`
- Turn timeout: `15.0`
- Speculative turn: `false`

## Поведение на не-человеческом ответе

- Если слышно IVR, запись разговора, `ожидайте`, `подождите`, гудки, неясный шум или тишину, агент не делает pitch и молчит.
- Для этого в live включены built-in tools `skip_turn` и `voicemail_detection`.
- Если линия предлагает оставить сообщение, агент оставляет только короткое сообщение с номером менеджера `8 999 556-67-77`.
- Если линия сообщает, что абонент временно недоступен, агент не пытается продавать и завершает звонок с логикой `no_answer`.
- Окно ожидания живого человека после последней машинной фразы или progress tone: до `15` секунд.

## Текущий pronunciation dictionary

- В live-agent TTS подключён отдельный словарь произношения.
- Dictionary ID: `NnZrxd6lJkbHKqW6w04N`
- Version ID: `8SrjbTKmOZjOnHxLQrxE`
- Locator в live: `pronunciation_dictionary_locators = [{ pronunciation_dictionary_id, version_id }]`
- Исходник словаря в репозитории: `docs/call-translation-bridge/pronunciation/lipolong_agent_base_2026-04-04.rules.json`

Словарь нормализует в первую очередь:
- бренд как `липолонг`
- частые продуктовые слова: `липолитик`, `липолитиками`, `коррекция`, `инъекционные`, `консультация`, `процедуры`
- клиентские каналы: `Telegram`, `WhatsApp`, `MAX`

## Что важно не менять без отдельного теста

- `voice_id`
- `speed`, `stability`, `similarity_boost`
- `pronunciation_dictionary_locators` без проверки новой версии словаря
- webhook URL tools
- `tool_ids` и built-in tools без live-проверки через API
- правило `send_sms_info`: `на этот номер` -> `system__called_number`
- human-answer gate и пустой `first_message`

## Последние ключевые изменения

- `2026-04-04`: live system prompt переведен на английский при сохранении русского разговора.
- `2026-04-04`: подключён pronunciation dictionary.
- `2026-04-06`: outbound ElevenLabs переведён на relay на отдельном сервере.
- `2026-04-07`: старт разговора переведен в режим `human-answer gate`, обновлены `turn_timeout`, `turn_eagerness`, `speculative_turn`, включены `skip_turn` и `voicemail_detection`.
