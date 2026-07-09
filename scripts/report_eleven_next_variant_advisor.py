#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_MATRIX = Path(".runtime/eleven_control_tower_latest/turn_checks/variant_matrix.json")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_audit_payload(audit_raw):
    if isinstance(audit_raw, dict):
        return audit_raw
    if isinstance(audit_raw, list):
        issues = []
        for item in audit_raw:
            if isinstance(item, dict):
                issues.extend(item.get("issues") or [])
        return {
            "issues": issues,
            "recommendations": [],
            "timing_summary": {},
            "source_kind": "batch_list",
        }
    return {}


def normalize(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def detect_signals(complaints: list[str], audit: dict | None) -> tuple[set[str], list[str], dict]:
    signals: set[str] = set()
    reasons: list[str] = []
    details = {
        "issue_types": [],
        "recommendation_codes": [],
        "primary_bottlenecks": {},
    }

    complaint_text = " || ".join(normalize(item) for item in complaints if item)

    complaint_rules = [
        (
            "cannot_interrupt",
            ("не дает говорить", "не даёт говорить", "перебивает", "обрывает", "не успеваю ответить", "не пускает", "interrupt"),
            "Жалоба похожа на aggressive turn-taking или отключённые interruptions.",
        ),
        (
            "filler_too_early",
            ("слишком рано", "слишком быстро говорит алло", "рано filler", "рано говорит да", "рано начинает говорить", "слишком рано лезет", "рано начинает filler", "лезет filler", "раньше времени"),
            "Жалоба похожа на слишком ранний старт filler masking.",
        ),
        (
            "filler_bot_like",
            ("ботск", "секунду", "момент", "неестествен", "слишком робот", "слишком как бот", "бот"),
            "Жалоба похожа на неестественные filler-фразы или time-promise лексику.",
        ),
        (
            "empty_pause_too_long",
            ("длинная пауза", "долгая пауза", "молчит", "долго думает", "пустая тишина", "тишина между ответами"),
            "Жалоба похожа на длинную пустую паузу перед следующим ответом.",
        ),
    ]

    for code, markers, reason in complaint_rules:
        if any(marker in complaint_text for marker in markers):
            signals.add(code)
            reasons.append(reason)

    if audit:
        audit = normalize_audit_payload(audit)
        rec_codes = [item.get("code") for item in (audit.get("recommendations") or []) if isinstance(item, dict) and item.get("code")]
        issue_types = [item.get("type") for item in (audit.get("issues") or []) if isinstance(item, dict) and item.get("type")]
        bottlenecks = ((audit.get("timing_summary") or {}).get("primary_bottleneck_counts") or {})
        details = {
            "issue_types": issue_types,
            "recommendation_codes": rec_codes,
            "primary_bottlenecks": bottlenecks,
        }
        timing_summary = audit.get("timing_summary") or {}
        has_any_timing = any(
            timing_summary.get(key)
            for key in (
                "first_user_to_agent_gap_secs",
                "user_to_agent_gap_stats_secs",
                "known_path_stats_secs",
                "llm_ttfb_stats_secs",
                "tts_ttfb_stats_secs",
            )
        )
        if not has_any_timing and not issue_types and not (audit.get("termination_reason") or "").strip():
            details["issue_types"].append("no_behavioral_transcript")
            signals.add("invalid_or_empty_call")
            reasons.append("Audit не содержит transcript/timing и termination reason; это невалидный звонок для оценки агента.")

        if "focus_turn_taking" in rec_codes or "line_check_after_meaningful_post_opener_reply" in issue_types:
            signals.add("cannot_interrupt")
            reasons.append("Audit указывает на проблему turn-taking / rescue-поведения.")
        if "consecutive_agent_speech_without_user_reply" in issue_types:
            signals.add("cannot_interrupt")
            reasons.append("Audit показывает, что агент продолжал говорить без нового ответа человека.")
        if "stop_self_talk_loops" in rec_codes or "repeated_line_check_self_talk" in issue_types:
            signals.add("filler_too_early")
            reasons.append("Audit указывает на self-talk / repeated line-check loop.")
        if "filler_during_finalization" in issue_types:
            signals.add("filler_bot_like")
            reasons.append("Audit показывает filler не в том месте, где он должен звучать естественно.")
        if "focus_llm_latency" in rec_codes or "focus_tts_start" in rec_codes:
            signals.add("empty_pause_too_long")
            reasons.append("Audit указывает на заметную пустую паузу до ответа.")
        if "llm_generation" in bottlenecks or "tts_start" in bottlenecks:
            signals.add("empty_pause_too_long")
            reasons.append("Timing summary показывает bottleneck по генерации или старту аудио.")
        if "turn_taking_or_dialogue_flow" in bottlenecks:
            signals.add("cannot_interrupt")
            reasons.append("Timing summary показывает bottleneck именно в dialogue-flow, а не только в raw latency.")
        if "machine_transfer_phrase_reached_agent_dialogue" in issue_types:
            signals.add("needs_machine_hardstop")
            reasons.append("Audit показывает, что agent продолжает диалог после service-style machine phrase.")

    return signals, reasons, details


def build_action_plan(details: dict) -> tuple[list[dict], bool]:
    issue_types = set(details.get("issue_types") or [])
    rec_codes = set(details.get("recommendation_codes") or [])

    actions = []

    def add(code: str, title: str, why: str, next_step: str):
        actions.append({
            "kind": "fix_before_variant",
            "code": code,
            "title": title,
            "why": why,
            "next_step": next_step,
        })

    if "machine_transfer_phrase_reached_agent_dialogue" in issue_types or "hard_stop_machine_transfer" in rec_codes:
        add(
            "hard_stop_machine_transfer",
            "Сначала дожать hard-stop по machine phrase",
            "Если агент разговаривает с service-style автоответчиком, крутить turn-taking variant раньше времени бесполезно.",
            "Ужесточить machine/message-service rule и только потом возвращаться к variant A/B.",
        )
    if "no_behavioral_transcript" in issue_types:
        add(
            "no_behavioral_transcript",
            "Не засчитывать пустой/in-progress звонок",
            "Если нет transcript, timing и причины завершения, это не тест поведения агента.",
            "Повторить одиночный self-test или отдельно разбирать телефонию/SIP, но не делать выводы о prompt/voice.",
        )
    if "spoken_tool_pseudocode" in issue_types or "block_spoken_tool_pseudocode" in rec_codes:
        add(
            "block_spoken_tool_pseudocode",
            "Сначала убрать spoken tool pseudo-code",
            "Если агент произносит call_log/end_call/payload как обычную речь, этот agent head нельзя сравнивать как conversational variant.",
            "Откатиться к actual tool-call baseline или чинить tool binding так, чтобы tool_calls были реальными, а spoken text был чистым.",
        )
    if (
        "opener_not_first_agent_message" in issue_types
        or "missing_exact_opener" in issue_types
        or "restore_exact_opener_first" in rec_codes
    ):
        add(
            "restore_exact_opener_first",
            "Сначала вернуть exact opener первым сообщением",
            "Если первое сообщение агента не opener, остальные метрики разговора уже сняты с неправильного сценария.",
            "Зафиксировать opener-first gate и повторить self-test до любых turn-taking или voice A/B.",
        )
    if "line_check_after_meaningful_post_opener_reply" in issue_types or "remove_late_line_checks" in rec_codes:
        add(
            "remove_late_line_checks",
            "Сначала убрать поздние line-check",
            "Если после осмысленного ответа человека агент снова говорит Алло/Вы на линии, сценарий уже уехал в self-talk.",
            "Закрепить: после любого meaningful post-opener reply rescue/line-check запрещены до конца звонка.",
        )
    if (
        "duplicate_close_before_end_call" in issue_types
        or "final_close_spoken_before_call_log" in issue_types
        or "call_log_without_end_call" in issue_types
        or "single_close_only" in rec_codes
        or "no_normal_speech_after_call_log" in rec_codes
    ):
        add(
            "single_close_only",
            "Сначала дожать single-close finalization",
            "Если финализация ещё ломается, сравнение voice/turn variants будет шумным и нечестным.",
            "Сделать жёсткий порядок: silent call_log -> один end_call -> стоп.",
        )
    if "placeholder_conversation_id_in_tool_call" in issue_types or "fix_tool_identity_binding" in rec_codes:
        add(
            "fix_tool_identity_binding",
            "Сначала исправить identity binding tools",
            "Если conv/id поля текут, нельзя считать post-call telemetry надёжной.",
            "Починить binding conversation identity и только потом продолжать variant tests.",
        )
    if "context_fetch_before_opener" in issue_types or "ban_preopener_context_fetch" in rec_codes:
        add(
            "ban_preopener_context_fetch",
            "Сначала убрать pre-opener tool path",
            "Инструмент до opener ломает чистоту разговора и маскирует реальную conversational проблему.",
            "Убрать context/tool вызовы до нормального старта live-диалога.",
        )
    if "focus_tool_path" in rec_codes:
        add(
            "focus_tool_path",
            "Сначала проверить tool-path latency",
            "Если длинный хвост сидит в tools, variant по turn-taking может не быть главным выигрышем.",
            "Померить bridge/tools и убрать лишние spoken turns вокруг tool path.",
        )

    seen = set()
    deduped = []
    for item in actions:
        code = item["code"]
        if code in seen:
            continue
        seen.add(code)
        deduped.append(item)
    return deduped, not bool(deduped)


def build_advice(
    matrix: dict,
    signals: set[str],
    reasons: list[str],
    details: dict,
    complaints: list[str],
    audit_path: str | None,
) -> dict:
    quick = matrix.get("quick_reading") or {}
    variants = {item.get("label"): item for item in (matrix.get("variants") or [])}

    published = quick.get("published_reference")
    balanced = quick.get("best_for_barge_in_trial")
    softfill = quick.get("best_for_barge_in_plus_filler_trial")
    latefill = quick.get("best_for_later_filler_trial")

    action_plan, ready_for_variant_testing = build_action_plan(details)
    recommended = []

    if "cannot_interrupt" in signals:
        recommended.append({
            "variant": balanced,
            "why": "Сначала нужно дать человеку возможность нормально вклиниться в разговор.",
        })
    if "filler_bot_like" in signals or "empty_pause_too_long" in signals:
        recommended.append({
            "variant": softfill,
            "why": "Нужен более естественный filler без time-promise и без слишком ботской лексики.",
        })
    if "filler_too_early" in signals:
        recommended.append({
            "variant": latefill,
            "why": "Нужно отложить старт filler masking чуть дальше, к `soft_timeout = 3.0`.",
        })
    if not recommended:
        recommended = [
            {
                "variant": published,
                "why": "Нет явного проблемного сигнала; начинаем с current published как контрольной точки.",
            },
            {
                "variant": balanced,
                "why": "Первый осмысленный A/B шаг после published для человеческого turn-taking.",
            },
            {
                "variant": softfill,
                "why": "Второй шаг, если надо смягчить filler behavior.",
            },
            {
                "variant": latefill,
                "why": "Третий шаг, если fillers уже хорошие, но ещё стартуют рановато.",
            },
        ]

    deduped = []
    seen = set()
    for item in recommended:
        label = item.get("variant")
        if not label or label in seen:
            continue
        seen.add(label)
        variant = variants.get(label) or {}
        deduped.append({
            "variant": label,
            "why": item.get("why"),
            "turn_timeout": variant.get("turn_timeout"),
            "turn_eagerness": variant.get("turn_eagerness"),
            "soft_timeout_seconds": variant.get("soft_timeout_seconds"),
            "interruptions_enabled": variant.get("interruptions_enabled"),
            "soft_prompt_has_time_promise_marker": variant.get("soft_prompt_has_time_promise_marker"),
        })

    return {
        "inputs": {
            "complaints": complaints,
            "audit_path": audit_path,
            "signals": sorted(signals),
        },
        "detected_reasons": reasons,
        "ready_for_variant_testing": ready_for_variant_testing,
        "action_plan": action_plan,
        "recommended_order": deduped,
        "default_post_quota_order": [
            published,
            balanced,
            softfill,
            latefill,
        ],
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Eleven Next Variant Advisor",
        "",
        "## Входы",
    ]
    complaints = payload["inputs"].get("complaints") or []
    if complaints:
        for item in complaints:
            lines.append(f"- complaint: `{item}`")
    else:
        lines.append("- complaints: none")
    if payload["inputs"].get("audit_path"):
        lines.append(f"- audit_path: `{payload['inputs']['audit_path']}`")
    lines.append(f"- signals: `{', '.join(payload['inputs'].get('signals') or []) or 'none'}`")
    lines.append("")
    lines.append("## Почему")
    for reason in payload.get("detected_reasons") or ["Явные сигналы не обнаружены; используется базовый post-quota порядок."]:
        lines.append(f"- {reason}")
    lines.append("")
    lines.append("## Сначала исправить")
    if payload.get("action_plan"):
        for idx, item in enumerate(payload.get("action_plan") or [], start=1):
            lines.append(f"{idx}. `{item.get('code')}`")
            lines.append(f"   - title: {item.get('title')}")
            lines.append(f"   - why: {item.get('why')}")
            lines.append(f"   - next_step: {item.get('next_step')}")
    else:
        lines.append("- blocking fix-before-variant items: none")
    lines.append("")
    lines.append("## Что пробовать дальше")
    for idx, item in enumerate(payload.get("recommended_order") or [], start=1):
        lines.append(f"{idx}. `{item.get('variant')}`")
        lines.append(f"   - why: {item.get('why')}")
        lines.append(f"   - turn_timeout: `{item.get('turn_timeout')}`")
        lines.append(f"   - turn_eagerness: `{item.get('turn_eagerness')}`")
        lines.append(f"   - soft_timeout: `{item.get('soft_timeout_seconds')}`")
        lines.append(f"   - interruptions: `{str(item.get('interruptions_enabled')).lower()}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Recommend the next Eleven variant to test based on complaints and/or audit.")
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    parser.add_argument("--audit")
    parser.add_argument("--complaint", action="append", default=[])
    parser.add_argument("--json-output")
    parser.add_argument("--md-output")
    args = parser.parse_args()

    matrix_path = Path(args.matrix)
    matrix = load_json(matrix_path)

    audit = None
    if args.audit:
        audit = load_json(Path(args.audit))

    signals, reasons, details = detect_signals(args.complaint, audit)
    payload = build_advice(matrix, signals, reasons, details, args.complaint, args.audit)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    markdown = render_markdown(payload)

    if args.json_output:
        path = Path(args.json_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    if args.md_output:
        path = Path(args.md_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown + "\n", encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
