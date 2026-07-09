#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import shlex
import subprocess
from typing import Any

import requests


SERVER_ALIAS = "ai-core-prod-147"
TOOLS_URL = "https://api.elevenlabs.io/v1/convai/tools"
TOOL_NAME = "send_sms_and_log"
TOOL_URL = "https://www.n-8-n.site/webhook/eleven/tool/send-sms-and-log"


def remote_eleven_key(server_alias: str) -> str:
    script = (
        "for p in /home/aicore/n8n-server/.env.callcenter /home/aicore/n8n-ai-clean/.env.callcenter; do "
        "[ -f \"$p\" ] || continue; "
        "grep -E '^(ELEVENLABS_API_KEY|ELEVEN_API_KEY)=' \"$p\" | head -1 | cut -d= -f2- && exit 0; "
        "done; exit 1"
    )
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", server_alias, f"sh -lc {shlex.quote(script)}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip().strip('"').strip("'")


def prop(description: str, *, enum: list[str] | None = None, dynamic_variable: str = "") -> dict[str, Any]:
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


def tool_config() -> dict[str, Any]:
    return {
        "type": "webhook",
        "name": TOOL_NAME,
        "description": (
            "LAB fast-path: одним webhook-вызовом отправляет SMS через Mango и сразу пишет итог в call_log. "
            "Использовать только после явного согласия клиента получить SMS/контакты/информацию."
        ),
        "response_timeout_secs": 20,
        "disable_interruptions": True,
        "interruption_mode": "disable_during_tool_and_turn",
        "force_pre_tool_speech": False,
        "pre_tool_speech": "auto",
        "assignments": [],
        "tool_call_sound": None,
        "tool_call_sound_behavior": "auto",
        "tool_error_handling_mode": "auto",
        "dynamic_variables": {"dynamic_variable_placeholders": {}},
        "execution_mode": "immediate",
        "api_schema": {
            "request_headers": {},
            "url": TOOL_URL,
            "method": "POST",
            "path_params_schema": {},
            "query_params_schema": None,
            "request_body_schema": {
                "type": "object",
                "required": ["message_intent", "call_result", "next_step", "notes_short"],
                "description": "Отправка SMS и запись call_log одним быстрым backend-шагом",
                "properties": {
                    "request_id": prop("Уникальный id tool-вызова", dynamic_variable="request_id"),
                    "conversation_id": prop("ID разговора ElevenLabs", dynamic_variable="system__conversation_id"),
                    "eleven_conv_id": prop("ID разговора ElevenLabs для call_log", dynamic_variable="system__conversation_id"),
                    "lead_id": prop("ID лида или исходной строки", dynamic_variable="lead_id"),
                    "source_record_key": prop("Ключ исходной строки таблицы", dynamic_variable="source_record_key"),
                    "caller": prop("Номер текущего звонка", dynamic_variable="caller"),
                    "phone_primary": prop("Основной номер клиента", dynamic_variable="phone_primary"),
                    "current_call_number": prop("Номер текущего звонка для SMS fallback", dynamic_variable="system__called_number"),
                    "contact_name": prop("Имя контакта", dynamic_variable="contact_name"),
                    "client_name": prop("Имя клиента, если удалось узнать"),
                    "company_name": prop("Компания или бренд", dynamic_variable="company_name"),
                    "product": prop("Название продукта, обычно LipoLong"),
                    "phone_target": prop("Другой номер для SMS, только если клиент попросил отправить не на текущий номер"),
                    "message_intent": prop(
                        "Тип SMS: short_info для контактов, product_intro для описания LipoLong/преимуществ/условий",
                        enum=["short_info", "product_intro", "offer", "callback_confirmation"],
                    ),
                    "sms_text": prop("Необязательный готовый текст SMS"),
                    "reply_phone": prop("Номер менеджера для обратной связи"),
                    "callback_at": prop("Когда удобно вернуться к разговору"),
                    "call_result": prop(
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
                    "next_step": prop(
                        "Следующий шаг",
                        enum=["send_kp", "call_manager", "callback", "close_won", "close_lost", "archive"],
                    ),
                    "next_call_at": prop("Дата/время следующего касания ISO8601"),
                    "preferred_channel": prop("Предпочтительный канал", enum=["sms", "phone", "whatsapp", "telegram"]),
                    "interest_level": prop("Уровень интереса A/B/C", enum=["A", "B", "C"]),
                    "objection_text": prop("Ключевое возражение или контекст"),
                    "manager_owner": prop("Ответственный менеджер"),
                    "notes_short": prop("Короткое резюме разговора"),
                    "agent_version": prop("Версия/имя lab-агента"),
                },
            },
            "response_body_schema": None,
            "response_filter": None,
            "content_type": "application/json",
            "auth_resolved_params": [],
            "auth_connection": None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reuse ElevenLabs send_sms_and_log webhook tool.")
    parser.add_argument("output_dir", type=pathlib.Path)
    parser.add_argument("--server-alias", default=SERVER_ALIAS)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    key = remote_eleven_key(args.server_alias)
    headers = {"xi-api-key": key, "Content-Type": "application/json"}

    list_response = requests.get(TOOLS_URL, headers={"xi-api-key": key}, params={"page_size": 100, "types": "webhook"}, timeout=60)
    list_response.raise_for_status()
    list_path = args.output_dir / "tools_list_before.json"
    list_path.write_text(json.dumps(list_response.json(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for tool in list_response.json().get("tools", []):
        cfg = tool.get("tool_config") or {}
        if cfg.get("name") == TOOL_NAME and ((cfg.get("api_schema") or {}).get("url") == TOOL_URL):
            out = {"action": "reuse_existing", "id": tool.get("id"), "tool": tool}
            (args.output_dir / "create_tool_response.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"action": "reuse_existing", "id": tool.get("id"), "name": TOOL_NAME}, ensure_ascii=False, indent=2))
            return

    payload = {"tool_config": tool_config()}
    payload_path = args.output_dir / "create_tool_payload.json"
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    create_response = requests.post(TOOLS_URL, headers=headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), timeout=60)
    response_path = args.output_dir / "create_tool_response.json"
    response_path.write_text(json.dumps(create_response.json(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    create_response.raise_for_status()
    print(json.dumps({"action": "created", "id": create_response.json().get("id"), "name": TOOL_NAME}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
