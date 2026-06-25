# Контрольная точка — 2026-06-18 — Eleven Control Tower

## Сделано

- Для Eleven-контура собран единый инженерный entrypoint:
  - [scripts/refresh_eleven_control_tower.sh](/home/max/n8n_ai_call_center/scripts/refresh_eleven_control_tower.sh:1)
- Он уже реально прогонялся на состоянии `2026-06-18` и обновляет за один запуск:
  1. current snapshot;
  2. quota preflight;
  3. live readiness;
  4. docs alignment;
  5. `interruptible_balanced`;
  6. `interruptible_softfill`;
  7. `variant_checks`;
  8. post-quota pack;
  9. operational brief.
- Для короткого чтения без ручной археологии теперь есть:
  - [.runtime/eleven_control_tower_latest/operational_brief.md](/home/max/n8n_ai_call_center/.runtime/eleven_control_tower_latest/operational_brief.md:1)
- Для быстрого выбора следующего candidate по complaint/audit теперь есть:
  - [.runtime/eleven_control_tower_latest/next_variant_advisor.md](/home/max/n8n_ai_call_center/.runtime/eleven_control_tower_latest/next_variant_advisor.md:1)
  - это baseline-версия без конкретного audit-входа
  - а в pack лежит helper:
    - `recommend_next_variant.sh`
  - он понимает:
    - `finalization_audit.json`
    - run-dir с `finalization_audit.json`
    - или просто freeform complaint text
- И теперь сам `run_eleven_selftest_audit.sh` после аудита автоматически пишет:
  - `next_variant_advice.json`
  - `next_variant_advice.md`
  в ту же run-папку
- Если в advice видно:
  - `ready_for_variant_testing = false`
  значит следующий ход:
  - не variant switch;
  - а fix-before-variant шаг из `action_plan`
- Добавлен стабильный `latest`-слой поверх dated-артефактов:
  - [.runtime/eleven_control_tower_latest/README.txt](/home/max/n8n_ai_call_center/.runtime/eleven_control_tower_latest/README.txt:1)
  - [.runtime/eleven_control_tower_latest/pack/manifest.json](/home/max/n8n_ai_call_center/.runtime/eleven_control_tower_latest/pack/manifest.json:1)
- Для машинной проверки вариантов внутри pack уже есть:
  - [.runtime/eleven_post_quota_test_pack_2026-06-18/validate_variants.sh](/home/max/n8n_ai_call_center/.runtime/eleven_post_quota_test_pack_2026-06-18/validate_variants.sh:1)

## На чем остановились

- Live звонки сейчас блокируются не route-ошибкой, а:
  - `quota_blocker_active`
- Это подтверждено свежими артефактами:
  - [.runtime/eleven_quota_preflight_2026-06-18_check_now/eleven_quota_preflight_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_quota_preflight_2026-06-18_check_now/eleven_quota_preflight_summary.json:1)
  - [.runtime/eleven_live_readiness_2026-06-18_check_now/live_readiness_summary.json](/home/max/n8n_ai_call_center/.runtime/eleven_live_readiness_2026-06-18_check_now/live_readiness_summary.json:1)
- Current published state:
  - `version_id = agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
  - `llm = gpt-5-mini`
  - `tts = eleven_v3_conversational`
  - `turn_timeout = 1.78`
  - `turn_eagerness = eager`
  - `interruptions = false`
- Следующий подтверждённый инженерный порядок после снятия квоты:
  1. `validate_variants.sh`
  2. readiness
  3. self-test published current
  4. `interruptible_balanced`
  5. при необходимости `interruptible_softfill`
  6. при необходимости `interruptible_latefill`
  7. при необходимости repeatable fallback `0901...`

## Что делать дальше

1. Если нужен просто короткий вход:
   - открыть:
     - `.runtime/eleven_control_tower_latest/operational_brief.md`
2. Если нужен быстрый выбор следующего variant:
   - открыть:
     - `.runtime/eleven_control_tower_latest/next_variant_advisor.md`
3. Если нужен полный пересбор состояния:
   - выполнить:
     - `./scripts/refresh_eleven_control_tower.sh`
4. Если нужен refresh со свежим live snapshot:
   - выполнить:
     - `./scripts/refresh_eleven_control_tower.sh --with-fetch`
5. Пока readiness показывает `quota_blocker_active`:
   - не запускать новые live/self-test звонки;
   - продолжать только offline-аудит, validators, pack и документацию.
