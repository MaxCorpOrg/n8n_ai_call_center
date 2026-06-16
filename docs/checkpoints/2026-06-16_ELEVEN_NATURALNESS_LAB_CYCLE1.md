# Контрольная точка — 2026-06-16

## Тема

Первый рабочий цикл отдельного naturalness-lab контура: baseline -> turn-taking patch -> prompt naturalness patch -> повторные self-tests.

## Ветка

- текущая рабочая Git-ветка:
  - `codex/eleven-naturalness-lab`

## Lab-ветка ElevenLabs

- name:
  - `lab_naturalness_2026_06`
- `branch_id`:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- текущая версия после цикла:
  - `agtvrsn_7001kv7x1ztdfpnth8rw6rjmjbnh`

## Сделано

- Снят baseline manual self-test на отдельной lab-ветке:
  - `conv_1201kv7wpw78e53s5mgkc8rcwpa6`
  - version:
    - `agtvrsn_0401kv7waz0sfae92b77pgjhmcqf`
- Baseline зафиксировал:
  - turn profile:
    - `turn_timeout = 1.75`
    - `turn_eagerness = normal`
    - `speculative_turn = false`
    - `retranscribe_on_turn_timeout = true`
  - слишком медленные ответы на средних ходах;
  - слишком скриптовый и длинный второй/третий ход.
- После baseline внесён отдельный turn-taking patch:
  - version:
    - `agtvrsn_6801kv7ww8dnf1qsx2ah0qxab6rs`
  - изменения:
    - `turn_timeout: 1.75 -> 1.25`
    - `turn_eagerness: normal -> eager`
    - `speculative_turn: false -> true`
    - `retranscribe_on_turn_timeout: true -> false`
- Проверочный звонок после turn-патча:
  - `conv_7701kv7wwz1yesgvhynmn6b5tpb2`
- По нему подтверждено:
  - opener по wall-clock заметно не ускорился;
  - но последующие ответы agent стали приходить быстрее;
  - длинный scripted value-block всё ещё оставался и местами перебивался человеком.
- После этого внесён отдельный prompt naturalness patch:
  - version:
    - `agtvrsn_7001kv7x1ztdfpnth8rw6rjmjbnh`
  - добавлен `Lab naturalness priority override`
  - смысл правки:
    - меньше формального filler;
    - меньше stacked option-questions;
    - один move на ход;
    - короче и человечнее phrasing.
- Проверочный звонок после naturalness-патча:
  - `conv_7701kv7x2m70f5fata09r7rcx6et`
- По нему подтверждено:
  - exact opener не сломался;
  - второй ход стал короче и более разговорным;
  - not-target case закрывается чище;
  - `call_log` проходит нормально.

## Артефакты

- baseline и тестовые звонки:
  - `.runtime/eleven_lab_baseline_2026-06-16/`
- turn patch:
  - `.runtime/eleven_lab_turn_patch_2026-06-16/`

## На чем остановились

- Turn-taking в lab уже стал лучше на средних ходах.
- Prompt naturalness тоже стал лучше, но голос и интонационная подача пока ещё остались прежними.
- Следующий главный фронт теперь уже не ещё один prompt-overload, а voice/TTS layer.

## Что делать дальше

1. Сделать следующий isolated cycle только по voice/TTS.
2. Сравнить:
   - `eleven_flash_v2_5`
   - и `eleven_v3_conversational`
3. Для voice-cycle проверить:
   - naturalness интонации;
   - ударения;
   - не звучит ли голос как “читает заготовку”;
   - не ломается ли fast response.
4. После voice-cycle снова сделать manual self-test на той же lab-ветке.
