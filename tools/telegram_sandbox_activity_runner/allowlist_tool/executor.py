from __future__ import annotations

from typing import Any, Callable

from .audit_log import AuditLogger
from .models import ActionResult, AllowlistRecord, QueuedAction
from .safety import AccountBlockedError, SafetyController, SafetyViolation
from .telethon_client import TelethonRuntime
from .validator import EntityValidator, classify_entity


class ActionExecutor:
    def __init__(
        self,
        runtime: TelethonRuntime,
        *,
        allowlist: dict[str, AllowlistRecord],
        account_id: str,
        safety: SafetyController,
        audit_logger: AuditLogger,
        confirm_fn: Callable[[str], str] | None = None,
    ) -> None:
        self.runtime = runtime
        self.allowlist = allowlist
        self.account_id = account_id
        self.safety = safety
        self.audit_logger = audit_logger
        self.confirm_fn = confirm_fn or input
        self.validator = EntityValidator(
            runtime,
            account_id=account_id,
            safety=safety,
            audit_logger=audit_logger,
        )

    def execute(self, action: QueuedAction) -> ActionResult:
        if action.status != "pending":
            result = ActionResult(
                action_id=action.action_id,
                action_type=action.action_type,
                account_id=action.account_id,
                status="blocked",
                outcome="preflight_blocked",
                target_entity_id=action.target_entity_id,
                target_group_id=action.target_group_id,
                message=action.block_reason,
                details={"metadata": action.metadata},
            )
            self.audit_logger.log_result(result)
            return result

        if self.safety.is_account_blocked(self.account_id):
            result = ActionResult(
                action_id=action.action_id,
                action_type=action.action_type,
                account_id=action.account_id,
                status="blocked",
                outcome="account_blocked",
                target_entity_id=action.target_entity_id,
                target_group_id=action.target_group_id,
                message="Account is blocked after a previous suspicious Telegram response.",
            )
            self.audit_logger.log_result(result)
            return result

        if action.action_type == "validate":
            return self._execute_validate(action)
        if action.action_type == "send_message":
            return self._execute_send_message(action)
        if action.action_type == "add_to_group":
            return self._execute_add_to_group(action)

        result = ActionResult(
            action_id=action.action_id,
            action_type=action.action_type,
            account_id=action.account_id,
            status="error",
            outcome="unsupported_action_type",
            target_entity_id=action.target_entity_id,
            target_group_id=action.target_group_id,
            message=f"Unsupported action_type={action.action_type}",
        )
        self.audit_logger.log_result(result)
        return result

    def _execute_validate(self, action: QueuedAction) -> ActionResult:
        target = self.allowlist[action.target_entity_id]
        try:
            self.safety.begin_action(self.account_id)
        except SafetyViolation as exc:
            result = ActionResult(
                action_id=action.action_id,
                action_type=action.action_type,
                account_id=action.account_id,
                status="blocked",
                outcome="rate_limited",
                target_entity_id=target.entity_id,
                message=str(exc),
            )
            self.audit_logger.log_result(result)
            return result

        validation = self.validator.validate_entry(target)
        status = str(validation.get("status") or "error")
        outcome = "validated" if status == "ok" else status
        result = ActionResult(
            action_id=action.action_id,
            action_type=action.action_type,
            account_id=action.account_id,
            status=status,
            outcome=outcome,
            target_entity_id=target.entity_id,
            message=str(validation.get("error") or ""),
            details=validation,
        )
        self.audit_logger.log_result(result)
        return result

    def _execute_send_message(self, action: QueuedAction) -> ActionResult:
        target = self.allowlist[action.target_entity_id]
        if not self._confirm_action(
            action,
            (
                f"Action {action.action_id}: send message from account {self.account_id} "
                f"to {target.username}.\nMessage:\n{action.message_text}\n\nType YES to continue: "
            ),
        ):
            result = ActionResult(
                action_id=action.action_id,
                action_type=action.action_type,
                account_id=action.account_id,
                status="skipped",
                outcome="manual_decline",
                target_entity_id=target.entity_id,
                message="Operator declined manual confirmation.",
            )
            self.audit_logger.log_result(result)
            return result

        try:
            self.safety.begin_action(self.account_id)
            target_entity = self.validator.resolve_allowlisted_entity(target)
            entity_type = classify_entity(target_entity, self.runtime.types)
            if entity_type not in {"user", "bot"}:
                result = ActionResult(
                    action_id=action.action_id,
                    action_type=action.action_type,
                    account_id=action.account_id,
                    status="blocked",
                    outcome="unsupported_target_type",
                    target_entity_id=target.entity_id,
                    message=f"send_message only supports user or bot targets, got {entity_type}",
                )
                self.audit_logger.log_result(result)
                return result

            message = action.message_text.strip()
            sent = self._call_with_retry(
                lambda: self.runtime.client.send_message(target_entity, message),
                action=action,
                operation_name="send_message",
            )
            result = ActionResult(
                action_id=action.action_id,
                action_type=action.action_type,
                account_id=action.account_id,
                status="ok",
                outcome="message_sent",
                target_entity_id=target.entity_id,
                message="Message sent successfully.",
                details={
                    "message_id": getattr(sent, "id", None),
                    "entity_type": entity_type,
                    "resolved_username": getattr(target_entity, "username", ""),
                },
            )
            self.audit_logger.log_result(result)
            return result
        except SafetyViolation as exc:
            return self._blocked_result(action, "rate_limited", str(exc))
        except AccountBlockedError as exc:
            return self._blocked_result(action, "account_blocked", str(exc))
        except Exception as exc:  # noqa: BLE001
            return self._map_operation_exception(action, exc)

    def _execute_add_to_group(self, action: QueuedAction) -> ActionResult:
        target = self.allowlist[action.target_entity_id]
        group = self.allowlist[action.target_group_id]
        if not self._confirm_action(
            action,
            (
                f"Action {action.action_id}: invite {target.username} "
                f"into {group.username or group.title} from account {self.account_id}.\n"
                "Type YES to continue: "
            ),
        ):
            result = ActionResult(
                action_id=action.action_id,
                action_type=action.action_type,
                account_id=action.account_id,
                status="skipped",
                outcome="manual_decline",
                target_entity_id=target.entity_id,
                target_group_id=group.entity_id,
                message="Operator declined manual confirmation.",
            )
            self.audit_logger.log_result(result)
            return result

        try:
            self.safety.begin_action(self.account_id)
            user_entity = self.validator.resolve_allowlisted_entity(target)
            group_entity = self.validator.resolve_allowlisted_entity(group)
            user_type = classify_entity(user_entity, self.runtime.types)
            group_type = classify_entity(group_entity, self.runtime.types)
            if user_type != "user":
                return self._blocked_result(
                    action,
                    "unsupported_target_type",
                    f"add_to_group requires a user target, got {user_type}",
                )
            if group_type not in {"group", "channel"}:
                return self._blocked_result(
                    action,
                    "unsupported_group_type",
                    f"add_to_group requires a group or channel target, got {group_type}",
                )

            request = self.runtime.functions.channels.InviteToChannelRequest(
                channel=group_entity,
                users=[user_entity],
            )
            updates = self._call_with_retry(
                lambda: self.runtime.client(request),
                action=action,
                operation_name="add_to_group",
            )
            result = ActionResult(
                action_id=action.action_id,
                action_type=action.action_type,
                account_id=action.account_id,
                status="ok",
                outcome="invited_to_group",
                target_entity_id=target.entity_id,
                target_group_id=group.entity_id,
                message="Invite request completed successfully.",
                details={
                    "group_type": group_type,
                    "user_type": user_type,
                    "updates_type": type(updates).__name__,
                },
            )
            self.audit_logger.log_result(result)
            return result
        except SafetyViolation as exc:
            return self._blocked_result(action, "rate_limited", str(exc))
        except AccountBlockedError as exc:
            return self._blocked_result(action, "account_blocked", str(exc))
        except Exception as exc:  # noqa: BLE001
            return self._map_operation_exception(action, exc)

    def _call_with_retry(self, callback: Any, *, action: QueuedAction, operation_name: str) -> Any:
        for attempt in range(2):
            try:
                self.safety.before_api_request(self.account_id)
                return callback()
            except Exception as exc:  # noqa: BLE001
                decision = self.safety.handle_exception(self.account_id, exc)
                self.audit_logger.log_event(
                    "api_exception",
                    action_id=action.action_id,
                    action_type=action.action_type,
                    account_id=self.account_id,
                    operation_name=operation_name,
                    attempt=attempt + 1,
                    exception_name=type(exc).__name__,
                    decision=decision.action,
                    decision_code=decision.code,
                    decision_reason=decision.reason,
                    wait_seconds=decision.wait_seconds,
                )
                if decision.action == "backoff" and attempt == 0:
                    continue
                if decision.action == "stop_account":
                    raise AccountBlockedError(decision.reason) from exc
                raise
        raise RuntimeError("Unexpected executor retry exhaustion.")

    def _confirm_action(self, action: QueuedAction, prompt_text: str) -> bool:
        self.audit_logger.log_event(
            "manual_confirmation_requested",
            action_id=action.action_id,
            action_type=action.action_type,
            account_id=self.account_id,
        )
        response = str(self.confirm_fn(prompt_text) or "").strip()
        confirmed = response == "YES"
        self.audit_logger.log_event(
            "manual_confirmation_result",
            action_id=action.action_id,
            action_type=action.action_type,
            account_id=self.account_id,
            confirmed=confirmed,
        )
        return confirmed

    def _map_operation_exception(self, action: QueuedAction, exc: Exception) -> ActionResult:
        exception_name = type(exc).__name__
        message = str(exc)
        blocked_names = {
            "ChatAdminRequiredError",
            "ChannelPrivateError",
            "ChannelInvalidError",
            "UserNotMutualContactError",
            "UserPrivacyRestrictedError",
            "UserBlockedError",
            "UserBannedInChannelError",
            "UserChannelsTooMuchError",
            "UserKickedError",
            "UserIdInvalidError",
            "BotGroupsBlockedError",
        }
        if exception_name in blocked_names:
            return self._blocked_result(action, exception_name, message)
        result = ActionResult(
            action_id=action.action_id,
            action_type=action.action_type,
            account_id=action.account_id,
            status="error",
            outcome=exception_name or "error",
            target_entity_id=action.target_entity_id,
            target_group_id=action.target_group_id,
            message=message or exception_name,
        )
        self.audit_logger.log_result(result)
        return result

    def _blocked_result(self, action: QueuedAction, outcome: str, message: str) -> ActionResult:
        result = ActionResult(
            action_id=action.action_id,
            action_type=action.action_type,
            account_id=action.account_id,
            status="blocked",
            outcome=outcome,
            target_entity_id=action.target_entity_id,
            target_group_id=action.target_group_id,
            message=message,
        )
        self.audit_logger.log_result(result)
        return result
