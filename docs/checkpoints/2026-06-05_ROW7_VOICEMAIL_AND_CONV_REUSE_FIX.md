# 2026-06-05: `row_7`, voicemail-case и защита от reuse старого `conv_*`

## Сделано
- Выполнен следующий одиночный звонок по:
  - `row_7`
  - `+79627956556`
  - `Евгения Волкова`
- Разговор:
  - `conv_2101ktbynrjkffsaw7ttmhvxjxcd`
  - `version_id = agtvrsn_4801ktbw46wde348tvxnf4ewx54q`
- Это был voicemail-case:
  - линия сама сказала, что абонент не отвечает и звонок перенаправлен на голосовой почтовый ящик
- Agent снова отработал правильно по machine-path:
  - `call_log`
  - silent `end_call`
- Но в `call_log` найден reuse-баг:
  - вместо текущего `conv_2101ktbynrjkffsaw7ttmhvxjxcd` ушёл старый `conv_1901ktbtzw94ek4rzngccvtqka9k`
- После этого live prompt ещё раз усилен:
  - убран буквальный valid-example старого `conv_*`
  - добавлено правило не переиспользовать `conv_*` из предыдущего звонка, примера, transcript или tool-result
- Новая live version:
  - `agtvrsn_1001ktbys8ftfpys5gykctxrqka5`

## На чем остановились
- Минимальные workflow снова выключены.
- Контур снова на паузе.
- Точный двухфразный opener на живом человеке по-прежнему не проверен.
- Последний anti-reuse fix уже в live, но ещё не подтверждён следующей проверкой.

## Что делать дальше
- Следующий одиночный тест делать по `row_8`.
- Проверить:
  1. если machine-path — пишет ли `call_log` уже текущий `conv_*` без reuse;
  2. если live-human — стартует ли агент ровно заданным двухфразным opener.
