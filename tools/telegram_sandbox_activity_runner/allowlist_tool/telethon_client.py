from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from .models import AccountRecord


@dataclass(frozen=True)
class TelethonRuntime:
    client: Any
    functions: Any
    types: Any
    errors: Any


def load_telethon_runtime() -> tuple[Any, Any, Any, Any]:
    try:
        from telethon import errors, functions, types  # type: ignore
        from telethon.sync import TelegramClient  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"telethon import failed: {exc}") from exc
    return TelegramClient, functions, types, errors


@contextmanager
def open_telethon_client(account: AccountRecord) -> Iterator[TelethonRuntime]:
    telegram_client_cls, functions, types, errors = load_telethon_runtime()
    api_id = resolve_required_int_env(account.api_id_env)
    api_hash = resolve_required_text_env(account.api_hash_env)

    session_file = Path(account.session_file).expanduser().resolve()
    session_file.parent.mkdir(parents=True, exist_ok=True)
    client = telegram_client_cls(str(session_file), api_id, api_hash)
    client.connect()
    try:
        if not client.is_user_authorized():
            raise RuntimeError(
                f"Telethon session is not authorized for account {account.account_id}. "
                f"Initialize it manually before running this CLI."
            )
        yield TelethonRuntime(client=client, functions=functions, types=types, errors=errors)
    finally:
        client.disconnect()


def resolve_required_int_env(name: str) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer.") from exc


def resolve_required_text_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
