#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


TIME_PROMISE_MARKERS = (
    "секунду",
    "секунд",
    "момент",
    "подожд",
    "one second",
    "just a second",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize(label: str, path: Path) -> dict:
    data = load_json(path)
    turn = ((data.get("conversation_config") or {}).get("turn") or {})
    convo = ((data.get("conversation_config") or {}).get("conversation") or {})
    soft = turn.get("soft_timeout_config") or {}
    prompt = (
        ((data.get("conversation_config") or {}).get("agent") or {})
        .get("prompt", {})
        .get("prompt", "")
    )
    soft_prompt = (soft.get("llm_generated_message_prompt_override") or "").lower()
    time_promise = any(marker in soft_prompt for marker in TIME_PROMISE_MARKERS)
    return {
        "label": label,
        "path": str(path),
        "version_id": data.get("version_id"),
        "branch_id": data.get("branch_id"),
        "turn_timeout": turn.get("turn_timeout"),
        "turn_eagerness": turn.get("turn_eagerness"),
        "soft_timeout_seconds": soft.get("timeout_seconds"),
        "soft_timeout_message": soft.get("message"),
        "use_llm_generated_message": soft.get("use_llm_generated_message"),
        "client_events": convo.get("client_events") or [],
        "interruptions_enabled": "interruption" in (convo.get("client_events") or []),
        "soft_prompt_has_time_promise_marker": time_promise,
        "override_marker": (
            "interruptible_latefill"
            if "Interruptible latefill override:" in prompt
            else "interruptible_softfill"
            if "Interruptible softfill override:" in prompt
            else "interruptible_balanced"
            if "Interruptible balanced override:" in prompt
            else "none"
        ),
    }


def main() -> int:
    if len(sys.argv) < 3 or len(sys.argv[1:]) % 2 != 0:
        print(
            "Usage: report_eleven_turn_variant_matrix.py LABEL_1 JSON_1 [LABEL_2 JSON_2 ...]",
            file=sys.stderr,
        )
        return 2

    args = sys.argv[1:]
    rows = []
    for i in range(0, len(args), 2):
        label = args[i]
        path = Path(args[i + 1])
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            return 2
        rows.append(summarize(label, path))

    payload = {
        "variants": rows,
        "quick_reading": {
            "published_reference": next((r["label"] for r in rows if "published" in r["label"]), None),
            "best_for_barge_in_trial": next((r["label"] for r in rows if r["override_marker"] == "interruptible_balanced"), None),
            "best_for_barge_in_plus_filler_trial": next((r["label"] for r in rows if r["override_marker"] == "interruptible_softfill"), None),
            "best_for_later_filler_trial": next((r["label"] for r in rows if r["override_marker"] == "interruptible_latefill"), None),
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
