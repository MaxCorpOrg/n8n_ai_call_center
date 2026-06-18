# Контрольная точка — 2026-06-17

## Обновление 2026-06-17: отдельный цикл по system-binding для `conversation_id` и `context_fetch`

### Сделано

- Добавлен новый helper:
  - [scripts/prepare_eleven_system_binding_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_system_binding_variant.sh:1)
- Его задача:
  - не менять voice / LLM / turn-taking;
  - не трогать live `Main`;
  - только поправить lab-only binding служебных полей:
    - `context_fetch.session_id -> system__conversation_id`
    - `send_sms_info.conversation_id -> system__conversation_id`
  - и добавить узкий prompt-override:
    - не выдумывать `conv_*`;
    - не запускать `context_fetch` до opener ради общего `initial call context`.

### Что проверили

#### Цикл v1

- Выпущена версия:
  - `agtvrsn_1101kvabn43mfeztaavzxwcbtxyn`
- Контрольный self-test:
  - `conv_3001kvabnww3f878kczd95zcndkz`
- Что подтвердилось:
  - `context_fetch_before_opener` из аудита ушёл;
  - ранний generic `context_fetch` больше не всплыл;
  - actual webhook body для `call_log` продолжил получать правильный live `conv_*`.
- Что не ушло:
  - в draft `call_log.params_as_json` модель всё ещё пыталась писать:
    - `conv_abcdef1234567890`
  - при этом фактический `tool_details.body` уже шёл с правильным:
    - `conv_3001kvabnww3f878kczd95zcndkz`
- Остаточные issues в audit:
  - `duplicate_close_before_end_call`
  - `placeholder_conversation_id_in_tool_call`

#### Цикл v2

- Выпущена более жёсткая версия:
  - `agtvrsn_7501kvabt8d8ewcrmxmnrcrmtn42`
- Контрольный self-test:
  - `conv_6901kvabtxcrezm8y19zcyctde1f`
- Что улучшилось:
  - issue `placeholder_conversation_id_in_tool_call` из аудита исчез;
  - `context_fetch` в этом тесте тоже не всплыл.
- Что сломалось:
  - разговорная логика заметно деградировала;
  - вернулись spoken stage tags:
    - `[calm]`
  - появились повторные поздние line-check:
    - `Алло?`
  - разговор стал путаться и уходить в регрессивный петляющий сценарий.
- Поэтому `v2` отклонена как регрессивная.

### На чем остановились

- Lab-ветка не оставлена на неудачной `v2`.
- После отката текущий branch-head теперь:
  - `agtvrsn_0101kvac144tfsb88f32crqgbmvq`
- По смыслу это возврат к более безопасной линии уровня `v1`:
  - ранний `context_fetch` уже прибит;
  - жёсткая регрессия `v2` убрана.
- При этом важно:
  - лучший naturalness-winner всего lab-контура всё ещё не этот binding-fix цикл,
    а ранее подтверждённая softfill-линия:
    - `agtvrsn_1201kvaavm18fe8b4sgw5vxt7tqy`
    - лучший звонок:
      - `conv_0501kva6snynemktpje537318ep5`

### Что делать дальше

1. Не возвращаться на `agtvrsn_7501kvabt8d8ewcrmxmnrcrmtn42`.
2. Если нужен следующий цикл по placeholder `conv_*`, делать его уже не широким prompt-переписыванием.
3. Следующий узкий фронт:
   - либо искать schema-level способ, при котором `call_log` draft вообще не печатает эти поля руками;
   - либо изолировать эту проблему отдельно от разговорной naturalness-логики;
   - не смешивать больше technical binding-fix и разговорный flow в одном резком патче.
