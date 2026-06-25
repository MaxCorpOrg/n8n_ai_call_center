#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

import analyze_eleven_conversation as single


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

EVIDENCE_RANK = {
    "weak": 0,
    "moderate": 1,
    "strong": 2,
}


def iter_paths(items):
    for item in items:
        path = Path(item).expanduser()
        if path.is_file():
            yield path


def get_issue_penalty(issues):
    return sum(ISSUE_WEIGHTS.get(issue.get("type"), 1) for issue in issues)


def get_gap_avg(result):
    stats = ((result.get("timing_summary") or {}).get("user_to_agent_gap_stats_secs") or {})
    value = stats.get("avg")
    return float(value) if value is not None else None


def get_unexplained_avg(result):
    stats = ((result.get("timing_summary") or {}).get("unexplained_overhead_stats_secs") or {})
    value = stats.get("avg")
    return float(value) if value is not None else None


def score_result(result):
    issues = result.get("issues") or []
    issue_penalty = get_issue_penalty(issues)
    gap_avg = get_gap_avg(result) or 0.0
    unexplained_avg = get_unexplained_avg(result) or 0.0
    return round(issue_penalty + gap_avg + unexplained_avg, 3)


def classify_evidence(raw_data, analyzed):
    transcript = raw_data.get("transcript") or []
    transcript_len = len(transcript)
    agent_messages = 0
    user_messages = 0
    for turn in transcript:
        if (turn.get("role") == "agent") and (turn.get("message") or "").strip():
            agent_messages += 1
        if (turn.get("role") == "user") and single.norm(turn.get("message") or "") not in ("", "..."):
            user_messages += 1
    gap_count = len(((analyzed.get("timing_summary") or {}).get("gap_breakdown")) or [])
    issues_count = int(analyzed.get("issues_count") or 0)

    if transcript_len >= 8 and user_messages >= 2 and agent_messages >= 2 and (gap_count >= 2 or issues_count >= 2):
        return "strong"
    if transcript_len >= 4 and user_messages >= 1 and agent_messages >= 1:
        return "moderate"
    return "weak"


def build_version_rows(result_records):
    groups = defaultdict(list)
    for record in result_records:
        version_id = record["analyzed"].get("version_id") or "unknown_version"
        groups[version_id].append(record)

    rows = []
    for version_id, records in groups.items():
        analyzed_items = [record["analyzed"] for record in records]
        branch_id = analyzed_items[0].get("branch_id")
        conversation_ids = [item.get("conversation_id") for item in analyzed_items if item.get("conversation_id")]
        scores = [score_result(item) for item in analyzed_items]
        issue_counts = defaultdict(int)
        bottleneck_counts = defaultdict(int)
        evidence_counts = defaultdict(int)
        for record in records:
            item = record["analyzed"]
            evidence_counts[record["evidence_strength"]] += 1
            for issue in item.get("issues") or []:
                issue_type = issue.get("type")
                if issue_type:
                    issue_counts[issue_type] += 1
            for key, value in ((item.get("timing_summary") or {}).get("primary_bottleneck_counts") or {}).items():
                bottleneck_counts[key] += int(value)

        if evidence_counts["strong"] > 0:
            aggregate_evidence = "strong"
        elif evidence_counts["moderate"] > 0:
            aggregate_evidence = "moderate"
        else:
            aggregate_evidence = "weak"

        rows.append({
            "version_id": version_id,
            "branch_id": branch_id,
            "conversations_count": len(analyzed_items),
            "conversation_ids": conversation_ids,
            "evidence_strength": aggregate_evidence,
            "evidence_counts": dict(evidence_counts),
            "score_avg": round(mean(scores), 3),
            "score_min": round(min(scores), 3),
            "score_max": round(max(scores), 3),
            "gap_avg_of_avgs_secs": round(mean([v for v in (get_gap_avg(item) for item in analyzed_items) if v is not None]), 3)
            if any(get_gap_avg(item) is not None for item in analyzed_items) else None,
            "unexplained_avg_of_avgs_secs": round(mean([v for v in (get_unexplained_avg(item) for item in analyzed_items) if v is not None]), 3)
            if any(get_unexplained_avg(item) is not None for item in analyzed_items) else None,
            "issue_type_counts": dict(sorted(issue_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
            "primary_bottleneck_counts": dict(sorted(bottleneck_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        })

    rows.sort(
        key=lambda item: (
            -EVIDENCE_RANK.get(item["evidence_strength"], 0),
            item["score_avg"],
            item["score_max"],
            item["version_id"],
        )
    )
    return rows


def sort_rows(rows):
    return sorted(
        rows,
        key=lambda item: (
            -EVIDENCE_RANK.get(item["evidence_strength"], 0),
            item["score_avg"],
            item["score_max"],
            item["version_id"],
        ),
    )


def build_recommended_views(rows):
    repeatable = sort_rows([
        row for row in rows
        if row["evidence_strength"] == "strong" and row["conversations_count"] >= 2
    ])
    highly_repeatable = sort_rows([
        row for row in rows
        if row["evidence_strength"] == "strong" and row["conversations_count"] >= 3
    ])
    single_run = sort_rows([
        row for row in rows
        if row["evidence_strength"] == "strong" and row["conversations_count"] == 1
    ])
    moderate_or_better = sort_rows([
        row for row in rows
        if EVIDENCE_RANK.get(row["evidence_strength"], 0) >= EVIDENCE_RANK["moderate"]
    ])
    return {
        "selection_rule": {
            "primary": "prefer_strong_repeatable_candidate_with_2plus_conversations",
            "fallback": "if no repeatable candidate is acceptable, inspect the best single-run candidate manually before reuse",
            "note": "A low score from one conversation is useful, but it is weaker than a slightly worse score repeated across multiple conversations.",
        },
        "best_repeatable_candidates": repeatable[:10],
        "best_highly_repeatable_candidates": highly_repeatable[:10],
        "best_single_run_candidates": single_run[:10],
        "best_overall_moderate_or_better": moderate_or_better[:10],
    }


def main():
    parser = argparse.ArgumentParser(description="Rank Eleven lab version_ids by aggregated audit quality.")
    parser.add_argument("files", nargs="+", help="conversation_poll_final.json or conv_*.json files")
    args = parser.parse_args()

    paths = list(iter_paths(args.files))
    if not paths:
        raise SystemExit("No input files found.")

    records = []
    for path in paths:
        analyzed = single.analyze(path)
        raw_data = json.loads(path.read_text(encoding="utf-8"))
        records.append({
            "path": str(path),
            "analyzed": analyzed,
            "evidence_strength": classify_evidence(raw_data, analyzed),
        })

    rows = build_version_rows(records)
    payload = {
        "files": [str(path) for path in paths],
        "version_leaderboard": rows,
        "recommended_views": build_recommended_views(rows),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
