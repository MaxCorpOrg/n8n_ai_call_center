#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
import uuid
from typing import Any

import requests

REPO_ROOT = pathlib.Path('/home/max/n8n_ai_call_center')
SECRETS_ENV = REPO_ROOT / 'agent_contact_parser_docs' / '.secrets' / 'cosmetologist_hunter.env'
N8N_ENV_FILE = pathlib.Path('/home/max/.config/lipolong-eleven-relay.env')
N8N_BASE_URL = 'https://www.n-8-n.site'
WORKFLOW_NAME = 'COSMETOLOGIST_HUNTER_TELEGRAM_LIVE'
WEBHOOK_PATH = 'cosmetologist-hunter-telegram'
PROMPT_PATH = REPO_ROOT / 'prompts' / 'cosmetologist_hunter' / 'telegram_controller_system_prompt_ru.md'
RUNTIME_DIR = REPO_ROOT / '.runtime' / 'cosmetologist_hunter'
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
COMPILED_WORKFLOW_PATH = RUNTIME_DIR / 'COSMETOLOGIST_HUNTER_TELEGRAM_LIVE.compiled.json'


def load_env(path: pathlib.Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        data[key.strip()] = value.strip()
    return data


def load_n8n_api_key() -> str:
    text = N8N_ENV_FILE.read_text(encoding='utf-8')
    match = re.search(r'^N8N_API_KEY=(.+)$', text, re.MULTILINE)
    if not match:
        raise RuntimeError(f'Could not find N8N_API_KEY in {N8N_ENV_FILE}')
    return match.group(1).strip()


def api_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({'X-N8N-API-KEY': load_n8n_api_key(), 'Content-Type': 'application/json'})
    return session


def node(name: str, type_: str, parameters: dict[str, Any], position: list[int], *, type_version: float | int = 2, webhook_id: str | None = None) -> dict[str, Any]:
    out = {
        'id': str(uuid.uuid4()),
        'name': name,
        'type': type_,
        'typeVersion': type_version,
        'position': position,
        'parameters': parameters,
    }
    if webhook_id:
        out['webhookId'] = webhook_id
    return out


def switch_condition_equals(left_expr: str, right_value: str) -> dict[str, Any]:
    return {
        'conditions': {
            'options': {'caseSensitive': True, 'leftValue': '', 'typeValidation': 'strict', 'version': 2},
            'conditions': [
                {
                    'leftValue': left_expr,
                    'rightValue': right_value,
                    'operator': {'type': 'string', 'operation': 'equals'},
                }
            ],
            'combinator': 'and',
        },
        'renameOutput': True,
        'outputKey': right_value,
    }


def switch_condition_bool(left_expr: str, value: bool, output_key: str) -> dict[str, Any]:
    inner = left_expr
    if left_expr.startswith('={{') and left_expr.endswith('}}'):
        inner = left_expr[3:-2].strip()
    rendered_left = '={{ String(' + inner + ') }}'
    return {
        'conditions': {
            'options': {'caseSensitive': True, 'leftValue': '', 'typeValidation': 'strict', 'version': 2},
            'conditions': [
                {
                    'leftValue': rendered_left,
                    'rightValue': str(value).lower(),
                    'operator': {'type': 'string', 'operation': 'equals'},
                }
            ],
            'combinator': 'and',
        },
        'renameOutput': True,
        'outputKey': output_key,
    }


def build_workflow(cfg: dict[str, str]) -> dict[str, Any]:
    prompt = PROMPT_PATH.read_text(encoding='utf-8').strip()

    normalize_js = f"""
const update = $json.body ?? $json;
const headers = update.headers ?? $json.headers ?? {{}};
const message = update.message ?? update.edited_message ?? {{}};
const text = String(message.text ?? '').trim();
const chatId = String(message.chat?.id ?? '');
const secret = String(headers['x-telegram-bot-api-secret-token'] ?? headers['X-Telegram-Bot-Api-Secret-Token'] ?? '');
return [{{
  update,
  chat_id: chatId,
  text,
  is_text: !!text,
  has_voice: !!message.voice?.file_id,
  authorized: secret === {json.dumps(cfg['TELEGRAM_WEBHOOK_SECRET'])},
  telegram_send_url: {json.dumps(f"https://api.telegram.org/bot{cfg['TELEGRAM_BOT_TOKEN']}/sendMessage")},
  service_auth_token: {json.dumps(cfg['COSMETOLOGIST_HUNTER_AUTH_TOKEN'])},
  settings_get_url: {json.dumps(cfg['COSMETOLOGIST_HUNTER_LIVE_URL'].rstrip('/') + '/settings/get')} + '?chat_id=' + encodeURIComponent(chatId),
  settings_set_url: {json.dumps(cfg['COSMETOLOGIST_HUNTER_LIVE_URL'].rstrip('/') + '/settings/set')},
  run_url: {json.dumps(cfg['COSMETOLOGIST_HUNTER_LIVE_URL'].rstrip('/') + '/run')},
  mistral_api_url: 'https://api.mistral.ai/v1/chat/completions',
  mistral_api_key: {json.dumps(cfg['MISTRAL_API_KEY'])},
  mistral_model: 'mistral-medium-latest',
  controller_system_prompt: {json.dumps(prompt)},
}}];
""".strip()

    classify_command_js = r"""
const text = String($json.text || '').trim();
let command_kind = 'freeform';
if (/^\/(start|help)\b/i.test(text)) command_kind = 'help';
else if (/^\/settings\b/i.test(text)) command_kind = 'settings';
else if (/^\/city\s+.+/i.test(text)) command_kind = 'city';
else if (/^\/count\s+\d{1,3}/i.test(text)) command_kind = 'count';
return [{ ...$json, command_kind }];
""".strip()

    parse_city_js = r"""
const text = String($json.text || '').trim();
const match = text.match(/^\/city\s+(.+)$/i);
const city = match ? match[1].trim() : '';
return [{
  ...$json,
  action: city ? 'set_settings' : 'help',
  settings_set_body: { chat_id: $json.chat_id, city },
}];
""".strip()

    parse_count_js = r"""
const text = String($json.text || '').trim();
const match = text.match(/^\/count\s+(\d{1,3})$/i);
const raw = match ? Number(match[1]) : null;
const count = Number.isFinite(raw) ? Math.min(Math.max(Math.trunc(raw), 1), 300) : null;
return [{
  ...$json,
  action: count ? 'set_settings' : 'help',
  settings_set_body: { chat_id: $json.chat_id, count },
}];
""".strip()

    mistral_json_body = r'''={{ ({
  model: $json.mistral_model,
  messages: [
    { role: 'system', content: $json.controller_system_prompt },
    { role: 'user', content: $json.text },
  ],
  temperature: 0.1,
  max_tokens: 400,
  response_format: { type: 'json_object' },
}) }}'''

    parse_ai_js = r"""
const raw = String($json.body?.choices?.[0]?.message?.content ?? '').trim();
const base = $('Telegram | Normalize Update').item.json || {};
const clampCount = (value) => {
  const n = Number(value);
  if (!Number.isFinite(n)) return null;
  return Math.min(Math.max(Math.trunc(n), 1), 300);
};
const tryParse = (value) => {
  if (!value) return null;
  try { return JSON.parse(value); } catch (e) { return null; }
};
let parsed = tryParse(raw);
if (!parsed) {
  const match = raw.match(/\{[\s\S]*\}/);
  if (match) parsed = tryParse(match[0]);
}
parsed = parsed && typeof parsed === 'object' ? parsed : {};
let action = String(parsed.action || '').trim();
if (!action) {
  const text = String(base.text || '').toLowerCase();
  if (text.includes('настройк')) action = 'get_settings';
  else if (/(город|лимит|количеств)/.test(text)) action = 'set_settings';
  else if (/(найди|ищи|собери|контакт)/.test(text)) action = 'run_search';
  else action = 'help';
}
const city = String(parsed.city || '').trim();
const count = clampCount(parsed.count);
const settingsSetBody = { chat_id: base.chat_id };
const runBody = { chat_id: base.chat_id };
if (city) {
  settingsSetBody.city = city;
  runBody.city = city;
}
if (count !== null) {
  settingsSetBody.count = count;
  runBody.count = count;
}
return [{
  ...base,
  raw_ai_output: raw,
  action,
  city,
  count,
  reply_hint: String(parsed.reply_hint || '').trim(),
  settings_set_body: settingsSetBody,
  run_body: runBody,
}];
""".strip()

    build_help_reply_js = r"""
return [{
  chat_id: $json.chat_id,
  reply_text: [
    'Агент-сборщик косметологов готов.',
    '',
    'Команды:',
    '/settings',
    '/city <город>',
    '/count <число>',
    '',
    'Примеры:',
    'найди 30 косметологов в Казани',
    'собери ещё 45 новых косметологов в Москве',
  ].join('\n'),
  telegram_send_url: $json.telegram_send_url,
}];
""".strip()

    build_unsupported_reply_js = r"""
return [{
  chat_id: $json.chat_id,
  reply_text: 'Сейчас поддерживаются только текстовые сообщения. Напишите город и количество контактов текстом.',
  telegram_send_url: $json.telegram_send_url,
}];
""".strip()

    build_settings_reply_js = r"""
const data = $json.body ?? $json;
const input = $('Telegram | Normalize Update').item.json || {};
const settings = data.settings ?? {};
return [{
  chat_id: input.chat_id,
  telegram_send_url: input.telegram_send_url,
  reply_text: [
    'Текущие настройки агента:',
    `Город: ${settings.city || 'Москва'}`,
    `Лимит: ${settings.count || 45}`,
    '',
    'Можно написать:',
    'найди 45 косметологов в Москве',
  ].join('\n'),
}];
""".strip()

    build_saved_reply_js = r"""
const data = $json.body ?? $json;
const source = $('Switch | Save Source').item.json || $('Telegram | Normalize Update').item.json || {};
const settings = data.settings ?? {};
const ok = data.ok !== false;
return [{
  chat_id: source.chat_id,
  telegram_send_url: source.telegram_send_url,
  reply_text: ok
    ? [
        'Настройки сохранены.',
        `Город: ${settings.city || 'Москва'}`,
        `Лимит: ${settings.count || 45}`,
      ].join('\n')
    : `Не удалось сохранить настройки.\nОшибка: ${data.error || 'неизвестно'}`,
}];
""".strip()

    build_started_reply_js = r"""
return [{
  chat_id: $json.chat_id,
  telegram_send_url: $json.telegram_send_url,
  reply_text: 'Запускаю поиск контактов. Это может занять 30-90 секунд.',
}];
""".strip()

    build_search_reply_js = r"""
const data = $json.body ?? $json;
const source = $('Switch | Run Source').item.json || $('Telegram | Normalize Update').item.json || {};
const contactsCount = Number(data.contacts_count ?? (Array.isArray(data.contacts) ? data.contacts.length : 0));
let replyText = '';
if (data.ok) {
  replyText = [
    'Поиск завершён.',
    data.title ? `Таблица: ${data.title}` : '',
    contactsCount ? `Контактов: ${contactsCount}` : '',
    data.google_url ? `Google Sheets: ${data.google_url}` : '',
    data.local_file ? `Локальный файл: ${data.local_file}` : '',
  ].filter(Boolean).join('\n');
} else {
  replyText = `Поиск не завершился.\nОшибка: ${data.error || 'неизвестно'}`;
}
return [{
  chat_id: source.chat_id,
  telegram_send_url: source.telegram_send_url,
  reply_text: replyText,
}];
""".strip()

    send_message_json = r'''={{ ({
  chat_id: $json.chat_id,
  text: $json.reply_text
}) }}'''

    nodes = [
        node('Telegram | Webhook', 'n8n-nodes-base.webhook', {'httpMethod': 'POST', 'path': WEBHOOK_PATH, 'responseMode': 'responseNode', 'options': {}}, [-1040, 120], type_version=2, webhook_id=str(uuid.uuid4())),
        node('Telegram | Normalize Update', 'n8n-nodes-base.code', {'jsCode': normalize_js}, [-800, 120], type_version=2),
        node('Webhook | ACK', 'n8n-nodes-base.respondToWebhook', {'respondWith': 'json', 'responseBody': '={{ ({ ok: true }) }}', 'options': {}}, [-560, -80], type_version=1.1),
        node('Switch | Authorized', 'n8n-nodes-base.switch', {'rules': {'values': [switch_condition_bool('={{ $json.authorized }}', True, 'authorized')]}, 'options': {'fallbackOutput': 'extra'}}, [-560, 200], type_version=3.2),
        node('Switch | Input Kind', 'n8n-nodes-base.switch', {'rules': {'values': [switch_condition_bool('={{ $json.is_text }}', True, 'text')]}, 'options': {'fallbackOutput': 'extra'}}, [-320, 200], type_version=3.2),
        node('Telegram | Build Unsupported Reply', 'n8n-nodes-base.code', {'jsCode': build_unsupported_reply_js}, [-80, 360], type_version=2),
        node('Command | Classify', 'n8n-nodes-base.code', {'jsCode': classify_command_js}, [-80, 120], type_version=2),
        node('Switch | Quick Command', 'n8n-nodes-base.switch', {'rules': {'values': [switch_condition_equals('={{ $json.command_kind }}', 'help'), switch_condition_equals('={{ $json.command_kind }}', 'settings'), switch_condition_equals('={{ $json.command_kind }}', 'city'), switch_condition_equals('={{ $json.command_kind }}', 'count')]}, 'options': {'fallbackOutput': 'extra'}}, [160, 120], type_version=3.2),
        node('Telegram | Build Help Reply', 'n8n-nodes-base.code', {'jsCode': build_help_reply_js}, [420, -80], type_version=2),
        node('Command | Parse City', 'n8n-nodes-base.code', {'jsCode': parse_city_js}, [420, 120], type_version=2),
        node('Command | Parse Count', 'n8n-nodes-base.code', {'jsCode': parse_count_js}, [420, 280], type_version=2),
        node('AI | Request Mistral', 'n8n-nodes-base.httpRequest', {
            'method': 'POST',
            'url': '={{ $json.mistral_api_url }}',
            'sendHeaders': True,
            'headerParameters': {'parameters': [{'name': 'Authorization', 'value': "={{ 'Bearer ' + $json.mistral_api_key }}"}, {'name': 'Content-Type', 'value': 'application/json'}]},
            'sendBody': True,
            'specifyBody': 'json',
            'jsonBody': mistral_json_body,
            'options': {'response': {'response': {'neverError': True}}},
        }, [420, 520], type_version=4.2),
        node('AI | Parse Decision', 'n8n-nodes-base.code', {'jsCode': parse_ai_js}, [680, 520], type_version=2),
        node('Switch | AI Action', 'n8n-nodes-base.switch', {'rules': {'values': [switch_condition_equals('={{ $json.action }}', 'help'), switch_condition_equals('={{ $json.action }}', 'get_settings'), switch_condition_equals('={{ $json.action }}', 'set_settings'), switch_condition_equals('={{ $json.action }}', 'run_search')]}, 'options': {'fallbackOutput': 'extra'}}, [940, 520], type_version=3.2),
        node('Switch | Save Source', 'n8n-nodes-base.switch', {'rules': {'values': [switch_condition_equals('={{ $json.action || $json.command_kind || "" }}', 'set_settings')]}, 'options': {'fallbackOutput': 'extra'}}, [680, 200], type_version=3.2),
        node('Service | Get Settings', 'n8n-nodes-base.httpRequest', {
            'method': 'GET',
            'url': '={{ $json.settings_get_url }}',
            'sendHeaders': True,
            'headerParameters': {'parameters': [{'name': 'Authorization', 'value': "={{ 'Bearer ' + $json.service_auth_token }}"}]},
            'options': {'response': {'response': {'neverError': True}}},
        }, [1180, 120], type_version=4.2),
        node('Service | Save Settings', 'n8n-nodes-base.httpRequest', {
            'method': 'POST',
            'url': '={{ $json.settings_set_url }}',
            'sendHeaders': True,
            'headerParameters': {'parameters': [{'name': 'Authorization', 'value': "={{ 'Bearer ' + $json.service_auth_token }}"}, {'name': 'Content-Type', 'value': 'application/json'}]},
            'sendBody': True,
            'specifyBody': 'json',
            'jsonBody': '={{ $json.settings_set_body }}',
            'options': {'response': {'response': {'neverError': True}}},
        }, [1180, 300], type_version=4.2),
        node('Switch | Run Source', 'n8n-nodes-base.switch', {'rules': {'values': [switch_condition_equals('={{ $json.action || "" }}', 'run_search')]}, 'options': {'fallbackOutput': 'extra'}}, [1180, 520], type_version=3.2),
        node('Search | Build Started Reply', 'n8n-nodes-base.code', {'jsCode': build_started_reply_js}, [1420, 440], type_version=2),
        node('Service | Run Search', 'n8n-nodes-base.httpRequest', {
            'method': 'POST',
            'url': '={{ $json.run_url }}',
            'sendHeaders': True,
            'headerParameters': {'parameters': [{'name': 'Authorization', 'value': "={{ 'Bearer ' + $json.service_auth_token }}"}, {'name': 'Content-Type', 'value': 'application/json'}]},
            'sendBody': True,
            'specifyBody': 'json',
            'jsonBody': '={{ $json.run_body }}',
            'options': {'response': {'response': {'neverError': True}}},
        }, [1420, 600], type_version=4.2),
        node('Telegram | Build Settings Reply', 'n8n-nodes-base.code', {'jsCode': build_settings_reply_js}, [1420, 120], type_version=2),
        node('Telegram | Build Settings Saved Reply', 'n8n-nodes-base.code', {'jsCode': build_saved_reply_js}, [1420, 300], type_version=2),
        node('Telegram | Build Search Reply', 'n8n-nodes-base.code', {'jsCode': build_search_reply_js}, [1660, 600], type_version=2),
        node('Telegram | Send Message', 'n8n-nodes-base.httpRequest', {
            'method': 'POST',
            'url': '={{ $json.telegram_send_url }}',
            'sendHeaders': True,
            'headerParameters': {'parameters': [{'name': 'Content-Type', 'value': 'application/json'}]},
            'sendBody': True,
            'specifyBody': 'json',
            'jsonBody': send_message_json,
            'options': {'response': {'response': {'neverError': True}}},
        }, [1900, 280], type_version=4.2),
    ]

    connections = {
        'Telegram | Webhook': {'main': [[{'node': 'Telegram | Normalize Update', 'type': 'main', 'index': 0}]]},
        'Telegram | Normalize Update': {'main': [[{'node': 'Webhook | ACK', 'type': 'main', 'index': 0}, {'node': 'Switch | Authorized', 'type': 'main', 'index': 0}]]},
        'Switch | Authorized': {'main': [[{'node': 'Switch | Input Kind', 'type': 'main', 'index': 0}], []]},
        'Switch | Input Kind': {'main': [[{'node': 'Command | Classify', 'type': 'main', 'index': 0}], [{'node': 'Telegram | Build Unsupported Reply', 'type': 'main', 'index': 0}]]},
        'Telegram | Build Unsupported Reply': {'main': [[{'node': 'Telegram | Send Message', 'type': 'main', 'index': 0}]]},
        'Command | Classify': {'main': [[{'node': 'Switch | Quick Command', 'type': 'main', 'index': 0}]]},
        'Switch | Quick Command': {
            'main': [
                [{'node': 'Telegram | Build Help Reply', 'type': 'main', 'index': 0}],
                [{'node': 'Service | Get Settings', 'type': 'main', 'index': 0}],
                [{'node': 'Command | Parse City', 'type': 'main', 'index': 0}],
                [{'node': 'Command | Parse Count', 'type': 'main', 'index': 0}],
                [{'node': 'AI | Request Mistral', 'type': 'main', 'index': 0}],
            ]
        },
        'Telegram | Build Help Reply': {'main': [[{'node': 'Telegram | Send Message', 'type': 'main', 'index': 0}]]},
        'Command | Parse City': {'main': [[{'node': 'Switch | Save Source', 'type': 'main', 'index': 0}]]},
        'Command | Parse Count': {'main': [[{'node': 'Switch | Save Source', 'type': 'main', 'index': 0}]]},
        'AI | Request Mistral': {'main': [[{'node': 'AI | Parse Decision', 'type': 'main', 'index': 0}]]},
        'AI | Parse Decision': {'main': [[{'node': 'Switch | AI Action', 'type': 'main', 'index': 0}]]},
        'Switch | AI Action': {
            'main': [
                [{'node': 'Telegram | Build Help Reply', 'type': 'main', 'index': 0}],
                [{'node': 'Service | Get Settings', 'type': 'main', 'index': 0}],
                [{'node': 'Switch | Save Source', 'type': 'main', 'index': 0}],
                [{'node': 'Switch | Run Source', 'type': 'main', 'index': 0}],
                [{'node': 'Telegram | Build Help Reply', 'type': 'main', 'index': 0}],
            ]
        },
        'Switch | Save Source': {'main': [[{'node': 'Service | Save Settings', 'type': 'main', 'index': 0}], []]},
        'Service | Get Settings': {'main': [[{'node': 'Telegram | Build Settings Reply', 'type': 'main', 'index': 0}]]},
        'Service | Save Settings': {'main': [[{'node': 'Telegram | Build Settings Saved Reply', 'type': 'main', 'index': 0}]]},
        'Telegram | Build Settings Reply': {'main': [[{'node': 'Telegram | Send Message', 'type': 'main', 'index': 0}]]},
        'Telegram | Build Settings Saved Reply': {'main': [[{'node': 'Telegram | Send Message', 'type': 'main', 'index': 0}]]},
        'Switch | Run Source': {'main': [[{'node': 'Search | Build Started Reply', 'type': 'main', 'index': 0}, {'node': 'Service | Run Search', 'type': 'main', 'index': 0}], []]},
        'Search | Build Started Reply': {'main': [[{'node': 'Telegram | Send Message', 'type': 'main', 'index': 0}]]},
        'Service | Run Search': {'main': [[{'node': 'Telegram | Build Search Reply', 'type': 'main', 'index': 0}]]},
        'Telegram | Build Search Reply': {'main': [[{'node': 'Telegram | Send Message', 'type': 'main', 'index': 0}]]},
    }

    return {
        'name': WORKFLOW_NAME,
        'nodes': nodes,
        'connections': connections,
        'settings': {'executionOrder': 'v1', 'callerPolicy': 'workflowsFromSameOwner', 'availableInMCP': False},
    }


def find_existing_workflow(session: requests.Session) -> dict[str, Any] | None:
    response = session.get(f'{N8N_BASE_URL}/api/v1/workflows', timeout=60)
    response.raise_for_status()
    data = response.json().get('data', [])
    for item in data:
        if item.get('name') == WORKFLOW_NAME:
            return item
    return None


def sanitize_for_update(existing: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return {
        'name': payload['name'],
        'nodes': payload['nodes'],
        'connections': payload['connections'],
        'settings': payload.get('settings', {}),
    }


def upsert_workflow(session: requests.Session, payload: dict[str, Any]) -> dict[str, Any]:
    existing = find_existing_workflow(session)
    if existing:
        workflow_id = existing['id']
        session.post(f'{N8N_BASE_URL}/api/v1/workflows/{workflow_id}/deactivate', timeout=60)
        response = session.put(
            f'{N8N_BASE_URL}/api/v1/workflows/{workflow_id}',
            data=json.dumps(sanitize_for_update(existing, payload), ensure_ascii=True),
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
    else:
        response = session.post(f'{N8N_BASE_URL}/api/v1/workflows', data=json.dumps(payload, ensure_ascii=True), timeout=60)
        response.raise_for_status()
        result = response.json()
        workflow_id = result['id']
    activate = session.post(f"{N8N_BASE_URL}/api/v1/workflows/{result['id']}/activate", timeout=60)
    activate.raise_for_status()
    return activate.json()


def set_telegram_webhook(cfg: dict[str, str]) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{cfg['TELEGRAM_BOT_TOKEN']}/setWebhook"
    webhook_url = f'{N8N_BASE_URL}/webhook/{WEBHOOK_PATH}'
    response = requests.post(
        url,
        data={
            'url': webhook_url,
            'secret_token': cfg['TELEGRAM_WEBHOOK_SECRET'],
            'drop_pending_updates': 'true',
            'allowed_updates': json.dumps(['message', 'edited_message']),
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def get_telegram_webhook_info(cfg: dict[str, str]) -> dict[str, Any]:
    response = requests.get(f"https://api.telegram.org/bot{cfg['TELEGRAM_BOT_TOKEN']}/getWebhookInfo", timeout=60)
    response.raise_for_status()
    return response.json()


def main() -> int:
    cfg = load_env(SECRETS_ENV)
    required = [
        'TELEGRAM_BOT_TOKEN',
        'MISTRAL_API_KEY',
        'COSMETOLOGIST_HUNTER_AUTH_TOKEN',
        'COSMETOLOGIST_HUNTER_LIVE_URL',
        'TELEGRAM_WEBHOOK_SECRET',
    ]
    missing = [key for key in required if not cfg.get(key)]
    if missing:
        raise RuntimeError(f'Missing secrets: {", ".join(missing)}')

    payload = build_workflow(cfg)
    COMPILED_WORKFLOW_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    session = api_session()
    workflow = upsert_workflow(session, payload)
    webhook = set_telegram_webhook(cfg)
    webhook_info = get_telegram_webhook_info(cfg)

    print(json.dumps({
        'workflow_id': workflow['id'],
        'workflow_name': workflow['name'],
        'active': workflow['active'],
        'compiled_workflow': str(COMPILED_WORKFLOW_PATH),
        'telegram_set_webhook_ok': webhook.get('ok'),
        'telegram_webhook_url': webhook_info.get('result', {}).get('url', ''),
        'telegram_pending_update_count': webhook_info.get('result', {}).get('pending_update_count', 0),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
