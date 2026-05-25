#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_SHEET_ID = "1kAXIwaa_-rC4MO5vV3mFV-Geha08iL_6pJNCNxlQPAU"
DEFAULT_RANGE = "Лиды_обзвон!A:AM"

MACHINE_PATTERNS = (
    "автоответчик",
    "электронный помощник",
    "помощник",
    "защитник",
    "mts защитник",
    "мтс защитник",
    "mts defender",
    "defender",
    "рекламный звонок",
    "звонок записывается",
    "звонок фильтруется",
    "оставлено короткое сообщение",
    "передан контакт менеджера",
    "сообщение передано",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize live call_log rows from the Google Sheet.")
    parser.add_argument(
        "--env-file",
        default="/home/aicore/n8n-server/.env.callcenter",
        help="Path to env file with GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REFRESH_TOKEN.",
    )
    parser.add_argument("--sheet-id", default=DEFAULT_SHEET_ID, help="Google Sheet id.")
    parser.add_argument("--range", default=DEFAULT_RANGE, help="Google Sheet range to fetch.")
    parser.add_argument(
        "--date",
        default="2026-05-25",
        help="Filter rows by created_at date prefix (YYYY-MM-DD). Empty string disables date filter.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="How many recent rows / anomalies to print.",
    )
    parser.add_argument(
        "--show-timeline",
        action="store_true",
        help="Print per-lead recent timeline instead of only aggregate summary.",
    )
    return parser.parse_args()


def clean_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def load_env_value(env_text: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}=(.*)$", env_text, re.M)
    if not match:
        raise RuntimeError(f"Missing {name} in env file")
    return clean_env_value(match.group(1))


def fetch_access_token(env_path: Path) -> str:
    env_text = env_path.read_text(encoding="utf-8")
    payload = urllib.parse.urlencode(
        {
            "client_id": load_env_value(env_text, "GOOGLE_CLIENT_ID"),
            "client_secret": load_env_value(env_text, "GOOGLE_CLIENT_SECRET"),
            "refresh_token": load_env_value(env_text, "GOOGLE_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        }
    ).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=payload)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)["access_token"]


def fetch_rows(env_path: Path, sheet_id: str, range_name: str) -> list[list[str]]:
    token = fetch_access_token(env_path)
    encoded_range = urllib.parse.quote(range_name, safe="")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{encoded_range}?majorDimension=ROWS"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.load(response)
    return payload.get("values", [])


def normalize_header(text: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", text.strip().lower()).strip("_")


def row_to_dict(header: list[str], values: list[str]) -> dict[str, str]:
    row: dict[str, str] = {}
    for idx, key in enumerate(header):
        row[key] = values[idx] if idx < len(values) else ""
    return row


def parse_ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def ts_sort_value(value: str) -> float:
    parsed = parse_ts(value)
    return parsed.timestamp() if parsed else float("-inf")


def is_machine_note(note: str) -> bool:
    lower = (note or "").lower()
    return any(pattern in lower for pattern in MACHINE_PATTERNS)


@dataclass
class RowEvent:
    created_at: str
    lead_id: str
    source_system: str
    call_result: str
    next_step: str
    phone_primary: str
    contact_name: str
    notes_short: str
    eleven_conv_id: str
    raw: dict[str, str]


def build_events(rows: list[list[str]], date_prefix: str) -> tuple[list[RowEvent], int]:
    if not rows:
        return [], 0
    header = [normalize_header(item) for item in rows[0]]
    events: list[RowEvent] = []
    total_data_rows = max(len(rows) - 1, 0)
    for values in rows[1:]:
        row = row_to_dict(header, values)
        created_at = row.get("created_at", "")
        if date_prefix and not created_at.startswith(date_prefix):
            continue
        source_system = row.get("source_system", "")
        call_result = row.get("call_result", "")
        next_step = row.get("next_step", "")
        if not source_system and not call_result and not next_step:
            continue
        events.append(
            RowEvent(
                created_at=created_at,
                lead_id=row.get("lead_id", ""),
                source_system=source_system,
                call_result=call_result,
                next_step=next_step,
                phone_primary=row.get("phone_primary", ""),
                contact_name=row.get("contact_name", ""),
                notes_short=row.get("notes_short", ""),
                eleven_conv_id=row.get("eleven_conv_id", ""),
                raw=row,
            )
        )
    return events, total_data_rows


def summarize(events: list[RowEvent], total_rows: int, limit: int, show_timeline: bool) -> str:
    lines: list[str] = []
    lines.append(f"rows_total={total_rows}")
    lines.append(f"events_filtered={len(events)}")
    if not events:
        return "\n".join(lines)

    by_source = Counter(event.source_system or "unknown" for event in events)
    by_result = Counter(event.call_result or "empty" for event in events)
    machine_events = [event for event in events if is_machine_note(event.notes_short)]
    provider_failures = [event for event in events if event.call_result == "outbound_request_failed"]
    with_conv = [event for event in events if event.eleven_conv_id]
    by_lead: dict[str, list[RowEvent]] = defaultdict(list)
    for event in events:
        key = event.lead_id or event.raw.get("source_record_key", "") or event.phone_primary
        by_lead[key].append(event)

    resolved_provider_failures: list[RowEvent] = []
    unresolved_provider_failures: list[RowEvent] = []
    for lead_events in by_lead.values():
        lead_events.sort(key=lambda item: ts_sort_value(item.created_at))
        for idx, event in enumerate(lead_events):
            if event.source_system != "autodial_dispatcher" or event.call_result != "outbound_request_failed":
                continue
            later_eleven = [
                other
                for other in lead_events[idx + 1 :]
                if other.source_system == "elevenlabs" and (other.call_result or other.next_step)
            ]
            if later_eleven:
                resolved_provider_failures.append(event)
            else:
                unresolved_provider_failures.append(event)

    lines.append("")
    lines.append("source_system:")
    for key, value in by_source.most_common():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("call_result:")
    for key, value in by_result.most_common():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append(
        "key_signals: "
        f"machine_like_notes={len(machine_events)} "
        f"provider_failures_raw={len(provider_failures)} "
        f"provider_failures_resolved={len(resolved_provider_failures)} "
        f"provider_failures_unresolved={len(unresolved_provider_failures)} "
        f"rows_with_conv_id={len(with_conv)}"
    )

    if unresolved_provider_failures:
        lines.append("")
        lines.append("recent_unresolved_provider_failures:")
        for event in unresolved_provider_failures[-limit:]:
            lines.append(
                f"- {event.created_at} lead={event.lead_id} phone={event.phone_primary} "
                f"contact={event.contact_name} note={event.notes_short}"
            )

    if resolved_provider_failures:
        lines.append("")
        lines.append("recent_resolved_provider_failures:")
        for event in resolved_provider_failures[-limit:]:
            lines.append(
                f"- {event.created_at} lead={event.lead_id} phone={event.phone_primary} "
                f"contact={event.contact_name} note={event.notes_short}"
            )

    if machine_events:
        lines.append("")
        lines.append("recent_machine_like_notes:")
        for event in machine_events[-limit:]:
            lines.append(
                f"- {event.created_at} result={event.call_result} next={event.next_step} "
                f"lead={event.lead_id} conv={event.eleven_conv_id or '-'} note={event.notes_short}"
            )

    if show_timeline:
        timeline: dict[str, list[RowEvent]] = defaultdict(list)
        for event in events:
            key = event.lead_id or event.phone_primary or "unknown"
            timeline[key].append(event)
        lines.append("")
        lines.append("timelines:")
        for key, items in sorted(
            timeline.items(),
            key=lambda pair: ts_sort_value(pair[1][-1].created_at),
            reverse=True,
        )[:limit]:
            lines.append(f"- lead={key}")
            for event in items[-6:]:
                lines.append(
                    f"  {event.created_at} {event.source_system} {event.call_result} "
                    f"next={event.next_step} conv={event.eleven_conv_id or '-'}"
                )
                if event.notes_short:
                    lines.append(f"    note={event.notes_short}")

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    rows = fetch_rows(Path(args.env_file), args.sheet_id, args.range)
    events, total_rows = build_events(rows, args.date)
    print(summarize(events, total_rows, args.limit, args.show_timeline))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
