#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import uuid
from typing import Any


REPO_ROOT = pathlib.Path("/home/max/n8n_ai_call_center")
OUTPUT_PATH = REPO_ROOT / "workflows" / "ELEVEN_TOOL_SEND_SMS_AND_LOG_BRIDGE_LAB_DRAFT.json"


def node(
    name: str,
    type_: str,
    parameters: dict[str, Any],
    position: list[int],
    *,
    type_version: float | int = 2,
    webhook_id: str | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": type_,
        "typeVersion": type_version,
        "position": position,
        "parameters": parameters,
    }
    if webhook_id:
        out["webhookId"] = webhook_id
    return out


NORMALIZE_SMS_JS = r"""const body = $json.body ?? $json;
const nowIso = new Date().toISOString();

const asText = (v) => {
  if (v === null || v === undefined) return '';
  return String(v).trim();
};

const asBool = (v) => {
  if (typeof v === 'boolean') return v;
  const s = asText(v).toLowerCase();
  return ['1', 'true', 'yes', 'да', 'y'].includes(s);
};

const normalizeMultiline = (v) => String(v || '')
  .replace(/\r/g, '')
  .split('\n')
  .map((line) => line.replace(/\s+/g, ' ').trim())
  .filter(Boolean)
  .join('\n')
  .trim();

const normalizePhone = (input) => {
  const digits = String(input || '').replace(/\D/g, '');
  if (!digits) return '';
  if (digits.length === 11 && digits.startsWith('8')) return `+7${digits.slice(1)}`;
  if (digits.length === 11 && digits.startsWith('7')) return `+${digits}`;
  if (digits.length === 10) return `+7${digits}`;
  if (digits.length >= 11 && digits.length <= 15) return `+${digits}`;
  return '';
};

const explicitPhoneRaw = asText(body.phone_target);
const explicitPhone = normalizePhone(explicitPhoneRaw);
const currentCallNumber = asText(body.current_call_number || body.system__called_number || body.caller || body.phone_primary);
const currentCallPhone = normalizePhone(currentCallNumber);
const otherPhoneRaw = asText(body.phone || body.client_phone);
const otherPhone = normalizePhone(otherPhoneRaw);

const phoneTarget = explicitPhone || currentCallPhone || otherPhone;
const phoneTargetRaw = explicitPhone ? explicitPhoneRaw : (currentCallPhone ? currentCallNumber : otherPhoneRaw);

const clientName = asText(body.client_name || body.contact_name);
const companyName = asText(body.company_name) || 'LipoLong';
const product = asText(body.product) || 'LipoLong';
const materialUrl = asText(body.material_url);
const callbackAt = asText(body.callback_at || body.next_call_at);
const replyPhone = normalizePhone(asText(body.reply_phone || body.manager_phone)) || '+79923298897';
const rawMessageIntent = asText(body.message_intent).toLowerCase() || 'short_info';
const messageIntent = rawMessageIntent === 'offer' ? 'product_intro' : rawMessageIntent;
const customSmsText = normalizeMultiline(body.sms_text);
const requestId = asText(body.request_id || body.tool_call_id || body.tool_request_id || body.session_id || body.conversation_id) || `smslog.${Date.now()}`;

const contactPackText = normalizeMultiline(`
Отправляю контакты наших менеджеров для связи и консультации по направлению LipoLong:
Телефон: 8 999 556-67-77
Telegram: @Vorgesar_Peptides
Messenger Max: @Vorgesar_Peptides
Сайт: lipolong.com
Чаты Telegram: @MadCoreChat / @Peptides_shop / @vl26g_official / @Zhirotop_Shop
Условия оплаты: безналичный расчёт +6%
Реквизиты: ИП Клочков Сергей Александрович, ИНН 645308371993
`);

const productIntroText = normalizeMultiline(`
Коротко про LipoLong:
Липолитик для косметологической практики по направлению коррекции фигуры.
Почему его часто смотрят: мягкая и управляемая работа, понятный вход в направление, заказ от 1 шт.
Ориентир по стоимости: от 19 000 руб.
Доставка: 3-4 дня. Оплата: безнал +6%, полная предоплата.
Для консультации с менеджером: 8 999 556-67-77, Telegram/MAX @Vorgesar_Peptides, lipolong.com
`);

const buildTemplate = () => {
  if (messageIntent === 'callback_confirmation') {
    return normalizeMultiline(`
Информацию отправила SMS.
${callbackAt ? `Если удобно, свяжемся ${callbackAt}.` : ''}
${replyPhone ? `Контакт для связи: ${replyPhone}` : ''}
`);
  }
  if (messageIntent === 'product_intro') {
    return productIntroText;
  }
  return contactPackText;
};

const initialSmsText = customSmsText || buildTemplate();
const smsText = initialSmsText.length > 480
  ? `${initialSmsText.slice(0, 477).trim()}...`
  : initialSmsText;

const dryRun = asBool(body.dry_run);
const logDryRun = asBool(body.log_dry_run);
const warnings = [];
const errors = [];
if (!phoneTarget) errors.push('phone_target is empty or invalid');
if (!smsText) errors.push('sms_text is empty after normalization');
if (materialUrl && !/^https?:\/\//i.test(materialUrl)) warnings.push('material_url does not look like http/https');
if (!explicitPhone && currentCallPhone) warnings.push('phone_target not provided explicitly, used current_call_number fallback');
if (explicitPhoneRaw && !explicitPhone && currentCallPhone) warnings.push('explicit phone_target invalid, used current_call_number fallback');
if (rawMessageIntent === 'offer') warnings.push('message_intent offer mapped to product_intro for backward compatibility');
if (dryRun) warnings.push('dry_run enabled: Mango SMS will not be sent');
if (logDryRun) warnings.push('log_dry_run enabled: Google Sheet append will not run');

return [{
  received_at: nowIso,
  tool: 'send_sms_and_log',
  ok_to_send: errors.length === 0 && !dryRun,
  dry_run: dryRun,
  log_dry_run: logDryRun,
  errors,
  warnings,
  request_id: requestId,
  session_id: asText(body.session_id),
  conversation_id: asText(body.conversation_id || body.eleven_conv_id),
  lead_id: asText(body.lead_id || body.client_ref || body.source_record_key),
  client_name: clientName,
  company_name: companyName,
  product,
  material_url: materialUrl,
  callback_at: callbackAt,
  current_call_number: currentCallNumber,
  phone_target: phoneTarget,
  phone_target_raw: phoneTargetRaw,
  reply_phone: replyPhone,
  message_intent: messageIntent,
  sms_text: smsText,
  sms_length: smsText.length,
  source_payload: body,
}];"""


BUILD_SMS_COMMAND_JS = r"""const req = $json || {};
const warningBase = [ ...(req.warnings || []), ...(req.errors || []) ].filter(Boolean).join('; ');

if (req.dry_run) {
  return [{
    ...req,
    should_send: false,
    provider: 'mango_sms',
    status: 'dry_run',
    warning: warningBase,
  }];
}

if (!req.ok_to_send) {
  return [{
    ...req,
    should_send: false,
    provider: 'mango_sms',
    status: 'invalid_request',
    warning: warningBase,
  }];
}

const apiKey = String($env.MANGO_VPBX_API_KEY || '').trim();
const apiSalt = String($env.MANGO_VPBX_API_SALT || '').trim();
const fromExtension = String($env.MANGO_VPBX_FROM_EXTENSION || '').trim();
const smsSender = String($env.MANGO_SMS_SENDER || '').trim();

const missing = [];
if (!apiKey) missing.push('MANGO_VPBX_API_KEY');
if (!apiSalt) missing.push('MANGO_VPBX_API_SALT');
if (!fromExtension) missing.push('MANGO_VPBX_FROM_EXTENSION');

if (missing.length) {
  return [{
    ...req,
    should_send: false,
    provider: 'mango_sms',
    status: 'config_error',
    warning: [warningBase, `Missing env: ${missing.join(', ')}`].filter(Boolean).join('; '),
  }];
}

const payload = {
  command_id: req.request_id || `cmd.sms.${Date.now()}`,
  from_extension: fromExtension,
  text: String(req.sms_text || ''),
  to_number: String(req.phone_target || '').replace(/^\+/, ''),
  sms_sender: smsSender,
};
const jsonPayload = JSON.stringify(payload);
return [{
  ...req,
  should_send: true,
  provider: 'mango_sms',
  provider_command: payload,
  api_key: apiKey,
  sign_source: `${apiKey}${jsonPayload}${apiSalt}`,
  json_payload: jsonPayload,
  warning: warningBase,
}];"""


BUILD_SMS_PROVIDER_RESPONSE_JS = r"""const req = $('Mango | Build SMS Request').item.json || {};
const providerResponse = $json || {};
const hasNumericResult = providerResponse.result !== undefined && providerResponse.result !== null && providerResponse.result !== '' && !Number.isNaN(Number(providerResponse.result));
const numericResult = hasNumericResult ? Number(providerResponse.result) : null;
const hasExplicitError = Boolean(providerResponse.error_code || providerResponse.error || providerResponse.message);
const looksAccepted = !hasExplicitError && (!hasNumericResult || numericResult >= 1000);
const fail = !looksAccepted;
const warning = [req.warning || '', fail ? JSON.stringify(providerResponse).slice(0, 300) : ''].filter(Boolean).join('; ');

return [{
  ok: !fail,
  tool: 'send_sms_and_log',
  sms_status: fail ? 'send_error' : 'sent',
  provider: 'mango_sms',
  request_id: req.request_id || '',
  lead_id: req.lead_id || '',
  conversation_id: req.conversation_id || '',
  phone_target: req.phone_target || '',
  sms_length: req.sms_length || 0,
  message_intent: req.message_intent || '',
  sms_preview: req.sms_text || '',
  warning,
  provider_response: JSON.stringify(providerResponse).slice(0, 500),
  source_payload: req.source_payload || {},
  log_dry_run: !!req.log_dry_run,
  received_at: req.received_at || '',
}];"""


BUILD_SMS_SKIP_RESPONSE_JS = r"""return [{
  ok: false,
  tool: 'send_sms_and_log',
  sms_status: $json.status || 'invalid_request',
  provider: 'mango_sms',
  request_id: $json.request_id || '',
  lead_id: $json.lead_id || '',
  conversation_id: $json.conversation_id || '',
  phone_target: $json.phone_target || '',
  sms_length: $json.sms_length || 0,
  message_intent: $json.message_intent || '',
  sms_preview: $json.sms_text || '',
  warning: $json.warning || '',
  provider_response: '',
  source_payload: $json.source_payload || {},
  log_dry_run: !!$json.log_dry_run,
  received_at: $json.received_at || '',
}];"""


BUILD_CALL_LOG_ROW_JS = r"""const sms = $json || {};
const body = sms.source_payload || {};
const nowIso = new Date().toISOString();
const placeholderValues = new Set([
  'system__called_number',
  'system__conversation_id',
  'system__caller_id',
  '{{lead_id}}',
  '{{caller}}',
  '{{phone_primary}}',
  '{{source_record_key}}',
  '{{eleven_conv_id}}',
  '{{conversation_id}}',
  '{{company_name}}',
  '{{contact_name}}',
  '{{request_id}}',
]);

const asText = (v) => {
  if (v === null || v === undefined) return '';
  const s = String(v).trim();
  return placeholderValues.has(s) ? '' : s;
};

const asBoolText = (v) => {
  if (typeof v === 'boolean') return v ? 'true' : 'false';
  const s = asText(v).toLowerCase();
  if (!s) return '';
  if (['1','true','yes','да'].includes(s)) return 'true';
  if (['0','false','no','нет'].includes(s)) return 'false';
  return s;
};

const numText = (v, def='') => {
  if (v === null || v === undefined || v === '') return def;
  const n = Number(v);
  return Number.isFinite(n) ? String(n) : def;
};

const isMalformedConvId = (value) => {
  const s = asText(value);
  if (!s) return true;
  if (!s.startsWith('conv_')) return true;
  const suffix = s.slice(5);
  if (suffix.length < 12) return true;
  if (/^\d+$/.test(suffix)) return true;
  if (/^(?:[0-9a-f]{2}){8,}$/i.test(suffix)) return true;
  return false;
};

const normalizeConvId = (...values) => {
  for (const value of values) {
    const s = asText(value);
    if (!s) continue;
    if (!isMalformedConvId(s)) return s;
  }
  return '';
};

const caller = asText(body.caller) || asText(body.phone_primary) || asText(sms.phone_target);
const phonePrimary = asText(body.phone_primary) || caller || asText(sms.phone_target);
const conversationId = normalizeConvId(body.conversation_id, sms.conversation_id);
const elevenConvId = normalizeConvId(body.eleven_conv_id, conversationId);
const sourceRecordKey = asText(body.source_record_key)
  || asText(body.request_id)
  || asText(sms.request_id)
  || conversationId
  || elevenConvId
  || phonePrimary
  || asText(body.session_id);
const leadId = asText(body.lead_id)
  || asText(body.client_ref)
  || asText(sms.lead_id)
  || sourceRecordKey
  || phonePrimary
  || asText(body.session_id);

const callResult = asText(body.call_result) || (sms.ok ? 'send_kp_pending_callback' : 'refusal_soft');
const nextStep = asText(body.next_step) || (sms.ok ? 'callback' : 'manual_review');
const notesBase = asText(body.notes_short)
  || (sms.ok
    ? 'Клиент согласился получить SMS, SMS отправлена, нужен дальнейший контакт менеджера.'
    : `Клиент согласился получить SMS, но отправка не подтверждена: ${sms.sms_status || 'unknown'}.`);

const row = {
  created_at: asText(body.created_at) || nowIso,
  updated_at: nowIso,
  lead_id: leadId,
  source_system: asText(body.source_system) || 'elevenlabs',
  source_record_key: sourceRecordKey,
  company_name: asText(body.company_name),
  contact_name: asText(body.contact_name || body.client_name),
  phone_primary: phonePrimary,
  phone_secondary: asText(body.phone_secondary),
  city: asText(body.city),
  segment: asText(body.segment),
  lpr_role: asText(body.lpr_role),
  lpr_confirmed: asBoolText(body.lpr_confirmed),
  current_supplier: asText(body.current_supplier),
  current_product: asText(body.current_product),
  current_price: asText(body.current_price),
  pain_points: asText(body.pain_points),
  objection_code: asText(body.objection_code),
  objection_text: asText(body.objection_text),
  interest_level: asText(body.interest_level),
  call_result: callResult,
  next_step: nextStep,
  next_call_at: asText(body.next_call_at || body.callback_at),
  preferred_channel: asText(body.preferred_channel) || 'sms',
  manager_owner: asText(body.manager_owner),
  expected_volume: asText(body.expected_volume),
  expected_budget: asText(body.expected_budget),
  material_sent: asBoolText(body.material_sent || sms.ok),
  followup_count: numText(body.followup_count, '0'),
  max_touch_limit: numText(body.max_touch_limit, ''),
  do_not_call: asBoolText(body.do_not_call),
  final_reason: asText(body.final_reason) || (sms.ok ? 'sms_sent' : `sms_${sms.sms_status || 'error'}`),
  notes_short: notesBase,
  notes_redacted: asText(body.notes_redacted),
  call_record_url: asText(body.call_record_url),
  eleven_conv_id: elevenConvId,
  n8n_execution_id: asText(body.n8n_execution_id) || asText(body.execution_id),
  agent_version: asText(body.agent_version),
  last_updated_by: asText(body.last_updated_by) || 'ai_agent_lab_fastpath',
};

const row_values = [
  row.created_at,
  row.updated_at,
  row.lead_id,
  row.source_system,
  row.source_record_key,
  row.company_name,
  row.contact_name,
  row.phone_primary,
  row.phone_secondary,
  row.city,
  row.segment,
  row.lpr_role,
  row.lpr_confirmed,
  row.current_supplier,
  row.current_product,
  row.current_price,
  row.pain_points,
  row.objection_code,
  row.objection_text,
  row.interest_level,
  row.call_result,
  row.next_step,
  row.next_call_at,
  row.preferred_channel,
  row.manager_owner,
  row.expected_volume,
  row.expected_budget,
  row.material_sent,
  row.followup_count,
  row.max_touch_limit,
  row.do_not_call,
  row.final_reason,
  row.notes_short,
  row.notes_redacted,
  row.call_record_url,
  row.eleven_conv_id,
  row.n8n_execution_id,
  row.agent_version,
  row.last_updated_by,
];

return [{
  sms_result: sms,
  row,
  row_values,
  source_payload: body,
  log_dry_run: !!sms.log_dry_run,
  identity_seed: {
    lead_id: row.lead_id,
    caller,
    phone_primary: row.phone_primary,
    source_record_key: row.source_record_key,
    eleven_conv_id: row.eleven_conv_id,
  },
}];"""


VALIDATE_IDENTITY_JS = r"""const payload = $json || {};
const row = payload.row || {};
const sourcePayload = payload.source_payload || {};
const sourceSystem = String(row.source_system || sourcePayload.source_system || 'elevenlabs').trim() || 'elevenlabs';

const identitySnapshot = {
  lead_id: String(row.lead_id || '').trim(),
  caller: String(sourcePayload.caller || row.phone_primary || '').trim(),
  phone_primary: String(row.phone_primary || '').trim(),
  source_record_key: String(row.source_record_key || '').trim(),
  eleven_conv_id: String(row.eleven_conv_id || '').trim(),
};

const requiredFields = sourceSystem === 'autodial_dispatcher'
  ? ['lead_id', 'phone_primary', 'source_record_key']
  : ['lead_id', 'caller', 'phone_primary', 'source_record_key', 'eleven_conv_id'];

const missingIdentityFields = requiredFields.filter((field) => !identitySnapshot[field]);

return [{
  ...payload,
  source_system: sourceSystem,
  identity_ok: missingIdentityFields.length === 0,
  required_identity_fields: requiredFields,
  missing_identity_fields: missingIdentityFields,
  identity_snapshot: identitySnapshot,
}];"""


BUILD_GOOGLE_PAYLOAD_JS = r"""return [{
  spreadsheet_id: '1SyoGWXrvLNevGzjWQjfSP7eRqVCMOzR0MzXeWSL7HOo',
  sheet_name: 'Лиды_обзвон',
  range_encoded: '%D0%9B%D0%B8%D0%B4%D1%8B_%D0%BE%D0%B1%D0%B7%D0%B2%D0%BE%D0%BD%21A%3AAM',
  append_url: 'https://sheets.googleapis.com/v4/spreadsheets/1SyoGWXrvLNevGzjWQjfSP7eRqVCMOzR0MzXeWSL7HOo/values/%D0%9B%D0%B8%D0%B4%D1%8B_%D0%BE%D0%B1%D0%B7%D0%B2%D0%BE%D0%BD%21A%3AAM:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS',
  oauth_url: 'https://oauth2.googleapis.com/token',
  google_oauth_source: 'env',
}];"""


BUILD_COMBINED_RESPONSE_JS = r"""let payload = {};
try {
  payload = $node['Tool | Validate Identity'].json || {};
} catch (e) {
  payload = $json || {};
}

const row = payload.row || {};
const sms = payload.sms_result || {};
let tokenRes = {};
let append = {};
try { tokenRes = $node['Google | Refresh Access Token'].json || {}; } catch (e) {}
try { append = $node['Google | Append Row'].json || {}; } catch (e) {}

const tokenError = tokenRes.error || tokenRes.error_description || '';
const appendError = append.error?.message || append.error || '';
const identityOk = payload.identity_ok !== false;
const logSkippedDryRun = !!payload.log_dry_run;
const logOk = identityOk && (logSkippedDryRun || (!tokenError && !appendError));
const warnings = [
  sms.warning || '',
  identityOk ? '' : `missing_identity_package: ${(payload.missing_identity_fields || []).join(', ')}`,
  logSkippedDryRun ? 'log_dry_run enabled: Google append skipped' : '',
  tokenError || appendError || '',
].filter(Boolean).join('; ');

return [{
  ok: Boolean(sms.ok) && logOk,
  tool: 'send_sms_and_log',
  sms: {
    ok: Boolean(sms.ok),
    status: sms.sms_status || '',
    provider: sms.provider || '',
    request_id: sms.request_id || '',
    phone_target: sms.phone_target || '',
    message_intent: sms.message_intent || '',
    sms_length: sms.sms_length || 0,
  },
  call_log: {
    ok: logOk,
    skipped_dry_run: logSkippedDryRun,
    source: logSkippedDryRun ? 'dry_run' : (logOk ? 'google_sheets' : 'error'),
    spreadsheet_id: '1SyoGWXrvLNevGzjWQjfSP7eRqVCMOzR0MzXeWSL7HOo',
    updated_range: append.updates?.updatedRange || '',
    updated_rows: append.updates?.updatedRows ?? 0,
    missing_identity_fields: payload.missing_identity_fields || [],
    identity_snapshot: payload.identity_snapshot || {},
  },
  warning: warnings,
  lead_id: row.lead_id || '',
  source_record_key: row.source_record_key || '',
  phone_primary: row.phone_primary || '',
  eleven_conv_id: row.eleven_conv_id || '',
  call_result: row.call_result || '',
  next_step: row.next_step || '',
  next_call_at: row.next_call_at || '',
}];"""


def switch_rule(left_expr: str, right_value: str, output_key: str) -> dict[str, Any]:
    return {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
            "conditions": [
                {
                    "leftValue": left_expr,
                    "rightValue": right_value,
                    "operator": {"type": "string", "operation": "equals"},
                }
            ],
            "combinator": "and",
        },
        "renameOutput": True,
        "outputKey": output_key,
    }


def build_workflow() -> dict[str, Any]:
    nodes = [
        node(
            "Tool | Webhook Send SMS And Log",
            "n8n-nodes-base.webhook",
            {"httpMethod": "POST", "path": "eleven/tool/send-sms-and-log", "responseMode": "responseNode", "options": {}},
            [-1088, 256],
            webhook_id="f3a07206-11d4-4520-8c40-a21f8d4e16db",
        ),
        node("Tool | Normalize SMS+Log Request", "n8n-nodes-base.code", {"jsCode": NORMALIZE_SMS_JS}, [-832, 256]),
        node("Mango | Build SMS Command", "n8n-nodes-base.code", {"jsCode": BUILD_SMS_COMMAND_JS}, [-576, 256]),
        node(
            "Mango | Send Decision",
            "n8n-nodes-base.switch",
            {
                "rules": {
                    "values": [
                        switch_rule("={{ $json.should_send ? 'send' : 'skip' }}", "send", "Send"),
                        switch_rule("={{ $json.should_send ? 'send' : 'skip' }}", "skip", "Skip"),
                    ]
                },
                "options": {},
            },
            [-320, 256],
            type_version=3.2,
        ),
        node(
            "Mango | Sign SMS SHA256",
            "n8n-nodes-base.crypto",
            {"type": "SHA256", "value": "={{ $json.sign_source }}", "dataPropertyName": "sign"},
            [-64, 144],
            type_version=1,
        ),
        node("Mango | Build SMS Request", "n8n-nodes-base.code", {"jsCode": "return [{\n  ...$json,\n  sign: String($json.sign || '').toLowerCase(),\n}];"}, [192, 144]),
        node(
            "Mango | Send SMS HTTP",
            "n8n-nodes-base.httpRequest",
            {
                "method": "POST",
                "url": "https://app.mango-office.ru/vpbx/commands/sms",
                "sendBody": True,
                "contentType": "form-urlencoded",
                "bodyParameters": {
                    "parameters": [
                        {"name": "vpbx_api_key", "value": "={{ $json.api_key }}"},
                        {"name": "sign", "value": "={{ $json.sign }}"},
                        {"name": "json", "value": "={{ $json.json_payload }}"},
                    ]
                },
                "options": {"response": {"response": {"neverError": True}}},
            },
            [448, 144],
            type_version=4.2,
        ),
        node("Tool | Build SMS Provider Response", "n8n-nodes-base.code", {"jsCode": BUILD_SMS_PROVIDER_RESPONSE_JS}, [704, 144]),
        node("Tool | Build SMS Skip Response", "n8n-nodes-base.code", {"jsCode": BUILD_SMS_SKIP_RESPONSE_JS}, [704, 368]),
        node("Tool | Build Call Log Row", "n8n-nodes-base.code", {"jsCode": BUILD_CALL_LOG_ROW_JS}, [960, 256]),
        node("Tool | Validate Identity", "n8n-nodes-base.code", {"jsCode": VALIDATE_IDENTITY_JS}, [1216, 256]),
        node(
            "Tool | Log Decision",
            "n8n-nodes-base.switch",
            {
                "rules": {
                    "values": [
                        switch_rule("={{ ($json.identity_ok && !$json.log_dry_run) ? 'append' : 'skip' }}", "append", "Append"),
                        switch_rule("={{ ($json.identity_ok && !$json.log_dry_run) ? 'append' : 'skip' }}", "skip", "Skip"),
                    ]
                },
                "options": {},
            },
            [1472, 256],
            type_version=3.2,
        ),
        node("Google | Build Payload", "n8n-nodes-base.code", {"jsCode": BUILD_GOOGLE_PAYLOAD_JS}, [1728, 144]),
        node(
            "Google | Refresh Access Token",
            "n8n-nodes-base.httpRequest",
            {
                "method": "POST",
                "url": "={{ $node[\"Google | Build Payload\"].json.oauth_url }}",
                "sendBody": True,
                "contentType": "form-urlencoded",
                "bodyParameters": {
                    "parameters": [
                        {"name": "client_id", "value": "={{ $env.GOOGLE_CLIENT_ID || \"\" }}"},
                        {"name": "client_secret", "value": "={{ $env.GOOGLE_CLIENT_SECRET || \"\" }}"},
                        {"name": "refresh_token", "value": "={{ $env.GOOGLE_REFRESH_TOKEN || \"\" }}"},
                        {"name": "grant_type", "value": "refresh_token"},
                    ]
                },
                "options": {"response": {"response": {"neverError": True}}},
            },
            [1984, 144],
            type_version=4.2,
        ),
        node(
            "Google | Append Row",
            "n8n-nodes-base.httpRequest",
            {
                "method": "POST",
                "url": "={{ $node[\"Google | Build Payload\"].json[\"append_url\"] }}",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "Authorization", "value": "={{ \"Bearer \" + ($node[\"Google | Refresh Access Token\"].json[\"access_token\"] || \"\") }}"},
                        {"name": "Content-Type", "value": "application/json"},
                    ]
                },
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ {\"majorDimension\":\"ROWS\",\"values\":[ $node[\"Tool | Build Call Log Row\"].json[\"row_values\"] ] } }}",
                "options": {"response": {"response": {"neverError": True}}},
            },
            [2240, 144],
            type_version=4.2,
        ),
        node("Tool | Build Combined Response", "n8n-nodes-base.code", {"jsCode": BUILD_COMBINED_RESPONSE_JS}, [2496, 256]),
        node(
            "Tool | Respond Send SMS And Log",
            "n8n-nodes-base.respondToWebhook",
            {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}},
            [2752, 256],
            type_version=1.1,
        ),
    ]

    connections = {
        "Tool | Webhook Send SMS And Log": {"main": [[{"node": "Tool | Normalize SMS+Log Request", "type": "main", "index": 0}]]},
        "Tool | Normalize SMS+Log Request": {"main": [[{"node": "Mango | Build SMS Command", "type": "main", "index": 0}]]},
        "Mango | Build SMS Command": {"main": [[{"node": "Mango | Send Decision", "type": "main", "index": 0}]]},
        "Mango | Send Decision": {
            "main": [
                [{"node": "Mango | Sign SMS SHA256", "type": "main", "index": 0}],
                [{"node": "Tool | Build SMS Skip Response", "type": "main", "index": 0}],
            ]
        },
        "Mango | Sign SMS SHA256": {"main": [[{"node": "Mango | Build SMS Request", "type": "main", "index": 0}]]},
        "Mango | Build SMS Request": {"main": [[{"node": "Mango | Send SMS HTTP", "type": "main", "index": 0}]]},
        "Mango | Send SMS HTTP": {"main": [[{"node": "Tool | Build SMS Provider Response", "type": "main", "index": 0}]]},
        "Tool | Build SMS Provider Response": {"main": [[{"node": "Tool | Build Call Log Row", "type": "main", "index": 0}]]},
        "Tool | Build SMS Skip Response": {"main": [[{"node": "Tool | Build Call Log Row", "type": "main", "index": 0}]]},
        "Tool | Build Call Log Row": {"main": [[{"node": "Tool | Validate Identity", "type": "main", "index": 0}]]},
        "Tool | Validate Identity": {"main": [[{"node": "Tool | Log Decision", "type": "main", "index": 0}]]},
        "Tool | Log Decision": {
            "main": [
                [{"node": "Google | Build Payload", "type": "main", "index": 0}],
                [{"node": "Tool | Build Combined Response", "type": "main", "index": 0}],
            ]
        },
        "Google | Build Payload": {"main": [[{"node": "Google | Refresh Access Token", "type": "main", "index": 0}]]},
        "Google | Refresh Access Token": {"main": [[{"node": "Google | Append Row", "type": "main", "index": 0}]]},
        "Google | Append Row": {"main": [[{"node": "Tool | Build Combined Response", "type": "main", "index": 0}]]},
        "Tool | Build Combined Response": {"main": [[{"node": "Tool | Respond Send SMS And Log", "type": "main", "index": 0}]]},
    }

    return {
        "name": "ELEVEN_TOOL_SEND_SMS_AND_LOG_BRIDGE_LAB",
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1", "callerPolicy": "workflowsFromSameOwner", "availableInMCP": False},
    }


def main() -> None:
    workflow = build_workflow()
    OUTPUT_PATH.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
