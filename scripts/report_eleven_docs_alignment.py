#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


DOC_SOURCES = {
    "conversation_flow": "https://elevenlabs.io/docs/eleven-agents/customization/conversation-flow",
    "latency_optimization": "https://elevenlabs.io/docs/eleven-api/guides/how-to/best-practices/latency-optimization",
    "voice_settings": "https://elevenlabs.io/docs/eleven-creative/playground/text-to-speech",
    "prompting_guide": "https://elevenlabs.io/docs/eleven-agents/best-practices/prompting-guide",
    "pronunciation_dictionary": "https://elevenlabs.io/docs/eleven-agents/customization/voice/pronunciation-dictionary",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(agent):
    turn = ((agent.get("conversation_config") or {}).get("turn") or {})
    convo = ((agent.get("conversation_config") or {}).get("conversation") or {})
    tts = ((agent.get("conversation_config") or {}).get("tts") or {})
    soft_cfg = turn.get("soft_timeout_config") or {}

    client_events = convo.get("client_events") or []
    turn_timeout = turn.get("turn_timeout")
    turn_eagerness = turn.get("turn_eagerness")
    soft_timeout = soft_cfg.get("timeout_seconds")
    interruptions_enabled = "interruption" in client_events
    stability = tts.get("stability")
    similarity = tts.get("similarity_boost")
    speed = tts.get("speed")
    soft_message = soft_cfg.get("message")
    soft_llm_generated = soft_cfg.get("use_llm_generated_message")
    soft_prompt_override = soft_cfg.get("llm_generated_message_prompt_override") or ""

    findings = []
    suggested_next_experiments = []

    if not interruptions_enabled:
        findings.append({
            "severity": "high",
            "code": "interruptions_likely_disabled",
            "title": "Interruptions likely disabled in current published branch",
            "why": (
                "Official ElevenLabs conversation-flow docs say interruptions are enabled by selecting "
                "`interruption` as a client event. It is absent from the current published snapshot."
            ),
            "observed": {
                "client_events": client_events,
            },
            "docs_source": DOC_SOURCES["conversation_flow"],
        })
        suggested_next_experiments.append({
            "priority": 1,
            "code": "enable_interruptions_in_lab",
            "action": "Enable `interruption` in `conversation.client_events` on a lab-only branch and re-test barge-in behavior.",
        })

    if isinstance(turn_timeout, (int, float)):
        if turn_timeout < 2.0:
            findings.append({
                "severity": "high",
                "code": "turn_timeout_very_aggressive",
                "title": "Turn timeout is much more aggressive than Eleven customer-service examples",
                "why": (
                    "Official docs allow 1-30 seconds, but their customer-service examples use shorter timeouts "
                    "in the 5-10 second band. 1.78 seconds is intentionally aggressive and may increase cut-offs "
                    "or premature turn-grabs on a noisy phone line."
                ),
                "observed": {"turn_timeout": turn_timeout},
                "docs_source": DOC_SOURCES["conversation_flow"],
            })
            suggested_next_experiments.append({
                "priority": 2,
                "code": "raise_turn_timeout_slightly",
                "action": "Test a small lab-only increase of `turn_timeout` into roughly the 2.2-2.5 second band.",
            })

    if turn_eagerness == "eager":
        findings.append({
            "severity": "medium",
            "code": "turn_eagerness_is_eager",
            "title": "Published branch uses eager turn eagerness",
            "why": (
                "Official docs say eager mode suits fast responsive conversations, while patient mode gives users "
                "more space. For this outbound sales use case, eager may be fine for pace, but combined with a very "
                "short timeout it can make the agent feel interruptive."
            ),
            "observed": {"turn_eagerness": turn_eagerness},
            "docs_source": DOC_SOURCES["conversation_flow"],
        })
        suggested_next_experiments.append({
            "priority": 3,
            "code": "test_normal_turn_eagerness",
            "action": "Prepare a lab-only branch with `turn_eagerness=normal` while preserving the current prompt and voice stack.",
        })

    if isinstance(soft_timeout, (int, float)):
        findings.append({
            "severity": "info",
            "code": "soft_timeout_present",
            "title": "Soft timeout is already enabled for filler masking",
            "why": (
                "This aligns with ElevenLabs conversation-flow guidance: soft timeout provides natural audio feedback "
                "when the assistant needs time to think."
            ),
            "observed": {"soft_timeout_seconds": soft_timeout},
            "docs_source": DOC_SOURCES["conversation_flow"],
        })
        if soft_timeout < 3.0:
            findings.append({
                "severity": "medium",
                "code": "soft_timeout_faster_than_recommended_start",
                "title": "Soft timeout is faster than ElevenLabs recommended starting point",
                "why": (
                    "Official conversation-flow docs recommend starting soft timeout at 3.0 seconds. "
                    "The current 1.9-second value will mask pauses earlier, but it can also make the "
                    "assistant sound more obviously synthetic if fillers trigger too often."
                ),
                "observed": {"soft_timeout_seconds": soft_timeout},
                "docs_source": DOC_SOURCES["conversation_flow"],
            })
            suggested_next_experiments.append({
                "priority": 4,
                "code": "test_soft_timeout_22_to_25",
                "action": "If fillers feel too eager or bot-like, test a lab-only soft-timeout increase into roughly the 2.2-2.5 second band before jumping to 3.0.",
            })

    if soft_llm_generated:
        findings.append({
            "severity": "info",
            "code": "llm_generated_soft_fillers_enabled",
            "title": "LLM-generated soft fillers are enabled",
            "why": (
                "This matches the newer ElevenLabs soft-timeout capability and can sound more natural than a single static filler, "
                "as long as the filler prompt stays tight and does not drift into line-checks or sales copy."
            ),
            "observed": {
                "use_llm_generated_message": soft_llm_generated,
                "fallback_message": soft_message,
            },
            "docs_source": DOC_SOURCES["conversation_flow"],
        })

    soft_prompt_lower = soft_prompt_override.lower()
    if "секунд" in soft_prompt_lower or "секунду" in soft_prompt_lower:
        findings.append({
            "severity": "medium",
            "code": "soft_timeout_prompt_uses_time_promise_examples",
            "title": "Soft-timeout filler prompt still hints at time-promise phrasing",
            "why": (
                "Official ElevenLabs docs advise avoiding time-indicator fillers like 'one second' because actual response time is unpredictable. "
                "The current prompt override still includes an example shaped like 'Секунду...'."
            ),
            "observed": {
                "llm_generated_message_prompt_override": soft_prompt_override,
            },
            "docs_source": DOC_SOURCES["conversation_flow"],
        })
        suggested_next_experiments.append({
            "priority": 5,
            "code": "remove_time_promises_from_soft_fillers",
            "action": "Rewrite the lab filler prompt to prefer neutral thinking sounds like `Да...`, `Так...`, or `Угу...` instead of time-promise examples.",
        })

    voice_band_ok = (
        isinstance(stability, (int, float))
        and isinstance(similarity, (int, float))
        and 0.35 <= stability <= 0.55
        and 0.7 <= similarity <= 0.82
    )
    if voice_band_ok:
        findings.append({
            "severity": "info",
            "code": "voice_settings_near_common_band",
            "title": "Voice settings are already close to Eleven common recommendations",
            "why": (
                "Official voice docs describe a common starting point around stability 50 and similarity 75. "
                "Current settings are already close to that band."
            ),
            "observed": {
                "stability": stability,
                "similarity_boost": similarity,
                "speed": speed,
            },
            "docs_source": DOC_SOURCES["voice_settings"],
        })

    if isinstance(speed, (int, float)) and speed > 1.0:
        findings.append({
            "severity": "info",
            "code": "speed_above_default",
            "title": "Speech speed is already faster than default",
            "why": (
                "Official docs say speed 1.0 is the default and values above it speed up delivery. "
                "The current branch already uses a slightly faster delivery."
            ),
            "observed": {"speed": speed},
            "docs_source": DOC_SOURCES["voice_settings"],
        })

    suggested_next_experiments.sort(key=lambda item: item["priority"])

    return {
        "agent_id": agent.get("agent_id"),
        "branch_id": agent.get("branch_id"),
        "version_id": agent.get("version_id"),
        "observed": {
            "turn_timeout": turn_timeout,
            "turn_eagerness": turn_eagerness,
            "interruptions_enabled": interruptions_enabled,
            "client_events": client_events,
            "soft_timeout_seconds": soft_timeout,
            "tts_model": tts.get("model_id"),
            "stability": stability,
            "similarity_boost": similarity,
            "speed": speed,
            "expressive_mode": tts.get("expressive_mode"),
        },
        "docs_sources": DOC_SOURCES,
        "findings": findings,
        "suggested_next_experiments": suggested_next_experiments,
        "summary": {
            "main_risk": (
                "Current branch likely feels interruptive because interruptions appear disabled while turn-taking remains aggressive."
                if not interruptions_enabled and turn_eagerness == "eager" and isinstance(turn_timeout, (int, float)) and turn_timeout < 2.0
                else "No single dominant documentation mismatch detected."
            )
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Compare current Eleven agent snapshot against official-doc guidance.")
    parser.add_argument("source_json", help="Agent response.json snapshot")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    agent = load_json(Path(args.source_json))
    report = build_report(agent)
    payload = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
