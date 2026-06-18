# 2026-06-17 — Eleven naturalness lab: strict silence window published, runtime test blocked externally

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
- После этого patch уже реально опубликован в ElevenLabs:
  - `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz`
- Опубликованная версия тоже подтверждена по конфигу:
  - `26/26 ok`
  - в prompt есть:
    - strict silence block
    - запрет `Да? Чем могу помочь?`
    - запрет `SMS / callback / manager` в silence-state
    - требование одного `no_answer` path

## На чем остановились
- Strict-silence patch уже опубликован.
- Но живой runtime test не удалось подтвердить из-за внешнего ограничения телефонии, а не из-за prompt:
  - outbound ответ:
    - `status = sanctioned_country`
    - `message = This functionality is not available in your location.`
- Дополнительно прямой relay снова дал timeout, а webhook указывает на inactive workflow:
  - `Active version not found for workflow with id "sHTbALayEZdy8Mzs"`
- Значит по текущей контрольной точке:
  - prompt/config уже обновлён и опубликован;
  - живое доказательство по phone runtime временно заблокировано внешним состоянием.

## Что делать дальше
1. Как только внешний outbound снова станет доступен, снять один короткий test-call на молчание после opener.
2. Проверить, что больше нет:
  - `Да? Чем могу помочь?`
  - повторных `Алло?`
  - предложений `SMS / callback` в silence-state.
3. Отдельно проверить, не нужно ли перевязать live webhook вместо inactive workflow `sHTbALayEZdy8Mzs`.
4. Только после runtime-подтверждения решать, оставлять ли `agtvrsn_6001kvcq8b3zf8p9cxdheh1gtbxz` как новую рабочую вершину lab.
