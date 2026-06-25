#!/usr/bin/env python3
import json
import sys
from pathlib import Path


PARSE_REQUEST_JS = r"""const body = ($json.body && typeof $json.body === 'object') ? $json.body : ($json.body ?? $json);
const source = (body && typeof body === 'object' && !Array.isArray(body)) ? { ...body } : {};

const toNumber = String(source.to_number ?? source.to ?? '').trim();
const firstMessage = String(source.first_message ?? '').trim();
const dynamicContext = String(source.context ?? '').trim();

const providedClientData = (
  source.conversation_initiation_client_data &&
  typeof source.conversation_initiation_client_data === 'object' &&
  !Array.isArray(source.conversation_initiation_client_data)
) ? { ...source.conversation_initiation_client_data } : {};

const providedDynamicVariables = (
  providedClientData.dynamic_variables &&
  typeof providedClientData.dynamic_variables === 'object' &&
  !Array.isArray(providedClientData.dynamic_variables)
) ? { ...providedClientData.dynamic_variables } : {};

const fallbackLeadId = String(source.source_record_key ?? source.lead_id ?? source.client_ref ?? toNumber).trim();
const fallbackCaller = String(source.phone_primary ?? toNumber).trim();
const normalizedUserId = String(providedClientData.user_id ?? fallbackLeadId).trim();
const normalizedBranchId = String(providedClientData.branch_id ?? source.branch_id ?? '').trim();
const normalizedEnvironment = String(providedClientData.environment ?? source.environment ?? '').trim();

return [{
  ...source,
  to_number: toNumber,
  first_message: firstMessage,
  context: dynamicContext,
  agent_id_override: String(source.agent_id_override ?? source.agent_id ?? '').trim(),
  agent_phone_number_id_override: String(source.agent_phone_number_id_override ?? source.agent_phone_number_id ?? '').trim(),
  branch_id: normalizedBranchId,
  environment: normalizedEnvironment,
  conversation_initiation_client_data: {
    ...providedClientData,
    type: 'conversation_initiation_client_data',
    user_id: normalizedUserId,
    ...(normalizedBranchId ? { branch_id: normalizedBranchId } : {}),
    ...(normalizedEnvironment ? { environment: normalizedEnvironment } : {}),
    dynamic_variables: {
      ...providedDynamicVariables,
      lead_id: String(providedDynamicVariables.lead_id ?? fallbackLeadId).trim(),
      caller: String(providedDynamicVariables.caller ?? fallbackCaller).trim(),
      phone_primary: String(providedDynamicVariables.phone_primary ?? fallbackCaller).trim(),
      source_record_key: String(providedDynamicVariables.source_record_key ?? fallbackLeadId).trim(),
      company_name: String(providedDynamicVariables.company_name ?? source.company_name ?? '').trim(),
      contact_name: String(providedDynamicVariables.contact_name ?? source.contact_name ?? '').trim(),
      request_id: String(providedDynamicVariables.request_id ?? source.request_id ?? '').trim(),
      campaign_key: String(providedDynamicVariables.campaign_key ?? source.campaign_key ?? '').trim(),
      sheet_row_number: String(providedDynamicVariables.sheet_row_number ?? source.sheet_row_number ?? '').trim(),
    },
  },
}];"""


OUTBOUND_HTTP_JSON = r"""={{ (() => {
const baseClientData = ($json.conversation_initiation_client_data && typeof $json.conversation_initiation_client_data === 'object')
  ? $json.conversation_initiation_client_data
  : {};
const baseDynamicVariables = (baseClientData.dynamic_variables && typeof baseClientData.dynamic_variables === 'object')
  ? baseClientData.dynamic_variables
  : {};

const fallbackLeadId = String($json.source_record_key || $json.lead_id || $json.client_ref || $json.to_number || '').trim();
const fallbackCaller = String($json.phone_primary || $json.to_number || '').trim();
const branchId = String(baseClientData.branch_id || $json.branch_id || '').trim();
const environment = String(baseClientData.environment || $json.environment || '').trim();

return {
  agent_id: String($json.agent_id || '').trim(),
  agent_phone_number_id: String($json.agent_phone_number_id || '').trim(),
  to_number: String($json.to_number || '').trim(),
  conversation_initiation_client_data: {
    ...baseClientData,
    type: 'conversation_initiation_client_data',
    user_id: String(baseClientData.user_id || fallbackLeadId).trim(),
    ...(branchId ? { branch_id: branchId } : {}),
    ...(environment ? { environment: environment } : {}),
    dynamic_variables: {
      ...baseDynamicVariables,
      lead_id: String(baseDynamicVariables.lead_id || fallbackLeadId).trim(),
      caller: String(baseDynamicVariables.caller || fallbackCaller).trim(),
      phone_primary: String(baseDynamicVariables.phone_primary || fallbackCaller).trim(),
      source_record_key: String(baseDynamicVariables.source_record_key || fallbackLeadId).trim(),
      company_name: String(baseDynamicVariables.company_name || $json.company_name || '').trim(),
      contact_name: String(baseDynamicVariables.contact_name || $json.contact_name || '').trim(),
      request_id: String(baseDynamicVariables.request_id || $json.request_id || '').trim(),
      campaign_key: String(baseDynamicVariables.campaign_key || $json.campaign_key || '').trim(),
      sheet_row_number: String(baseDynamicVariables.sheet_row_number || $json.sheet_row_number || '').trim(),
    },
  },
};
})() }}"""


SUCCESS_RESPONSE_JS = r"""const raw = Object.prototype.hasOwnProperty.call($json, 'data') ? $json.data : $json;
const text = typeof raw === 'string' ? raw : JSON.stringify(raw ?? {});
const lower = text.toLowerCase();
const looksLikeHtml = lower.includes('<!doctype html') || lower.includes('<html') || lower.includes('just a moment') || lower.includes('help.elevenlabs.io') || lower.includes('cloudflare');
const parsed = typeof raw === 'object' && raw !== null ? raw : null;
const explicitFailure = parsed && parsed.success === false;
const explicitError = parsed && (parsed.error || parsed.detail || (explicitFailure ? parsed.message : ''));
const acceptedConversationId = String(parsed?.conversation_id ?? parsed?.id ?? '').trim();
const acceptedSipCallId = String(parsed?.sip_call_id ?? parsed?.callSid ?? parsed?.call_id ?? '').trim();
const requestJson = $('Eleven | Validate Request').item.json;
const requestClientData = (
  requestJson.conversation_initiation_client_data &&
  typeof requestJson.conversation_initiation_client_data === 'object'
) ? requestJson.conversation_initiation_client_data : {};

const hasAcceptedPayload = parsed && !explicitFailure && (
  parsed.success === true ||
  acceptedConversationId ||
  acceptedSipCallId ||
  parsed.status === 'queued' ||
  parsed.status === 'initiated' ||
  parsed.status === 'in_progress'
);

if (looksLikeHtml || explicitFailure || !hasAcceptedPayload) {
  return [{
    ok: false,
    success: false,
    action: 'provider_rejected',
    to_number: String(requestJson.to_number ?? ''),
    agent_id: String(requestJson.agent_id ?? ''),
    agent_phone_number_id: String(requestJson.agent_phone_number_id ?? ''),
    user_id: String(requestClientData.user_id ?? ''),
    branch_id: String(requestClientData.branch_id ?? requestJson.branch_id ?? ''),
    environment: String(requestClientData.environment ?? requestJson.environment ?? ''),
    eleven_response: parsed ?? $json,
    note: looksLikeHtml
      ? 'ElevenLabs returned an HTML challenge or block page instead of API JSON.'
      : String(explicitError || 'ElevenLabs did not return an accepted outbound-call payload.'),
  }];
}

return [{
  ok: true,
  success: true,
  action: 'call_requested',
  to_number: String(requestJson.to_number ?? ''),
  agent_id: String(requestJson.agent_id ?? ''),
  agent_phone_number_id: String(requestJson.agent_phone_number_id ?? ''),
  user_id: String(requestClientData.user_id ?? ''),
  branch_id: String(requestClientData.branch_id ?? requestJson.branch_id ?? ''),
  environment: String(requestClientData.environment ?? requestJson.environment ?? ''),
  conversation_id: acceptedConversationId,
  sip_call_id: acceptedSipCallId,
  eleven_response: parsed ?? $json,
  note: 'Запрос на исходящий звонок отправлен в ElevenLabs.',
}];"""


def usage() -> None:
    print(
        "Usage: prepare_eleven_outbound_call_bridge_branch_fix.py INPUT_JSON OUTPUT_JSON",
        file=sys.stderr,
    )
    raise SystemExit(1)


def main() -> None:
    if len(sys.argv) != 3:
        usage()

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    data = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise SystemExit("Expected exported workflow JSON array with one workflow object")

    workflow = data[0]
    nodes = workflow.get("nodes", [])
    by_name = {node.get("name"): node for node in nodes}

    required = [
        "Eleven | Parse Request",
        "Eleven | Outbound HTTP",
        "Eleven | Build Success Response",
    ]
    missing = [name for name in required if name not in by_name]
    if missing:
        raise SystemExit(f"Missing expected nodes: {', '.join(missing)}")

    by_name["Eleven | Parse Request"]["parameters"]["jsCode"] = PARSE_REQUEST_JS
    by_name["Eleven | Outbound HTTP"]["parameters"]["jsonBody"] = OUTBOUND_HTTP_JSON
    by_name["Eleven | Build Success Response"]["parameters"]["jsCode"] = SUCCESS_RESPONSE_JS

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(dst)


if __name__ == "__main__":
    main()
