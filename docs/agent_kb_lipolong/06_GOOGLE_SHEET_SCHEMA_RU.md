# Google Sheet: схема для фиксации звонков

Лист `Лиды_обзвон` (основной):

1. `created_at`
2. `updated_at`
3. `lead_id`
4. `source_system`
5. `source_record_key`
6. `company_name`
7. `contact_name`
8. `phone_primary`
9. `phone_secondary`
10. `city`
11. `segment`
12. `lpr_role`
13. `lpr_confirmed`
14. `current_supplier`
15. `current_product`
16. `current_price`
17. `pain_points`
18. `objection_code`
19. `objection_text`
20. `interest_level`
21. `call_result`
22. `next_step`
23. `next_call_at`
24. `preferred_channel`
25. `manager_owner`
26. `expected_volume`
27. `expected_budget`
28. `material_sent`
29. `followup_count`
30. `max_touch_limit`
31. `do_not_call`
32. `final_reason`
33. `notes_short`
34. `notes_redacted`
35. `call_record_url`
36. `eleven_conv_id`
37. `n8n_execution_id`
38. `agent_version`
39. `last_updated_by`

Лист `Справочники`:

- `call_result`: `order_test`, `manager_call`, `callback_scheduled`, `send_kp_pending_callback`, `refusal_soft`, `not_target`, `dnc`, `no_answer`, `busy`.
- `next_step`: `send_kp`, `call_manager`, `callback`, `close_won`, `close_lost`, `archive`.
- `preferred_channel`: `phone`, `whatsapp`, `telegram`.
- `interest_level`: `A`, `B`, `C`.

## Примечание по автодозвону

- Строки с `source_system = xlsx_import` считаются исходной очередью контактов.
- Строки, добавленные через live `call_log`, имеют `source_system = elevenlabs` и используются как история звонков.
- Для автодозвона не нужно смешивать seed-строки и лог-строки в одну логику выбора.
- Стабильный ключ лида для outbound-цепочки рекомендуется брать из `source_record_key`.
