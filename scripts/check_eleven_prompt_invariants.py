#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


EXACT_OPENER = (
    '"Здравствуйте, я официальный представитель липолитика Липолонг. '
    'Это липолитик для косметологов. Вам это интересно?"'
)
DEFAULT_EXPECTED_SOFT_TIMEOUT_SECONDS = 1.9
ACCEPTED_SOFT_TIMEOUT_PROMPT_MARKERS = (
    "only after the exact opener has already finished",
    "only after the exact opener has been fully completed",
)


def load_prompt(data: dict) -> str:
    try:
        return data["conversation_config"]["agent"]["prompt"]["prompt"]
    except KeyError as exc:
        raise SystemExit(f"Missing prompt path in JSON: {exc}") from exc


def load_anchor() -> dict:
    anchor_path = Path(
        "/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/10_COMMERCIAL_ANCHOR_RU.json"
    )
    if not anchor_path.exists():
        raise SystemExit(f"Missing anchor JSON: {anchor_path}")
    return json.loads(anchor_path.read_text(encoding="utf-8"))


def check_contains_once(prompt: str, needle: str, name: str) -> dict:
    count = prompt.count(needle)
    return {
        "name": name,
        "ok": count == 1,
        "count": count,
        "needle": needle,
        "message": "exactly once" if count == 1 else f"expected exactly once, got {count}",
    }


def check_contains(prompt: str, needle: str, name: str) -> dict:
    ok = needle in prompt
    return {
        "name": name,
        "ok": ok,
        "needle": needle,
        "message": "present" if ok else "missing",
    }


def check_equals(actual, expected, name: str) -> dict:
    ok = actual == expected
    return {
        "name": name,
        "ok": ok,
        "expected": expected,
        "value": actual,
        "message": f"exactly {expected}" if ok else f"expected {expected}",
    }


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print(
            "Usage: check_eleven_prompt_invariants.py AGENT_JSON [EXPECTED_SOFT_TIMEOUT_SECONDS]",
            file=sys.stderr,
        )
        return 2

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"File not found: {src}", file=sys.stderr)
        return 2

    expected_soft_timeout_seconds = DEFAULT_EXPECTED_SOFT_TIMEOUT_SECONDS
    if len(sys.argv) == 3:
        expected_soft_timeout_seconds = float(sys.argv[2])

    data = json.loads(src.read_text(encoding="utf-8"))
    prompt = load_prompt(data)
    anchor = load_anchor()
    soft_timeout = (
        data.get("conversation_config", {})
        .get("turn", {})
        .get("soft_timeout_config", {})
    )

    price_anchor_text = anchor["price_anchor_text_ru"]
    min_order_text = anchor["min_order_text_ru"]
    test_pack_text = anchor["test_pack_text_ru"]
    delivery_text = anchor["delivery_text_ru"]
    payment_text = anchor["payment_prompt_text_ru"]

    checks = [
        check_contains_once(prompt, "Price-answer anchor override:", "price_block_once"),
        check_contains(prompt, "Do not volunteer price on your own", "price_not_volunteered"),
        check_contains(prompt, "do not mention any commercial anchor details from this block at all", "no_proactive_commercial_anchor"),
        check_contains(prompt, "do not proactively mention price, cost, 19 000 rubles, minimum order, start from one unit, test pack, delivery terms, payment terms, price list, pricing sheet, or price conditions", "no_proactive_price_list_offer"),
        check_contains(prompt, "do not proactively use wording like: прайс, прайс-лист, цены, условия по цене", "no_proactive_price_words"),
        check_contains(prompt, "your value turn should stay non-commercial: official supply, originality, comparison, calm test, fit for practice", "non_commercial_value_turn"),
        check_contains(prompt, "Mention price only if the user directly asks", "price_only_on_direct_ask"),
        check_contains(prompt, f"ориентир по стоимости: {price_anchor_text}", "price_anchor_value"),
        check_contains(prompt, f"старт возможен: {min_order_text}", "price_anchor_min_order"),
        check_contains(prompt, f"тестовая упаковка: {test_pack_text}.", "price_anchor_not_free"),
        check_contains(prompt, f"доставка обычно {delivery_text}", "price_anchor_delivery"),
        check_contains(prompt, f"оплата: {payment_text}", "price_anchor_payment"),
        check_contains_once(prompt, EXACT_OPENER, "exact_opener_once"),
        check_contains(prompt, 'You have exactly one rescue line-check for the whole call.', "one_rescue_rule"),
        check_contains(prompt, '"абонент", "абоненту", or "абонентам" means machine', "abonent_hard_stop"),
        check_contains(prompt, 'Treat MTS Defender / МТС Защитник / anti-spam screening', "mts_defender_hard_stop"),
        check_contains(prompt, 'do not leave a message;', "no_machine_message"),
        check_contains(prompt, 'call call_log with `call_result=no_answer` or `busy`', "machine_call_log_rule"),
        check_contains(prompt, 'then end silently.', "machine_silent_end"),
        check_contains_once(prompt, "False-positive ASR gate override:", "false_positive_block_once"),
        check_contains(prompt, "A lone short pickup token like алло, да, угу, ага, or что is ambiguous by default before the opener.", "ambiguous_short_pickup_rule"),
        check_contains(prompt, "stay silent, use skip_turn if needed, and wait for a clearer answer instead of opening sales dialogue.", "skip_turn_before_opener_rule"),
        check_contains(prompt, "Do not classify not_target from a bare single-word Нет alone.", "no_bare_net_not_target"),
        check_contains_once(prompt, "Strict post-opener silence override:", "strict_silence_block_once"),
        check_contains(prompt, "Silence after the opener is a special no-answer state, not a sales state.", "strict_silence_is_no_answer_state"),
        check_contains(prompt, "do not continue discovery, do not explain the product further, and do not offer SMS, callback, or manager options yet.", "strict_silence_no_sales_progression"),
        check_contains(prompt, "you may use exactly one short rescue line-check only once.", "strict_silence_one_rescue_only"),
        check_contains(prompt, "immediately do silent `call_log(no_answer)` and end the call silently.", "strict_silence_silent_no_answer_end"),
        check_contains(prompt, "Do not ask repeated `Алло?` questions.", "strict_silence_no_repeated_allo"),
        check_contains(prompt, "Do not say inbound-support phrases like `Да? Чем могу помочь?`, `Чем могу помочь?`, `Можно перезвонить позже или отправить SMS?`, or similar while the call is still in the silence/no-answer state.", "strict_silence_no_helpdesk_phrases"),
        check_contains(prompt, "Otherwise, silence must end in exactly one no-answer finalization path, not in a loop.", "strict_silence_single_finalization_path"),
        check_contains(prompt, "Rescue micro-cut override:", "rescue_micro_cut_block"),
        check_contains(prompt, "Use only a one- or two-word line-check shape, not a clause.", "rescue_micro_cut_short_shape"),
        check_contains(prompt, "Good shapes: `Алло?`, `Слышно?`, `Да?`", "rescue_micro_cut_good_shapes"),
        check_contains(prompt, "The close should be spoken only through `end_call.system__message_to_speak`, not as a normal assistant response turn.", "single_spoken_close_through_end_call"),
        check_contains(prompt, "Do not produce a normal assistant speech turn and then another spoken copy of the same close inside `end_call`.", "no_duplicate_spoken_close"),
        check_contains(prompt, "Do not say help-desk tails like \"Могу ли я помочь вам ещё чем-то?\"", "no_helpdesk_midcall_phrase"),
    ]

    checks.extend(
        [
            check_equals(soft_timeout.get("message", None), "...", "soft_timeout_message_placeholder"),
            {
                "name": "soft_timeout_prompt_after_opener_only",
                "ok": any(
                    marker in soft_timeout.get("llm_generated_message_prompt_override", "")
                    for marker in ACCEPTED_SOFT_TIMEOUT_PROMPT_MARKERS
                ),
                "value": soft_timeout.get("llm_generated_message_prompt_override", ""),
                "message": "present"
                if any(
                    marker in soft_timeout.get("llm_generated_message_prompt_override", "")
                    for marker in ACCEPTED_SOFT_TIMEOUT_PROMPT_MARKERS
                )
                else "missing",
            },
            check_equals(
                float(soft_timeout.get("timeout_seconds", -1)),
                expected_soft_timeout_seconds,
                "soft_timeout_timeout_expected",
            ),
            check_equals(
                bool(soft_timeout.get("use_llm_generated_message", False)),
                True,
                "soft_timeout_llm_filler_enabled",
            ),
            check_equals(
                bool(soft_timeout.get("randomize_fillers", True)),
                False,
                "soft_timeout_randomize_fillers_disabled",
            ),
            check_equals(
                int(soft_timeout.get("max_soft_timeouts_per_generation", -1)),
                1,
                "soft_timeout_single_fill_per_generation",
            ),
        ]
    )

    failed = [c for c in checks if not c["ok"]]
    result = {
        "source_file": str(src),
        "anchor_source_file": "/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/10_COMMERCIAL_ANCHOR_RU.json",
        "version_id": data.get("version_id"),
        "branch_id": data.get("branch_id"),
        "llm": (
            data.get("conversation_config", {})
            .get("agent", {})
            .get("prompt", {})
            .get("llm")
        ),
        "tts_model_id": (
            data.get("conversation_config", {})
            .get("tts", {})
            .get("model_id")
        ),
        "expected_soft_timeout_seconds": expected_soft_timeout_seconds,
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failed),
        "checks_failed": len(failed),
        "ok": not failed,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
