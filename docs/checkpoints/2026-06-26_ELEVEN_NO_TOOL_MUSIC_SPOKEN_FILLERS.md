# 2026-06-26: ElevenLabs без tool-music, с короткими spoken fillers

## Сделано
- Подтверждён источник "музыки" в текущем published lab-head:
  - `.conversation_config.tts.background_sound = null`
  - значит это не фоновая музыка TTS.
- Подтверждено, что музыка шла именно из webhook-инструментов:
  - `context_fetch.tool_call_sound = elevator3`
  - `call_log.tool_call_sound = elevator3`
  - `send_sms_info.tool_call_sound = elevator3`
  - `tool_call_sound_behavior = always`
- Подтверждено, что spoken fill layer был фактически выключен:
  - `soft_timeout_config.message = "Так..."`
  - `use_llm_generated_message = false`
- Добавлен новый узкий helper:
  - [scripts/prepare_eleven_no_tool_music_softfill_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_no_tool_music_softfill_variant.sh:1)
- Его задача:
  - убрать музыкальную маскировку на webhook-tools;
  - включить короткий словесный filler вместо этого;
  - не трогать opener, machine-stop, voice stack и остальную wiring-часть.
- Через него опубликована новая branch-version:
  - `agtvrsn_6201kw1jmfrdejz8e0gk5b8x7xn5`
- В ней подтверждено:
  - `llm = gpt-5-mini`
  - `tts = eleven_v3_conversational`
  - `turn_timeout = 1.78`
  - `soft_timeout_seconds = 2.4`
  - fallback filler теперь `Да...`
  - `use_llm_generated_message = true`
- Дополнительно расширен existing helper:
  - [scripts/patch_eleven_tool_call_sounds_via_server_env.sh](/home/max/n8n_ai_call_center/scripts/patch_eleven_tool_call_sounds_via_server_env.sh:1)
  - теперь он умеет:
    - `TOOL_CALL_SOUND=null`
    - и реально пишет JSON `null`, а не строку `"null"`.
- После этого direct tool patch применён к shared tools:
  - `tool_1601km62rxpqegqr52m9gk9sftr3` (`context_fetch`)
  - `tool_5701ktec2x6wfnj8t5b1rwhtw51p` (`call_log`)
  - `tool_1701km86jmcpek4rj2j1rbhxqtfr` (`send_sms_info`)
- Direct tool backup/after-summary лежит в:
  - [.runtime/eleven_tool_sound_disable_2026-06-26/summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_tool_sound_disable_2026-06-26/summary.json:1)
- Этот summary подтверждает:
  - `before = elevator3 / always`
  - `after = null / auto`

## На чем остановились
- Причина уже не спорная: музыка шла из tool-layer.
- Spoken filler уже включён, shared tools уже пропатчены.
- Остался не engineering-поиск, а functional check:
  - убедиться одним коротким self-test, что в реальном звонке больше нет `elevator3`,
  - и что filler звучит словами, а не музыкой.
- Важная техническая тонкость:
  - branch snapshot агента после direct tool patch всё ещё может сериализовать старый embedded `elevator3`;
  - для этого слоя источником истины теперь считать direct tool backup/after-files, а не только agent snapshot.

## Что делать дальше
1. Сделать один короткий self-test.
2. Во время теста смотреть:
  - нет ли больше `elevator3`;
  - не стало ли filler слишком ранним;
  - не полезли ли filler-фразы до opener.
3. Если filler всё ещё будет звучать неестественно:
  - менять уже не tool-layer, а только:
    - `soft_timeout_seconds`
    - prompt override для filler-лексики.
