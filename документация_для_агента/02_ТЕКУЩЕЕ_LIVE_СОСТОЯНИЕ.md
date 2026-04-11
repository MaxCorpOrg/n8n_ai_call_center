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
- `call_center` Postgres как operational data layer;
- `postgrest` и `adminer` как часть текущего серверного контура;
- Google Sheet как лог звонков через `call_log`.

## 2. Что работает сейчас

Работает:
- live звонковый контур;
- `context_fetch`;
- `call_log`;
- `send_sms_info`;
- PostgreSQL memory stack;
- `call_center` Postgres;
- `postgrest`;
- `adminer`;
- knowledge chunks и script steps в памяти;
- логирование результатов разговора.

## 3. Что не считать главным боевым контуром

Не считать основой текущего боевого маршрута:
- локальные untracked backup/runtime-артефакты в `/home/max/n8n_ai_call_center`;
- любые draft-файлы, не подтвержденные на live-сервере или в live n8n.

## 4. Текущий live-агент ElevenLabs

- Agent name: `AI_CALL_AGENT_1`
- Agent ID: `agent_8801kgybyekned2a8yae6rp8hk3q`
- Branch ID: `agtbrch_7801kgybyg9nesrbv64y078pazq0`

Текущая конфигурация:
- `LLM = gpt-4.1`
- `system prompt language = en`
- `spoken client language = ru`
- `TTS = eleven_flash_v2_5`
- `voice = Elena Gromova`
- `voice_id = 0ArNnoIAWKlT4WweaVMY`
- `speed = 1.16`
- `stability = 0.5`
- `similarity_boost = 0.78`
- `turn_eagerness = normal`
- `turn_timeout = 15.0`
- `speculative_turn = false`
- built-in tools: `end_call`, `skip_turn`, `voicemail_detection`
- active tools: `context_fetch`, `call_log`, `send_sms_info`, `end_call`
- `tool_ids`:
  - `tool_1601km62rxpqegqr52m9gk9sftr3`
  - `tool_0901km62rxpre578kd1zvd7q7g04`
  - `tool_1701km86jmcpek4rj2j1rbhxqtfr`

Дополнительно подключено:
- pronunciation dictionary: `NnZrxd6lJkbHKqW6w04N`
- version id: `8SrjbTKmOZjOnHxLQrxE`
- базовая нормализация бренда: `ЛипоЛонг / LipoLong / lipolong -> липолонг`

## 5. Текущий старт разговора

Сейчас live-agent работает через `human-answer gate`:
- `first_message = ""`
- до живого ответа человека pitch не начинается;
- первая живая реплика агента: `Здравствуйте.`
- после ещё одного короткого человеческого ответа агент переходит к business-opener.

Текущий business-opener:
- `Наша компания является официальным представителем липолитика lipolong и предлагает сотрудничество на выгодных условиях. Вам это в принципе интересно?`

## 6. Что зафиксировано по поведению агента

- агент стал живее после перехода на Flash-модель;
- основная проблема теперь смещена в качество самого opener и дальнейшего pitch, а не в мгновенный автозапуск;
- автоответчики и IVR обрабатываются лучше за счёт `skip_turn`, `voicemail_detection` и ожидания живого ответа;
- consent/recording-фразы вида `Продолжая разговор, вы соглашаетесь на запись данного звонка...` должны трактоваться как машинный пролог, а не как человек;
- фразы `абонент сейчас не может ответить / телефон занят / недоступен` должны завершаться без ответной речи, с логикой `busy/no_answer + callback`;
- message-service должен получать только короткий callback-месседж с номером менеджера, без qualification и sales-pitch;
- follow-up переведен на сценарий без почты: агент должен собирать имя, номер и удобный канал связи;
- `call_log` и `context_fetch` были восстановлены через валидные `tool_ids` после очистки битых tool-ссылок;
- словарь произношения собран по живым звонкам и текущему prompt, чтобы выровнять бренд `липолонг` и частые термины;
- live system prompt переведен на английский, но сам агент продолжает говорить с клиентом только по-русски;
- остаточная задержка может появляться на нечетких репликах клиента и в LLM-ходе, а не только в TTS;
- главный текущий фронт улучшения: логика звонка после открытия, value reveal, дожим после возражений, работа с автоответчиками и полурелевантными ответами;
- в prompt запрещены реплики `Здравствуйте. Чем могу быть полезна?`, `Я вас слушаю`, `Вы на связи?` и повтор машинной фразы про недоступного абонента.
