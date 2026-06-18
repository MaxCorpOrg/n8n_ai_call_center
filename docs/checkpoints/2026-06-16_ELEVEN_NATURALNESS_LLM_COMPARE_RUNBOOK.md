# Контрольная точка — 2026-06-16

## Обновление 2026-06-17: tuned `GPT-5 Mini + Eleven v3 Conversational` стал текущим интересным lab-tip

## Фактический статус после tuning-cycle

- Сырая связка:
  - `GPT-5 Mini + Eleven v3 Conversational`
  - `conv_7301kva3kn56ep7b4esk2qqvcdd5`
  была слишком длинной и вязкой.
- После targeted tuning-patch выпущена версия:
  - `agtvrsn_3201kva3xjj1fxr959jzkymjk038`
  - self-test:
    - `conv_4101kva3y9agf5yrp04g78m87wk0`
- Подтверждено:
  - `duration: 159s -> 89s`
  - `tts_seconds: 94.0 -> 49.33`
  - early `call_log` до opener исчез
  - post-SMS close стал чистым:
    - `send_sms_info -> call_log -> spoken close -> end_call`
- Остаток:
  - agent всё ещё немного давит и не всегда даёт пользователю пространство;
  - rescue внутри разговора ещё встречается;
  - tool-call transcript всё ещё местами показывает placeholder-like `params_as_json`.

## Текущая рабочая точка lab

- Сейчас считать основным lab-кандидатом:
  - `agtvrsn_0301kva4xj1vers8ry3evaf4q0jp`
  - `llm = gpt-5-mini`
  - `tts.model_id = eleven_v3_conversational`
- Это возврат на лучшую tuned1-линию после того, как:
  - `tuned2`
  - `tuned3`
  - `tuned1b`
  не дали более качественного поведения в сумме.

## Обновление 2026-06-17: отдельные V3-комбинации тоже уже проверены

## Фактический статус после voice/LLM mix cycle

- `Gemini 2.5 Flash + Eleven v3 Conversational`:
  - `version_id = agtvrsn_5201kva3dwhyf0xrm8wjdz7xnykc`
  - `conv_2801kva3emkdf0p9dd2jk0s38agv`
  - вывод:
    - допустимый lab-вариант;
    - без явного сценарного развала;
    - но всё ещё медленнее и тяжелее по темпу, чем Flash-вершина.
- `GPT-5 Mini + Eleven v3 Conversational`:
  - `version_id = agtvrsn_9401kva3jyk3eyja2v0manq9r8mk`
  - `conv_7301kva3kn56ep7b4esk2qqvcdd5`
  - вывод:
    - регрессивный вариант;
    - слишком длинный разговор;
    - ранний `call_log`;
    - после SMS agent не завершил разговор коротко.
- После сравнения branch снова возвращён на:
  - `version_id = agtvrsn_0201kva3t7vyexzvv7prj3z7wbef`
  - `llm = gemini-2.5-flash`
  - `tts.model_id = eleven_flash_v2_5`

## Обновление 2026-06-17: цикл `GPT-5 Mini / GPT-5 Nano / GPT-5` уже пройден

## Фактический статус после нового OpenAI-cycle

- `GPT-5 Mini`:
  - `version_id = agtvrsn_0101kva2ts7ee57r5b86vqts64me`
  - `conv_4901kva2vhn5fx4s3gtxjj5vcptr`
  - вывод:
    - рабочий кандидат;
    - финализация нормальная;
    - но objection-turn всё ещё тяжёлый и pitch длинноват;
    - в transcript есть странность в `params_as_json` tool-call.
- `GPT-5 Nano`:
  - `version_id = agtvrsn_2401kva2zfqdegt8wam2nhyqx3k1`
  - `conv_8601kva308pbf8bvc7bd1pservfe`
  - вывод:
    - регрессивен;
    - повторяет opener;
    - для нашего phone sales-flow слишком слаб.
- `GPT-5`:
  - `version_id = agtvrsn_4901kva34bqhf8ybm1zcm04h6bbf`
  - `conv_6201kva352w6fe4ajzyntq6p46x3`
  - вывод:
    - уже держит сценарий;
    - clean `call_log -> end_call` есть;
    - но ответы длиннее нужного и модель дорогая.
- После сравнения branch снова возвращён на Gemini:
  - `version_id = agtvrsn_4401kva39np7e8hbze7anrs0565y`
  - `llm = gemini-2.5-flash`

## Текущая рабочая вершина после этого цикла

- Всё ещё считать текущим лучшим балансом:
  - `gemini-2.5-flash + eleven_flash_v2_5`
- `GPT-5 Mini` оставить как возможный следующий OpenAI-кандидат для отдельного prompt-trim цикла.

## Обновление 2026-06-17: отдельный `GPT-4o Mini` self-test уже снят

## Фактический статус после нового цикла

- От текущей лучшей Gemini-версии был собран отдельный payload со сменой только LLM:
  - `gpt-4o-mini`
- Кандидат опубликован как:
  - `version_id = agtvrsn_5201kva2hgb6ezxayw69t4qkzrpf`
- Реальный self-test:
  - `conv_1801kva2jcc7e9rtkcvj95jz1k63`
- Подтверждённые регрессии:
  - objection-turn тяжёлый:
    - `нет` в `11s`
    - ответ agent только в `15s`
  - смысловой фокус хуже, чем на Gemini:
    - agent уходит в объяснение, кто такие косметологи, вместо короткого product-flow
  - finalization сломалась:
    - `Поняла, спасибо. Хорошего дня.` прозвучало дважды
    - затем agent снова вернулся в разговор
- Поэтому `GPT-4o Mini` не стал новой вершиной lab.
- После этого branch сразу возвращён обратно на Gemini:
  - `version_id = agtvrsn_3901kva2qtdhe0ebbrgv2ck1gv5g`
  - `llm = gemini-2.5-flash`
  - `tts.model_id = eleven_flash_v2_5`

## Текущая рабочая вершина после rollback

- Считать актуальной lab-линией:
  - `gemini-2.5-flash + eleven_flash_v2_5`
- `GPT-4o Mini` на сейчас считать проверенным и регрессивным именно для телефонного sales-диалога.

## Тема

Практический runbook для следующего отдельного цикла сравнения LLM в `lab_naturalness_2026_06` без изменения live `Main`.

## Фактический статус после реального цикла

- Live `Main` не менялся.
- `scripts/run_eleven_branch_selftest.sh` доведён до рабочего состояния для реальных lab-звонков:
  - сохраняет раздельные артефакты по `webhook`, `relay`, `relay_via_server`;
  - не затирает полезный ответ пустым телом;
  - умеет реально уходить в `relay_via_server`, если local relay недоступен;
  - исправлен перенос payload на сервер через SSH.
- Подтверждено runtime-ограничение:
  - branch-targeted self-test идёт по текущей вершине branch;
  - если branch после публикации переехал, сравнение по старому `expected_version_id` уже нечестное.
- Реальные self-test результаты на 2026-06-16:
  - Claude:
    - `conv_8601kv8bgf72fdrtgq4ez8w30yd0`
    - `version_id = agtvrsn_8301kv8adscff0sb23dwjcmvcxb1`
    - плюс:
      - чистый opener без короткого обрубка;
    - минус:
      - после возражения `Нет, не интересно` LLM-пауза была около `2.84s`.
  - Gemini:
    - `conv_3901kv8bm93tfdas3dqtnykzcnh6`
    - `version_id = agtvrsn_5501kv8bkjkffjna37fq79vd5c7j`
    - плюс:
      - быстрее на objection-flow;
      - `Вы вообще с липолитиками работаете?` вышел примерно за `1.06s`;
    - минус:
      - на первом ходе словили opener-fragment:
        - `Здравствуйте,...`
  - Gemini без `interruption` в `client_events`:
    - `conv_7501kv8c555zetvbbxe74205zdwg`
    - `version_id = agtvrsn_9401kv8c4ebrec8b9xqxceqygqtk`
    - плюс:
      - opener прошёл чисто, без fragment;
    - минус:
      - objection-turn стал заметно тяжелее:
        - `Поняла. А вы вообще с липолитиками работаете?`
        - `LLM TTFB ≈ 2.25s`
      - final close тоже замедлился:
        - `LLM TTFB ≈ 2.63s`
  - Неудачный prompt-патч на opener:
    - `conv_0401kv8bsthdfyvt0d6bp0fjjfe9`
    - `version_id = agtvrsn_7301kv8bs45tfryst3c38jcpy0za`
    - результат:
      - стало хуже;
      - agent повторял opener несколько раз.
  - Неудачный turn-patch через `interruption_ignore_terms`:
    - `conv_3501kv8c9xkfffsb4kbm9ay4bf5m`
    - `version_id = agtvrsn_2201kv8c97stfsdrakry2k06ej7p`
    - результат:
      - agent вообще не дошёл до opener;
      - в transcript были только два пользовательских `Алло!`
  - Гипотеза `no-interruption + eager` пока не подтверждена answered-call:
    - один запуск:
      - `relay_upstream_failed`
    - второй запуск:
      - `conv_5501kv8cfgatf7dskfeh4v5j3nbq`
      - ушёл в polling timeout без ответа человека
  - `no-interruption + eager` теперь подтверждён answered self-test:
    - `conv_1901kva1cvmcf19rkxvk4xfcvh4g`
    - `version_id = agtvrsn_8901kva1a0pyexwan9hzkhmf832c`
    - плюс:
      - opener снова чистый, без fragment;
      - objection-turn стал быстрее, чем на `no-interruption + normal`:
        - `~2.25s -> ~1.98s`
      - value-turn со сценарием
        - `интересно -> пока не используем -> SMS`
        прошёл заметно живее:
        - `LLM TTFB ≈ 1.64s`
      - финальный post-SMS close тоже быстрый:
        - `LLM TTFB ≈ 0.48s`
    - остаток:
      - финальная spoken-фраза после SMS всё ещё может обрываться на хвосте:
        - `Хорошего дня...`
  - Усиленный `tool-only final close` patch поверх eager:
    - `conv_4301kva21wg8ets9xf29cbz0y0yf`
    - `version_id = agtvrsn_0901kva21515f08v6xn9w3v05zg3`
    - плюс:
      - refusal-close больше не произносится дважды;
      - теперь последовательность на финале стала:
        - silent `call_log`
        - один spoken close
        - `end_call`
    - что подтверждено:
      - пропал дублирующийся второй spoken-turn `Поняла, спасибо. Хорошего дня.` до и после `call_log`
    - остаток:
      - post-SMS close после этого общего patch-а ещё не подтверждён отдельным SMS self-test
- После этого lab-ветка возвращена на более здоровый Gemini-state:
  - текущая верхняя lab-version:
    - `agtvrsn_0901kva21515f08v6xn9w3v05zg3`
  - стек:
    - `llm = gemini-2.5-flash`
    - `tts.model_id = eleven_flash_v2_5`
    - `client_events` без `interruption`
    - `turn_eagerness = eager`

## Базовый контур

- Git-ветка:
  - `codex/eleven-naturalness-lab`
- ElevenLabs `agent_id`:
  - `agent_8801kgybyekned2a8yae6rp8hk3q`
- Lab `branch_id`:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- Текущий baseline source snapshot:
  - `.runtime/eleven_lab_flash_return_2026-06-16/response.json`
- Текущий baseline stack:
  - `llm = gpt-4.1`
  - `tts.model_id = eleven_flash_v2_5`
  - `voice_id = 0ArNnoIAWKlT4WweaVMY`

## Точные LLM identifiers

Использовать именно эти значения:

- baseline:
  - `gpt-4.1`
- Gemini-кандидат:
  - `gemini-2.5-flash`
- Claude-кандидат:
  - `claude-sonnet-4-5`

## Подготовленные локальные артефакты

- Helper для одиночного variant payload:
  - `scripts/prepare_eleven_llm_variant.sh`
- Helper для пары compare-variants:
  - `scripts/prepare_eleven_llm_compare_variants.sh`
- Helper для безопасного применения payload в lab-ветку:
  - `scripts/apply_eleven_agent_payload.sh`
- Helper для применения payload с автоматическим чтением ключа из серверного `.env.callcenter`:
  - `scripts/apply_eleven_agent_payload_via_server_env.sh`
- Helper для branch-targeted self-test end-to-end:
  - `scripts/run_eleven_branch_selftest.sh`
- Уже собранный Gemini payload:
  - `.runtime/eleven_lab_llm_compare_gemini_2026-06-16/payload.json`
- Уже собранный Claude payload:
  - `.runtime/eleven_lab_llm_compare_claude_2026-06-16/payload.json`

## Как собрать оба compare-payload

```bash
scripts/prepare_eleven_llm_compare_variants.sh \
  .runtime/eleven_lab_flash_return_2026-06-16/response.json \
  .runtime \
  2026-06-16
```

Ожидаемые файлы:

- `.runtime/eleven_lab_llm_compare_gemini_2026-06-16/payload.json`
- `.runtime/eleven_lab_llm_compare_claude_2026-06-16/payload.json`

## Как применять payload в lab-ветку

Официальный путь — `Update agent` с `branch_id`, не в live `Main`.

### Безопасный локальный helper

С защитой от случайного попадания в `Main` и без вывода секрета:

```bash
ELEVEN_ENV_FILE=/tmp/.env.callcenter \
scripts/apply_eleven_agent_payload.sh \
  .runtime/eleven_lab_llm_compare_gemini_2026-06-16/payload.json \
  .runtime/eleven_lab_llm_compare_gemini_2026-06-16/apply_result
```

Что делает helper:

- читает ключ из:
  - `ELEVENLABS_API_KEY`
  - или `ELEVEN_API_KEY`
  - или из файла `ELEVEN_ENV_FILE`
- по умолчанию целится в:
  - `agent_id = agent_8801kgybyekned2a8yae6rp8hk3q`
  - `branch_id = agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- запрещает apply в live `Main`, если явно не выставлен:
  - `ALLOW_MAIN_BRANCH_APPLY=1`
- сохраняет:
  - `request_info.json`
  - `response.json`
- если ElevenLabs вернул API-error:
  - печатает короткий `detail`
  - завершает команду с `exit 1`

### Helper с серверным `.env.callcenter`

Если локально нет ключа в env, но есть рабочий `ssh ai-core-prod-147`, можно применять так:

```bash
scripts/apply_eleven_agent_payload_via_server_env.sh \
  .runtime/eleven_lab_llm_compare_gemini_2026-06-16/payload.json \
  .runtime/eleven_lab_llm_compare_gemini_2026-06-16/apply_result
```

Что он делает:

- по SSH находит один из файлов:
  - `/home/aicore/n8n-server/.env.callcenter`
  - `/home/aicore/n8n-ai-clean/.env.callcenter`
- читает оттуда:
  - `ELEVENLABS_API_KEY`
  - или `ELEVEN_API_KEY`
- не печатает секрет в лог
- затем локально вызывает:
  - `scripts/apply_eleven_agent_payload.sh`

### Dry-run без ключа

```bash
scripts/apply_eleven_agent_payload.sh \
  .runtime/eleven_lab_llm_compare_gemini_2026-06-16/payload.json \
  .runtime/eleven_lab_llm_compare_gemini_2026-06-16/apply_result \
  --dry-run
```

## Как запускать branch-targeted self-test

```bash
scripts/run_eleven_branch_selftest.sh \
  .runtime/eleven_lab_llm_compare_gemini_2026-06-16/call_01_selftest \
  +79251130826 \
  gemini_call_01 \
  agtbrch_3701kv7waz0teny9xvsgv7sjt0bp \
  agtvrsn_3901kv89xcg3fnntrp2zwbjt0xcb
```

Dry-run без реального звонка:

```bash
scripts/run_eleven_branch_selftest.sh \
  .runtime/eleven_lab_llm_compare_gemini_2026-06-16/call_01_selftest \
  +79251130826 \
  gemini_call_01 \
  agtbrch_3701kv7waz0teny9xvsgv7sjt0bp \
  agtvrsn_3901kv89xcg3fnntrp2zwbjt0xcb \
  --dry-run
```

Что делает helper:

- собирает `request.json`
- сначала пытается вызвать:
  - `POST https://www.n-8-n.site/webhook/eleven/outbound-call`
- если этот webhook отвечает `404 Active version not found`, автоматически уходит в direct relay:
  - `POST http://151.241.228.232:8787/eleven/outbound-call`
  - c заголовком `X-Relay-Token`
- сохраняет:
  - `outbound_response.json`
  - `conversation_id.txt`
  - `transport.txt`
- затем через Eleven API поллит:
  - `GET /v1/convai/conversations/{conversation_id}`
- сохраняет:
  - `conversation_poll_*.json`
  - `conversation_poll_final.json`
- в конце печатает краткую сводку:
  - `conversation_id`
  - `status`
  - `branch_id`
  - `version_id`
  - совпадает ли `version_id` с ожидаемым

### Ручной curl-шаблон

Если нужен ручной путь:

```bash
curl -X PATCH "https://api.elevenlabs.io/v1/convai/agents/agent_8801kgybyekned2a8yae6rp8hk3q?branch_id=agtbrch_3701kv7waz0teny9xvsgv7sjt0bp" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  --data @.runtime/eleven_lab_llm_compare_gemini_2026-06-16/payload.json
```

После ответа сохранить:

- `response.json`
- `version_id`
- фактический `llm`
- фактический `tts.model_id`

## Единый сценарий self-test

На каждом LLM гонять один и тот же сценарий:

1. `Алло!`
2. `Что это?`
3. `Да, интересно`
4. `Нет, пока не используем`
5. попросить объяснить подробнее
6. согласиться на SMS

## Что фиксировать

- `convai_llm_service_ttfb`
- чувствуется ли задержка до первого осмысленного ответа
- перебивает ли пользователя
- ломается ли ветка:
  - `интересно -> пока не используем`
- удерживает ли краткость и естественность
- не вылезают ли fragments:
  - `...`
  - `Я уже...`
- чисто ли проходят:
  - `send_sms_info`
  - `call_log`
  - финальный close

## Сделано

- Текущий baseline зафиксирован:
  - `gpt-4.1 + eleven_flash_v2_5`
- Подготовлен helper для одиночной смены LLM:
  - `scripts/prepare_eleven_llm_variant.sh`
- Подготовлен helper для compare-cycle:
  - `scripts/prepare_eleven_llm_compare_variants.sh`
- Подготовлен helper для безопасного PATCH в lab branch:
  - `scripts/apply_eleven_agent_payload.sh`
- Подготовлен helper для apply через SSH-доступ к серверному env:
  - `scripts/apply_eleven_agent_payload_via_server_env.sh`
- Подготовлен helper для branch-targeted self-test:
  - `scripts/run_eleven_branch_selftest.sh`
- Оба compare-payload уже локально собраны и проверены:
  - Gemini:
    - `llm = gemini-2.5-flash`
    - `tts.model_id = eleven_flash_v2_5`
  - Claude:
    - `llm = claude-sonnet-4-5`
    - `tts.model_id = eleven_flash_v2_5`
- Gemini-вариант уже реально опубликован в lab branch:
  - `version_id = agtvrsn_3901kv89xcg3fnntrp2zwbjt0xcb`
  - `llm = gemini-2.5-flash`
  - `tts.model_id = eleven_flash_v2_5`
- Claude-вариант тоже уже реально опубликован в lab branch:
  - `version_id = agtvrsn_8301kv8adscff0sb23dwjcmvcxb1`
  - `llm = claude-sonnet-4-5`
  - `tts.model_id = eleven_flash_v2_5`
- До этого был пойман и закрыт реальный payload-дефект:
  - ElevenLabs отклонял payload с ошибкой:
    - `Cannot specify both tools and tool IDs`
  - причина:
    - snapshot содержал одновременно `prompt.tool_ids` и `prompt.tools`
  - после этого `scripts/prepare_eleven_llm_variant.sh` стал автоматически удалять:
    - `conversation_config.agent.prompt.tools`
  - а `scripts/apply_eleven_agent_payload.sh` теперь честно падает на API-error, а не делает вид, что publish прошёл.
- Это поведение отдельно проверено negative test-ом:
  - заведомо битый payload с `tools + tool_ids`
  - результат:
    - `exit 1`
    - ошибка сохранена в:
      - `.runtime/eleven_lab_bad_payload_test_2026-06-16/apply_result/response.json`
- Артефакты публикации:
  - `.runtime/eleven_lab_llm_compare_gemini_2026-06-16/server_apply_result_v2/request_info.json`
  - `.runtime/eleven_lab_llm_compare_gemini_2026-06-16/server_apply_result_v2/response.json`
  - `.runtime/eleven_lab_llm_compare_claude_2026-06-16/server_apply_result/request_info.json`
  - `.runtime/eleven_lab_llm_compare_claude_2026-06-16/server_apply_result/response.json`

## На чем остановились

- Gemini и Claude уже не просто опубликованы, а проверены живыми self-test.
- Практический вывод на сейчас:
  - `Claude` мягче стартует, но ощутимо медленнее на objection-turn;
  - baseline `Gemini` заметно быстрее на objection-flow, но режет opener на overlap;
  - `Gemini` без interruptions даёт самый чистый opener из реально подтверждённых Gemini-вариантов;
  - `Gemini + no-interruption + eager` сейчас даёт лучший подтверждённый баланс:
    - чистый opener;
    - заметно более живой objection-flow;
    - рабочий SMS-path.
- Поверх этого уже подтверждено ещё одно улучшение:
  - `tool-only final close` убирает дубль spoken-close на refusal path.
- Последний prompt-патч под opener оказался регрессивным и уже откатан.
- `hello-ignore` эксперимент тоже признан неудачным.
- Текущая безопасная верхняя lab-точка:
  - `agtvrsn_0901kva21515f08v6xn9w3v05zg3`

## Что делать дальше

1. Не крутить prompt на opener вслепую ещё раз.
2. Держать lab-ветку на:
   - `agtvrsn_0901kva21515f08v6xn9w3v05zg3`
   как на лучшей подтверждённой Gemini-точке.
3. Следующий малый шаг теперь уже точечный SMS self-test:
   - подтвердить, что после общего `tool-only final close` post-SMS ветка тоже больше не даёт:
     - `Хорошего дня...`
     - и не дублирует spoken-close
4. Для следующего сравнения мерить минимум:
   - opener fragment / no fragment;
   - `convai_llm_service_ttfb` на отказе;
   - поведение после `Нет, не интересно`;
   - чистоту post-SMS финального close;
   - стабильность `call_log`.
