#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any


FASTPATH_TOOL_NAME = "send_sms_and_log"
FASTPATH_URL = "https://www.n-8-n.site/webhook/eleven/tool/send-sms-and-log"
OVERRIDE_TITLE = "SMS+call_log fast-path lab override"


def property_schema(
    description: str,
    *,
    enum: list[str] | None = None,
    dynamic_variable: str = "",
) -> dict[str, Any]:
    return {
        "type": "string",
        "description": "" if dynamic_variable else description,
        "enum": enum,
        "is_system_provided": False,
        "dynamic_variable": dynamic_variable,
        "allowed_values_dynamic_variable": "",
        "constant_value": "",
        "is_omitted": False,
    }


def build_tool() -> dict[str, Any]:
    return {
        "name": FASTPATH_TOOL_NAME,
        "type": "webhook",
        "tool_id": None,
        "description": (
            "LAB fast-path: одним webhook-вызовом отправляет SMS через Mango и сразу пишет итог в call_log. "
            "Использовать только после явного согласия клиента получить SMS/контакты/информацию. "
            "Не использовать для machine/voicemail/абонент hard-stop."
        ),
        "api_schema": {
            "request_headers": {},
            "url": FASTPATH_URL,
            "method": "POST",
            "path_params_schema": {},
            "query_params_schema": None,
            "request_body_schema": {
                "type": "object",
                "required": ["message_intent", "call_result", "next_step", "notes_short"],
                "description": "Отправка SMS и запись call_log одним быстрым backend-шагом",
                "properties": {
                    "request_id": property_schema("Уникальный id tool-вызова"),
                    "conversation_id": property_schema("ID разговора ElevenLabs", dynamic_variable="system__conversation_id"),
                    "eleven_conv_id": property_schema("ID разговора ElevenLabs для call_log", dynamic_variable="system__conversation_id"),
                    "lead_id": property_schema("ID лида или исходной строки, например row_8"),
                    "source_record_key": property_schema("Ключ исходной строки таблицы, например row_8"),
                    "caller": property_schema("Номер текущего звонка", dynamic_variable="system__called_number"),
                    "phone_primary": property_schema("Основной номер клиента", dynamic_variable="system__called_number"),
                    "current_call_number": property_schema("Номер текущего звонка для SMS fallback", dynamic_variable="system__called_number"),
                    "contact_name": property_schema("Имя контакта, если удалось узнать"),
                    "client_name": property_schema("Имя клиента, если удалось узнать"),
                    "company_name": property_schema("Компания или бренд, если удалось узнать"),
                    "product": property_schema("Название продукта, обычно LipoLong"),
                    "phone_target": property_schema("Другой номер для SMS, только если клиент попросил отправить не на текущий номер"),
                    "message_intent": property_schema(
                        "Тип SMS: short_info для контактов, product_intro для описания LipoLong/преимуществ/условий",
                        enum=["short_info", "product_intro", "offer", "callback_confirmation"],
                    ),
                    "sms_text": property_schema("Необязательный готовый текст SMS"),
                    "reply_phone": property_schema("Номер менеджера для обратной связи"),
                    "callback_at": property_schema("Когда удобно вернуться к разговору"),
                    "call_result": property_schema(
                        "Итог звонка",
                        enum=[
                            "order_test",
                            "manager_call",
                            "callback_scheduled",
                            "send_kp_pending_callback",
                            "refusal_soft",
                            "not_target",
                            "dnc",
                            "no_answer",
                            "busy",
                        ],
                    ),
                    "next_step": property_schema(
                        "Следующий шаг",
                        enum=["send_kp", "call_manager", "callback", "close_won", "close_lost", "archive"],
                    ),
                    "next_call_at": property_schema("Дата/время следующего касания ISO8601"),
                    "preferred_channel": property_schema("Предпочтительный канал", enum=["sms", "phone", "whatsapp", "telegram"]),
                    "interest_level": property_schema("Уровень интереса A/B/C", enum=["A", "B", "C"]),
                    "objection_text": property_schema("Ключевое возражение или контекст"),
                    "manager_owner": property_schema("Ответственный менеджер"),
                    "notes_short": property_schema("Короткое резюме разговора"),
                    "agent_version": property_schema("Версия/имя lab-агента"),
                },
            },
            "response_body_schema": None,
            "response_filter": None,
            "content_type": "application/json",
            "auth_resolved_params": [],
            "auth_connection": None,
        },
        "pre_tool_speech": "off",
        "tool_call_sound": None,
        "tool_call_sound_behavior": "auto",
    }


def strip_existing_override(prompt: str) -> str:
    pattern = rf"\n\n{re.escape(OVERRIDE_TITLE)}:[\s\S]*$"
    return re.sub(pattern, "", prompt).rstrip()


def build_override() -> str:
    return f"""

{OVERRIDE_TITLE}:
- This override applies only in the ElevenLabs lab branch.
- For explicit SMS consent, use the single combined tool `send_sms_and_log`.
- Do not use the old two-step sequence `send_sms_info` -> `call_log` for SMS consent in this lab branch.
- Do not use `send_sms_and_log` for machine, voicemail, screening-service, or any phrase with service-style `абонент`. Those still use normal `call_log` and silent `end_call`.
- When the user clearly agrees to receive SMS/contact info/details, immediately say one short natural progress cue before backend work.
- Good progress cue examples: `Да, отправляю.`, `Хорошо, сейчас отправлю.`, `Да, секунду.`.
- After that progress cue, call `send_sms_and_log` immediately.
- Required SMS success payload shape:
  - `message_intent`: `short_info` for contacts, `product_intro` if the user asked what LipoLong is / price / details.
  - `call_result`: usually `send_kp_pending_callback`.
  - `next_step`: usually `callback`.
  - `preferred_channel`: `sms`.
  - include current `conversation_id` / `eleven_conv_id`, `phone_primary`, `caller`, `lead_id`, `source_record_key` when available.
- After `send_sms_and_log` returns, do not pitch again and do not ask another sales question.
- End with one short `end_call` spoken close, for example: `SMS отправила, хорошего дня.`
- The desired sequence is:
  1. user agrees to SMS
  2. one short spoken progress cue
  3. `send_sms_and_log`
  4. one short `end_call`
  5. stop
"""


def prepare_payload(source: dict[str, Any], version_description: str) -> dict[str, Any]:
    payload = {
        "conversation_config": source["conversation_config"],
        "platform_settings": source.get("platform_settings"),
        "workflow": source.get("workflow"),
    }
    prompt_cfg = payload["conversation_config"]["agent"]["prompt"]
    prompt_cfg.pop("tool_ids", None)
    tools = prompt_cfg.setdefault("tools", [])
    prompt_cfg["tools"] = [tool for tool in tools if tool.get("name") != FASTPATH_TOOL_NAME]
    prompt_cfg["tools"].append(build_tool())
    prompt_cfg["prompt"] = strip_existing_override(prompt_cfg.get("prompt", "")) + build_override()
    if version_description:
        payload["version_description"] = version_description
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare ElevenLabs lab payload with send_sms_and_log fast-path tool.")
    parser.add_argument("source_agent_json", type=pathlib.Path)
    parser.add_argument("output_json", type=pathlib.Path)
    parser.add_argument("--version-description", default="LAB: combined send_sms_and_log fast-path for SMS consent")
    args = parser.parse_args()

    source = json.loads(args.source_agent_json.read_text(encoding="utf-8"))
    payload = prepare_payload(source, args.version_description)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared payload: {args.output_json}")
    print(f"Added tool: {FASTPATH_TOOL_NAME}")
    print(f"URL: {FASTPATH_URL}")


if __name__ == "__main__":
    main()
