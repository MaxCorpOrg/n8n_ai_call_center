#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

LEADS_HEADERS = [
    "created_at",
    "updated_at",
    "lead_id",
    "source_system",
    "source_record_key",
    "company_name",
    "contact_name",
    "phone_primary",
    "phone_secondary",
    "city",
    "segment",
    "lpr_role",
    "lpr_confirmed",
    "current_supplier",
    "current_product",
    "current_price",
    "pain_points",
    "objection_code",
    "objection_text",
    "interest_level",
    "call_result",
    "next_step",
    "next_call_at",
    "preferred_channel",
    "manager_owner",
    "expected_volume",
    "expected_budget",
    "material_sent",
    "followup_count",
    "max_touch_limit",
    "do_not_call",
    "final_reason",
    "notes_short",
    "notes_redacted",
    "call_record_url",
    "eleven_conv_id",
    "n8n_execution_id",
    "agent_version",
    "last_updated_by",
]

REF_ROWS = [
    ["dict_key", "value"],
    ["call_result", "order_test"],
    ["call_result", "manager_call"],
    ["call_result", "callback_scheduled"],
    ["call_result", "send_kp_pending_callback"],
    ["call_result", "refusal_soft"],
    ["call_result", "not_target"],
    ["call_result", "dnc"],
    ["call_result", "no_answer"],
    ["call_result", "busy"],
    ["next_step", "send_kp"],
    ["next_step", "call_manager"],
    ["next_step", "callback"],
    ["next_step", "close_won"],
    ["next_step", "close_lost"],
    ["next_step", "archive"],
    ["preferred_channel", "phone"],
    ["preferred_channel", "whatsapp"],
    ["preferred_channel", "telegram"],
    ["interest_level", "A"],
    ["interest_level", "B"],
    ["interest_level", "C"],
]


def http_json(url, method="GET", token=None, json_body=None):
    body = None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def http_form(url, form_data):
    body = urllib.parse.urlencode(form_data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.chmod(path, 0o600)


def build_auth_url(client):
    params = {
        "client_id": client["client_id"],
        "redirect_uri": client["redirect_uris"][0],
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }
    return f"{client['auth_uri']}?{urllib.parse.urlencode(params)}"


def exchange_code(client, code):
    token = http_form(
        client["token_uri"],
        {
            "code": code,
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": client["redirect_uris"][0],
            "grant_type": "authorization_code",
        },
    )
    token["expires_at"] = int(time.time()) + int(token.get("expires_in", 3600)) - 60
    return token


def refresh_token(client, refresh):
    token = http_form(
        client["token_uri"],
        {
            "refresh_token": refresh,
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "grant_type": "refresh_token",
        },
    )
    token["refresh_token"] = refresh
    token["expires_at"] = int(time.time()) + int(token.get("expires_in", 3600)) - 60
    return token


def ensure_access_token(client, token_path, auth_code=None):
    token = None
    if os.path.exists(token_path):
        token = load_json(token_path)

    if auth_code:
        token = exchange_code(client, auth_code)
        save_json(token_path, token)
        return token["access_token"], token

    if token and token.get("access_token") and int(token.get("expires_at", 0)) > int(time.time()):
        return token["access_token"], token

    if token and token.get("refresh_token"):
        token = refresh_token(client, token["refresh_token"])
        save_json(token_path, token)
        return token["access_token"], token

    raise RuntimeError("NO_TOKEN")


def create_sheet(access_token, title):
    spreadsheet = http_json(
        "https://sheets.googleapis.com/v4/spreadsheets",
        method="POST",
        token=access_token,
        json_body={
            "properties": {"title": title},
            "sheets": [
                {"properties": {"title": "Лиды_обзвон", "gridProperties": {"frozenRowCount": 1}}},
                {"properties": {"title": "Справочники"}},
            ],
        },
    )
    spreadsheet_id = spreadsheet["spreadsheetId"]

    http_json(
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values:batchUpdate",
        method="POST",
        token=access_token,
        json_body={
            "valueInputOption": "RAW",
            "data": [
                {"range": "Лиды_обзвон!A1", "majorDimension": "ROWS", "values": [LEADS_HEADERS]},
                {"range": "Справочники!A1", "majorDimension": "ROWS", "values": REF_ROWS},
            ],
        },
    )

    http_json(
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate",
        method="POST",
        token=access_token,
        json_body={
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": spreadsheet["sheets"][0]["properties"]["sheetId"],
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "textFormat": {"bold": True},
                                "backgroundColor": {"red": 0.92, "green": 0.95, "blue": 0.99},
                            }
                        },
                        "fields": "userEnteredFormat(textFormat,backgroundColor)",
                    }
                }
            ]
        },
    )

    return spreadsheet_id


def share_sheet(access_token, spreadsheet_id, email):
    http_json(
        f"https://www.googleapis.com/drive/v3/files/{spreadsheet_id}/permissions",
        method="POST",
        token=access_token,
        json_body={
            "type": "user",
            "role": "writer",
            "emailAddress": email,
        },
    )


def norm_phone(value):
    s = str(value or "").strip()
    if not s:
        return ""
    digits = re.sub(r"\D+", "", s)
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    return f"+{digits}" if len(digits) == 11 else ""


def load_seed_rows(seed_csv_path, limit=500):
    rows = []
    with open(seed_csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        idx = {name: i for i, name in enumerate(header)}
        phone_cols = [i for i, h in enumerate(header) if h == "Телефон"]

        def val(r, col, default=""):
            i = idx.get(col)
            if i is None or i >= len(r):
                return default
            return str(r[i] or "").strip()

        for row_num, r in enumerate(reader, start=2):
            company = val(r, "Наименование")
            if not company:
                continue
            phone1 = ""
            phone2 = ""
            if len(phone_cols) >= 1 and phone_cols[0] < len(r):
                phone1 = norm_phone(r[phone_cols[0]])
            if len(phone_cols) >= 2 and phone_cols[1] < len(r):
                phone2 = norm_phone(r[phone_cols[1]])
            city = val(r, "Город")
            segment = val(r, "Рубрики")
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            row = [
                now,  # created_at
                now,  # updated_at
                "",  # lead_id
                "xlsx_import",  # source_system
                f"row_{row_num}",  # source_record_key
                company,  # company_name
                "",  # contact_name
                phone1,  # phone_primary
                phone2,  # phone_secondary
                city,  # city
                segment,  # segment
                "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "0", "3", "false", "", "", "", "", "", "", "AI_CALL_AGENT_1", "system_seed",
            ]
            rows.append(row)
            if len(rows) >= limit:
                break
    return rows


def append_seed_rows(access_token, spreadsheet_id, seed_rows):
    if not seed_rows:
        return
    range_encoded = urllib.parse.quote("Лиды_обзвон!A2", safe="")
    http_json(
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_encoded}:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS",
        method="POST",
        token=access_token,
        json_body={"majorDimension": "ROWS", "values": seed_rows},
    )


def main():
    parser = argparse.ArgumentParser(description="Create call-center Google Sheet for LipoLong.")
    parser.add_argument(
        "--client-secret",
        default="/home/max/гугл/client_secret_565432086278-5cdudpbljg0ods2tlmj92n1kd06gkpkl.apps.googleusercontent.com.json",
    )
    parser.add_argument(
        "--token-path",
        default=os.path.expanduser("~/.openclaw/secrets/google_oauth_token.json"),
    )
    parser.add_argument("--auth-code", default="", help="Authorization code from redirect URL.")
    parser.add_argument("--title", default=f"LipoLong Call Log {time.strftime('%Y-%m-%d')}")
    parser.add_argument("--share-with", default="max.corp.org@gmail.com")
    parser.add_argument("--seed-csv", default="", help="Optional CSV with leads to prefill the first sheet.")
    parser.add_argument("--seed-limit", type=int, default=500)
    args = parser.parse_args()

    secret = load_json(args.client_secret)
    client = secret.get("web") or secret.get("installed")
    if not client:
        raise RuntimeError("client_secret json must contain 'web' or 'installed'")

    try:
        access_token, _ = ensure_access_token(client, args.token_path, args.auth_code or None)
    except RuntimeError as exc:
        if str(exc) != "NO_TOKEN":
            raise
        auth_url = build_auth_url(client)
        print("Требуется OAuth авторизация. Открой URL и затем запусти этот же скрипт с --auth-code:")
        print(auth_url)
        return 2

    spreadsheet_id = create_sheet(access_token, args.title)
    if args.share_with:
        share_sheet(access_token, spreadsheet_id, args.share_with)

    if args.seed_csv:
        rows = load_seed_rows(args.seed_csv, max(1, args.seed_limit))
        append_seed_rows(access_token, spreadsheet_id, rows)

    print("OK")
    print(f"spreadsheet_id={spreadsheet_id}")
    print(f"url=https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
