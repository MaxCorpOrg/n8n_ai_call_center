#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path("/home/max/n8n_ai_call_center")
ANCHOR_PATH = ROOT / "docs/agent_kb_lipolong/10_COMMERCIAL_ANCHOR_RU.json"
PROFILE_PATH = ROOT / "docs/agent_kb_lipolong/01_PRODUCT_PROFILE_RU.md"
SMS_DOC_PATH = ROOT / "docs/call-translation-bridge/09_ELEVEN_TOOL_SEND_SMS_RU.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def contains(text: str, needle: str, name: str) -> dict:
    ok = needle in text
    return {
        "name": name,
        "ok": ok,
        "needle": needle,
        "message": "present" if ok else "missing",
    }


def main() -> int:
    if not ANCHOR_PATH.exists():
        print(f"Missing anchor file: {ANCHOR_PATH}", file=sys.stderr)
        return 2

    anchor = json.loads(read(ANCHOR_PATH))
    profile = read(PROFILE_PATH)
    sms_doc = read(SMS_DOC_PATH)

    price_ru = anchor["price_anchor_text_ru"]
    min_order_units = anchor["min_order_units"]
    delivery_ru = anchor["delivery_text_ru"]
    payment_prompt_ru = anchor["payment_prompt_text_ru"]
    payment_sms_ru = anchor["payment_sms_text_ru"]
    payment_profile_ru = anchor["payment_profile_text_ru"]
    test_pack_free = anchor["test_pack_free"]
    min_order_profile = f"Минимальный заказ: от `{min_order_units}` шт."
    avg_check_profile = f"Ориентир среднего чека: от `{str(anchor['price_anchor_rub'])}` руб."
    delivery_profile = f"Доставка: `{delivery_ru.replace(' дня', '')}` дня."
    payment_profile = f"Оплата: {payment_profile_ru}."
    test_pack_phrase = "не бесплатная" if not test_pack_free else "бесплатная"

    checks = [
        contains(profile, min_order_profile, "profile_min_order"),
        contains(profile, avg_check_profile, "profile_avg_check"),
        contains(profile, delivery_profile, "profile_delivery"),
        contains(profile, payment_profile, "profile_payment"),
        contains(sms_doc, f"Ориентир по стоимости: {price_ru}", "sms_price_anchor"),
        contains(sms_doc, f"заказ от {min_order_units} шт.", "sms_min_order"),
        contains(sms_doc, f"Доставка: {delivery_ru}.", "sms_delivery"),
        contains(sms_doc, f"Оплата: {payment_sms_ru}.", "sms_payment_doc_current"),
        {
            "name": "prompt_payment_channel_defined",
            "ok": bool(payment_prompt_ru),
            "message": "present" if bool(payment_prompt_ru) else "missing",
            "value": payment_prompt_ru,
        },
        {
            "name": "anchor_test_pack_not_free_flag",
            "ok": test_pack_free is False,
            "message": "false as expected" if test_pack_free is False else "unexpected true",
            "value": test_pack_free,
        },
        {
            "name": "anchor_test_pack_phrase",
            "ok": test_pack_phrase == "не бесплатная",
            "message": "matches expected live policy" if test_pack_phrase == "не бесплатная" else "unexpected phrase",
            "value": test_pack_phrase,
        },
    ]

    failed = [c for c in checks if not c["ok"]]
    result = {
        "anchor_source_file": str(ANCHOR_PATH),
        "profile_source_file": str(PROFILE_PATH),
        "sms_doc_source_file": str(SMS_DOC_PATH),
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
