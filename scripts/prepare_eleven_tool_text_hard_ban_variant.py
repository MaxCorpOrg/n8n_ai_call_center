#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any


OVERRIDE_TITLE = "No spoken tool text hard-ban override"


def strip_existing_override(prompt: str) -> str:
    pattern = rf"\n\n{re.escape(OVERRIDE_TITLE)}:[\s\S]*$"
    return re.sub(pattern, "", prompt).rstrip()


def build_override() -> str:
    return f"""

{OVERRIDE_TITLE}:
- Never pronounce tool names, tool payloads, JSON, pseudo-code, or implementation instructions to the user.
- Forbidden spoken fragments include: `call_log with`, `send_sms_info with`, `send_sms_and_log with`, `end_call with`, `skip_turn`, `params_as_json`, `silent`, raw JSON braces, or any similar tool narration.
- If a tool is needed, call the actual tool silently through the tool system. Do not describe that action in normal speech.
- After a repeated clear refusal, do not say tool text. Use the actual `call_log` tool silently, then use `end_call` with one short human close.
- If you catch yourself about to say a tool name or JSON, stop that spoken response and execute the tool instead.
"""


def prepare_payload(source: dict[str, Any], version_description: str, add_tool_id: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {
        "conversation_config": source["conversation_config"],
        "platform_settings": source.get("platform_settings"),
        "workflow": source.get("workflow"),
    }
    prompt_cfg = payload["conversation_config"]["agent"]["prompt"]
    if add_tool_id:
        tool_ids = list(prompt_cfg.get("tool_ids") or [])
        if add_tool_id not in tool_ids:
            tool_ids.append(add_tool_id)
        prompt_cfg["tool_ids"] = tool_ids
        prompt_cfg.pop("tools", None)
    else:
        prompt_cfg.pop("tool_ids", None)
    prompt_cfg["prompt"] = strip_existing_override(prompt_cfg.get("prompt", "")) + build_override()
    if version_description:
        payload["version_description"] = version_description
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare ElevenLabs payload that hard-bans spoken tool text.")
    parser.add_argument("source_agent_json", type=pathlib.Path)
    parser.add_argument("output_json", type=pathlib.Path)
    parser.add_argument("--add-tool-id", default="")
    parser.add_argument("--version-description", default="LAB: hard-ban spoken tool text")
    args = parser.parse_args()

    source = json.loads(args.source_agent_json.read_text(encoding="utf-8"))
    payload = prepare_payload(source, args.version_description, args.add_tool_id)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared payload: {args.output_json}")
    print(f"Added override: {OVERRIDE_TITLE}")
    if args.add_tool_id:
        print(f"Added tool_id: {args.add_tool_id}")


if __name__ == "__main__":
    main()
