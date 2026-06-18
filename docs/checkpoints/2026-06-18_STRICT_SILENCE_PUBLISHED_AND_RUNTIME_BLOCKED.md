# Контрольная точка — 2026-06-18

## Тема

Naturalness lab: strict-silence patch уже опубликован, но живой runtime-test заблокирован внешним outbound-ограничением.

## Сделано

- Подтверждено, что lab-версия:
  - `agtvrsn_1301kvagt880eg88y6kynrmyxzvx`
  даёт регрессию именно на тишине после opener:
  - repeated `Алло?`
  - `Да? Чем могу помочь?`
  - предложения `SMS / callback` внутри silence-state
- Подготовлен и опубликован узкий patch поверх более здоровой базы:
  - база:
    - `agtvrsn_2101kvag7mw1fpgv6y64jp58qk7j`
  - опубликованная версия:
    - `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
- По опубликованной версии уже локально подтверждено:
  - strict silence block на месте
  - запрет `Да? Чем могу помочь?` на месте
  - запрет `SMS / callback / manager` в silence-state на месте
  - усиленные инварианты payload зелёные:
    - `43/43 ok`
  - артефакт:
    - `.runtime/eleven_lab_strict_silence_window_2026-06-17/apply_result/prompt_invariants_43.json`
- Обновлены основные handoff-документы:
  - `docs/knowledge_base/09_PROJECT_CHANGELOG_AND_STATE.md`
  - `документация_для_агента/02_ТЕКУЩЕЕ_LIVE_СОСТОЯНИЕ.md`
 - Усилен локальный verifier:
   - `scripts/check_eleven_prompt_invariants.py`
   теперь дополнительно страхует:
   - strict silence block;
   - запрет helpdesk-фраз в silence-state;
   - запрет repeated `Алло?`;
   - single finalization path;
   - short rescue micro-cut;
   - single spoken close через `end_call`;
   - soft-timeout filler config.

## На чем остановились

- Prompt/config уже опубликованы в lab и подтверждены по структуре.
- Но живой проверочный звонок пока не дал нормального transcript из-за внешнего состояния outbound:
  - `status = sanctioned_country`
  - `message = This functionality is not available in your location.`
- Параллельно виден отдельный инфраструктурный хвост:
  - direct relay timeout
  - webhook отвечает:
    - `Active version not found for workflow with id "sHTbALayEZdy8Mzs"`
- Значит сейчас нельзя честно утверждать, что silence-fix уже доказан в живом звонке.
- Дополнительно на `2026-06-18` это перепроверено свежими probe:
  - `POST https://www.n-8-n.site/webhook/eleven/outbound-call` сейчас реально возвращает:
    - `404 Active version not found for workflow with id "sHTbALayEZdy8Mzs"`
  - direct probe с локальной машины в:
    - `http://151.241.228.232:8787/health`
    уходит в timeout;
  - но тот же health probe с live-сервера `ai-core-prod-147` возвращает:
    - `{"ok": true, "service": "eleven_outbound_relay", ...}`
- Значит для lab self-test сейчас канонический путь старта звонка:
  - `relay_via_server`
  а не live webhook и не прямой relay с локальной машины.

## Что делать дальше

1. Как только outbound снова станет доступен, снять один короткий self-test на сценарий:
   - подняли трубку
   - после opener молчим
2. Подтвердить, что в разговоре больше нет:
   - repeated `Алло?`
   - `Да? Чем могу помочь?`
   - `SMS / callback` внутри silence-state
3. Отдельно проверить, не нужно ли перевязать webhook вместо inactive workflow:
   - `sHTbALayEZdy8Mzs`
4. До runtime-подтверждения не объявлять `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz` окончательной победной вершиной.
5. Для branch self-test использовать текущий дефолт:
   - `relay_via_server -> relay -> webhook`
