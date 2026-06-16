# Контрольная точка — 2026-06-16

## Тема

Второй lab-cycle: сравнение voice/TTS-подходов. Проверка `eleven_v3_conversational` против softened `eleven_flash_v2_5`.

## Ветка

- текущая рабочая Git-ветка:
  - `codex/eleven-naturalness-lab`

## Lab-ветка ElevenLabs

- `branch_id`:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`

## Сделано

- Снят pre-voice baseline snapshot:
  - version:
    - `agtvrsn_7001kv7x1ztdfpnth8rw6rjmjbnh`
  - baseline TTS:
    - `eleven_flash_v2_5`
    - `speed = 1.08`
    - `stability = 0.46`
    - `similarity_boost = 0.82`
- Сделан V3 voice-test patch:
  - version:
    - `agtvrsn_7501kv7xb334emqtt4rvz06wq4zm`
  - TTS:
    - `eleven_v3_conversational`
    - `expressive_mode = true`
    - `speed = 1.02`
    - `stability = 0.42`
    - `similarity_boost = 0.78`
- Проверочный звонок на V3:
  - `conv_0001kv7xbt11em1akwnvn60g1w52`
- Что подтвердилось:
  - модель реально переключилась на `eleven_v3_conversational`;
  - но в нашем контуре появился регресс:
    - pre-opener rescue;
    - ранний `no_answer`;
    - живой ответ пришёл уже после premature close.
- Практический вывод:
  - в текущем состоянии V3 нельзя считать лучшим lab-state.
- После этого выполнен recovery на Flash с более мягкими голосовыми параметрами:
  - version:
    - `agtvrsn_5001kv7xeea2ef7smebsma02kaek`
  - TTS:
    - `eleven_flash_v2_5`
    - `speed = 1.00`
    - `stability = 0.40`
    - `similarity_boost = 0.76`
- Проверочный звонок после recovery:
  - `conv_6701kv7xf23aevv9ehmw2w5ns2b5`
- По нему подтверждено:
  - логика не деградировала;
  - opener прошёл правильно;
  - confused follow-up и soft-refusal path сохранились;
  - voice-layer остался безопасным.

## Артефакты

- `.runtime/eleven_lab_voice_cycle_2026-06-16/`

## На чем остановились

- Лучшее текущее состояние lab после voice-cycle:
  - `agtvrsn_5001kv7xeea2ef7smebsma02kaek`
- V3 пока даёт интересную выразительность, но слишком дорогой поведенческий регресс для нашего контура.

## Что делать дальше

1. Продолжать улучшать голос поверх softened Flash, а не через слепой переход на V3.
2. Если когда-нибудь снова тестировать V3, то только после отдельного hardening против:
   - pre-opener rescue;
   - premature no_answer;
   - игнорирования позднего lexical reply.
3. Следующий self-test снова строить на коротких живых сценариях.
