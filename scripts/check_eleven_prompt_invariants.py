#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


EXACT_OPENER = (
    '"Здравствуйте, я официальный представитель липолитика Липолонг. '
    'Это липолитик для косметологов. Вам это интересно?"'
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


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_eleven_prompt_invariants.py AGENT_JSON", file=sys.stderr)
        return 2

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"File not found: {src}", file=sys.stderr)
        return 2

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
    ]

    checks.extend(
        [
            {
                "name": "soft_timeout_message_placeholder",
                "ok": soft_timeout.get("message", None) == "...",
                "value": soft_timeout.get("message", None),
                "message": "exactly ..." if soft_timeout.get("message", None) == "..." else "expected ...",
            },
            {
                "name": "soft_timeout_prompt_after_opener_only",
                "ok": "only after the exact opener has been fully completed" in soft_timeout.get(
                    "llm_generated_message_prompt_override", ""
                ),
                "value": soft_timeout.get("llm_generated_message_prompt_override", ""),
                "message": "present"
                if "only after the exact opener has been fully completed"
                in soft_timeout.get("llm_generated_message_prompt_override", "")
                else "missing",
            },
            {
                "name": "soft_timeout_timeout_3_2",
                "ok": float(soft_timeout.get("timeout_seconds", -1)) == 3.2,
                "value": soft_timeout.get("timeout_seconds", None),
                "message": "exactly 3.2" if float(soft_timeout.get("timeout_seconds", -1)) == 3.2 else "expected 3.2",
            },
        ]
    )

    failed = [c for c in checks if not c["ok"]]
    result = {
        "source_file": str(src),
        "anchor_source_file": "/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/10_COMMERCIAL_ANCHOR_RU.json",
        "version_id": data.get("version_id"),
        "branch_id": data.get("branch_id"),
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
