from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .audit_log import load_events
from .models import ActionResult, to_serializable


def build_report(results: list[ActionResult]) -> dict[str, Any]:
    status_counter = Counter(result.status for result in results)
    outcome_counter = Counter(result.outcome for result in results)
    return {
        "total": len(results),
        "by_status": dict(sorted(status_counter.items())),
        "by_outcome": dict(sorted(outcome_counter.items())),
        "items": [result.to_dict() for result in results],
    }


def write_report(results: list[ActionResult], output_path: Path) -> Path:
    payload = build_report(results)
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(to_serializable(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def build_report_from_audit_log(path: Path) -> dict[str, Any]:
    events = load_events(path)
    results = [event for event in events if event.get("event_type") == "action_result"]
    status_counter = Counter(str(event.get("status") or "unknown") for event in results)
    outcome_counter = Counter(str(event.get("outcome") or "unknown") for event in results)
    return {
        "total_result_events": len(results),
        "by_status": dict(sorted(status_counter.items())),
        "by_outcome": dict(sorted(outcome_counter.items())),
        "event_count": len(events),
    }
