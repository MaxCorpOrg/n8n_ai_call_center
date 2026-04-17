#!/usr/bin/env python3
import argparse
import json
import os
import re
import smtplib
import socket
import ssl
import time
import urllib.parse
from email.message import EmailMessage
from email.utils import formataddr
from html import unescape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
DEFAULT_REPLY_TO = os.getenv("EMAIL_FOLLOWUP_REPLY_TO", "").strip()
DEFAULT_SUBJECT_TEMPLATE = (
    os.getenv("EMAIL_FOLLOWUP_SUBJECT_TEMPLATE", "Информация по {product_name} для {company_name}").strip()
    or "Информация по {product_name} для {company_name}"
)

TRUTHY = {"1", "true", "yes", "y", "on", "да"}
DNS_CHECK_TIMEOUT = 8
DNS_CACHE = {}
EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.IGNORECASE)
SEARCH_RESULT_LINK_PATTERN = re.compile(
    r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"', re.IGNORECASE
)
HREF_PATTERN = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
EMAIL_SIGNAL_PATTERN = re.compile(r"(почт|e-mail|email|на\s+почту|mail)", re.IGNORECASE)
DIRECTORY_HOSTS = {
    "2gis.ru",
    "www.2gis.ru",
    "yandex.ru",
    "yandex.com",
    "yandex.by",
    "maps.yandex.ru",
    "yandex.com.tr",
    "prodoctorov.ru",
    "zoon.ru",
    "flamp.ru",
    "vk.com",
    "t.me",
    "telegram.me",
    "wa.me",
    "whatsapp.com",
    "instagram.com",
    "facebook.com",
    "ok.ru",
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
]
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


def normalize_company_name(value):
    return re.sub(r"[^a-zа-я0-9]+", "", str(value or "").lower())


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
            except Exception:
                continue
            urls = []
            for raw_url in SEARCH_RESULT_LINK_PATTERN.findall(response.text or ""):
                candidate = unescape(raw_url)
                if "duckduckgo.com/l/?" in candidate:
                    parsed = urllib.parse.urlparse(candidate)
                    params = urllib.parse.parse_qs(parsed.query)
                    candidate = (params.get("uddg") or [""])[0]
                candidate = clean_url(candidate)
                if not candidate:
                    continue
                host = urllib.parse.urlparse(candidate).netloc.lower()
                if host in DIRECTORY_HOSTS:
                    continue
                urls.append(candidate)
            for item in dedupe_keep_order(urls):
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

    def page_matches(self, html, row):
        if not html:
            return False
        body = str(html or "")
        body_digits = re.sub(r"\D+", "", body)
        company_key = normalize_company_name(row.get("company_name"))
        for phone_field in ("phone_primary", "phone_secondary"):
            phone = normalize_phone(row.get(phone_field))
            if not phone:
                continue
            digits = re.sub(r"\D+", "", phone)
            if digits and (digits in body_digits or digits[-10:] in body_digits):
                return True
        if company_key and company_key in normalize_company_name(body):
            return True
        return False

    def score_email(self, email_address, page_url):
        parsed = urllib.parse.urlparse(page_url)
        page_root = approx_root_domain(parsed.netloc)
        local_part, _, domain = email_address.partition("@")
        score = 0
        if approx_root_domain(domain) == page_root:
            score += 8
        if local_part in {"info", "mail", "hello", "office", "sales", "contact", "admin"}:
            score += 3
        if "noreply" in local_part or "no-reply" in local_part:
            score -= 10
        if domain in {"example.com", "example.org", "example.net"}:
            score -= 20
        return score

    def resolve(self, row):
        deadline = resolver_deadline(RESOLVER_TOTAL_TIMEOUT)
        explicit_urls = []
        for field in ("website_url", "website", "site_url", "site", "url", "domain"):
            value = clean_url(row.get(field))
            if value:
                explicit_urls.append(value)

        phone_queries = []
        for phone_field in ("phone_primary", "phone_secondary"):
            phone = normalize_phone(row.get(phone_field))
            if phone:
                phone_queries.append(f'"{phone}" "{row.get("company_name", "").strip()}" email')
                phone_queries.append(f'"{phone}" "{row.get("company_name", "").strip()}" контакты')
                phone_queries.append(f'"{phone}" email')
        company = str(row.get("company_name") or "").strip()
        city = str(row.get("city") or "").strip()
        if company:
            phone_queries.append(f'"{company}" "{city}" email')
            phone_queries.append(f'"{company}" "{city}" контакты')

        url_candidates = dedupe_keep_order(
            explicit_urls + self.search_urls(phone_queries, limit=RESOLVER_SEARCH_LIMIT, deadline=deadline)
        )[:RESOLVER_SEARCH_LIMIT]
        if not url_candidates:
            return {}

        for candidate_url in url_candidates:
            if remaining_seconds(deadline) <= 0:
                break
            visited = set()
            queue = [candidate_url]
            first_html = ""
            while queue and len(visited) < RESOLVER_MAX_VISITS:
                if remaining_seconds(deadline) <= 0:
                    break
                current_url = queue.pop(0)
                if current_url in visited:
                    continue
                visited.add(current_url)
                html = self.fetch_html(current_url, deadline=deadline)
                if not html:
                    continue
                if not first_html:
                    first_html = html
                    for extra_url in self.same_domain_contact_urls(candidate_url, first_html):
                        if extra_url not in visited:
                            queue.append(extra_url)
                emails = extract_emails(html)
                if not emails:
                    continue
                if not self.page_matches(html, row) and current_url != candidate_url:
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
                    }
        return {}


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

    def send(self, to_email, subject, text_body, html_body=""):
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


class EmailFollowupService:
    def __init__(self, sheet_prefix=DEFAULT_SHEET_PREFIX, preferred_sheet_name=DEFAULT_SHEET_NAME):
        self.sheet_prefix = sheet_prefix
        self.preferred_sheet_name = preferred_sheet_name
        self.google = GoogleSheetsClient(drive_folder_id=DEFAULT_DRIVE_FOLDER_ID)
        self.resolver = WebsiteEmailResolver(
            firecrawl=FirecrawlClient(
                base_url=DEFAULT_FIRECRAWL_BASE_URL,
                api_key=DEFAULT_FIRECRAWL_API_KEY,
            )
        )
        self.mailer = SmtpEmailSender()

    def health(self):
        return {
            "ok": True,
            "service": "email_followup_service",
            "sheet_prefix": self.sheet_prefix,
            "preferred_sheet_name": self.preferred_sheet_name,
            "drive_folder_id": DEFAULT_DRIVE_FOLDER_ID,
            "firecrawl_enabled": self.resolver.firecrawl.enabled(),
            "smtp_enabled": self.mailer.enabled(),
            "test_recipient": os.getenv("EMAIL_FOLLOWUP_TEST_RECIPIENT", "").strip(),
        }

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
            email_candidates = extract_emails(row.get(field, ""))
            if email_candidates:
                status = "from_sheet"
                if field not in {"contact_email", "email", "email_address", "client_email", "customer_email"}:
                    status = "from_misplaced_field"
                return email_candidates[0], status
        for field in ("notes_short", "notes_redacted"):
            email_candidates = extract_emails(row.get(field, ""))
            if email_candidates:
                return email_candidates[0], "from_notes"
        return "", ""

    def build_email(self, row, to_email):
        contact_name = str(row.get("contact_name") or "").strip()
        company_name_raw = str(row.get("company_name") or "").strip()
        company_name_for_subject = company_name_raw or "клиники"
        subject = DEFAULT_SUBJECT_TEMPLATE.format(
            product_name=DEFAULT_PRODUCT_NAME,
            company_name=company_name_for_subject,
            contact_name=contact_name or company_name_for_subject,
        )
        salutation = contact_name or company_name_raw or "Коллеги"
        text_body = (
            f"Здравствуйте, {salutation}!\n\n"
            f"Отправляем информацию по продукту {DEFAULT_PRODUCT_NAME}, как и договаривались.\n\n"
            f"{DEFAULT_PRODUCT_NAME} используется в косметологической практике по направлению коррекции фигуры.\n"
            f"Если будет удобно, можно отдельно обсудить формат входа, стоимость и рабочие условия поставки.\n\n"
            f"Материалы: {DEFAULT_MATERIAL_URL}\n"
            f"Сайт: {DEFAULT_PRODUCT_SITE}\n"
            f"Контакт для связи: {DEFAULT_MANAGER_PHONE}\n"
            f"Telegram: {DEFAULT_MANAGER_TELEGRAM}\n\n"
            f"Если удобно, ответьте на это письмо или напишите в Telegram.\n"
        )
        html_body = (
            f"<p>Здравствуйте, {salutation}!</p>"
            f"<p>Отправляем информацию по продукту <strong>{DEFAULT_PRODUCT_NAME}</strong>, как и договаривались.</p>"
            f"<p>{DEFAULT_PRODUCT_NAME} используется в косметологической практике по направлению коррекции фигуры. "
            f"Если будет удобно, можно отдельно обсудить формат входа, стоимость и рабочие условия поставки.</p>"
            f"<p>Материалы: <a href=\"{DEFAULT_MATERIAL_URL}\">{DEFAULT_MATERIAL_URL}</a><br>"
            f"Сайт: <a href=\"{DEFAULT_PRODUCT_SITE}\">{DEFAULT_PRODUCT_SITE}</a><br>"
            f"Контакт для связи: {DEFAULT_MANAGER_PHONE}<br>"
            f"Telegram: {DEFAULT_MANAGER_TELEGRAM}</p>"
            f"<p>Если удобно, ответьте на это письмо или напишите в Telegram.</p>"
        )
        return {
            "to_email": to_email,
            "subject": subject,
            "text_body": text_body,
            "html_body": html_body,
        }

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
        send_status = str(row.get("email_send_status") or "").strip().lower()
        if send_status == "sent" and row.get("email_sent_at") and not force_resend:
            return {"action": "skipped", "reason": "already_sent", "lead_key": state["lead_key"]}
        if send_status == "manual_review" and not force_resend:
            return {"action": "skipped", "reason": "manual_review_pending", "lead_key": state["lead_key"]}
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

        if not email_address:
            resolved = self.resolver.resolve(row)
            if resolved:
                email_address = resolved.get("email", "")
                source_url = resolved.get("source_url", "")
                verification_status = "verified_from_website"
            else:
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
        record_limit = int(max_records or DEFAULT_MAX_RECORDS_PER_RUN)
        spreadsheets = self.google.list_prefixed_sheets(prefix, limit=sheet_limit)

        summary = {
            "ok": True,
            "service": "email_followup_service",
            "dry_run": bool(dry_run),
            "force_resend": bool(force_resend),
            "sheet_prefix": prefix,
            "spreadsheets_found": len(spreadsheets),
            "groups_seen": 0,
            "records_processed": 0,
            "sent": 0,
            "dry_run_ready": 0,
            "needs_review": 0,
            "skipped": 0,
            "blocked": 0,
            "errors": 0,
            "results": [],
        }

        for spreadsheet in spreadsheets:
            if summary["records_processed"] >= record_limit:
                break
            spreadsheet_id = spreadsheet.get("id", "")
            spreadsheet_name = spreadsheet.get("name", "")
            if not spreadsheet_id:
                continue
            sheet_name = self.google.resolve_sheet_name(spreadsheet_id, self.preferred_sheet_name)
            values = self.google.read_values(spreadsheet_id, sheet_name, range_suffix="A1:AZ")
            if not values:
                continue
            header_map = self.google.ensure_headers(spreadsheet_id, sheet_name, values[0], EXTRA_HEADERS)
            rows = self.rows_from_values(values)
            grouped = self.group_rows(rows)
            ordered_groups = sorted(
                grouped.values(),
                key=lambda item: (
                    (item.get("latest_event_row") or item.get("latest_row") or {}).get("_row_number", 0)
                ),
                reverse=True,
            )

            for state in ordered_groups:
                if summary["records_processed"] >= record_limit:
                    break
                summary["groups_seen"] += 1
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
                elif action == "dry_run_ready":
                    summary["dry_run_ready"] += 1
                    summary["records_processed"] += 1
                elif action == "needs_review":
                    summary["needs_review"] += 1
                    summary["records_processed"] += 1
                elif action == "blocked":
                    summary["blocked"] += 1
                    summary["records_processed"] += 1
                elif action == "error":
                    summary["errors"] += 1
                    summary["records_processed"] += 1
                else:
                    summary["skipped"] += 1
                if action != "skipped":
                    summary["results"].append(result)

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
        self.mailer.send(to_email=recipient, subject=subject, text_body=text_body, html_body=html_body)
        return {
            "ok": True,
            "service": "email_followup_service",
            "action": "send_test_email",
            "to_email": recipient,
            "sent_at": sent_at,
        }


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class EmailFollowupRequestHandler(BaseHTTPRequestHandler):
    service = None

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
                self._send(200, self.service.health())
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
            if self.path == "/run":
                result = self.service.run(
                    dry_run=as_bool(payload.get("dry_run")),
                    force_resend=as_bool(payload.get("force_resend")),
                    sheet_prefix=payload.get("sheet_prefix", ""),
                    limit_sheets=int(payload.get("limit_sheets") or 0),
                    max_records=int(payload.get("max_records") or 0),
                )
                self._send(200, result)
                return
            if self.path == "/send-test":
                result = self.service.send_test_email(to_email=payload.get("to_email", ""))
                self._send(200, result)
                return
            self._send(404, {"ok": False, "error": "Not found"})
        except Exception as exc:
            self._send(500, {"ok": False, "error": str(exc)})

    def log_message(self, format, *args):
        return


def run_server(args):
    EmailFollowupRequestHandler.service = EmailFollowupService(
        sheet_prefix=args.sheet_prefix,
        preferred_sheet_name=args.sheet_name,
    )
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
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
