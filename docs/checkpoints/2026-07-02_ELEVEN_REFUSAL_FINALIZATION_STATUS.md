# 2026-07-02: ElevenLabs lab — opener уже лучше, добиваем refusal finalization

## Сделано
- Проведён live self-test на `agtvrsn_1201kwh2kt2pfsna2qcrmv50svda`.
- Подтверждено, что этот head не дал честно проверить lexical `not_target`, потому что раньше него всплывали:
  - повтор opener;
  - late line-check / rescue;
  - helpdesk-tail.
- Под это опубликован head:
  - `agtvrsn_5001kwh30b0yfpdvjqk497p7pbj7`
  - builder:
    - [scripts/prepare_eleven_single_shot_opener_nottarget_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_single_shot_opener_nottarget_variant.sh:1)
- Практический результат `5001...`:
  - helpdesk-tail ушёл;
  - грубый multi-restart flow стал лучше;
  - но остались pre-opener `Алло?` и duplicate close.
- Под это опубликован head:
  - `agtvrsn_0601kwh345rse22aztp6hezdkazt`
  - это:
    - `Plaintext terminal single-close`
    - `Non-interruptible finalization`
- Практический результат `0601...`:
  - finalization стала чище;
  - но duplicate close остался;
  - opener всё ещё мог повторяться.
- Под это опубликован head:
  - `agtvrsn_6401kwh3889qfb6art4b4s2692fa`
  - builder:
    - [scripts/prepare_eleven_no_preopener_linecheck_variant.sh](/home/max/n8n_ai_call_center/scripts/prepare_eleven_no_preopener_linecheck_variant.sh:1)
- Практический результат `6401...`:
  - pre-opener `Алло?` ушёл;
  - opener стартует сразу с первого живого `Алло!`;
  - основной remaining defect теперь сидит в refusal finalization path.

## На чем остановились
- Current newest lab head:
  - `agtvrsn_6401kwh3889qfb6art4b4s2692fa`
- Current real blocker:
  - agent всё ещё умеет:
    1. сначала сказать обычное `Поняла, спасибо. Хорошего дня.`
    2. потом сделать `call_log`
    3. потом ещё раз закрыть через `end_call`
- Дополнительно resurfaced:
  - `[calm]` в opener.

## Что делать дальше
1. Делать следующий patch только под `refusal_soft` finalization.
2. Жёстко зафиксировать порядок:
  - silent `call_log(refusal_soft)`
  - one spoken `end_call`
  - stop
3. Отдельным микрошагом снова прибить `[calm]`.
4. После этого снять ещё один короткий self-test и сверить:
  - исчез ли duplicate close;
  - исчезла ли normal speech after `call_log`;
  - исчез ли `[calm]`.
