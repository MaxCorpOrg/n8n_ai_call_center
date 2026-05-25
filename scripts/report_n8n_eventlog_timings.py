#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


@dataclass
class RunnerTiming:
    task_id: str
    workflow_name: str
    execution_id: str
    node_name: str
    requested_at: datetime
    responded_at: datetime | None = None

    @property
    def latency_ms(self) -> float | None:
        if not self.responded_at:
            return None
        return (self.responded_at - self.requested_at).total_seconds() * 1000.0


def load_lines(paths: Iterable[Path]) -> list[dict]:
    events: list[dict] = []
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    events.sort(key=lambda item: item.get("ts", ""))
    return events


def summarize(events: list[dict], workflow_filters: set[str], limit: int) -> str:
    node_started: dict[tuple[str, str], datetime] = {}
    node_timings: list[tuple[str, str, str, float]] = []
    runner_requested: dict[str, RunnerTiming] = {}
    runner_timings: list[RunnerTiming] = []
    workflow_started: dict[str, tuple[str, datetime]] = {}
    workflow_finished: list[tuple[str, str, float, str]] = []

    for event in events:
        event_name = event.get("eventName", "")
        payload = event.get("payload", {}) or {}
        ts = parse_ts(event.get("ts"))
        if not ts:
            continue

        workflow_name = str(payload.get("workflowName", "") or "")
        if workflow_filters and workflow_name not in workflow_filters:
            continue

        execution_id = str(payload.get("executionId", "") or "")
        node_name = str(payload.get("nodeName", "") or "")

        if event_name == "n8n.workflow.started" and execution_id:
            workflow_started[execution_id] = (workflow_name, ts)
        elif event_name == "n8n.workflow.success" and execution_id:
            start = workflow_started.get(execution_id)
            if start:
                workflow_finished.append(
                    (
                        start[0],
                        execution_id,
                        (ts - start[1]).total_seconds() * 1000.0,
                        "success",
                    )
                )
        elif event_name == "n8n.workflow.failed" and execution_id:
            start = workflow_started.get(execution_id)
            if start:
                workflow_finished.append(
                    (
                        start[0],
                        execution_id,
                        (ts - start[1]).total_seconds() * 1000.0,
                        "failed",
                    )
                )
        elif event_name == "n8n.node.started" and execution_id and node_name:
            node_started[(execution_id, node_name)] = ts
        elif event_name == "n8n.node.finished" and execution_id and node_name:
            started_at = node_started.get((execution_id, node_name))
            if started_at:
                node_timings.append(
                    (
                        workflow_name,
                        execution_id,
                        node_name,
                        (ts - started_at).total_seconds() * 1000.0,
                    )
                )
        elif event_name == "n8n.runner.task.requested":
            task_id = str(payload.get("taskId", "") or "")
            if task_id:
                runner_requested[task_id] = RunnerTiming(
                    task_id=task_id,
                    workflow_name=workflow_name,
                    execution_id=execution_id,
                    node_name=node_name,
                    requested_at=ts,
                )
        elif event_name == "n8n.runner.response.received":
            task_id = str(payload.get("taskId", "") or "")
            item = runner_requested.get(task_id)
            if item:
                item.responded_at = ts
                runner_timings.append(item)

    def top(values: list, key_index: int) -> list:
        return sorted(values, key=lambda item: item[key_index], reverse=True)[:limit]

    by_workflow_runner: dict[str, list[float]] = defaultdict(list)
    for item in runner_timings:
        if item.latency_ms is not None:
            by_workflow_runner[item.workflow_name].append(item.latency_ms)

    lines: list[str] = []
    lines.append("Workflow durations (latest longest):")
    for workflow_name, execution_id, duration_ms, status in top(workflow_finished, 2):
        lines.append(f"- {workflow_name} exec={execution_id} status={status} duration_ms={duration_ms:.1f}")

    lines.append("")
    lines.append("Node durations (latest longest):")
    for workflow_name, execution_id, node_name, duration_ms in top(node_timings, 3):
        lines.append(f"- {workflow_name} exec={execution_id} node={node_name} duration_ms={duration_ms:.1f}")

    lines.append("")
    lines.append("Runner request latencies (latest longest):")
    for item in sorted(
        [entry for entry in runner_timings if entry.latency_ms is not None],
        key=lambda entry: entry.latency_ms or 0.0,
        reverse=True,
    )[:limit]:
        lines.append(
            f"- {item.workflow_name} exec={item.execution_id} node={item.node_name} "
            f"task={item.task_id} runner_wait_ms={item.latency_ms:.1f}"
        )

    if by_workflow_runner:
        lines.append("")
        lines.append("Runner latency summary by workflow:")
        for workflow_name in sorted(by_workflow_runner):
            samples = sorted(by_workflow_runner[workflow_name])
            p95 = samples[max(0, int(len(samples) * 0.95) - 1)]
            avg = sum(samples) / len(samples)
            lines.append(
                f"- {workflow_name}: count={len(samples)} avg_ms={avg:.1f} p95_ms={p95:.1f} max_ms={samples[-1]:.1f}"
            )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize n8n event log timings for call-center workflows.")
    parser.add_argument("paths", nargs="+", help="Paths to n8nEventLog*.log files")
    parser.add_argument(
        "--workflow",
        action="append",
        default=[],
        help="Workflow name to include. Can be passed multiple times.",
    )
    parser.add_argument("--limit", type=int, default=10, help="How many top entries to show per section.")
    args = parser.parse_args()

    events = load_lines([Path(path) for path in args.paths])
    print(summarize(events, set(args.workflow), args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
