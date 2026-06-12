# 2026-06-12: wording opener уточнен, второй ход после opener ужат

## Сделано
- Live `AI_CALL_AGENT_1` точечно пропатчен без запуска нового звонкового цикла.
- Новый live version:
  - `agtvrsn_6301ktxp7b4cezb8mc8pba7fxyq9`
- Fixed opener заменён на точную формулировку:
  - `Здравствуйте. Мы официальный представитель липолитика ЛипоЛонг, звоним по поводу сотрудничества для косметологов. Вам это в принципе интересно?`
- `Second turn after opener` в live prompt ужат и конкретизирован:
  - максимум `2` коротких предложения;
  - максимум `1` вопрос;
  - короткие шаблоны для:
    - нейтрального/мягко-позитивного ответа;
    - вопроса `о чём звонок`;
    - занятости;
    - живого посредника.
- Новый prompt подтверждён обратным чтением live-агента через relay-host.

## На чем остановились
- Правка уже стоит в live, но на новом одиночном звонке ещё не проверялась.
- Тестовый outbound-контур остаётся на паузе.
- Bundle `short opener + pre-opener rescue guard` был подтверждён ранее, а текущая правка добавляет поверх него:
  - более точный wording opener;
  - более короткий и направленный второй ход.

## Что делать дальше
1. Следующим шагом запустить один одиночный live-call по следующему номеру по порядку.
2. Проверить:
   - звучит ли opener именно с `официальный представитель липолитика ЛипоЛонг`;
   - не стал ли второй ход снова длинным;
   - не вернулся ли ранний rescue до opener.
3. Если второй ход всё ещё затянут, следующая правка должна идти уже не в opener, а в ещё более жёсткое ограничение follow-up после первого человеческого ответа.

## Артефакты
- `backups/2026-06-12_opener_lipolitik_and_second_turn_trim/current_ai_call_agent_1.before_opener_lipolitik_and_second_turn_trim.json`
- `backups/2026-06-12_opener_lipolitik_and_second_turn_trim/main_opener_lipolitik_and_second_turn_trim_payload.json`
- `backups/2026-06-12_opener_lipolitik_and_second_turn_trim/patch_response.json`
- `backups/2026-06-12_opener_lipolitik_and_second_turn_trim/current_ai_call_agent_1.after_opener_lipolitik_and_second_turn_trim.json`
