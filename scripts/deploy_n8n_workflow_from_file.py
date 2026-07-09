#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any

import requests


DEFAULT_N8N_ENV_FILE = pathlib.Path("/home/max/.config/lipolong-eleven-relay.env")
DEFAULT_N8N_BASE_URL = "https://www.n-8-n.site"


def load_n8n_api_key(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^N8N_API_KEY=(.+)$", text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not find N8N_API_KEY in {path}")
    return match.group(1).strip()


def api_session(env_file: pathlib.Path) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "X-N8N-API-KEY": load_n8n_api_key(env_file),
            "Content-Type": "application/json",
        }
    )
    return session


def find_existing_workflow(session: requests.Session, base_url: str, workflow_name: str) -> dict[str, Any] | None:
    response = session.get(f"{base_url}/api/v1/workflows", timeout=60)
    response.raise_for_status()
    for item in response.json().get("data", []):
        if item.get("name") == workflow_name:
            return item
    return None


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": payload["name"],
        "nodes": payload["nodes"],
        "connections": payload["connections"],
        "settings": payload.get("settings", {}),
    }


def upsert_workflow(
    session: requests.Session,
    base_url: str,
    payload: dict[str, Any],
    *,
    activate: bool,
) -> dict[str, Any]:
    existing = find_existing_workflow(session, base_url, payload["name"])
    if existing:
        workflow_id = existing["id"]
        session.post(f"{base_url}/api/v1/workflows/{workflow_id}/deactivate", timeout=60)
        response = session.put(
            f"{base_url}/api/v1/workflows/{workflow_id}",
            data=json.dumps(sanitize_payload(payload), ensure_ascii=True),
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
    else:
        response = session.post(
            f"{base_url}/api/v1/workflows",
            data=json.dumps(sanitize_payload(payload), ensure_ascii=True),
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()

    if activate:
        activate_response = session.post(f"{base_url}/api/v1/workflows/{result['id']}/activate", timeout=60)
        activate_response.raise_for_status()
        return activate_response.json()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Upsert an n8n workflow JSON by workflow name.")
    parser.add_argument("workflow_json", type=pathlib.Path)
    parser.add_argument("--env-file", type=pathlib.Path, default=DEFAULT_N8N_ENV_FILE)
    parser.add_argument("--base-url", default=DEFAULT_N8N_BASE_URL)
    parser.add_argument("--activate", action="store_true")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    payload = json.loads(args.workflow_json.read_text(encoding="utf-8"))
    session = api_session(args.env_file)
    result = upsert_workflow(session, args.base_url.rstrip("/"), payload, activate=args.activate)

    summary = {
        "id": result.get("id"),
        "name": result.get("name"),
        "active": result.get("active"),
        "versionId": result.get("versionId"),
        "triggerCount": result.get("triggerCount"),
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
