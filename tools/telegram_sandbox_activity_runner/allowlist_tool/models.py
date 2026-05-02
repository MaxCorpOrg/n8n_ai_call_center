from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any


ALLOWED_ACTION_TYPES = {"validate", "send_message", "add_to_group"}


@dataclass(frozen=True)
class AccountRecord:
    account_id: str
    session_file: Path
    api_id_env: str
    api_hash_env: str
    enabled: bool = True
    label: str = ""


@dataclass(frozen=True)
class AllowlistRecord:
    entity_id: str
    kind_hint: str
    username: str
    title: str
    consent_confirmed: bool
    allowed_actions: frozenset[str]
    notes: str = ""


@dataclass(frozen=True)
class ActionRecord:
    action_id: str
    action_type: str
    account_id: str
    target_entity_id: str
    target_group_id: str = ""
    message_text: str = ""
    notes: str = ""


@dataclass(frozen=True)
class QueuedAction:
    action_id: str
    action_type: str
    account_id: str
    target_entity_id: str
    target_group_id: str = ""
    message_text: str = ""
    status: str = "pending"
    block_reason: str = ""
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionResult:
    action_id: str
    action_type: str
    account_id: str
    status: str
    outcome: str
    target_entity_id: str = ""
    target_group_id: str = ""
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return to_serializable(asdict(self))


def to_serializable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return to_serializable(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_serializable(item) for item in value]
    if isinstance(value, set):
        return sorted(to_serializable(item) for item in value)
    return value
