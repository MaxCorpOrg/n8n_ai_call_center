#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_price_anchor_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Example:
  scripts/prepare_eleven_price_anchor_variant.sh \
    .runtime/eleven_lab_finalization_interrupt_fix_2026-06-17/apply_result/response.json \
    .runtime/eleven_lab_price_anchor_fix_2026-06-17/payload.json \
    "Lab: price anchor clarification fix"

Builds a minimal payload that adds only a narrow price-answer rule:
  - do not volunteer price on your own
  - when the person asks about price or cost,
    answer briefly with the documented anchor price
  - then move to SMS / manager confirmation
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_JSON="$2"
VERSION_DESCRIPTION="${3:-}"
ANCHOR_JSON="${ANCHOR_JSON:-/home/max/n8n_ai_call_center/docs/agent_kb_lipolong/10_COMMERCIAL_ANCHOR_RU.json}"

if [[ ! -f "$SOURCE_JSON" ]]; then
  echo "Source file not found: $SOURCE_JSON" >&2
  exit 1
fi

if [[ ! -f "$ANCHOR_JSON" ]]; then
  echo "Anchor file not found: $ANCHOR_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSON")"

PRICE_ANCHOR_TEXT="$(jq -r '.price_anchor_text_ru' "$ANCHOR_JSON")"
MIN_ORDER_TEXT="$(jq -r '.min_order_text_ru' "$ANCHOR_JSON")"
TEST_PACK_TEXT="$(jq -r '.test_pack_text_ru' "$ANCHOR_JSON")"
DELIVERY_TEXT="$(jq -r '.delivery_text_ru' "$ANCHOR_JSON")"
PAYMENT_TEXT="$(jq -r '.payment_prompt_text_ru' "$ANCHOR_JSON")"

jq \
  --arg version_description "$VERSION_DESCRIPTION" \
  --arg price_anchor_text "$PRICE_ANCHOR_TEXT" \
  --arg min_order_text "$MIN_ORDER_TEXT" \
  --arg test_pack_text "$TEST_PACK_TEXT" \
  --arg delivery_text "$DELIVERY_TEXT" \
  --arg payment_text "$PAYMENT_TEXT" '
  {
    conversation_config: .conversation_config,
    platform_settings: .platform_settings,
    workflow: .workflow
  }
  | del(.conversation_config.agent.prompt.tool_ids)
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nPrice-answer anchor override:[\\s\\S]*$"; "")
      + "\n\nPrice-answer anchor override:\n- Do not volunteer price on your own in the opener, normal pitch, or proactive product explanation.\n- Before the user directly asks about price, do not mention any commercial anchor details from this block at all.\n- That means: do not proactively mention price, cost, 19 000 rubles, minimum order, start from one unit, test pack, delivery terms, payment terms, price list, pricing sheet, or price conditions.\n- Before the user directly asks about price, do not proactively use wording like: прайс, прайс-лист, цены, условия по цене.\n- Before a direct price question, if you offer a next step, offer only short info, key differences, contacts, or a manager callback.\n- If the user is relevant and works with the category but has not asked about price, your value turn should stay non-commercial: official supply, originality, comparison, calm test, fit for practice.\n- Mention price only if the user directly asks about price, cost, how much it costs, or whether the test pack is free.\n- Only after that direct price question may you reveal the commercial anchor.\n- If the user asks, answer directly and briefly instead of dodging.\n- Use the current documented anchor price:\n  - ориентир по стоимости: " + $price_anchor_text + "\n  - старт возможен: " + $min_order_text + "\n  - тестовая упаковка: " + $test_pack_text + ".\n- If useful, you may also mention briefly:\n  - доставка обычно " + $delivery_text + "\n  - оплата: " + $payment_text + "\n- Keep the price answer short: 1 or 2 short sentences max.\n- After the short price answer, move to one next step only:\n  - either offer SMS with the exact details and conditions;\n  - or offer a manager callback for confirmation.\n- Do not turn every interested lead into a price monologue. Give the anchor only on request, clarify briefly, then move forward.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added only: price-answer anchor override"
echo "Anchor source: $ANCHOR_JSON"
