#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import html
import json
import os
import random
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from zoneinfo import ZoneInfo

import requests

STATE_VERSION = 1
MSK_TZ = ZoneInfo("Europe/Moscow")
DEFAULT_STATE_PATH = Path.home() / ".local" / "share" / "telegram-sandbox-activity-runner" / "state.json"
DEFAULT_RUNS_DIR_NAME = "runs"
DEFAULT_HISTORY_LIMIT = 2000
DEFAULT_SITE_CONTROL_KIT_ROOT = Path.home() / "site-control-kit"
DEFAULT_API_SIDECAR_SESSION_DIR = Path.home() / ".local" / "share" / "telegram-sandbox-activity-runner" / "api_sessions"
DEFAULT_ENABLED_ACTIONS = ("send_message", "open_chat", "idle_scroll")
DEFAULT_ACTION_WEIGHTS = {
    "send_message": 5,
    "open_chat": 2,
    "idle_scroll": 1,
}
ALLOWED_ACTIONS = {"send_message", "open_chat", "idle_scroll"}
ALLOWED_API_SIDECAR_MODES = {"portable_only", "api_first", "api_only"}
CHAT_READY_SELECTOR = "#LeftColumn, #column-left, a.chatlist-chat, .chatlist-chat"
TELEGRAM_WEB_HOST_RE = re.compile(r"^web\.telegram\.org$", re.IGNORECASE)
EXTERNAL_LINK_RE = re.compile(r"(https?://|t\.me/)", re.IGNORECASE)
COMPOSER_SELECTORS = (
    ".chat-input-main .input-message-input[contenteditable='true']:not(.input-field-input-fake)",
    ".chat-input .input-message-input[contenteditable='true']:not(.input-field-input-fake)",
    ".new-message-wrapper .input-message-input[contenteditable='true']:not(.input-field-input-fake)",
    "#editable-message-text",
    ".input-message-input[contenteditable='true']",
    ".input-message-input",
    ".composer_rich_textarea",
    ".new-message-wrapper [contenteditable='true']",
)
CHAT_SCROLL_SELECTORS = (
    "#MiddleColumn .bubbles-inner",
    "#MiddleColumn .bubbles",
    ".bubbles-inner",
    ".bubbles",
    ".messages-container",
)
CHAT_INFO_CLICK_SELECTORS = (
    "#MiddleColumn .chat-info",
    "#MiddleColumn header",
    ".chat-info",
    "header",
)
RIGHT_SIDEBAR_SELECTORS = (
    "#column-right .profile-content",
    "#column-right .profile-container",
    "#column-right .sidebar-content",
)
ADD_MEMBERS_OPEN_SELECTORS = (
    "#column-right .profile-container.can-add-members button.btn-circle.btn-corner",
    "#column-right .profile-container.can-add-members button.btn-circle",
    ".profile-container.can-add-members button.btn-circle.btn-corner",
)
ADD_MEMBERS_SEARCH_SELECTOR = ".add-members-container .selector-search-input"
ADD_MEMBERS_CONFIRM_SELECTOR = ".add-members-container > .sidebar-content > button.btn-circle.btn-corner"
ADD_MEMBERS_POPUP_ADD_SELECTOR = ".popup-add-members .popup-buttons button:nth-child(1)"
JOIN_BUTTON_TERMS = ("Join", "Join Group", "Join Channel", "Вступить", "Присоединиться")
DESKTOP_ADD_CONTACT_X_RATIO = 0.3364
DESKTOP_ADD_CONTACT_Y_RATIO = 0.5417
DESKTOP_DONE_CONTACT_X_RATIO = 0.5785
DESKTOP_DONE_CONTACT_Y_RATIO = 0.7956
DESKTOP_ADD_CONTACT_BUTTON_TERMS = ("ДОБАВИТЬ КОНТАКТ", "Добавить контакт", "ADD TO CONTACTS", "Add to contacts")
DESKTOP_ADD_TO_CONTACTS_CHAT_TERMS = ("В КОНТАКТЫ", "TO CONTACTS")
DESKTOP_DONE_BUTTON_TERMS = ("Готово", "Done")
DESKTOP_FIRST_NAME_TERMS = ("Имя", "First name")
DESKTOP_LAST_NAME_TERMS = ("Фамилия", "Last name")
DESKTOP_CONTACT_EDIT_TERMS = ("ИЗМЕНИТЬ КОНТАКТ", "Изменить контакт", "EDIT CONTACT", "Edit contact")
DESKTOP_CONTACT_DELETE_TERMS = ("УДАЛИТЬ КОНТАКТ", "Удалить контакт", "DELETE CONTACT", "Delete contact")
DESKTOP_SEARCH_TERMS = ("Поиск", "Search")
DESKTOP_CHAT_INFO_TERMS = ("Информация", "Info")
DESKTOP_CHAT_MENU_TERMS = ("Меню чата", "Chat menu")
DESKTOP_SHOW_PROFILE_TERMS = ("Показать профиль", "Show profile")
DESKTOP_PROFILE_HEADER_X_RATIO = 0.37
DESKTOP_PROFILE_HEADER_Y_RATIO = 0.047
DESKTOP_SEARCH_RESULT_X_RATIO = 0.105
DESKTOP_SEARCH_RESULT_Y_RATIO = 0.134
DESKTOP_SEARCH_RESULT_STEP_Y_RATIO = 0.096

CHAT_SNAPSHOT_SCRIPT = r"""
const compact = (value) => String(value || "").replace(/\s+/g, " ").trim();
const firstText = (selectors) => {
  for (const selector of selectors) {
    const node = document.querySelector(selector);
    const text = compact(node?.innerText || node?.textContent || node?.getAttribute?.("aria-label") || "");
    if (text) return text;
  }
  return "";
};
const currentUrl = String(window.location.href || "");
const currentFragment = currentUrl.includes("#") ? currentUrl.split("#").slice(1).join("#") : "";
const headerTitle = firstText([
  "#MiddleColumn .chat-info .peer-title",
  ".chat-info .peer-title",
  "#MiddleColumn header .peer-title",
  "header .peer-title",
  "#column-right .profile-name .peer-title",
  ".profile-content .profile-name .peer-title",
]);
const headerSubtitle = firstText([
  "#MiddleColumn .chat-info .info",
  ".chat-info .info",
  "header .info",
  ".profile-content .subtitle",
]);
const dialogSelectors = [
  "#LeftColumn a.chatlist-chat",
  "#column-left a.chatlist-chat",
  "a.chatlist-chat",
  "a[href^='#'][data-peer-id]"
];
const dialogs = [];
const seenFragments = new Set();
for (const selector of dialogSelectors) {
  for (const anchor of Array.from(document.querySelectorAll(selector))) {
    const href = compact(anchor.getAttribute("href") || "");
    const peerId = compact(anchor.getAttribute("data-peer-id") || "");
    const fragment = href.startsWith("#") ? href.slice(1) : peerId;
    if (!fragment || seenFragments.has(fragment)) continue;
    const title = firstText([
      `${selector}[href='${href}'] .fullName`,
      `${selector}[href='${href}'] .peer-title-inner`,
      `${selector}[href='${href}'] .peer-title`,
      `${selector}[href='${href}'] [dir='auto']`,
    ]) || compact(anchor.innerText || anchor.textContent || "");
    const row = anchor.closest("a, .ListItem, .chatlist-chat") || anchor;
    const active = row.classList.contains("active") || anchor.classList.contains("active") || anchor.getAttribute("aria-current") === "true";
    dialogs.push({
      title,
      fragment,
      peer_id: peerId,
      active,
    });
    seenFragments.add(fragment);
  }
  if (dialogs.length) break;
}
const activeDialog = dialogs.find((item) => item.active) || {};
let composerSelector = "";
let composerText = "";
for (const selector of (args.selectors || [])) {
  const node = document.querySelector(selector);
  if (!node) continue;
  composerSelector = selector;
  composerText = compact(node.innerText || node.textContent || node.value || "");
  break;
}
return {
  current_url: currentUrl,
  current_fragment: currentFragment,
  document_title: String(document.title || ""),
  chat_title: headerTitle,
  chat_subtitle: headerSubtitle,
  active_dialog_title: compact(activeDialog.title || ""),
  active_dialog_fragment: compact(activeDialog.fragment || ""),
  composer_present: Boolean(composerSelector),
  composer_selector: composerSelector,
  composer_text: composerText,
  dialog_count: dialogs.length,
};
"""

SET_COMPOSER_TEXT_SCRIPT = r"""
const selectors = Array.isArray(args.selectors) ? args.selectors : [];
const payloadText = String(args.text || "");
const dispatchInput = (node) => {
  for (const eventName of ["input", "change", "keyup"]) {
    node.dispatchEvent(new Event(eventName, { bubbles: true }));
  }
};
const setCaretToEnd = (node) => {
  try {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(node);
    range.collapse(false);
    selection.removeAllRanges();
    selection.addRange(range);
  } catch (_error) {
  }
};
for (const selector of selectors) {
  const node = document.querySelector(selector);
  if (!node) continue;
  node.focus();
  if (node.isContentEditable) {
    node.innerHTML = "";
    const lines = payloadText.split(/\n/);
    lines.forEach((line, index) => {
      if (index > 0) {
        node.appendChild(document.createElement("br"));
      }
      node.appendChild(document.createTextNode(line));
    });
    setCaretToEnd(node);
    dispatchInput(node);
    return {
      selector,
      text: String(node.innerText || node.textContent || "").replace(/\s+/g, " ").trim(),
      ok: true,
    };
  }
  if ("value" in node) {
    node.value = payloadText;
    dispatchInput(node);
    return {
      selector,
      text: String(node.value || "").replace(/\s+/g, " ").trim(),
      ok: true,
    };
  }
}
throw new Error("Telegram composer not found");
"""

READ_COMPOSER_TEXT_SCRIPT = r"""
const compact = (value) => String(value || "").replace(/\s+/g, " ").trim();
for (const selector of (args.selectors || [])) {
  const node = document.querySelector(selector);
  if (!node) continue;
  return {
    selector,
    text: compact(node.innerText || node.textContent || node.value || ""),
    ok: true,
  };
}
return { selector: "", text: "", ok: false };
"""

SCROLL_CHAT_SCRIPT = r"""
const selectors = Array.isArray(args.selectors) ? args.selectors : [];
const deltaY = Number(args.delta_y || 0);
for (const selector of selectors) {
  const node = document.querySelector(selector);
  if (!node) continue;
  const beforeTop = Number(node.scrollTop || 0);
  node.scrollTop = beforeTop + deltaY;
  const afterTop = Number(node.scrollTop || 0);
  return {
    selector,
    before_top: beforeTop,
    after_top: afterTop,
    moved: Math.abs(afterTop - beforeTop) >= 1,
    ok: true,
  };
}
throw new Error("Telegram chat scroll container not found");
"""

FIND_VISIBLE_TEXT_SCRIPT = r"""
const compact = (value) => String(value || "").replace(/\s+/g, " ").trim();
const terms = (Array.isArray(args.terms) ? args.terms : []).map((item) => compact(item).toLowerCase()).filter(Boolean);
const rootSelector = String(args.root_selector || "").trim();
const root = rootSelector ? document.querySelector(rootSelector) : document.body;
if (!root) {
  return { ok: false, text: "", found: false };
}
const visible = (node) => {
  if (!node) return false;
  const rect = node.getBoundingClientRect();
  if (rect.width < 4 || rect.height < 4) return false;
  const style = window.getComputedStyle(node);
  return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity || "1") !== 0;
};
const nodes = Array.from(root.querySelectorAll("button, a, div, span"));
for (const node of nodes) {
  if (!visible(node)) continue;
  const text = compact(node.innerText || node.textContent || node.getAttribute?.("aria-label") || "");
  if (!text) continue;
  const lowered = text.toLowerCase();
  if (terms.some((term) => lowered.includes(term))) {
    return { ok: true, found: true, text };
  }
}
return { ok: true, found: false, text: "" };
"""


class ConfigError(ValueError):
    pass


class ExecutionSafetyError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def now_msk_parts() -> dict[str, str]:
    current = datetime.now(MSK_TZ)
    return {
        "date_msk": current.strftime("%Y-%m-%d"),
        "time_msk": current.strftime("%H:%M:%S"),
        "weekday_msk": current.strftime("%A"),
    }


def parse_iso8601(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ConfigError(f"Expected JSON object in {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_json(path, payload)


def normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_title(value: Any) -> str:
    return normalize_space(value).casefold()


def normalize_fragment(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.startswith("http://") or raw.startswith("https://"):
        fragment = raw.split("#", 1)[1] if "#" in raw else ""
    else:
        fragment = raw
    fragment = unquote(fragment).strip()
    if fragment.startswith("#"):
        fragment = fragment[1:]
    if fragment.startswith("/"):
        fragment = fragment[1:]
    return fragment


def fragment_from_url(url: str) -> str:
    parsed = urlparse(str(url or "").strip())
    if not TELEGRAM_WEB_HOST_RE.fullmatch(parsed.netloc or ""):
        raise ConfigError(f"Telegram chat url must point to web.telegram.org: {url}")
    if not parsed.fragment:
        raise ConfigError(f"Telegram chat url must include a fragment: {url}")
    return normalize_fragment(parsed.fragment)


def day_key_msk() -> str:
    return datetime.now(MSK_TZ).strftime("%Y-%m-%d")


def to_int(value: Any, *, default: int, minimum: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = int(default)
    return max(parsed, minimum)


def validate_message_text(text: str, *, block_external_links: bool) -> None:
    compact = normalize_space(text)
    if not compact:
        raise ConfigError("Message template rendered to empty text")
    if block_external_links and EXTERNAL_LINK_RE.search(compact):
        raise ConfigError(f"Rendered message contains an external link and is blocked by safety policy: {compact}")


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


USERNAME_IMPORT_RE = re.compile(r"@?[A-Za-z0-9_]{5,32}")


def parse_usernames_blob(text: str) -> tuple[list[str], list[str]]:
    valid: list[str] = []
    invalid: list[str] = []
    seen: set[str] = set()
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        token = ""
        if line.startswith("@"):
            match = re.match(r"^(@[A-Za-z0-9_]{5,32})\b", line)
            if match:
                token = match.group(1)
        else:
            match = re.fullmatch(r"@?[A-Za-z0-9_]{5,32}", line)
            if match:
                token = match.group(0)
        if not token:
            invalid.append(line)
            continue
        normalized = token if token.startswith("@") else f"@{token}"
        lowered = normalized.lower()
        if lowered in seen:
            continue
        valid.append(normalized)
        seen.add(lowered)
    return valid, invalid


def contact_id_from_username(username: str) -> str:
    handle = str(username or "").strip().lstrip("@").lower()
    handle = re.sub(r"[^a-z0-9_]+", "_", handle).strip("_")
    handle = handle or "contact"
    return f"import_{handle}"


def ensure_unique_contact_id(existing_ids: set[str], base_id: str) -> str:
    candidate = base_id
    index = 2
    while candidate in existing_ids:
        candidate = f"{base_id}_{index}"
        index += 1
    existing_ids.add(candidate)
    return candidate


def _normalize_actor(actor: dict[str, Any]) -> dict[str, Any]:
    actor_id = normalize_space(actor.get("actor_id"))
    client_id = normalize_space(actor.get("client_id"))
    if not actor_id:
        raise ConfigError("Each actor requires actor_id")
    if not client_id:
        raise ConfigError(f"Actor {actor_id} requires client_id")
    tab_id = to_int(actor.get("tab_id"), default=0, minimum=0)
    return {
        "actor_id": actor_id,
        "label": normalize_space(actor.get("label")) or actor_id,
        "client_id": client_id,
        "tab_id": tab_id or None,
        "url_pattern": normalize_space(actor.get("url_pattern")),
        "active": bool(actor.get("active", True)),
        "portable_profile_name": normalize_space(actor.get("portable_profile_name")),
        "portable_profile_dir": normalize_space(actor.get("portable_profile_dir")),
        "portable_account_username": normalize_space(actor.get("portable_account_username")),
        "portable_account_label": normalize_space(actor.get("portable_account_label")),
        "api_session_name": normalize_space(actor.get("api_session_name")),
        "api_session_file": normalize_space(actor.get("api_session_file")),
        "api_phone_number": normalize_space(actor.get("api_phone_number")),
    }


def _normalize_api_sidecar(payload: dict[str, Any]) -> dict[str, Any]:
    mode = normalize_space(payload.get("preferred_mode")) or "portable_only"
    if mode not in ALLOWED_API_SIDECAR_MODES:
        raise ConfigError(f"Unsupported api_sidecar preferred_mode: {mode}")
    python_bin = normalize_space(payload.get("python_bin")) or sys.executable or "python3"
    script_path = normalize_space(payload.get("script_path"))
    session_base_dir = normalize_space(payload.get("session_base_dir")) or str(DEFAULT_API_SIDECAR_SESSION_DIR)
    return {
        "enabled": bool(payload.get("enabled", False)),
        "preferred_mode": mode,
        "python_bin": python_bin,
        "python_path": normalize_space(payload.get("python_path")),
        "script_path": script_path,
        "api_id_env": normalize_space(payload.get("api_id_env")) or "TG_API_ID",
        "api_hash_env": normalize_space(payload.get("api_hash_env")) or "TG_API_HASH",
        "session_base_dir": session_base_dir,
        "connect_timeout_seconds": to_int(payload.get("connect_timeout_seconds"), default=15, minimum=1),
    }


def _normalize_chat(chat: dict[str, Any], actor_ids: set[str]) -> dict[str, Any]:
    chat_id = normalize_space(chat.get("chat_id"))
    title = normalize_space(chat.get("title"))
    url = normalize_space(chat.get("url"))
    if not chat_id:
        raise ConfigError("Each allowlist chat requires chat_id")
    if not title:
        raise ConfigError(f"Allowlist chat {chat_id} requires title")
    if not url:
        raise ConfigError(f"Allowlist chat {chat_id} requires url")
    expected_fragment = fragment_from_url(url)
    allowed_actor_ids = [normalize_space(item) for item in chat.get("allowed_actor_ids") or [] if normalize_space(item)]
    unknown_actor_ids = sorted(set(allowed_actor_ids) - actor_ids)
    if unknown_actor_ids:
        raise ConfigError(f"Allowlist chat {chat_id} references unknown actors: {', '.join(unknown_actor_ids)}")
    template_ids = [normalize_space(item) for item in chat.get("template_ids") or [] if normalize_space(item)]
    return {
        "chat_id": chat_id,
        "title": title,
        "title_norm": normalize_title(title),
        "url": url,
        "expected_fragment": expected_fragment,
        "allowed_actor_ids": allowed_actor_ids,
        "template_ids": template_ids,
    }


def _normalize_contact(contact: dict[str, Any], chat_ids: set[str]) -> dict[str, Any]:
    contact_id = normalize_space(contact.get("contact_id"))
    username = normalize_space(contact.get("username"))
    display_name = normalize_space(contact.get("display_name"))
    if not contact_id:
        raise ConfigError("Each allowlist contact requires contact_id")
    if not username:
        raise ConfigError(f"Allowlist contact {contact_id} requires username")
    if not re.fullmatch(r"@?[A-Za-z0-9_]{5,32}", username):
        raise ConfigError(f"Allowlist contact {contact_id} has invalid username: {username}")
    allowed_chat_ids = [normalize_space(item) for item in contact.get("allowed_chat_ids") or [] if normalize_space(item)]
    unknown_chat_ids = sorted(set(allowed_chat_ids) - chat_ids)
    if unknown_chat_ids:
        raise ConfigError(f"Allowlist contact {contact_id} references unknown chats: {', '.join(unknown_chat_ids)}")
    return {
        "contact_id": contact_id,
        "username": username if username.startswith("@") else f"@{username}",
        "display_name": display_name,
        "display_name_norm": normalize_title(display_name),
        "peer_id": normalize_space(contact.get("peer_id")),
        "search_query": normalize_space(contact.get("search_query")) or username.lstrip("@"),
        "search_result_index": to_int(contact.get("search_result_index"), default=0, minimum=0),
        "allowed_chat_ids": allowed_chat_ids,
        "allow_first_result": bool(contact.get("allow_first_result", False)),
    }


def _normalize_template(template: dict[str, Any], actor_ids: set[str], chat_ids: set[str]) -> dict[str, Any]:
    template_id = normalize_space(template.get("template_id"))
    text = str(template.get("text") or "").strip()
    if not template_id:
        raise ConfigError("Each message template requires template_id")
    if not text:
        raise ConfigError(f"Message template {template_id} requires text")
    allowed_actor_ids = [normalize_space(item) for item in template.get("actor_ids") or [] if normalize_space(item)]
    allowed_chat_ids = [normalize_space(item) for item in template.get("chat_ids") or [] if normalize_space(item)]
    unknown_actors = sorted(set(allowed_actor_ids) - actor_ids)
    if unknown_actors:
        raise ConfigError(f"Template {template_id} references unknown actor ids: {', '.join(unknown_actors)}")
    unknown_chats = sorted(set(allowed_chat_ids) - chat_ids)
    if unknown_chats:
        raise ConfigError(f"Template {template_id} references unknown chat ids: {', '.join(unknown_chats)}")
    return {
        "template_id": template_id,
        "text": text,
        "weight": to_int(template.get("weight"), default=1, minimum=1),
        "actor_ids": allowed_actor_ids,
        "chat_ids": allowed_chat_ids,
    }


def normalize_config(payload: dict[str, Any], config_path: Path) -> dict[str, Any]:
    actors_raw = payload.get("actors")
    if not isinstance(actors_raw, list) or not actors_raw:
        raise ConfigError("Config must contain a non-empty actors array")
    actors = [_normalize_actor(dict(item)) for item in actors_raw if isinstance(item, dict)]
    actor_ids = {row["actor_id"] for row in actors}
    if len(actor_ids) != len(actors):
        raise ConfigError("actor_id values must be unique")

    chats_raw = payload.get("allowlist_chats") or []
    if not isinstance(chats_raw, list):
        raise ConfigError("allowlist_chats must be an array when provided")
    chats = [_normalize_chat(dict(item), actor_ids) for item in chats_raw if isinstance(item, dict)]
    chat_ids = {row["chat_id"] for row in chats}
    if len(chat_ids) != len(chats):
        raise ConfigError("chat_id values must be unique")

    contacts_raw = payload.get("allowlist_contacts") or []
    if not isinstance(contacts_raw, list):
        raise ConfigError("allowlist_contacts must be an array when provided")
    contacts = [_normalize_contact(dict(item), chat_ids) for item in contacts_raw if isinstance(item, dict)]
    contact_ids = {row["contact_id"] for row in contacts}
    if len(contact_ids) != len(contacts):
        raise ConfigError("contact_id values must be unique")

    templates_raw = payload.get("message_templates") or []
    if not isinstance(templates_raw, list):
        raise ConfigError("message_templates must be an array when provided")
    templates = [_normalize_template(dict(item), actor_ids, chat_ids) for item in templates_raw if isinstance(item, dict)]
    template_ids = {row["template_id"] for row in templates}
    if len(template_ids) != len(templates):
        raise ConfigError("template_id values must be unique")

    missing_template_refs: list[str] = []
    for chat in chats:
        for template_id in chat["template_ids"]:
            if template_id not in template_ids:
                missing_template_refs.append(f"{chat['chat_id']} -> {template_id}")
    if missing_template_refs:
        raise ConfigError(f"Unknown template references in allowlist chats: {', '.join(missing_template_refs)}")

    activity = dict(payload.get("activity") or {})
    enabled_actions = [normalize_space(item) for item in activity.get("enabled_actions") or DEFAULT_ENABLED_ACTIONS if normalize_space(item)]
    invalid_actions = sorted(set(enabled_actions) - ALLOWED_ACTIONS)
    if invalid_actions:
        raise ConfigError(f"Unsupported activity actions: {', '.join(invalid_actions)}")
    if not enabled_actions:
        raise ConfigError("At least one activity action must be enabled")
    action_weights = dict(DEFAULT_ACTION_WEIGHTS)
    raw_weights = activity.get("action_weights") or {}
    if isinstance(raw_weights, dict):
        for key, value in raw_weights.items():
            action_name = normalize_space(key)
            if action_name not in ALLOWED_ACTIONS:
                continue
            action_weights[action_name] = to_int(value, default=1, minimum=1)

    safety = dict(payload.get("safety") or {})
    api_sidecar = _normalize_api_sidecar(dict(payload.get("api_sidecar") or {}))
    normalized = {
        "config_path": str(config_path),
        "version": int(payload.get("version") or 1),
        "tool_name": normalize_space(payload.get("tool_name")) or "Telegram Sandbox Activity Runner",
        "desktop_automation": {
            "site_control_kit_root": normalize_space((payload.get("desktop_automation") or {}).get("site_control_kit_root"))
            or str(DEFAULT_SITE_CONTROL_KIT_ROOT),
        },
        "site_control": {
            "server_url": normalize_space((payload.get("site_control") or {}).get("server_url")) or "http://127.0.0.1:8765",
            "token": normalize_space((payload.get("site_control") or {}).get("token")),
            "token_env": normalize_space((payload.get("site_control") or {}).get("token_env")) or "SITECTL_TOKEN",
        },
        "api_sidecar": api_sidecar,
        "actors": actors,
        "allowlist_chats": chats,
        "allowlist_contacts": contacts,
        "message_templates": templates,
        "activity": {
            "enabled_actions": enabled_actions,
            "action_weights": action_weights,
            "iterations_per_run_default": to_int(activity.get("iterations_per_run_default"), default=1, minimum=1),
            "min_delay_seconds": to_int(activity.get("min_delay_seconds"), default=45, minimum=0),
            "max_delay_seconds": to_int(activity.get("max_delay_seconds"), default=180, minimum=0),
            "actor_cooldown_seconds": to_int(activity.get("actor_cooldown_seconds"), default=300, minimum=0),
            "chat_cooldown_seconds": to_int(activity.get("chat_cooldown_seconds"), default=180, minimum=0),
        },
        "safety": {
            "dry_run_default": bool(safety.get("dry_run_default", True)),
            "require_fragment_match": bool(safety.get("require_fragment_match", True)),
            "require_title_match": bool(safety.get("require_title_match", True)),
            "block_external_links": bool(safety.get("block_external_links", True)),
            "max_messages_per_actor_per_day": to_int(safety.get("max_messages_per_actor_per_day"), default=12, minimum=0),
            "max_messages_per_chat_per_day": to_int(safety.get("max_messages_per_chat_per_day"), default=20, minimum=0),
            "max_actions_per_actor_per_day": to_int(safety.get("max_actions_per_actor_per_day"), default=24, minimum=0),
            "history_limit": to_int(safety.get("history_limit"), default=DEFAULT_HISTORY_LIMIT, minimum=100),
        },
    }
    if normalized["activity"]["max_delay_seconds"] < normalized["activity"]["min_delay_seconds"]:
        normalized["activity"]["max_delay_seconds"] = normalized["activity"]["min_delay_seconds"]
    return normalized


def load_config(config_path: Path) -> dict[str, Any]:
    payload = load_json(config_path)
    return normalize_config(payload, config_path.resolve())


def build_default_state(config_path: Path) -> dict[str, Any]:
    timestamp = now_utc()
    return {
        "version": STATE_VERSION,
        "config_path": str(config_path),
        "created_at": timestamp,
        "updated_at": timestamp,
        "actors": {},
        "chats": {},
        "history": [],
    }


def load_or_init_state(state_path: Path, config_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return build_default_state(config_path)
    payload = load_json(state_path)
    payload.setdefault("version", STATE_VERSION)
    payload.setdefault("config_path", str(config_path))
    payload.setdefault("created_at", now_utc())
    payload.setdefault("updated_at", now_utc())
    payload.setdefault("actors", {})
    payload.setdefault("chats", {})
    payload.setdefault("history", [])
    if not isinstance(payload.get("actors"), dict):
        raise ConfigError(f"Invalid actors section in state file: {state_path}")
    if not isinstance(payload.get("chats"), dict):
        raise ConfigError(f"Invalid chats section in state file: {state_path}")
    if not isinstance(payload.get("history"), list):
        raise ConfigError(f"Invalid history section in state file: {state_path}")
    return payload


def _ensure_actor_state(state: dict[str, Any], actor_id: str) -> dict[str, Any]:
    actors = state.setdefault("actors", {})
    if actor_id not in actors or not isinstance(actors.get(actor_id), dict):
        actors[actor_id] = {
            "last_action_at": "",
            "last_chat_id": "",
            "last_template_id": "",
            "daily": {},
        }
    return actors[actor_id]


def _ensure_chat_state(state: dict[str, Any], chat_id: str) -> dict[str, Any]:
    chats = state.setdefault("chats", {})
    if chat_id not in chats or not isinstance(chats.get(chat_id), dict):
        chats[chat_id] = {
            "last_action_at": "",
            "last_actor_id": "",
            "last_template_id": "",
            "daily": {},
        }
    return chats[chat_id]


def _ensure_daily_bucket(record: dict[str, Any], day_key: str) -> dict[str, int]:
    daily = record.setdefault("daily", {})
    bucket = daily.get(day_key)
    if not isinstance(bucket, dict):
        bucket = {"actions": 0, "messages": 0}
        daily[day_key] = bucket
    bucket["actions"] = to_int(bucket.get("actions"), default=0, minimum=0)
    bucket["messages"] = to_int(bucket.get("messages"), default=0, minimum=0)
    return bucket


def _last_action_timestamp(record: dict[str, Any]) -> datetime | None:
    return parse_iso8601(str(record.get("last_action_at") or ""))


def _cooldown_passed(record: dict[str, Any], cooldown_seconds: int) -> bool:
    if cooldown_seconds <= 0:
        return True
    last_action = _last_action_timestamp(record)
    if last_action is None:
        return True
    return (datetime.now(timezone.utc) - last_action.astimezone(timezone.utc)).total_seconds() >= cooldown_seconds


def _actor_daily_counts(state: dict[str, Any], actor_id: str, day_key: str) -> dict[str, int]:
    actor_state = _ensure_actor_state(state, actor_id)
    return _ensure_daily_bucket(actor_state, day_key)


def _chat_daily_counts(state: dict[str, Any], chat_id: str, day_key: str) -> dict[str, int]:
    chat_state = _ensure_chat_state(state, chat_id)
    return _ensure_daily_bucket(chat_state, day_key)


def weighted_choice(items: list[dict[str, Any]], *, weight_key: str, rng: random.Random) -> dict[str, Any]:
    if not items:
        raise ConfigError("weighted_choice received empty items")
    total = sum(max(int(item.get(weight_key, 1) or 1), 1) for item in items)
    pick = rng.uniform(0, float(total))
    upto = 0.0
    for item in items:
        upto += float(max(int(item.get(weight_key, 1) or 1), 1))
        if pick <= upto:
            return item
    return items[-1]


def _eligible_actors(config: dict[str, Any], state: dict[str, Any], *, actor_filter: str | None, day_key: str) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    limit = int(config["safety"]["max_actions_per_actor_per_day"])
    cooldown = int(config["activity"]["actor_cooldown_seconds"])
    for actor in config["actors"]:
        if not bool(actor.get("active", True)):
            continue
        if actor_filter and actor["actor_id"] != actor_filter:
            continue
        actor_state = _ensure_actor_state(state, actor["actor_id"])
        day_counts = _ensure_daily_bucket(actor_state, day_key)
        if limit and day_counts["actions"] >= limit:
            continue
        if not _cooldown_passed(actor_state, cooldown):
            continue
        eligible.append(actor)
    eligible.sort(key=lambda item: (_last_action_timestamp(_ensure_actor_state(state, item["actor_id"])) or datetime.fromtimestamp(0, timezone.utc), item["actor_id"]))
    return eligible


def _eligible_chats(config: dict[str, Any], state: dict[str, Any], *, actor: dict[str, Any], day_key: str) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    message_limit = int(config["safety"]["max_messages_per_chat_per_day"])
    cooldown = int(config["activity"]["chat_cooldown_seconds"])
    for chat in config["allowlist_chats"]:
        allowed_actor_ids = chat["allowed_actor_ids"]
        if allowed_actor_ids and actor["actor_id"] not in allowed_actor_ids:
            continue
        chat_state = _ensure_chat_state(state, chat["chat_id"])
        if not _cooldown_passed(chat_state, cooldown):
            continue
        if message_limit and _ensure_daily_bucket(chat_state, day_key)["messages"] >= message_limit:
            continue
        eligible.append(chat)
    eligible.sort(key=lambda item: (_last_action_timestamp(_ensure_chat_state(state, item["chat_id"])) or datetime.fromtimestamp(0, timezone.utc), item["chat_id"]))
    return eligible


def render_message(template: dict[str, Any], actor: dict[str, Any], chat: dict[str, Any], *, block_external_links: bool) -> str:
    values = {
        "actor_id": actor["actor_id"],
        "actor_label": actor["label"],
        "chat_id": chat["chat_id"],
        "chat_title": chat["title"],
        "chat_url": chat["url"],
        **now_msk_parts(),
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "time_utc": datetime.now(timezone.utc).strftime("%H:%M:%S"),
    }
    try:
        text = str(template["text"]).format(**values)
    except KeyError as exc:
        raise ConfigError(f"Unknown template placeholder {exc} in template {template['template_id']}") from exc
    validate_message_text(text, block_external_links=block_external_links)
    return text.strip()


def _available_templates(config: dict[str, Any], *, actor: dict[str, Any], chat: dict[str, Any]) -> list[dict[str, Any]]:
    available: list[dict[str, Any]] = []
    allow_template_ids = set(chat["template_ids"])
    for template in config["message_templates"]:
        if allow_template_ids and template["template_id"] not in allow_template_ids:
            continue
        if template["actor_ids"] and actor["actor_id"] not in template["actor_ids"]:
            continue
        if template["chat_ids"] and chat["chat_id"] not in template["chat_ids"]:
            continue
        available.append(template)
    return available


def _available_actions(config: dict[str, Any], state: dict[str, Any], *, actor: dict[str, Any], chat: dict[str, Any], day_key: str) -> list[dict[str, Any]]:
    actor_counts = _actor_daily_counts(state, actor["actor_id"], day_key)
    chat_counts = _chat_daily_counts(state, chat["chat_id"], day_key)
    message_limit_actor = int(config["safety"]["max_messages_per_actor_per_day"])
    message_limit_chat = int(config["safety"]["max_messages_per_chat_per_day"])
    available: list[dict[str, Any]] = []
    for action in config["activity"]["enabled_actions"]:
        if action == "send_message":
            if message_limit_actor and actor_counts["messages"] >= message_limit_actor:
                continue
            if message_limit_chat and chat_counts["messages"] >= message_limit_chat:
                continue
            if not _available_templates(config, actor=actor, chat=chat):
                continue
        available.append({"action": action, "weight": int(config["activity"]["action_weights"].get(action, 1) or 1)})
    return available


def _choose_template(config: dict[str, Any], state: dict[str, Any], *, actor: dict[str, Any], chat: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    templates = _available_templates(config, actor=actor, chat=chat)
    if not templates:
        raise ConfigError(f"No templates available for actor {actor['actor_id']} and chat {chat['chat_id']}")
    chat_state = _ensure_chat_state(state, chat["chat_id"])
    last_template_id = normalize_space(chat_state.get("last_template_id"))
    if len(templates) > 1:
        filtered = [item for item in templates if item["template_id"] != last_template_id]
        if filtered:
            templates = filtered
    return weighted_choice(templates, weight_key="weight", rng=rng)


def find_actor(config: dict[str, Any], actor_id: str) -> dict[str, Any]:
    normalized = normalize_space(actor_id)
    for actor in config["actors"]:
        if actor["actor_id"] == normalized:
            return actor
    raise ConfigError(f"Unknown actor_id: {actor_id}")


def find_chat(config: dict[str, Any], chat_id: str) -> dict[str, Any]:
    normalized = normalize_space(chat_id)
    for chat in config["allowlist_chats"]:
        if chat["chat_id"] == normalized:
            return chat
    raise ConfigError(f"Unknown chat_id: {chat_id}")


def find_contact(config: dict[str, Any], contact_id: str) -> dict[str, Any]:
    normalized = normalize_space(contact_id)
    for contact in config.get("allowlist_contacts") or []:
        if contact["contact_id"] == normalized:
            return contact
    raise ConfigError(f"Unknown contact_id: {contact_id}")


def site_control_kit_root(config: dict[str, Any]) -> Path:
    return Path(config["desktop_automation"]["site_control_kit_root"]).expanduser().resolve()


def tool_root_dir() -> Path:
    return Path(__file__).resolve().parent


def api_sidecar_script_path(config: dict[str, Any]) -> Path:
    configured = normalize_space((config.get("api_sidecar") or {}).get("script_path"))
    if configured:
        return Path(configured).expanduser().resolve()
    return tool_root_dir() / "telegram_api_sidecar.py"


def api_session_file_path(config: dict[str, Any], actor: dict[str, Any]) -> Path:
    configured = normalize_space(actor.get("api_session_file"))
    if configured:
        return Path(configured).expanduser().resolve()
    session_name = normalize_space(actor.get("api_session_name")) or actor["actor_id"]
    session_base_dir = Path(config["api_sidecar"]["session_base_dir"]).expanduser().resolve()
    return session_base_dir / f"{session_name}.session"


def resolve_actor_tdata_dir(actor: dict[str, Any], explicit_path: str = "") -> Path:
    explicit = normalize_space(explicit_path)
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if root.name == "tdata":
            return root
        direct_tdata = root / "tdata"
        portable_tdata = root / "TelegramForcePortable" / "tdata"
        if direct_tdata.exists():
            return direct_tdata
        if portable_tdata.exists():
            return portable_tdata
        return root

    portable_profile_dir = normalize_space(actor.get("portable_profile_dir"))
    if not portable_profile_dir:
        raise ConfigError(
            f"Actor {actor['actor_id']} has no portable_profile_dir; pass --tdata-dir explicitly"
        )
    root = Path(portable_profile_dir).expanduser().resolve()
    candidates = []
    if root.name == "tdata":
        candidates.append(root)
    candidates.extend([root / "TelegramForcePortable" / "tdata", root / "tdata"])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ConfigError(
        f"Could not find Telegram Desktop tdata for actor {actor['actor_id']} under {root}; pass --tdata-dir explicitly"
    )


def api_sidecar_base_command(config: dict[str, Any], actor: dict[str, Any], action: str) -> list[str]:
    python_bin = normalize_space(config["api_sidecar"]["python_bin"]) or sys.executable or "python3"
    session_file = api_session_file_path(config, actor)
    return [
        python_bin,
        str(api_sidecar_script_path(config)),
        "--api-id-env",
        str(config["api_sidecar"]["api_id_env"]),
        "--api-hash-env",
        str(config["api_sidecar"]["api_hash_env"]),
        "--session-file",
        str(session_file),
        "--connect-timeout",
        str(int(config["api_sidecar"]["connect_timeout_seconds"])),
        action,
    ]


def run_api_sidecar_json(config: dict[str, Any], actor: dict[str, Any], action: str, *action_args: str) -> dict[str, Any]:
    command = [*api_sidecar_base_command(config, actor, action), *action_args]
    env = os.environ.copy()
    python_path = normalize_space(config["api_sidecar"].get("python_path"))
    if python_path:
        env["PYTHONPATH"] = python_path if not env.get("PYTHONPATH") else f"{python_path}{os.pathsep}{env['PYTHONPATH']}"
    proc = subprocess.run(
        command,
        cwd=str(tool_root_dir()),
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    payload: dict[str, Any] = {
        "command": command,
        "returncode": int(proc.returncode),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_json": {},
    }
    try:
        payload["stdout_json"] = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        payload["stdout_json"] = {}
    return payload


def run_self_json(command_args: list[str]) -> dict[str, Any]:
    command = [sys.executable or "python3", str(Path(__file__).resolve()), *command_args]
    proc = subprocess.run(
        command,
        cwd=str(tool_root_dir()),
        check=False,
        capture_output=True,
        text=True,
    )
    payload: dict[str, Any] = {
        "command": command,
        "returncode": int(proc.returncode),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_json": {},
    }
    try:
        payload["stdout_json"] = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        payload["stdout_json"] = {}
    return payload


def build_contact_id_batch(config: dict[str, Any], *, explicit_contact_ids: list[str], limit: int | None) -> list[str]:
    if explicit_contact_ids:
        ordered: list[str] = []
        seen: set[str] = set()
        for item in explicit_contact_ids:
            normalized = normalize_space(item)
            if not normalized or normalized in seen:
                continue
            find_contact(config, normalized)
            ordered.append(normalized)
            seen.add(normalized)
        if limit is not None and limit >= 0:
            return ordered[:limit]
        return ordered

    ordered = [contact["contact_id"] for contact in config.get("allowlist_contacts") or []]
    if limit is not None and limit >= 0:
        return ordered[:limit]
    return ordered


def read_contact_ids_file(path_value: str) -> list[str]:
    path = Path(path_value).expanduser()
    values: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = normalize_space(raw_line)
        if not line or line.startswith("#"):
            continue
        values.append(line)
    return values


def compact_process_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "command": payload.get("command"),
        "returncode": int(payload.get("returncode", 1) or 0),
        "stderr": payload.get("stderr") or "",
        "stdout_json": payload.get("stdout_json") if isinstance(payload.get("stdout_json"), dict) else {},
    }


def random_pause_seconds(minimum: float, maximum: float, *, rng: random.Random) -> float:
    minimum_value = max(float(minimum), 0.0)
    maximum_value = max(float(maximum), minimum_value)
    if maximum_value <= minimum_value:
        return round(minimum_value, 3)
    return round(rng.uniform(minimum_value, maximum_value), 3)


def portable_actor_args(actor: dict[str, Any]) -> list[str]:
    profile_dir = normalize_space(actor.get("portable_profile_dir"))
    if profile_dir:
        return ["--profile-dir", profile_dir]
    profile_name = normalize_space(actor.get("portable_profile_name"))
    if profile_name:
        return ["--profile-name", profile_name]
    raise ConfigError(
        f"Actor {actor['actor_id']} does not have portable_profile_dir or portable_profile_name configured for desktop contact automation"
    )


def portable_command(config: dict[str, Any], actor: dict[str, Any], action: str, *action_args: str) -> list[str]:
    root = site_control_kit_root(config)
    return ["python3", str(root / "scripts" / "telegram_portable.py"), action, *portable_actor_args(actor), *action_args]


def run_portable_json(config: dict[str, Any], command: list[str]) -> dict[str, Any]:
    root = site_control_kit_root(config)
    proc = subprocess.run(
        command,
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )
    payload: dict[str, Any] = {
        "command": command,
        "returncode": int(proc.returncode),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_json": {},
    }
    try:
        payload["stdout_json"] = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        payload["stdout_json"] = {}
    return payload


def portable_accessibility_dump(
    config: dict[str, Any],
    actor: dict[str, Any],
    *,
    query: str = "",
    role: str = "",
    visible_only: bool = True,
    max_results: int = 25,
    state_filters: tuple[str, ...] | list[str] = ("showing",),
) -> dict[str, Any]:
    command = portable_command(config, actor, "accessibility-dump")
    if query:
        command.extend(["--query", query])
    if role:
        command.extend(["--role", role])
    if visible_only:
        command.append("--visible-only")
    for state_name in state_filters or []:
        if normalize_space(state_name):
            command.extend(["--state", normalize_space(state_name)])
    command.extend(["--max-results", str(max(int(max_results), 1))])
    return run_portable_json(config, command)


def portable_find_accessible_match(
    config: dict[str, Any],
    actor: dict[str, Any],
    *,
    terms: tuple[str, ...] | list[str],
    role: str = "",
    visible_only: bool = True,
    state_filters: tuple[str, ...] | list[str] = ("showing",),
) -> dict[str, Any] | None:
    for term in terms:
        result = portable_accessibility_dump(
            config,
            actor,
            query=str(term or ""),
            role=role,
            visible_only=visible_only,
            state_filters=state_filters,
        )
        listing = result.get("stdout_json") if isinstance(result.get("stdout_json"), dict) else {}
        matches = listing.get("matches") if isinstance(listing.get("matches"), list) else []
        if int(result.get("returncode", 1) or 0) == 0 and matches:
            return {
                "term": str(term or ""),
                "result": result,
                "listing": listing,
                "match": matches[0] if isinstance(matches[0], dict) else {},
            }
    return None


def derive_accessible_click_ratio(
    match: dict[str, Any],
    window: dict[str, Any],
    *,
    x_anchor: float = 0.18,
    y_anchor: float = 0.45,
) -> dict[str, float] | None:
    extents = match.get("relative_extents") if isinstance(match.get("relative_extents"), dict) else {}
    try:
        rel_x = int(extents.get("x", 0) or 0)
        rel_y = int(extents.get("y", 0) or 0)
        width = int(extents.get("width", 0) or 0)
        height = int(extents.get("height", 0) or 0)
        window_width = int(window.get("width", 0) or 0)
        window_height = int(window.get("height", 0) or 0)
    except (TypeError, ValueError):
        return None
    if width <= 0 or height <= 0 or window_width <= 1 or window_height <= 1:
        return None
    x_inset = min(max(int(round(width * float(x_anchor))), 18), max(width - 4, 1))
    y_inset = min(max(int(round(height * float(y_anchor))), 10), max(height - 4, 1))
    click_x = rel_x + x_inset
    click_y = rel_y + y_inset
    return {
        "x_ratio": round(min(max(float(click_x) / float(window_width), 0.0), 1.0), 4),
        "y_ratio": round(min(max(float(click_y) / float(window_height), 0.0), 1.0), 4),
    }


def resolve_accessible_node_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    stdout_json = payload.get("stdout_json") if isinstance(payload.get("stdout_json"), dict) else {}
    node = stdout_json.get("node")
    if isinstance(node, dict):
        return node
    click_payload = stdout_json.get("click") if isinstance(stdout_json.get("click"), dict) else {}
    click_node = click_payload.get("node")
    if isinstance(click_node, dict):
        return click_node
    match = payload.get("match")
    if isinstance(match, dict):
        return match
    return None


def derive_dialog_submit_ratio(
    payload: dict[str, Any] | None,
    window: dict[str, Any],
    *,
    x_anchor: float = 0.69,
    y_anchor: float = 0.96,
) -> dict[str, float] | None:
    node = resolve_accessible_node_payload(payload)
    if not isinstance(node, dict):
        return None
    dialog_extents: dict[str, Any] | None = None
    for ancestor in reversed(node.get("ancestors") or []):
        if not isinstance(ancestor, dict):
            continue
        if str(ancestor.get("role") or "") != "dialog":
            continue
        extents = ancestor.get("resolved_extents") if isinstance(ancestor.get("resolved_extents"), dict) else {}
        if int(extents.get("width", 0) or 0) > 0 and int(extents.get("height", 0) or 0) > 0:
            dialog_extents = extents
            break
    if dialog_extents is None:
        return None
    try:
        dialog_x = int(dialog_extents.get("x", 0) or 0)
        dialog_y = int(dialog_extents.get("y", 0) or 0)
        dialog_width = int(dialog_extents.get("width", 0) or 0)
        dialog_height = int(dialog_extents.get("height", 0) or 0)
        window_x = int(window.get("x", 0) or 0)
        window_y = int(window.get("y", 0) or 0)
        window_width = int(window.get("width", 0) or 0)
        window_height = int(window.get("height", 0) or 0)
    except (TypeError, ValueError):
        return None
    if dialog_width <= 0 or dialog_height <= 0 or window_width <= 1 or window_height <= 1:
        return None
    rel_x = dialog_x - window_x
    rel_y = dialog_y - window_y
    max_x = rel_x + dialog_width - 4
    max_y = rel_y + dialog_height - 4
    if max_x <= rel_x or max_y <= rel_y:
        return None
    click_x = min(max(int(round(rel_x + dialog_width * float(x_anchor))), rel_x + 4), max_x)
    click_y = min(max(int(round(rel_y + dialog_height * float(y_anchor))), rel_y + 4), max_y)
    return {
        "x_ratio": round(min(max(float(click_x) / float(window_width), 0.0), 1.0), 4),
        "y_ratio": round(min(max(float(click_y) / float(window_height), 0.0), 1.0), 4),
    }


def summarize_contact_verify_state(
    *,
    username_visible: bool,
    add_button_visible: bool,
    edit_button_visible: bool,
    delete_button_visible: bool,
) -> str:
    if edit_button_visible or delete_button_visible:
        return "ui_verify_contact_present"
    if username_visible and add_button_visible:
        return "ui_verify_add_button_visible"
    if username_visible:
        return "ui_verify_profile_visible_without_add_button"
    return "ui_verify_profile_not_detected"


def resolve_search_result_index(args: argparse.Namespace, contact: dict[str, Any]) -> int:
    override = getattr(args, "search_result_index", None)
    if override is not None:
        return max(int(override), 0)
    try:
        configured = int(contact.get("search_result_index", 0) or 0)
    except (TypeError, ValueError):
        configured = 0
    return max(configured, 0)


def preferred_accessible_text_indices() -> tuple[int, ...]:
    return (0, 1)


def split_display_name_parts(display_name: str) -> tuple[str, str]:
    normalized = normalize_space(display_name)
    if not normalized:
        return "", ""
    parts = re.findall(r"[^\W_]+(?:[-'][^\W_]+)*", normalized, flags=re.UNICODE)
    if not parts:
        return normalized, ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def resolve_contact_name_parts(args: argparse.Namespace, contact: dict[str, Any]) -> tuple[str, str]:
    explicit_first = normalize_space(getattr(args, "first_name_text", ""))
    explicit_last = normalize_space(getattr(args, "last_name_text", ""))
    derived_first = ""
    derived_last = ""
    display_name = normalize_space(contact.get("display_name"))
    if display_name:
        derived_first, derived_last = split_display_name_parts(display_name)
    else:
        username_base = normalize_space(contact.get("username")).lstrip("@")
        if username_base:
            derived_first, derived_last = split_display_name_parts(username_base)
    return explicit_first or derived_first, explicit_last or derived_last


def ensure_portable_actor_ready(config: dict[str, Any], actor: dict[str, Any], *, launch_if_needed: bool) -> dict[str, Any]:
    status_result = run_portable_json(config, portable_command(config, actor, "status"))
    status_payload = status_result.get("stdout_json") if isinstance(status_result.get("stdout_json"), dict) else {}
    launch_result: dict[str, Any] | None = None
    if int(status_result.get("returncode", 1) or 0) == 0 and not bool(status_payload.get("running")) and launch_if_needed:
        launch_result = run_portable_json(config, portable_command(config, actor, "launch"))
        status_result = run_portable_json(config, portable_command(config, actor, "status"))
        status_payload = status_result.get("stdout_json") if isinstance(status_result.get("stdout_json"), dict) else {}
    return {
        "status_result": status_result,
        "launch_result": launch_result,
        "running": bool(status_payload.get("running")),
        "pids": status_payload.get("pids") if isinstance(status_payload.get("pids"), list) else [],
        "windows": status_payload.get("windows") if isinstance(status_payload.get("windows"), list) else [],
    }


def _random_delay(config: dict[str, Any], *, index: int, rng: random.Random) -> int:
    if index == 0:
        return 0
    minimum = int(config["activity"]["min_delay_seconds"])
    maximum = int(config["activity"]["max_delay_seconds"])
    if maximum <= minimum:
        return minimum
    return int(rng.randint(minimum, maximum))


def record_step_result(
    state: dict[str, Any],
    step: dict[str, Any],
    *,
    status: str,
    error: str = "",
    preserve_history_limit: int,
) -> None:
    timestamp = now_utc()
    step["executed_at"] = timestamp
    step["status"] = status
    if error:
        step["error"] = error

    actor_state = _ensure_actor_state(state, step["actor_id"])
    chat_state = _ensure_chat_state(state, step["chat_id"])
    actor_bucket = _ensure_daily_bucket(actor_state, day_key_msk())
    chat_bucket = _ensure_daily_bucket(chat_state, day_key_msk())

    if status == "executed":
        actor_state["last_action_at"] = timestamp
        actor_state["last_chat_id"] = step["chat_id"]
        actor_state["last_template_id"] = step.get("template_id") or ""
        chat_state["last_action_at"] = timestamp
        chat_state["last_actor_id"] = step["actor_id"]
        chat_state["last_template_id"] = step.get("template_id") or ""
        actor_bucket["actions"] += 1
        chat_bucket["actions"] += 1
        if step["action"] == "send_message":
            actor_bucket["messages"] += 1
            chat_bucket["messages"] += 1

    history = state.setdefault("history", [])
    history.append(
        {
            "run_id": step["run_id"],
            "step_id": step["step_id"],
            "actor_id": step["actor_id"],
            "chat_id": step["chat_id"],
            "action": step["action"],
            "template_id": step.get("template_id") or "",
            "status": status,
            "executed_at": timestamp,
            "error": error,
        }
    )
    if len(history) > preserve_history_limit:
        del history[: len(history) - preserve_history_limit]
    state["updated_at"] = timestamp


def build_plan(
    config: dict[str, Any],
    state: dict[str, Any],
    *,
    iterations: int,
    actor_filter: str | None,
    seed: int | None,
) -> dict[str, Any]:
    rng = random.Random(seed)
    plan_state = copy.deepcopy(state)
    plan_steps: list[dict[str, Any]] = []
    run_id = now_utc().replace(":", "").replace("-", "").replace("Z", "") + "-" + uuid.uuid4().hex[:8]
    current_day = day_key_msk()
    for index in range(max(iterations, 0)):
        actors = _eligible_actors(config, plan_state, actor_filter=actor_filter, day_key=current_day)
        if not actors:
            break
        actor = actors[0]
        chats = _eligible_chats(config, plan_state, actor=actor, day_key=current_day)
        if not chats:
            break
        chat = chats[0]
        actions = _available_actions(config, plan_state, actor=actor, chat=chat, day_key=current_day)
        if not actions:
            break
        action_choice = weighted_choice(actions, weight_key="weight", rng=rng)
        template_id = ""
        message_text = ""
        if action_choice["action"] == "send_message":
            template = _choose_template(config, plan_state, actor=actor, chat=chat, rng=rng)
            template_id = template["template_id"]
            message_text = render_message(template, actor, chat, block_external_links=bool(config["safety"]["block_external_links"]))
        delay_seconds = _random_delay(config, index=index, rng=rng)
        scroll_delta_y = 0
        if action_choice["action"] == "idle_scroll":
            scroll_delta_y = rng.choice((220, 280, 340, 420))
        step = {
            "run_id": run_id,
            "step_id": f"{run_id}-{index + 1:03d}",
            "step_index": index + 1,
            "actor_id": actor["actor_id"],
            "actor_label": actor["label"],
            "client_id": actor["client_id"],
            "tab_id": actor["tab_id"],
            "url_pattern": actor["url_pattern"],
            "action": action_choice["action"],
            "chat_id": chat["chat_id"],
            "chat_title": chat["title"],
            "chat_url": chat["url"],
            "expected_fragment": chat["expected_fragment"],
            "template_id": template_id,
            "message_text": message_text,
            "delay_seconds": delay_seconds,
            "scroll_delta_y": scroll_delta_y,
            "status": "planned",
        }
        plan_steps.append(step)
        record_step_result(
            plan_state,
            copy.deepcopy(step),
            status="executed",
            preserve_history_limit=int(config["safety"]["history_limit"]),
        )

    return {
        "run_id": run_id,
        "created_at": now_utc(),
        "config_path": config["config_path"],
        "iterations_requested": iterations,
        "iterations_planned": len(plan_steps),
        "dry_run_default": bool(config["safety"]["dry_run_default"]),
        "steps": plan_steps,
    }


def summarize_state(config: dict[str, Any], state: dict[str, Any], *, state_path: Path) -> dict[str, Any]:
    current_day = day_key_msk()
    actor_rows: list[dict[str, Any]] = []
    for actor in config["actors"]:
        actor_state = _ensure_actor_state(state, actor["actor_id"])
        day_counts = _ensure_daily_bucket(actor_state, current_day)
        actor_rows.append(
            {
                "actor_id": actor["actor_id"],
                "label": actor["label"],
                "client_id": actor["client_id"],
                "last_action_at": actor_state.get("last_action_at") or "",
                "last_chat_id": actor_state.get("last_chat_id") or "",
                "actions_today": day_counts["actions"],
                "messages_today": day_counts["messages"],
            }
        )

    chat_rows: list[dict[str, Any]] = []
    for chat in config["allowlist_chats"]:
        chat_state = _ensure_chat_state(state, chat["chat_id"])
        day_counts = _ensure_daily_bucket(chat_state, current_day)
        chat_rows.append(
            {
                "chat_id": chat["chat_id"],
                "title": chat["title"],
                "last_action_at": chat_state.get("last_action_at") or "",
                "last_actor_id": chat_state.get("last_actor_id") or "",
                "actions_today": day_counts["actions"],
                "messages_today": day_counts["messages"],
            }
        )

    return {
        "tool_name": config["tool_name"],
        "config_path": config["config_path"],
        "state_path": str(state_path),
        "today_msk": current_day,
        "history_entries": len(state.get("history") or []),
        "actors": actor_rows,
        "allowlist_chats": chat_rows,
    }


class SiteControlClient:
    def __init__(self, *, server_url: str, token: str):
        self.server_url = str(server_url or "").rstrip("/")
        self.token = str(token or "").strip()
        self.session = requests.Session()

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Access-Token": self.token,
        }

    def _request_json(self, method: str, path: str, *, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
        response = self.session.request(
            method=method.upper(),
            url=f"{self.server_url}{path}",
            headers=self._headers(),
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected site-control response for {method} {path}")
        return data

    def list_clients(self) -> list[dict[str, Any]]:
        response = self._request_json("GET", "/api/clients", timeout=20)
        clients = response.get("clients")
        return [dict(item) for item in clients] if isinstance(clients, list) else []

    def build_target(self, actor: dict[str, Any]) -> dict[str, Any]:
        target = {
            "client_id": actor["client_id"],
            "active": bool(actor.get("active", True)),
        }
        if actor.get("tab_id"):
            target["tab_id"] = int(actor["tab_id"])
        if actor.get("url_pattern"):
            target["url_pattern"] = actor["url_pattern"]
        return target

    def ensure_actor_online(self, actor: dict[str, Any]) -> None:
        clients = self.list_clients()
        for client in clients:
            if normalize_space(client.get("client_id")) == actor["client_id"]:
                return
        raise RuntimeError(f"SiteControlKit client is not connected: {actor['client_id']}")

    def send_command(
        self,
        *,
        actor: dict[str, Any],
        command: dict[str, Any],
        timeout_sec: int,
        raise_on_fail: bool = True,
    ) -> dict[str, Any]:
        created = self._request_json(
            "POST",
            "/api/commands",
            payload={
                "issued_by": "telegram-sandbox-activity-runner",
                "timeout_ms": max(timeout_sec * 1000, 1000),
                "target": self.build_target(actor),
                "command": command,
            },
            timeout=max(timeout_sec, 20),
        )
        command_id = normalize_space(created.get("command_id"))
        if not command_id:
            raise RuntimeError(f"SiteControlKit command creation failed: {created}")
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            state = self._request_json("GET", f"/api/commands/{command_id}", timeout=max(timeout_sec, 20))
            command_state = state.get("command") or {}
            status = normalize_space(command_state.get("status"))
            if status in {"completed", "failed", "cancelled", "timed_out"}:
                deliveries = command_state.get("deliveries") or {}
                result_payload: dict[str, Any] = {}
                if isinstance(deliveries, dict):
                    direct = (deliveries.get(actor["client_id"]) or {}).get("result")
                    if isinstance(direct, dict):
                        result_payload = direct
                    else:
                        for delivery in deliveries.values():
                            if not isinstance(delivery, dict):
                                continue
                            candidate = delivery.get("result")
                            if isinstance(candidate, dict):
                                result_payload = candidate
                                break
                if "ok" not in result_payload:
                    result_payload["ok"] = False
                if "status" not in result_payload:
                    result_payload["status"] = status
                if raise_on_fail and not result_payload.get("ok"):
                    error = result_payload.get("error") or {}
                    if isinstance(error, dict):
                        message = normalize_space(error.get("message")) or json.dumps(error, ensure_ascii=False)
                    else:
                        message = normalize_space(error)
                    raise RuntimeError(f"SiteControlKit command failed ({command.get('type')}): {message or status}")
                return result_payload
            time.sleep(0.2)
        if raise_on_fail:
            raise RuntimeError(f"Timeout waiting for SiteControlKit command: {command.get('type')}")
        return {"ok": False, "status": "timed_out"}


def resolve_token(config: dict[str, Any]) -> str:
    explicit = normalize_space(config["site_control"].get("token"))
    if explicit:
        return explicit
    env_name = normalize_space(config["site_control"].get("token_env"))
    if env_name:
        env_value = normalize_space(os.getenv(env_name))
        if env_value:
            return env_value
    raise ConfigError("SiteControlKit token is not configured. Set site_control.token or the token_env variable.")


def _snapshot_actor(site_control: SiteControlClient, actor: dict[str, Any]) -> dict[str, Any]:
    delivery = site_control.send_command(
        actor=actor,
        command={
            "type": "run_script",
            "script": CHAT_SNAPSHOT_SCRIPT,
            "args": {"selectors": list(COMPOSER_SELECTORS)},
        },
        timeout_sec=12,
    )
    data = delivery.get("data") or {}
    if not isinstance(data, dict):
        return {}
    value = data.get("value")
    return dict(value) if isinstance(value, dict) else {}


def _verify_chat_snapshot(config: dict[str, Any], chat: dict[str, Any], snapshot: dict[str, Any], *, require_composer: bool) -> None:
    current_url = normalize_space(snapshot.get("current_url"))
    parsed = urlparse(current_url)
    if not TELEGRAM_WEB_HOST_RE.fullmatch(parsed.netloc or ""):
        raise ExecutionSafetyError(f"Active tab is not Telegram Web: {current_url}")
    fragment_ok = normalize_fragment(snapshot.get("current_fragment")) == chat["expected_fragment"]
    if not fragment_ok:
        fragment_ok = normalize_fragment(snapshot.get("active_dialog_fragment")) == chat["expected_fragment"]
    title_ok = False
    expected_title = chat["title_norm"]
    for candidate in (
        snapshot.get("chat_title"),
        snapshot.get("active_dialog_title"),
        snapshot.get("document_title"),
    ):
        normalized = normalize_title(candidate)
        if normalized and expected_title and expected_title in normalized:
            title_ok = True
            break
    if config["safety"]["require_fragment_match"] and not fragment_ok:
        raise ExecutionSafetyError(
            f"Opened chat fragment does not match allowlist for {chat['chat_id']}: "
            f"expected={chat['expected_fragment']} actual={normalize_fragment(snapshot.get('current_fragment'))}"
        )
    if config["safety"]["require_title_match"] and not title_ok:
        raise ExecutionSafetyError(
            f"Opened chat title does not match allowlist for {chat['chat_id']}: "
            f"expected={chat['title']} actual={normalize_space(snapshot.get('chat_title'))}"
        )
    if require_composer and not bool(snapshot.get("composer_present")):
        raise ExecutionSafetyError(f"Telegram composer is not ready in allowlisted chat {chat['chat_id']}")


def prepare_chat(site_control: SiteControlClient, config: dict[str, Any], actor: dict[str, Any], chat: dict[str, Any], *, require_composer: bool) -> dict[str, Any]:
    site_control.ensure_actor_online(actor)
    site_control.send_command(
        actor=actor,
        command={"type": "navigate", "url": chat["url"]},
        timeout_sec=20,
    )
    site_control.send_command(
        actor=actor,
        command={"type": "wait_selector", "selector": CHAT_READY_SELECTOR, "timeout_ms": 15000, "visible_only": False},
        timeout_sec=18,
    )
    deadline = time.time() + 15
    last_snapshot: dict[str, Any] = {}
    while time.time() < deadline:
        snapshot = _snapshot_actor(site_control, actor)
        last_snapshot = snapshot
        try:
            _verify_chat_snapshot(config, chat, snapshot, require_composer=require_composer)
            return snapshot
        except ExecutionSafetyError:
            time.sleep(0.6)
    _verify_chat_snapshot(config, chat, last_snapshot, require_composer=require_composer)
    return last_snapshot


def append_state_history(state: dict[str, Any], entry: dict[str, Any], *, preserve_history_limit: int) -> None:
    history = state.setdefault("history", [])
    history.append(entry)
    if len(history) > preserve_history_limit:
        del history[: len(history) - preserve_history_limit]
    state["updated_at"] = now_utc()


def try_click_any(site_control: SiteControlClient, actor: dict[str, Any], selectors: tuple[str, ...], *, timeout_sec: int = 8) -> dict[str, Any] | None:
    for selector in selectors:
        result = site_control.send_command(
            actor=actor,
            command={"type": "click", "selector": selector},
            timeout_sec=timeout_sec,
            raise_on_fail=False,
        )
        if result.get("ok"):
            return {"selector": selector, "result": result}
    return None


def wait_for_any_selector(site_control: SiteControlClient, actor: dict[str, Any], selectors: tuple[str, ...], *, timeout_ms: int = 6000) -> dict[str, Any] | None:
    per_selector = max(int(timeout_ms / max(len(selectors), 1)), 800)
    for selector in selectors:
        result = site_control.send_command(
            actor=actor,
            command={"type": "wait_selector", "selector": selector, "timeout_ms": per_selector, "visible_only": False},
            timeout_sec=max(int(timeout_ms / 1000) + 2, 4),
            raise_on_fail=False,
        )
        if result.get("ok"):
            return {"selector": selector, "result": result}
    return None


def read_body_html(site_control: SiteControlClient, actor: dict[str, Any]) -> str:
    result = site_control.send_command(
        actor=actor,
        command={"type": "get_html"},
        timeout_sec=12,
    )
    data = result.get("data") or {}
    html_payload = data.get("html") if isinstance(data, dict) else ""
    if not isinstance(html_payload, str):
        raise RuntimeError("SiteControlKit did not return page HTML")
    return html_payload


def open_profile_sidebar(site_control: SiteControlClient, actor: dict[str, Any]) -> dict[str, Any]:
    clicked = try_click_any(site_control, actor, CHAT_INFO_CLICK_SELECTORS, timeout_sec=8)
    if not clicked:
        raise RuntimeError("Could not click Telegram chat header to open sidebar")
    sidebar = wait_for_any_selector(site_control, actor, RIGHT_SIDEBAR_SELECTORS, timeout_ms=8000)
    if not sidebar:
        raise RuntimeError("Telegram right sidebar did not open")
    return {
        "header_click": clicked,
        "sidebar_ready": sidebar,
    }


def open_add_members_panel(site_control: SiteControlClient, actor: dict[str, Any]) -> dict[str, Any]:
    clicked = try_click_any(site_control, actor, ADD_MEMBERS_OPEN_SELECTORS, timeout_sec=8)
    if not clicked:
        raise RuntimeError("Add members button is not available in this allowlisted chat")
    ready = site_control.send_command(
        actor=actor,
        command={"type": "wait_selector", "selector": ADD_MEMBERS_SEARCH_SELECTOR, "timeout_ms": 10000, "visible_only": False},
        timeout_sec=12,
    )
    return {
        "open_click": clicked,
        "search_ready": ready,
    }


def parse_add_members_candidates(html_payload: str) -> list[dict[str, str]]:
    scoped = html_payload
    marker = "add-members-container active"
    start = html_payload.find(marker)
    if start >= 0:
        scoped = html_payload[start:]
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    row_pattern = re.compile(
        r'<a\b(?=[^>]*\bdata-peer-id="(?P<peer_id>\d+)")[^>]*\bclass="(?P<class>[^"]*\bchatlist-chat[^"]*)"[^>]*>(?P<body>.*?)</a>',
        re.DOTALL,
    )
    title_pattern = re.compile(r'<span\b(?=[^>]*\bclass="[^"]*\bpeer-title\b[^"]*")[^>]*>(?P<title>.*?)</span>', re.DOTALL)
    for match in row_pattern.finditer(scoped):
        peer_id = match.group("peer_id")
        if peer_id in seen:
            continue
        title_match = title_pattern.search(match.group("body"))
        title = strip_tags(title_match.group("title")) if title_match else ""
        if not title:
            continue
        seen.add(peer_id)
        candidates.append({"peer_id": peer_id, "title": title})
    return candidates


def choose_add_members_candidate(contact: dict[str, Any], candidates: list[dict[str, str]], *, allow_first_result: bool) -> dict[str, str]:
    if not candidates:
        raise RuntimeError(f"No add-members candidates found for {contact['contact_id']}")
    peer_id = normalize_space(contact.get("peer_id"))
    if peer_id:
        for candidate in candidates:
            if normalize_space(candidate.get("peer_id")) == peer_id:
                return candidate
    display_name_norm = normalize_title(contact.get("display_name"))
    if display_name_norm:
        exact = [candidate for candidate in candidates if normalize_title(candidate.get("title")) == display_name_norm]
        if len(exact) == 1:
            return exact[0]
    if len(candidates) == 1:
        return candidates[0]
    if allow_first_result or bool(contact.get("allow_first_result")):
        return candidates[0]
    raise RuntimeError(
        f"Add-members search returned multiple candidates for {contact['contact_id']}; "
        "set allow_first_result for that contact or pass --allow-first-result after manual verification"
    )


def find_visible_terms(site_control: SiteControlClient, actor: dict[str, Any], terms: tuple[str, ...], *, root_selector: str = "") -> dict[str, Any]:
    delivery = site_control.send_command(
        actor=actor,
        command={
            "type": "run_script",
            "script": FIND_VISIBLE_TEXT_SCRIPT,
            "args": {"terms": list(terms), "root_selector": root_selector},
        },
        timeout_sec=10,
        raise_on_fail=False,
    )
    data = delivery.get("data") or {}
    value = data.get("value")
    return dict(value) if isinstance(value, dict) else {}


def set_composer_text(site_control: SiteControlClient, actor: dict[str, Any], text: str) -> dict[str, Any]:
    delivery = site_control.send_command(
        actor=actor,
        command={
            "type": "run_script",
            "script": SET_COMPOSER_TEXT_SCRIPT,
            "args": {
                "selectors": list(COMPOSER_SELECTORS),
                "text": text,
            },
        },
        timeout_sec=12,
    )
    data = delivery.get("data") or {}
    value = data.get("value")
    if not isinstance(value, dict):
        raise RuntimeError("SiteControlKit returned unexpected composer write payload")
    return dict(value)


def read_composer_text(site_control: SiteControlClient, actor: dict[str, Any]) -> dict[str, Any]:
    delivery = site_control.send_command(
        actor=actor,
        command={
            "type": "run_script",
            "script": READ_COMPOSER_TEXT_SCRIPT,
            "args": {"selectors": list(COMPOSER_SELECTORS)},
        },
        timeout_sec=10,
    )
    data = delivery.get("data") or {}
    value = data.get("value")
    return dict(value) if isinstance(value, dict) else {}


def scroll_chat(site_control: SiteControlClient, actor: dict[str, Any], delta_y: int) -> dict[str, Any]:
    delivery = site_control.send_command(
        actor=actor,
        command={
            "type": "run_script",
            "script": SCROLL_CHAT_SCRIPT,
            "args": {
                "selectors": list(CHAT_SCROLL_SELECTORS),
                "delta_y": int(delta_y),
            },
        },
        timeout_sec=12,
    )
    data = delivery.get("data") or {}
    value = data.get("value")
    return dict(value) if isinstance(value, dict) else {}


def execute_step(site_control: SiteControlClient, config: dict[str, Any], step: dict[str, Any]) -> dict[str, Any]:
    actor = next(item for item in config["actors"] if item["actor_id"] == step["actor_id"])
    chat = next(item for item in config["allowlist_chats"] if item["chat_id"] == step["chat_id"])
    snapshot = prepare_chat(
        site_control,
        config,
        actor,
        chat,
        require_composer=step["action"] == "send_message",
    )
    result: dict[str, Any] = {
        "preflight_snapshot": snapshot,
        "actor_id": step["actor_id"],
        "chat_id": step["chat_id"],
        "action": step["action"],
    }
    if step["action"] == "open_chat":
        return result
    if step["action"] == "idle_scroll":
        result["scroll"] = scroll_chat(site_control, actor, int(step.get("scroll_delta_y") or 280))
        return result
    if step["action"] == "send_message":
        message_text = str(step.get("message_text") or "")
        composer_write = set_composer_text(site_control, actor, message_text)
        result["composer_write"] = composer_write
        composer_selector = normalize_space(composer_write.get("selector")) or normalize_space(snapshot.get("composer_selector"))
        pre_send = read_composer_text(site_control, actor)
        result["composer_before_send"] = pre_send
        if normalize_space(pre_send.get("text")) != normalize_space(message_text):
            raise RuntimeError("Composer text verification failed before send")
        site_control.send_command(
            actor=actor,
            command={"type": "press_key", "key": "Enter", "selector": composer_selector or None},
            timeout_sec=8,
        )
        time.sleep(0.8)
        post_send = read_composer_text(site_control, actor)
        result["composer_after_send"] = post_send
        if normalize_space(post_send.get("text")) == normalize_space(message_text):
            raise RuntimeError("Composer still contains the same text after send")
        return result
    raise RuntimeError(f"Unsupported plan action: {step['action']}")


def write_run_artifacts(state_path: Path, payload: dict[str, Any]) -> Path:
    run_id = normalize_space(payload.get("run_id")) or now_utc().replace(":", "").replace("-", "").replace("Z", "")
    runs_dir = state_path.parent / DEFAULT_RUNS_DIR_NAME / run_id
    runs_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(runs_dir / "run.json", payload)
    return runs_dir


def command_init(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    state_path = Path(args.state_file).expanduser()
    config = load_config(config_path)
    state = build_default_state(config_path)
    atomic_write_json(state_path, state)
    print(json.dumps(summarize_state(config, state, state_path=state_path), ensure_ascii=False, indent=2))
    return 0


def command_status(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    state_path = Path(args.state_file).expanduser()
    config = load_config(config_path)
    state = load_or_init_state(state_path, config_path)
    print(json.dumps(summarize_state(config, state, state_path=state_path), ensure_ascii=False, indent=2))
    return 0


def command_import_contacts(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    raw_config = load_json(config_path)

    if args.usernames_file:
        raw_text = Path(args.usernames_file).expanduser().read_text(encoding="utf-8")
    else:
        raw_text = sys.stdin.read()
    usernames, invalid_lines = parse_usernames_blob(raw_text)

    contacts = raw_config.get("allowlist_contacts")
    if not isinstance(contacts, list):
        contacts = []
        raw_config["allowlist_contacts"] = contacts

    existing_usernames: set[str] = set()
    existing_ids: set[str] = set()
    for item in contacts:
        if not isinstance(item, dict):
            continue
        username = normalize_space(item.get("username"))
        if username:
            existing_usernames.add(username.lower())
        contact_id = normalize_space(item.get("contact_id"))
        if contact_id:
            existing_ids.add(contact_id)

    imported: list[dict[str, Any]] = []
    skipped_duplicates: list[str] = []
    for username in usernames:
        lowered = username.lower()
        if lowered in existing_usernames:
            skipped_duplicates.append(username)
            continue
        existing_usernames.add(lowered)
        base_id = contact_id_from_username(username)
        contact_id = ensure_unique_contact_id(existing_ids, base_id)
        record = {
            "contact_id": contact_id,
            "username": username,
            "display_name": username.lstrip("@"),
            "allowed_chat_ids": [],
        }
        contacts.append(record)
        imported.append(record)

    normalize_config(raw_config, config_path)
    write_json(config_path, raw_config)

    response = {
        "status": "completed",
        "config_path": str(config_path),
        "imported_count": len(imported),
        "skipped_duplicates_count": len(skipped_duplicates),
        "invalid_lines_count": len(invalid_lines),
        "imported_preview": imported[:20],
        "invalid_lines_preview": invalid_lines[:20],
        "total_allowlist_contacts": len([item for item in contacts if isinstance(item, dict)]),
    }
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


def command_api_status(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    config = load_config(config_path)
    actor = find_actor(config, args.actor_id)
    payload: dict[str, Any] = {
        "config_path": str(config_path),
        "actor_id": actor["actor_id"],
        "api_sidecar_enabled": bool(config["api_sidecar"]["enabled"]),
        "preferred_mode": config["api_sidecar"]["preferred_mode"],
        "session_file": str(api_session_file_path(config, actor)),
    }
    if not bool(config["api_sidecar"]["enabled"]):
        payload["status"] = "disabled"
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    result = run_api_sidecar_json(config, actor, "status")
    payload["status"] = "completed" if int(result.get("returncode", 1) or 0) == 0 else "failed"
    payload["probe"] = compact_process_payload(result)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "completed" else 1


def command_api_import_tdata_session(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    config = load_config(config_path)
    actor = find_actor(config, args.actor_id)
    payload: dict[str, Any] = {
        "config_path": str(config_path),
        "actor_id": actor["actor_id"],
        "api_sidecar_enabled": bool(config["api_sidecar"]["enabled"]),
        "preferred_mode": config["api_sidecar"]["preferred_mode"],
        "session_file": str(api_session_file_path(config, actor)),
    }
    if not bool(config["api_sidecar"]["enabled"]):
        payload["status"] = "disabled"
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    tdata_dir = resolve_actor_tdata_dir(actor, args.tdata_dir)
    payload["tdata_dir"] = str(tdata_dir)
    action_args = ["--tdata-dir", str(tdata_dir)]
    if normalize_space(args.desktop_passcode):
        action_args.extend(["--desktop-passcode", str(normalize_space(args.desktop_passcode))])
    result = run_api_sidecar_json(config, actor, "import-tdata-session", *action_args)
    payload["status"] = "completed" if int(result.get("returncode", 1) or 0) == 0 else "failed"
    payload["probe"] = compact_process_payload(result)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "completed" else 1


def command_api_scan_contacts(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    state_path = Path(args.state_file).expanduser()
    config = load_config(config_path)
    actor = find_actor(config, args.actor_id)
    explicit_contact_ids = list(args.contact_id or [])
    if args.contact_id_file:
        explicit_contact_ids.extend(read_contact_ids_file(args.contact_id_file))
    contact_ids = build_contact_id_batch(
        config,
        explicit_contact_ids=explicit_contact_ids,
        limit=(int(args.limit) if args.limit is not None else None),
    )
    payload: dict[str, Any] = {
        "run_id": now_utc().replace(":", "").replace("-", "").replace("Z", "") + "-" + uuid.uuid4().hex[:8],
        "command": "api-scan-contacts",
        "config_path": str(config_path),
        "state_path": str(state_path),
        "actor_id": actor["actor_id"],
        "contact_ids": contact_ids,
        "target_count": len(contact_ids),
        "items": [],
    }
    if not bool(config["api_sidecar"]["enabled"]):
        payload["status"] = "disabled"
        run_dir = write_run_artifacts(state_path, payload)
        payload["run_dir"] = str(run_dir)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    api_probe = run_api_sidecar_json(config, actor, "status")
    payload["api_probe"] = compact_process_payload(api_probe)
    probe_json = payload["api_probe"]["stdout_json"]
    authorized = bool(payload["api_probe"]["returncode"] == 0 and probe_json.get("authorized"))
    if not authorized:
        payload["status"] = "api_not_authorized"
        run_dir = write_run_artifacts(state_path, payload)
        payload["run_dir"] = str(run_dir)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    valid_user_contact_ids: list[str] = []
    invalid_contact_ids: list[str] = []
    non_user_contact_ids: list[str] = []
    failed_contact_ids: list[str] = []

    for contact_id in contact_ids:
        contact = find_contact(config, contact_id)
        item: dict[str, Any] = {
            "contact_id": contact["contact_id"],
            "username": contact["username"],
            "display_name": contact["display_name"],
        }
        resolve_result = run_api_sidecar_json(config, actor, "resolve-username", "--username", str(contact["username"]))
        item["api_resolve"] = compact_process_payload(resolve_result)
        resolve_json = item["api_resolve"]["stdout_json"]
        status = normalize_space(resolve_json.get("status"))
        item["status"] = status or ("resolved" if item["api_resolve"]["returncode"] == 0 else "failed")
        if item["api_resolve"]["returncode"] == 0 and status == "resolved_user":
            item["entity_id"] = resolve_json.get("entity_id")
            item["entity_username"] = resolve_json.get("entity_username")
            valid_user_contact_ids.append(contact["contact_id"])
        elif status == "resolved_non_user":
            non_user_contact_ids.append(contact["contact_id"])
        elif status == "not_found":
            invalid_contact_ids.append(contact["contact_id"])
        else:
            failed_contact_ids.append(contact["contact_id"])
        payload["items"].append(item)

    payload["valid_user_contact_ids"] = valid_user_contact_ids
    payload["invalid_contact_ids"] = invalid_contact_ids
    payload["non_user_contact_ids"] = non_user_contact_ids
    payload["failed_contact_ids"] = failed_contact_ids
    payload["counts"] = {
        "valid_user": len(valid_user_contact_ids),
        "invalid_not_found": len(invalid_contact_ids),
        "resolved_non_user": len(non_user_contact_ids),
        "failed": len(failed_contact_ids),
    }
    if normalize_space(args.write_valid_contact_id_file):
        output_path = Path(args.write_valid_contact_id_file).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(valid_user_contact_ids) + ("\n" if valid_user_contact_ids else ""), encoding="utf-8")
        payload["write_valid_contact_id_file"] = str(output_path.resolve())
    payload["status"] = "completed"
    run_dir = write_run_artifacts(state_path, payload)
    payload["run_dir"] = str(run_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_plan(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    state_path = Path(args.state_file).expanduser()
    config = load_config(config_path)
    state = load_or_init_state(state_path, config_path)
    iterations = to_int(args.iterations, default=config["activity"]["iterations_per_run_default"], minimum=1)
    plan = build_plan(config, state, iterations=iterations, actor_filter=normalize_space(args.actor_id) or None, seed=args.seed)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def command_batch_add_contacts(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    state_path = Path(args.state_file).expanduser()
    config = load_config(config_path)
    actor = find_actor(config, args.actor_id)
    explicit_contact_ids = list(args.contact_id or [])
    if args.contact_id_file:
        explicit_contact_ids.extend(read_contact_ids_file(args.contact_id_file))
    contact_ids = build_contact_id_batch(
        config,
        explicit_contact_ids=explicit_contact_ids,
        limit=(int(args.limit) if args.limit is not None else None),
    )
    backend_preference = normalize_space(args.backend) or config["api_sidecar"]["preferred_mode"]
    if backend_preference not in ALLOWED_API_SIDECAR_MODES:
        raise ConfigError(f"Unsupported backend mode: {backend_preference}")

    run_id = now_utc().replace(":", "").replace("-", "").replace("Z", "") + "-" + uuid.uuid4().hex[:8]
    payload: dict[str, Any] = {
        "run_id": run_id,
        "command": "batch-add-contacts",
        "config_path": str(config_path),
        "state_path": str(state_path),
        "actor_id": actor["actor_id"],
        "contact_ids": contact_ids,
        "target_count": len(contact_ids),
        "execute": bool(args.execute),
        "backend_preference": backend_preference,
        "random_pause_seconds": {
            "min": float(args.min_random_pause),
            "max": float(args.max_random_pause),
        },
        "items": [],
    }
    if not contact_ids:
        payload["status"] = "no_targets"
        write_run_artifacts(state_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not args.execute:
        payload["status"] = "dry_run"
        payload["manual_gate"] = "Pass --execute to run Add to contacts in batch mode."
        write_run_artifacts(state_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    api_probe: dict[str, Any] | None = None
    api_authorized = False
    api_enabled = bool(config["api_sidecar"]["enabled"])
    if backend_preference != "portable_only":
        if api_enabled:
            api_probe = run_api_sidecar_json(config, actor, "status")
            probe_json = api_probe.get("stdout_json") if isinstance(api_probe.get("stdout_json"), dict) else {}
            api_authorized = int(api_probe.get("returncode", 1) or 0) == 0 and bool(probe_json.get("authorized"))
        else:
            api_probe = {
                "command": [],
                "returncode": 1,
                "stderr": "",
                "stdout_json": {
                    "ok": False,
                    "status": "disabled",
                    "reason": "api_sidecar is disabled in config",
                },
            }
        payload["api_probe"] = compact_process_payload(api_probe)

    rng = random.Random(args.seed)
    stop_early = False
    for index, contact_id in enumerate(contact_ids):
        contact = find_contact(config, contact_id)
        item: dict[str, Any] = {
            "index": index + 1,
            "contact_id": contact["contact_id"],
            "username": contact["username"],
            "display_name": contact["display_name"],
            "started_at": now_utc(),
        }
        success = False
        skip_portable_fallback = False
        if backend_preference != "portable_only" and api_authorized:
            api_resolve = run_api_sidecar_json(
                config,
                actor,
                "resolve-username",
                "--username",
                str(contact["username"]),
            )
            item["api_resolve"] = compact_process_payload(api_resolve)
            api_resolve_json = item["api_resolve"]["stdout_json"]
            resolve_status = normalize_space(api_resolve_json.get("status"))
            if item["api_resolve"]["returncode"] != 0:
                item["backend_used"] = "api"
                item["status"] = resolve_status or "failed"
                item["error"] = normalize_space(
                    str(api_resolve_json.get("error") or item["api_resolve"].get("stderr") or "API resolve-username failed")
                )
                if resolve_status in {"not_found", "resolved_non_user"}:
                    skip_portable_fallback = True
            else:
                item["resolved_entity_id"] = api_resolve_json.get("entity_id")
                item["resolved_entity_username"] = api_resolve_json.get("entity_username")

        if backend_preference != "portable_only" and api_authorized and not skip_portable_fallback:
            api_add = run_api_sidecar_json(
                config,
                actor,
                "add-contact",
                "--username",
                str(contact["username"]),
                "--first-name",
                str(contact["display_name"] or contact["username"].lstrip("@")),
                "--last-name",
                str(normalize_space(args.last_name_text)),
            )
            item["api_add"] = compact_process_payload(api_add)
            api_add_json = item["api_add"]["stdout_json"]
            if item["api_add"]["returncode"] == 0 and bool(api_add_json.get("ok")):
                item["backend_used"] = "api"
                item["status"] = str(api_add_json.get("status") or "api_contact_added")
                item["verified"] = bool(api_add_json.get("contact_present_after"))
                item["verification_backend"] = "api"
                success = True
            elif backend_preference == "api_only":
                item["backend_used"] = "api"
                item["status"] = "failed"
                item["error"] = normalize_space(
                    str(api_add_json.get("error") or item["api_add"].get("stderr") or "API add-contact failed")
                )

        if not success and not skip_portable_fallback and backend_preference != "api_only":
            child_args = [
                "prepare-add-contact-profile",
                "--config",
                str(config_path),
                "--state-file",
                str(state_path),
                "--actor-id",
                actor["actor_id"],
                "--contact-id",
                contact["contact_id"],
                "--execute",
                "--launch-if-needed",
                "--confirm-add",
                "--search-results-wait",
                str(float(args.search_results_wait)),
                "--open-wait",
                str(float(args.open_wait)),
                "--after-add-wait",
                str(float(args.after_add_wait)),
                "--after-done-wait",
                str(float(args.after_done_wait)),
                "--verify-wait",
                str(float(args.verify_wait)),
                "--done-click-repeat",
                str(int(args.done_click_repeat)),
                "--search-result-x-ratio",
                str(float(args.search_result_x_ratio)),
                "--search-result-y-ratio",
                str(float(args.search_result_y_ratio)),
                "--search-result-step-y-ratio",
                str(float(args.search_result_step_y_ratio)),
                "--add-click-x-ratio",
                str(float(args.add_click_x_ratio)),
                "--add-click-y-ratio",
                str(float(args.add_click_y_ratio)),
                "--done-click-x-ratio",
                str(float(args.done_click_x_ratio)),
                "--done-click-y-ratio",
                str(float(args.done_click_y_ratio)),
            ]
            if bool(args.verify_profile_reopen):
                child_args.append("--verify-profile-reopen")
            if getattr(args, "search_result_index", None) is not None:
                child_args.extend(["--search-result-index", str(int(args.search_result_index))])
            if normalize_space(args.last_name_text):
                child_args.extend(["--last-name-text", str(normalize_space(args.last_name_text))])
            if normalize_space(args.first_name_text):
                child_args.extend(["--first-name-text", str(normalize_space(args.first_name_text))])
            portable_result = run_self_json(child_args)
            item["portable_add"] = compact_process_payload(portable_result)
            portable_json = item["portable_add"]["stdout_json"]
            item["backend_used"] = "portable"
            item["status"] = str(portable_json.get("status") or "portable_completed")
            item["run_dir"] = str(portable_json.get("run_dir") or "")
            if api_authorized:
                api_check = run_api_sidecar_json(config, actor, "check-contact", "--username", str(contact["username"]))
                item["api_verify_after_portable"] = compact_process_payload(api_check)
                api_check_json = item["api_verify_after_portable"]["stdout_json"]
                item["verified"] = bool(
                    item["api_verify_after_portable"]["returncode"] == 0 and api_check_json.get("contact_present")
                )
                item["verification_backend"] = "api"
            else:
                item["verified"] = False
                item["verification_backend"] = "portable_screenshot"
                if bool(args.verify_profile_reopen):
                    item["manual_review_required"] = True
            success = item["portable_add"]["returncode"] == 0
            if not success:
                item["error"] = normalize_space(
                    str(item["portable_add"]["stdout_json"].get("error") or item["portable_add"].get("stderr") or "")
                )

        item["completed_at"] = now_utc()
        payload["items"].append(item)
        if not success and bool(args.fail_fast):
            stop_early = True
            break
        if index < len(contact_ids) - 1 and not stop_early:
            pause_seconds = random_pause_seconds(float(args.min_random_pause), float(args.max_random_pause), rng=rng)
            item["next_pause_seconds"] = pause_seconds
            if pause_seconds > 0:
                time.sleep(pause_seconds)

    state = load_or_init_state(state_path, config_path)
    append_state_history(
        state,
        {
            "run_id": run_id,
            "action": "batch_add_contacts",
            "actor_id": actor["actor_id"],
            "target_count": len(contact_ids),
            "completed_count": len([item for item in payload["items"] if normalize_space(item.get("status"))]),
            "verified_count": len([item for item in payload["items"] if bool(item.get("verified"))]),
            "status": "completed" if not stop_early else "stopped_early",
            "executed_at": now_utc(),
        },
        preserve_history_limit=int(config["safety"]["history_limit"]),
    )
    atomic_write_json(state_path, state)
    payload["status"] = "completed" if not stop_early else "stopped_early"
    payload["completed_at"] = now_utc()
    payload["summary"] = summarize_state(config, state, state_path=state_path)
    payload["verified_count"] = len([item for item in payload["items"] if bool(item.get("verified"))])
    payload["successful_count"] = len(
        [item for item in payload["items"] if normalize_space(item.get("status")) and "failed" not in str(item.get("status"))]
    )
    run_dir = write_run_artifacts(state_path, payload)
    payload["run_dir"] = str(run_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "completed" else 1


def command_run(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    state_path = Path(args.state_file).expanduser()
    config = load_config(config_path)
    state = load_or_init_state(state_path, config_path)
    iterations = to_int(args.iterations, default=config["activity"]["iterations_per_run_default"], minimum=1)
    plan = build_plan(config, state, iterations=iterations, actor_filter=normalize_space(args.actor_id) or None, seed=args.seed)
    should_execute = bool(args.execute)
    run_payload: dict[str, Any] = {
        "run_id": plan["run_id"],
        "created_at": now_utc(),
        "config_path": config["config_path"],
        "state_path": str(state_path),
        "execute": should_execute,
        "steps": [],
    }

    if not should_execute:
        run_payload["mode"] = "dry_run"
        run_payload["steps"] = plan["steps"]
        write_run_artifacts(state_path, run_payload)
        print(json.dumps(run_payload, ensure_ascii=False, indent=2))
        return 0

    site_control = SiteControlClient(
        server_url=config["site_control"]["server_url"],
        token=resolve_token(config),
    )
    for index, step in enumerate(plan["steps"]):
        step_copy = copy.deepcopy(step)
        if args.respect_delays and index > 0 and int(step_copy.get("delay_seconds") or 0) > 0:
            time.sleep(int(step_copy["delay_seconds"]))
        try:
            step_copy["result"] = execute_step(site_control, config, step_copy)
            record_step_result(
                state,
                step_copy,
                status="executed",
                preserve_history_limit=int(config["safety"]["history_limit"]),
            )
        except Exception as exc:
            record_step_result(
                state,
                step_copy,
                status="failed",
                error=str(exc),
                preserve_history_limit=int(config["safety"]["history_limit"]),
            )
            step_copy["status"] = "failed"
            step_copy["error"] = str(exc)
            if args.fail_fast:
                run_payload["steps"].append(step_copy)
                break
        run_payload["steps"].append(step_copy)

    atomic_write_json(state_path, state)
    run_payload["completed_at"] = now_utc()
    run_payload["summary"] = summarize_state(config, state, state_path=state_path)
    run_dir = write_run_artifacts(state_path, run_payload)
    run_payload["run_dir"] = str(run_dir)
    print(json.dumps(run_payload, ensure_ascii=False, indent=2))
    return 0


def command_prepare_invite(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    state_path = Path(args.state_file).expanduser()
    config = load_config(config_path)
    state = load_or_init_state(state_path, config_path)
    actor = find_actor(config, args.actor_id)
    chat = find_chat(config, args.chat_id)
    contact = find_contact(config, args.contact_id)
    if contact["allowed_chat_ids"] and chat["chat_id"] not in contact["allowed_chat_ids"]:
        raise ConfigError(f"Contact {contact['contact_id']} is not allowlisted for chat {chat['chat_id']}")

    run_id = now_utc().replace(":", "").replace("-", "").replace("Z", "") + "-" + uuid.uuid4().hex[:8]
    payload: dict[str, Any] = {
        "run_id": run_id,
        "command": "prepare-invite",
        "actor_id": actor["actor_id"],
        "chat_id": chat["chat_id"],
        "contact_id": contact["contact_id"],
        "contact_username": contact["username"],
        "execute": bool(args.execute),
        "confirm_final": bool(args.confirm_final),
        "allow_first_result": bool(args.allow_first_result),
        "steps": [],
    }
    if not args.execute:
        payload["status"] = "dry_run"
        payload["search_query"] = contact["search_query"]
        payload["manual_gate"] = "The tool will stop before the final Telegram confirmation popup click unless --confirm-final is passed."
        write_run_artifacts(state_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    site_control = SiteControlClient(
        server_url=config["site_control"]["server_url"],
        token=resolve_token(config),
    )
    snapshot = prepare_chat(site_control, config, actor, chat, require_composer=False)
    payload["steps"].append({"label": "prepare_chat", "snapshot": snapshot})

    sidebar = open_profile_sidebar(site_control, actor)
    payload["steps"].append({"label": "open_profile_sidebar", **sidebar})

    add_members = open_add_members_panel(site_control, actor)
    payload["steps"].append({"label": "open_add_members_panel", **add_members})

    site_control.send_command(
        actor=actor,
        command={"type": "fill", "selector": ADD_MEMBERS_SEARCH_SELECTOR, "value": contact["search_query"]},
        timeout_sec=10,
    )
    time.sleep(max(float(args.search_wait), 0.0))
    html_payload = read_body_html(site_control, actor)
    candidates = parse_add_members_candidates(html_payload)
    selected = choose_add_members_candidate(contact, candidates, allow_first_result=bool(args.allow_first_result))
    payload["steps"].append(
        {
            "label": "search_contact",
            "search_query": contact["search_query"],
            "candidates": candidates,
            "selected_candidate": selected,
        }
    )

    site_control.send_command(
        actor=actor,
        command={
            "type": "click",
            "selector": f'.add-members-container .chatlist a.row[data-peer-id="{selected["peer_id"]}"], .add-members-container a[data-peer-id="{selected["peer_id"]}"]',
        },
        timeout_sec=10,
    )
    payload["steps"].append({"label": "select_candidate", "peer_id": selected["peer_id"], "title": selected["title"]})

    site_control.send_command(
        actor=actor,
        command={"type": "click", "selector": ADD_MEMBERS_CONFIRM_SELECTOR},
        timeout_sec=10,
    )
    payload["steps"].append({"label": "open_confirmation_popup"})

    if args.confirm_final:
        site_control.send_command(
            actor=actor,
            command={"type": "click", "selector": ADD_MEMBERS_POPUP_ADD_SELECTOR},
            timeout_sec=10,
        )
        payload["status"] = "invite_requested"
        payload["steps"].append({"label": "confirm_final_add"})
    else:
        payload["status"] = "awaiting_manual_confirmation"
        payload["manual_gate"] = "Telegram confirmation popup is open. User can review and click the final Add button manually."

    append_state_history(
        state,
        {
            "run_id": run_id,
            "action": "prepare_invite",
            "actor_id": actor["actor_id"],
            "chat_id": chat["chat_id"],
            "contact_id": contact["contact_id"],
            "status": payload["status"],
            "executed_at": now_utc(),
        },
        preserve_history_limit=int(config["safety"]["history_limit"]),
    )
    atomic_write_json(state_path, state)
    payload["summary"] = summarize_state(config, state, state_path=state_path)
    run_dir = write_run_artifacts(state_path, payload)
    payload["run_dir"] = str(run_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_prepare_join(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    state_path = Path(args.state_file).expanduser()
    config = load_config(config_path)
    state = load_or_init_state(state_path, config_path)
    actor = find_actor(config, args.actor_id)
    chat = find_chat(config, args.chat_id)

    run_id = now_utc().replace(":", "").replace("-", "").replace("Z", "") + "-" + uuid.uuid4().hex[:8]
    payload: dict[str, Any] = {
        "run_id": run_id,
        "command": "prepare-join",
        "actor_id": actor["actor_id"],
        "chat_id": chat["chat_id"],
        "execute": bool(args.execute),
        "confirm_join": bool(args.confirm_join),
    }
    if not args.execute:
        payload["status"] = "dry_run"
        payload["manual_gate"] = "Without --confirm-join the tool only opens the allowlisted chat and reports whether a Join button is visible."
        write_run_artifacts(state_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    site_control = SiteControlClient(
        server_url=config["site_control"]["server_url"],
        token=resolve_token(config),
    )
    snapshot = prepare_chat(site_control, config, actor, chat, require_composer=False)
    button_state = find_visible_terms(site_control, actor, JOIN_BUTTON_TERMS, root_selector="")
    payload["snapshot"] = snapshot
    payload["join_button_state"] = button_state

    if not bool(button_state.get("found")):
        payload["status"] = "already_open_or_join_not_needed"
    elif not args.confirm_join:
        payload["status"] = "awaiting_manual_confirmation"
        payload["manual_gate"] = f"Visible join button detected: {button_state.get('text') or 'join'}. User can click it manually."
    else:
        site_control.send_command(
            actor=actor,
            command={"type": "click_text", "terms": list(JOIN_BUTTON_TERMS)},
            timeout_sec=10,
        )
        payload["status"] = "join_requested"

    append_state_history(
        state,
        {
            "run_id": run_id,
            "action": "prepare_join",
            "actor_id": actor["actor_id"],
            "chat_id": chat["chat_id"],
            "status": payload["status"],
            "executed_at": now_utc(),
        },
        preserve_history_limit=int(config["safety"]["history_limit"]),
    )
    atomic_write_json(state_path, state)
    payload["summary"] = summarize_state(config, state, state_path=state_path)
    run_dir = write_run_artifacts(state_path, payload)
    payload["run_dir"] = str(run_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_prepare_add_contact_profile(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    state_path = Path(args.state_file).expanduser()
    config = load_config(config_path)
    state = load_or_init_state(state_path, config_path)
    actor = find_actor(config, args.actor_id)
    contact = find_contact(config, args.contact_id)

    run_id = now_utc().replace(":", "").replace("-", "").replace("Z", "") + "-" + uuid.uuid4().hex[:8]
    uri = f"tg://resolve?domain={contact['username'].lstrip('@')}&profile"
    payload: dict[str, Any] = {
        "run_id": run_id,
        "command": "prepare-add-contact-profile",
        "actor_id": actor["actor_id"],
        "contact_id": contact["contact_id"],
        "contact_username": contact["username"],
        "uri": uri,
        "execute": bool(args.execute),
        "confirm_add": bool(args.confirm_add),
        "launch_if_needed": bool(args.launch_if_needed),
        "steps": [],
    }
    if not args.execute:
        payload["status"] = "dry_run"
        payload["manual_gate"] = (
            "Without --confirm-add the tool searches the allowlisted username, opens the first chat result, "
            "and stops for operator review. With --confirm-add it will continue with the desktop add-contact flow."
        )
        write_run_artifacts(state_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    portable = ensure_portable_actor_ready(config, actor, launch_if_needed=bool(args.launch_if_needed))
    if int(portable["status_result"].get("returncode", 1) or 0) != 0:
        raise RuntimeError(
            portable["status_result"].get("stderr")
            or portable["status_result"].get("stdout")
            or "portable actor status failed"
        )
    if not portable["running"]:
        raise RuntimeError("Portable actor is not running; start Telegram Desktop portable or use --launch-if-needed")

    execution_dir = state_path.parent / DEFAULT_RUNS_DIR_NAME / run_id
    execution_dir.mkdir(parents=True, exist_ok=True)

    def run_portable_step(label: str, command: list[str], *, required: bool = True) -> dict[str, Any]:
        result = {"label": label, **run_portable_json(config, command)}
        payload["steps"].append(result)
        if required and int(result.get("returncode", 1) or 0) != 0:
            raise RuntimeError(f"{label} failed: {result.get('stderr') or result.get('stdout')}")
        return result

    def capture_screenshot(label: str, filename: str) -> None:
        screenshot_path = execution_dir / filename
        result = run_portable_step(
            label,
            portable_command(config, actor, "window-screenshot", "--output", str(screenshot_path)),
            required=False,
        )
        output_json = result.get("stdout_json") if isinstance(result.get("stdout_json"), dict) else {}
        payload.setdefault("screenshots", {})[label] = str(output_json.get("output_path") or screenshot_path)

    def write_debug_json(filename: str, body: dict[str, Any]) -> None:
        target_path = execution_dir / filename
        target_path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload.setdefault("artifacts", {})[filename] = str(target_path)

    def try_accessible_type(label_prefix: str, terms: tuple[str, ...], text: str) -> dict[str, Any] | None:
        for index, term in enumerate(terms, start=1):
            for node_index in preferred_accessible_text_indices():
                result = run_portable_step(
                    f"{label_prefix}_{index}_{node_index}",
                    portable_command(
                        config,
                        actor,
                        "accessibility-type-text",
                        "--query",
                        term,
                        "--role",
                        "text",
                        "--visible-only",
                        "--state",
                        "showing",
                        "--index",
                        str(node_index),
                        "--text",
                        text,
                        "--clear-first",
                    ),
                    required=False,
                )
                if int(result.get("returncode", 1) or 0) == 0:
                    return result
        return None

    def try_accessible_click(label_prefix: str, terms: tuple[str, ...], *, role: str = "push button") -> dict[str, Any] | None:
        for index, term in enumerate(terms, start=1):
            result = run_portable_step(
                f"{label_prefix}_{index}",
                portable_command(
                    config,
                    actor,
                    "accessibility-click",
                    "--query",
                    term,
                    "--role",
                    role,
                    "--visible-only",
                    "--state",
                    "showing",
                ),
                required=False,
            )
            if int(result.get("returncode", 1) or 0) == 0:
                return result
        return None

    def find_add_contact_button() -> dict[str, Any] | None:
        return portable_find_accessible_match(
            config,
            actor,
            terms=(*DESKTOP_ADD_TO_CONTACTS_CHAT_TERMS, *DESKTOP_ADD_CONTACT_BUTTON_TERMS),
            role="push button",
            visible_only=True,
        )

    def find_exact_username_label(username: str) -> dict[str, Any] | None:
        target_username = username if str(username or "").startswith("@") else f"@{username}"
        for role in ("label", "text"):
            match = portable_find_accessible_match(
                config,
                actor,
                terms=(target_username,),
                role=role,
                visible_only=True,
            )
            if not match:
                continue
            match_name = normalize_space(str(match["match"].get("name") or ""))
            if match_name.casefold() == target_username.casefold():
                return match
        return None

    def click_window_ratio(label: str, *, x_ratio: float, y_ratio: float, required: bool = False) -> dict[str, Any]:
        return run_portable_step(
            label,
            portable_command(
                config,
                actor,
                "window-click",
                "--coordinate-space",
                "window_geometry",
                "--x-ratio",
                str(float(x_ratio)),
                "--y-ratio",
                str(float(y_ratio)),
            ),
            required=required,
        )

    def match_origin_ratio(match: dict[str, Any]) -> dict[str, float] | None:
        try:
            x_ratio = float(match.get("relative_x_ratio"))
            y_ratio = float(match.get("relative_y_ratio"))
        except (TypeError, ValueError):
            return None
        return {
            "x_ratio": round(min(max(x_ratio, 0.0), 1.0), 4),
            "y_ratio": round(min(max(y_ratio, 0.0), 1.0), 4),
        }

    def click_match_origin(label: str, match: dict[str, Any], *, required: bool = False) -> dict[str, Any] | None:
        origin = match_origin_ratio(match)
        if not origin:
            return None
        payload.setdefault("match_origin_clicks", {})[label] = origin
        return click_window_ratio(
            label,
            x_ratio=float(origin["x_ratio"]),
            y_ratio=float(origin["y_ratio"]),
            required=required,
        )

    def click_match_body(label: str, match: dict[str, Any], *, required: bool = False) -> dict[str, Any] | None:
        derived = derive_accessible_click_ratio(match, window_geometry)
        if derived:
            payload.setdefault("derived_clicks", {})[label] = derived
            return click_window_ratio(
                label,
                x_ratio=float(derived["x_ratio"]),
                y_ratio=float(derived["y_ratio"]),
                required=required,
            )
        return click_match_origin(label, match, required=required)

    def open_profile_overlay() -> tuple[str | None, dict[str, Any] | None]:
        menu_click = try_accessible_click("open_chat_menu", DESKTOP_CHAT_MENU_TERMS, role="push button")
        if menu_click is not None:
            time.sleep(0.2)
            show_profile_click = try_accessible_click("show_profile_from_menu", DESKTOP_SHOW_PROFILE_TERMS, role="menu item")
            if show_profile_click is not None:
                time.sleep(0.45)
                add_match = find_add_contact_button()
                if add_match:
                    return "chat_menu_show_profile", add_match

        click_window_ratio(
            "open_profile_header_fallback",
            x_ratio=DESKTOP_PROFILE_HEADER_X_RATIO,
            y_ratio=DESKTOP_PROFILE_HEADER_Y_RATIO,
            required=False,
        )
        time.sleep(0.45)
        add_match = find_add_contact_button()
        if add_match:
            return "chat_header_click_fallback", add_match

        info_click = try_accessible_click("open_chat_info", DESKTOP_CHAT_INFO_TERMS, role="push button")
        if info_click is not None:
            time.sleep(0.35)
            add_match = find_add_contact_button()
            if add_match:
                return "chat_info_button", add_match
        return None, None

    run_portable_step("preflight_log", portable_command(config, actor, "log-diagnose"), required=False)
    run_portable_step(
        "reset_to_main_window",
        portable_command(
            config,
            actor,
            "press-keys",
            "--sequence",
            "Escape",
            "--sequence",
            "Escape",
            "--sequence",
            "Escape",
        ),
        required=False,
    )
    search_result = try_accessible_type("search_contact_accessible", DESKTOP_SEARCH_TERMS, contact["username"])
    if search_result is None:
        raise RuntimeError(f"Could not type username into Telegram Desktop search field for {contact['contact_id']}")
    time.sleep(max(float(args.search_results_wait), 0.0))
    search_result_index = resolve_search_result_index(args, contact)
    search_result_y_ratio = float(args.search_result_y_ratio) + (float(args.search_result_step_y_ratio) * float(search_result_index))
    payload["search_result_target"] = {
        "index": search_result_index,
        "x_ratio": round(float(args.search_result_x_ratio), 4),
        "y_ratio": round(search_result_y_ratio, 4),
        "wait_seconds": float(args.search_results_wait),
    }
    run_portable_step(
        "open_search_result_row",
        portable_command(
            config,
            actor,
            "window-click",
            "--coordinate-space",
            "window_geometry",
            "--x-ratio",
            str(float(args.search_result_x_ratio)),
            "--y-ratio",
            str(search_result_y_ratio),
        ),
    )
    time.sleep(max(float(args.open_wait), 0.0))
    capture_screenshot("profile_before", "desktop_add_contact_profile_before.png")

    window_geometry = portable["windows"][0] if portable["windows"] else {}
    chat_info_match = portable_find_accessible_match(
        config,
        actor,
        terms=DESKTOP_CHAT_INFO_TERMS,
        role="push button",
        visible_only=True,
    )
    chat_menu_match = portable_find_accessible_match(
        config,
        actor,
        terms=DESKTOP_CHAT_MENU_TERMS,
        role="push button",
        visible_only=True,
    )
    add_contact_match = portable_find_accessible_match(
        config,
        actor,
        terms=(*DESKTOP_ADD_TO_CONTACTS_CHAT_TERMS, *DESKTOP_ADD_CONTACT_BUTTON_TERMS),
        role="push button",
        visible_only=True,
    )
    payload["profile_before_accessibility"] = {
        "chat_info_visible": bool(chat_info_match),
        "chat_menu_visible": bool(chat_menu_match),
        "add_button_visible": bool(add_contact_match),
    }
    if chat_info_match:
        payload["steps"].append(
            {
                "label": "probe_chat_info_button",
                "term": chat_info_match["term"],
                "match": chat_info_match["match"],
                "command": chat_info_match["result"]["command"],
            }
        )
    if chat_menu_match:
        payload["steps"].append(
            {
                "label": "probe_chat_menu_button",
                "term": chat_menu_match["term"],
                "match": chat_menu_match["match"],
                "command": chat_menu_match["result"]["command"],
            }
        )
    if add_contact_match:
        payload["steps"].append(
            {
                "label": "probe_add_contact_button",
                "term": add_contact_match["term"],
                "match": add_contact_match["match"],
                "command": add_contact_match["result"]["command"],
            }
        )
        if isinstance(add_contact_match.get("listing"), dict):
            write_debug_json("accessibility_profile_before_add_button.json", add_contact_match["listing"])

    if args.confirm_add:
        profile_open_route, current_add_contact_match = open_profile_overlay()
        payload["profile_open_route"] = profile_open_route or ""
        profile_username_match = find_exact_username_label(contact["username"])
        payload["profile_username_exact_match_visible"] = bool(profile_username_match)
        if profile_username_match:
            payload["steps"].append(
                {
                    "label": "profile_username_exact_match",
                    "term": profile_username_match["term"],
                    "match": profile_username_match["match"],
                    "command": profile_username_match["result"]["command"],
                }
            )
        if current_add_contact_match:
            capture_screenshot("profile_overlay_before_add", "desktop_add_contact_profile_overlay_before_add.png")

        if current_add_contact_match is None:
            payload["status"] = "ui_profile_not_detected_after_chat_open"
        elif not profile_username_match:
            payload["status"] = "ui_opened_profile_username_mismatch"
        else:
            click_match_origin("click_add_to_contacts_match_origin", current_add_contact_match["match"], required=False)
            time.sleep(max(float(args.after_add_wait), 0.0))
            post_add_button = find_add_contact_button()
            post_add_first_name = portable_find_accessible_match(
                config,
                actor,
                terms=DESKTOP_FIRST_NAME_TERMS,
                visible_only=True,
            )
            post_add_done_button = portable_find_accessible_match(
                config,
                actor,
                terms=DESKTOP_DONE_BUTTON_TERMS,
                role="push button",
                visible_only=True,
            )
            if post_add_button and not post_add_first_name and not post_add_done_button:
                click_add_result = try_accessible_click(
                    "click_add_to_contacts_accessible",
                    (*DESKTOP_ADD_TO_CONTACTS_CHAT_TERMS, *DESKTOP_ADD_CONTACT_BUTTON_TERMS),
                    role="push button",
                )
                if click_add_result is None:
                    add_click_x_ratio = float(args.add_click_x_ratio)
                    add_click_y_ratio = float(args.add_click_y_ratio)
                    raw_match_click = match_origin_ratio(current_add_contact_match["match"])
                    if raw_match_click:
                        payload["raw_add_contact_click"] = raw_match_click
                        add_click_x_ratio = float(raw_match_click["x_ratio"])
                        add_click_y_ratio = float(raw_match_click["y_ratio"])
                    else:
                        derived_click = derive_accessible_click_ratio(current_add_contact_match["match"], window_geometry)
                        if derived_click:
                            payload["derived_add_contact_click"] = derived_click
                            add_click_x_ratio = float(derived_click["x_ratio"])
                            add_click_y_ratio = float(derived_click["y_ratio"])
                    click_window_ratio(
                        "click_add_to_contacts_fallback",
                        x_ratio=add_click_x_ratio,
                        y_ratio=add_click_y_ratio,
                        required=False,
                    )
                add_click_x_ratio = float(args.add_click_x_ratio)
                add_click_y_ratio = float(args.add_click_y_ratio)
                time.sleep(max(float(args.after_add_wait), 0.0))
                post_add_button = find_add_contact_button()
                post_add_first_name = portable_find_accessible_match(
                    config,
                    actor,
                    terms=DESKTOP_FIRST_NAME_TERMS,
                    visible_only=True,
                )
                post_add_done_button = portable_find_accessible_match(
                    config,
                    actor,
                    terms=DESKTOP_DONE_BUTTON_TERMS,
                    role="push button",
                    visible_only=True,
                )
            payload["post_add_button_still_visible"] = bool(post_add_button)
            dialog_detected = bool(post_add_first_name or post_add_done_button)
            payload["post_add_dialog_detected"] = dialog_detected
            if post_add_button and not dialog_detected:
                retry_click = match_origin_ratio(post_add_button["match"])
                if retry_click:
                    payload["retry_add_contact_click"] = retry_click
                    click_window_ratio(
                        "retry_add_to_contacts_match_origin",
                        x_ratio=float(retry_click["x_ratio"]),
                        y_ratio=float(retry_click["y_ratio"]),
                        required=False,
                    )
                    time.sleep(max(float(args.after_add_wait), 0.0))
                    post_add_button = find_add_contact_button()
                    payload["post_add_button_still_visible"] = bool(post_add_button)
                    post_add_first_name = portable_find_accessible_match(
                        config,
                        actor,
                        terms=DESKTOP_FIRST_NAME_TERMS,
                        visible_only=True,
                    )
                    post_add_done_button = portable_find_accessible_match(
                        config,
                        actor,
                        terms=DESKTOP_DONE_BUTTON_TERMS,
                        role="push button",
                        visible_only=True,
                    )
                    dialog_detected = bool(post_add_first_name or post_add_done_button)
                    payload["post_add_dialog_detected"] = dialog_detected
            if post_add_button and not dialog_detected:
                payload["steps"].append(
                    {
                        "label": "post_click_add_button_still_visible",
                        "term": post_add_button["term"],
                        "match": post_add_button["match"],
                        "command": post_add_button["result"]["command"],
                    }
                )
                if isinstance(post_add_button.get("listing"), dict):
                    write_debug_json("accessibility_post_click_add_button.json", post_add_button["listing"])
                payload["status"] = "ui_add_button_still_visible_after_click"
            elif not dialog_detected:
                payload["status"] = "ui_add_dialog_not_detected_after_click"
            else:
                resolved_first_name_text, resolved_last_name_text = resolve_contact_name_parts(args, contact)
                payload["resolved_contact_name_parts"] = {
                    "first_name_text": resolved_first_name_text,
                    "last_name_text": resolved_last_name_text,
                }
                first_name_result = None
                last_name_result = None
                if resolved_first_name_text:
                    first_name_result = try_accessible_type("type_first_name_accessible", DESKTOP_FIRST_NAME_TERMS, resolved_first_name_text)
                    if first_name_result is None:
                        run_portable_step(
                            "type_first_name_fallback",
                            portable_command(config, actor, "type-text", "--text", resolved_first_name_text),
                            required=False,
                        )
                    time.sleep(0.2)

                if resolved_last_name_text:
                    last_name_result = try_accessible_type("type_last_name_accessible", DESKTOP_LAST_NAME_TERMS, resolved_last_name_text)
                    if last_name_result is None:
                        run_portable_step(
                            "type_last_name_fallback",
                            portable_command(config, actor, "type-text", "--text", resolved_last_name_text),
                            required=False,
                        )
                    time.sleep(0.15)

                dialog_submit_ratio = (
                    derive_dialog_submit_ratio(last_name_result, window_geometry)
                    or derive_dialog_submit_ratio(first_name_result, window_geometry)
                    or derive_dialog_submit_ratio(post_add_first_name, window_geometry)
                )
                if dialog_submit_ratio:
                    payload["dialog_submit_click"] = dialog_submit_ratio
                    click_window_ratio(
                        "click_done_dialog_submit",
                        x_ratio=float(dialog_submit_ratio["x_ratio"]),
                        y_ratio=float(dialog_submit_ratio["y_ratio"]),
                        required=False,
                    )
                    time.sleep(0.25)
                    done_result = {"status": "dialog_submit_clicked"}
                elif post_add_done_button:
                    click_match_body("click_done_match_origin", post_add_done_button["match"], required=False)
                    time.sleep(0.25)
                    done_result = {"status": "match_origin_clicked"}
                else:
                    done_result = try_accessible_click("click_done_accessible", DESKTOP_DONE_BUTTON_TERMS)
                if done_result is None:
                    done_repeat = max(int(args.done_click_repeat), 1)
                    for index in range(done_repeat):
                        click_window_ratio(
                            f"click_done_{index + 1}",
                            x_ratio=float(args.done_click_x_ratio),
                            y_ratio=float(args.done_click_y_ratio),
                            required=False,
                        )
                        time.sleep(0.12)
                time.sleep(max(float(args.after_done_wait), 0.0))
                payload["status"] = "contact_submit_clicked"
    else:
        payload["status"] = "search_chat_opened_manual_review"

    capture_screenshot("profile_after_actions", "desktop_add_contact_profile_after_actions.png")

    if bool(args.verify_profile_reopen):
        run_portable_step(
            "reset_to_main_window_for_verify",
            portable_command(
                config,
                actor,
                "press-keys",
                "--sequence",
                "Escape",
                "--sequence",
                "Escape",
                "--sequence",
                "Escape",
            ),
            required=False,
        )
        verify_search = try_accessible_type("verify_search_contact_accessible", DESKTOP_SEARCH_TERMS, contact["username"])
        if verify_search is None:
            raise RuntimeError(f"Could not type username into Telegram Desktop search during verify for {contact['contact_id']}")
        time.sleep(max(float(args.search_results_wait), 0.0))
        run_portable_step(
            "verify_open_search_result_row",
            portable_command(
                config,
                actor,
                "window-click",
                "--coordinate-space",
                "window_geometry",
                "--x-ratio",
                str(float(args.search_result_x_ratio)),
                "--y-ratio",
                str(search_result_y_ratio),
            ),
        )
        time.sleep(max(float(args.verify_wait), 0.0))
        verify_profile_route, _ = open_profile_overlay()
        payload["verify_profile_open_route"] = verify_profile_route or ""
        verify_username_match = find_exact_username_label(contact["username"])
        capture_screenshot("profile_verify", "desktop_add_contact_profile_verify.png")
        verify_add_button = portable_find_accessible_match(
            config,
            actor,
            terms=(*DESKTOP_ADD_TO_CONTACTS_CHAT_TERMS, *DESKTOP_ADD_CONTACT_BUTTON_TERMS),
            role="push button",
            visible_only=True,
        )
        verify_edit_button = portable_find_accessible_match(
            config,
            actor,
            terms=DESKTOP_CONTACT_EDIT_TERMS,
            role="push button",
            visible_only=True,
        )
        verify_delete_button = portable_find_accessible_match(
            config,
            actor,
            terms=DESKTOP_CONTACT_DELETE_TERMS,
            role="push button",
            visible_only=True,
        )
        payload["verify_profile_state"] = {
            "username_visible": bool(verify_username_match or verify_add_button or verify_edit_button or verify_delete_button),
            "exact_username_visible": bool(verify_username_match),
            "add_button_visible": bool(verify_add_button),
            "edit_button_visible": bool(verify_edit_button),
            "delete_button_visible": bool(verify_delete_button),
        }
        payload["verify_profile_state"]["status"] = summarize_contact_verify_state(
            username_visible=payload["verify_profile_state"]["username_visible"],
            add_button_visible=payload["verify_profile_state"]["add_button_visible"],
            edit_button_visible=payload["verify_profile_state"]["edit_button_visible"],
            delete_button_visible=payload["verify_profile_state"]["delete_button_visible"],
        )
        if not verify_username_match and payload["verify_profile_state"]["status"] != "ui_verify_profile_not_detected":
            payload["verify_profile_state"]["status"] = "ui_verify_username_mismatch"
        if verify_add_button:
            payload["steps"].append(
                {
                    "label": "verify_add_contact_button",
                    "term": verify_add_button["term"],
                    "match": verify_add_button["match"],
                    "command": verify_add_button["result"]["command"],
                }
            )
        if verify_edit_button:
            payload["steps"].append(
                {
                    "label": "verify_edit_contact_button",
                    "term": verify_edit_button["term"],
                    "match": verify_edit_button["match"],
                    "command": verify_edit_button["result"]["command"],
                }
            )
        if verify_delete_button:
            payload["steps"].append(
                {
                    "label": "verify_delete_contact_button",
                    "term": verify_delete_button["term"],
                    "match": verify_delete_button["match"],
                    "command": verify_delete_button["result"]["command"],
                }
            )
        if verify_username_match:
            payload["steps"].append(
                {
                    "label": "verify_profile_username_exact_match",
                    "term": verify_username_match["term"],
                    "match": verify_username_match["match"],
                    "command": verify_username_match["result"]["command"],
                }
            )
        if payload["verify_profile_state"]["status"] != "ui_verify_profile_not_detected":
            payload["status"] = payload["verify_profile_state"]["status"]

    append_state_history(
        state,
        {
            "run_id": run_id,
            "action": "prepare_add_contact_profile",
            "actor_id": actor["actor_id"],
            "contact_id": contact["contact_id"],
            "status": payload["status"],
            "executed_at": now_utc(),
        },
        preserve_history_limit=int(config["safety"]["history_limit"]),
    )
    atomic_write_json(state_path, state)
    payload["portable"] = portable
    payload["summary"] = summarize_state(config, state, state_path=state_path)
    run_dir = write_run_artifacts(state_path, payload)
    payload["run_dir"] = str(run_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe Telegram sandbox activity runner for allowlisted internal chats only.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_arguments(target: argparse.ArgumentParser) -> None:
        target.add_argument("--config", required=True, help="Path to tool config JSON")
        target.add_argument(
            "--state-file",
            default=str(DEFAULT_STATE_PATH),
            help=f"Path to tool state JSON (default: {DEFAULT_STATE_PATH})",
        )

    init_parser = subparsers.add_parser("init", help="Create a fresh state file")
    add_common_arguments(init_parser)
    init_parser.set_defaults(func=command_init)

    status_parser = subparsers.add_parser("status", help="Show current counters and last activity")
    add_common_arguments(status_parser)
    status_parser.set_defaults(func=command_status)

    import_contacts_parser = subparsers.add_parser(
        "import-contacts",
        help="Import approved @username values into allowlist_contacts in the local config.",
    )
    add_common_arguments(import_contacts_parser)
    import_contacts_parser.add_argument(
        "--usernames-file",
        help="Optional path to a text file with one or more usernames per line. Without it, stdin is used.",
    )
    import_contacts_parser.set_defaults(func=command_import_contacts)

    api_status_parser = subparsers.add_parser(
        "api-status",
        help="Probe the optional Telegram API sidecar for a specific actor/session.",
    )
    add_common_arguments(api_status_parser)
    api_status_parser.add_argument("--actor-id", required=True, help="Which actor/session should be checked")
    api_status_parser.set_defaults(func=command_api_status)

    api_import_tdata_parser = subparsers.add_parser(
        "api-import-tdata-session",
        help="Create or refresh the actor API session from Telegram Desktop portable tdata.",
    )
    add_common_arguments(api_import_tdata_parser)
    api_import_tdata_parser.add_argument("--actor-id", required=True, help="Which actor/session should be bootstrapped")
    api_import_tdata_parser.add_argument(
        "--tdata-dir",
        default="",
        help="Optional explicit path to Telegram Desktop tdata. Otherwise it is inferred from portable_profile_dir.",
    )
    api_import_tdata_parser.add_argument(
        "--desktop-passcode",
        default="",
        help="Optional Telegram Desktop local passcode if the tdata folder is encrypted.",
    )
    api_import_tdata_parser.set_defaults(func=command_api_import_tdata_session)

    api_scan_parser = subparsers.add_parser(
        "api-scan-contacts",
        help="Resolve allowlisted contact_id values through Telegram API and classify which usernames are still live users.",
    )
    add_common_arguments(api_scan_parser)
    api_scan_parser.add_argument("--actor-id", required=True, help="Which actor/session should be used for API resolve checks")
    api_scan_parser.add_argument("--contact-id", action="append", help="Allowlisted contact_id to scan. Can be repeated.")
    api_scan_parser.add_argument("--contact-id-file", help="Optional text file with one contact_id per line.")
    api_scan_parser.add_argument("--limit", type=int, help="Optional cap on how many contacts to scan.")
    api_scan_parser.add_argument(
        "--write-valid-contact-id-file",
        default="",
        help="Optional output file where only valid resolved user contact_id values will be written.",
    )
    api_scan_parser.set_defaults(func=command_api_scan_contacts)

    plan_parser = subparsers.add_parser("plan", help="Build a dry execution plan without touching Telegram")
    add_common_arguments(plan_parser)
    plan_parser.add_argument("--iterations", type=int, help="How many steps to plan")
    plan_parser.add_argument("--actor-id", help="Restrict planning to a single actor")
    plan_parser.add_argument("--seed", type=int, help="Optional random seed for reproducible plans")
    plan_parser.set_defaults(func=command_plan)

    batch_add_parser = subparsers.add_parser(
        "batch-add-contacts",
        help="Batch Add to contacts for allowlisted contact_id values with random pauses and optional API-first execution.",
    )
    add_common_arguments(batch_add_parser)
    batch_add_parser.add_argument("--actor-id", required=True, help="Which actor/profile should add the contacts")
    batch_add_parser.add_argument("--contact-id", action="append", help="Allowlisted contact_id to add. Can be repeated.")
    batch_add_parser.add_argument("--contact-id-file", help="Optional text file with one contact_id per line.")
    batch_add_parser.add_argument("--limit", type=int, help="Optional cap on how many contacts to process.")
    batch_add_parser.add_argument("--backend", choices=sorted(ALLOWED_API_SIDECAR_MODES), help="portable_only, api_first or api_only")
    batch_add_parser.add_argument("--seed", type=int, help="Optional random seed for reproducible pause selection")
    batch_add_parser.add_argument("--execute", action="store_true", help="Actually perform Add to contacts. Without it the command stays in dry-run.")
    batch_add_parser.add_argument("--fail-fast", action="store_true", help="Stop the batch on the first failed contact")
    batch_add_parser.add_argument("--min-random-pause", type=float, default=2.0, help="Minimum pause between contacts in seconds")
    batch_add_parser.add_argument("--max-random-pause", type=float, default=6.0, help="Maximum pause between contacts in seconds")
    batch_add_parser.add_argument(
        "--verify-profile-reopen",
        action="store_true",
        default=True,
        help="For portable fallback, reopen the profile and capture a verification screenshot after each contact",
    )
    batch_add_parser.add_argument("--open-wait", type=float, default=2.0, help="Seconds to wait after opening the profile")
    batch_add_parser.add_argument("--search-results-wait", type=float, default=2.5, help="Seconds to wait for Telegram Desktop search results before clicking a row")
    batch_add_parser.add_argument("--search-result-index", type=int, help="Optional zero-based result row override for every contact in this batch")
    batch_add_parser.add_argument("--search-result-x-ratio", type=float, default=DESKTOP_SEARCH_RESULT_X_RATIO)
    batch_add_parser.add_argument("--search-result-y-ratio", type=float, default=DESKTOP_SEARCH_RESULT_Y_RATIO)
    batch_add_parser.add_argument("--search-result-step-y-ratio", type=float, default=DESKTOP_SEARCH_RESULT_STEP_Y_RATIO)
    batch_add_parser.add_argument("--after-add-wait", type=float, default=0.9, help="Seconds to wait after clicking Add to contacts")
    batch_add_parser.add_argument("--after-done-wait", type=float, default=0.9, help="Seconds to wait after the Done clicks")
    batch_add_parser.add_argument("--verify-wait", type=float, default=1.0, help="Seconds to wait before the verification screenshot")
    batch_add_parser.add_argument("--first-name-text", default="", help="Optional first name override for the Add Contact form")
    batch_add_parser.add_argument("--last-name-text", default="", help="Optional last name text to type before clicking Done")
    batch_add_parser.add_argument("--add-click-x-ratio", type=float, default=DESKTOP_ADD_CONTACT_X_RATIO)
    batch_add_parser.add_argument("--add-click-y-ratio", type=float, default=DESKTOP_ADD_CONTACT_Y_RATIO)
    batch_add_parser.add_argument("--done-click-x-ratio", type=float, default=DESKTOP_DONE_CONTACT_X_RATIO)
    batch_add_parser.add_argument("--done-click-y-ratio", type=float, default=DESKTOP_DONE_CONTACT_Y_RATIO)
    batch_add_parser.add_argument("--done-click-repeat", type=int, default=2, help="How many times to click Done in portable fallback mode")
    batch_add_parser.set_defaults(func=command_batch_add_contacts)

    run_parser = subparsers.add_parser("run", help="Run a planned batch. Dry-run unless --execute is passed.")
    add_common_arguments(run_parser)
    run_parser.add_argument("--iterations", type=int, help="How many steps to plan and run")
    run_parser.add_argument("--actor-id", help="Restrict planning to a single actor")
    run_parser.add_argument("--seed", type=int, help="Optional random seed for reproducible plans")
    run_parser.add_argument("--execute", action="store_true", help="Actually send SiteControlKit commands")
    run_parser.add_argument("--respect-delays", action="store_true", help="Sleep between steps using planned delay_seconds")
    run_parser.add_argument("--fail-fast", action="store_true", help="Stop the batch on first failed step")
    run_parser.set_defaults(func=command_run)

    invite_parser = subparsers.add_parser(
        "prepare-invite",
        help="Operator-assisted invite flow for allowlisted contacts only. Stops before final Telegram confirmation unless --confirm-final is passed.",
    )
    add_common_arguments(invite_parser)
    invite_parser.add_argument("--actor-id", required=True, help="Which allowlisted actor/client should perform the invite")
    invite_parser.add_argument("--chat-id", required=True, help="Which allowlisted internal chat to invite into")
    invite_parser.add_argument("--contact-id", required=True, help="Which allowlisted contact to prepare in Add Members")
    invite_parser.add_argument("--execute", action="store_true", help="Actually drive SiteControlKit instead of printing the plan")
    invite_parser.add_argument("--search-wait", type=float, default=1.5, help="Seconds to wait after filling Add Members search")
    invite_parser.add_argument("--allow-first-result", action="store_true", help="Allow selecting the first visible search result when multiple candidates are returned")
    invite_parser.add_argument("--confirm-final", action="store_true", help="Also click the final Telegram Add button instead of stopping at manual confirmation")
    invite_parser.set_defaults(func=command_prepare_invite)

    join_parser = subparsers.add_parser(
        "prepare-join",
        help="Open an allowlisted chat and optionally click Join. Default mode only reaches the manual confirmation point.",
    )
    add_common_arguments(join_parser)
    join_parser.add_argument("--actor-id", required=True, help="Which allowlisted actor/client should open the chat")
    join_parser.add_argument("--chat-id", required=True, help="Which allowlisted chat to open or join")
    join_parser.add_argument("--execute", action="store_true", help="Actually drive SiteControlKit instead of printing the plan")
    join_parser.add_argument("--confirm-join", action="store_true", help="Click the Join button automatically if it is visible")
    join_parser.set_defaults(func=command_prepare_join)

    add_contact_parser = subparsers.add_parser(
        "prepare-add-contact-profile",
        help="Operator-assisted Add to contacts flow for an allowlisted username via Telegram Desktop portable profile.",
    )
    add_common_arguments(add_contact_parser)
    add_contact_parser.add_argument("--actor-id", required=True, help="Which actor/profile should add the contact")
    add_contact_parser.add_argument("--contact-id", required=True, help="Which allowlisted contact to open by username")
    add_contact_parser.add_argument("--execute", action="store_true", help="Actually drive the portable Telegram profile")
    add_contact_parser.add_argument("--launch-if-needed", action="store_true", help="Launch the portable profile if it is not running")
    add_contact_parser.add_argument("--confirm-add", action="store_true", help="Perform the Add to contacts -> Done click path")
    add_contact_parser.add_argument("--search-results-wait", type=float, default=2.5, help="Seconds to wait for Telegram Desktop search results before clicking a row")
    add_contact_parser.add_argument("--search-result-index", type=int, help="Optional zero-based result row override when the exact username is not the first match")
    add_contact_parser.add_argument("--search-result-x-ratio", type=float, default=DESKTOP_SEARCH_RESULT_X_RATIO)
    add_contact_parser.add_argument("--search-result-y-ratio", type=float, default=DESKTOP_SEARCH_RESULT_Y_RATIO)
    add_contact_parser.add_argument("--search-result-step-y-ratio", type=float, default=DESKTOP_SEARCH_RESULT_STEP_Y_RATIO)
    add_contact_parser.add_argument("--open-wait", type=float, default=2.0, help="Seconds to wait after opening the profile")
    add_contact_parser.add_argument("--after-add-wait", type=float, default=0.9, help="Seconds to wait after the Add to contacts click")
    add_contact_parser.add_argument("--after-done-wait", type=float, default=0.9, help="Seconds to wait after the Done clicks")
    add_contact_parser.add_argument("--verify-profile-reopen", action="store_true", help="Reopen profile and capture one more screenshot after the action")
    add_contact_parser.add_argument("--verify-wait", type=float, default=1.0, help="Seconds to wait before the verification screenshot")
    add_contact_parser.add_argument("--first-name-text", default="", help="Optional first name override for the Add Contact form")
    add_contact_parser.add_argument("--last-name-text", default="", help="Optional text to type before clicking Done")
    add_contact_parser.add_argument("--add-click-x-ratio", type=float, default=DESKTOP_ADD_CONTACT_X_RATIO)
    add_contact_parser.add_argument("--add-click-y-ratio", type=float, default=DESKTOP_ADD_CONTACT_Y_RATIO)
    add_contact_parser.add_argument("--done-click-x-ratio", type=float, default=DESKTOP_DONE_CONTACT_X_RATIO)
    add_contact_parser.add_argument("--done-click-y-ratio", type=float, default=DESKTOP_DONE_CONTACT_Y_RATIO)
    add_contact_parser.add_argument("--done-click-repeat", type=int, default=2, help="How many times to click Done")
    add_contact_parser.set_defaults(func=command_prepare_add_contact_profile)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ConfigError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    except requests.HTTPError as exc:
        message = exc.response.text if exc.response is not None else str(exc)
        print(json.dumps({"ok": False, "error": normalize_space(message)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 3
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
