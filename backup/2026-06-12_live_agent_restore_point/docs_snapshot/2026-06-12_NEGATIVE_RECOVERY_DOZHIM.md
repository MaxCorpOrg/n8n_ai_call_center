# 2026-06-12: refusal-логика после opener развёрнута обратно в дожим

## Сделано
- После обратной связи по живой продаже отменена логика:
  - `нет / не надо / не нужно / неинтересно` -> сразу финальный отказ.
- Live-agent перепатчен.
- Новая live version:
  - `agtvrsn_0901ktxsrethemqr4prhkw701wr2`
- В live prompt закреплено:
  - короткий отказ сразу после opener не финальный по умолчанию;
  - сначала один короткий уточняющий вопрос;
  - потом, если контакт релевантный, один rescue-move:
    - SMS,
    - callback менеджера,
    - или одна короткая value-line + next step;
  - если это вообще не их направление — `not_target`;
  - если после уточнения и одного rescue-move всё равно отказ — `refusal_soft`, короткое завершение, без повторного дожима.

## На чем остановились
- Live-правка уже стоит и подтверждена обратным `GET`.
- Новый test-call после этой правки ещё не запускался.
- Тестовый outbound-контур остаётся на паузе.

## Что делать дальше
1. Следующий одиночный звонок делать уже на version `agtvrsn_0901ktxsrethemqr4prhkw701wr2`.
2. Проверять именно кейсы:
   - `нет`
   - `не надо`
   - `не нужно`
   - `неинтересно`
3. Снимать по ним:
   - какой уточняющий вопрос дал агент;
   - был ли rescue-move;
   - не ушёл ли агент в длинный монолог;
   - чем завершился кейс:
     - `not_target`
     - `refusal_soft`
     - SMS
     - callback.

## Артефакты
- `backups/2026-06-12_negative_recovery_dozhim/current_ai_call_agent_1.before_negative_recovery_dozhim.json`
- `backups/2026-06-12_negative_recovery_dozhim/main_negative_recovery_dozhim_payload.json`
- `backups/2026-06-12_negative_recovery_dozhim/patch_response.json`
- `backups/2026-06-12_negative_recovery_dozhim/current_ai_call_agent_1.after_negative_recovery_dozhim_confirmed.json`
