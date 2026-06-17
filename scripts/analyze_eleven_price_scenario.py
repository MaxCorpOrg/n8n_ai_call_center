#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


PRICE_ASK_PATTERNS = [
    r"\bсколько\b.*\bстоит\b",
    r"\bкакая\s+цена\b",
    r"\bпо\s+цене\b",
    r"\bстоимость\b",
    r"\bцена\b",
    r"\bбесплатн\w*\b",
]

PRICE_MENTION_PATTERNS = [
    r"19\s*000\s*руб",
    r"от\s*19\s*000\s*руб",
    r"\bцен",
    r"\bстоим",
    r"\bне бесплатн",
]

NEXT_STEP_PATTERNS = [
    r"\bsms\b",
    r"\bсмс\b",
    r"\bменеджер",
    r"\bперезвон",
    r"\bcallback\b",
]


def norm(text: str) -> str:
    text = text or ""
    text = re.sub(r"\[[^\]]+\]", " ", text)
    return re.sub(r"\s+", " ", text.strip().lower())


def matches(text: str, patterns: list[str]) -> bool:
    t = norm(text)
    return any(re.search(p, t, flags=re.IGNORECASE) for p in patterns)


def sentence_count(text: str) -> int:
    parts = [p for p in re.split(r"[.!?]+", text or "") if p.strip()]
    return len(parts)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def analyze(path: Path) -> dict:
    data = load(path)
    turns = data.get("transcript") or []

    first_price_question_idx = None
    first_price_question_time = None
    first_agent_price_before_question = None
    first_agent_price_after_question = None
    next_step_after_price = None

    for idx, turn in enumerate(turns):
        role = turn.get("role")
        msg = turn.get("message") or ""

        if role == "user" and first_price_question_idx is None and matches(msg, PRICE_ASK_PATTERNS):
            first_price_question_idx = idx
            first_price_question_time = turn.get("time_in_call_secs")
            continue

        if role != "agent":
            continue

        if matches(msg, PRICE_MENTION_PATTERNS):
            item = {
                "index": idx,
                "time_in_call_secs": turn.get("time_in_call_secs"),
                "message": msg,
                "sentence_count": sentence_count(msg),
            }
            if first_price_question_idx is None and first_agent_price_before_question is None:
                first_agent_price_before_question = item
            elif first_price_question_idx is not None and idx > first_price_question_idx and first_agent_price_after_question is None:
                first_agent_price_after_question = item

        if first_agent_price_after_question is not None:
            if idx == first_agent_price_after_question["index"] and matches(msg, NEXT_STEP_PATTERNS):
                next_step_after_price = {
                    "index": idx,
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "message": msg,
                }
                break
            if idx > first_agent_price_after_question["index"] and matches(msg, NEXT_STEP_PATTERNS):
                next_step_after_price = {
                    "index": idx,
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "message": msg,
                }
                break

    issues = []

    if first_agent_price_before_question is not None:
        issues.append({
            "type": "price_mentioned_before_user_asked",
            **first_agent_price_before_question,
        })

    if first_price_question_idx is None:
        issues.append({
            "type": "no_price_question_detected",
        })

    if first_price_question_idx is not None and first_agent_price_after_question is None:
        issues.append({
            "type": "no_price_answer_after_question",
            "time_in_call_secs": first_price_question_time,
        })

    if first_agent_price_after_question is not None and first_agent_price_after_question["sentence_count"] > 2:
        issues.append({
            "type": "price_answer_too_long",
            **first_agent_price_after_question,
        })

    if first_agent_price_after_question is not None and next_step_after_price is None:
        issues.append({
            "type": "no_next_step_after_price_answer",
            "time_in_call_secs": first_agent_price_after_question["time_in_call_secs"],
            "message": first_agent_price_after_question["message"],
        })

    result = {
        "file": str(path),
        "conversation_id": data.get("conversation_id"),
        "branch_id": data.get("branch_id"),
        "version_id": data.get("version_id"),
        "price_question_detected": first_price_question_idx is not None,
        "first_price_question": {
            "index": first_price_question_idx,
            "time_in_call_secs": first_price_question_time,
        } if first_price_question_idx is not None else None,
        "price_before_question": first_agent_price_before_question,
        "price_answer_after_question": first_agent_price_after_question,
        "next_step_after_price": next_step_after_price,
        "issues_count": len(issues),
        "issues": issues,
        "ok": len(issues) == 0,
    }
    return result


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: analyze_eleven_price_scenario.py CONVERSATION_JSON [...]", file=sys.stderr)
        return 1

    results = [analyze(Path(arg)) for arg in sys.argv[1:]]
    if len(results) == 1:
        print(json.dumps(results[0], ensure_ascii=False, indent=2))
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
