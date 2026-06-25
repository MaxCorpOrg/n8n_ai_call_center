# 2026-06-13: разбор плохого тестового звонка и откат TTS с silent-fix

## Что случилось

- Был запущен ручной исходящий тест на номер:
  - `+79251130826`
- Conversation:
  - `conv_7101kv0dzef5fp7sw6vff092xza7`
- По факту звонок показал два дефекта:
  1. новый voice-profile на `eleven_multilingual_v2` дал неудачное субъективное качество речи;
  2. после тишины агент произнёс лишнюю сервисную фразу:
     - `Могу ли я помочь вам ещё чем-то?`

## Что подтвердил transcript

- Прямой transcript показал:
  - pre-opener rescue всё ещё вылез:
    - `Алло, меня слышно? Вы тут?`
  - после opener пользователь не дал осмысленного ответа;
  - агент вызвал `call_log`;
  - `call_log` снова упал в `404`:
    - `Active version not found for workflow with id "kZSdJrsAHWWIC2l6"`
  - затем агент сказал запрещённую сервисную фразу и сам завершил звонок.

## Что исправлено

- Live TTS откатан с:
  - `eleven_multilingual_v2`
  обратно на:
  - `eleven_flash_v2_5`
- Новый рабочий TTS-профиль:
  - `optimize_streaming_latency = 2`
  - `stability = 0.46`
  - `speed = 1.08`
  - `similarity_boost = 0.82`
- В live prompt добавлен жёсткий запрет:
  - никогда не говорить
    - `Могу ли я помочь вам ещё чем-то?`
  - и вообще не произносить spoken-tail в ветках:
    - `no_answer`
    - silence-after-opener
    - failed-dialogue
- Новая live version:
  - `agtvrsn_0401kv0e8v2ffad82f2r1pje6ef5`

## Где лежит backup

- `backups/2026-06-13_voice_revert_and_silent_noanswer_fix/`

## На чем остановились

- Голосовой тюнинг `multilingual_v2` признан неудачным для этого кейса и уже снят.
- Spoken-farewell в no-answer ветке запрещён в live.
- Но отдельно остаются техдолги:
  - pre-opener rescue ещё надо добить;
  - `call_log` bridge `kZSdJrsAHWWIC2l6` всё ещё не имеет active version.

## Что делать дальше

1. Сделать ещё один короткий тестовый звонок.
2. Проверить:
   - ушла ли плохая подача голоса;
   - исчезла ли фраза `Могу ли я помочь вам ещё чем-то?`
3. Затем уже отдельно чинить:
   - `call_log` bridge `404`
   - pre-opener rescue.
