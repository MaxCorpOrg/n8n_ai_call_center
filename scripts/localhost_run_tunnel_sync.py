#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path


N8N_BASE_URL = os.getenv("N8N_BASE_URL", "https://www.n-8-n.site").rstrip("/")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")
N8N_WORKFLOW_ID = os.getenv("N8N_WORKFLOW_ID", "bfNbTwtyXNSFzMc2")
TARGET_NODE_NAME = os.getenv("N8N_TARGET_NODE_NAME", "Eleven | Outbound HTTP")
RELAY_SHARED_TOKEN = os.getenv("RELAY_SHARED_TOKEN", "")
LOCAL_RELAY_PORT = os.getenv("LOCAL_RELAY_PORT", "8787")
STATE_PATH = Path(
    os.getenv(
        "LOCALHOST_RUN_STATE_PATH",
        "/home/max/.config/lipolong-eleven-relay-state.json",
    )
)


def api_request(method: str, path: str, payload=None):
    req = urllib.request.Request(
        f"{N8N_BASE_URL}{path}",
        method=method,
        headers={
            "X-N8N-API-KEY": N8N_API_KEY,
            "Content-Type": "application/json",
        },
        data=None if payload is None else json.dumps(payload).encode(),
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def patch_workflow(relay_url: str) -> None:
    workflow = api_request("GET", f"/api/v1/workflows/{N8N_WORKFLOW_ID}")
    patched = False
    for node in workflow["nodes"]:
        if node.get("name") != TARGET_NODE_NAME:
            continue
        node["parameters"]["url"] = relay_url
        header_params = node["parameters"].setdefault("headerParameters", {}).setdefault(
            "parameters", []
        )
        names = {str(item.get("name")): idx for idx, item in enumerate(header_params)}
        token_header = {"name": "X-Relay-Token", "value": RELAY_SHARED_TOKEN}
        if "X-Relay-Token" in names:
            header_params[names["X-Relay-Token"]] = token_header
        else:
            header_params.append(token_header)
        patched = True
        break

    if not patched:
        raise RuntimeError(f"Node not found: {TARGET_NODE_NAME}")

    payload = {
        "name": workflow["name"],
        "nodes": workflow["nodes"],
        "connections": workflow["connections"],
        "settings": workflow.get("settings", {}),
    }
    result = api_request("PUT", f"/api/v1/workflows/{N8N_WORKFLOW_ID}", payload)
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(
            {
                "relay_url": relay_url,
                "workflow_id": N8N_WORKFLOW_ID,
                "workflow_version_id": result.get("versionId"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(
        json.dumps(
            {
                "ok": True,
                "patched": True,
                "relay_url": relay_url,
                "workflow_id": N8N_WORKFLOW_ID,
                "workflow_version_id": result.get("versionId"),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


def main() -> None:
    if not N8N_API_KEY:
        raise SystemExit("N8N_API_KEY is required")
    if not RELAY_SHARED_TOKEN:
        raise SystemExit("RELAY_SHARED_TOKEN is required")

    cmd = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "ExitOnForwardFailure=yes",
        "-R",
        f"80:localhost:{LOCAL_RELAY_PORT}",
        "nokey@localhost.run",
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    seen = None
    pattern = re.compile(r"(https://[a-z0-9.-]+)")

    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        if "tunneled with tls termination" not in line:
            continue
        match = pattern.search(line)
        if not match:
            continue
        base = match.group(1).rstrip("/")
        relay_url = f"{base}/eleven/outbound-call"
        if relay_url == seen:
            continue
        patch_workflow(relay_url)
        seen = relay_url

    raise SystemExit(proc.wait())


if __name__ == "__main__":
    main()
