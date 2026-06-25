#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean

import analyze_eleven_conversation as single


def round_or_none(value):
    if value is None:
        return None
    return round(value, 3)


def extract_paths(items):
    paths = []
    for item in items:
        path = Path(item).expanduser()
        if path.is_file():
            paths.append(path)
    return paths


def stats_from_values(values):
    if not values:
        return None
    return {
        "count": len(values),
        "min": round(min(values), 3),
        "avg": round(mean(values), 3),
        "max": round(max(values), 3),
    }


def get_nested(summary, *keys):
    current = summary
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def summarize_runs(results):
    issue_counts = Counter()
    bottleneck_counts = Counter()
    recommendation_counts = Counter()
    gap_avg_values = []
    gap_max_values = []
    known_path_avg_values = []
    unexplained_avg_values = []
    llm_ttfb_avg_values = []
    tts_ttfb_avg_values = []

    for result in results:
        for issue in result.get("issues") or []:
            issue_type = issue.get("type")
            if issue_type:
                issue_counts[issue_type] += 1

        for key, value in (get_nested(result, "timing_summary", "primary_bottleneck_counts") or {}).items():
            bottleneck_counts[key] += int(value)

        for rec in result.get("recommendations") or []:
            code = rec.get("code")
            if code:
                recommendation_counts[code] += 1

        gap_avg = get_nested(result, "timing_summary", "user_to_agent_gap_stats_secs", "avg")
        gap_max = get_nested(result, "timing_summary", "user_to_agent_gap_stats_secs", "max")
        known_avg = get_nested(result, "timing_summary", "known_path_stats_secs", "avg")
        unexplained_avg = get_nested(result, "timing_summary", "unexplained_overhead_stats_secs", "avg")
        llm_avg = get_nested(result, "timing_summary", "llm_ttfb_stats_secs", "avg")
        tts_avg = get_nested(result, "timing_summary", "tts_ttfb_stats_secs", "avg")

        if gap_avg is not None:
            gap_avg_values.append(float(gap_avg))
        if gap_max is not None:
            gap_max_values.append(float(gap_max))
        if known_avg is not None:
            known_path_avg_values.append(float(known_avg))
        if unexplained_avg is not None:
            unexplained_avg_values.append(float(unexplained_avg))
        if llm_avg is not None:
            llm_ttfb_avg_values.append(float(llm_avg))
        if tts_avg is not None:
            tts_ttfb_avg_values.append(float(tts_avg))

    ranked_recommendations = []
    for code, count in recommendation_counts.most_common():
        sample = None
        for result in results:
            for rec in result.get("recommendations") or []:
                if rec.get("code") == code:
                    sample = rec
                    break
            if sample:
                break
        ranked_recommendations.append({
            "code": code,
            "count": count,
            "priority": None if sample is None else sample.get("priority"),
            "title": None if sample is None else sample.get("title"),
        })

    return {
        "conversations_analyzed": len(results),
        "issue_type_counts": dict(issue_counts.most_common()),
        "primary_bottleneck_counts": dict(bottleneck_counts.most_common()),
        "top_recommendation_counts": ranked_recommendations,
        "timing_rollup": {
            "gap_avg_of_avgs_secs": round_or_none(mean(gap_avg_values)) if gap_avg_values else None,
            "gap_max_of_maxes_secs": round_or_none(max(gap_max_values)) if gap_max_values else None,
            "known_path_avg_of_avgs_secs": round_or_none(mean(known_path_avg_values)) if known_path_avg_values else None,
            "unexplained_overhead_avg_of_avgs_secs": round_or_none(mean(unexplained_avg_values)) if unexplained_avg_values else None,
            "llm_ttfb_avg_of_avgs_secs": round_or_none(mean(llm_ttfb_avg_values)) if llm_ttfb_avg_values else None,
            "tts_ttfb_avg_of_avgs_secs": round_or_none(mean(tts_ttfb_avg_values)) if tts_ttfb_avg_values else None,
            "gap_avg_distribution_secs": stats_from_values(gap_avg_values),
            "known_path_avg_distribution_secs": stats_from_values(known_path_avg_values),
            "unexplained_overhead_avg_distribution_secs": stats_from_values(unexplained_avg_values),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Batch-analyze multiple Eleven conversation JSON files and aggregate common issues."
    )
    parser.add_argument("files", nargs="+", help="conversation_poll_final.json or conv_*.json files")
    args = parser.parse_args()

    paths = extract_paths(args.files)
    if not paths:
        raise SystemExit("No input files found.")

    results = [single.analyze(path) for path in paths]
    payload = {
        "files": [str(path) for path in paths],
        "summary": summarize_runs(results),
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
