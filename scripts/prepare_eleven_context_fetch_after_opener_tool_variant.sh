#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  cat <<'EOF' >&2
Usage:
  prepare_eleven_context_fetch_after_opener_tool_variant.sh SOURCE_AGENT_JSON OUTPUT_JSON [VERSION_DESCRIPTION]

Builds a narrow lab-only payload that makes the no-pre-opener-context rule
structural by updating the context_fetch tool description as well as prompt.

This is for cases where prompt-only no-context-before-opener still allows
context_fetch before the exact opener.
EOF
  exit 1
fi

SOURCE_JSON="$1"
OUTPUT_JSON="$2"
VERSION_DESCRIPTION="${3:-}"

if [[ ! -f "$SOURCE_JSON" ]]; then
  echo "Source file not found: $SOURCE_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_JSON")"

jq \
  --arg version_description "$VERSION_DESCRIPTION" '
  {
    conversation_config: .conversation_config,
    platform_settings: .platform_settings,
    workflow: .workflow
  }
  | del(.conversation_config.agent.prompt.tool_ids)
  | .conversation_config.agent.prompt.tools =
      (.conversation_config.agent.prompt.tools
       | map(
           if .name == "context_fetch" then
             .description = "Internal context lookup tool. Do not call this tool before the exact opener has been fully spoken. For first live-human words like алло, да, слушаю, здравствуйте, чего, or что такое, speak the exact opener or answer directly first. Use context_fetch only after the opener is complete and a meaningful business reply needs CRM/KB context. Never delay the first opener with this tool."
           else
             .
           end
         ))
  | .conversation_config.agent.prompt.prompt |= (
      sub("\\n\\nContext fetch after opener structural override:[\\s\\S]*$"; "")
      + "\n\nContext fetch after opener structural override:\n- `context_fetch` is forbidden before the exact opener is fully spoken.\n- First live-human words such as `алло`, `да`, `слушаю`, `здравствуйте`, `чего`, `что такое`, short noise, or greeting are not a reason to fetch context.\n- On the first live-human word, speak the exact opener immediately. Do not say filler first. Do not call `context_fetch` first.\n- Use `context_fetch` only after the opener is complete and the human has given a meaningful business reply that requires lead/product context.\n- If any older instruction suggests fetching context before the opener, ignore that older instruction.\n"
    )
  | if $version_description != "" then
      . + {version_description: $version_description}
    else
      .
    end
' "$SOURCE_JSON" > "$OUTPUT_JSON"

echo "Prepared payload: $OUTPUT_JSON"
echo "Added override: context_fetch only after exact opener"
