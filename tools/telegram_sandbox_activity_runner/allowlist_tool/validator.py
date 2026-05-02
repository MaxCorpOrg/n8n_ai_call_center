from __future__ import annotations

from typing import Any

from .audit_log import AuditLogger
from .models import AllowlistRecord
from .safety import AccountBlockedError, SafetyController
from .telethon_client import TelethonRuntime


def classify_entity(entity: Any, types_module: Any) -> str:
    if isinstance(entity, types_module.User):
        return "bot" if bool(getattr(entity, "bot", False)) else "user"
    if isinstance(entity, types_module.Channel):
        if bool(getattr(entity, "megagroup", False)):
            return "group"
        if bool(getattr(entity, "broadcast", False)):
            return "channel"
        return "channel"
    if isinstance(entity, types_module.Chat):
        return "group"
    return "unknown"


class EntityValidator:
    def __init__(
        self,
        runtime: TelethonRuntime,
        *,
        account_id: str,
        safety: SafetyController,
        audit_logger: AuditLogger,
    ) -> None:
        self.runtime = runtime
        self.account_id = account_id
        self.safety = safety
        self.audit_logger = audit_logger
        self._cache: dict[str, Any] = {}

    def validate_entry(self, record: AllowlistRecord) -> dict[str, Any]:
        result = {
            "entity_id": record.entity_id,
            "username": record.username,
            "kind_hint": record.kind_hint,
            "status": "error",
            "entity_type": "unknown",
            "resolved_username": "",
            "resolved_title": "",
            "resolved_id": None,
        }
        try:
            entity = self.resolve_allowlisted_entity(record)
        except AccountBlockedError as exc:
            result.update({"status": "blocked", "error": str(exc)})
            self.audit_logger.log_event("validate_blocked", account_id=self.account_id, **result)
            return result
        except Exception as exc:  # noqa: BLE001
            if is_not_found_exception(exc):
                result.update({"status": "not_found", "error": str(exc)})
                self.audit_logger.log_event("validate_not_found", account_id=self.account_id, **result)
                return result
            result.update({"status": "error", "error": str(exc)})
            self.audit_logger.log_event("validate_error", account_id=self.account_id, **result)
            return result

        entity_type = classify_entity(entity, self.runtime.types)
        result.update(
            {
                "status": "ok",
                "entity_type": entity_type,
                "resolved_username": normalize_entity_username(entity),
                "resolved_title": normalize_entity_title(entity),
                "resolved_id": getattr(entity, "id", None),
            }
        )
        self.audit_logger.log_event("validate_ok", account_id=self.account_id, **result)
        return result

    def resolve_allowlisted_entity(self, record: AllowlistRecord) -> Any:
        cache_key = record.entity_id
        if cache_key in self._cache:
            return self._cache[cache_key]

        entity = self._call_client(lambda: self.runtime.client.get_entity(record.username))
        self._cache[cache_key] = entity
        return entity

    def _call_client(self, callback: Any) -> Any:
        for attempt in range(2):
            try:
                self.safety.before_api_request(self.account_id)
                return callback()
            except Exception as exc:  # noqa: BLE001
                decision = self.safety.handle_exception(self.account_id, exc)
                self.audit_logger.log_event(
                    "validator_exception",
                    account_id=self.account_id,
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
        raise RuntimeError("Unexpected validator retry exhaustion.")


def is_not_found_exception(exc: Exception) -> bool:
    exception_name = type(exc).__name__
    message = str(exc).lower()
    if exception_name in {"UsernameNotOccupiedError", "UsernameInvalidError", "PeerIdInvalidError"}:
        return True
    if "no user has" in message:
        return True
    if "could not find the input entity" in message:
        return True
    return False


def normalize_entity_username(entity: Any) -> str:
    username = str(getattr(entity, "username", "") or "").strip()
    return f"@{username}" if username else ""


def normalize_entity_title(entity: Any) -> str:
    for attr_name in ("title", "first_name", "username"):
        value = str(getattr(entity, attr_name, "") or "").strip()
        if value:
            return value
    return ""
