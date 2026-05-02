from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable


class SafetyViolation(RuntimeError):
    """Raised when the local safety policy blocks an action."""


class AccountBlockedError(RuntimeError):
    """Raised when Telegram signals a suspicious or blocked account state."""


@dataclass(frozen=True)
class SafetyDecision:
    action: str
    reason: str
    wait_seconds: int = 0
    code: str = ""


class SafetyController:
    def __init__(
        self,
        *,
        max_actions_per_hour: int = 20,
        request_delay_seconds: int = 5,
        flood_wait_padding_ratio: float = 0.10,
        clock_fn: Callable[[], float] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self.max_actions_per_hour = int(max_actions_per_hour)
        self.request_delay_seconds = int(request_delay_seconds)
        self.flood_wait_padding_ratio = float(flood_wait_padding_ratio)
        self.clock_fn = clock_fn or time.monotonic
        self.sleep_fn = sleep_fn or time.sleep
        self._actions_by_account: dict[str, deque[float]] = {}
        self._last_request_at: dict[str, float] = {}
        self._blocked_accounts: set[str] = set()

    def begin_action(self, account_id: str) -> None:
        self._ensure_account_allowed(account_id)
        history = self._actions_by_account.setdefault(account_id, deque())
        now = self.clock_fn()
        self._prune_history(history, now)
        if len(history) >= self.max_actions_per_hour:
            raise SafetyViolation(
                f"Account {account_id} reached the local hourly limit ({self.max_actions_per_hour} actions/hour)."
            )
        history.append(now)

    def before_api_request(self, account_id: str) -> None:
        self._ensure_account_allowed(account_id)
        now = self.clock_fn()
        last_request_at = self._last_request_at.get(account_id)
        if last_request_at is not None:
            elapsed = now - last_request_at
            remaining = float(self.request_delay_seconds) - elapsed
            if remaining > 0:
                self.sleep_fn(remaining)
                now = self.clock_fn()
        self._last_request_at[account_id] = now

    def is_account_blocked(self, account_id: str) -> bool:
        return account_id in self._blocked_accounts

    def handle_exception(self, account_id: str, exc: Exception) -> SafetyDecision:
        exception_name = type(exc).__name__
        message = str(exc)
        message_upper = message.upper()
        if "FloodWait" in exception_name or "FLOOD_WAIT" in message_upper:
            wait_seconds = _extract_flood_wait_seconds(exc)
            padded_wait = int(math.ceil(wait_seconds * (1.0 + self.flood_wait_padding_ratio)))
            self.sleep_fn(max(padded_wait, 1))
            return SafetyDecision(
                action="backoff",
                reason=message or exception_name,
                wait_seconds=max(padded_wait, 1),
                code="flood_wait",
            )
        if (
            exception_name in {"PeerFloodError", "UserBannedInChannelError"}
            or "PEER_FLOOD" in message_upper
            or "BANNED" in message_upper
        ):
            self._blocked_accounts.add(account_id)
            return SafetyDecision(
                action="stop_account",
                reason=message or exception_name,
                code="peer_flood",
            )
        return SafetyDecision(action="raise", reason=message or exception_name, code=exception_name)

    def _ensure_account_allowed(self, account_id: str) -> None:
        if account_id in self._blocked_accounts:
            raise AccountBlockedError(f"Account {account_id} is blocked after a previous suspicious Telegram response.")

    @staticmethod
    def _prune_history(history: deque[float], now: float) -> None:
        while history and (now - history[0]) >= 3600:
            history.popleft()


def _extract_flood_wait_seconds(exc: Exception) -> int:
    for attr_name in ("seconds", "value"):
        raw_value = getattr(exc, attr_name, None)
        if raw_value is None:
            continue
        try:
            return max(int(raw_value), 1)
        except (TypeError, ValueError):
            continue
    return 60
