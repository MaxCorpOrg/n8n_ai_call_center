#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


LINE_CHECK_PATTERNS = [
    r"\bалло\b",
    r"\bслышно\b",
    r"\bвы на линии\b",
    r"\bвы всё ещё на линии\b",
    r"\bвы слышны\b",
]

FILLER_PATTERNS = [
    r"^\s*так\.\.\.?\s*$",
    r"^\s*поняла\.\.\.?\s*$",
    r"^\s*ясно\.\.\.?\s*$",
    r"^\s*\.\.\.\s*$",
]

CLOSE_PATTERNS = [
    r"поняла[, ]+спасибо[. ]+хорошего дня",
    r"поняла[. ]+хорошего дня",
    r"я уже отправила sms на этот номер[. ]+хорошего дня",
]

PLACEHOLDER_PATTERNS = [
    r"system__conversation_id",
    r"conv_abcdef",
    r"conv_current",
    r"conv_123\b",
]


def strip_stage_directions(text: str) -> str:
    text = text or ""
    text = re.sub(r"\[[^\]]+\]", " ", text)
    return text


def norm(text: str) -> str:
    text = strip_stage_directions(text)
    return re.sub(r"\s+", " ", text.strip().lower())


def matches_any(text: str, patterns) -> bool:
    t = norm(text)
    return any(re.search(p, t, flags=re.IGNORECASE) for p in patterns)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def first_tool_name(turn):
    tool_calls = turn.get("tool_calls") or []
    if tool_calls:
        return tool_calls[0].get("tool_name")
    return None


def extract_end_call_message(turns):
    for t in turns:
        for call in t.get("tool_calls") or []:
            if call.get("tool_name") != "end_call":
                continue
            payload = call.get("params_as_json")
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}
            if isinstance(payload, dict):
                msg = payload.get("system__message_to_speak")
                if msg:
                    return msg
    return None


def analyze(path: Path):
    data = load_json(path)
    turns = data.get("transcript") or []
    issues = []
    opener_index = None
    first_post_opener_user_reply_index = None
    first_call_log_index = None
    end_call_message = extract_end_call_message(turns)
    normal_close_messages = []

    for i, turn in enumerate(turns):
        role = turn.get("role")
        msg = turn.get("message") or ""
        tool_name = first_tool_name(turn)

        if role == "agent" and opener_index is None and "Здравствуйте, я официальный представитель липолитика Липолонг." in msg:
            opener_index = i

        if opener_index is not None and i > opener_index and first_post_opener_user_reply_index is None:
            if role == "user" and norm(msg) and norm(msg) != "...":
                first_post_opener_user_reply_index = i

        if first_call_log_index is None and tool_name == "call_log":
            first_call_log_index = i

        if role == "agent" and msg:
            if "[" in msg and "]" in msg:
                issues.append({
                    "type": "bracketed_stage_direction",
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "message": msg,
                })

            if matches_any(msg, CLOSE_PATTERNS):
                normal_close_messages.append({
                    "index": i,
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "message": msg,
                })

    # Duplicate close vs end_call message
    if end_call_message:
        for item in normal_close_messages:
            if norm(item["message"]) == norm(end_call_message):
                issues.append({
                    "type": "duplicate_close_before_end_call",
                    "time_in_call_secs": item["time_in_call_secs"],
                    "message": item["message"],
                    "end_call_message": end_call_message,
                })

    # Line-check after a real post-opener user reply
    if first_post_opener_user_reply_index is not None:
        for i, turn in enumerate(turns):
            if i <= first_post_opener_user_reply_index:
                continue
            if turn.get("role") != "agent":
                continue
            msg = turn.get("message") or ""
            if matches_any(msg, LINE_CHECK_PATTERNS):
                issues.append({
                    "type": "line_check_after_meaningful_post_opener_reply",
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "message": msg,
                })

    # Filler during finalization window
    if first_call_log_index is not None:
        finalization_start = first_call_log_index
        for item in normal_close_messages:
            if item["index"] < first_call_log_index:
                finalization_start = min(finalization_start, item["index"])
        for i, turn in enumerate(turns):
            if i < finalization_start:
                continue
            if turn.get("role") != "agent":
                continue
            msg = turn.get("message") or ""
            if matches_any(msg, FILLER_PATTERNS):
                issues.append({
                    "type": "filler_during_finalization",
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "message": msg,
                })

    # Placeholder conv values in tool calls
    for turn in turns:
        for call in turn.get("tool_calls") or []:
            payload = call.get("params_as_json")
            payload_text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
            if any(re.search(p, payload_text, flags=re.IGNORECASE) for p in PLACEHOLDER_PATTERNS):
                issues.append({
                    "type": "placeholder_conversation_id_in_tool_call",
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "tool_name": call.get("tool_name"),
                    "params_as_json": payload_text,
                })

    # context_fetch before opener
    if opener_index is not None:
        for i, turn in enumerate(turns):
            if i >= opener_index:
                break
            for call in turn.get("tool_calls") or []:
                if call.get("tool_name") == "context_fetch":
                    issues.append({
                        "type": "context_fetch_before_opener",
                        "time_in_call_secs": turn.get("time_in_call_secs"),
                        "tool_name": "context_fetch",
                    })

    summary = {
        "file": str(path),
        "conversation_id": data.get("conversation_id"),
        "branch_id": data.get("branch_id"),
        "version_id": data.get("version_id"),
        "call_summary_title": ((data.get("analysis") or {}).get("call_summary_title")),
        "termination_reason": ((data.get("metadata") or {}).get("termination_reason")),
        "issues_count": len(issues),
        "issues": issues,
    }
    return summary


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_eleven_conversation.py CONVERSATION_JSON [...]", file=sys.stderr)
        sys.exit(1)

    results = [analyze(Path(arg)) for arg in sys.argv[1:]]
    if len(results) == 1:
        print(json.dumps(results[0], ensure_ascii=False, indent=2))
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
