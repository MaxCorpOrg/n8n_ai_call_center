#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_CONTROL_TOWER_DIR = Path(".runtime/eleven_control_tower_latest")
DEFAULT_QUOTA = DEFAULT_CONTROL_TOWER_DIR / "quota" / "eleven_quota_preflight_summary.json"
DEFAULT_READINESS = DEFAULT_CONTROL_TOWER_DIR / "readiness" / "live_readiness_summary.json"
DEFAULT_PACK = DEFAULT_CONTROL_TOWER_DIR / "pack" / "manifest.json"
DEFAULT_MATRIX = DEFAULT_CONTROL_TOWER_DIR / "turn_checks" / "variant_matrix.json"
DEFAULT_ALIGNMENT = DEFAULT_CONTROL_TOWER_DIR / "alignment.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(
    quota: dict,
    readiness: dict,
    pack: dict,
    matrix: dict,
    alignment: dict,
    artifact_paths: dict,
) -> dict:
    published = pack.get("current_published") or {}
    latest_quota_fail = ((readiness.get("quota_preflight") or {}).get("latest_quota_fail") or {})
    checks = readiness.get("checks") or {}
    quick = matrix.get("quick_reading") or {}
    variants = {item.get("label"): item for item in (matrix.get("variants") or [])}

    published_variant = variants.get("published_current") or {}
    balanced_variant = variants.get("interruptible_balanced") or {}
    softfill_variant = variants.get("interruptible_softfill") or {}
    latefill_variant = variants.get("interruptible_latefill") or {}

    operational_state = {
        "live_calls_allowed_now": not bool(checks.get("calls_should_be_blocked_now")),
        "overall_diagnosis": readiness.get("overall_diagnosis"),
        "call_attempt_recommendation": (readiness.get("quota_preflight") or {}).get("call_attempt_recommendation"),
        "latest_quota_fail": latest_quota_fail,
        "relay_health_ok": bool(checks.get("public_health_ok")),
        "workflow_matches_state": bool(checks.get("workflow_matches_state")),
        "local_stack_running": bool(checks.get("local_stack_running")),
    }

    current_published = {
        "branch_id": published.get("branch_id"),
        "version_id": published.get("version_id"),
        "llm": published.get("llm"),
        "tts": published.get("tts"),
        "turn_timeout": published_variant.get("turn_timeout"),
        "turn_eagerness": published_variant.get("turn_eagerness"),
        "soft_timeout_seconds": published_variant.get("soft_timeout_seconds"),
        "interruptions_enabled": published_variant.get("interruptions_enabled"),
        "soft_prompt_has_time_promise_marker": published_variant.get("soft_prompt_has_time_promise_marker"),
    }

    next_candidates = {
        "best_for_barge_in_trial": {
            "label": quick.get("best_for_barge_in_trial"),
            "turn_timeout": balanced_variant.get("turn_timeout"),
            "turn_eagerness": balanced_variant.get("turn_eagerness"),
            "soft_timeout_seconds": balanced_variant.get("soft_timeout_seconds"),
            "interruptions_enabled": balanced_variant.get("interruptions_enabled"),
            "soft_prompt_has_time_promise_marker": balanced_variant.get("soft_prompt_has_time_promise_marker"),
        },
        "best_for_barge_in_plus_filler_trial": {
            "label": quick.get("best_for_barge_in_plus_filler_trial"),
            "turn_timeout": softfill_variant.get("turn_timeout"),
            "turn_eagerness": softfill_variant.get("turn_eagerness"),
            "soft_timeout_seconds": softfill_variant.get("soft_timeout_seconds"),
            "interruptions_enabled": softfill_variant.get("interruptions_enabled"),
            "soft_prompt_has_time_promise_marker": softfill_variant.get("soft_prompt_has_time_promise_marker"),
        },
        "best_for_later_filler_trial": {
            "label": quick.get("best_for_later_filler_trial"),
            "turn_timeout": latefill_variant.get("turn_timeout"),
            "turn_eagerness": latefill_variant.get("turn_eagerness"),
            "soft_timeout_seconds": latefill_variant.get("soft_timeout_seconds"),
            "interruptions_enabled": latefill_variant.get("interruptions_enabled"),
            "soft_prompt_has_time_promise_marker": latefill_variant.get("soft_prompt_has_time_promise_marker"),
        },
        "repeatable_fallback": pack.get("repeatable_fallback_candidate"),
    }

    main_risk = ((alignment.get("summary") or {}).get("main_risk"))

    return {
        "operational_state": operational_state,
        "current_published": current_published,
        "next_candidates": next_candidates,
        "post_quota_execution_order": pack.get("execution_order") or [],
        "docs_alignment_main_risk": main_risk,
        "artifacts": artifact_paths,
    }


def render_markdown(payload: dict) -> str:
    ops = payload["operational_state"]
    cur = payload["current_published"]
    nxt = payload["next_candidates"]
    latest = ops.get("latest_quota_fail") or {}
    lines = [
        "# Eleven Operational Brief",
        "",
        "## Сейчас",
        f"- Live calls allowed now: `{str(ops.get('live_calls_allowed_now')).lower()}`",
        f"- Diagnosis: `{ops.get('overall_diagnosis')}`",
        f"- Recommendation: `{ops.get('call_attempt_recommendation')}`",
        f"- Relay health ok: `{str(ops.get('relay_health_ok')).lower()}`",
        f"- Workflow matches state: `{str(ops.get('workflow_matches_state')).lower()}`",
        f"- Local stack running: `{str(ops.get('local_stack_running')).lower()}`",
        "",
        "## Последний quota-fail",
        f"- Conversation: `{latest.get('conversation_id')}`",
        f"- Reason: `{latest.get('termination_reason')}`",
        f"- Start UTC: `{latest.get('start_time_utc')}`",
        f"- Version: `{latest.get('version_id')}`",
        "",
        "## Current published",
        f"- Branch: `{cur.get('branch_id')}`",
        f"- Version: `{cur.get('version_id')}`",
        f"- Stack: `{cur.get('llm')} + {cur.get('tts')}`",
        f"- Turn timeout: `{cur.get('turn_timeout')}`",
        f"- Turn eagerness: `{cur.get('turn_eagerness')}`",
        f"- Soft timeout: `{cur.get('soft_timeout_seconds')}`",
        f"- Interruptions enabled: `{str(cur.get('interruptions_enabled')).lower()}`",
        f"- Time-promise fillers present: `{str(cur.get('soft_prompt_has_time_promise_marker')).lower()}`",
        "",
        "## Следующие кандидаты",
        f"- First barge-in trial: `{nxt['best_for_barge_in_trial'].get('label')}`",
        f"  - interruptions: `{str(nxt['best_for_barge_in_trial'].get('interruptions_enabled')).lower()}`",
        f"  - soft timeout: `{nxt['best_for_barge_in_trial'].get('soft_timeout_seconds')}`",
        f"  - time-promise fillers present: `{str(nxt['best_for_barge_in_trial'].get('soft_prompt_has_time_promise_marker')).lower()}`",
        f"- Second filler-sensitive trial: `{nxt['best_for_barge_in_plus_filler_trial'].get('label')}`",
        f"  - interruptions: `{str(nxt['best_for_barge_in_plus_filler_trial'].get('interruptions_enabled')).lower()}`",
        f"  - soft timeout: `{nxt['best_for_barge_in_plus_filler_trial'].get('soft_timeout_seconds')}`",
        f"  - time-promise fillers present: `{str(nxt['best_for_barge_in_plus_filler_trial'].get('soft_prompt_has_time_promise_marker')).lower()}`",
        f"- Third later-filler trial: `{nxt['best_for_later_filler_trial'].get('label')}`",
        f"  - interruptions: `{str(nxt['best_for_later_filler_trial'].get('interruptions_enabled')).lower()}`",
        f"  - soft timeout: `{nxt['best_for_later_filler_trial'].get('soft_timeout_seconds')}`",
        f"  - time-promise fillers present: `{str(nxt['best_for_later_filler_trial'].get('soft_prompt_has_time_promise_marker')).lower()}`",
        f"- Repeatable fallback: `{(nxt.get('repeatable_fallback') or {}).get('version_id')}`",
        "",
        "## Main risk",
        f"- {payload.get('docs_alignment_main_risk')}",
        "",
        "## Post-quota order",
    ]
    for idx, item in enumerate(payload.get("post_quota_execution_order") or [], start=1):
        lines.append(f"{idx}. {item}")
    lines.extend(
        [
            "",
            "## Артефакты",
        ]
    )
    for key, value in (payload.get("artifacts") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a concise operational brief for the Eleven live/lab state.")
    parser.add_argument("--quota", default=str(DEFAULT_QUOTA))
    parser.add_argument("--readiness", default=str(DEFAULT_READINESS))
    parser.add_argument("--pack", default=str(DEFAULT_PACK))
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    parser.add_argument("--alignment", default=str(DEFAULT_ALIGNMENT))
    parser.add_argument("--json-output")
    parser.add_argument("--md-output")
    args = parser.parse_args()

    quota = load_json(Path(args.quota))
    readiness = load_json(Path(args.readiness))
    pack = load_json(Path(args.pack))
    matrix = load_json(Path(args.matrix))
    alignment = load_json(Path(args.alignment))

    artifact_paths = {
        "quota_summary": str(Path(args.quota)),
        "readiness_summary": str(Path(args.readiness)),
        "pack_manifest": str(Path(args.pack)),
        "variant_matrix": str(Path(args.matrix)),
        "alignment_summary": str(Path(args.alignment)),
    }

    payload = build_payload(quota, readiness, pack, matrix, alignment, artifact_paths)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    markdown = render_markdown(payload)

    if args.json_output:
        path = Path(args.json_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    if args.md_output:
        path = Path(args.md_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
