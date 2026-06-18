#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


LLM_NODE_MARKERS = (
    "@n8n/n8n-nodes-langchain.lmChat",
    "@n8n/n8n-nodes-langchain.agent",
)

MODEL_KEYS = (
    "model",
    "modelName",
    "chatModel",
)


def iter_json_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".json":
            yield path
            continue
        if path.is_dir():
            for item in sorted(path.rglob("*.json")):
                if item.is_file():
                    yield item


def extract_model_value(parameters: dict) -> str:
    for key in MODEL_KEYS:
        value = parameters.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = value.get("value")
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
    return ""


def scan_workflow_file(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - operator tool
        return [{"file": str(path), "error": f"json_parse_failed: {exc}"}]

    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        return []

    rows: list[dict] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("type") or "")
        parameters = node.get("parameters")
        if not isinstance(parameters, dict):
            parameters = {}
        model = extract_model_value(parameters)

        if model or any(marker in node_type for marker in LLM_NODE_MARKERS):
            rows.append(
                {
                    "file": str(path),
                    "workflow_name": str(data.get("name") or ""),
                    "node_name": str(node.get("name") or ""),
                    "node_type": node_type,
                    "model": model,
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show LLM/model-bearing nodes from exported n8n workflow JSON files."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Workflow JSON file(s) or directories to scan.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a text table.",
    )
    args = parser.parse_args()

    paths = [Path(p).expanduser() for p in args.paths]
    rows: list[dict] = []
    for file_path in iter_json_files(paths):
        rows.extend(scan_workflow_file(file_path))

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    if not rows:
        print("No model-bearing workflow nodes found.")
        return 0

    file_w = max(len("FILE"), *(len(row.get("file", "")) for row in rows))
    workflow_w = max(len("WORKFLOW"), *(len(row.get("workflow_name", "")) for row in rows))
    node_w = max(len("NODE"), *(len(row.get("node_name", "")) for row in rows))
    type_w = max(len("TYPE"), *(len(row.get("node_type", "")) for row in rows))

    header = (
        f"{'FILE'.ljust(file_w)}  "
        f"{'WORKFLOW'.ljust(workflow_w)}  "
        f"{'NODE'.ljust(node_w)}  "
        f"{'TYPE'.ljust(type_w)}  "
        "MODEL"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        if "error" in row:
            print(f"{row['file']}  ERROR  {row['error']}")
            continue
        print(
            f"{row['file'].ljust(file_w)}  "
            f"{row['workflow_name'].ljust(workflow_w)}  "
            f"{row['node_name'].ljust(node_w)}  "
            f"{row['node_type'].ljust(type_w)}  "
            f"{row['model']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
