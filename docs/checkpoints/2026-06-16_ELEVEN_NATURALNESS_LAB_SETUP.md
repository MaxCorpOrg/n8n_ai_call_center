# Контрольная точка — 2026-06-16

## Тема

Создан отдельный безопасный контур для настройки naturalness и “живого” общения ElevenLabs без риска для боевого агента.

## Ветка

- текущая рабочая Git-ветка:
  - `codex/eleven-naturalness-lab`
- source branch, от которой она создана:
  - `codex/email-followup-agent-live`

## Live-агент

- `agent_id`: `agent_8801kgybyekned2a8yae6rp8hk3q`
- live `Main branch_id`:
  - `agtbrch_7801kgybyg9nesrbv64y078pazq0`
- текущая подтверждённая live version:
  - `agtvrsn_9001kv0k051efpr84vwwttz6kthj`

## Lab-ветка ElevenLabs

- name:
  - `lab_naturalness_2026_06`
- `branch_id`:
  - `agtbrch_3701kv7waz0teny9xvsgv7sjt0bp`
- первая version в этой ветке:
  - `agtvrsn_0401kv7waz0sfae92b77pgjhmcqf`
- parent branch:
  - `agtbrch_7801kgybyg9nesrbv64y078pazq0`
- live traffic:
  - `0%`

## Сделано

- От текущей рабочей ветки создан отдельный Git-контур:
  - `codex/eleven-naturalness-lab`
- От текущей live-версии в ElevenLabs создан отдельный агентный branch:
  - `lab_naturalness_2026_06`
- Подтверждено разделение контуров:
  - live `Main` остаётся на `100%` трафика;
  - lab-ветка остаётся на `0%`;
  - никаких product-experiments в боевую ветку этим шагом не вносилось.
- Снят baseline voice/turn state, с которого стартует lab:
  - `tts.model_id = eleven_flash_v2_5`
  - `voice_id = 0ArNnoIAWKlT4WweaVMY`
  - `expressive_mode = false`
  - `speed = 1.08`
  - `stability = 0.46`
  - `similarity_boost = 0.82`
  - `optimize_streaming_latency = 2`
  - `turn_timeout = 1.75`
  - `turn_eagerness = normal`
  - `turn_model = turn_v2`
- Сохранены артефакты создания и baseline-снимки:
  - `.runtime/eleven_lab_setup_2026-06-16/current_agent.json`
  - `.runtime/eleven_lab_setup_2026-06-16/branches_before.json`
  - `.runtime/eleven_lab_setup_2026-06-16/branch_create_response.json`
  - `.runtime/eleven_lab_setup_2026-06-16/branches_after.json`
  - `.runtime/eleven_lab_setup_2026-06-16/lab_agent_branch_snapshot.json`

## На чем остановились

- Lab-контур уже создан, но это пока только инфраструктурная точка старта.
- Никакие voice/TTS/turn-taking/prompt naturalness-изменения в `lab_naturalness_2026_06` ещё не применялись.
- Значит следующий шаг должен быть не “улучшать вслепую”, а сначала снять baseline manual self-tests на отдельной lab-ветке.

## Что делать дальше

1. Сделать baseline manual self-tests именно на `lab_naturalness_2026_06`:
   - `Алло!`
   - `Ну а? / Чего? / Что это?`
   - `Нет / Неактуально / Не надо`
   - тишина после opener
   - `абонент / voicemail / screening-service`
2. Зафиксировать baseline:
   - пауза до первого ответа;
   - перебивания;
   - premature hangup;
   - machine-detection;
   - naturalness голоса и ударений.
3. После baseline применять только один класс правок за цикл:
   - либо `voice/TTS`;
   - либо `turn-taking`;
   - либо `prompt naturalness`.
4. Первый безопасный naturalness-эксперимент подготовить как сравнение:
   - текущий `eleven_flash_v2_5`
   - против `eleven_v3_conversational`
   без изменения live `Main`.
5. Tiny canary на реальных лидах разрешать только после self-tests без регрессий по:
   - exact opener;
   - `абонент`/machine hard-stop;
   - one-rescue rule;
   - premature hangup.
