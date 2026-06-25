#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import analyze_eleven_conversation as analyzer


ISSUE_WEIGHTS = {
    "machine_transfer_phrase_reached_agent_dialogue": 10,
    "call_log_without_end_call": 9,
    "normal_assistant_speech_after_call_log": 8,
    "duplicate_close_before_end_call": 8,
    "final_close_spoken_before_call_log": 7,
    "line_check_after_meaningful_post_opener_reply": 7,
    "placeholder_conversation_id_in_tool_call": 7,
    "context_fetch_before_opener": 6,
    "helpdesk_tail_in_outbound_close": 6,
    "repeated_line_check_self_talk": 6,
    "consecutive_agent_speech_without_user_reply": 5,
    "bracketed_stage_direction": 3,
    "filler_during_finalization": 3,
    "long_user_to_agent_gap": 2,
}


def load_audit(path: Path):
    audit_json = path / "finalization_audit.json"
    if audit_json.exists():
        return json.loads(audit_json.read_text(encoding="utf-8"))

    final_json = path / "conversation_poll_final.json"
    if final_json.exists():
        return analyzer.analyze(final_json)

    raise FileNotFoundError(f"No finalization_audit.json or conversation_poll_final.json in {path}")


def weighted_score(audit):
    issues = audit.get("issues") or []
    issue_penalty = sum(ISSUE_WEIGHTS.get(issue.get("type"), 1) for issue in issues)
    timing = audit.get("timing_summary") or {}
    gap_avg = ((timing.get("user_to_agent_gap_stats_secs") or {}).get("avg")) or 0.0
    unexplained_avg = ((timing.get("unexplained_overhead_stats_secs") or {}).get("avg")) or 0.0
    return round(issue_penalty + float(gap_avg) + float(unexplained_avg), 3)


def timing_complete(audit):
    timing = audit.get("timing_summary") or {}
    gap_avg = ((timing.get("user_to_agent_gap_stats_secs") or {}).get("avg"))
    unexplained_avg = ((timing.get("unexplained_overhead_stats_secs") or {}).get("avg"))
    return gap_avg is not None and unexplained_avg is not None


def summarize_candidate(path: Path):
    audit = load_audit(path)
    timing = audit.get("timing_summary") or {}
    complete = timing_complete(audit)
    warnings = []
    if not complete:
        warnings.append("timing_summary_incomplete_score_is_less_reliable")
    return {
        "path": str(path),
        "conversation_id": audit.get("conversation_id"),
        "version_id": audit.get("version_id"),
        "call_summary_title": audit.get("call_summary_title"),
        "termination_reason": audit.get("termination_reason"),
        "issues_count": audit.get("issues_count"),
        "issue_types": [issue.get("type") for issue in (audit.get("issues") or [])],
        "primary_bottleneck_counts": timing.get("primary_bottleneck_counts") or {},
        "gap_avg_of_avgs_secs": ((timing.get("user_to_agent_gap_stats_secs") or {}).get("avg")),
        "unexplained_avg_of_avgs_secs": ((timing.get("unexplained_overhead_stats_secs") or {}).get("avg")),
        "llm_ttfb_avg_secs": ((timing.get("llm_ttfb_stats_secs") or {}).get("avg")),
        "tts_ttfb_avg_secs": ((timing.get("tts_ttfb_stats_secs") or {}).get("avg")),
        "timing_complete": complete,
        "warnings": warnings,
        "top_recommendations": [
            {
                "priority": rec.get("priority"),
                "code": rec.get("code"),
                "title": rec.get("title"),
            }
            for rec in (audit.get("recommendations") or [])[:3]
        ],
        "score": weighted_score(audit),
    }


def main():
    parser = argparse.ArgumentParser(description="Compare multiple Eleven candidate run directories.")
    parser.add_argument("dirs", nargs="+", help="Run directories containing finalization_audit.json or conversation_poll_final.json")
    parser.add_argument("--output", help="Optional output JSON file")
    args = parser.parse_args()

    rows = [summarize_candidate(Path(d)) for d in args.dirs]
    rows.sort(key=lambda row: (not row["timing_complete"], row["score"], row["issues_count"], row["path"]))

    payload = {
        "comparison_rule": {
            "lower_score_is_better": True,
            "score_formula": "weighted_issue_penalty + avg_user_to_agent_gap + avg_unexplained_overhead",
            "sort_order": "timing_complete first, then lower score",
        },
        "candidates": rows,
        "best_candidate": rows[0] if rows else None,
    }

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
