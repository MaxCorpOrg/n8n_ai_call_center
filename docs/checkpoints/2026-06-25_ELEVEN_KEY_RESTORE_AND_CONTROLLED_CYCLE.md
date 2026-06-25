# Контрольная точка: 2026-06-25 — возврат рабочего ключа Eleven и controlled cycle

## Сделано
- Подтверждено, что live `Eleven` снова работает с новым ключом:
  - первый успешный probe:
    - `conv_1701kvywnxy1fb9bm40n263y709v`
- Восстановлен и перепроверен relay/tunnel контур.
- Исправлен `scripts/report_eleven_live_readiness.sh`:
  - historical quota-pressure больше не трактуется как active blocker после нового успешного звонка.
- Проведён controlled cycle с published branch:
  - `conv_8901kvyyr24cee28s4zxwkwc3t24`
  - `conv_4501kvyyz89wfq88gyqrt833b5nm`
  - `conv_2201kvyz4kf6e9avc45fvqc7kxjr`
  - `conv_9401kvyzg726f6qvrk7vskh1vcpv`
  - `conv_6901kvz1bwyye11skyebrrj42w9p`
- Добавлены новые helper-скрипты для узких published-патчей:
  - `scripts/prepare_eleven_late_rescue_sms_fastlane_variant.sh`
  - `scripts/prepare_eleven_callback_close_override_variant.sh`

## Что подтвердили по живым разговорам
- Базовая published-версия `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k` снова реально звонит.
- На ней подтверждены дефекты:
  - поздний `Алло?` после уже живого business-dialogue;
  - `Секунду...` / filler перед `send_sms_info`;
  - spoken close вокруг SMS-finalization;
  - длинные user->agent gaps.
- Узкая версия `agtvrsn_7601kvyyy5sce6xarqwa6nsj7kcy` частично улучшила SMS-сценарий:
  - поздний `Алло?` в SMS path ушёл;
  - но остались:
    - `[calm]`
    - callback tail `Могу чем-то ещё помочь?`
- Версия `agtvrsn_6501kvyz3x23f0ktzbjr2aw52g07` признана плохой:
  - агент начал проговаривать tool-инструкции как обычную речь.
- После этого выполнен safe revert.

## Текущий безопасный live-state
- Safe rollback head:
  - `agtvrsn_0401kvyz7rxwek0ascbsx8det42f`
- Узкий callback-close кандидат сверху:
  - `agtvrsn_8601kvyzffdyf58bhf4knm6wk15m`
- На `8601...` уже подтверждено:
  - нет нового tool-speech regression;
  - разговоры доходят до финала;
  - `6501...`-дефект не вернулся.
- Но `8601...` ещё не подтверждён на чистом callback terminal case:
  - тесты снова уходили в SMS path или pronunciation path.

## На чём остановились
- Текущая инженерная задача уже не про ключ, квоту или relay.
- Текущая задача:
  - дожать callback final close без helpdesk tail;
  - отдельно от rescue/SMS/tool sequencing.
- Последний тест на `8601...`:
  - `conv_6901kvz1bwyye11skyebrrj42w9p`
  показал:
  - версия рабочая;
  - но сценарий опять ушёл в SMS, а не в callback-later finalization.

## Что делать дальше
1. Следующий тест делать только под target-case:
   - `сейчас неудобно`
   - `перезвоните позже`
   - `я занят, давайте потом`
2. Не уводить этот тест в SMS.
3. Проверять только один вопрос:
   - исчез ли хвост `Могу чем-то ещё помочь?`
     после callback finalization.
4. Не смешивать в одном patch:
   - callback close
   - late rescue
   - terminal tool phrasing
   - SMS fastlane

## Важные версии
- Базовая старая published:
  - `agtvrsn_9601kvcyw6eyebtrv3wpdq56cj0k`
- Частично улучшенная, но не финальная:
  - `agtvrsn_7601kvyyy5sce6xarqwa6nsj7kcy`
- Плохая, не использовать:
  - `agtvrsn_6501kvyz3x23f0ktzbjr2aw52g07`
- Safe revert head:
  - `agtvrsn_0401kvyz7rxwek0ascbsx8det42f`
- Текущий callback-close кандидат:
  - `agtvrsn_8601kvyzffdyf58bhf4knm6wk15m`
