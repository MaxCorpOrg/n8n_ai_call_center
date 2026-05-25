#!/usr/bin/env python3
import json
import pathlib
import uuid


REPO_ROOT = pathlib.Path("/home/max/n8n_ai_call_center")
SCHEDULED_OUT_PATH = REPO_ROOT / "workflows" / "EMAIL_FOLLOWUP_AGENT_DRAFT.json"
MANUAL_OUT_PATH = REPO_ROOT / "workflows" / "EMAIL_FOLLOWUP_AGENT_MANUAL_DRAFT.json"


def node(name, type_name, parameters, position, *, type_version=1):
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": type_name,
        "typeVersion": type_version,
        "position": position,
        "parameters": parameters,
    }


def build_scheduled_workflow():
    schedule = node(
        "Email Followup | Schedule Tick",
        "n8n-nodes-base.scheduleTrigger",
        {"rule": {"interval": [{"field": "cronExpression", "expression": "0 9,15 * * *"}]}},
        [240, 220],
    )
    build_scheduled = node(
        "Email Followup | Build Scheduled Run",
        "n8n-nodes-base.code",
        {
            "jsCode": (
                "return [{\n"
                "  run_body: {\n"
                "    dry_run: false,\n"
                "    force_resend: false,\n"
                "    limit_sheets: 100,\n"
                "    max_records: -1,\n"
                "  },\n"
                "}];"
            )
        },
        [500, 220],
        type_version=2,
    )
    run_scheduled = node(
        "Email Followup | Run Scheduled Batch",
        "n8n-nodes-base.httpRequest",
        {
            "method": "POST",
            "url": "={{ ($env.EMAIL_FOLLOWUP_URL || 'http://127.0.0.1:8791') + '/run' }}",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Authorization",
                        "value": "={{ $env.EMAIL_FOLLOWUP_AUTH_TOKEN ? 'Bearer ' + $env.EMAIL_FOLLOWUP_AUTH_TOKEN : '' }}",
                    }
                ]
            },
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ $json.run_body }}",
            "options": {"response": {"response": {"neverError": True}}},
        },
        [760, 220],
        type_version=4.2,
    )
    build_scheduled_result = node(
        "Email Followup | Build Scheduled Result",
        "n8n-nodes-base.code",
        {
            "jsCode": (
                "const body = $json.body ?? $json;\n"
                "return [{\n"
                "  ok: body.ok !== false,\n"
                "  source: 'scheduled_run',\n"
                "  spreadsheets_found: Number(body.spreadsheets_found || 0),\n"
                "  groups_seen: Number(body.groups_seen || 0),\n"
                "  records_processed: Number(body.records_processed || 0),\n"
                "  sent: Number(body.sent || 0),\n"
                "  dry_run_ready: Number(body.dry_run_ready || 0),\n"
                "  needs_review: Number(body.needs_review || 0),\n"
                "  blocked: Number(body.blocked || 0),\n"
                "  errors: Number(body.errors || 0),\n"
                "}];"
            )
        },
        [1020, 220],
        type_version=2,
    )

    workflow = {
        "name": "EMAIL_FOLLOWUP_AGENT (draft)",
        "nodes": [
            schedule,
            build_scheduled,
            run_scheduled,
            build_scheduled_result,
        ],
        "connections": {
            "Email Followup | Schedule Tick": {
                "main": [[{"node": "Email Followup | Build Scheduled Run", "type": "main", "index": 0}]]
            },
            "Email Followup | Build Scheduled Run": {
                "main": [[{"node": "Email Followup | Run Scheduled Batch", "type": "main", "index": 0}]]
            },
            "Email Followup | Run Scheduled Batch": {
                "main": [[{"node": "Email Followup | Build Scheduled Result", "type": "main", "index": 0}]]
            },
        },
        "settings": {
            "executionOrder": "v1",
            "callerPolicy": "workflowsFromSameOwner",
            "availableInMCP": False,
        },
        "active": False,
        "pinData": {},
        "versionId": str(uuid.uuid4()),
        "meta": None,
    }
    return workflow


def build_manual_workflow():
    webhook = node(
        "Email Followup | Manual Webhook",
        "n8n-nodes-base.webhook",
        {"httpMethod": "POST", "path": "email-followup-live/run", "responseMode": "responseNode", "options": {}},
        [240, 300],
        type_version=2,
    )
    webhook["webhookId"] = str(uuid.uuid4())
    normalize_manual = node(
        "Email Followup | Normalize Manual Run",
        "n8n-nodes-base.code",
        {
            "jsCode": (
                "const body = $json.body ?? $json;\n"
                "return [{\n"
                "  run_body: {\n"
                "    dry_run: !!body.dry_run,\n"
                "    force_resend: !!body.force_resend,\n"
                "    sheet_prefix: String(body.sheet_prefix || ''),\n"
                "    limit_sheets: Number(body.limit_sheets || 0),\n"
                "    max_records: Number(body.max_records || 0),\n"
                "  },\n"
                "}];"
            )
        },
        [500, 300],
        type_version=2,
    )
    run_manual = node(
        "Email Followup | Run Manual Batch",
        "n8n-nodes-base.httpRequest",
        {
            "method": "POST",
            "url": "={{ ($env.EMAIL_FOLLOWUP_URL || 'http://127.0.0.1:8791') + '/run' }}",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Authorization",
                        "value": "={{ $env.EMAIL_FOLLOWUP_AUTH_TOKEN ? 'Bearer ' + $env.EMAIL_FOLLOWUP_AUTH_TOKEN : '' }}",
                    }
                ]
            },
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ $json.run_body }}",
            "options": {"response": {"response": {"neverError": True}}},
        },
        [760, 300],
        type_version=4.2,
    )
    build_manual_result = node(
        "Email Followup | Build Manual Response",
        "n8n-nodes-base.code",
        {"jsCode": "const body = $json.body ?? $json;\nreturn [body];"},
        [1020, 300],
        type_version=2,
    )
    respond_manual = node(
        "Email Followup | Respond Manual",
        "n8n-nodes-base.respondToWebhook",
        {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}},
        [1280, 300],
        type_version=1.1,
    )

    workflow = {
        "name": "EMAIL_FOLLOWUP_AGENT_MANUAL (draft)",
        "nodes": [
            webhook,
            normalize_manual,
            run_manual,
            build_manual_result,
            respond_manual,
        ],
        "connections": {
            "Email Followup | Manual Webhook": {
                "main": [[{"node": "Email Followup | Normalize Manual Run", "type": "main", "index": 0}]]
            },
            "Email Followup | Normalize Manual Run": {
                "main": [[{"node": "Email Followup | Run Manual Batch", "type": "main", "index": 0}]]
            },
            "Email Followup | Run Manual Batch": {
                "main": [[{"node": "Email Followup | Build Manual Response", "type": "main", "index": 0}]]
            },
            "Email Followup | Build Manual Response": {
                "main": [[{"node": "Email Followup | Respond Manual", "type": "main", "index": 0}]]
            },
        },
        "settings": {
            "executionOrder": "v1",
            "callerPolicy": "workflowsFromSameOwner",
            "availableInMCP": False,
        },
        "active": False,
        "pinData": {},
        "versionId": str(uuid.uuid4()),
        "meta": None,
    }
    return workflow


def main():
    scheduled_workflow = build_scheduled_workflow()
    manual_workflow = build_manual_workflow()
    SCHEDULED_OUT_PATH.write_text(json.dumps(scheduled_workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MANUAL_OUT_PATH.write_text(json.dumps(manual_workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(SCHEDULED_OUT_PATH)
    print(MANUAL_OUT_PATH)


if __name__ == "__main__":
    raise SystemExit(main())
