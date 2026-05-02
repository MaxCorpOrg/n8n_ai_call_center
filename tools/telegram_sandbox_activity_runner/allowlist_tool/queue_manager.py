from __future__ import annotations

from dataclasses import replace

from .models import AccountRecord, ActionRecord, AllowlistRecord, QueuedAction


class QueueManager:
    def __init__(
        self,
        *,
        accounts: dict[str, AccountRecord],
        allowlist: dict[str, AllowlistRecord],
    ) -> None:
        self.accounts = accounts
        self.allowlist = allowlist

    def build_queue(self, actions: list[ActionRecord]) -> list[QueuedAction]:
        queued: list[QueuedAction] = []
        for action in actions:
            queued_action = QueuedAction(
                action_id=action.action_id,
                action_type=action.action_type,
                account_id=action.account_id,
                target_entity_id=action.target_entity_id,
                target_group_id=action.target_group_id,
                message_text=action.message_text,
                notes=action.notes,
            )
            reasons = self._preflight_reasons(action)
            if reasons:
                queued_action = replace(
                    queued_action,
                    status="blocked",
                    block_reason="; ".join(reasons),
                    metadata={"preflight_reasons": reasons},
                )
            queued.append(queued_action)
        return queued

    def _preflight_reasons(self, action: ActionRecord) -> list[str]:
        reasons: list[str] = []
        account = self.accounts.get(action.account_id)
        if account is None:
            reasons.append(f"unknown account_id={action.account_id}")
        elif not account.enabled:
            reasons.append(f"account {action.account_id} is disabled")

        target = self.allowlist.get(action.target_entity_id)
        if target is None:
            reasons.append(f"target_entity_id={action.target_entity_id} is not present in allowlist.csv")
            return reasons

        if not target.consent_confirmed:
            reasons.append(f"target entity {target.entity_id} is missing consent_confirmed=yes")

        if action.action_type != "validate" and action.action_type not in target.allowed_actions:
            reasons.append(f"target entity {target.entity_id} does not allow action {action.action_type}")

        if action.action_type == "send_message" and not action.message_text.strip():
            reasons.append("send_message requires non-empty message_text")

        if action.action_type == "add_to_group":
            if not action.target_group_id:
                reasons.append("add_to_group requires target_group_id")
            else:
                group = self.allowlist.get(action.target_group_id)
                if group is None:
                    reasons.append(f"target_group_id={action.target_group_id} is not present in allowlist.csv")
                else:
                    if group.kind_hint not in {"group", "channel"}:
                        reasons.append(
                            f"target group {group.entity_id} must have kind_hint=group or channel, got {group.kind_hint or 'unknown'}"
                        )
                    if not group.consent_confirmed:
                        reasons.append(f"target group {group.entity_id} is missing consent_confirmed=yes")

        return reasons
