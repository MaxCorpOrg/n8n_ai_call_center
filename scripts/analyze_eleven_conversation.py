#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path
from statistics import mean


LINE_CHECK_PATTERNS = [
    r"\bалло\b",
    r"\bслышно\b",
    r"\bвы на линии\b",
    r"\bвы всё ещё на линии\b",
    r"\bвы слышны\b",
]

FILLER_PATTERNS = [
    r"^\s*так\.\.\.?\s*$",
    r"^\s*поняла\.\.\.?\s*$",
    r"^\s*ясно\.\.\.?\s*$",
    r"^\s*\.\.\.\s*$",
]

CLOSE_PATTERNS = [
    r"поняла[, ]+спасибо[. ]+хорошего дня",
    r"поняла[. ]+хорошего дня",
    r"я уже отправила sms на этот номер[. ]+хорошего дня",
]

HELPDESK_TAIL_PATTERNS = [
    r"могу ли я .*чем[- ]?то ещё помочь",
    r"могу .*чем[- ]?то ещё помочь",
    r"чем[- ]?то ещё помочь",
    r"могу ли я помочь вам .*ещ[её]",
]

PLACEHOLDER_PATTERNS = [
    r"system__conversation_id",
    r"conv_abcdef",
    r"conv_current",
    r"conv_123\b",
]

SPOKEN_TOOL_TEXT_PATTERNS = [
    r"\bcall_log\s*\(",
    r"\bend_call\s*\(",
    r"\bsend_sms_info\s*\(",
    r"\bcontext_fetch\s*\(",
    r"silent[_ ]call_log",
    r"\bsilent\b",
    r"call_log with payload",
    r"call_log with appropriate fields",
    r"end_call\)\s*system__message_to_speak",
    r"\bpayload\b",
    r"\blead_id\b",
    r"\bsource_record_key\b",
    r"\bphone_primary\b",
    r"\beleven_conv_id\b",
    r"\bconversation_id\b",
    r"\{\\?\"[a-zA-Z_]+\\?\"",
]

MACHINE_TRANSFER_PATTERNS = [
    r"\bабонент(?:у|ам|а)?\b",
    r"\bчто передать абонент",
    r"\bесли абонент захочет",
    r"\bя передам\b",
    r"\bсообщу это абоненту\b",
]

SELF_TALK_LINECHECK_PATTERNS = [
    r"\bалло\b",
    r"\bслышно\b",
    r"\bвы тут\b",
    r"\bвы на линии\b",
]

DEFAULT_LONG_GAP_SECONDS = 2.0
EXPECTED_OPENER_SNIPPET = "здравствуйте, я официальный представитель липолитика липолонг"
EXPECTED_OPENER_START = "здравствуйте, я официальный"


def strip_stage_directions(text: str) -> str:
    text = text or ""
    text = re.sub(r"\[[^\]]+\]", " ", text)
    return text


def norm(text: str) -> str:
    text = strip_stage_directions(text)
    return re.sub(r"\s+", " ", text.strip().lower())


def matches_any(text: str, patterns) -> bool:
    t = norm(text)
    return any(re.search(p, t, flags=re.IGNORECASE) for p in patterns)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def turn_time(turn):
    value = turn.get("time_in_call_secs")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def extract_metric(turn, metric_name: str):
    metrics = ((turn.get("conversation_turn_metrics") or {}).get("metrics") or {})
    metric = metrics.get(metric_name)
    if not isinstance(metric, dict):
        return None
    value = metric.get("elapsed_time")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def sum_tool_result_latencies(turns):
    total = 0.0
    found = False
    for turn in turns:
        for result in turn.get("tool_results") or []:
            value = result.get("tool_latency_secs")
            if isinstance(value, (int, float)):
                total += float(value)
                found = True
    return total if found else None


def collect_tool_names(turns):
    names = []
    for turn in turns:
        for call in turn.get("tool_calls") or []:
            name = call.get("tool_name")
            if isinstance(name, str) and name:
                names.append(name)
    return names


def summarize_numeric(values):
    if not values:
        return None
    return {
        "count": len(values),
        "min": round(min(values), 3),
        "avg": round(mean(values), 3),
        "max": round(max(values), 3),
    }


def round_or_none(value):
    if value is None:
        return None
    return round(value, 3)


def classify_gap_bottleneck(item):
    unexplained = item.get("estimated_unexplained_overhead_secs") or 0.0
    known_path = item.get("known_path_secs") or 0.0
    llm_ttfb = item.get("agent_llm_ttfb_secs") or 0.0
    tts_ttfb = item.get("agent_tts_ttfb_secs") or 0.0
    tool_latency = (item.get("intermediate_tool_latency_secs") or 0.0) + (
        item.get("intermediate_tool_request_generation_secs") or 0.0
    )
    tool_names = item.get("intermediate_tool_names") or []

    if tool_names and tool_latency >= max(unexplained, llm_ttfb, tts_ttfb, 1.0):
        return "tool_path"
    if llm_ttfb >= max(unexplained, tool_latency, tts_ttfb, 1.5):
        return "llm_generation"
    if tts_ttfb >= max(unexplained, tool_latency, llm_ttfb, 0.8):
        return "tts_start"
    if unexplained >= max(known_path, 1.0):
        return "turn_taking_or_dialogue_flow"
    if known_path >= 2.0 and unexplained >= 0.7:
        return "mixed_known_path_and_flow"
    return "mixed_or_small_gap"


def summarize_bottlenecks(items):
    if not items:
        return None
    counts = {}
    for item in items:
        key = item.get("likely_primary_bottleneck")
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    return counts or None


def build_recommendations(issues, bottleneck_counts):
    issue_types = [item.get("type") for item in issues]
    recommendations = []

    def add(code, priority, title, why, next_step):
        recommendations.append({
            "code": code,
            "priority": priority,
            "title": title,
            "why": why,
            "next_step": next_step,
        })

    if bottleneck_counts:
        flow_count = bottleneck_counts.get("turn_taking_or_dialogue_flow", 0)
        tool_count = bottleneck_counts.get("tool_path", 0)
        llm_count = bottleneck_counts.get("llm_generation", 0)
        tts_count = bottleneck_counts.get("tts_start", 0)

        if flow_count >= max(tool_count, llm_count, tts_count, 1):
            add(
                "focus_turn_taking",
                10,
                "Главный фокус: turn-taking и dialogue-flow",
                "Большинство длинных пауз выглядят как лишний хвост сценария, а не как медленный raw LLM/TTS.",
                "После восстановления квоты первым делом править turn_timeout, rescue/sequencing и пост-репличную логику, а не только менять модель.",
            )
        if tool_count >= 1:
            add(
                "focus_tool_path",
                8,
                "Проверить tool-path на длинных финальных шагах",
                "Часть длинных gap уже объясняется промежуточными tools, особенно call_log/send_sms_info.",
                "Померить и при необходимости ускорить call_log/send_sms_info bridge, а также убрать лишние spoken turns вокруг tool path.",
            )
        if llm_count >= 1:
            add(
                "focus_llm_latency",
                7,
                "Есть признаки LLM latency",
                "По части gap основной bottleneck выглядит как генерация ответа.",
                "Сократить длину ответа, проверить prompt-ветку, soft-timeout и возможный лишний reasoning перед репликой.",
            )
        if tts_count >= 1:
            add(
                "focus_tts_start",
                6,
                "Есть признаки TTS start latency",
                "По части gap старт аудио выглядит медленнее других компонентов.",
                "Проверить voice/TTS model, first audio latency и не слишком ли тяжёл spoken текст перед первым звуком.",
            )

    if "line_check_after_meaningful_post_opener_reply" in issue_types:
        add(
            "remove_late_line_checks",
            9,
            "Убрать поздние line-check после осмысленного ответа",
            "Агент возвращается в rescue-поведение уже после живого business-reply.",
            "Ужесточить правило: после осмысленного post-opener ответа rescue больше не возвращается.",
        )

    if "duplicate_close_before_end_call" in issue_types or "final_close_spoken_before_call_log" in issue_types:
        add(
            "single_close_only",
            9,
            "Дожать single-close sequencing",
            "Финализация всё ещё даёт duplicate close или spoken close до call_log.",
            "Сделать жёсткий порядок: silent call_log -> один spoken end_call -> stop.",
        )

    if "normal_assistant_speech_after_call_log" in issue_types:
        add(
            "no_normal_speech_after_call_log",
            8,
            "Убрать обычную речь после call_log",
            "После terminal outcome агент всё ещё продолжает обычный диалоговый turn.",
            "Запретить normal assistant speech после call_log и держать весь финальный close только внутри end_call.",
        )

    if "placeholder_conversation_id_in_tool_call" in issue_types:
        add(
            "fix_tool_identity_binding",
            8,
            "Добить identity binding в tools",
            "В tool-call ещё проскакивают placeholder conversation ids.",
            "Использовать только system-bound conversation fields и не позволять модели печатать fake conv_* вручную.",
        )

    if "spoken_tool_pseudocode" in issue_types:
        add(
            "block_spoken_tool_pseudocode",
            10,
            "Запретить spoken tool pseudo-code",
            "Агент произнёс или сгенерировал как обычную реплику текст вида call_log(...), end_call(...) или JSON-поля.",
            "Вернуть actual platform tool calls: assistant message empty, tool_calls populated, no JSON/tool names in spoken text.",
        )

    if "opener_not_first_agent_message" in issue_types or "missing_exact_opener" in issue_types:
        add(
            "restore_exact_opener_first",
            10,
            "Вернуть exact opener первым сообщением",
            "Первое сообщение агента не началось с обязательного представления ЛипоЛонг.",
            "До context/tools/qualification агент должен сказать exact opener; на раннее пользовательское слово нельзя отвечать как на продолжение диалога.",
        )

    if "opener_micro_fragment_before_full_opener" in issue_types:
        add(
            "polish_opener_micro_cut",
            7,
            "Отполировать micro-cut opener",
            "Первый opener начался правильными словами, но был оборван и полный opener прозвучал следующим turn.",
            "Это не semantic wrong-start, но нужно уменьшать ранний barge-in/cut или терпимее относиться к первому короткому overlap.",
        )

    if "context_fetch_before_opener" in issue_types:
        add(
            "ban_preopener_context_fetch",
            7,
            "Убрать context_fetch до opener",
            "Инструмент вызывается ещё до нормального старта живого диалога.",
            "Оставить context_fetch только для реального дефицита фактов уже после начала business-dialogue.",
        )

    if "machine_transfer_phrase_reached_agent_dialogue" in issue_types:
        add(
            "hard_stop_machine_transfer",
            10,
            "Ужесточить hard-stop на subscriber-transfer phrases",
            "После service-style фразы про абонента агент всё ещё продолжает диалог.",
            "Сразу переводить такой кейс в machine/no_answer path: silent call_log и silent end_call без продажной речи.",
        )

    if "repeated_line_check_self_talk" in issue_types or "consecutive_agent_speech_without_user_reply" in issue_types:
        add(
            "stop_self_talk_loops",
            8,
            "Срезать self-talk и повторные line-check loops",
            "Агент продолжает говорить без нового осмысленного ответа пользователя.",
            "Разрешить только один rescue в допустимом окне и потом либо ждать meaningful reply, либо завершать no_answer path.",
        )

    recommendations.sort(key=lambda item: (-item["priority"], item["code"]))
    return recommendations


def append_agent_streak_issues(issues, streak):
    if len(streak) < 2:
        return
    issues.append({
        "type": "consecutive_agent_speech_without_user_reply",
        "time_in_call_secs": streak[0].get("time_in_call_secs"),
        "messages": [item["message"] for item in streak],
    })
    repeated_line_checks = [
        item["message"]
        for item in streak
        if matches_any(item["message"], SELF_TALK_LINECHECK_PATTERNS)
    ]
    if repeated_line_checks:
        issues.append({
            "type": "repeated_line_check_self_talk",
            "time_in_call_secs": streak[0].get("time_in_call_secs"),
            "messages": repeated_line_checks,
        })


def first_tool_name(turn):
    tool_calls = turn.get("tool_calls") or []
    if tool_calls:
        return tool_calls[0].get("tool_name")
    return None


def extract_end_call_message(turns):
    for t in turns:
        for call in t.get("tool_calls") or []:
            if call.get("tool_name") != "end_call":
                continue
            payload = call.get("params_as_json")
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}
            if isinstance(payload, dict):
                msg = payload.get("system__message_to_speak")
                if msg:
                    return msg
    return None


def is_end_call_spoken_projection(turns, message_index, first_end_call_index, end_call_message):
    """Eleven may show end_call.system__message_to_speak as a prior spoken turn."""
    if first_end_call_index is None or end_call_message is None:
        return False
    if message_index >= first_end_call_index:
        return False
    turn = turns[message_index]
    msg = turn.get("message") or ""
    if norm(msg) != norm(end_call_message):
        return False
    end_turn = turns[first_end_call_index]
    if first_tool_name(end_turn) != "end_call":
        return False

    # The common platform shape is: assistant speaks message, then the very next
    # transcript row carries the end_call tool call for that same source event.
    if message_index == first_end_call_index - 1:
        return True

    message_event = turn.get("source_event_id")
    end_event = end_turn.get("source_event_id")
    if message_event is not None and message_event == end_event:
        between = turns[message_index + 1:first_end_call_index]
        return all(
            not (item.get("message") or "")
            and not (item.get("tool_calls") or [])
            for item in between
        )

    return False


def analyze(path: Path):
    data = load_json(path)
    turns = data.get("transcript") or []
    issues = []
    opener_index = None
    first_post_opener_user_reply_index = None
    first_call_log_index = None
    first_end_call_index = None
    first_agent_message_index = None
    end_call_message = extract_end_call_message(turns)
    normal_close_messages = []
    user_to_agent_gaps = []
    llm_ttfb_values = []
    llm_ttf_sentence_values = []
    llm_last_sentence_values = []
    tts_ttfb_values = []
    last_meaningful_user_turn = None
    agent_only_streak = []
    first_machine_transfer_user_turn = None

    for i, turn in enumerate(turns):
        role = turn.get("role")
        msg = turn.get("message") or ""
        tool_name = first_tool_name(turn)
        msg_norm = norm(msg)
        current_time = turn_time(turn)

        if role == "agent" and msg and first_agent_message_index is None:
            first_agent_message_index = i

        if role == "agent" and opener_index is None and EXPECTED_OPENER_SNIPPET in msg_norm:
            opener_index = i

        if opener_index is not None and i > opener_index and first_post_opener_user_reply_index is None:
            if role == "user" and msg_norm and msg_norm != "...":
                first_post_opener_user_reply_index = i

        if first_call_log_index is None and tool_name == "call_log":
            first_call_log_index = i

        if first_end_call_index is None and tool_name == "end_call":
            first_end_call_index = i

        if role == "user" and msg_norm and msg_norm != "...":
            append_agent_streak_issues(issues, agent_only_streak)
            last_meaningful_user_turn = {
                "index": i,
                "time_in_call_secs": current_time,
                "message": msg,
            }
            if first_machine_transfer_user_turn is None and matches_any(msg, MACHINE_TRANSFER_PATTERNS):
                first_machine_transfer_user_turn = {
                    "index": i,
                    "time_in_call_secs": current_time,
                    "message": msg,
                }
            agent_only_streak = []

        if role == "agent" and msg:
            llm_ttfb = extract_metric(turn, "convai_llm_service_ttfb")
            llm_ttf_sentence = extract_metric(turn, "convai_llm_service_ttf_sentence")
            llm_last_sentence = extract_metric(turn, "convai_llm_service_tt_last_sentence")
            tts_ttfb = extract_metric(turn, "convai_tts_service_ttfb")
            if llm_ttfb is not None:
                llm_ttfb_values.append(llm_ttfb)
            if llm_ttf_sentence is not None:
                llm_ttf_sentence_values.append(llm_ttf_sentence)
            if llm_last_sentence is not None:
                llm_last_sentence_values.append(llm_last_sentence)
            if tts_ttfb is not None:
                tts_ttfb_values.append(tts_ttfb)

            if last_meaningful_user_turn and current_time is not None:
                previous_time = last_meaningful_user_turn.get("time_in_call_secs")
                if previous_time is not None:
                    user_to_agent_gaps.append({
                        "user_index": last_meaningful_user_turn["index"],
                        "agent_index": i,
                        "user_time_in_call_secs": previous_time,
                        "agent_time_in_call_secs": current_time,
                        "gap_secs": round(current_time - previous_time, 3),
                        "user_message": last_meaningful_user_turn["message"],
                        "agent_message": msg,
                    })
                last_meaningful_user_turn = None

            agent_only_streak.append({
                "index": i,
                "time_in_call_secs": current_time,
                "message": msg,
            })

            if "[" in msg and "]" in msg:
                issues.append({
                    "type": "bracketed_stage_direction",
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "message": msg,
                })

            if matches_any(msg, SPOKEN_TOOL_TEXT_PATTERNS):
                issues.append({
                    "type": "spoken_tool_pseudocode",
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "message": msg,
                })

            if matches_any(msg, CLOSE_PATTERNS):
                normal_close_messages.append({
                    "index": i,
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "message": msg,
                })

        elif role != "agent" or tool_name or (turn.get("tool_calls") or []):
            append_agent_streak_issues(issues, agent_only_streak)
            agent_only_streak = []

    if first_agent_message_index is not None:
        first_agent_msg = turns[first_agent_message_index].get("message") or ""
        first_agent_msg_norm = norm(first_agent_msg)
        if EXPECTED_OPENER_SNIPPET not in first_agent_msg_norm:
            issue_type = "opener_not_first_agent_message"
            if first_agent_msg_norm.startswith(EXPECTED_OPENER_START) and opener_index is not None:
                issue_type = "opener_micro_fragment_before_full_opener"
            issues.append({
                "type": issue_type,
                "time_in_call_secs": turns[first_agent_message_index].get("time_in_call_secs"),
                "first_agent_message": first_agent_msg,
                "opener_index": opener_index,
            })
    elif turns:
        issues.append({
            "type": "missing_exact_opener",
            "message": "Conversation has transcript turns, but no agent opener message was found.",
        })

    gap_breakdown = []
    for gap in user_to_agent_gaps:
        user_turn = turns[gap["user_index"]]
        agent_turn = turns[gap["agent_index"]]
        intermediate_turns = turns[gap["user_index"] + 1:gap["agent_index"]]
        user_asr_latency = extract_metric(user_turn, "convai_asr_trailing_service_latency")
        agent_llm_ttfb = extract_metric(agent_turn, "convai_llm_service_ttfb")
        agent_llm_ttf_sentence = extract_metric(agent_turn, "convai_llm_service_ttf_sentence")
        agent_llm_last_sentence = extract_metric(agent_turn, "convai_llm_service_tt_last_sentence")
        agent_tts_ttfb = extract_metric(agent_turn, "convai_tts_service_ttfb")
        speech_tool_generation_latency = extract_metric(agent_turn, "convai_llm_tool_request_generation_latency")
        intermediate_tool_generation_values = [
            extract_metric(turn, "convai_llm_tool_request_generation_latency")
            for turn in intermediate_turns
        ]
        intermediate_tool_generation_values = [
            value for value in intermediate_tool_generation_values if value is not None
        ]
        intermediate_tool_generation_latency = (
            sum(intermediate_tool_generation_values) if intermediate_tool_generation_values else None
        )
        intermediate_tool_latency = sum_tool_result_latencies(intermediate_turns)
        known_components = [
            value
            for value in [
                user_asr_latency,
                intermediate_tool_generation_latency,
                intermediate_tool_latency,
                agent_llm_ttfb,
                agent_tts_ttfb,
            ]
            if value is not None
        ]
        known_path_secs = sum(known_components) if known_components else None
        unexplained_overhead_secs = None
        if known_path_secs is not None:
            unexplained_overhead_secs = gap["gap_secs"] - known_path_secs
        gap_breakdown.append({
            "user_index": gap["user_index"],
            "agent_index": gap["agent_index"],
            "gap_secs": gap["gap_secs"],
            "user_time_in_call_secs": gap["user_time_in_call_secs"],
            "agent_time_in_call_secs": gap["agent_time_in_call_secs"],
            "user_asr_trailing_secs": round_or_none(user_asr_latency),
            "agent_llm_ttfb_secs": round_or_none(agent_llm_ttfb),
            "agent_llm_ttf_sentence_secs": round_or_none(agent_llm_ttf_sentence),
            "agent_llm_last_sentence_secs": round_or_none(agent_llm_last_sentence),
            "agent_tts_ttfb_secs": round_or_none(agent_tts_ttfb),
            "agent_tool_request_generation_secs": round_or_none(speech_tool_generation_latency),
            "intermediate_tool_request_generation_secs": round_or_none(intermediate_tool_generation_latency),
            "intermediate_tool_latency_secs": round_or_none(intermediate_tool_latency),
            "intermediate_tool_names": collect_tool_names(intermediate_turns),
            "known_path_secs": round_or_none(known_path_secs),
            "estimated_unexplained_overhead_secs": round_or_none(unexplained_overhead_secs),
            "user_message": gap["user_message"],
            "agent_message": gap["agent_message"],
        })

    for item in gap_breakdown:
        item["likely_primary_bottleneck"] = classify_gap_bottleneck(item)

    # Duplicate close vs end_call message
    if end_call_message:
        for item in normal_close_messages:
            if norm(item["message"]) == norm(end_call_message):
                if is_end_call_spoken_projection(turns, item["index"], first_end_call_index, end_call_message):
                    continue
                issues.append({
                    "type": "duplicate_close_before_end_call",
                    "time_in_call_secs": item["time_in_call_secs"],
                    "message": item["message"],
                    "end_call_message": end_call_message,
                })

    # Line-check after a real post-opener user reply
    if first_post_opener_user_reply_index is not None:
        for i, turn in enumerate(turns):
            if i <= first_post_opener_user_reply_index:
                continue
            if turn.get("role") != "agent":
                continue
            msg = turn.get("message") or ""
            if matches_any(msg, LINE_CHECK_PATTERNS):
                issues.append({
                    "type": "line_check_after_meaningful_post_opener_reply",
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "message": msg,
                })

    # Filler during finalization window
    if first_call_log_index is not None:
        finalization_start = first_call_log_index
        for item in normal_close_messages:
            if item["index"] < first_call_log_index:
                finalization_start = min(finalization_start, item["index"])
        for i, turn in enumerate(turns):
            if i < finalization_start:
                continue
            if turn.get("role") != "agent":
                continue
            msg = turn.get("message") or ""
            if matches_any(msg, FILLER_PATTERNS):
                issues.append({
                    "type": "filler_during_finalization",
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "message": msg,
                })

    # Normal assistant speech after call_log
    if first_call_log_index is not None:
        for i, turn in enumerate(turns):
            if i <= first_call_log_index:
                continue
            if turn.get("role") != "agent":
                continue
            msg = (turn.get("message") or "").strip()
            if not msg:
                continue
            if is_end_call_spoken_projection(turns, i, first_end_call_index, end_call_message):
                continue
            issues.append({
                "type": "normal_assistant_speech_after_call_log",
                "time_in_call_secs": turn.get("time_in_call_secs"),
                "message": msg,
            })

    # Final close spoken before call_log
    if first_call_log_index is not None:
        for item in normal_close_messages:
            if item["index"] < first_call_log_index:
                issues.append({
                    "type": "final_close_spoken_before_call_log",
                    "time_in_call_secs": item["time_in_call_secs"],
                    "message": item["message"],
                })

    # Missing end_call after call_log
    if first_call_log_index is not None and first_end_call_index is None:
        issues.append({
            "type": "call_log_without_end_call",
            "time_in_call_secs": turns[first_call_log_index].get("time_in_call_secs"),
            "message": "call_log was executed, but end_call tool was never called.",
        })

    # Helpdesk tails in outbound finalization
    for turn in turns:
        if turn.get("role") != "agent":
            continue
        msg = turn.get("message") or ""
        if msg and matches_any(msg, HELPDESK_TAIL_PATTERNS):
            issues.append({
                "type": "helpdesk_tail_in_outbound_close",
                "time_in_call_secs": turn.get("time_in_call_secs"),
                "message": msg,
            })

    # Placeholder conv values in tool calls
    for turn in turns:
        for call in turn.get("tool_calls") or []:
            payload = call.get("params_as_json")
            payload_text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
            if any(re.search(p, payload_text, flags=re.IGNORECASE) for p in PLACEHOLDER_PATTERNS):
                issues.append({
                    "type": "placeholder_conversation_id_in_tool_call",
                    "time_in_call_secs": turn.get("time_in_call_secs"),
                    "tool_name": call.get("tool_name"),
                    "params_as_json": payload_text,
                })

    # context_fetch before opener
    if opener_index is not None:
        for i, turn in enumerate(turns):
            if i >= opener_index:
                break
            for call in turn.get("tool_calls") or []:
                if call.get("tool_name") == "context_fetch":
                    issues.append({
                        "type": "context_fetch_before_opener",
                        "time_in_call_secs": turn.get("time_in_call_secs"),
                        "tool_name": "context_fetch",
                    })

    # Machine-transfer phrase appeared, but the agent still continued dialogue
    if first_machine_transfer_user_turn is not None:
        for i, turn in enumerate(turns):
            if i <= first_machine_transfer_user_turn["index"]:
                continue
            if turn.get("role") != "agent":
                continue
            msg = (turn.get("message") or "").strip()
            if not msg:
                continue
            issues.append({
                "type": "machine_transfer_phrase_reached_agent_dialogue",
                "time_in_call_secs": turn.get("time_in_call_secs"),
                "user_message": first_machine_transfer_user_turn["message"],
                "agent_message": msg,
            })
            break

    # Long user -> agent response gaps
    for gap in user_to_agent_gaps:
        if gap["gap_secs"] > DEFAULT_LONG_GAP_SECONDS:
            matching_breakdown = next(
                (
                    item
                    for item in gap_breakdown
                    if item["user_index"] == gap["user_index"] and item["agent_index"] == gap["agent_index"]
                ),
                None,
            )
            issues.append({
                "type": "long_user_to_agent_gap",
                "gap_secs": gap["gap_secs"],
                "user_index": gap["user_index"],
                "agent_index": gap["agent_index"],
                "user_message": gap["user_message"],
                "agent_message": gap["agent_message"],
                "estimated_unexplained_overhead_secs": (
                    None if matching_breakdown is None else matching_breakdown["estimated_unexplained_overhead_secs"]
                ),
                "intermediate_tool_names": (
                    [] if matching_breakdown is None else matching_breakdown["intermediate_tool_names"]
                ),
                "likely_primary_bottleneck": (
                    None if matching_breakdown is None else matching_breakdown["likely_primary_bottleneck"]
                ),
            })

    append_agent_streak_issues(issues, agent_only_streak)

    primary_bottleneck_counts = summarize_bottlenecks(gap_breakdown)
    recommendations = build_recommendations(issues, primary_bottleneck_counts)

    summary = {
        "file": str(path),
        "conversation_id": data.get("conversation_id"),
        "branch_id": data.get("branch_id"),
        "version_id": data.get("version_id"),
        "call_summary_title": ((data.get("analysis") or {}).get("call_summary_title")),
        "termination_reason": ((data.get("metadata") or {}).get("termination_reason")),
        "timing_summary": {
            "long_gap_threshold_secs": DEFAULT_LONG_GAP_SECONDS,
            "user_to_agent_gap_stats_secs": summarize_numeric([item["gap_secs"] for item in user_to_agent_gaps]),
            "first_user_to_agent_gap_secs": user_to_agent_gaps[0]["gap_secs"] if user_to_agent_gaps else None,
            "known_path_stats_secs": summarize_numeric([
                item["known_path_secs"] for item in gap_breakdown if item["known_path_secs"] is not None
            ]),
            "unexplained_overhead_stats_secs": summarize_numeric([
                item["estimated_unexplained_overhead_secs"]
                for item in gap_breakdown
                if item["estimated_unexplained_overhead_secs"] is not None
            ]),
            "primary_bottleneck_counts": primary_bottleneck_counts,
            "llm_ttfb_stats_secs": summarize_numeric(llm_ttfb_values),
            "llm_ttf_sentence_stats_secs": summarize_numeric(llm_ttf_sentence_values),
            "llm_last_sentence_stats_secs": summarize_numeric(llm_last_sentence_values),
            "tts_ttfb_stats_secs": summarize_numeric(tts_ttfb_values),
            "gap_breakdown": gap_breakdown,
        },
        "recommendations": recommendations,
        "issues_count": len(issues),
        "issues": issues,
    }
    return summary


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_eleven_conversation.py CONVERSATION_JSON [...]", file=sys.stderr)
        sys.exit(1)

    results = [analyze(Path(arg)) for arg in sys.argv[1:]]
    if len(results) == 1:
        print(json.dumps(results[0], ensure_ascii=False, indent=2))
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
