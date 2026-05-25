from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path


TOOL_ROOT = Path("/home/max/n8n_ai_call_center/tools/telegram_sandbox_activity_runner")
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from allowlist_tool import csv_loader, models, queue_manager, report, safety
from allowlist_tool.audit_log import AuditLogger
from allowlist_tool.executor import ActionExecutor
from allowlist_tool.telethon_client import TelethonRuntime


class _FakeUser:
    def __init__(self, *, user_id: int, username: str, bot: bool = False) -> None:
        self.id = user_id
        self.username = username
        self.bot = bot
        self.first_name = username


class _FakeChannel:
    def __init__(self, *, channel_id: int, username: str, title: str, megagroup: bool = False, broadcast: bool = False) -> None:
        self.id = channel_id
        self.username = username
        self.title = title
        self.megagroup = megagroup
        self.broadcast = broadcast


class _FakeChat:
    def __init__(self, *, chat_id: int, title: str) -> None:
        self.id = chat_id
        self.title = title


class _FakeInviteRequest:
    def __init__(self, *, channel, users) -> None:
        self.channel = channel
        self.users = users


class _FakeFunctions:
    class channels:
        InviteToChannelRequest = _FakeInviteRequest


class _FakeClient:
    def __init__(self, entities: dict[str, object]) -> None:
        self.entities = entities
        self.sent_messages: list[tuple[str, str]] = []
        self.invites: list[_FakeInviteRequest] = []

    def get_entity(self, reference: str):
        if reference not in self.entities:
            raise ValueError(f"Could not find the input entity for {reference}")
        return self.entities[reference]

    def send_message(self, entity, message: str):
        self.sent_messages.append((str(getattr(entity, "username", "")), message))
        return types.SimpleNamespace(id=77)

    def __call__(self, request):
        self.invites.append(request)
        return {"status": "ok"}


class _FakeFloodWaitError(Exception):
    def __init__(self, seconds: int) -> None:
        super().__init__(f"FLOOD_WAIT_{seconds}")
        self.seconds = seconds


class _FakePeerFloodError(Exception):
    pass


class TelegramAllowlistToolTests(unittest.TestCase):
    def test_load_allowlist_parses_actions_and_consent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "allowlist.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "entity_id,kind_hint,username,title,consent_confirmed,allowed_actions,notes",
                        "user_1,user,@alice,Alice,yes,\"validate,send_message,add_to_group\",ok",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            allowlist = csv_loader.load_allowlist(csv_path)

        self.assertEqual(sorted(allowlist["user_1"].allowed_actions), ["add_to_group", "send_message", "validate"])
        self.assertTrue(allowlist["user_1"].consent_confirmed)

    def test_queue_manager_blocks_send_without_consent(self) -> None:
        accounts = {
            "main": models.AccountRecord(
                account_id="main",
                session_file=Path("/tmp/main.session"),
                api_id_env="TG_API_ID_MAIN",
                api_hash_env="TG_API_HASH_MAIN",
            )
        }
        allowlist = {
            "user_1": models.AllowlistRecord(
                entity_id="user_1",
                kind_hint="user",
                username="@alice",
                title="Alice",
                consent_confirmed=False,
                allowed_actions=frozenset({"send_message", "validate"}),
            )
        }
        actions = [
            models.ActionRecord(
                action_id="msg_1",
                action_type="send_message",
                account_id="main",
                target_entity_id="user_1",
                message_text="Hello",
            )
        ]

        queue = queue_manager.QueueManager(accounts=accounts, allowlist=allowlist).build_queue(actions)
        self.assertEqual(queue[0].status, "blocked")
        self.assertIn("consent_confirmed=yes", queue[0].block_reason)

    def test_safety_controller_backoffs_on_flood_wait(self) -> None:
        slept: list[float] = []
        controller = safety.SafetyController(sleep_fn=slept.append)
        decision = controller.handle_exception("main", _FakeFloodWaitError(10))
        self.assertEqual(decision.action, "backoff")
        self.assertEqual(decision.wait_seconds, 11)
        self.assertEqual(slept, [11])

    def test_safety_controller_blocks_account_on_peer_flood(self) -> None:
        controller = safety.SafetyController(sleep_fn=lambda _seconds: None)
        decision = controller.handle_exception("main", _FakePeerFloodError("PEER_FLOOD"))
        self.assertEqual(decision.action, "stop_account")
        self.assertTrue(controller.is_account_blocked("main"))

    def test_executor_send_message_requires_yes_and_sends_on_confirm(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_logger = AuditLogger(Path(tmpdir) / "audit.jsonl")
            runtime = TelethonRuntime(
                client=_FakeClient({"@alice": _FakeUser(user_id=1, username="alice")}),
                functions=_FakeFunctions,
                types=types.SimpleNamespace(User=_FakeUser, Channel=_FakeChannel, Chat=_FakeChat),
                errors=types.SimpleNamespace(),
            )
            allowlist = {
                "user_1": models.AllowlistRecord(
                    entity_id="user_1",
                    kind_hint="user",
                    username="@alice",
                    title="Alice",
                    consent_confirmed=True,
                    allowed_actions=frozenset({"send_message", "validate"}),
                )
            }
            action = models.QueuedAction(
                action_id="msg_1",
                action_type="send_message",
                account_id="main",
                target_entity_id="user_1",
                message_text="Hello Alice",
            )
            executor = ActionExecutor(
                runtime,
                allowlist=allowlist,
                account_id="main",
                safety=safety.SafetyController(sleep_fn=lambda _seconds: None),
                audit_logger=audit_logger,
                confirm_fn=lambda _prompt: "YES",
            )

            result = executor.execute(action)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.outcome, "message_sent")
        self.assertEqual(runtime.client.sent_messages, [("alice", "Hello Alice")])

    def test_executor_add_to_group_invites_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_logger = AuditLogger(Path(tmpdir) / "audit.jsonl")
            runtime = TelethonRuntime(
                client=_FakeClient(
                    {
                        "@alice": _FakeUser(user_id=1, username="alice"),
                        "@opsgroup": _FakeChannel(channel_id=10, username="opsgroup", title="Ops", megagroup=True),
                    }
                ),
                functions=_FakeFunctions,
                types=types.SimpleNamespace(User=_FakeUser, Channel=_FakeChannel, Chat=_FakeChat),
                errors=types.SimpleNamespace(),
            )
            allowlist = {
                "user_1": models.AllowlistRecord(
                    entity_id="user_1",
                    kind_hint="user",
                    username="@alice",
                    title="Alice",
                    consent_confirmed=True,
                    allowed_actions=frozenset({"add_to_group", "validate"}),
                ),
                "group_1": models.AllowlistRecord(
                    entity_id="group_1",
                    kind_hint="group",
                    username="@opsgroup",
                    title="Ops",
                    consent_confirmed=True,
                    allowed_actions=frozenset({"validate"}),
                ),
            }
            action = models.QueuedAction(
                action_id="invite_1",
                action_type="add_to_group",
                account_id="main",
                target_entity_id="user_1",
                target_group_id="group_1",
            )
            executor = ActionExecutor(
                runtime,
                allowlist=allowlist,
                account_id="main",
                safety=safety.SafetyController(sleep_fn=lambda _seconds: None),
                audit_logger=audit_logger,
                confirm_fn=lambda _prompt: "YES",
            )

            result = executor.execute(action)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.outcome, "invited_to_group")
        self.assertEqual(len(runtime.client.invites), 1)
        self.assertEqual(runtime.client.invites[0].channel.username, "opsgroup")
        self.assertEqual(runtime.client.invites[0].users[0].username, "alice")

    def test_report_summary_counts_statuses(self) -> None:
        results = [
            models.ActionResult(action_id="a", action_type="validate", account_id="main", status="ok", outcome="validated"),
            models.ActionResult(action_id="b", action_type="send_message", account_id="main", status="blocked", outcome="rate_limited"),
            models.ActionResult(action_id="c", action_type="send_message", account_id="main", status="skipped", outcome="manual_decline"),
        ]
        payload = report.build_report(results)
        self.assertEqual(payload["by_status"], {"blocked": 1, "ok": 1, "skipped": 1})

