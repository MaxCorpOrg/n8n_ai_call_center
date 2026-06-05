#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cosmetologist_hunter_service import (
    DEFAULT_SHEET_NAME,
    DEFAULT_SOURCE_SPREADSHEET_ID,
    DEFAULT_TABLES_DIR,
    GoogleSheetsClient,
    LEADS_HEADERS,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FOLDER_ID = "1YguwTRirqR1KFzqTevqsEZzvtxksslUo"
CHAT_MARKERS = (
    "чат",
    "forum",
    "форум",
    "chat",
    "cosmetology_chat",
    "cosmetologi_chat",
    "chatkosmetologa",
)
ORG_MARKERS = (
    "ооо",
    "центр",
    "clinic",
    "клиника",
    "салон",
    "forum",
    "форум",
)


@dataclass
class ContactRow:
    phone: str
    username: str
    full_name: str
    first_seen_chat: str
    first_seen_target: str
    seen_in_chats: str
    seen_in_targets: str
    source_files: str


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def as_text(value: object) -> str:
    return str(value or "").strip()


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return ""
    if len(digits) == 11 and digits.startswith("8"):
        return "+7" + digits[1:]
    if len(digits) == 11 and digits.startswith("7"):
        return "+" + digits
    if len(digits) == 10:
        return "+7" + digits
    if 11 <= len(digits) <= 15:
        return "+" + digits
    return as_text(value)


def username_plain(username: str) -> str:
    text = as_text(username)
    if text in {"", "—", "-"}:
        return ""
    return text.lstrip("@")


def looks_like_chat_or_community(*parts: str) -> bool:
    haystack = " | ".join(as_text(part).lower() for part in parts)
    return any(marker in haystack for marker in CHAT_MARKERS)


def looks_like_org(*parts: str) -> bool:
    haystack = " | ".join(as_text(part).lower() for part in parts)
    return any(marker in haystack for marker in ORG_MARKERS)


def should_do_not_call(contact: ContactRow, phone: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not phone.startswith("+7"):
        reasons.append("номер не РФ")
    if phone.startswith("+7800"):
        reasons.append("номер 8-800")
    if looks_like_chat_or_community(
        contact.username,
        contact.full_name,
    ):
        reasons.append("похоже на чат/сообщество")
    if looks_like_org(contact.full_name):
        reasons.append("похоже на организацию")
    return (len(reasons) > 0, reasons)


def pick_company_name(contact: ContactRow) -> str:
    full_name = as_text(contact.full_name)
    if full_name:
        return full_name
    username = username_plain(contact.username)
    if username:
        return username
    return "Косметолог"


def pick_contact_name(contact: ContactRow) -> str:
    full_name = as_text(contact.full_name)
    if not full_name:
        return ""
    if looks_like_chat_or_community(full_name) or looks_like_org(full_name):
        return ""
    return full_name


def load_contacts(path: Path) -> list[ContactRow]:
    rows: list[ContactRow] = []
    with path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for item in reader:
            rows.append(
                ContactRow(
                    phone=as_text(item.get("phone")),
                    username=as_text(item.get("username")),
                    full_name=as_text(item.get("full_name")),
                    first_seen_chat=as_text(item.get("first_seen_chat")),
                    first_seen_target=as_text(item.get("first_seen_target")),
                    seen_in_chats=as_text(item.get("seen_in_chats")),
                    seen_in_targets=as_text(item.get("seen_in_targets")),
                    source_files=as_text(item.get("source_files")),
                )
            )
    return rows


def build_rows(contacts: list[ContactRow]) -> tuple[list[list[str]], list[dict[str, object]]]:
    timestamp = now_iso()
    rows: list[list[str]] = []
    preview: list[dict[str, object]] = []
    for row_idx, contact in enumerate(contacts, start=2):
        phone = normalize_phone(contact.phone)
        do_not_call, reasons = should_do_not_call(contact, phone)
        notes_short_parts = []
        if contact.first_seen_target:
            notes_short_parts.append(f"Источник: {contact.first_seen_target}")
        if reasons:
            notes_short_parts.append("Стоп: " + ", ".join(reasons))
        notes_short = " | ".join(notes_short_parts)
        notes_redacted = " | ".join(
            part
            for part in [
                f"username: {contact.username}" if contact.username else "",
                f"first_seen_chat: {contact.first_seen_chat}" if contact.first_seen_chat else "",
                f"seen_in_targets: {contact.seen_in_targets}" if contact.seen_in_targets else "",
                f"source_files: {contact.source_files}" if contact.source_files else "",
            ]
            if part
        )

        row_map = {header: "" for header in LEADS_HEADERS}
        row_map.update(
            {
                "created_at": timestamp,
                "updated_at": timestamp,
                "lead_id": "",
                "source_system": "xlsx_import",
                "source_record_key": f"row_{row_idx}",
                "company_name": pick_company_name(contact),
                "contact_name": pick_contact_name(contact),
                "phone_primary": phone,
                "phone_secondary": "",
                "city": "",
                "segment": "Частный косметолог",
                "lpr_role": "Косметолог",
                "lpr_confirmed": "false",
                "followup_count": "0",
                "max_touch_limit": "3",
                "do_not_call": "true" if do_not_call else "false",
                "notes_short": notes_short,
                "notes_redacted": notes_redacted,
                "agent_version": "AI_CALL_AGENT_1",
                "last_updated_by": "system_seed",
            }
        )
        rows.append([row_map.get(header, "") for header in LEADS_HEADERS])
        preview.append(
            {
                "row": row_idx,
                "phone_primary": phone,
                "company_name": row_map["company_name"],
                "contact_name": row_map["contact_name"],
                "do_not_call": do_not_call,
                "reasons": reasons,
            }
        )
    return rows, preview


def spreadsheet_sheet_gid(client: GoogleSheetsClient, spreadsheet_id: str, sheet_name: str) -> str:
    resp = client.request_with_auth(
        "GET",
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}",
        params={"fields": "sheets.properties(sheetId,title)"},
        timeout=60,
    )
    data = resp.json()
    for sheet in data.get("sheets", []):
        props = sheet.get("properties", {})
        if props.get("title") == sheet_name:
            return str(props.get("sheetId"))
    raise RuntimeError(f"Sheet {sheet_name!r} not found in spreadsheet {spreadsheet_id}")


def write_preview(preview: list[dict[str, object]], title: str) -> Path:
    runtime_dir = PROJECT_ROOT / ".runtime" / "contact_imports"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    preview_path = runtime_dir / f"{title}.preview.json"
    preview_path.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
    return preview_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Import tab-separated cosmetologist contacts into call-center sheet format.")
    parser.add_argument("--input", required=True, help="Path to source .txt file")
    parser.add_argument("--title", required=True, help="Google Sheet title to create")
    parser.add_argument("--drive-folder-id", default=DEFAULT_FOLDER_ID)
    parser.add_argument("--source-spreadsheet-id", default=DEFAULT_SOURCE_SPREADSHEET_ID)
    parser.add_argument("--sheet-name", default=DEFAULT_SHEET_NAME)
    parser.add_argument("--local-output-dir", default=str(DEFAULT_TABLES_DIR))
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    local_output_dir = Path(args.local_output_dir).expanduser().resolve()
    local_output_dir.mkdir(parents=True, exist_ok=True)

    contacts = load_contacts(input_path)
    rows, preview = build_rows(contacts)
    preview_path = write_preview(preview, args.title)

    google = GoogleSheetsClient(
        source_spreadsheet_id=args.source_spreadsheet_id,
        source_sheet_name=args.sheet_name,
        drive_folder_id=args.drive_folder_id,
    )
    spreadsheet_id = google.copy_sheet(args.title)
    google.clear_data_rows(spreadsheet_id, args.sheet_name)
    google.append_rows(spreadsheet_id, rows, args.sheet_name)

    local_xlsx = local_output_dir / f"{args.title}.xlsx"
    try:
        google.export_xlsx(spreadsheet_id, local_xlsx)
    except Exception as exc:
        raise RuntimeError(f"Failed to export xlsx copy: {exc}") from exc

    sheet_gid = spreadsheet_sheet_gid(google, spreadsheet_id, args.sheet_name)
    result = {
        "ok": True,
        "title": args.title,
        "input_path": str(input_path),
        "contacts_count": len(contacts),
        "spreadsheet_id": spreadsheet_id,
        "sheet_name": args.sheet_name,
        "sheet_gid": sheet_gid,
        "google_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit?gid={sheet_gid}#gid={sheet_gid}",
        "local_xlsx": str(local_xlsx),
        "preview_path": str(preview_path),
        "do_not_call_count": sum(1 for item in preview if item["do_not_call"]),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
