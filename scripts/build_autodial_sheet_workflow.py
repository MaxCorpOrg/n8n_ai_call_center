#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import pathlib
import re
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


REPO_ROOT = pathlib.Path("/home/max/n8n_ai_call_center")
REPO_WORKFLOW = REPO_ROOT / "workflows" / "AUTODIAL_DISPATCHER_DRAFT.json"
LIVE_WORKFLOW_ID = "iZ8OaN4xW0ZtxaCJ"
LIVE_CALL_LOG_WORKFLOW_ID = "kZSdJrsAHWWIC2l6"
LIVE_WORKFLOW_TEMP = pathlib.Path("/tmp/autodial_dispatcher_sheet_first_live.json")
N8N_BASE_URL = "https://www.n-8-n.site"
N8N_ENV_FILE = pathlib.Path("/home/max/.config/lipolong-eleven-relay.env")
LIVE_SPREADSHEET_ID = "1SyoGWXrvLNevGzjWQjfSP7eRqVCMOzR0MzXeWSL7HOo"
LIVE_SHEET_GID = "199760593"
LIVE_SHEET_NAME = "Лиды_обзвон"
LIVE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/1SyoGWXrvLNevGzjWQjfSP7eRqVCMOzR0MzXeWSL7HOo/edit?gid=199760593#gid=199760593"


def load_n8n_api_key() -> str:
    text = N8N_ENV_FILE.read_text(encoding="utf-8")
    match = re.search(r"^N8N_API_KEY=(.+)$", text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not find N8N_API_KEY in {N8N_ENV_FILE}")
    return match.group(1).strip()


def api_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "X-N8N-API-KEY": load_n8n_api_key(),
            "Content-Type": "application/json",
        }
    )
    return session


def fetch_workflow(session: requests.Session, workflow_id: str) -> dict:
    response = session.get(f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}", timeout=30)
    response.raise_for_status()
    return response.json()


def put_workflow(session: requests.Session, workflow_id: str, payload: dict) -> dict:
    response = session.put(
        f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}",
        data=json.dumps(payload, ensure_ascii=True),
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def make_node(name: str, type_: str, parameters: dict, position: list[int], *, type_version=2) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": type_,
        "typeVersion": type_version,
        "position": position,
        "parameters": parameters,
    }


def find_node(workflow: dict, name: str) -> dict:
    for node in workflow["nodes"]:
        if node["name"] == name:
            return node
    raise KeyError(f"Node not found: {name}")


def upsert_node(workflow: dict, node: dict) -> None:
    for idx, current in enumerate(workflow["nodes"]):
        if current["name"] == node["name"]:
            workflow["nodes"][idx] = node
            return
    workflow["nodes"].append(node)


def sanitize_google_payload_js(js_code: str) -> str:
    js_code = re.sub(r"(client_id:\s*)'[^']+'", r"\1'{{GOOGLE_CLIENT_ID}}'", js_code)
    js_code = re.sub(r"(client_secret:\s*)'[^']+'", r"\1'{{GOOGLE_CLIENT_SECRET}}'", js_code)
    js_code = re.sub(r"(refresh_token:\s*)'[^']+'", r"\1'{{GOOGLE_REFRESH_TOKEN}}'", js_code)
    return js_code


def extract_google_oauth_credentials(js_code: str) -> dict[str, str]:
    patterns = {
        "client_id": r"client_id:\s*'([^']+)'",
        "client_secret": r"client_secret:\s*'([^']+)'",
        "refresh_token": r"refresh_token:\s*'([^']+)'",
    }
    creds = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, js_code)
        if not match:
            raise RuntimeError(f"Could not extract Google OAuth field {key} from workflow JS payload")
        creds[key] = match.group(1)
    return creds


def inject_google_oauth_js(js_code: str, creds: dict[str, str]) -> str:
    js_code = re.sub(r"(client_id:\s*)'[^']+'", rf"\1'{creds['client_id']}'", js_code)
    js_code = re.sub(r"(client_secret:\s*)'[^']+'", rf"\1'{creds['client_secret']}'", js_code)
    js_code = re.sub(r"(refresh_token:\s*)'[^']+'", rf"\1'{creds['refresh_token']}'", js_code)
    return js_code


def load_google_oauth_credentials(session: requests.Session) -> dict[str, str]:
    workflow = fetch_workflow(session, LIVE_CALL_LOG_WORKFLOW_ID)
    node = find_node(workflow, "Google | Build Payload")
    return extract_google_oauth_credentials(node["parameters"]["jsCode"])


def build_google_sheet_payload_js() -> str:
    return """
return [{
  spreadsheet_id: '__LIVE_SPREADSHEET_ID__',
  target_sheet_gid: '__LIVE_SHEET_GID__',
  fallback_sheet_name: '__LIVE_SHEET_NAME__',
  metadata_url: 'https://sheets.googleapis.com/v4/spreadsheets/__LIVE_SPREADSHEET_ID__?fields=sheets.properties(sheetId,title)',
  oauth_url: 'https://oauth2.googleapis.com/token',
  client_id: '{{GOOGLE_CLIENT_ID}}',
  client_secret: '{{GOOGLE_CLIENT_SECRET}}',
  refresh_token: '{{GOOGLE_REFRESH_TOKEN}}',
}];
""".strip().replace("__LIVE_SPREADSHEET_ID__", LIVE_SPREADSHEET_ID).replace("__LIVE_SHEET_GID__", LIVE_SHEET_GID).replace("__LIVE_SHEET_NAME__", LIVE_SHEET_NAME)


def build_run_context_js() -> str:
    return """
const now = new Date();
const fmt = new Intl.DateTimeFormat('sv-SE', {
  timeZone: 'Europe/Moscow',
  hour12: false,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
}).format(now);
const weekdayFmt = new Intl.DateTimeFormat('en-US', {
  timeZone: 'Europe/Moscow',
  weekday: 'short',
});
const [mskDate, mskTime] = fmt.split(' ');
const [hh, mm] = mskTime.split(':');
const minutes = Number(hh) * 60 + Number(mm);
const mskWeekday = weekdayFmt.format(now);
const isWeekend = mskWeekday === 'Sat' || mskWeekday === 'Sun';
const withinClockWindow = minutes >= 600 && minutes < 840;
const withinWindow = !isWeekend && withinClockWindow;
const campaignKey = 'lipolong_contacts_msk';
const jobId = `autodial.${mskDate}.${mskTime.replace(/:/g, '')}.${Math.random().toString(36).slice(2, 8)}`;
return [{
  run_ts: now.toISOString(),
  msk_datetime: `${mskDate}T${mskTime}+03:00`,
  msk_date: mskDate,
  msk_time: mskTime,
  msk_weekday: mskWeekday,
  is_weekend: isWeekend,
  within_clock_window: withinClockWindow,
  within_window: withinWindow,
  reason: isWeekend ? 'weekend_day' : (withinClockWindow ? '' : 'outside_call_window'),
  campaign_key: campaignKey,
  job_id: jobId,
  daily_live_limit: 15,
  daily_dialing_limit: 30,
  daily_nonhuman_limit: 10,
  daily_provider_failure_limit: 8,
  daily_attempt_limit_per_lead: 2,
  monthly_touch_limit_per_phone: 1,
  max_unreachable_total: 3,
  max_attempts_per_lead: 3,
  call_window_start: '10:00',
  call_window_end: '14:00',
  dial_timeout_minutes: 5,
  spreadsheet_id: '__LIVE_SPREADSHEET_ID__',
  sheet_gid: '__LIVE_SHEET_GID__',
  fallback_sheet_name: '__LIVE_SHEET_NAME__',
  sheet_url: '__LIVE_SHEET_URL__',
  sheet_range: 'A1:AM',
}];
""".strip().replace("__LIVE_SPREADSHEET_ID__", LIVE_SPREADSHEET_ID).replace("__LIVE_SHEET_GID__", LIVE_SHEET_GID).replace("__LIVE_SHEET_NAME__", LIVE_SHEET_NAME).replace("__LIVE_SHEET_URL__", LIVE_SHEET_URL)


def parse_sheet_rows_js() -> str:
    return r"""
const body = $json.body ?? $json;
const values = Array.isArray(body.values) ? body.values : [];
const headers = values.length ? values[0].map((h) => String(h || '').trim()) : [];
const asText = (v) => String(v ?? '').trim();
const normalizePhone = (input) => {
  const digits = String(input || '').replace(/\D/g, '');
  if (!digits) return '';
  if (digits.length === 11 && digits.startsWith('8')) return `+7${digits.slice(1)}`;
  if (digits.length === 11 && digits.startsWith('7')) return `+${digits}`;
  if (digits.length === 10) return `+7${digits}`;
  if (digits.length >= 11 && digits.length <= 15) return `+${digits}`;
  return String(input || '').trim();
};
const isDialablePhone = (input) => /^\+\d{11,15}$/.test(String(input || '').trim());
const asBool = (v) => ['1', 'true', 'yes', 'да'].includes(asText(v).toLowerCase());
const parseTs = (v) => {
  if (!v) return null;
  const t = Date.parse(String(v));
  return Number.isFinite(t) ? t : null;
};
const fmtMsk = (date, withTime = false) => new Intl.DateTimeFormat('sv-SE', {
  timeZone: 'Europe/Moscow',
  hour12: false,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  ...(withTime ? { hour: '2-digit', minute: '2-digit', second: '2-digit' } : {}),
}).format(date);
const nextMskDayAt = (baseTs, hour, minute) => {
  const currentDate = fmtMsk(new Date(baseTs), false);
  const [y, m, d] = currentDate.split('-').map(Number);
  const nextUtc = new Date(Date.UTC(y, m - 1, d, 0, 0, 0));
  nextUtc.setUTCDate(nextUtc.getUTCDate() + 1);
  const nextDate = fmtMsk(nextUtc, false);
  const hh = String(hour).padStart(2, '0');
  const mm = String(minute).padStart(2, '0');
  return parseTs(`${nextDate}T${hh}:${mm}:00+03:00`);
};
const now = new Date();
const mskFmt = fmtMsk(now, true);
const [mskDate, mskTime] = mskFmt.split(' ');
const nowTs = parseTs(`${mskDate}T${mskTime}+03:00`) || now.getTime();
const campaignKey = String($node['Dispatcher | Build Run Context'].json.campaign_key || 'lipolong_contacts_msk');
const jobId = String($node['Dispatcher | Build Run Context'].json.job_id || `autodial.${Date.now()}`);
const dailyLiveLimit = Number($node['Dispatcher | Build Run Context'].json.daily_live_limit || 15);
const dailyDialingLimit = Number($node['Dispatcher | Build Run Context'].json.daily_dialing_limit || 50);
const dailyNonHumanLimit = Number($node['Dispatcher | Build Run Context'].json.daily_nonhuman_limit || 10);
const dailyProviderFailureLimit = Number($node['Dispatcher | Build Run Context'].json.daily_provider_failure_limit || 8);
const dailyAttemptLimit = Number($node['Dispatcher | Build Run Context'].json.daily_attempt_limit_per_lead || 2);
const monthlyTouchLimitPerPhone = Number($node['Dispatcher | Build Run Context'].json.monthly_touch_limit_per_phone || 1);
const maxUnreachableTotal = Number($node['Dispatcher | Build Run Context'].json.max_unreachable_total || 3);
const maxAttemptsPerLead = Number($node['Dispatcher | Build Run Context'].json.max_attempts_per_lead || 3);
const dialTimeoutMinutes = Number($node['Dispatcher | Build Run Context'].json.dial_timeout_minutes || 5);
const callWindowStart = String($node['Dispatcher | Build Run Context'].json.call_window_start || '10:00');
const callWindowEnd = String($node['Dispatcher | Build Run Context'].json.call_window_end || '14:00');
const mskMonth = mskDate.slice(0, 7);

const failureResults = new Set(['busy', 'no_answer', 'timeout', 'outbound_request_failed']);
const finalResults = new Set(['dnc', 'not_target', 'order_test', 'manager_call']);
const unreachableResults = new Set(['no_answer', 'timeout']);
const retryResults = new Set(['busy', 'no_answer', 'timeout', 'callback_scheduled', 'send_kp_pending_callback', 'refusal_soft', 'outbound_request_failed', 'dialing']);
const monthlyTouchResults = new Set(['refusal_soft', 'send_kp_pending_callback', 'order_test', 'manager_call', 'not_target', 'dnc']);
const nonHumanConversationResults = new Set(['busy', 'no_answer', 'send_kp_pending_callback']);

const makeRow = (rowValues, sheetRowNumber) => {
  const obj = { sheet_row_number: sheetRowNumber };
  headers.forEach((header, idx) => {
    if (!header) return;
    obj[header] = asText(rowValues[idx]);
  });
  obj.source_system = asText(obj.source_system);
  obj.lead_id = asText(obj.lead_id);
  obj.source_record_key = asText(obj.source_record_key);
  obj.phone_primary = normalizePhone(obj.phone_primary || obj.caller || obj.phone || '');
  obj.phone_secondary = normalizePhone(obj.phone_secondary || '');
  obj.lpr_confirmed = asBool(obj.lpr_confirmed);
  obj.material_sent = asBool(obj.material_sent);
  obj.do_not_call = asBool(obj.do_not_call);
  obj.followup_count = Number(obj.followup_count || 0) || 0;
  obj.max_touch_limit = Number(obj.max_touch_limit || 0) || maxAttemptsPerLead;
  obj.lead_key = obj.source_record_key || obj.lead_id || obj.phone_primary || obj.phone_secondary || `row_${sheetRowNumber}`;
  obj.phone_key = obj.phone_primary || obj.phone_secondary || '';
  obj.dial_phone = isDialablePhone(obj.phone_primary)
    ? obj.phone_primary
    : (isDialablePhone(obj.phone_secondary) ? obj.phone_secondary : '');
  obj.has_dialable_phone = !!obj.dial_phone;
  obj.result_key = String(obj.call_result || '').toLowerCase();
  obj.created_ts = parseTs(obj.created_at) || parseTs(obj.updated_at) || null;
  obj.updated_ts = parseTs(obj.updated_at) || obj.created_ts || null;
  obj.row_date = obj.updated_ts ? fmtMsk(new Date(obj.updated_ts), false) : mskDate;
  obj.row_month = obj.row_date.slice(0, 7);
  obj.next_call_ts = parseTs(obj.next_call_at);
  obj.is_autodial_attempt = obj.source_system === 'autodial_dispatcher' && obj.result_key === 'dialing';
  obj.has_valid_conv_id = /^conv_[a-z0-9]+$/i.test(String(obj.eleven_conv_id || '').trim());
  obj.has_row_key_identity = /^row_\d+$/i.test(String(obj.source_record_key || '').trim())
    || /^row_\d+$/i.test(String(obj.lead_id || '').trim());
  const leadIdPhone = normalizePhone(obj.lead_id || '');
  const sourceRecordPhone = normalizePhone(obj.source_record_key || '');
  obj.has_traceable_identity = obj.has_valid_conv_id
    || obj.has_row_key_identity
    || isDialablePhone(obj.phone_primary)
    || isDialablePhone(obj.phone_secondary)
    || isDialablePhone(leadIdPhone)
    || isDialablePhone(sourceRecordPhone);
  obj.is_live_success = obj.source_system === 'elevenlabs' && obj.has_valid_conv_id && !failureResults.has(obj.result_key) && obj.result_key !== 'dialing' && obj.result_key !== '';
  obj.has_monthly_touch = obj.source_system !== 'xlsx_import' && obj.row_month === mskMonth && (obj.is_live_success || monthlyTouchResults.has(obj.result_key));
  return obj;
};

const effectiveNextCallTs = (row, state) => {
  if (row.next_call_ts) return row.next_call_ts;
  const anchorTs = row.updated_ts || row.created_ts || nowTs;
  if (row.result_key === 'outbound_request_failed') {
    if (state.attempts_today >= dailyAttemptLimit) return nextMskDayAt(anchorTs, 10, 15);
    return anchorTs + (15 * 60 * 1000);
  }
  if (row.result_key === 'busy' || row.result_key === 'no_answer' || row.result_key === 'timeout') {
    if (state.attempts_today >= dailyAttemptLimit) return nextMskDayAt(anchorTs, 10, 15);
    return anchorTs + (30 * 60 * 1000);
  }
  return null;
};

const rows = values.slice(1)
  .map((rowValues, idx) => makeRow(rowValues, idx + 2))
  .filter((row) => Object.values(row).some((v) => String(v ?? '').trim() !== ''));

const seedByPhone = new Map();
for (const row of rows) {
  if (row.source_system === 'xlsx_import' && row.phone_key && !seedByPhone.has(row.phone_key)) {
    seedByPhone.set(row.phone_key, row);
  }
}

for (const row of rows) {
  const seed = row.phone_key ? seedByPhone.get(row.phone_key) : null;
  const seedLeadKey = String(seed?.lead_key || '').trim();
  const seedSourceRecordKey = String(seed?.source_record_key || seedLeadKey || '').trim();
  row.canonical_lead_key = seedLeadKey || row.lead_key || `row_${row.sheet_row_number}`;
  row.canonical_source_record_key = seedSourceRecordKey || row.source_record_key || row.canonical_lead_key;
  row.canonical_sheet_row_number = Number(seed?.sheet_row_number || row.sheet_row_number || 0);
  if (!row.company_name && seed?.company_name) row.company_name = seed.company_name;
  if (!row.contact_name && seed?.contact_name) row.contact_name = seed.contact_name;
  if (!row.city && seed?.city) row.city = seed.city;
  if (!row.segment && seed?.segment) row.segment = seed.segment;
  if (!row.lpr_role && seed?.lpr_role) row.lpr_role = seed.lpr_role;
  if (!row.preferred_channel && seed?.preferred_channel) row.preferred_channel = seed.preferred_channel;
  if (!row.manager_owner && seed?.manager_owner) row.manager_owner = seed.manager_owner;
  if (!row.phone_secondary && seed?.phone_secondary) row.phone_secondary = seed.phone_secondary;
  if (!row.phone_primary && seed?.phone_primary) row.phone_primary = seed.phone_primary;
}

const seedRows = [];
const outcomeRows = [];
const byLead = new Map();
const byPhoneMonth = new Map();

for (const row of rows) {
  if (row.source_system === 'xlsx_import') {
    seedRows.push({
      sheet_row_number: row.canonical_sheet_row_number || row.sheet_row_number,
      lead_key: row.canonical_lead_key || row.lead_key,
      source_system: row.source_system,
      source_record_key: row.canonical_source_record_key || row.source_record_key,
      company_name: row.company_name || '',
      contact_name: row.contact_name || '',
      phone_primary: row.phone_primary || '',
      phone_secondary: row.phone_secondary || '',
      city: row.city || '',
      segment: row.segment || '',
      lpr_role: row.lpr_role || '',
      lpr_confirmed: row.lpr_confirmed === true,
      current_supplier: row.current_supplier || '',
      current_product: row.current_product || '',
      current_price: row.current_price || '',
      pain_points: row.pain_points || '',
      interest_level: row.interest_level || '',
      objection_code: row.objection_code || '',
      objection_text: row.objection_text || '',
      preferred_channel: row.preferred_channel || 'phone',
      manager_owner: row.manager_owner || '',
      notes_short: row.notes_short || '',
      do_not_call: row.do_not_call === true,
      max_touch_limit: row.max_touch_limit || maxAttemptsPerLead,
    });
  } else {
    outcomeRows.push({
      sheet_row_number: row.canonical_sheet_row_number || row.sheet_row_number,
      lead_key: row.canonical_lead_key || row.lead_key,
      lead_id: row.lead_id || '',
      source_system: row.source_system,
      source_record_key: row.canonical_source_record_key || row.source_record_key,
      company_name: row.company_name || '',
      contact_name: row.contact_name || '',
      phone_primary: row.phone_primary || '',
      phone_secondary: row.phone_secondary || '',
      city: row.city || '',
      segment: row.segment || '',
      lpr_role: row.lpr_role || '',
      lpr_confirmed: row.lpr_confirmed === true,
      current_supplier: row.current_supplier || '',
      current_product: row.current_product || '',
      current_price: row.current_price || '',
      pain_points: row.pain_points || '',
      interest_level: row.interest_level || '',
      objection_code: row.objection_code || '',
      objection_text: row.objection_text || '',
      preferred_channel: row.preferred_channel || 'phone',
      manager_owner: row.manager_owner || '',
      notes_short: row.notes_short || '',
      call_result: row.call_result || '',
      next_step: row.next_step || '',
      next_call_at: row.next_call_at || '',
      material_sent: row.material_sent === true,
      do_not_call: row.do_not_call === true,
      final_reason: row.final_reason || '',
      eleven_conv_id: row.eleven_conv_id || '',
      n8n_execution_id: row.n8n_execution_id || '',
      call_record_url: row.call_record_url || '',
      created_at: row.created_at || '',
      updated_at: row.updated_at || '',
      row_date: row.row_date || '',
      result_key: row.result_key || '',
      has_valid_conv_id: row.has_valid_conv_id === true,
      has_traceable_identity: row.has_traceable_identity === true,
      is_live_connect: row.is_live_success === true,
    });
  }

  if (row.phone_key) {
    const phoneState = byPhoneMonth.get(row.phone_key) || {
      phone_key: row.phone_key,
      monthly_touch_count: 0,
      latest_touch_ts: 0,
    };
    if (row.has_monthly_touch) {
      phoneState.monthly_touch_count += 1;
      phoneState.latest_touch_ts = Math.max(phoneState.latest_touch_ts, row.updated_ts || row.created_ts || 0);
    }
    byPhoneMonth.set(row.phone_key, phoneState);
  }

  const key = String(row.canonical_lead_key || row.lead_key || '').trim();
  if (!key) continue;
  const state = byLead.get(key) || {
    lead_key: key,
    latest: null,
    history: [],
    attempts_today: 0,
    attempts_total: 0,
    unreachable_total: 0,
    live_success_today: false,
    has_retryable_history: false,
  };
  state.history.push(row);
  state.latest = row;
  if (row.is_autodial_attempt) {
    state.attempts_total += 1;
    if (row.row_date === mskDate) state.attempts_today += 1;
  }
  if (row.result_key && unreachableResults.has(row.result_key)) {
    state.unreachable_total += 1;
  }
  if (row.is_live_success && row.row_date === mskDate) {
    state.live_success_today = true;
  }
  if (row.source_system === 'autodial_dispatcher' || retryResults.has(row.result_key) || !finalResults.has(row.result_key)) {
    state.has_retryable_history = true;
  }
  byLead.set(key, state);
}

const states = Array.from(byLead.values());
const totalLeads = states.length;
const dailyLiveCount = states.filter((s) => s.live_success_today).length;
const dailyDialingCount = outcomeRows.filter((row) => {
  return row.source_system === 'autodial_dispatcher'
    && row.row_date === mskDate
    && String(row.call_result || row.result_key || '').toLowerCase() === 'dialing';
}).length;
const hasResolvedProviderFailure = (row) => {
  if (row.source_system !== 'autodial_dispatcher') return false;
  if (String(row.call_result || '').toLowerCase() !== 'outbound_request_failed') return false;
  const rowTs = row.updated_at ? parseTs(row.updated_at) : (row.created_at ? parseTs(row.created_at) : null);
  if (!rowTs) return false;
  const key = String(row.lead_key || row.lead_id || '').trim();
  const state = byLead.get(key);
  if (!state || !Array.isArray(state.history)) return false;
  return state.history.some((other) => {
    const otherTs = other.updated_ts || other.created_ts || 0;
    const otherResult = String(other.result_key || other.call_result || '').toLowerCase();
    return other.source_system === 'elevenlabs'
      && other.row_date === row.row_date
      && otherTs >= rowTs
      && !!otherResult
      && otherResult !== 'dialing';
  });
};
const recentProviderFailureCount = outcomeRows.filter((row) => {
  const rowTs = row.updated_at ? parseTs(row.updated_at) : (row.created_at ? parseTs(row.created_at) : null);
  if (!rowTs) return false;
  return row.source_system === 'autodial_dispatcher'
    && String(row.call_result || '').toLowerCase() === 'outbound_request_failed'
    && !hasResolvedProviderFailure(row)
    && rowTs >= (nowTs - 15 * 60 * 1000);
}).length;
const todayProviderFailureCount = outcomeRows.filter((row) => {
  return row.source_system === 'autodial_dispatcher'
    && row.row_date === mskDate
    && String(row.call_result || '').toLowerCase() === 'outbound_request_failed'
    && !hasResolvedProviderFailure(row);
}).length;
const dailyNonHumanConversationCount = outcomeRows.filter((row) => {
  const result = String(row.call_result || row.result_key || '').toLowerCase();
  return row.source_system === 'elevenlabs'
    && row.row_date === mskDate
    && row.has_traceable_identity === true
    && nonHumanConversationResults.has(result);
}).length;
const todayTechnicalWasteCount = outcomeRows.filter((row) => {
  const result = String(row.call_result || '').toLowerCase();
  if (result === 'outbound_request_failed' && hasResolvedProviderFailure(row)) return false;
  return row.row_date === mskDate
    && ['outbound_request_failed', 'busy', 'no_answer', 'timeout'].includes(result)
    && row.is_live_connect !== true;
}).length;
const activeDialing = states.filter((s) => {
  if (!s.latest || !s.latest.is_autodial_attempt) return false;
  const nextTs = effectiveNextCallTs(s.latest, s);
  return !!nextTs && nextTs > nowTs;
});

const wrapFinish = (reason, eligibleCount = 0) => ([{
  action: 'finish',
  reason,
  campaign_key: campaignKey,
  job_id: jobId,
  msk_datetime: mskFmt,
  msk_date: mskDate,
  msk_time: mskTime,
  daily_live_count: dailyLiveCount,
  daily_live_limit: dailyLiveLimit,
  daily_dialing_count: dailyDialingCount,
  daily_dialing_limit: dailyDialingLimit,
  daily_nonhuman_conversation_count: dailyNonHumanConversationCount,
  daily_nonhuman_limit: dailyNonHumanLimit,
  recent_provider_failure_count: recentProviderFailureCount,
  today_provider_failure_count: todayProviderFailureCount,
  daily_provider_failure_limit: dailyProviderFailureLimit,
  today_technical_waste_count: todayTechnicalWasteCount,
  active_dial_count: activeDialing.length,
  eligible_count: eligibleCount,
  total_leads: totalLeads,
  seed_rows_json: JSON.stringify(seedRows),
  outcome_rows_json: JSON.stringify(outcomeRows),
}]);

if (dailyLiveCount >= dailyLiveLimit) {
  return wrapFinish('daily_limit_reached');
}

if (dailyDialingCount >= dailyDialingLimit) {
  return wrapFinish('daily_dialing_limit_reached');
}

if (dailyNonHumanConversationCount >= dailyNonHumanLimit) {
  return wrapFinish('nonhuman_conversation_limit_reached');
}

if (activeDialing.length > 0) {
  return wrapFinish('active_dialing');
}

if (recentProviderFailureCount >= 3) {
  return wrapFinish('provider_circuit_breaker');
}

if (todayProviderFailureCount >= dailyProviderFailureLimit) {
  return wrapFinish('daily_provider_failure_limit_reached');
}

if (dailyLiveCount === 0 && todayTechnicalWasteCount >= 20) {
  return wrapFinish('tech_waste_limit_reached');
}

const retireCandidates = [];
const dialCandidates = [];

for (const state of states) {
  const latest = state.latest;
  if (!latest) continue;
  const latestResult = String(latest.result_key || '').toLowerCase();
  if (latest.do_not_call || latest.final_reason === 'number_unreachable' || finalResults.has(latestResult)) continue;
  if (state.live_success_today) continue;
  if (!latest.has_dialable_phone) continue;

  const callbackOverride = latestResult === 'callback_scheduled' || String(latest.next_step || '').toLowerCase() === 'callback';
  const nextCallTs = effectiveNextCallTs(latest, state);
  const phoneState = latest.phone_key ? byPhoneMonth.get(latest.phone_key) : null;
  const monthlyTouchCount = Number(phoneState?.monthly_touch_count || 0);

  if (monthlyTouchCount >= monthlyTouchLimitPerPhone && !callbackOverride) continue;

  if (state.unreachable_total >= maxUnreachableTotal && unreachableResults.has(latestResult)) {
    const dueTs = nextCallTs || latest.updated_ts || latest.created_ts || 0;
    retireCandidates.push({ state, dueTs });
    continue;
  }

  if (state.attempts_today >= dailyAttemptLimit && !callbackOverride) continue;
  if (nextCallTs && nextCallTs > nowTs) continue;

  const isRetryable = !latestResult
    || retryResults.has(latestResult)
    || latest.source_system === 'xlsx_import'
    || latest.source_system === 'autodial_dispatcher';
  if (!isRetryable) continue;

  const priority = nextCallTs ? 0 : 1;
  const dueTs = nextCallTs || latest.updated_ts || latest.created_ts || 0;
  dialCandidates.push({ state, priority, dueTs, nextCallTs });
}

retireCandidates.sort((a, b) => (
  a.dueTs - b.dueTs
  || (a.state.latest?.sheet_row_number || 0) - (b.state.latest?.sheet_row_number || 0)
));

if (retireCandidates.length > 0) {
  const state = retireCandidates[0].state;
  const latest = state.latest || {};
  const requestId = `${campaignKey}.${mskDate}.${mskTime.replace(/:/g, '')}.dead.${Math.random().toString(36).slice(2, 8)}`;
  return [{
    action: 'retire',
    reason: 'number_unreachable',
    campaign_key: campaignKey,
    job_id: jobId,
    msk_datetime: mskFmt,
    msk_date: mskDate,
    msk_time: mskTime,
    daily_live_count: dailyLiveCount,
    daily_live_limit: dailyLiveLimit,
    active_dial_count: 0,
    eligible_count: dialCandidates.length,
    total_leads: totalLeads,
    seed_rows_json: JSON.stringify(seedRows),
    outcome_rows_json: JSON.stringify(outcomeRows),
    retire_payload: {
      lead_id: String(state.lead_key || ''),
      client_ref: String(state.lead_key || ''),
      source_system: 'autodial_dispatcher',
      source_record_key: String(latest.canonical_source_record_key || latest.source_record_key || state.lead_key || ''),
      company_name: String(latest.company_name || ''),
      contact_name: String(latest.contact_name || ''),
      caller: String(latest.phone_primary || ''),
      phone_primary: String(latest.phone_primary || ''),
      phone_secondary: String(latest.phone_secondary || ''),
      city: String(latest.city || ''),
      segment: String(latest.segment || ''),
      lpr_role: String(latest.lpr_role || ''),
      lpr_confirmed: latest.lpr_confirmed === true,
      current_supplier: String(latest.current_supplier || ''),
      current_product: String(latest.current_product || ''),
      current_price: String(latest.current_price || ''),
      pain_points: String(latest.pain_points || ''),
      objection_code: String(latest.objection_code || ''),
      objection_text: String(latest.objection_text || ''),
      interest_level: String(latest.interest_level || ''),
      call_result: 'no_answer',
      next_step: 'archive',
      next_call_at: '',
      preferred_channel: String(latest.preferred_channel || 'phone'),
      manager_owner: String(latest.manager_owner || ''),
      material_sent: latest.material_sent === true,
      followup_count: Number(state.attempts_total || 0),
      max_touch_limit: Number(latest.max_touch_limit || maxAttemptsPerLead || 3),
      do_not_call: true,
      final_reason: 'number_unreachable',
      notes_short: 'Автодозвон остановлен: номер трижды недоступен, номер не работает.',
      notes_redacted: '',
      call_record_url: '',
      eleven_conv_id: '',
      n8n_execution_id: requestId,
      agent_version: 'AUTODIAL_DISPATCHER_SHEET_V2',
      last_updated_by: 'autodial_dispatcher',
    },
  }];
}

dialCandidates.sort((a, b) => (
  a.priority - b.priority
  || a.dueTs - b.dueTs
  || a.state.attempts_today - b.state.attempts_today
  || (a.state.latest?.sheet_row_number || 0) - (b.state.latest?.sheet_row_number || 0)
));

if (dialCandidates.length === 0) {
  const hasRetryableHistory = states.some((s) => s.has_retryable_history && !s.live_success_today && !s.latest?.do_not_call && !finalResults.has(String(s.latest?.result_key || '').toLowerCase()));
  return wrapFinish(hasRetryableHistory ? 'no_due_rows' : 'exhausted');
}

const selectedState = dialCandidates[0].state;
const latest = selectedState.latest || {};
const attemptCountToday = selectedState.attempts_today + 1;
const attemptCountTotal = selectedState.attempts_total + 1;
const lockUntilTs = nowTs + dialTimeoutMinutes * 60 * 1000;
const lockUntil = new Date(lockUntilTs).toISOString();
const nextCallTs = dialCandidates[0].nextCallTs;
const selectedPhoneState = latest.phone_key ? byPhoneMonth.get(latest.phone_key) : null;
const selected = {
  campaign_key: campaignKey,
  job_id: jobId,
  lead_key: String(latest.canonical_lead_key || selectedState.lead_key),
  client_ref: String(latest.canonical_lead_key || selectedState.lead_key),
  source_record_key: String(latest.canonical_source_record_key || latest.source_record_key || selectedState.lead_key),
  sheet_row_number: Number(latest.canonical_sheet_row_number || latest.sheet_row_number || 0),
  company_name: String(latest.company_name || ''),
  contact_name: String(latest.contact_name || ''),
  phone_primary: String(latest.dial_phone || latest.phone_primary || ''),
  phone_secondary: String(latest.phone_secondary || ''),
  city: String(latest.city || ''),
  segment: String(latest.segment || ''),
  lpr_role: String(latest.lpr_role || ''),
  lpr_confirmed: latest.lpr_confirmed === true,
  current_supplier: String(latest.current_supplier || ''),
  current_product: String(latest.current_product || ''),
  current_price: String(latest.current_price || ''),
  pain_points: String(latest.pain_points || ''),
  objection_code: String(latest.objection_code || ''),
  objection_text: String(latest.objection_text || ''),
  preferred_channel: String(latest.preferred_channel || 'phone'),
  manager_owner: String(latest.manager_owner || ''),
  notes_short: String(latest.notes_short || ''),
  interest_level: String(latest.interest_level || ''),
  call_result: String(latest.call_result || ''),
  next_step: String(latest.next_step || ''),
  next_call_at: nextCallTs ? new Date(nextCallTs).toISOString() : '',
  attempt_count_today: attemptCountToday,
  attempt_count_total: attemptCountTotal,
  previous_attempts_today: selectedState.attempts_today,
  previous_attempts_total: selectedState.attempts_total,
  unreachable_total: selectedState.unreachable_total,
  max_touch_limit: Number(latest.max_touch_limit || maxAttemptsPerLead) || maxAttemptsPerLead,
  daily_attempt_limit_per_lead: dailyAttemptLimit,
  monthly_touch_limit_per_phone: monthlyTouchLimitPerPhone,
  monthly_touch_count_for_phone: Number(selectedPhoneState?.monthly_touch_count || 0),
  max_unreachable_total: maxUnreachableTotal,
  call_window_start: callWindowStart,
  call_window_end: callWindowEnd,
  dial_timeout_minutes: dialTimeoutMinutes,
  request_id: `${campaignKey}.${mskDate}.${mskTime.replace(/:/g, '')}.${Math.random().toString(36).slice(2, 8)}`,
  run_ts: now.toISOString(),
  msk_datetime: mskFmt,
  msk_date: mskDate,
  msk_time: mskTime,
  lock_until: lockUntil,
};

const lockPayload = {
  lead_id: selected.lead_key,
  client_ref: selected.lead_key,
  source_system: 'autodial_dispatcher',
  source_record_key: selected.source_record_key,
  company_name: selected.company_name,
  contact_name: selected.contact_name,
  caller: selected.phone_primary,
  phone_primary: selected.phone_primary,
  phone_secondary: selected.phone_secondary,
  city: selected.city,
  segment: selected.segment,
  lpr_role: selected.lpr_role,
  lpr_confirmed: selected.lpr_confirmed,
  current_supplier: selected.current_supplier,
  current_product: selected.current_product,
  current_price: selected.current_price,
  pain_points: selected.pain_points,
  objection_code: selected.objection_code,
  objection_text: selected.objection_text,
  interest_level: selected.interest_level,
  call_result: 'dialing',
  next_step: 'autodial_dialing',
  next_call_at: selected.lock_until,
  preferred_channel: selected.preferred_channel,
  manager_owner: selected.manager_owner,
  material_sent: false,
  followup_count: selected.attempt_count_total,
  max_touch_limit: selected.max_touch_limit,
  do_not_call: false,
  final_reason: '',
  notes_short: 'Автодозвон: взят в работу',
  notes_redacted: '',
  call_record_url: '',
  eleven_conv_id: '',
  n8n_execution_id: selected.request_id,
  agent_version: 'AUTODIAL_DISPATCHER_SHEET_V2',
  last_updated_by: 'autodial_dispatcher',
};

return [{
  action: 'dial',
  reason: 'candidate_selected',
  campaign_key: campaignKey,
  job_id: jobId,
  msk_datetime: mskFmt,
  msk_date: mskDate,
  msk_time: mskTime,
  daily_live_count: dailyLiveCount,
  daily_live_limit: dailyLiveLimit,
  active_dial_count: 0,
  eligible_count: dialCandidates.length,
  total_leads: totalLeads,
  seed_rows_json: JSON.stringify(seedRows),
  outcome_rows_json: JSON.stringify(outcomeRows),
  selected,
  lock_payload: lockPayload,
}];
""".strip()


def build_outbound_request_js() -> str:
    return """
const row = $node['Dispatcher | Parse Sheet Rows'].json.selected || {};
const leadKey = String(row.lead_key || '');
const phone = String(row.phone_primary || row.phone_secondary || '');
return [{
  campaign_key: String(row.campaign_key || 'lipolong_contacts_msk'),
  job_id: String(row.job_id || ''),
  lead_key: leadKey,
  client_ref: leadKey,
  source_record_key: String(row.source_record_key || leadKey),
  company_name: String(row.company_name || ''),
  contact_name: String(row.contact_name || ''),
  phone_primary: phone,
  phone_target: phone,
  sheet_row_number: Number(row.sheet_row_number || 0),
  attempt_no: Number(row.attempt_count_total || 0),
  attempt_count_today: Number(row.attempt_count_today || 0),
  daily_attempt_limit_per_lead: Number(row.daily_attempt_limit_per_lead || 2),
  call_window_start: String(row.call_window_start || '10:00'),
  call_window_end: String(row.call_window_end || '14:00'),
  dial_timeout_minutes: Number(row.dial_timeout_minutes || 5),
  request_id: String(row.request_id || `autodial.${Date.now()}`),
  notes_short: String(row.notes_short || ''),
}];
""".strip()


def build_outbound_failure_js() -> str:
    return """
const responseEnvelope = $json || {};
const response = responseEnvelope.response_body || responseEnvelope.body || responseEnvelope;
const elevenResponse = response.eleven_response || responseEnvelope.eleven_response || {};
const selected = $node['Dispatcher | Parse Sheet Rows'].json.selected || {};
const attemptsToday = Number(selected.attempt_count_today || 1);
const dailyAttemptLimit = Number(selected.daily_attempt_limit_per_lead || 2);
const failureReason = String(
  response.note
  || response.message
  || response.error
  || elevenResponse.message
  || elevenResponse.error
  || responseEnvelope.note
  || responseEnvelope.message
  || responseEnvelope.error
  || response.action
  || responseEnvelope.action
  || 'outbound_request_failed'
);
const failureReasonLower = failureReason.toLowerCase();
const isBusyReject = failureReasonLower.includes('busy here') || failureReasonLower.includes('sip 486');
const now = new Date();
const fmtMsk = (date, withTime = false) => new Intl.DateTimeFormat('sv-SE', {
  timeZone: 'Europe/Moscow',
  hour12: false,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  ...(withTime ? { hour: '2-digit', minute: '2-digit', second: '2-digit' } : {}),
}).format(date);
const nextMskDayAt = (baseDate, hour, minute) => {
  const currentDate = fmtMsk(baseDate, false);
  const [y, m, d] = currentDate.split('-').map(Number);
  const nextUtc = new Date(Date.UTC(y, m - 1, d, 0, 0, 0));
  nextUtc.setUTCDate(nextUtc.getUTCDate() + 1);
  const nextDate = fmtMsk(nextUtc, false);
  const hh = String(hour).padStart(2, '0');
  const mm = String(minute).padStart(2, '0');
  return `${nextDate}T${hh}:${mm}:00+03:00`;
};
const retryDelayMinutes = isBusyReject ? 30 : 15;
const nextCallAt = attemptsToday >= dailyAttemptLimit
  ? nextMskDayAt(now, 10, 15)
  : new Date(now.getTime() + retryDelayMinutes * 60 * 1000).toISOString();
const callResult = isBusyReject ? 'busy' : 'outbound_request_failed';
const nextStep = isBusyReject ? 'retry_busy' : 'retry_after_failed_outbound';
const notesShort = isBusyReject
  ? (attemptsToday >= dailyAttemptLimit
    ? 'Автодозвон: линия занята, переносим на следующий день.'
    : 'Автодозвон: линия занята, ставим повтор.')
  : (attemptsToday >= dailyAttemptLimit
    ? 'Автодозвон: outbound запрос не принят, переносим на следующий день.'
    : 'Автодозвон: outbound запрос не принят, ставим повтор.');
return [{
  lead_id: String(selected.lead_key || ''),
  client_ref: String(selected.lead_key || ''),
  source_system: 'autodial_dispatcher',
  source_record_key: String(selected.source_record_key || selected.lead_key || ''),
  company_name: String(selected.company_name || ''),
  contact_name: String(selected.contact_name || ''),
  caller: String(selected.phone_primary || ''),
  phone_primary: String(selected.phone_primary || ''),
  phone_secondary: String(selected.phone_secondary || ''),
  city: String(selected.city || ''),
  segment: String(selected.segment || ''),
  lpr_role: String(selected.lpr_role || ''),
  lpr_confirmed: selected.lpr_confirmed === true,
  current_supplier: String(selected.current_supplier || ''),
  current_product: String(selected.current_product || ''),
  current_price: String(selected.current_price || ''),
  pain_points: String(selected.pain_points || ''),
  objection_code: String(selected.objection_code || ''),
  objection_text: String(selected.objection_text || ''),
  interest_level: String(selected.interest_level || ''),
  call_result: callResult,
  next_step: nextStep,
  next_call_at: nextCallAt,
  preferred_channel: String(selected.preferred_channel || ''),
  manager_owner: String(selected.manager_owner || ''),
  material_sent: false,
  followup_count: Number(selected.attempt_count_total || 0),
  max_touch_limit: Number(selected.max_touch_limit || 3),
  do_not_call: false,
  final_reason: '',
  notes_short: notesShort,
  notes_redacted: '',
  call_record_url: '',
  eleven_conv_id: '',
  n8n_execution_id: String(selected.request_id || ''),
  agent_version: 'AUTODIAL_DISPATCHER_SHEET_V2',
  last_updated_by: 'autodial_dispatcher',
  failure_reason: failureReason,
}];
""".strip()


def build_dead_number_row_js() -> str:
    return """
const payload = $node['Dispatcher | Parse Sheet Rows'].json.retire_payload || {};
return [payload];
""".strip()


def finish_skip_js() -> str:
    return """
const data = $json || {};
return [{
  ok: true,
  action: 'skipped',
  reason: String(data.reason || 'no_due_rows'),
  campaign_key: String(data.campaign_key || 'lipolong_contacts_msk'),
  job_id: String(data.job_id || ''),
  msk_datetime: String(data.msk_datetime || ''),
  msk_date: String(data.msk_date || ''),
  msk_time: String(data.msk_time || ''),
  daily_live_count: Number(data.daily_live_count || 0),
  daily_live_limit: Number(data.daily_live_limit || 15),
  daily_dialing_count: Number(data.daily_dialing_count || 0),
  daily_dialing_limit: Number(data.daily_dialing_limit || 50),
  daily_nonhuman_conversation_count: Number(data.daily_nonhuman_conversation_count || 0),
  daily_nonhuman_limit: Number(data.daily_nonhuman_limit || 10),
  active_dial_count: Number(data.active_dial_count || 0),
  eligible_count: Number(data.eligible_count || 0),
  total_leads: Number(data.total_leads || 0),
  recent_provider_failure_count: Number(data.recent_provider_failure_count || 0),
  today_provider_failure_count: Number(data.today_provider_failure_count || 0),
  daily_provider_failure_limit: Number(data.daily_provider_failure_limit || 8),
  today_technical_waste_count: Number(data.today_technical_waste_count || 0),
  msk_weekday: String(data.msk_weekday || ''),
  is_weekend: Boolean(data.is_weekend),
  table_finished: String(data.reason || '') === 'exhausted',
  message: ({
    weekend_day: 'Выходной день: суббота/воскресенье, автодозвон не работает.',
    outside_call_window: 'Вне окна обзвона 10:00–14:00 МСК.',
    daily_limit_reached: 'Достигнут дневной лимит живых разговоров.',
    daily_dialing_limit_reached: 'Достигнут дневной лимит попыток автодозвона.',
    nonhuman_conversation_limit_reached: 'Автодозвон остановлен: накопилось слишком много коротких нецелевых non-human разговоров.',
    active_dialing: 'Есть активный звонок в работе, новый старт пока не нужен.',
    provider_circuit_breaker: 'Автодозвон поставлен на паузу: подряд накопились технические outbound-фейлы.',
    daily_provider_failure_limit_reached: 'Автодозвон остановлен: превышен дневной лимит технических outbound-фейлов.',
    tech_waste_limit_reached: 'Автодозвон остановлен: слишком много технических пустых попыток без живых разговоров.',
    no_due_rows: 'Подходящих номеров на текущий момент нет.',
    exhausted: 'Таблица обзвона исчерпана: все доступные номера уже обработаны.',
  })[String(data.reason || 'no_due_rows')] || 'Автодозвон пропущен по текущим условиям.',
}];
""".strip()


def finish_dead_number_js() -> str:
    return """
const data = $json || {};
return [{
  ok: true,
  action: 'retired',
  reason: 'number_unreachable',
  lead_key: String(data.lead_id || data.lead_key || ''),
  note: 'dispatcher marked the number as unreachable after three unavailable attempts',
}];
""".strip()


def patch_workflow(workflow: dict, google_creds: dict[str, str]) -> dict:
    workflow = copy.deepcopy(workflow)

    find_node(workflow, "Dispatcher | Schedule Tick")["parameters"]["rule"]["interval"][0]["expression"] = "*/1 * * * *"
    find_node(workflow, "Dispatcher | Build Run Context")["parameters"]["jsCode"] = build_run_context_js()
    google_payload = find_node(workflow, "Google | Build Sheet Payload")
    google_payload["parameters"]["jsCode"] = inject_google_oauth_js(build_google_sheet_payload_js(), google_creds)
    find_node(workflow, "Dispatcher | Parse Sheet Rows")["parameters"]["jsCode"] = parse_sheet_rows_js()
    find_node(workflow, "Dispatcher | Finish Outside Window")["parameters"]["jsCode"] = finish_skip_js()
    find_node(workflow, "Dispatcher | Finish Exhausted")["parameters"]["jsCode"] = finish_skip_js()
    find_node(workflow, "Dispatcher | Build Outbound Request")["parameters"]["jsCode"] = build_outbound_request_js()
    find_node(workflow, "Postgres | Mark Outbound Failure")["parameters"]["jsCode"] = build_outbound_failure_js()

    exhaustion_switch = find_node(workflow, "Dispatcher | Exhaustion Switch")
    exhaustion_switch["parameters"]["rules"]["values"] = [
        {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
                "conditions": [
                    {"leftValue": "={{ $json.action }}", "rightValue": "dial", "operator": {"type": "string", "operation": "equals"}},
                ],
                "combinator": "and",
            },
            "renameOutput": True,
            "outputKey": "Dial",
        },
        {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
                "conditions": [
                    {"leftValue": "={{ $json.action }}", "rightValue": "retire", "operator": {"type": "string", "operation": "equals"}},
                ],
                "combinator": "and",
            },
            "renameOutput": True,
            "outputKey": "Retire",
        },
        {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
                "conditions": [
                    {"leftValue": "={{ $json.action }}", "rightValue": "finish", "operator": {"type": "string", "operation": "equals"}},
                ],
                "combinator": "and",
            },
            "renameOutput": True,
            "outputKey": "Finish",
        },
    ]

    upsert_node(
        workflow,
        make_node(
            "Dispatcher | Build Dead Number Row",
            "n8n-nodes-base.code",
            {"jsCode": build_dead_number_row_js()},
            [1740, 620],
        ),
    )
    upsert_node(
        workflow,
        make_node(
            "Dispatcher | Append Dead Number Row",
            "n8n-nodes-base.httpRequest",
            {
                "method": "POST",
                "url": "https://www.n-8-n.site/webhook/eleven/tool/call-log",
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ $json }}",
                "options": {"response": {"response": {"neverError": True}}},
            },
            [1980, 620],
            type_version=4.2,
        ),
    )
    upsert_node(
        workflow,
        make_node(
            "Dispatcher | Finish Dead Number",
            "n8n-nodes-base.code",
            {"jsCode": finish_dead_number_js()},
            [2220, 620],
        ),
    )

    workflow["connections"]["Dispatcher | Exhaustion Switch"] = {
        "main": [
            [{"node": "Postgres | Claim Next Lead", "type": "main", "index": 0}],
            [{"node": "Dispatcher | Build Dead Number Row", "type": "main", "index": 0}],
            [{"node": "Dispatcher | Finish Exhausted", "type": "main", "index": 0}],
        ]
    }
    workflow["connections"]["Dispatcher | Build Dead Number Row"] = {
        "main": [[{"node": "Dispatcher | Append Dead Number Row", "type": "main", "index": 0}]]
    }
    workflow["connections"]["Dispatcher | Append Dead Number Row"] = {
        "main": [[{"node": "Dispatcher | Finish Dead Number", "type": "main", "index": 0}]]
    }

    return workflow


def repo_payload_from_live(workflow: dict) -> dict:
    payload = {
        "name": workflow["name"],
        "active": workflow.get("active", True),
        "nodes": copy.deepcopy(workflow["nodes"]),
        "connections": copy.deepcopy(workflow["connections"]),
        "settings": copy.deepcopy(workflow.get("settings", {})),
    }
    google_payload = find_node(payload, "Google | Build Sheet Payload")
    google_payload["parameters"]["jsCode"] = sanitize_google_payload_js(google_payload["parameters"]["jsCode"])
    return payload


def main() -> None:
    session = api_session()
    live_before = fetch_workflow(session, LIVE_WORKFLOW_ID)
    google_creds = load_google_oauth_credentials(session)
    live_after = patch_workflow(live_before, google_creds)
    repo_workflow = repo_payload_from_live(live_after)

    LIVE_WORKFLOW_TEMP.write_text(json.dumps(live_after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPO_WORKFLOW.write_text(json.dumps(repo_workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    backup_stamp = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d_%H-%M-%S")
    backup_dir = REPO_ROOT / "backups" / f"{backup_stamp}_autodial_busy_reject_fix"
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / "autodial_live_before.json").write_text(json.dumps(live_before, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (backup_dir / "autodial_live_after.json").write_text(json.dumps(live_after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    live_put_payload = {
        "name": live_after["name"],
        "nodes": live_after["nodes"],
        "connections": live_after["connections"],
        "settings": live_after["settings"],
    }
    response = put_workflow(session, LIVE_WORKFLOW_ID, live_put_payload)
    summary = {
        "id": response.get("id", LIVE_WORKFLOW_ID),
        "name": response.get("name", live_after["name"]),
        "active": response.get("active", live_after.get("active")),
        "nodes": len(live_after["nodes"]),
        "cron": find_node(live_after, "Dispatcher | Schedule Tick")["parameters"]["rule"]["interval"][0]["expression"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
