# 2026-06-17 — Eleven naturalness lab: strict silence window pending

## Сделано
- Подтверждён регресс опубликованной lab-версии:
  - `agtvrsn_1301kvagt880eg88y6kynrmyxzvx`
- Контрольный звонок:
  - `conv_4701kvagtyy2f23sp134p47b0tp0`
  показал, что agent нарушает правило тишины:
  - уходит в цикл `Алло?`
  - использует inbound-style фразы вроде:
    - `Да? Чем могу помочь?`
  - предлагает `SMS / callback` прямо в состоянии молчания
  - не закрывает silence-path как один `no_answer`.
- Это признано регрессией и не должно считаться новой рабочей вершиной.
- Подготовлен новый локальный helper:
  - [scripts/prepare_eleven_strict_silence_window_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_strict_silence_window_variant.sh:1)
- Он собирает узкий patch поверх более здоровой базы:
  - `agtvrsn_2101kvag7mw1fpgv6y64jp58qk7j`
- Что именно добавляет patch:
  - silence после opener трактуется только как `no_answer`-state;
  - в этом состоянии нельзя:
    - продолжать discovery;
    - объяснять продукт;
    - предлагать SMS / callback / manager;
    - говорить `Да? Чем могу помочь?`
  - разрешён только один rescue;
  - после него при отсутствии нормального ответа должен быть:
    - silent `call_log(no_answer)`
    - silent end.
- Локальная верификация payload:
  - `26/26 ok`
  - артефакт:
    - `.runtime/eleven_lab_strict_silence_window_2026-06-17/payload.json`

## На чем остановились
- Strict-silence patch уже собран локально.
- Но на момент этой контрольной точки он ещё не опубликован в ElevenLabs, потому что ход был прерван перед apply-step.
- Значит текущая опубликованная вершина всё ещё проблемная для silence-сценария и не должна считаться финальной.

## Что делать дальше
1. Опубликовать:
  - `.runtime/eleven_lab_strict_silence_window_2026-06-17/payload.json`
2. Снять один короткий test-call на молчание после opener.
3. Проверить, что больше нет:
  - `Да? Чем могу помочь?`
  - повторных `Алло?`
  - предложений `SMS / callback` в silence-state.
4. Только после этого решать, оставлять ли новую версию как рабочую вершину lab.
