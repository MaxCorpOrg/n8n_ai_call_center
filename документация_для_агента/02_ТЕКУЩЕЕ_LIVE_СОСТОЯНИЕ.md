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
- `LLM = gemini-2.5-flash`
- `TTS = eleven_flash_v2_5`
- `speed = 1.2`
- `turn_eagerness = eager`
- `turn_timeout = 4.0`
- `disable_first_message_interruptions = true`
- в `client_events` удалено `interruption`

## 5. Важное бизнес-ограничение

`first_message` нельзя менять без отдельного решения пользователя.

Это обязательная фраза для старта звонка.

## 6. Что зафиксировано по поведению агента

- агент стал живее после перехода на Flash-модель;
- основная проблема в начале разговора была связана с длинной стартовой фразой и ранними перебиваниями клиента;
- прерывания реплик отключены, чтобы агент договаривал мысль до конца;
- остаточная задержка может появляться на нечетких репликах клиента и в turn-taking, а не только в TTS.
