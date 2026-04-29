#!/usr/bin/env python3
import argparse
import email
import imaplib
import json
import mimetypes
import os
import re
import smtplib
import socket
import ssl
import time
import urllib.parse
from email.message import EmailMessage
from email import policy
from email.utils import formataddr
from html import unescape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ATTACHMENT_FALLBACK = (
    PROJECT_ROOT / "Документация по скриптам " / "КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ (2).pdf"
)


def load_env_file_if_exists(path):
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


for candidate in (PROJECT_ROOT / ".env.email_followup", Path.cwd() / ".env.email_followup"):
    load_env_file_if_exists(candidate)


DEFAULT_PORT = int(os.getenv("EMAIL_FOLLOWUP_PORT", "8791").strip() or "8791")
DEFAULT_HOST = os.getenv("EMAIL_FOLLOWUP_HOST", "127.0.0.1").strip() or "127.0.0.1"
DEFAULT_SHEET_PREFIX = os.getenv(
    "EMAIL_FOLLOWUP_SHEET_PREFIX", "контакты_косметологов_москва_"
).strip() or "контакты_косметологов_москва_"
DEFAULT_SHEET_NAME = os.getenv("EMAIL_FOLLOWUP_SHEET_NAME", "Лиды_обзвон").strip() or "Лиды_обзвон"
DEFAULT_DRIVE_FOLDER_ID = os.getenv("EMAIL_FOLLOWUP_DRIVE_FOLDER_ID", "").strip()
DEFAULT_FIRECRAWL_BASE_URL = (
    os.getenv("EMAIL_FOLLOWUP_FIRECRAWL_BASE_URL", "").strip()
    or os.getenv("COSMETOLOGIST_HUNTER_FIRECRAWL_BASE_URL", "").strip()
)
DEFAULT_FIRECRAWL_API_KEY = (
    os.getenv("EMAIL_FOLLOWUP_FIRECRAWL_API_KEY", "").strip()
    or os.getenv("COSMETOLOGIST_HUNTER_FIRECRAWL_API_KEY", "").strip()
)
DEFAULT_MAX_SHEETS_PER_RUN = int(os.getenv("EMAIL_FOLLOWUP_MAX_SHEETS_PER_RUN", "25").strip() or "25")
DEFAULT_MAX_RECORDS_PER_RUN = int(os.getenv("EMAIL_FOLLOWUP_MAX_RECORDS_PER_RUN", "20").strip() or "20")
DEFAULT_REQUEST_TIMEOUT = int(os.getenv("EMAIL_FOLLOWUP_HTTP_TIMEOUT_SEC", "15").strip() or "15")
RESOLVER_TOTAL_TIMEOUT = int(
    os.getenv("EMAIL_FOLLOWUP_RESOLVER_TOTAL_TIMEOUT_SEC", "25").strip() or "25"
)
RESOLVER_SEARCH_LIMIT = int(os.getenv("EMAIL_FOLLOWUP_RESOLVER_SEARCH_LIMIT", "4").strip() or "4")
RESOLVER_MAX_VISITS = int(os.getenv("EMAIL_FOLLOWUP_RESOLVER_MAX_VISITS", "4").strip() or "4")
RESOLVER_CONTACT_URL_LIMIT = int(
    os.getenv("EMAIL_FOLLOWUP_RESOLVER_CONTACT_URL_LIMIT", "4").strip() or "4"
)
DEFAULT_PRODUCT_NAME = os.getenv("EMAIL_FOLLOWUP_PRODUCT_NAME", "LipoLong").strip() or "LipoLong"
DEFAULT_PRODUCT_SITE = os.getenv("EMAIL_FOLLOWUP_PRODUCT_SITE", "https://lipolong.com").strip() or "https://lipolong.com"
DEFAULT_MATERIAL_URL = (
    os.getenv("EMAIL_FOLLOWUP_MATERIAL_URL", "").strip() or DEFAULT_PRODUCT_SITE
)
DEFAULT_MANAGER_PHONE = os.getenv("EMAIL_FOLLOWUP_MANAGER_PHONE", "8 999 556-67-77").strip() or "8 999 556-67-77"
DEFAULT_MANAGER_TELEGRAM = (
    os.getenv("EMAIL_FOLLOWUP_MANAGER_TELEGRAM", "@Vorgesar_Peptides").strip() or "@Vorgesar_Peptides"
)
DEFAULT_ATTACHMENT_PATH = (
    os.getenv("EMAIL_FOLLOWUP_ATTACHMENT_PATH", "").strip()
    or str(DEFAULT_ATTACHMENT_FALLBACK)
)
DEFAULT_ATTACHMENT_NAME = (
    os.getenv("EMAIL_FOLLOWUP_ATTACHMENT_NAME", "").strip()
    or Path(DEFAULT_ATTACHMENT_PATH).name
)
DEFAULT_SPREADSHEET_IDS = []
DEFAULT_REPLY_TO = os.getenv("EMAIL_FOLLOWUP_REPLY_TO", "").strip()
DEFAULT_SUBJECT_TEMPLATE = (
    os.getenv("EMAIL_FOLLOWUP_SUBJECT_TEMPLATE", "Информация по {product_name} для {company_name}").strip()
    or "Информация по {product_name} для {company_name}"
)
DEFAULT_IMAP_HOST = os.getenv("EMAIL_FOLLOWUP_IMAP_HOST", "imap.gmail.com").strip() or "imap.gmail.com"
DEFAULT_IMAP_PORT = int(os.getenv("EMAIL_FOLLOWUP_IMAP_PORT", "993").strip() or "993")
DEFAULT_IMAP_USERNAME = (
    os.getenv("EMAIL_FOLLOWUP_IMAP_USERNAME", "").strip()
    or os.getenv("EMAIL_FOLLOWUP_SMTP_USERNAME", "").strip()
)
DEFAULT_IMAP_PASSWORD = (
    os.getenv("EMAIL_FOLLOWUP_IMAP_PASSWORD", "").strip()
    or os.getenv("EMAIL_FOLLOWUP_SMTP_PASSWORD", "").strip()
)
DEFAULT_IMAP_MAILBOX = os.getenv("EMAIL_FOLLOWUP_IMAP_MAILBOX", "INBOX").strip() or "INBOX"
DEFAULT_BOUNCE_SCAN_LIMIT = int(os.getenv("EMAIL_FOLLOWUP_BOUNCE_SCAN_LIMIT", "40").strip() or "40")
DEFAULT_BOUNCE_STATE_PATH = (
    os.getenv("EMAIL_FOLLOWUP_BOUNCE_STATE_PATH", "").strip()
    or str(PROJECT_ROOT / ".runtime" / "email_followup_bounce_state.json")
)
DEFAULT_DOMAIN_BLACKLIST_PATH = (
    os.getenv("EMAIL_FOLLOWUP_DOMAIN_BLACKLIST_PATH", "").strip()
    or str(PROJECT_ROOT / ".runtime" / "email_followup_domain_blacklist.json")
)
DEFAULT_TELEGRAM_BOT_TOKEN = os.getenv("EMAIL_FOLLOWUP_TELEGRAM_BOT_TOKEN", "").strip()
DEFAULT_TELEGRAM_API_BASE = (
    os.getenv("EMAIL_FOLLOWUP_TELEGRAM_API_BASE", "https://api.telegram.org").strip().rstrip("/")
    or "https://api.telegram.org"
)
DEFAULT_TELEGRAM_CHAT_ID = os.getenv("EMAIL_FOLLOWUP_TELEGRAM_CHAT_ID", "").strip()
DEFAULT_TELEGRAM_THREAD_ID = os.getenv("EMAIL_FOLLOWUP_TELEGRAM_THREAD_ID", "").strip()
DEFAULT_TELEGRAM_REPORTS_ENABLED = os.getenv("EMAIL_FOLLOWUP_TELEGRAM_REPORTS_ENABLED", "false").strip()
DEFAULT_TELEGRAM_REPORT_ON_EMPTY = os.getenv("EMAIL_FOLLOWUP_TELEGRAM_REPORT_ON_EMPTY", "false").strip()
DEFAULT_USE_JINA_SEARCH_FALLBACK = os.getenv("EMAIL_FOLLOWUP_USE_JINA_SEARCH_FALLBACK", "true").strip()
DEFAULT_INFER_EMAIL_FROM_DOMAIN = os.getenv("EMAIL_FOLLOWUP_INFER_EMAIL_FROM_DOMAIN", "true").strip()
JINA_DDG_SEARCH_PREFIX = "https://r.jina.ai/http://duckduckgo.com/html/?q="
INFERRED_EMAIL_LOCALS = ("info", "contact", "mail", "office")

TRUTHY = {"1", "true", "yes", "y", "on", "да"}
DNS_CHECK_TIMEOUT = 8
DNS_CACHE = {}
EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.IGNORECASE)
SEARCH_RESULT_LINK_PATTERN = re.compile(
    r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"', re.IGNORECASE
)
HREF_PATTERN = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
EMAIL_SIGNAL_PATTERN = re.compile(r"(почт|e-mail|email|на\s+почту|mail)", re.IGNORECASE)
TWO_GIS_FIRM_LINK_PATTERN = re.compile(r'href=["\'](/[^"\']+/firm/\d+[^"\']*)["\']', re.IGNORECASE)
DIRECTORY_HOSTS = {
    "2gis.ru",
    "avito.ru",
    "docdoc.ru",
    "doct.ru",
    "dreamjob.ru",
    "flamp.ru",
    "hh.ru",
    "joblab.ru",
    "napopravku.ru",
    "prodoctorov.ru",
    "rabota.ru",
    "spr.ru",
    "superjob.ru",
    "taplink.ws",
    "www.2gis.ru",
    "yandex.ru",
    "yandex.com",
    "yandex.by",
    "maps.yandex.ru",
    "yandex.com.tr",
    "zoon.ru",
    "yell.ru",
    "youla.ru",
    "zarplata.ru",
    "vk.com",
    "t.me",
    "taplink.ws",
    "telegram.me",
    "wa.me",
    "whatsapp.com",
    "instagram.com",
    "facebook.com",
    "ok.ru",
    "taplink.ws",
    "yclients.com",
}
PROTECTED_PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yandex.ru",
    "yandex.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "mail.ru",
    "bk.ru",
    "inbox.ru",
    "list.ru",
    "icloud.com",
}
PLACEHOLDER_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "yourdomain.com",
    "your-company.com",
    "yourcompany.com",
    "domain.com",
}
EXCLUDED_EMAIL_ROOT_DOMAINS = {
    "2gis.ru",
    "avito.ru",
    "docdoc.ru",
    "doct.ru",
    "dreamjob.ru",
    "facebook.com",
    "flamp.ru",
    "hh.ru",
    "instagram.com",
    "joblab.ru",
    "napopravku.ru",
    "ok.ru",
    "prodoctorov.ru",
    "rabota.ru",
    "spr.ru",
    "superjob.ru",
    "taplink.ws",
    "telegram.me",
    "t.me",
    "vk.com",
    "wa.me",
    "whatsapp.com",
    "yclients.com",
    "yell.ru",
    "youla.ru",
    "zarplata.ru",
    "zoon.ru",
}
SUSPICIOUS_EMAIL_LOCALPART_TOKENS = (
    "bounce",
    "do-not-reply",
    "donotreply",
    "mailer-daemon",
    "no-reply",
    "noreply",
    "notification",
    "notifications",
    "postmaster",
    "robot",
    "sentry",
)
GARBAGE_PHONE_VALUES = {
    "system__called_number",
    "алло",
    "алло!",
    "алло, здравствуйте",
    "алло, здравствуйте!",
}
PLACEHOLDER_COMPANY_NAMES = {
    "delete",
    "deleted",
    "test",
    "none",
    "null",
    "n/a",
    "na",
    "тест",
    "удалить",
    "удалено",
}
EXTRA_HEADERS = [
    "contact_email",
    "email_source_url",
    "email_verified_at",
    "email_verification_status",
    "email_send_status",
    "email_sent_at",
    "email_sent_to",
    "email_last_error",
    "email_bounced_at",
    "email_bounce_reason",
    "email_blacklisted_at",
    "email_blacklist_reason",
]
STATE_OVERRIDE_FIELDS = {
    "contact_email",
    "email_source_url",
    "email_verified_at",
    "email_verification_status",
    "email_send_status",
    "email_sent_at",
    "email_sent_to",
    "email_last_error",
    "email_bounced_at",
    "email_bounce_reason",
    "email_blacklisted_at",
    "email_blacklist_reason",
}
FATAL_BOUNCE_TYPES = {
    "domain_not_found",
    "mailbox_not_found",
    "policy_blocked",
}
SEED_SYNC_HEADERS = [
    "contact_email",
    "email_source_url",
    "email_verified_at",
    "email_verification_status",
]


def default_google_source_candidates():
    return [
        os.getenv("GOOGLE_OAUTH_SOURCE_JSON", ""),
        str(PROJECT_ROOT / "backups" / "2026-04-07_human_gate_autodial_refresh" / "autodial_live_after.json"),
        str(PROJECT_ROOT / "backups" / "2026-04-06_live_autodial_gid_sync" / "call_log_before_20260406_154135.json"),
    ]


def extract_google_oauth_from_text(text):
    client_id = re.search(r"client_id:\s*'([^']+)'", text)
    client_secret = re.search(r"client_secret:\s*'([^']+)'", text)
    refresh_token = re.search(r"refresh_token:\s*'([^']+)'", text)
    if not (client_id and client_secret and refresh_token):
        return None
    return {
        "client_id": client_id.group(1),
        "client_secret": client_secret.group(1),
        "refresh_token": refresh_token.group(1),
    }


def load_google_oauth():
    direct = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", "").strip(),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", "").strip(),
        "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN", "").strip(),
    }
    if all(direct.values()):
        return direct

    for candidate in default_google_source_candidates():
        if not candidate:
            continue
        path = Path(candidate)
        if not path.exists():
            continue
        creds = extract_google_oauth_from_text(path.read_text(encoding="utf-8", errors="ignore"))
        if creds:
            return creds

    raise RuntimeError(
        "Не найдены Google OAuth credentials. Задайте GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REFRESH_TOKEN."
    )


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def as_bool(value):
    return str(value or "").strip().lower() in TRUTHY


def parse_csv_list(value):
    return [item for item in (part.strip() for part in re.split(r"[\n,;]+", str(value or ""))) if item]


DEFAULT_SPREADSHEET_IDS = parse_csv_list(os.getenv("EMAIL_FOLLOWUP_SPREADSHEET_IDS", ""))


def normalize_phone(value):
    digits = re.sub(r"\D+", "", str(value or ""))
    if not digits:
        return ""
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 11 and digits.startswith("7"):
        return "+" + digits
    if 11 <= len(digits) <= 15:
        return "+" + digits
    return ""


def phone_search_variants(value):
    normalized = normalize_phone(value)
    if not normalized:
        return []
    digits = re.sub(r"\D+", "", normalized)
    variants = [normalized, digits]
    if len(digits) == 11 and digits.startswith("7"):
        local = digits[1:]
        variants.extend(
            [
                local,
                f"8{local}",
                f"+7 ({local[:3]}) {local[3:6]}-{local[6:8]}-{local[8:10]}",
                f"8 ({local[:3]}) {local[3:6]}-{local[6:8]}-{local[8:10]}",
            ]
        )
    return dedupe_keep_order([item for item in variants if item])


def is_garbage_phone_value(value):
    raw = str(value or "").strip().lower()
    if not raw:
        return True
    if raw in GARBAGE_PHONE_VALUES:
        return True
    if raw.startswith("system__"):
        return True
    if raw in {"-", "—", "нет", "none", "null", "n/a"}:
        return True
    return False


def normalize_email_candidate(value):
    text = unescape(str(value or ""))
    replacements = {
        "[at]": "@",
        "(at)": "@",
        "{at}": "@",
        " собака ": "@",
        " dog ": "@",
        "[dot]": ".",
        "(dot)": ".",
        "{dot}": ".",
    }
    lowered = text
    for old, new in replacements.items():
        lowered = re.sub(re.escape(old), new, lowered, flags=re.IGNORECASE)
    lowered = re.sub(r"\s*@\s*", "@", lowered)
    lowered = re.sub(r"\s*\.\s*", ".", lowered)
    lowered = re.sub(r"mailto:", "", lowered, flags=re.IGNORECASE)
    lowered = re.sub(r"@([A-Za-z0-9.\-]+),([A-Za-z]{2,})\b", r"@\1.\2", lowered)
    lowered = lowered.strip().strip("<>").strip("\"' ,;")
    return lowered


def extract_emails(text):
    normalized = normalize_email_candidate(text)
    found = []
    seen = set()
    for match in EMAIL_PATTERN.finditer(normalized):
        candidate = match.group(0).strip().lower()
        candidate = candidate.rstrip(".,;:")
        if candidate in seen:
            continue
        if not is_valid_email(candidate):
            continue
        seen.add(candidate)
        found.append(candidate)
    return found


def is_valid_email(email):
    if not email:
        return False
    if ".." in email:
        return False
    return bool(EMAIL_PATTERN.fullmatch(email.strip()))


def is_placeholder_email(email):
    domain = email_domain(email)
    if not domain:
        return True
    if domain in PLACEHOLDER_EMAIL_DOMAINS:
        return True
    compact = re.sub(r"[^a-z0-9]+", "", domain.lower())
    if any(token in compact for token in ("example", "yourdomain", "yourcompany")):
        return True
    return False


def is_excluded_business_email(email):
    clean = normalize_email_candidate(email).lower()
    if not clean or "@" not in clean:
        return True
    local_part, _, domain = clean.partition("@")
    root_domain = approx_root_domain(domain)
    if root_domain in EXCLUDED_EMAIL_ROOT_DOMAINS:
        return True
    if any(token in local_part for token in SUSPICIOUS_EMAIL_LOCALPART_TOKENS):
        return True
    return False


def email_domain(email):
    _, _, domain = str(email or "").strip().rpartition("@")
    return domain.strip().lower().strip(".")


def resolve_domain_via_doh(domain):
    cached = DNS_CACHE.get(domain)
    if cached:
        return cached
    endpoint = "https://dns.google/resolve"
    answers_by_type = {}
    saw_nxdomain = False
    for record_type in ("MX", "A", "AAAA"):
        try:
            response = requests.get(
                endpoint,
                params={"name": domain, "type": record_type},
                timeout=DNS_CHECK_TIMEOUT,
            )
            response.raise_for_status()
            body = response.json()
        except Exception:
            answers_by_type[record_type] = None
            continue
        status = body.get("Status")
        answers = body.get("Answer") or []
        if status == 3:
            saw_nxdomain = True
        answers_by_type[record_type] = answers
    result = {
        "mx": bool(answers_by_type.get("MX")),
        "a": bool(answers_by_type.get("A")),
        "aaaa": bool(answers_by_type.get("AAAA")),
        "nxdomain": saw_nxdomain,
    }
    DNS_CACHE[domain] = result
    return result


def check_email_domain_resolves(email):
    domain = email_domain(email)
    if not domain:
        return False, "empty_domain"
    doh = resolve_domain_via_doh(domain)
    if doh["mx"] or doh["a"] or doh["aaaa"]:
        return True, ""
    if doh["nxdomain"]:
        return False, "domain_not_found"
    try:
        socket.getaddrinfo(domain, None)
        return True, ""
    except socket.gaierror:
        return False, "domain_not_found"
    except Exception:
        return False, "domain_lookup_failed"


def resolver_deadline(timeout_seconds):
    return time.monotonic() + max(int(timeout_seconds or 0), 1)


def remaining_seconds(deadline):
    return max(0.0, float(deadline or 0) - time.monotonic())


def request_timeout_for(deadline, fallback):
    remaining = remaining_seconds(deadline)
    if remaining <= 0:
        return 0
    return max(3, min(int(fallback or DEFAULT_REQUEST_TIMEOUT), int(remaining) or 1))


def ensure_parent_dir(path):
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def load_json_file(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json_file(path, data):
    ensure_parent_dir(path)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def html_to_text(value):
    text = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", " ", str(value or ""))
    text = re.sub(r"(?i)<br\\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_company_name(value):
    return re.sub(r"[^a-zа-я0-9]+", "", str(value or "").lower())


def company_search_aliases(value):
    raw = str(value or "").strip()
    if not raw:
        return []
    aliases = []
    for separator in (",", ";", "/", "|"):
        if separator in raw:
            aliases.append(raw.split(separator, 1)[0].strip())
    for separator in (" — ", " – ", " - "):
        if separator in raw:
            aliases.append(raw.split(separator, 1)[0].strip())
    aliases.append(raw)
    result = []
    seen = set()
    for item in aliases:
        normalized = normalize_company_name(item)
        if len(normalized) < 4:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(item.strip())
    return result


def company_match_keys(value):
    return [normalize_company_name(item) for item in company_search_aliases(value)]


PLACEHOLDER_COMPANY_NAMES_NORMALIZED = {
    normalize_company_name(item) for item in PLACEHOLDER_COMPANY_NAMES
}


def dedupe_keep_order(values):
    result = []
    seen = set()
    for item in values:
        key = str(item or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(key)
    return result


def is_placeholder_company_name(value):
    raw = str(value or "").strip().lower()
    normalized = normalize_company_name(value)
    if not raw and not normalized:
        return False
    if raw in PLACEHOLDER_COMPANY_NAMES:
        return True
    if normalized in PLACEHOLDER_COMPANY_NAMES_NORMALIZED:
        return True
    if normalized.startswith("delete") or normalized.startswith("тест"):
        return True
    return False


def to_column_letter(index):
    value = int(index)
    if value <= 0:
        raise ValueError("Column index must be positive")
    chars = []
    while value > 0:
        value, remainder = divmod(value - 1, 26)
        chars.append(chr(65 + remainder))
    return "".join(reversed(chars))


def approx_root_domain(hostname):
    host = str(hostname or "").lower().strip(".")
    if not host:
        return ""
    parts = [part for part in host.split(".") if part]
    if len(parts) <= 2:
        return host
    return ".".join(parts[-2:])


def clean_url(url):
    value = str(url or "").strip()
    if not value:
        return ""
    if value.startswith("//"):
        return "https:" + value
    if not re.match(r"^https?://", value, flags=re.IGNORECASE):
        value = "https://" + value
    return value


def host_matches(hostname, host_set):
    host = str(hostname or "").strip().lower().split(":", 1)[0]
    if not host:
        return False
    for entry in host_set:
        target = str(entry or "").strip().lower()
        if not target:
            continue
        if host == target or host.endswith("." + target):
            return True
    return False


class FirecrawlClient:
    def __init__(self, base_url="", api_key=""):
        self.base_url = str(base_url or "").rstrip("/")
        self.api_key = str(api_key or "").strip()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def enabled(self):
        return bool(self.base_url)

    def scrape_html(self, url, timeout=45):
        if not self.enabled():
            return ""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "url": url,
            "formats": ["rawHtml", "html"],
            "onlyMainContent": False,
            "waitFor": 1500,
            "timeout": int(timeout * 1000),
        }
        try:
            response = self.session.post(
                f"{self.base_url}/v2/scrape",
                headers=headers,
                json=payload,
                timeout=max(timeout, 15),
            )
            response.raise_for_status()
            body = response.json()
        except Exception:
            return ""
        data = body.get("data") or {}
        return str(data.get("rawHtml") or data.get("html") or "")


class GoogleSheetsClient:
    def __init__(self, drive_folder_id=""):
        self.drive_folder_id = str(drive_folder_id or "").strip()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})
        self._access_token = None

    def access_token(self):
        if self._access_token:
            return self._access_token
        creds = load_google_oauth()
        response = self.session.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
                "refresh_token": creds["refresh_token"],
                "grant_type": "refresh_token",
            },
            timeout=60,
        )
        response.raise_for_status()
        self._access_token = response.json()["access_token"]
        return self._access_token

    def refresh_access_token(self):
        self._access_token = None
        return self.access_token()

    def request_with_auth(self, method, url, *, json_body=False, retry_on_auth=True, **kwargs):
        headers = dict(kwargs.pop("headers", {}) or {})
        headers["Authorization"] = f"Bearer {self.access_token()}"
        if json_body:
            headers["Content-Type"] = "application/json"
        response = self.session.request(method, url, headers=headers, **kwargs)
        if retry_on_auth and response.status_code in {401, 403}:
            self.refresh_access_token()
            headers["Authorization"] = f"Bearer {self.access_token()}"
            response = self.session.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    def list_prefixed_sheets(self, title_prefix, limit=100):
        query_parts = [
            "mimeType='application/vnd.google-apps.spreadsheet'",
            f"name contains '{title_prefix}'",
            "trashed=false",
        ]
        if self.drive_folder_id:
            query_parts.append(f"'{self.drive_folder_id}' in parents")
        response = self.request_with_auth(
            "GET",
            "https://www.googleapis.com/drive/v3/files",
            params={
                "q": " and ".join(query_parts),
                "fields": "files(id,name,createdTime,modifiedTime)",
                "pageSize": min(max(int(limit or 100), 1), 200),
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            },
            timeout=60,
        )
        items = response.json().get("files") or []
        return sorted(items, key=lambda item: (item.get("name", ""), item.get("createdTime", "")))

    def get_drive_file(self, file_id):
        response = self.request_with_auth(
            "GET",
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={
                "fields": "id,name,createdTime,modifiedTime",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            },
            timeout=60,
        )
        return response.json()

    def get_spreadsheet_metadata(self, spreadsheet_id):
        response = self.request_with_auth(
            "GET",
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}",
            params={"fields": "sheets.properties(sheetId,title,index,hidden)"},
            timeout=60,
        )
        return response.json()

    def resolve_sheet_name(self, spreadsheet_id, preferred_sheet_name):
        metadata = self.get_spreadsheet_metadata(spreadsheet_id)
        sheets = metadata.get("sheets") or []
        for sheet in sheets:
            props = sheet.get("properties") or {}
            if props.get("title") == preferred_sheet_name:
                return preferred_sheet_name
        for sheet in sheets:
            props = sheet.get("properties") or {}
            if not props.get("hidden"):
                return str(props.get("title") or preferred_sheet_name)
        return preferred_sheet_name

    def read_values(self, spreadsheet_id, sheet_name, range_suffix="A1:AZ"):
        a1 = f"{sheet_name}!{range_suffix}"
        range_encoded = urllib.parse.quote(a1, safe="")
        response = self.request_with_auth(
            "GET",
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_encoded}",
            params={"majorDimension": "ROWS"},
            timeout=60,
        )
        return response.json().get("values") or []

    def write_header_row(self, spreadsheet_id, sheet_name, header_values):
        last_column = to_column_letter(len(header_values))
        a1 = f"{sheet_name}!A1:{last_column}1"
        range_encoded = urllib.parse.quote(a1, safe="")
        self.request_with_auth(
            "PUT",
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_encoded}",
            params={"valueInputOption": "RAW"},
            json={"range": a1, "majorDimension": "ROWS", "values": [header_values]},
            timeout=60,
            json_body=True,
        )

    def ensure_headers(self, spreadsheet_id, sheet_name, header_values, required_headers):
        current = [str(value or "").strip() for value in (header_values or [])]
        if not current:
            current = []
        changed = False
        for header in required_headers:
            if header not in current:
                current.append(header)
                changed = True
        if changed:
            self.write_header_row(spreadsheet_id, sheet_name, current)
        return {name: idx + 1 for idx, name in enumerate(current) if name}

    def batch_update_row_fields(self, spreadsheet_id, sheet_name, header_map, row_number, updates):
        data = []
        for header, value in updates.items():
            column_index = header_map.get(header)
            if not column_index:
                continue
            a1 = f"{sheet_name}!{to_column_letter(column_index)}{row_number}"
            data.append({"range": a1, "values": [[str(value or "")]]})
        if not data:
            return
        self.request_with_auth(
            "POST",
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values:batchUpdate",
            json={"valueInputOption": "USER_ENTERED", "data": data},
            timeout=60,
            json_body=True,
        )


class WebsiteEmailResolver:
    def __init__(self, firecrawl=None):
        self.firecrawl = firecrawl or FirecrawlClient()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})
        self.use_jina_search_fallback = as_bool(DEFAULT_USE_JINA_SEARCH_FALLBACK)
        self.infer_email_from_domain = as_bool(DEFAULT_INFER_EMAIL_FROM_DOMAIN)

    def is_directory_url(self, url):
        host = urllib.parse.urlparse(clean_url(url)).netloc.lower()
        return host_matches(host, DIRECTORY_HOSTS)

    def extract_search_result_urls(self, search_html):
        urls = []
        for raw_url in SEARCH_RESULT_LINK_PATTERN.findall(search_html or ""):
            candidate = unescape(raw_url)
            if "duckduckgo.com/l/?" in candidate:
                parsed = urllib.parse.urlparse(candidate)
                params = urllib.parse.parse_qs(parsed.query)
                candidate = (params.get("uddg") or [""])[0]
            candidate = clean_url(candidate)
            if candidate:
                urls.append(candidate)
        return dedupe_keep_order(urls)

    def search_urls_via_2gis_phone(self, row, limit=RESOLVER_SEARCH_LIMIT, deadline=None):
        urls = []
        for phone_field in ("phone_primary", "phone_secondary"):
            phone = normalize_phone(row.get(phone_field))
            if not phone:
                continue
            digits = re.sub(r"\D+", "", phone)
            if not digits:
                continue
            timeout = request_timeout_for(deadline, DEFAULT_REQUEST_TIMEOUT) if deadline else DEFAULT_REQUEST_TIMEOUT
            if deadline and timeout <= 0:
                break
            search_url = f"https://2gis.ru/search/{digits}"
            try:
                response = self.session.get(search_url, timeout=timeout)
                response.raise_for_status()
            except Exception:
                continue
            search_html = response.text or ""
            for match in TWO_GIS_FIRM_LINK_PATTERN.finditer(search_html):
                relative_url = match.group(1)
                candidate = clean_url(urllib.parse.urljoin("https://2gis.ru", unescape(relative_url)))
                if not candidate:
                    continue
                detail_html = self.fetch_2gis_detail_html(candidate, deadline=deadline)
                if detail_html and self.page_matches(detail_html, row):
                    urls.extend(self.external_site_urls(candidate, detail_html, limit=limit))
                urls.append(candidate)
                if len(dedupe_keep_order(urls)) >= limit:
                    return dedupe_keep_order(urls)[:limit]
        return dedupe_keep_order(urls)[:limit]

    def search_urls_via_jina(self, query, limit=RESOLVER_SEARCH_LIMIT, deadline=None):
        if not self.use_jina_search_fallback:
            return []
        timeout = request_timeout_for(deadline, DEFAULT_REQUEST_TIMEOUT) if deadline else DEFAULT_REQUEST_TIMEOUT
        if deadline and timeout <= 0:
            return []
        endpoint = JINA_DDG_SEARCH_PREFIX + urllib.parse.quote(str(query or ""))
        try:
            response = self.session.get(endpoint, timeout=timeout)
            response.raise_for_status()
        except Exception:
            return []
        text = str(response.text or "")
        urls = []
        for encoded in re.findall(r"http://duckduckgo\.com/l/\?uddg=([^&\s)]+)", text, flags=re.IGNORECASE):
            candidate = clean_url(urllib.parse.unquote(encoded))
            if candidate:
                urls.append(candidate)
        return dedupe_keep_order(urls)[:limit]

    def infer_email_from_url(self, url):
        if not self.infer_email_from_domain:
            return ""
        host = urllib.parse.urlparse(clean_url(url)).netloc.lower()
        root = approx_root_domain(host)
        if not root or host_matches(root, DIRECTORY_HOSTS):
            return ""
        for local_part in INFERRED_EMAIL_LOCALS:
            candidate = f"{local_part}@{root}"
            if is_valid_email(candidate):
                return candidate
        return ""

    def is_2gis_challenge_html(self, html):
        lowered = str(html or "").lower()
        if not lowered:
            return False
        return any(
            token in lowered
            for token in ("servicepipe.ru", "get_cookie_spsn", "id_captcha_frame_div", "back_location=https%3a%2f%2f2gis.ru")
        )

    def fetch_2gis_detail_html(self, url, deadline=None):
        timeout = request_timeout_for(deadline, DEFAULT_REQUEST_TIMEOUT) if deadline else DEFAULT_REQUEST_TIMEOUT
        if deadline and timeout <= 0:
            return ""

        def load_once(current_timeout):
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=current_timeout,
            )
            response.raise_for_status()
            return response.text or ""

        try:
            html = load_once(timeout)
        except Exception:
            return ""
        if not self.is_2gis_challenge_html(html):
            return html

        retry_delay = 10
        if deadline:
            retry_delay = min(retry_delay, max(0, int(remaining_seconds(deadline)) - 2))
        if retry_delay <= 0:
            return html
        time.sleep(retry_delay)

        timeout = request_timeout_for(deadline, DEFAULT_REQUEST_TIMEOUT) if deadline else DEFAULT_REQUEST_TIMEOUT
        if deadline and timeout <= 0:
            return html
        try:
            return load_once(timeout)
        except Exception:
            return html

    def fetch_html(self, url, deadline=None):
        clean = clean_url(url)
        if not clean:
            return ""
        timeout = request_timeout_for(deadline, DEFAULT_REQUEST_TIMEOUT) if deadline else DEFAULT_REQUEST_TIMEOUT
        if deadline and timeout <= 0:
            return ""
        if self.firecrawl.enabled():
            html = self.firecrawl.scrape_html(clean, timeout=min(timeout, 20))
            if html:
                return html
        try:
            response = self.session.get(clean, timeout=timeout)
            response.raise_for_status()
            return response.text or ""
        except Exception:
            return ""

    def search_urls(self, queries, limit=RESOLVER_SEARCH_LIMIT, deadline=None):
        found = []
        for query in dedupe_keep_order(queries):
            timeout = request_timeout_for(deadline, DEFAULT_REQUEST_TIMEOUT) if deadline else DEFAULT_REQUEST_TIMEOUT
            if deadline and timeout <= 0:
                break
            try:
                response = self.session.get(
                    "https://duckduckgo.com/html/",
                    params={"q": query},
                    timeout=timeout,
                )
                response.raise_for_status()
                urls = self.extract_search_result_urls(response.text or "")
            except Exception:
                urls = []
            if len(urls) < max(2, limit // 2):
                urls = dedupe_keep_order(
                    urls + self.search_urls_via_jina(query, limit=max(limit, RESOLVER_SEARCH_LIMIT * 2), deadline=deadline)
                )
            primary = []
            secondary = []
            for candidate in urls:
                host = urllib.parse.urlparse(candidate).netloc.lower()
                if not host:
                    continue
                if host_matches(host, DIRECTORY_HOSTS):
                    secondary.append(candidate)
                else:
                    primary.append(candidate)
            for item in dedupe_keep_order(primary + secondary):
                if item not in found:
                    found.append(item)
                if len(found) >= limit:
                    return found
        return found

    def same_domain_contact_urls(self, base_url, html, limit=RESOLVER_CONTACT_URL_LIMIT):
        base = clean_url(base_url)
        parsed_base = urllib.parse.urlparse(base)
        base_root = approx_root_domain(parsed_base.netloc)
        candidates = []
        for raw_href in HREF_PATTERN.findall(html or ""):
            href = unescape(raw_href).strip()
            if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            absolute = clean_url(urllib.parse.urljoin(base, href))
            if not absolute:
                continue
            parsed = urllib.parse.urlparse(absolute)
            if approx_root_domain(parsed.netloc) != base_root:
                continue
            path = parsed.path.lower()
            if any(marker in path for marker in ("contact", "kontakt", "kontakty", "about", "o-nas", "contacts")):
                candidates.append(absolute)
        defaults = [
            urllib.parse.urljoin(base, "/contacts"),
            urllib.parse.urljoin(base, "/contact"),
            urllib.parse.urljoin(base, "/kontakty"),
            urllib.parse.urljoin(base, "/o-nas"),
        ]
        candidates.extend(defaults)
        return dedupe_keep_order(candidates)[:limit]

    def decode_directory_outbound_url(self, url):
        clean = clean_url(url)
        parsed = urllib.parse.urlparse(clean)
        host = parsed.netloc.lower()
        if host_matches(host, {"link.2gis.ru"}):
            unescaped = unescape(clean)
            marker = unescaped.find("?http")
            if marker != -1:
                return clean_url(unescaped[marker + 1 :])
        return ""

    def external_site_urls(self, base_url, html, limit=RESOLVER_CONTACT_URL_LIMIT):
        base = clean_url(base_url)
        parsed_base = urllib.parse.urlparse(base)
        base_root = approx_root_domain(parsed_base.netloc)
        primary = []
        social = []
        secondary = []
        for raw_href in HREF_PATTERN.findall(html or ""):
            href = unescape(raw_href).strip()
            if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            absolute = clean_url(urllib.parse.urljoin(base, href))
            if not absolute:
                continue
            outbound = self.decode_directory_outbound_url(absolute)
            if outbound:
                absolute = outbound
            parsed = urllib.parse.urlparse(absolute)
            if parsed.scheme not in {"http", "https"}:
                continue
            host = parsed.netloc.lower()
            if not host:
                continue
            if host_matches(host, DIRECTORY_HOSTS):
                continue
            if approx_root_domain(host) == base_root:
                continue
            if host_matches(host, {"youtube.com", "www.youtube.com", "vk.com", "t.me", "telegram.me", "max.ru"}):
                social.append(absolute)
            elif host_matches(host, {"go.checkscan.ru", "redirect.2gis.com"}):
                secondary.append(absolute)
            else:
                primary.append(absolute)
        return dedupe_keep_order(primary + social + secondary)[:limit]

    def page_matches(self, html, row):
        if not html:
            return False
        body = str(html or "")
        body_digits = re.sub(r"\D+", "", body)
        body_key = normalize_company_name(body)
        for phone_field in ("phone_primary", "phone_secondary"):
            phone = normalize_phone(row.get(phone_field))
            if not phone:
                continue
            digits = re.sub(r"\D+", "", phone)
            if digits and (digits in body_digits or digits[-10:] in body_digits):
                return True
        for company_key in company_match_keys(row.get("company_name")):
            if company_key and company_key in body_key:
                return True
        return False

    def score_email(self, email_address, page_url):
        parsed = urllib.parse.urlparse(page_url)
        page_root = approx_root_domain(parsed.netloc)
        local_part, _, domain = email_address.partition("@")
        score = 0
        if is_excluded_business_email(email_address):
            return -50
        if approx_root_domain(domain) == page_root:
            score += 8
        if local_part in {"info", "mail", "hello", "office", "sales", "contact", "admin"}:
            score += 3
        if "noreply" in local_part or "no-reply" in local_part:
            score -= 10
        if is_placeholder_email(email_address):
            score -= 30
        return score

    def resolve(self, row):
        deadline = resolver_deadline(RESOLVER_TOTAL_TIMEOUT)
        inferred_candidate = {}
        explicit_urls = []
        for field in ("website_url", "website", "site_url", "site", "url", "domain"):
            value = clean_url(row.get(field))
            if value:
                explicit_urls.append(value)

        company = str(row.get("company_name") or "").strip()
        city = str(row.get("city") or "").strip()
        company_queries = []
        for company_alias in company_search_aliases(company):
            company_queries.append(f'"{company_alias}" email')
            company_queries.append(f'"{company_alias}" контакты')
            if city:
                company_queries.append(f'"{company_alias}" "{city}" email')
                company_queries.append(f'"{company_alias}" "{city}" контакты')

        phone_queries = []
        for phone_field in ("phone_primary", "phone_secondary"):
            for phone_variant in phone_search_variants(row.get(phone_field)):
                phone_queries.append(f'"{phone_variant}" "{row.get("company_name", "").strip()}" email')
                phone_queries.append(f'"{phone_variant}" "{row.get("company_name", "").strip()}" контакты')
                phone_queries.append(f'"{phone_variant}" email')

        url_candidates = dedupe_keep_order(explicit_urls + self.search_urls_via_2gis_phone(row, limit=RESOLVER_SEARCH_LIMIT, deadline=deadline))
        if len(url_candidates) < RESOLVER_SEARCH_LIMIT:
            url_candidates = dedupe_keep_order(
                url_candidates
                + self.search_urls(company_queries + phone_queries, limit=RESOLVER_SEARCH_LIMIT, deadline=deadline)
            )
        url_candidates = url_candidates[:RESOLVER_SEARCH_LIMIT]
        if not url_candidates:
            return {}

        for candidate_url in url_candidates:
            if remaining_seconds(deadline) <= 0:
                break
            visited = set()
            queue = [(candidate_url, False)]
            first_html = ""
            while queue and len(visited) < RESOLVER_MAX_VISITS:
                if remaining_seconds(deadline) <= 0:
                    break
                current_url, inherited_match = queue.pop(0)
                if current_url in visited:
                    continue
                visited.add(current_url)
                html = self.fetch_html(current_url, deadline=deadline)
                if not html:
                    continue
                current_is_directory = self.is_directory_url(current_url)
                matched_page = inherited_match or self.page_matches(html, row)
                if current_is_directory and not matched_page:
                    continue
                if not first_html:
                    first_html = html
                    if not current_is_directory:
                        for extra_url in self.same_domain_contact_urls(candidate_url, first_html):
                            if extra_url not in visited:
                                queue.append((extra_url, inherited_match))
                if current_is_directory and matched_page:
                    for external_url in self.external_site_urls(current_url, html):
                        if external_url not in visited:
                            queue.append((external_url, True))
                if not inferred_candidate and matched_page and not current_is_directory:
                    inferred_email = self.infer_email_from_url(current_url)
                    if inferred_email:
                        inferred_candidate = {
                            "email": inferred_email,
                            "source_url": current_url,
                            "search_url": candidate_url,
                            "resolution_status": "inferred_from_domain",
                        }
                emails = [
                    item
                    for item in extract_emails(html)
                    if not is_placeholder_email(item) and not is_excluded_business_email(item)
                ]
                if current_is_directory:
                    emails = [item for item in emails if not host_matches(email_domain(item), DIRECTORY_HOSTS)]
                if not emails:
                    continue
                if not matched_page and current_url != candidate_url:
                    continue
                ranked = sorted(
                    ((self.score_email(email_address, current_url), email_address) for email_address in emails),
                    reverse=True,
                )
                if ranked:
                    return {
                        "email": ranked[0][1],
                        "source_url": current_url,
                        "search_url": candidate_url,
                        "resolution_status": "verified_from_website",
                    }
        return inferred_candidate


class SmtpEmailSender:
    def __init__(self):
        self.host = os.getenv("EMAIL_FOLLOWUP_SMTP_HOST", "").strip()
        self.port = int(os.getenv("EMAIL_FOLLOWUP_SMTP_PORT", "587").strip() or "587")
        self.username = os.getenv("EMAIL_FOLLOWUP_SMTP_USERNAME", "").strip()
        self.password = os.getenv("EMAIL_FOLLOWUP_SMTP_PASSWORD", "").strip()
        self.use_ssl = as_bool(os.getenv("EMAIL_FOLLOWUP_SMTP_USE_SSL", "false"))
        self.use_starttls = as_bool(os.getenv("EMAIL_FOLLOWUP_SMTP_USE_STARTTLS", "true"))
        self.from_email = os.getenv("EMAIL_FOLLOWUP_FROM_EMAIL", "").strip()
        self.from_name = os.getenv("EMAIL_FOLLOWUP_FROM_NAME", DEFAULT_PRODUCT_NAME).strip() or DEFAULT_PRODUCT_NAME
        self.reply_to = DEFAULT_REPLY_TO

    def enabled(self):
        return bool(self.host and self.from_email)

    def send(self, to_email, subject, text_body, html_body="", attachments=None):
        if not self.enabled():
            raise RuntimeError("SMTP не настроен")
        message = EmailMessage()
        message["From"] = formataddr((self.from_name, self.from_email))
        message["To"] = to_email
        message["Subject"] = subject
        if self.reply_to:
            message["Reply-To"] = self.reply_to
        message.set_content(text_body)
        if html_body:
            message.add_alternative(html_body, subtype="html")
        for attachment in attachments or []:
            path = Path(str(attachment.get("path") or "")).expanduser()
            if not path.exists() or not path.is_file():
                raise RuntimeError(f"Не найден файл вложения: {path}")
            mime_type, _ = mimetypes.guess_type(path.name)
            if mime_type and "/" in mime_type:
                maintype, subtype = mime_type.split("/", 1)
            else:
                maintype, subtype = "application", "octet-stream"
            message.add_attachment(
                path.read_bytes(),
                maintype=maintype,
                subtype=subtype,
                filename=str(attachment.get("filename") or path.name),
            )

        if self.use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=30) as server:
                if self.username:
                    server.login(self.username, self.password)
                server.send_message(message)
            return

        with smtplib.SMTP(self.host, self.port, timeout=30) as server:
            if self.use_starttls:
                server.starttls(context=ssl.create_default_context())
            if self.username:
                server.login(self.username, self.password)
            server.send_message(message)


class DomainBlacklist:
    def __init__(self, path=DEFAULT_DOMAIN_BLACKLIST_PATH):
        self.path = path
        self.payload = load_json_file(self.path, {"domains": {}})
        self.domains = self.payload.get("domains") or {}

    def contains(self, email_or_domain):
        domain = email_domain(email_or_domain) or str(email_or_domain or "").strip().lower().strip(".")
        return domain in self.domains

    def get(self, email_or_domain):
        domain = email_domain(email_or_domain) or str(email_or_domain or "").strip().lower().strip(".")
        return self.domains.get(domain) or {}

    def add(self, domain, reason, source="bounce"):
        clean = str(domain or "").strip().lower().strip(".")
        if not clean:
            return False
        if clean in PROTECTED_PUBLIC_EMAIL_DOMAINS:
            return False
        existing = self.domains.get(clean) or {}
        entry = {
            "domain": clean,
            "reason": str(reason or existing.get("reason") or "").strip(),
            "source": str(source or existing.get("source") or "").strip() or "bounce",
            "updated_at": now_iso(),
        }
        if existing == entry:
            return False
        self.domains[clean] = entry
        self.payload["domains"] = self.domains
        save_json_file(self.path, self.payload)
        return True

    def size(self):
        return len(self.domains)


class TelegramReporter:
    def __init__(self):
        self.bot_token = DEFAULT_TELEGRAM_BOT_TOKEN
        self.api_base = DEFAULT_TELEGRAM_API_BASE
        self.chat_id = DEFAULT_TELEGRAM_CHAT_ID
        self.thread_id = DEFAULT_TELEGRAM_THREAD_ID
        self.reports_enabled = as_bool(DEFAULT_TELEGRAM_REPORTS_ENABLED)
        self.report_on_empty = as_bool(DEFAULT_TELEGRAM_REPORT_ON_EMPTY)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "email_followup_service/1.0"})

    def enabled(self):
        return bool(self.reports_enabled and self.bot_token and self.chat_id)

    def send_message(self, text):
        if not self.enabled() or not str(text or "").strip():
            return {"ok": False, "reason": "telegram_disabled"}
        payload = {
            "chat_id": self.chat_id,
            "text": str(text).strip(),
            "disable_web_page_preview": True,
        }
        if self.thread_id:
            payload["message_thread_id"] = int(self.thread_id)
        response = self.session.post(
            f"{self.api_base}/bot{self.bot_token}/sendMessage",
            json=payload,
            timeout=20,
        )
        if not response.ok:
            detail = response.text.strip()
            raise RuntimeError(f"Telegram sendMessage failed ({response.status_code}): {detail[:500]}")
        response.raise_for_status()
        return response.json()

    def should_notify(self, summary):
        if not self.enabled():
            return False
        if self.report_on_empty:
            return True
        for key in ("sent", "needs_review", "errors", "blocked", "bounces_processed", "blacklisted_domains_added"):
            if int(summary.get(key) or 0) > 0:
                return True
        return False

    def format_summary(self, summary):
        lines = [
            "Email Followup Report",
            f"UTC: {now_iso()}",
            f"Mode: {'dry-run' if summary.get('dry_run') else 'live'}",
            f"Sheets: {summary.get('spreadsheets_found', 0)} | Groups: {summary.get('groups_seen', 0)}",
            (
                "Processed: {processed} | Sent: {sent} | Review: {review} | Blocked: {blocked} | Errors: {errors}".format(
                    processed=summary.get("records_processed", 0),
                    sent=summary.get("sent", 0),
                    review=summary.get("needs_review", 0),
                    blocked=summary.get("blocked", 0),
                    errors=summary.get("errors", 0),
                )
            ),
        ]
        if summary.get("limit_reached"):
            lines.append("Run cap reached before full scan: yes")
        if "bounces_processed" in summary:
            lines.append(
                "Bounces: {processed} | Matched: {matched} | Blacklisted domains: {blacklisted}".format(
                    processed=summary.get("bounces_processed", 0),
                    matched=summary.get("bounces_matched", 0),
                    blacklisted=summary.get("blacklisted_domains_added", 0),
                )
            )
        sheet_summaries = list(summary.get("sheet_summaries") or [])
        if sheet_summaries:
            lines.append("")
            lines.append("Sheets:")
            for item in sheet_summaries[:12]:
                name = str(item.get("spreadsheet_name") or item.get("spreadsheet_id") or "-").strip()
                status = str(item.get("status") or "").strip()
                if status == "updated":
                    lines.append(
                        "- {name}: sent {sent}, review {review}, blocked {blocked}, errors {errors}".format(
                            name=name,
                            sent=item.get("sent", 0),
                            review=item.get("needs_review", 0),
                            blocked=item.get("blocked", 0),
                            errors=item.get("errors", 0),
                        )
                    )
                elif status == "empty_sheet":
                    lines.append(f"- {name}: пусто или лист без данных")
                else:
                    lines.append(f"- {name}: новых записей для email-отправки нет")
        results = list(summary.get("results") or [])[:5]
        if results:
            lines.append("")
            lines.append("Top results:")
            for item in results:
                target = item.get("email") or item.get("phone_primary") or item.get("lead_key") or "-"
                company = str(item.get("company_name") or "").strip()
                label = f"{item.get('action')} / {item.get('reason', '')}".strip(" /")
                if company:
                    lines.append(f"- {label}: {company} -> {target}")
                else:
                    lines.append(f"- {label}: {target}")
        bounce_items = list(summary.get("bounce_results") or [])[:5]
        if bounce_items:
            lines.append("")
            lines.append("Bounces:")
            for item in bounce_items:
                lines.append(
                    f"- {item.get('bounce_type', 'bounce')}: {item.get('email', '-')}"
                )
        return "\n".join(line for line in lines if line)


class GmailBounceWatcher:
    def __init__(self, blacklist=None, state_path=DEFAULT_BOUNCE_STATE_PATH):
        self.host = DEFAULT_IMAP_HOST
        self.port = DEFAULT_IMAP_PORT
        self.username = DEFAULT_IMAP_USERNAME
        self.password = DEFAULT_IMAP_PASSWORD
        self.mailbox = DEFAULT_IMAP_MAILBOX
        self.scan_limit = DEFAULT_BOUNCE_SCAN_LIMIT
        self.state_path = state_path
        self.blacklist = blacklist or DomainBlacklist()
        self.state = load_json_file(self.state_path, {"processed_uids": []})
        self.processed_uids = set(str(item) for item in (self.state.get("processed_uids") or []))

    def enabled(self):
        return bool(self.username and self.password)

    def _persist_state(self):
        recent = sorted(self.processed_uids, key=lambda item: int(item))[-500:]
        self.state["processed_uids"] = recent
        save_json_file(self.state_path, self.state)

    def _extract_text(self, message_obj):
        text_parts = []
        html_parts = []
        if message_obj.is_multipart():
            for part in message_obj.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                disposition = str(part.get("Content-Disposition") or "").lower()
                if "attachment" in disposition and part.get_content_type() != "message/rfc822":
                    continue
                content_type = part.get_content_type()
                try:
                    payload = part.get_content()
                except Exception:
                    try:
                        payload = part.get_payload(decode=True).decode(errors="ignore")
                    except Exception:
                        payload = ""
                if content_type == "text/plain":
                    text_parts.append(str(payload or ""))
                elif content_type == "text/html":
                    html_parts.append(str(payload or ""))
                elif content_type == "message/rfc822":
                    try:
                        nested = part.get_payload(0)
                        nested_text = self._extract_text(nested)
                        if nested_text:
                            text_parts.append(nested_text)
                    except Exception:
                        continue
        else:
            try:
                payload = message_obj.get_content()
            except Exception:
                payload = message_obj.get_payload(decode=True).decode(errors="ignore")
            if message_obj.get_content_type() == "text/html":
                html_parts.append(str(payload or ""))
            else:
                text_parts.append(str(payload or ""))
        text = "\n".join(item for item in text_parts if item).strip()
        if text:
            return text
        return "\n".join(html_to_text(item) for item in html_parts if item).strip()

    def _classify_bounce(self, text):
        lowered = str(text or "").lower()
        if any(
            token in lowered
            for token in (
                "nxdomain",
                "domain name not found",
                "badrcptdomain",
                "dns type 'mx' lookup",
                "recipient domain not found",
                "host or domain name not found",
            )
        ):
            return "domain_not_found", "Домен email не существует или не резолвится"
        if any(
            token in lowered
            for token in (
                "user unknown",
                "no such user",
                "mailbox unavailable",
                "address not found",
                "address couldn't be found",
                "address could not be found",
                "recipient address rejected",
                "550 5.1.1",
                "550 5.7.1 no such user",
            )
        ):
            return "mailbox_not_found", "Почтовый адрес не существует или недоступен"
        if any(token in lowered for token in ("quota exceeded", "mailbox full", "over quota")):
            return "mailbox_full", "Почтовый ящик переполнен"
        if any(token in lowered for token in ("blocked", "spam", "policy", "rejected for policy")):
            return "policy_blocked", "Письмо отклонено политикой принимающей стороны"
        if any(token in lowered for token in ("timed out", "temporary", "transient", "try again later", "greylist")):
            return "temporary_failure", "Временная ошибка доставки"
        return "delivery_failed", "Письмо не доставлено"

    def _extract_recipient(self, text):
        patterns = [
            r"Final-Recipient:\s*rfc822;\s*([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})",
            r"Original-Recipient:\s*rfc822;\s*([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})",
            r"wasn't delivered to\s*([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})",
            r"was not delivered to\s*([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})",
            r"to\s*([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})\s*because",
            r"Recipient address rejected:\s*([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})",
            r"\bfor\s*<([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})>",
        ]
        for pattern in patterns:
            match = re.search(pattern, str(text or ""), flags=re.IGNORECASE)
            if match:
                candidate = normalize_email_candidate(match.group(1)).lower()
                if is_valid_email(candidate):
                    return candidate
        return ""

    def fetch_events(self, limit_messages=0):
        summary = {
            "ok": True,
            "enabled": self.enabled(),
            "checked": 0,
            "processed": 0,
            "events": [],
        }
        if not self.enabled():
            return summary
        limit = int(limit_messages or self.scan_limit or 0) or self.scan_limit
        mail = imaplib.IMAP4_SSL(self.host, self.port)
        try:
            mail.login(self.username, self.password)
            mail.select(self.mailbox)
            status, payload = mail.uid("search", None, "ALL")
            if status != "OK":
                return summary
            uids = [item.decode() for item in payload[0].split() if item][-limit:]
            for uid in reversed(uids):
                summary["checked"] += 1
                if uid in self.processed_uids:
                    continue
                status, fetched = mail.uid("fetch", uid, "(RFC822)")
                if status != "OK" or not fetched:
                    continue
                raw = b""
                for item in fetched:
                    if isinstance(item, tuple) and len(item) > 1:
                        raw += item[1]
                if not raw:
                    continue
                message_obj = email.message_from_bytes(raw, policy=policy.default)
                sender = str(message_obj.get("From") or "")
                subject = str(message_obj.get("Subject") or "")
                text = self._extract_text(message_obj)
                fingerprint = "\n".join([sender, subject, text]).lower()
                if not any(token in fingerprint for token in ("mailer-daemon", "mail delivery subsystem", "delivery status notification", "undelivered", "postmaster")):
                    self.processed_uids.add(uid)
                    continue
                recipient = self._extract_recipient(text)
                if not recipient:
                    self.processed_uids.add(uid)
                    continue
                bounce_type, human_reason = self._classify_bounce(text)
                event = {
                    "uid": uid,
                    "email": recipient,
                    "bounce_type": bounce_type,
                    "human_reason": human_reason,
                    "subject": subject.strip(),
                    "from": sender.strip(),
                    "message_id": str(message_obj.get("Message-ID") or "").strip(),
                    "raw_reason": re.sub(r"\s+", " ", text).strip()[:500],
                    "blacklisted_domain": False,
                }
                if bounce_type == "domain_not_found":
                    event["blacklisted_domain"] = self.blacklist.add(email_domain(recipient), human_reason, source="bounce")
                summary["events"].append(event)
                summary["processed"] += 1
                self.processed_uids.add(uid)
            self._persist_state()
            return summary
        finally:
            try:
                mail.logout()
            except Exception:
                pass


class EmailFollowupService:
    def __init__(self, sheet_prefix=DEFAULT_SHEET_PREFIX, preferred_sheet_name=DEFAULT_SHEET_NAME):
        self.sheet_prefix = sheet_prefix
        self.preferred_sheet_name = preferred_sheet_name
        self.target_spreadsheet_ids = list(DEFAULT_SPREADSHEET_IDS)
        self.google = GoogleSheetsClient(drive_folder_id=DEFAULT_DRIVE_FOLDER_ID)
        self.domain_blacklist = DomainBlacklist()
        self.resolver = WebsiteEmailResolver(
            firecrawl=FirecrawlClient(
                base_url=DEFAULT_FIRECRAWL_BASE_URL,
                api_key=DEFAULT_FIRECRAWL_API_KEY,
            )
        )
        self.mailer = SmtpEmailSender()
        self.bounce_watcher = GmailBounceWatcher(blacklist=self.domain_blacklist)
        self.telegram = TelegramReporter()
        self._phone_email_cache = {}
        self._phone_email_cache_built = False

    def max_records_limit(self, value):
        if value is None:
            return DEFAULT_MAX_RECORDS_PER_RUN
        try:
            limit = int(value)
        except Exception:
            return DEFAULT_MAX_RECORDS_PER_RUN
        if limit < 0:
            return 0
        return limit

    def build_email_attachments(self, strict=False):
        raw_path = str(DEFAULT_ATTACHMENT_PATH or "").strip()
        if not raw_path:
            return []
        path = Path(raw_path).expanduser()
        if not path.exists() or not path.is_file():
            if strict:
                raise RuntimeError(f"Не найден файл вложения: {path}")
            return []
        return [{"path": str(path), "filename": DEFAULT_ATTACHMENT_NAME or path.name}]

    def list_target_spreadsheets(self, prefix="", limit_sheets=0, spreadsheet_ids=None):
        explicit_ids = list(spreadsheet_ids or self.target_spreadsheet_ids or [])
        if explicit_ids:
            items = []
            for spreadsheet_id in explicit_ids:
                try:
                    meta = self.google.get_drive_file(spreadsheet_id)
                except Exception:
                    meta = {"id": spreadsheet_id, "name": spreadsheet_id}
                items.append(meta)
            return items
        sheet_limit = int(limit_sheets or DEFAULT_MAX_SHEETS_PER_RUN)
        return self.google.list_prefixed_sheets(
            str(prefix or self.sheet_prefix).strip() or self.sheet_prefix,
            limit=sheet_limit,
        )

    def health(self):
        raw_attachment_path = str(DEFAULT_ATTACHMENT_PATH or "").strip()
        attachment_path = Path(raw_attachment_path).expanduser() if raw_attachment_path else None
        attachments = self.build_email_attachments(strict=False)
        return {
            "ok": True,
            "service": "email_followup_service",
            "sheet_prefix": self.sheet_prefix,
            "preferred_sheet_name": self.preferred_sheet_name,
            "drive_folder_id": DEFAULT_DRIVE_FOLDER_ID,
            "target_spreadsheet_ids": self.target_spreadsheet_ids,
            "firecrawl_enabled": self.resolver.firecrawl.enabled(),
            "smtp_enabled": self.mailer.enabled(),
            "imap_bounce_enabled": self.bounce_watcher.enabled(),
            "telegram_reports_enabled": self.telegram.enabled(),
            "blacklisted_domains": self.domain_blacklist.size(),
            "attachment_enabled": bool(attachments),
            "attachment_path": str(attachment_path) if attachment_path else "",
            "attachment_exists": bool(attachment_path and attachment_path.exists() and attachment_path.is_file()),
            "attachment_filename": (attachments[0].get("filename") if attachments else ""),
            "test_recipient": os.getenv("EMAIL_FOLLOWUP_TEST_RECIPIENT", "").strip(),
        }

    def build_phone_email_cache(self, sheet_prefix="", limit_sheets=0):
        if self._phone_email_cache_built:
            return self._phone_email_cache
        prefix = str(sheet_prefix or self.sheet_prefix).strip() or self.sheet_prefix
        cache = {}
        spreadsheets = self.list_target_spreadsheets(prefix=prefix, limit_sheets=limit_sheets)
        for spreadsheet in spreadsheets:
            spreadsheet_id = spreadsheet.get("id", "")
            if not spreadsheet_id:
                continue
            sheet_name = self.google.resolve_sheet_name(spreadsheet_id, self.preferred_sheet_name)
            values = self.google.read_values(spreadsheet_id, sheet_name, range_suffix="A1:AZ")
            if not values:
                continue
            rows = self.rows_from_values(values)
            for row in rows:
                candidates = []
                for field in ("contact_email", "email", "email_address", "client_email", "customer_email"):
                    candidates.extend(extract_emails(row.get(field, "")))
                if not candidates:
                    continue
                status = str(row.get("email_send_status") or "").strip().lower()
                verification = str(row.get("email_verification_status") or "").strip().lower()
                for phone_field in ("phone_primary", "phone_secondary"):
                    phone = normalize_phone(row.get(phone_field))
                    if not phone:
                        continue
                    bucket = cache.setdefault(phone, {})
                    for email_address in dedupe_keep_order(candidates):
                        if self.domain_blacklist.contains(email_address):
                            continue
                        if is_excluded_business_email(email_address):
                            continue
                        score = 1
                        if status == "sent":
                            score += 5
                        if verification in {"verified", "verified_from_website", "from_notes", "from_sheet", "from_misplaced_field", "from_phone_history"}:
                            score += 2
                        if verification in {"domain_not_found", "domain_check_failed", "not_found", "blacklisted_domain"}:
                            score -= 5
                        if status in {"manual_review", "bounced"}:
                            score -= 2
                        if score <= 0:
                            continue
                        item = bucket.setdefault(email_address, {"score": 0, "occurrences": 0})
                        item["score"] += score
                        item["occurrences"] += 1
        self._phone_email_cache = cache
        self._phone_email_cache_built = True
        return self._phone_email_cache

    def lookup_email_from_phone_cache(self, row, sheet_prefix="", limit_sheets=0):
        cache = self.build_phone_email_cache(sheet_prefix=sheet_prefix, limit_sheets=limit_sheets)
        best = None
        for phone_field in ("phone_primary", "phone_secondary"):
            phone = normalize_phone(row.get(phone_field))
            if not phone:
                continue
            options = cache.get(phone) or {}
            for email_address, payload in options.items():
                score = int(payload.get("score") or 0)
                occurrences = int(payload.get("occurrences") or 0)
                candidate = (score, occurrences, email_address)
                if best is None or candidate > best:
                    best = candidate
        if not best:
            return {}
        _, _, email_address = best
        if not is_valid_email(email_address):
            return {}
        if is_excluded_business_email(email_address):
            return {}
        return {
            "email": email_address,
            "source_url": "history_phone_match",
            "resolution_status": "from_phone_history",
        }

    def resolve_best_email_candidate(self, row, skip_email="", sheet_prefix="", limit_sheets=0):
        skip_normalized = normalize_email_candidate(skip_email).lower() if skip_email else ""
        candidates = []
        resolved = self.resolver.resolve(row)
        if resolved:
            candidates.append(resolved)
        cached = self.lookup_email_from_phone_cache(
            row,
            sheet_prefix=sheet_prefix,
            limit_sheets=limit_sheets,
        )
        if cached:
            candidates.append(cached)

        for candidate in candidates:
            email_address = normalize_email_candidate(candidate.get("email", "")).lower()
            if not email_address or not is_valid_email(email_address):
                continue
            if is_placeholder_email(email_address):
                continue
            if is_excluded_business_email(email_address):
                continue
            if skip_normalized and email_address == skip_normalized:
                continue
            if self.domain_blacklist.contains(email_address):
                continue
            domain = email_domain(email_address)
            domain_ok, domain_reason = check_email_domain_resolves(email_address)
            if not domain_ok:
                if domain_reason == "domain_not_found":
                    self.domain_blacklist.add(domain, "Домен email не существует или не резолвится", source="resolver")
                continue
            return {
                "email": email_address,
                "source_url": candidate.get("source_url", ""),
                "resolution_status": candidate.get("resolution_status") or "verified_from_website",
            }
        return {}

    def rows_from_values(self, values):
        if not values:
            return []
        header = [str(item or "").strip() for item in values[0]]
        rows = []
        for row_number, raw_values in enumerate(values[1:], start=2):
            if not any(str(item or "").strip() for item in raw_values):
                continue
            record = {"_row_number": row_number}
            for idx, name in enumerate(header):
                if not name:
                    continue
                record[name] = str(raw_values[idx] if idx < len(raw_values) else "").strip()
            rows.append(record)
        return rows

    def group_rows(self, rows):
        grouped = {}
        for row in rows:
            lead_key = (
                row.get("lead_id")
                or row.get("source_record_key")
                or normalize_phone(row.get("phone_primary"))
                or f"row_{row.get('_row_number')}"
            )
            state = grouped.setdefault(
                lead_key,
                {"lead_key": lead_key, "rows": [], "seed_row": None, "latest_row": None, "latest_event_row": None},
            )
            state["rows"].append(row)
            source_system = str(row.get("source_system") or "").strip().lower()
            if source_system == "xlsx_import" and state["seed_row"] is None:
                state["seed_row"] = row
            if state["latest_row"] is None or row.get("_row_number", 0) > state["latest_row"].get("_row_number", 0):
                state["latest_row"] = row
            if source_system not in {"xlsx_import", "autodial_dispatcher"}:
                if (
                    state["latest_event_row"] is None
                    or row.get("_row_number", 0) > state["latest_event_row"].get("_row_number", 0)
                ):
                    state["latest_event_row"] = row
        return grouped

    def merge_context(self, state):
        merged = {}
        for source in (state.get("seed_row") or {}, state.get("latest_row") or {}, state.get("latest_event_row") or {}):
            for key, value in source.items():
                if key.startswith("_"):
                    continue
                if str(value or "").strip():
                    merged[key] = str(value).strip()
        # Stateful operational columns must respect explicit clearing in newer rows,
        # otherwise old imported values (for example a directory email) can leak back in.
        for source in (state.get("latest_row") or {}, state.get("latest_event_row") or {}):
            for key in STATE_OVERRIDE_FIELDS:
                if key in source:
                    merged[key] = str(source.get(key) or "").strip()
        merged["_seed_row_number"] = (state.get("seed_row") or {}).get("_row_number", 0)
        merged["_latest_row_number"] = (state.get("latest_row") or {}).get("_row_number", 0)
        merged["_event_row_number"] = (state.get("latest_event_row") or {}).get("_row_number", 0)
        merged["_target_row_number"] = merged["_event_row_number"] or merged["_latest_row_number"] or merged["_seed_row_number"]
        return merged

    def has_email_signal(self, row):
        preferred_channel = str(row.get("preferred_channel") or "").strip().lower()
        next_step = str(row.get("next_step") or "").strip().lower()
        call_result = str(row.get("call_result") or "").strip().lower()
        text_blob = "\n".join(
            [
                str(row.get("notes_short") or ""),
                str(row.get("notes_redacted") or ""),
                str(row.get("contact_email") or ""),
                preferred_channel,
                next_step,
                call_result,
            ]
        )
        if row.get("contact_email"):
            return True
        if preferred_channel in {"email", "mail", "почта"}:
            return True
        if next_step in {"send_kp", "send_email", "email_followup"}:
            return True
        if call_result in {"send_kp_pending_callback", "manager_call"}:
            return True
        if EMAIL_SIGNAL_PATTERN.search(text_blob):
            return True
        if extract_emails(text_blob):
            return True
        return False

    def extract_row_email(self, row):
        direct_fields = [
            "contact_email",
            "email",
            "email_address",
            "client_email",
            "customer_email",
            "phone_primary",
            "phone_secondary",
            "lead_id",
            "source_record_key",
        ]
        for field in direct_fields:
            email_candidates = [
                item
                for item in extract_emails(row.get(field, ""))
                if not is_placeholder_email(item) and not is_excluded_business_email(item)
            ]
            if email_candidates:
                status = "from_sheet"
                if field not in {"contact_email", "email", "email_address", "client_email", "customer_email"}:
                    status = "from_misplaced_field"
                return email_candidates[0], status
        for field in ("notes_short", "notes_redacted"):
            email_candidates = [
                item
                for item in extract_emails(row.get(field, ""))
                if not is_placeholder_email(item) and not is_excluded_business_email(item)
            ]
            if email_candidates:
                return email_candidates[0], "from_notes"
        return "", ""

    def build_email(self, row, to_email):
        contact_name = str(row.get("contact_name") or "").strip()
        company_name_raw = str(row.get("company_name") or "").strip()
        company_name_for_subject = company_name_raw or "клиники"
        attachments = self.build_email_attachments(strict=True)
        attachment_note = ""
        attachment_html_note = ""
        if attachments:
            attachment_note = (
                f"Во вложении также направляем файл «{attachments[0].get('filename', '')}».\n\n"
            )
            attachment_html_note = (
                f"<p>Во вложении также направляем файл <strong>{attachments[0].get('filename', '')}</strong>.</p>"
            )
        subject = DEFAULT_SUBJECT_TEMPLATE.format(
            product_name=DEFAULT_PRODUCT_NAME,
            company_name=company_name_for_subject,
            contact_name=contact_name or company_name_for_subject,
        )
        salutation = contact_name or company_name_raw or "Коллеги"
        text_body = (
            f"Здравствуйте, {salutation}!\n\n"
            f"Как и договаривались, направляем информацию по {DEFAULT_PRODUCT_NAME}.\n\n"
            f"{DEFAULT_PRODUCT_NAME} используется в косметологической практике по направлению коррекции фигуры. "
            f"В рабочих коммуникациях мы позиционируем продукт как липолитик нового поколения с акцентом на "
            f"безопасность, прогнозируемость применения и управляемый косметологический результат.\n\n"
            "Что важно по продукту:\n"
            "- официальный канал поставки и оригинальный продукт;\n"
            "- мягкий вход в работу: тестовый заказ возможен от 1 шт.;\n"
            "- базовый ориентир по экономике: средний чек от 19 000 руб.;\n"
            "- при соблюдении протокола в практике обычно отмечают видимый косметологический эффект на 7-10 день;\n"
            "- курс обычно составляет 3-4 процедуры.\n\n"
            "Что важно по сотрудничеству:\n"
            "- доставка 3-4 дня;\n"
            "- безналичный расчет;\n"
            "- полная предоплата;\n"
            "- при заказе от 2 шт. действует подарок, а при объеме от 100 шт. обсуждаются специальные условия.\n\n"
            "Если для вас направление актуально, можем отдельно обсудить:\n"
            "- формат спокойного тестового входа без тяжелой закупки;\n"
            "- экономику процедуры под вашу практику;\n"
            "- рабочие условия поставки и дальнейшего сопровождения.\n\n"
            f"{attachment_note}"
            f"Материалы: {DEFAULT_MATERIAL_URL}\n"
            f"Сайт: {DEFAULT_PRODUCT_SITE}\n"
            f"Контакт для связи: {DEFAULT_MANAGER_PHONE}\n"
            f"Telegram: {DEFAULT_MANAGER_TELEGRAM}\n\n"
            "Если удобно, ответьте на это письмо или напишите в Telegram. "
            "Также можно согласовать короткий созвон, чтобы быстро обсудить условия и ответить на вопросы.\n"
        )
        html_body = (
            f"<p>Здравствуйте, {salutation}!</p>"
            f"<p>Как и договаривались, направляем информацию по <strong>{DEFAULT_PRODUCT_NAME}</strong>.</p>"
            f"<p><strong>{DEFAULT_PRODUCT_NAME}</strong> используется в косметологической практике по направлению коррекции фигуры. "
            f"В рабочих коммуникациях мы позиционируем продукт как липолитик нового поколения с акцентом на безопасность, "
            f"прогнозируемость применения и управляемый косметологический результат.</p>"
            "<p><strong>Что важно по продукту:</strong></p>"
            "<ul>"
            "<li>официальный канал поставки и оригинальный продукт;</li>"
            "<li>мягкий вход в работу: тестовый заказ возможен от 1 шт.;</li>"
            "<li>базовый ориентир по экономике: средний чек от 19 000 руб.;</li>"
            "<li>при соблюдении протокола в практике обычно отмечают видимый косметологический эффект на 7-10 день;</li>"
            "<li>курс обычно составляет 3-4 процедуры.</li>"
            "</ul>"
            "<p><strong>Что важно по сотрудничеству:</strong></p>"
            "<ul>"
            "<li>доставка 3-4 дня;</li>"
            "<li>безналичный расчет;</li>"
            "<li>полная предоплата;</li>"
            "<li>при заказе от 2 шт. действует подарок, а при объеме от 100 шт. обсуждаются специальные условия.</li>"
            "</ul>"
            "<p>Если для вас направление актуально, можем отдельно обсудить формат спокойного тестового входа без тяжелой закупки, "
            "экономику процедуры под вашу практику и рабочие условия поставки.</p>"
            f"{attachment_html_note}"
            f"<p>Материалы: <a href=\"{DEFAULT_MATERIAL_URL}\">{DEFAULT_MATERIAL_URL}</a><br>"
            f"Сайт: <a href=\"{DEFAULT_PRODUCT_SITE}\">{DEFAULT_PRODUCT_SITE}</a><br>"
            f"Контакт для связи: {DEFAULT_MANAGER_PHONE}<br>"
            f"Telegram: {DEFAULT_MANAGER_TELEGRAM}</p>"
            f"<p>Если удобно, ответьте на это письмо или напишите в Telegram. Также можно согласовать короткий созвон, чтобы быстро обсудить условия и ответить на вопросы.</p>"
        )
        return {
            "to_email": to_email,
            "subject": subject,
            "text_body": text_body,
            "html_body": html_body,
            "attachments": attachments,
        }

    def row_email_keys(self, row):
        keys = set()
        for field in ("contact_email", "email_sent_to", "email", "email_address", "lead_id", "source_record_key"):
            for candidate in extract_emails(row.get(field, "")):
                keys.add(candidate)
        return keys

    def process_bounces(self, sheet_prefix="", limit_sheets=0, limit_messages=0):
        bounce_summary = {
            "ok": True,
            "enabled": self.bounce_watcher.enabled(),
            "bounces_checked": 0,
            "bounces_processed": 0,
            "bounces_matched": 0,
            "blacklisted_domains_added": 0,
            "bounce_results": [],
        }
        fetched = self.bounce_watcher.fetch_events(limit_messages=limit_messages)
        bounce_summary["bounces_checked"] = int(fetched.get("checked") or 0)
        bounce_summary["bounces_processed"] = int(fetched.get("processed") or 0)
        if not fetched.get("events"):
            return bounce_summary

        prefix = str(sheet_prefix or self.sheet_prefix).strip() or self.sheet_prefix
        spreadsheets = self.list_target_spreadsheets(prefix=prefix, limit_sheets=limit_sheets)
        seen_bounce_keys = set()
        for event in fetched.get("events") or []:
            bounce_key = (event.get("email", ""), event.get("bounce_type", ""))
            if bounce_key in seen_bounce_keys:
                continue
            seen_bounce_keys.add(bounce_key)
            if event.get("blacklisted_domain"):
                bounce_summary["blacklisted_domains_added"] += 1
            matched = False
            for spreadsheet in spreadsheets:
                spreadsheet_id = spreadsheet.get("id", "")
                if not spreadsheet_id:
                    continue
                spreadsheet_name = spreadsheet.get("name", "")
                sheet_name = self.google.resolve_sheet_name(spreadsheet_id, self.preferred_sheet_name)
                values = self.google.read_values(spreadsheet_id, sheet_name, range_suffix="A1:AZ")
                if not values:
                    continue
                header_map = self.google.ensure_headers(spreadsheet_id, sheet_name, values[0], EXTRA_HEADERS)
                rows = self.rows_from_values(values)
                grouped = self.group_rows(rows)
                for state in grouped.values():
                    row = self.merge_context(state)
                    if event["email"] not in self.row_email_keys(row):
                        continue
                    target_row_number = int(row.get("_target_row_number") or 0)
                    if not target_row_number:
                        continue
                    send_status = (
                        "manual_review"
                        if event.get("blacklisted_domain") or event.get("bounce_type") in FATAL_BOUNCE_TYPES
                        else "bounced"
                    )
                    updates = {
                        "contact_email": event["email"],
                        "email_send_status": send_status,
                        "email_verification_status": event["bounce_type"],
                        "email_last_error": event["human_reason"],
                        "email_bounced_at": now_iso(),
                        "email_bounce_reason": event["raw_reason"][:400],
                    }
                    if self.domain_blacklist.contains(event["email"]):
                        updates["email_blacklisted_at"] = now_iso()
                        updates["email_blacklist_reason"] = self.domain_blacklist.get(event["email"]).get("reason", "")
                    self.google.batch_update_row_fields(
                        spreadsheet_id,
                        sheet_name,
                        header_map,
                        target_row_number,
                        updates,
                    )
                    matched = True
                    bounce_summary["bounces_matched"] += 1
                    bounce_summary["bounce_results"].append(
                        {
                            "action": "bounce_processed",
                            "sheet_name": spreadsheet_name,
                            "email": event["email"],
                            "bounce_type": event["bounce_type"],
                            "lead_key": state["lead_key"],
                            "company_name": row.get("company_name", ""),
                        }
                    )
                    break
                if matched:
                    break
            if not matched:
                bounce_summary["bounce_results"].append(
                    {
                        "action": "bounce_unmatched",
                        "email": event["email"],
                        "bounce_type": event["bounce_type"],
                    }
                )
        return bounce_summary

    def process_group(self, spreadsheet_id, spreadsheet_name, sheet_name, header_map, state, dry_run=False, force_resend=False):
        row = self.merge_context(state)
        target_row_number = int(row.get("_target_row_number") or 0)
        seed_row_number = int(row.get("_seed_row_number") or 0)
        company_name = str(row.get("company_name") or "").strip()

        if not target_row_number:
            return {"action": "skipped", "reason": "no_target_row", "lead_key": state["lead_key"]}
        if as_bool(row.get("do_not_call")) or str(row.get("final_reason") or "").strip().lower() == "dnc":
            return {"action": "skipped", "reason": "dnc", "lead_key": state["lead_key"]}
        if not self.has_email_signal(row):
            return {"action": "skipped", "reason": "no_email_signal", "lead_key": state["lead_key"]}
        phone_primary = str(row.get("phone_primary") or "").strip()
        phone_secondary = str(row.get("phone_secondary") or "").strip()
        has_valid_phone = bool(normalize_phone(phone_primary) or normalize_phone(phone_secondary))
        if not has_valid_phone and not row.get("contact_email") and is_garbage_phone_value(phone_primary) and is_garbage_phone_value(phone_secondary):
            return {"action": "skipped", "reason": "low_quality_phone_data", "lead_key": state["lead_key"]}
        send_status = str(row.get("email_send_status") or "").strip().lower()
        verification_status = str(row.get("email_verification_status") or "").strip().lower()
        if send_status == "sent" and row.get("email_sent_at") and not force_resend:
            return {"action": "skipped", "reason": "already_sent", "lead_key": state["lead_key"]}
        retryable_manual_review = verification_status in {"not_found", "domain_check_failed", "domain_not_found"}
        if send_status == "manual_review" and not force_resend and not retryable_manual_review:
            return {"action": "skipped", "reason": "manual_review_pending", "lead_key": state["lead_key"]}
        if (
            send_status == "bounced"
            and not force_resend
            and (
                verification_status in FATAL_BOUNCE_TYPES
                or self.domain_blacklist.contains(row.get("contact_email"))
            )
        ):
            return {"action": "skipped", "reason": "fatal_bounce_pending_review", "lead_key": state["lead_key"]}
        if is_placeholder_company_name(company_name):
            updates = {
                "email_send_status": "manual_review",
                "email_last_error": "Подозрительное название компании; нужна ручная проверка",
            }
            if not dry_run:
                self.google.batch_update_row_fields(
                    spreadsheet_id, sheet_name, header_map, target_row_number, updates
                )
            return {
                "action": "needs_review",
                "reason": "company_name_placeholder",
                "lead_key": state["lead_key"],
                "company_name": company_name,
            }

        email_address, email_status = self.extract_row_email(row)
        source_url = str(row.get("email_source_url") or "").strip()
        verification_status = email_status
        if email_address:
            email_address = normalize_email_candidate(email_address).lower()
            if (
                not is_valid_email(email_address)
                or is_placeholder_email(email_address)
                or is_excluded_business_email(email_address)
            ):
                email_address = ""
                source_url = ""
                verification_status = ""

        if not email_address:
            candidate = self.resolve_best_email_candidate(row)
            if candidate:
                email_address = candidate.get("email", "")
                source_url = candidate.get("source_url", "")
                verification_status = candidate.get("resolution_status") or "verified_from_website"
            if not email_address:
                updates = {
                    "email_verified_at": now_iso(),
                    "email_verification_status": "not_found",
                    "email_send_status": "manual_review",
                    "email_last_error": "Email не найден на сайте по номеру или названию компании",
                }
                if not dry_run:
                    self.google.batch_update_row_fields(
                        spreadsheet_id, sheet_name, header_map, target_row_number, updates
                    )
                return {
                    "action": "needs_review",
                    "reason": "email_not_found",
                    "lead_key": state["lead_key"],
                    "company_name": row.get("company_name", ""),
                    "phone_primary": row.get("phone_primary", ""),
                }

        if self.domain_blacklist.contains(email_address):
            blacklist_reason = self.domain_blacklist.get(email_address).get("reason") or "Домен в локальном blacklist"
            updates = {
                "contact_email": email_address,
                "email_verified_at": now_iso(),
                "email_verification_status": "blacklisted_domain",
                "email_last_error": blacklist_reason,
                "email_send_status": "manual_review",
                "email_blacklisted_at": now_iso(),
                "email_blacklist_reason": blacklist_reason,
            }
            if not dry_run:
                self.google.batch_update_row_fields(
                    spreadsheet_id, sheet_name, header_map, target_row_number, updates
                )
            return {
                "action": "needs_review",
                "reason": "blacklisted_domain",
                "lead_key": state["lead_key"],
                "company_name": row.get("company_name", ""),
                "email": email_address,
            }

        domain_ok, domain_reason = check_email_domain_resolves(email_address)
        if not domain_ok:
            recovered = self.resolve_best_email_candidate(row, skip_email=email_address)
            if recovered:
                email_address = recovered.get("email", "")
                source_url = recovered.get("source_url", "")
                verification_status = recovered.get("resolution_status") or "verified_from_website"
                domain_ok, domain_reason = check_email_domain_resolves(email_address)
            if not domain_ok:
                status = "domain_not_found" if domain_reason == "domain_not_found" else "domain_check_failed"
                error_text = (
                    "Домен email не существует или не резолвится"
                    if domain_reason == "domain_not_found"
                    else "Не удалось проверить домен email"
                )
                updates = {
                    "contact_email": email_address,
                    "email_verified_at": now_iso(),
                    "email_verification_status": status,
                    "email_last_error": error_text,
                    "email_send_status": "manual_review",
                }
                if not dry_run:
                    self.google.batch_update_row_fields(
                        spreadsheet_id, sheet_name, header_map, target_row_number, updates
                    )
                return {
                    "action": "needs_review",
                    "reason": "email_domain_not_found" if domain_reason == "domain_not_found" else "email_domain_check_failed",
                    "lead_key": state["lead_key"],
                    "company_name": row.get("company_name", ""),
                    "email": email_address,
                }

        verify_updates = {
            "contact_email": email_address,
            "email_source_url": source_url,
            "email_verified_at": now_iso(),
            "email_verification_status": verification_status or "verified",
            "email_last_error": "",
        }
        if not dry_run:
            self.google.batch_update_row_fields(
                spreadsheet_id, sheet_name, header_map, target_row_number, verify_updates
            )
            if seed_row_number and seed_row_number != target_row_number:
                self.google.batch_update_row_fields(
                    spreadsheet_id,
                    sheet_name,
                    header_map,
                    seed_row_number,
                    {key: verify_updates[key] for key in SEED_SYNC_HEADERS},
                )

        if dry_run:
            return {
                "action": "dry_run_ready",
                "lead_key": state["lead_key"],
                "company_name": row.get("company_name", ""),
                "email": email_address,
                "verification_status": verification_status or "verified",
                "sheet_name": spreadsheet_name,
            }

        if not self.mailer.enabled():
            self.google.batch_update_row_fields(
                spreadsheet_id,
                sheet_name,
                header_map,
                target_row_number,
                {
                    "email_send_status": "smtp_not_configured",
                    "email_last_error": "SMTP не настроен",
                },
            )
            return {
                "action": "blocked",
                "reason": "smtp_not_configured",
                "lead_key": state["lead_key"],
                "email": email_address,
            }

        email_payload = self.build_email(row, email_address)
        self.google.batch_update_row_fields(
            spreadsheet_id,
            sheet_name,
            header_map,
            target_row_number,
            {
                "email_send_status": "sending",
                "email_last_error": "",
            },
        )
        try:
            self.mailer.send(
                to_email=email_payload["to_email"],
                subject=email_payload["subject"],
                text_body=email_payload["text_body"],
                html_body=email_payload["html_body"],
                attachments=email_payload.get("attachments") or [],
            )
        except Exception as exc:
            self.google.batch_update_row_fields(
                spreadsheet_id,
                sheet_name,
                header_map,
                target_row_number,
                {
                    "email_send_status": "send_failed",
                    "email_last_error": str(exc),
                },
            )
            return {
                "action": "error",
                "reason": "send_failed",
                "lead_key": state["lead_key"],
                "email": email_address,
                "error": str(exc),
            }

        self.google.batch_update_row_fields(
            spreadsheet_id,
            sheet_name,
            header_map,
            target_row_number,
            {
                "contact_email": email_address,
                "email_send_status": "sent",
                "email_sent_at": now_iso(),
                "email_sent_to": email_address,
                "email_last_error": "",
            },
        )
        return {
            "action": "sent",
            "lead_key": state["lead_key"],
            "company_name": row.get("company_name", ""),
            "email": email_address,
            "sheet_name": spreadsheet_name,
        }

    def run(self, dry_run=False, force_resend=False, sheet_prefix="", limit_sheets=0, max_records=0):
        prefix = str(sheet_prefix or self.sheet_prefix).strip() or self.sheet_prefix
        sheet_limit = int(limit_sheets or DEFAULT_MAX_SHEETS_PER_RUN)
        record_limit = self.max_records_limit(max_records or DEFAULT_MAX_RECORDS_PER_RUN)

        summary = {
            "ok": True,
            "service": "email_followup_service",
            "dry_run": bool(dry_run),
            "force_resend": bool(force_resend),
            "sheet_prefix": prefix,
            "target_spreadsheet_ids": list(self.target_spreadsheet_ids),
            "record_limit": record_limit,
            "limit_reached": False,
            "spreadsheets_found": 0,
            "groups_seen": 0,
            "records_processed": 0,
            "sent": 0,
            "dry_run_ready": 0,
            "needs_review": 0,
            "skipped": 0,
            "blocked": 0,
            "errors": 0,
            "results": [],
            "bounces_checked": 0,
            "bounces_processed": 0,
            "bounces_matched": 0,
            "blacklisted_domains_added": 0,
            "bounce_results": [],
            "sheet_summaries": [],
        }
        if not dry_run:
            bounce_summary = self.process_bounces(sheet_prefix=prefix, limit_sheets=sheet_limit)
            for key in ("bounces_checked", "bounces_processed", "bounces_matched", "blacklisted_domains_added"):
                summary[key] = int(bounce_summary.get(key) or 0)
            summary["bounce_results"] = list(bounce_summary.get("bounce_results") or [])

        spreadsheets = self.list_target_spreadsheets(prefix=prefix, limit_sheets=sheet_limit)
        summary["spreadsheets_found"] = len(spreadsheets)

        for spreadsheet in spreadsheets:
            if record_limit and summary["records_processed"] >= record_limit:
                summary["limit_reached"] = True
                break
            spreadsheet_id = spreadsheet.get("id", "")
            spreadsheet_name = spreadsheet.get("name", "")
            if not spreadsheet_id:
                continue
            sheet_name = self.google.resolve_sheet_name(spreadsheet_id, self.preferred_sheet_name)
            sheet_summary = {
                "spreadsheet_id": spreadsheet_id,
                "spreadsheet_name": spreadsheet_name,
                "sheet_name": sheet_name,
                "groups_seen": 0,
                "processed": 0,
                "sent": 0,
                "dry_run_ready": 0,
                "needs_review": 0,
                "blocked": 0,
                "errors": 0,
                "skipped": 0,
                "status": "no_new_records",
                "results": [],
            }
            values = self.google.read_values(spreadsheet_id, sheet_name, range_suffix="A1:AZ")
            if not values:
                sheet_summary["status"] = "empty_sheet"
                summary["sheet_summaries"].append(sheet_summary)
                continue
            header_map = self.google.ensure_headers(spreadsheet_id, sheet_name, values[0], EXTRA_HEADERS)
            rows = self.rows_from_values(values)
            if not rows:
                sheet_summary["status"] = "empty_sheet"
                summary["sheet_summaries"].append(sheet_summary)
                continue
            grouped = self.group_rows(rows)
            ordered_groups = sorted(
                grouped.values(),
                key=lambda item: (
                    (item.get("latest_event_row") or item.get("latest_row") or {}).get("_row_number", 0)
                ),
                reverse=True,
            )

            for state in ordered_groups:
                if record_limit and summary["records_processed"] >= record_limit:
                    summary["limit_reached"] = True
                    break
                summary["groups_seen"] += 1
                sheet_summary["groups_seen"] += 1
                result = self.process_group(
                    spreadsheet_id=spreadsheet_id,
                    spreadsheet_name=spreadsheet_name,
                    sheet_name=sheet_name,
                    header_map=header_map,
                    state=state,
                    dry_run=dry_run,
                    force_resend=force_resend,
                )
                action = result.get("action", "unknown")
                if action == "sent":
                    summary["sent"] += 1
                    summary["records_processed"] += 1
                    sheet_summary["sent"] += 1
                    sheet_summary["processed"] += 1
                elif action == "dry_run_ready":
                    summary["dry_run_ready"] += 1
                    summary["records_processed"] += 1
                    sheet_summary["dry_run_ready"] += 1
                    sheet_summary["processed"] += 1
                elif action == "needs_review":
                    summary["needs_review"] += 1
                    summary["records_processed"] += 1
                    sheet_summary["needs_review"] += 1
                    sheet_summary["processed"] += 1
                elif action == "blocked":
                    summary["blocked"] += 1
                    summary["records_processed"] += 1
                    sheet_summary["blocked"] += 1
                    sheet_summary["processed"] += 1
                elif action == "error":
                    summary["errors"] += 1
                    summary["records_processed"] += 1
                    sheet_summary["errors"] += 1
                    sheet_summary["processed"] += 1
                else:
                    summary["skipped"] += 1
                    sheet_summary["skipped"] += 1
                if action != "skipped":
                    summary["results"].append(result)
                    sheet_summary["results"].append(result)

            if sheet_summary["processed"] > 0:
                sheet_summary["status"] = "updated"
            elif sheet_summary["groups_seen"] == 0:
                sheet_summary["status"] = "empty_sheet"
            else:
                sheet_summary["status"] = "no_new_records"
            summary["sheet_summaries"].append(sheet_summary)

        if self.telegram.should_notify(summary):
            try:
                telegram_response = self.telegram.send_message(self.telegram.format_summary(summary))
                summary["telegram_report"] = {"ok": True, "result": telegram_response.get("ok", True)}
            except Exception as exc:
                summary["telegram_report"] = {"ok": False, "error": str(exc)}

        return summary

    def send_test_email(self, to_email=""):
        recipient = str(to_email or os.getenv("EMAIL_FOLLOWUP_TEST_RECIPIENT", "")).strip()
        if not recipient:
            raise RuntimeError("Не задан test recipient")
        if not is_valid_email(recipient):
            raise RuntimeError("Test recipient is invalid")
        if not self.mailer.enabled():
            raise RuntimeError("SMTP не настроен")

        sent_at = now_iso()
        subject = f"SMTP test: {DEFAULT_PRODUCT_NAME}"
        text_body = (
            f"Это тестовое письмо для проверки SMTP-контура {DEFAULT_PRODUCT_NAME}.\n\n"
            f"Сервис email_followup_service успешно собрал и отправил это письмо.\n"
            f"Время UTC: {sent_at}\n"
        )
        html_body = (
            f"<p>Это тестовое письмо для проверки SMTP-контура <strong>{DEFAULT_PRODUCT_NAME}</strong>.</p>"
            f"<p>Сервис <code>email_followup_service</code> успешно собрал и отправил это письмо.</p>"
            f"<p>Время UTC: {sent_at}</p>"
        )
        attachments = self.build_email_attachments(strict=True)
        if attachments:
            text_body += f"\nВо вложении приложен файл: {attachments[0].get('filename', '')}\n"
            html_body += f"<p>Во вложении приложен файл: <strong>{attachments[0].get('filename', '')}</strong></p>"
        self.mailer.send(
            to_email=recipient,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            attachments=attachments,
        )
        return {
            "ok": True,
            "service": "email_followup_service",
            "action": "send_test_email",
            "to_email": recipient,
            "sent_at": sent_at,
            "attachments": [item.get("filename", "") for item in attachments],
        }

    def process_bounces_only(self, sheet_prefix="", limit_sheets=0, limit_messages=0):
        result = self.process_bounces(
            sheet_prefix=sheet_prefix or self.sheet_prefix,
            limit_sheets=limit_sheets,
            limit_messages=limit_messages,
        )
        if self.telegram.should_notify(result):
            try:
                telegram_response = self.telegram.send_message(self.telegram.format_summary(result))
                result["telegram_report"] = {"ok": True, "result": telegram_response.get("ok", True)}
            except Exception as exc:
                result["telegram_report"] = {"ok": False, "error": str(exc)}
        return result


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class EmailFollowupRequestHandler(BaseHTTPRequestHandler):
    service_factory_kwargs = {
        "sheet_prefix": DEFAULT_SHEET_PREFIX,
        "preferred_sheet_name": DEFAULT_SHEET_NAME,
    }

    @classmethod
    def build_service(cls):
        return EmailFollowupService(
            sheet_prefix=cls.service_factory_kwargs.get("sheet_prefix", DEFAULT_SHEET_PREFIX),
            preferred_sheet_name=cls.service_factory_kwargs.get("preferred_sheet_name", DEFAULT_SHEET_NAME),
        )

    def _authorized(self):
        expected = os.getenv("EMAIL_FOLLOWUP_AUTH_TOKEN", "").strip()
        if not expected:
            return True
        received = self.headers.get("Authorization", "").strip()
        return received == f"Bearer {expected}"

    def _send(self, code, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except BrokenPipeError:
            return

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        body = self.rfile.read(length).decode("utf-8")
        return json.loads(body) if body else {}

    def do_GET(self):
        try:
            if not self._authorized():
                self._send(401, {"ok": False, "error": "Unauthorized"})
                return
            if self.path == "/health":
                self._send(200, self.build_service().health())
                return
            self._send(404, {"ok": False, "error": "Not found"})
        except Exception as exc:
            self._send(500, {"ok": False, "error": str(exc)})

    def do_POST(self):
        try:
            if not self._authorized():
                self._send(401, {"ok": False, "error": "Unauthorized"})
                return
            payload = self._read_json()
            service = self.build_service()
            if self.path == "/run":
                result = service.run(
                    dry_run=as_bool(payload.get("dry_run")),
                    force_resend=as_bool(payload.get("force_resend")),
                    sheet_prefix=payload.get("sheet_prefix", ""),
                    limit_sheets=int(payload.get("limit_sheets") or 0),
                    max_records=int(payload.get("max_records") or 0),
                )
                self._send(200, result)
                return
            if self.path == "/process-bounces":
                result = service.process_bounces_only(
                    sheet_prefix=payload.get("sheet_prefix", ""),
                    limit_sheets=int(payload.get("limit_sheets") or 0),
                    limit_messages=int(payload.get("limit_messages") or 0),
                )
                self._send(200, result)
                return
            if self.path == "/send-test":
                result = service.send_test_email(to_email=payload.get("to_email", ""))
                self._send(200, result)
                return
            self._send(404, {"ok": False, "error": "Not found"})
        except Exception as exc:
            self._send(500, {"ok": False, "error": str(exc)})

    def log_message(self, format, *args):
        return


def run_server(args):
    EmailFollowupRequestHandler.service_factory_kwargs = {
        "sheet_prefix": args.sheet_prefix,
        "preferred_sheet_name": args.sheet_name,
    }
    server = ThreadingHTTPServer((args.host, args.port), EmailFollowupRequestHandler)
    print(f"Email followup service listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


def run_once(args):
    service = EmailFollowupService(
        sheet_prefix=args.sheet_prefix,
        preferred_sheet_name=args.sheet_name,
    )
    result = service.run(
        dry_run=args.dry_run,
        force_resend=args.force_resend,
        sheet_prefix=args.sheet_prefix,
        limit_sheets=args.limit_sheets,
        max_records=args.max_records,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def run_send_test(args):
    service = EmailFollowupService(
        sheet_prefix=args.sheet_prefix,
        preferred_sheet_name=args.sheet_name,
    )
    result = service.send_test_email(to_email=args.to_email)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def run_process_bounces(args):
    service = EmailFollowupService(
        sheet_prefix=args.sheet_prefix,
        preferred_sheet_name=args.sheet_name,
    )
    result = service.process_bounces_only(
        sheet_prefix=args.sheet_prefix,
        limit_sheets=args.limit_sheets,
        limit_messages=args.limit_messages,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(description="Email followup service for cosmetology contact sheets")
    parser.add_argument("--sheet-prefix", default=DEFAULT_SHEET_PREFIX)
    parser.add_argument("--sheet-name", default=DEFAULT_SHEET_NAME)

    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run HTTP service")
    serve.add_argument("--host", default=DEFAULT_HOST)
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    serve.set_defaults(handler=run_server)

    run = subparsers.add_parser("run", help="Run one batch")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--force-resend", action="store_true")
    run.add_argument("--limit-sheets", type=int, default=DEFAULT_MAX_SHEETS_PER_RUN)
    run.add_argument("--max-records", type=int, default=DEFAULT_MAX_RECORDS_PER_RUN)
    run.set_defaults(handler=run_once)

    send_test = subparsers.add_parser("send-test", help="Send SMTP smoke-test email")
    send_test.add_argument("--to-email", default="")
    send_test.set_defaults(handler=run_send_test)

    process_bounces = subparsers.add_parser("process-bounces", help="Process bounce emails via IMAP")
    process_bounces.add_argument("--limit-sheets", type=int, default=DEFAULT_MAX_SHEETS_PER_RUN)
    process_bounces.add_argument("--limit-messages", type=int, default=DEFAULT_BOUNCE_SCAN_LIMIT)
    process_bounces.set_defaults(handler=run_process_bounces)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
