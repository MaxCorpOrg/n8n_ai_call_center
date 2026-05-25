from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .audit_log import AuditLogger
from .csv_loader import load_accounts, load_actions, load_allowlist
from .executor import ActionExecutor
from .models import ActionResult, QueuedAction, to_serializable
from .queue_manager import QueueManager
from .report import build_report, build_report_from_audit_log, write_report
from .safety import SafetyController
from .telethon_client import open_telethon_client
from .validator import EntityValidator


DEFAULT_AUDIT_LOG = Path.home() / ".local" / "share" / "telegram-allowlist-tool" / "audit.log.jsonl"
DEFAULT_REPORT_PATH = Path.cwd() / "telegram_allowlist_report.json"


def command_sample_files(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "accounts.example.csv").write_text(
        "\n".join(
            [
                "account_id,label,session_file,api_id_env,api_hash_env,enabled",
                "main_admin,Main Admin,/home/max/.telegram_sessions/main_admin.session,TG_API_ID_MAIN,TG_API_HASH_MAIN,yes",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "allowlist.example.csv").write_text(
        "\n".join(
            [
                "entity_id,kind_hint,username,title,consent_confirmed,allowed_actions,notes",
                "user_alice,user,@alice_example,Alice Example,yes,\"validate,send_message,add_to_group\",Explicit written consent",
                "group_ops,group,@ops_example,Ops Example,yes,\"validate\",Internal admin group",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "actions.example.csv").write_text(
        "\n".join(
            [
                "action_id,action_type,account_id,target_entity_id,target_group_id,message_text,notes",
                "validate_alice,validate,main_admin,user_alice,,,Check that the user still resolves",
                "msg_alice,send_message,main_admin,user_alice,,Hello from the compliant allowlist tool.,Manual confirm required",
                "invite_alice,add_to_group,main_admin,user_alice,group_ops,,Manual confirm required",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "completed", "output_dir": str(output_dir)}, ensure_ascii=False, indent=2))
    return 0


def command_validate_allowlist(args: argparse.Namespace) -> int:
    accounts = load_accounts(Path(args.accounts_csv))
    allowlist = load_allowlist(Path(args.allowlist_csv))
    account = select_account(accounts, args.account_id)
    audit_logger = AuditLogger(Path(args.audit_log))
    safety = SafetyController(
        max_actions_per_hour=int(args.max_actions_per_hour),
        request_delay_seconds=int(args.request_delay_seconds),
    )
    results: list[ActionResult] = []
    with open_telethon_client(account) as runtime:
        validator = EntityValidator(
            runtime,
            account_id=account.account_id,
            safety=safety,
            audit_logger=audit_logger,
        )
        for record in allowlist.values():
            try:
                safety.begin_action(account.account_id)
            except Exception as exc:  # noqa: BLE001
                result = ActionResult(
                    action_id=f"validate::{record.entity_id}",
                    action_type="validate",
                    account_id=account.account_id,
                    status="blocked",
                    outcome="rate_limited",
                    target_entity_id=record.entity_id,
                    message=str(exc),
                )
                audit_logger.log_result(result)
                results.append(result)
                continue
            payload = validator.validate_entry(record)
            results.append(
                ActionResult(
                    action_id=f"validate::{record.entity_id}",
                    action_type="validate",
                    account_id=account.account_id,
                    status=str(payload.get("status") or "error"),
                    outcome="validated" if payload.get("status") == "ok" else str(payload.get("status") or "error"),
                    target_entity_id=record.entity_id,
                    message=str(payload.get("error") or ""),
                    details=payload,
                )
            )
            audit_logger.log_result(results[-1])

    report_path = write_report(results, Path(args.report_path))
    print(json.dumps({"status": "completed", "report_path": str(report_path), "summary": build_report(results)}, ensure_ascii=False, indent=2))
    return 0


def command_build_queue(args: argparse.Namespace) -> int:
    accounts = load_accounts(Path(args.accounts_csv))
    allowlist = load_allowlist(Path(args.allowlist_csv))
    actions = load_actions(Path(args.actions_csv))
    queue = QueueManager(accounts=accounts, allowlist=allowlist).build_queue(actions)
    payload = {
        "status": "completed",
        "total_actions": len(queue),
        "queue": [to_serializable(item) for item in queue],
    }
    output_path = Path(args.output_json).expanduser().resolve() if args.output_json else None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload["output_json"] = str(output_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_run_actions(args: argparse.Namespace) -> int:
    accounts = load_accounts(Path(args.accounts_csv))
    allowlist = load_allowlist(Path(args.allowlist_csv))
    actions = load_actions(Path(args.actions_csv))
    queue = QueueManager(accounts=accounts, allowlist=allowlist).build_queue(actions)
    if args.account_id:
        queue = [item for item in queue if item.account_id == args.account_id]
    audit_logger = AuditLogger(Path(args.audit_log))
    results: list[ActionResult] = []
    blocked_preflight = [item for item in queue if item.status != "pending"]
    for item in blocked_preflight:
        results.append(
            ActionResult(
                action_id=item.action_id,
                action_type=item.action_type,
                account_id=item.account_id,
                status="blocked",
                outcome="preflight_blocked",
                target_entity_id=item.target_entity_id,
                target_group_id=item.target_group_id,
                message=item.block_reason,
                details={"metadata": item.metadata},
            )
        )
        audit_logger.log_result(results[-1])

    pending_by_account: dict[str, list[QueuedAction]] = defaultdict(list)
    for item in queue:
        if item.status == "pending":
            pending_by_account[item.account_id].append(item)

    for account_id, account_actions in pending_by_account.items():
        account = select_account(accounts, account_id)
        safety = SafetyController(
            max_actions_per_hour=int(args.max_actions_per_hour),
            request_delay_seconds=int(args.request_delay_seconds),
        )
        with open_telethon_client(account) as runtime:
            executor = ActionExecutor(
                runtime,
                allowlist=allowlist,
                account_id=account.account_id,
                safety=safety,
                audit_logger=audit_logger,
            )
            for action in account_actions:
                results.append(executor.execute(action))

    report_path = write_report(results, Path(args.report_path))
    print(json.dumps({"status": "completed", "report_path": str(report_path), "summary": build_report(results)}, ensure_ascii=False, indent=2))
    return 0


def command_report(args: argparse.Namespace) -> int:
    payload = build_report_from_audit_log(Path(args.audit_log))
    print(json.dumps({"status": "completed", "summary": payload}, ensure_ascii=False, indent=2))
    return 0


def select_account(accounts: dict[str, Any], requested_account_id: str | None) -> Any:
    if requested_account_id:
        account = accounts.get(str(requested_account_id))
        if account is None:
            raise KeyError(f"Unknown account_id={requested_account_id}")
        return account
    enabled_accounts = [account for account in accounts.values() if account.enabled]
    if not enabled_accounts:
        raise RuntimeError("No enabled accounts found in accounts.csv")
    if len(enabled_accounts) > 1:
        raise RuntimeError("Multiple enabled accounts found. Pass --account-id explicitly.")
    return enabled_accounts[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compliant allowlist-only Telegram CLI. "
            "It validates entities, sends messages, and invites users to groups only after manual confirmation."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sample_parser = subparsers.add_parser("sample-files", help="Write example accounts/allowlist/actions CSV templates.")
    sample_parser.add_argument("--output-dir", required=True)
    sample_parser.set_defaults(func=command_sample_files)

    validate_parser = subparsers.add_parser("validate-allowlist", help="Validate every allowlist username through Telethon.")
    add_base_csv_arguments(validate_parser)
    validate_parser.add_argument("--account-id", help="Which account from accounts.csv should validate the allowlist.")
    add_runtime_arguments(validate_parser)
    validate_parser.set_defaults(func=command_validate_allowlist)

    queue_parser = subparsers.add_parser("build-queue", help="Build a preflight queue from actions.csv without touching Telegram.")
    add_action_csv_arguments(queue_parser)
    queue_parser.add_argument("--output-json", help="Optional output path for the queue JSON.")
    queue_parser.set_defaults(func=command_build_queue)

    run_parser = subparsers.add_parser(
        "run-actions",
        help=(
            "Execute pending allowlist actions. "
            "Every send_message or add_to_group action requires typing YES in the console."
        ),
    )
    add_action_csv_arguments(run_parser)
    run_parser.add_argument("--account-id", help="Optional account filter if actions.csv contains multiple admins.")
    add_runtime_arguments(run_parser)
    run_parser.set_defaults(func=command_run_actions)

    report_parser = subparsers.add_parser("report", help="Summarize action_result entries from the JSONL audit log.")
    report_parser.add_argument("--audit-log", default=str(DEFAULT_AUDIT_LOG))
    report_parser.set_defaults(func=command_report)
    return parser


def add_base_csv_arguments(target: argparse.ArgumentParser) -> None:
    target.add_argument("--accounts-csv", required=True)
    target.add_argument("--allowlist-csv", required=True)


def add_action_csv_arguments(target: argparse.ArgumentParser) -> None:
    add_base_csv_arguments(target)
    target.add_argument("--actions-csv", required=True)


def add_runtime_arguments(target: argparse.ArgumentParser) -> None:
    target.add_argument("--audit-log", default=str(DEFAULT_AUDIT_LOG))
    target.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    target.add_argument("--max-actions-per-hour", type=int, default=20)
    target.add_argument("--request-delay-seconds", type=int, default=5)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
