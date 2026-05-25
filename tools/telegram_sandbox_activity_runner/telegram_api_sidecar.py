#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import types
from pathlib import Path
from typing import Any


def normalize_space(value: Any) -> str:
    return str(value or "").strip()


def print_json(payload: dict[str, Any], *, stream=None) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=stream or sys.stdout)


def read_api_credentials(args: argparse.Namespace) -> tuple[int, str]:
    api_id_raw = normalize_space(os.environ.get(args.api_id_env))
    api_hash = normalize_space(os.environ.get(args.api_hash_env))
    if not api_id_raw or not api_hash:
        raise RuntimeError(
            f"Missing Telegram API credentials in env vars {args.api_id_env} / {args.api_hash_env}"
        )
    try:
        api_id = int(api_id_raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid api_id in {args.api_id_env}: {api_id_raw}") from exc
    return api_id, api_hash


def ensure_tgcrypto_compat() -> None:
    try:
        import tgcrypto  # type: ignore  # pragma: no cover - host-dependent fast path

        if getattr(tgcrypto, "ige256_encrypt", None) and getattr(tgcrypto, "ige256_decrypt", None):
            return
    except Exception:
        pass

    try:
        from telethon.crypto.aes import AES
    except Exception as exc:  # pragma: no cover - depends on host env
        raise RuntimeError(
            "Could not import tgcrypto and Telethon AES fallback is unavailable"
        ) from exc

    def to_bytes(value: Any) -> bytes:
        if isinstance(value, (bytes, bytearray)):
            return bytes(value)
        data = getattr(value, "data", None)
        if callable(data):
            return bytes(data())
        return bytes(value)

    shim = types.ModuleType("tgcrypto")
    shim.ige256_encrypt = lambda src, key, iv: AES.encrypt_ige(to_bytes(src), to_bytes(key), to_bytes(iv))
    shim.ige256_decrypt = lambda src, key, iv: AES.decrypt_ige(to_bytes(src), to_bytes(key), to_bytes(iv))
    sys.modules["tgcrypto"] = shim


def install_relaxed_opentele_reader(warnings: list[str]) -> None:
    import opentele.td.account as account_mod

    existing = getattr(account_mod.StorageAccount.readMapWith, "_tsar_relaxed", False)
    if existing:
        return

    def relaxed_read_map_with(self, localKey, legacyPasscode=account_mod.QByteArray()):
        try:
            self._StorageAccount__mapData.read(localKey, legacyPasscode)
        except BaseException as exc:
            warnings.append(str(exc))
        self.readMtpData()
        return True

    setattr(relaxed_read_map_with, "_tsar_relaxed", True)
    account_mod.StorageAccount.readMapWith = relaxed_read_map_with


async def build_client(args: argparse.Namespace):
    try:
        from telethon import TelegramClient
    except Exception as exc:  # pragma: no cover - depends on host env
        raise RuntimeError(f"telethon import failed: {exc}") from exc

    api_id, api_hash = read_api_credentials(args)
    session_file = Path(args.session_file).expanduser().resolve()
    session_file.parent.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(str(session_file), api_id, api_hash, timeout=int(args.connect_timeout))
    await client.connect()
    return client, session_file


async def command_status(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "ok": False,
        "command": "status",
        "api_id_env": args.api_id_env,
        "api_hash_env": args.api_hash_env,
        "session_file": str(Path(args.session_file).expanduser().resolve()),
        "session_exists": Path(args.session_file).expanduser().resolve().exists(),
    }
    client = None
    try:
        client, session_file = await build_client(args)
        payload["session_exists"] = session_file.exists()
        authorized = await client.is_user_authorized()
        payload["authorized"] = bool(authorized)
        if authorized:
            me = await client.get_me()
            payload["me"] = {
                "id": getattr(me, "id", None),
                "username": f"@{me.username}" if getattr(me, "username", None) else "",
                "first_name": getattr(me, "first_name", "") or "",
                "last_name": getattr(me, "last_name", "") or "",
                "phone": getattr(me, "phone", "") or "",
            }
        payload["ok"] = bool(authorized)
        payload["status"] = "authorized" if authorized else (
            "session_file_present_but_unauthorized" if payload["session_exists"] else "session_missing"
        )
        print_json(payload)
        return 0 if authorized else 1
    except Exception as exc:
        payload["status"] = "failed"
        payload["error"] = str(exc)
        print_json(payload)
        return 1
    finally:
        if client is not None:
            await client.disconnect()


async def command_check_contact(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "ok": False,
        "command": "check-contact",
        "username": normalize_space(args.username),
    }
    client = None
    try:
        from telethon import functions

        client, _session_file = await build_client(args)
        if not await client.is_user_authorized():
            raise RuntimeError("Telegram API session is not authorized")
        entity = await client.get_entity(payload["username"])
        contact_ids = await client(functions.contacts.GetContactIDsRequest(hash=0))
        payload.update(
            {
                "entity_id": getattr(entity, "id", None),
                "entity_username": f"@{entity.username}" if getattr(entity, "username", None) else payload["username"],
                "contact_present": bool(getattr(entity, "id", None) in set(contact_ids or [])),
                "ok": True,
                "status": "completed",
            }
        )
        print_json(payload)
        return 0
    except Exception as exc:
        payload["status"] = "failed"
        payload["error"] = str(exc)
        print_json(payload)
        return 1
    finally:
        if client is not None:
            await client.disconnect()


async def command_resolve_username(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "ok": False,
        "command": "resolve-username",
        "username": normalize_space(args.username),
    }
    client = None
    try:
        from telethon import types

        client, _session_file = await build_client(args)
        if not await client.is_user_authorized():
            raise RuntimeError("Telegram API session is not authorized")
        entity = await client.get_entity(payload["username"])
        entity_username = f"@{entity.username}" if getattr(entity, "username", None) else ""
        entity_type = type(entity).__name__
        payload.update(
            {
                "entity_id": getattr(entity, "id", None),
                "entity_username": entity_username,
                "entity_type": entity_type,
                "is_user": isinstance(entity, types.User),
                "is_bot": bool(getattr(entity, "bot", False)),
                "is_channel": isinstance(entity, types.Channel),
                "is_chat": isinstance(entity, types.Chat),
            }
        )
        if payload["is_user"]:
            payload["ok"] = True
            payload["status"] = "resolved_user"
            print_json(payload)
            return 0
        payload["status"] = "resolved_non_user"
        payload["error"] = f"Resolved entity is not a plain user: {entity_type}"
        print_json(payload)
        return 1
    except Exception as exc:
        message = str(exc)
        payload["status"] = "not_found" if "No user has" in message else "failed"
        payload["error"] = message
        print_json(payload)
        return 1
    finally:
        if client is not None:
            await client.disconnect()


async def command_add_contact(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "ok": False,
        "command": "add-contact",
        "username": normalize_space(args.username),
        "first_name": normalize_space(args.first_name),
        "last_name": normalize_space(args.last_name),
    }
    client = None
    try:
        from telethon import functions

        client, _session_file = await build_client(args)
        if not await client.is_user_authorized():
            raise RuntimeError("Telegram API session is not authorized")
        entity = await client.get_entity(payload["username"])
        contact_ids_before = set(await client(functions.contacts.GetContactIDsRequest(hash=0)) or [])
        payload["contact_present_before"] = bool(getattr(entity, "id", None) in contact_ids_before)
        if not payload["contact_present_before"]:
            await client(
                functions.contacts.AddContactRequest(
                    id=entity,
                    first_name=payload["first_name"] or payload["username"].lstrip("@"),
                    last_name=payload["last_name"],
                    phone="",
                    add_phone_privacy_exception=False,
                )
            )
        contact_ids_after = set(await client(functions.contacts.GetContactIDsRequest(hash=0)) or [])
        payload.update(
            {
                "entity_id": getattr(entity, "id", None),
                "entity_username": f"@{entity.username}" if getattr(entity, "username", None) else payload["username"],
                "contact_present_after": bool(getattr(entity, "id", None) in contact_ids_after),
                "ok": True,
                "status": "already_present" if payload["contact_present_before"] else "contact_added",
            }
        )
        print_json(payload)
        return 0 if payload["contact_present_after"] else 1
    except Exception as exc:
        payload["status"] = "failed"
        payload["error"] = str(exc)
        print_json(payload)
        return 1
    finally:
        if client is not None:
            await client.disconnect()


async def command_interactive_login(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "ok": False,
        "command": "interactive-login",
        "session_file": str(Path(args.session_file).expanduser().resolve()),
    }
    client = None
    try:
        from telethon import errors

        client, _session_file = await build_client(args)
        if await client.is_user_authorized():
            me = await client.get_me()
            payload["ok"] = True
            payload["status"] = "already_authorized"
            payload["me"] = {
                "id": getattr(me, "id", None),
                "username": f"@{me.username}" if getattr(me, "username", None) else "",
            }
            print_json(payload)
            return 0

        phone_number = normalize_space(args.phone_number) or normalize_space(input("Telegram phone number: "))
        if not phone_number:
            raise RuntimeError("Phone number is required for interactive-login")
        await client.send_code_request(phone_number)
        code = normalize_space(input("Telegram login code: "))
        try:
            await client.sign_in(phone=phone_number, code=code)
        except errors.SessionPasswordNeededError:
            password = input("Telegram 2FA password: ")
            await client.sign_in(password=password)
        me = await client.get_me()
        payload["ok"] = True
        payload["status"] = "authorized"
        payload["me"] = {
            "id": getattr(me, "id", None),
            "username": f"@{me.username}" if getattr(me, "username", None) else "",
        }
        print_json(payload)
        return 0
    except Exception as exc:
        payload["status"] = "failed"
        payload["error"] = str(exc)
        print_json(payload)
        return 1
    finally:
        if client is not None:
            await client.disconnect()


async def command_import_tdata_session(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "ok": False,
        "command": "import-tdata-session",
        "session_file": str(Path(args.session_file).expanduser().resolve()),
        "tdata_dir": str(Path(args.tdata_dir).expanduser().resolve()),
    }
    client = None
    try:
        ensure_tgcrypto_compat()
        from opentele.api import APIData, CreateNewSession
        from opentele.td import TDesktop

        warnings: list[str] = []
        install_relaxed_opentele_reader(warnings)
        api_id, api_hash = read_api_credentials(args)
        tdata_dir = Path(args.tdata_dir).expanduser().resolve()
        if not tdata_dir.is_dir():
            raise RuntimeError(f"Telegram Desktop tdata dir not found: {tdata_dir}")
        session_file = Path(args.session_file).expanduser().resolve()
        session_file.parent.mkdir(parents=True, exist_ok=True)
        api = APIData(
            api_id,
            api_hash,
            device_model=normalize_space(args.device_model) or "TSAR Sidecar",
            system_version=normalize_space(args.system_version) or "Ubuntu 24.04",
            app_version=normalize_space(args.app_version) or "1.0",
            lang_code="en",
            system_lang_code="en",
            lang_pack="",
        )
        tdesk = TDesktop(str(tdata_dir), passcode=normalize_space(args.desktop_passcode) or None)
        payload["accounts_count"] = int(getattr(tdesk, "accountsCount", 0) or 0)
        if warnings:
            payload["warnings"] = warnings
        client = await tdesk.ToTelethon(
            session=str(session_file),
            flag=CreateNewSession,
            api=api,
        )
        await client.connect()
        authorized = await client.is_user_authorized()
        payload["authorized"] = bool(authorized)
        if not authorized:
            raise RuntimeError("Telethon session was created but is not authorized")
        me = await client.get_me()
        payload["me"] = {
            "id": getattr(me, "id", None),
            "username": f"@{me.username}" if getattr(me, "username", None) else "",
            "first_name": getattr(me, "first_name", "") or "",
            "last_name": getattr(me, "last_name", "") or "",
            "phone": getattr(me, "phone", "") or "",
        }
        payload["ok"] = True
        payload["status"] = "authorized"
        print_json(payload)
        return 0
    except Exception as exc:
        payload["status"] = "failed"
        payload["error"] = str(exc)
        print_json(payload)
        return 1
    finally:
        if client is not None:
            await client.disconnect()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Telegram API sidecar for fast resolve/add contact operations.")
    parser.add_argument("--api-id-env", required=True, help="Environment variable that stores api_id")
    parser.add_argument("--api-hash-env", required=True, help="Environment variable that stores api_hash")
    parser.add_argument("--session-file", required=True, help="Path to Telethon session file")
    parser.add_argument("--connect-timeout", type=int, default=15, help="Telethon connect timeout")

    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Check whether the API session is authorized")
    status_parser.set_defaults(func=command_status)

    check_parser = subparsers.add_parser("check-contact", help="Verify whether a username is already present in contacts")
    check_parser.add_argument("--username", required=True, help="Telegram username to verify")
    check_parser.set_defaults(func=command_check_contact)

    resolve_parser = subparsers.add_parser("resolve-username", help="Resolve a username and classify the Telegram entity type")
    resolve_parser.add_argument("--username", required=True, help="Telegram username to resolve")
    resolve_parser.set_defaults(func=command_resolve_username)

    add_parser = subparsers.add_parser("add-contact", help="Resolve a username and add it into contacts via Telegram API")
    add_parser.add_argument("--username", required=True, help="Telegram username to add")
    add_parser.add_argument("--first-name", default="", help="First name to store in contacts")
    add_parser.add_argument("--last-name", default="", help="Last name to store in contacts")
    add_parser.set_defaults(func=command_add_contact)

    login_parser = subparsers.add_parser("interactive-login", help="Initialize or refresh the Telethon session interactively")
    login_parser.add_argument("--phone-number", default="", help="Optional phone number for authorization")
    login_parser.set_defaults(func=command_interactive_login)

    import_tdata_parser = subparsers.add_parser(
        "import-tdata-session",
        help="Create or refresh a Telethon session from an existing Telegram Desktop tdata directory",
    )
    import_tdata_parser.add_argument("--tdata-dir", required=True, help="Path to Telegram Desktop tdata directory")
    import_tdata_parser.add_argument("--desktop-passcode", default="", help="Optional local passcode used by Telegram Desktop")
    import_tdata_parser.add_argument("--device-model", default="", help="Optional device model label for the new API session")
    import_tdata_parser.add_argument("--system-version", default="", help="Optional system version label for the new API session")
    import_tdata_parser.add_argument("--app-version", default="", help="Optional app version label for the new API session")
    import_tdata_parser.set_defaults(func=command_import_tdata_session)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(asyncio.run(args.func(args)))


if __name__ == "__main__":
    raise SystemExit(main())
