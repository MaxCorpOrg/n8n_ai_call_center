# 2026-06-17 — Eleven naturalness lab: mid-dialogue reassurance trim

## Сделано
- Поверх pre-opener self-talk fix выпущен ещё один узкий lab-only patch:
  - [scripts/prepare_eleven_mid_dialogue_reassurance_trim_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_mid_dialogue_reassurance_trim_variant.sh:1)
- Его цель:
  - убрать support-style хвосты внутри уже активного разговора;
  - запретить фразы:
    - `Да, я тут`
    - `Я тут`
    - `Да, я на линии`
    - `Я на линии`
    - `Да, слышу вас`
    - `Я вас слышу`
  - запретить bracket tags в spoken text:
    - `[calm]`
    - `[pause]`
    - `[thinking]`
- Новый published lab version:
  - `agtvrsn_2101kvag7mw1fpgv6y64jp58qk7j`
- Контрольный self-test:
  - `conv_3701kvag8d1wfvx9egszbbwj21zr`
- Что подтвердилось по этому звонку:
  - `Да, я тут` исчезло;
  - `[calm]` исчезло;
  - opener остался чистым и без префикса;
  - call_log дошёл;
  - финальный `end_call` дошёл.

## На чем остановились
- Новый патч реально улучшил разговорный хвост.
- Но в контрольном звонке всё ещё остались два технических остатка:
  - один поздний `Алло?` внутри уже активного диалога;
  - `duplicate_close_before_end_call`
- Значит текущая линия стала лучше по naturalness, но финализация и late line-check ещё не добиты до конца.

## Что делать дальше
1. Следующий узкий цикл держать только по двум остаткам:
  - late `Алло?`
  - duplicate close перед `end_call`
2. Не трогать снова opener, price-answer и machine-stop, потому что эта линия их сейчас не ломает.
3. Базовой рабочей точкой lab на сейчас считать:
  - `agtvrsn_2101kvag7mw1fpgv6y64jp58qk7j`
