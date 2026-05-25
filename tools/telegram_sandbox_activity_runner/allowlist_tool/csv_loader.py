from __future__ import annotations

import csv
import re
from pathlib import Path

from .models import ALLOWED_ACTION_TYPES, AccountRecord, ActionRecord, AllowlistRecord


def load_accounts(path: Path) -> dict[str, AccountRecord]:
    records: dict[str, AccountRecord] = {}
    for row in read_csv_rows(path):
        account_id = normalize_required(row.get("account_id"), "account_id", path)
        record = AccountRecord(
            account_id=account_id,
            session_file=Path(normalize_required(row.get("session_file"), "session_file", path)).expanduser().resolve(),
            api_id_env=normalize_required(row.get("api_id_env"), "api_id_env", path),
            api_hash_env=normalize_required(row.get("api_hash_env"), "api_hash_env", path),
            enabled=parse_bool(row.get("enabled"), default=True),
            label=normalize_text(row.get("label")),
        )
        records[record.account_id] = record
    return records


def load_allowlist(path: Path) -> dict[str, AllowlistRecord]:
    records: dict[str, AllowlistRecord] = {}
    for row in read_csv_rows(path):
        entity_id = normalize_required(row.get("entity_id"), "entity_id", path)
        allowed_actions = frozenset(parse_csv_set(row.get("allowed_actions")))
        invalid_actions = sorted(item for item in allowed_actions if item not in ALLOWED_ACTION_TYPES)
        if invalid_actions:
            raise ValueError(f"{path}: entity_id={entity_id} has unsupported allowed_actions: {', '.join(invalid_actions)}")
        record = AllowlistRecord(
            entity_id=entity_id,
            kind_hint=normalize_kind_hint(row.get("kind_hint")),
            username=normalize_username(row.get("username")),
            title=normalize_text(row.get("title")),
            consent_confirmed=parse_bool(row.get("consent_confirmed"), default=False),
            allowed_actions=allowed_actions,
            notes=normalize_text(row.get("notes")),
        )
        if not record.username:
            raise ValueError(f"{path}: entity_id={entity_id} must have username")
        records[record.entity_id] = record
    return records


def load_actions(path: Path) -> list[ActionRecord]:
    actions: list[ActionRecord] = []
    for row in read_csv_rows(path):
        action_type = normalize_required(row.get("action_type"), "action_type", path)
        if action_type not in ALLOWED_ACTION_TYPES:
            raise ValueError(f"{path}: unsupported action_type={action_type}")
        actions.append(
            ActionRecord(
                action_id=normalize_required(row.get("action_id"), "action_id", path),
                action_type=action_type,
                account_id=normalize_required(row.get("account_id"), "account_id", path),
                target_entity_id=normalize_required(row.get("target_entity_id"), "target_entity_id", path),
                target_group_id=normalize_text(row.get("target_group_id")),
                message_text=normalize_multiline_text(row.get("message_text")),
                notes=normalize_text(row.get("notes")),
            )
        )
    return actions


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    try:
        import pandas as pd  # type: ignore
    except Exception:
        pd = None

    if pd is not None:
        frame = pd.read_csv(path, dtype=str).fillna("")
        return [
            {str(key): normalize_multiline_text(value) for key, value in row.items()}
            for row in frame.to_dict(orient="records")
        ]

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            {str(key): normalize_multiline_text(value) for key, value in row.items()}
            for row in reader
        ]


def normalize_required(value: str | None, field_name: str, path: Path) -> str:
    text = normalize_text(value)
    if not text:
        raise ValueError(f"{path}: missing required field {field_name}")
    return text


def normalize_text(value: str | None) -> str:
    return str(value or "").strip()


def normalize_multiline_text(value: str | None) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def parse_bool(value: str | None, *, default: bool) -> bool:
    text = normalize_text(value).lower()
    if not text:
        return default
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Unsupported boolean value: {value}")


def parse_csv_set(value: str | None) -> list[str]:
    text = normalize_text(value)
    if not text:
        return []
    items: list[str] = []
    seen: set[str] = set()
    for raw_item in re.split(r"[,\n;|]+", text):
        item = normalize_text(raw_item)
        if not item or item in seen:
            continue
        seen.add(item)
        items.append(item)
    return items


def normalize_username(value: str | None) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    if text.startswith("https://t.me/"):
        text = text.rsplit("/", 1)[-1]
    if not text.startswith("@"):
        text = f"@{text}"
    if not re.fullmatch(r"@[A-Za-z0-9_]{5,64}", text):
        raise ValueError(f"Unsupported Telegram username format: {value}")
    return text


def normalize_kind_hint(value: str | None) -> str:
    text = normalize_text(value).lower()
    return text or "unknown"
