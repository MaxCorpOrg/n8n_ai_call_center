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


PROFILES = {
    "published_current": {
        "turn_timeout": 1.78,
        "turn_eagerness": "eager",
        "soft_timeout": 1.9,
        "interruptions_enabled": False,
        "time_promise_allowed": True,
        "override_marker": "none",
    },
    "interruptible_balanced": {
        "turn_timeout": 2.3,
        "turn_eagerness": "normal",
        "soft_timeout": 1.9,
        "interruptions_enabled": True,
        "time_promise_allowed": True,
        "override_marker": "interruptible_balanced",
    },
    "interruptible_softfill": {
        "turn_timeout": 2.3,
        "turn_eagerness": "normal",
        "soft_timeout": 2.4,
        "interruptions_enabled": True,
        "time_promise_allowed": False,
        "override_marker": "interruptible_softfill",
    },
    "interruptible_latefill": {
        "turn_timeout": 2.3,
        "turn_eagerness": "normal",
        "soft_timeout": 3.0,
        "interruptions_enabled": True,
        "time_promise_allowed": False,
        "override_marker": "interruptible_latefill",
    },
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def approx_equal(a, b, tol=1e-6):
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return False


def check_equals(actual, expected, name: str) -> dict:
    ok = actual == expected
    return {
        "name": name,
        "ok": ok,
        "expected": expected,
        "value": actual,
        "message": "exact match" if ok else f"expected {expected}",
    }


def check_float(actual, expected, name: str) -> dict:
    ok = approx_equal(actual, expected)
    return {
        "name": name,
        "ok": ok,
        "expected": expected,
        "value": actual,
        "message": "exact float match" if ok else f"expected {expected}",
    }


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: check_eleven_turn_variant_invariants.py AGENT_JSON PROFILE",
            file=sys.stderr,
        )
        print(f"Profiles: {', '.join(sorted(PROFILES))}", file=sys.stderr)
        return 2

    src = Path(sys.argv[1])
    profile_name = sys.argv[2]

    if not src.exists():
        print(f"File not found: {src}", file=sys.stderr)
        return 2
    if profile_name not in PROFILES:
        print(f"Unknown profile: {profile_name}", file=sys.stderr)
        return 2

    expected = PROFILES[profile_name]
    data = load_json(src)

    turn = ((data.get("conversation_config") or {}).get("turn") or {})
    convo = ((data.get("conversation_config") or {}).get("conversation") or {})
    soft = (turn.get("soft_timeout_config") or {})
    prompt = (
        ((data.get("conversation_config") or {}).get("agent") or {})
        .get("prompt", {})
        .get("prompt", "")
    )

    client_events = convo.get("client_events") or []
    interruptions_enabled = "interruption" in client_events
    soft_prompt = soft.get("llm_generated_message_prompt_override") or ""
    soft_prompt_lower = soft_prompt.lower()
    has_time_promise_marker = any(marker in soft_prompt_lower for marker in TIME_PROMISE_MARKERS)
    override_marker = (
        "interruptible_latefill"
        if "Interruptible latefill override:" in prompt
        else "interruptible_softfill"
        if "Interruptible softfill override:" in prompt
        else "interruptible_balanced"
        if "Interruptible balanced override:" in prompt
        else "none"
    )

    expected_soft_message = (
        "Да..." if profile_name in {"interruptible_softfill", "interruptible_latefill"} else "..."
    )

    checks = [
        check_float(turn.get("turn_timeout"), expected["turn_timeout"], "turn_timeout_expected"),
        check_equals(turn.get("turn_eagerness"), expected["turn_eagerness"], "turn_eagerness_expected"),
        check_float(soft.get("timeout_seconds"), expected["soft_timeout"], "soft_timeout_expected"),
        check_equals(interruptions_enabled, expected["interruptions_enabled"], "interruptions_enabled_expected"),
        check_equals(bool(soft.get("use_llm_generated_message", False)), True, "soft_timeout_llm_generated_enabled"),
        check_equals(soft.get("message"), expected_soft_message, "soft_timeout_fallback_message_expected"),
        check_equals(bool(soft.get("randomize_fillers", True)), False, "soft_timeout_randomize_fillers_disabled"),
        check_equals(int(soft.get("max_soft_timeouts_per_generation", -1)), 1, "soft_timeout_single_fill_per_generation"),
        check_equals(override_marker, expected["override_marker"], "override_marker_expected"),
        {
            "name": "soft_prompt_has_no_time_promise_markers",
            "ok": (not has_time_promise_marker) if not expected["time_promise_allowed"] else True,
            "expected": False if not expected["time_promise_allowed"] else "allowed",
            "value": has_time_promise_marker,
            "message": "no time-promise marker"
            if ((not has_time_promise_marker) or expected["time_promise_allowed"])
            else "time-promise marker detected",
        },
    ]

    failed = [c for c in checks if not c["ok"]]
    result = {
        "source_file": str(src),
        "profile": profile_name,
        "version_id": data.get("version_id"),
        "branch_id": data.get("branch_id"),
        "observed": {
            "turn_timeout": turn.get("turn_timeout"),
            "turn_eagerness": turn.get("turn_eagerness"),
            "soft_timeout_seconds": soft.get("timeout_seconds"),
            "soft_timeout_message": soft.get("message"),
            "use_llm_generated_message": soft.get("use_llm_generated_message"),
            "client_events": client_events,
            "interruptions_enabled": interruptions_enabled,
            "soft_prompt_has_time_promise_marker": has_time_promise_marker,
            "override_marker": override_marker,
        },
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failed),
        "checks_failed": len(failed),
        "ok": not failed,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
