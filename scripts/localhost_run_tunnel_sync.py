#!/usr/bin/env python3
import base64
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SERVER_ALIAS = os.getenv("SERVER_ALIAS", "ai-core-prod-147")
LOCAL_RELAY_PORT = os.getenv("LOCAL_RELAY_PORT", "18787")
WORKFLOW_ID = os.getenv("N8N_WORKFLOW_ID", "sHTbALayEZdy8Mzs")
STATE_PATH = Path(
    os.getenv(
        "LOCALHOST_RUN_STATE_PATH",
        "/home/max/.config/lipolong-eleven-relay-state.json",
    )
)
REMOTE_HELPER = r"""
import base64
import json
import os
import subprocess
import sys

workflow_id = base64.b64decode(sys.argv[1]).decode()
relay_url = base64.b64decode(sys.argv[2]).decode()
target_node = base64.b64decode(sys.argv[3]).decode()

def sh(cmd):
    return subprocess.check_output(cmd, text=True).strip()

def sh_json(cmd):
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)

container_rows = sh(["docker", "ps", "--format", "{{.Names}} {{.Image}}"]).splitlines()
pg_name = ""
n8n_name = ""
for row in container_rows:
    parts = row.split(" ", 1)
    if len(parts) != 2:
        continue
    name, image = parts
    if image.startswith("postgres:") and name == "n8n-server-postgres-1":
        pg_name = name
        break
for row in container_rows:
    parts = row.split(" ", 1)
    if len(parts) != 2:
        continue
    name, image = parts
    if image.startswith("docker.n8n.io/n8nio/n8n:") and name == "n8n-server-n8n-1":
        n8n_name = name
        break
if not pg_name:
    for row in container_rows:
        parts = row.split(" ", 1)
        if len(parts) != 2:
            continue
        name, image = parts
        if image.startswith("postgres:") and "n8n-server-postgres" in name and "memory" not in name:
            pg_name = name
            break
if not pg_name:
    raise SystemExit("Could not find n8n postgres container on remote server")
if not n8n_name:
    raise SystemExit("Could not find n8n app container on remote server")

env_lines = sh(["docker", "inspect", n8n_name, "--format", "{{range .Config.Env}}{{println .}}{{end}}"]).splitlines()
env = {}
for line in env_lines:
    if "=" in line:
        k, v = line.split("=", 1)
        env[k] = v

db_name = env.get("DB_POSTGRESDB_DATABASE") or env.get("POSTGRES_DB") or "n8n_prod"
db_user = env.get("DB_POSTGRESDB_USER") or env.get("POSTGRES_USER") or "n8n"
db_pass = env.get("DB_POSTGRESDB_PASSWORD") or env.get("POSTGRES_PASSWORD") or ""

def psql(sql: str) -> str:
    cmd = ["docker", "exec"]
    if db_pass:
        cmd += ["-e", f"PGPASSWORD={db_pass}"]
    cmd += [pg_name, "psql", "-U", db_user, "-d", db_name, "-At", "-c", sql]
    return sh(cmd)

active_version = psql(f"select \"activeVersionId\" from workflow_entity where id='{workflow_id}';")
if not active_version:
    raise SystemExit(f"Workflow {workflow_id} has no activeVersionId")

entity_nodes_raw = psql(f"select nodes::text from workflow_entity where id='{workflow_id}';")
history_nodes_raw = psql(
    f"select nodes::text from workflow_history where \"workflowId\"='{workflow_id}' and \"versionId\"='{active_version}';"
)

entity_nodes = json.loads(entity_nodes_raw)
history_nodes = json.loads(history_nodes_raw)

def patch_nodes(nodes):
    patched = False
    for node in nodes:
        if node.get("name") != target_node:
            continue
        params = node.setdefault("parameters", {})
        params["url"] = relay_url
        headers = params.setdefault("headerParameters", {}).setdefault("parameters", [])
        header_map = {str(item.get("name")): idx for idx, item in enumerate(headers)}
        token_value = env.get("ELEVEN_OUTBOUND_RELAY_TOKEN", "")
        if token_value:
            token_header = {"name": "X-Relay-Token", "value": token_value}
            if "X-Relay-Token" in header_map:
                headers[header_map["X-Relay-Token"]] = token_header
            else:
                headers.append(token_header)
        patched = True
        break
    if not patched:
        raise RuntimeError(f"Node not found: {target_node}")
    return nodes

entity_nodes = patch_nodes(entity_nodes)
history_nodes = patch_nodes(history_nodes)

entity_json = json.dumps(entity_nodes, ensure_ascii=False).replace("'", "''")
history_json = json.dumps(history_nodes, ensure_ascii=False).replace("'", "''")

psql("BEGIN;"
     f"UPDATE workflow_entity SET nodes='{entity_json}'::json WHERE id='{workflow_id}';"
     f"UPDATE workflow_history SET nodes='{history_json}'::json WHERE \"workflowId\"='{workflow_id}' AND \"versionId\"='{active_version}';"
     "COMMIT;")

print(json.dumps({
    "ok": True,
    "workflow_id": workflow_id,
    "active_version_id": active_version,
    "relay_url": relay_url,
    "target_node_name": target_node,
    "mode": "server_postgres",
}, ensure_ascii=False))
"""


def patch_live_workflow(relay_url: str, target_node_name: str) -> dict:
    workflow_id_b64 = base64.b64encode(WORKFLOW_ID.encode()).decode()
    relay_url_b64 = base64.b64encode(relay_url.encode()).decode()
    target_node_b64 = base64.b64encode(target_node_name.encode()).decode()
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        SERVER_ALIAS,
        "python3",
        "-",
        workflow_id_b64,
        relay_url_b64,
        target_node_b64,
    ]
    result = subprocess.run(
        cmd,
        input=REMOTE_HELPER,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def save_state(payload: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    target_node_name = os.getenv("N8N_TARGET_NODE_NAME", "Eleven | Outbound HTTP")

    cmd = [
        "ssh",
        "-tt",
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
        result = patch_live_workflow(relay_url, target_node_name)
        state = {
            "relay_url": relay_url,
            "workflow_id": result["workflow_id"],
            "active_version_id": result["active_version_id"],
            "target_node_name": result["target_node_name"],
            "mode": result["mode"],
        }
        save_state(state)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        seen = relay_url

    raise SystemExit(proc.wait())


if __name__ == "__main__":
    main()
