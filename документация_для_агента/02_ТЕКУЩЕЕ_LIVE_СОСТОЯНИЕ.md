# Текущее live-состояние

## 1. Боевой контур

Сейчас боевой маршрут такой:
- `Mango -> Asterisk -> ElevenLabs -> n8n`

Что реально задействовано:
- Mango как телефония;
- Asterisk как SIP bridge;
- ElevenLabs как голосовой агент;
- n8n как webhook/tools/логика интеграции;
- `postgres_memory` как memory-слой;
- Google Sheet как лог звонков через `call_log`.

## 2. Что работает сейчас

Работает:
- live звонковый контур;
- `context_fetch`;
- `call_log`;
- PostgreSQL memory stack;
- knowledge chunks и script steps в памяти;
- логирование результатов разговора.

## 3. Что не считать главным боевым контуром

Подготовлено, но не является основой текущего live-маршрута:
- отдельный callcenter Postgres-контур с `call_tasks/call_events` как обязательная часть боевой схемы;
- любые локальные draft-артефакты, не подтвержденные в live.

## 4. Текущий live-агент ElevenLabs

- Agent name: `AI_CALL_AGENT_1`
- Agent ID: `agent_8801kgybyekned2a8yae6rp8hk3q`
- Branch ID: `agtbrch_7801kgybyg9nesrbv64y078pazq0`

Текущая конфигурация:
- `LLM = gpt-4.1`
- `TTS = eleven_flash_v2_5`
- `voice = Elena Gromova`
- `voice_id = 0ArNnoIAWKlT4WweaVMY`
- `speed = 1.16`
- `stability = 0.5`
- `similarity_boost = 0.78`
- `turn_eagerness = eager`
- `turn_timeout = 3.0`
- `disable_first_message_interruptions = true`
- `speculative_turn = true`
- active tools: `context_fetch`, `call_log`, `send_sms_info`, `end_call`
- `tool_ids`:
  - `tool_1601km62rxpqegqr52m9gk9sftr3`
  - `tool_0901km62rxpre578kd1zvd7q7g04`
  - `tool_1701km86jmcpek4rj2j1rbhxqtfr`

Дополнительно подключено:
- pronunciation dictionary: `NnZrxd6lJkbHKqW6w04N`
- version id: `8lEt5avz1g7b4oYD9yUn`
- базовая нормализация бренда: `ЛипоЛонг / LipoLong / lipolong -> липолонг`

## 5. Важное бизнес-ограничение

`first_message` нельзя менять без отдельного решения пользователя.

Это обязательная фраза для старта звонка.

## 6. Что зафиксировано по поведению агента

- агент стал живее после перехода на Flash-модель;
- основная проблема в начале разговора была связана с длинной стартовой фразой и задержкой первого содержательного ответа;
- прерывания стартовой фразы отключены, чтобы агент договаривал обязательную вводную до конца;
- follow-up переведен на сценарий без почты: агент должен собирать имя, номер и удобный канал связи;
- `call_log` и `context_fetch` были восстановлены через валидные `tool_ids` после очистки битых tool-ссылок;
- словарь произношения собран по живым звонкам и текущему prompt, чтобы выровнять бренд `липолонг` и частые термины;
- остаточная задержка может появляться на нечетких репликах клиента и в LLM-ходе, а не только в TTS.
