from __future__ import annotations

import importlib.util
import argparse
import tempfile
import unittest
from pathlib import Path


def _load_module():
    module_path = (
        Path("/home/max/n8n_ai_call_center")
        / "tools"
        / "telegram_sandbox_activity_runner"
        / "telegram_sandbox_activity_runner.py"
    )
    spec = importlib.util.spec_from_file_location("telegram_sandbox_activity_runner", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load telegram_sandbox_activity_runner module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TelegramSandboxActivityRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def _config_payload(self) -> dict:
        return {
            "version": 1,
            "desktop_automation": {
                "site_control_kit_root": "/home/max/site-control-kit",
            },
            "site_control": {
                "server_url": "http://127.0.0.1:8765",
                "token": "test-token",
            },
            "api_sidecar": {
                "enabled": True,
                "preferred_mode": "api_first",
                "python_bin": "/tmp/runner-venv/bin/python",
                "api_id_env": "TG_API_ID_TEST",
                "api_hash_env": "TG_API_HASH_TEST",
            },
            "actors": [
                {
                    "actor_id": "actor_a",
                    "label": "Actor A",
                    "client_id": "client-a",
                    "url_pattern": "web.telegram.org",
                    "portable_profile_dir": "/home/max/TelegramPortableAK",
                    "api_session_name": "actor_a",
                }
            ],
            "allowlist_chats": [
                {
                    "chat_id": "chat_ops",
                    "title": "Ops Room",
                    "url": "https://web.telegram.org/a/#-1001001001001",
                    "template_ids": ["tmpl_ping"],
                }
            ],
            "allowlist_contacts": [
                {
                    "contact_id": "friend_qa",
                    "username": "@qa_friend",
                    "display_name": "QA Friend",
                    "allowed_chat_ids": ["chat_ops"],
                }
            ],
            "message_templates": [
                {
                    "template_id": "tmpl_ping",
                    "text": "Ping from {actor_label} to {chat_title}.",
                }
            ],
        }

    def _normalized_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{}", encoding="utf-8")
            return self.mod.normalize_config(self._config_payload(), config_path)

    def test_normalize_config_keeps_allowlist_contacts(self) -> None:
        config = self._normalized_config()
        self.assertEqual(len(config["allowlist_contacts"]), 1)
        self.assertEqual(config["allowlist_contacts"][0]["contact_id"], "friend_qa")
        self.assertEqual(config["allowlist_contacts"][0]["username"], "@qa_friend")
        self.assertEqual(config["allowlist_contacts"][0]["search_result_index"], 0)
        self.assertEqual(config["actors"][0]["portable_profile_dir"], "/home/max/TelegramPortableAK")
        self.assertEqual(config["api_sidecar"]["preferred_mode"], "api_first")
        self.assertEqual(config["api_sidecar"]["api_id_env"], "TG_API_ID_TEST")

    def test_render_message_blocks_external_links(self) -> None:
        config = self._normalized_config()
        actor = config["actors"][0]
        chat = config["allowlist_chats"][0]
        template = {"template_id": "bad", "text": "https://example.com", "weight": 1, "actor_ids": [], "chat_ids": []}
        with self.assertRaises(self.mod.ConfigError):
            self.mod.render_message(template, actor, chat, block_external_links=True)

    def test_build_plan_stays_inside_allowlist(self) -> None:
        config = self._normalized_config()
        state = self.mod.build_default_state(Path(config["config_path"]))
        plan = self.mod.build_plan(config, state, iterations=2, actor_filter=None, seed=7)
        self.assertGreaterEqual(plan["iterations_planned"], 1)
        for step in plan["steps"]:
            self.assertEqual(step["actor_id"], "actor_a")
            self.assertEqual(step["chat_id"], "chat_ops")

    def test_inactive_actor_is_excluded_from_plan(self) -> None:
        config = self._normalized_config()
        config["actors"][0]["active"] = False
        state = self.mod.build_default_state(Path(config["config_path"]))
        plan = self.mod.build_plan(config, state, iterations=2, actor_filter=None, seed=7)
        self.assertEqual(plan["iterations_planned"], 0)
        self.assertEqual(plan["steps"], [])

    def test_choose_add_members_candidate_prefers_exact_display_name(self) -> None:
        config = self._normalized_config()
        contact = config["allowlist_contacts"][0]
        candidates = [
            {"peer_id": "10", "title": "QA Friend"},
            {"peer_id": "11", "title": "QA Friend Backup"},
        ]
        selected = self.mod.choose_add_members_candidate(contact, candidates, allow_first_result=False)
        self.assertEqual(selected["peer_id"], "10")

    def test_portable_actor_args_uses_profile_dir(self) -> None:
        config = self._normalized_config()
        actor = config["actors"][0]
        args = self.mod.portable_actor_args(actor)
        self.assertEqual(args, ["--profile-dir", "/home/max/TelegramPortableAK"])

    def test_api_session_file_path_uses_session_name(self) -> None:
        config = self._normalized_config()
        actor = config["actors"][0]
        session_path = self.mod.api_session_file_path(config, actor)
        self.assertTrue(str(session_path).endswith("/api_sessions/actor_a.session"))

    def test_resolve_actor_tdata_dir_prefers_portable_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tdata_dir = Path(tmpdir) / "TelegramForcePortable" / "tdata"
            tdata_dir.mkdir(parents=True)
            actor = dict(self._normalized_config()["actors"][0])
            actor["portable_profile_dir"] = tmpdir
            resolved = self.mod.resolve_actor_tdata_dir(actor)
            self.assertEqual(resolved, tdata_dir.resolve())

    def test_resolve_actor_tdata_dir_accepts_explicit_tdata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tdata_dir = Path(tmpdir) / "tdata"
            tdata_dir.mkdir(parents=True)
            actor = dict(self._normalized_config()["actors"][0])
            resolved = self.mod.resolve_actor_tdata_dir(actor, str(tdata_dir))
            self.assertEqual(resolved, tdata_dir.resolve())

    def test_preferred_accessible_text_indices_prefers_best_match_first(self) -> None:
        self.assertEqual(self.mod.preferred_accessible_text_indices(), (0, 1))

    def test_normalize_contact_preserves_search_result_index(self) -> None:
        normalized = self.mod._normalize_contact(
            {
                "contact_id": "friend_qa",
                "username": "@qa_friend",
                "display_name": "QA Friend",
                "search_result_index": 2,
            },
            set(),
        )
        self.assertEqual(normalized["search_result_index"], 2)

    def test_split_display_name_parts_strips_trailing_emoji(self) -> None:
        self.assertEqual(
            self.mod.split_display_name_parts("Павел Сухомлинов 😎"),
            ("Павел", "Сухомлинов"),
        )

    def test_resolve_contact_name_parts_falls_back_to_display_name(self) -> None:
        first_name, last_name = self.mod.resolve_contact_name_parts(
            argparse.Namespace(first_name_text="", last_name_text=""),
            {
                "username": "@super_pavlik",
                "display_name": "Павел Сухомлинов",
            },
        )
        self.assertEqual((first_name, last_name), ("Павел", "Сухомлинов"))

    def test_resolve_contact_name_parts_uses_username_when_display_name_missing(self) -> None:
        first_name, last_name = self.mod.resolve_contact_name_parts(
            argparse.Namespace(first_name_text="", last_name_text=""),
            {
                "username": "@qa_friend",
                "display_name": "",
            },
        )
        self.assertEqual((first_name, last_name), ("qa", "friend"))

    def test_resolve_contact_name_parts_preserves_explicit_overrides(self) -> None:
        first_name, last_name = self.mod.resolve_contact_name_parts(
            argparse.Namespace(first_name_text="Паша", last_name_text=""),
            {
                "username": "@super_pavlik",
                "display_name": "Павел Сухомлинов",
            },
        )
        self.assertEqual((first_name, last_name), ("Паша", "Сухомлинов"))

    def test_normalize_config_allows_contact_only_mode(self) -> None:
        payload = self._config_payload()
        payload["allowlist_chats"] = []
        payload["message_templates"] = []
        payload["allowlist_contacts"] = [
            {
                "contact_id": "friend_qa",
                "username": "@qa_friend",
                "display_name": "QA Friend",
                "allowed_chat_ids": [],
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "contact_only.json"
            config_path.write_text("{}", encoding="utf-8")
            config = self.mod.normalize_config(payload, config_path)
        self.assertEqual(config["allowlist_chats"], [])
        self.assertEqual(config["message_templates"], [])

    def test_parse_usernames_blob_deduplicates_and_skips_invalid(self) -> None:
        text = "\n".join(
            [
                "@valid_one",
                "@valid_two extra words",
                "@VALID_ONE",
                "[04_RUNBOOK_TROUBLESHOOTING_RU.md](docs/call-translation-bridge/04_RUNBOOK_TROUBLESHOOTING_RU.md)",
                "not a username line",
            ]
        )
        usernames, invalid_lines = self.mod.parse_usernames_blob(text)
        self.assertEqual(usernames, ["@valid_one", "@valid_two"])
        self.assertTrue(any("not a username line" in line for line in invalid_lines))

    def test_build_contact_id_batch_preserves_order_and_limit(self) -> None:
        config = self._normalized_config()
        batch = self.mod.build_contact_id_batch(config, explicit_contact_ids=["friend_qa", "friend_qa"], limit=1)
        self.assertEqual(batch, ["friend_qa"])

    def test_build_parser_supports_api_import_tdata_session(self) -> None:
        parser = self.mod.build_parser()
        args = parser.parse_args(
            [
                "api-import-tdata-session",
                "--config",
                "/tmp/config.json",
                "--actor-id",
                "actor_a",
            ]
        )
        self.assertIs(args.func, self.mod.command_api_import_tdata_session)

    def test_build_parser_supports_api_scan_contacts(self) -> None:
        parser = self.mod.build_parser()
        args = parser.parse_args(
            [
                "api-scan-contacts",
                "--config",
                "/tmp/config.json",
                "--actor-id",
                "actor_a",
                "--contact-id",
                "friend_qa",
            ]
        )
        self.assertIs(args.func, self.mod.command_api_scan_contacts)

    def test_derive_accessible_click_ratio_biases_into_button_body(self) -> None:
        ratio = self.mod.derive_accessible_click_ratio(
            {
                "relative_extents": {
                    "x": 426,
                    "y": 948,
                    "width": 784,
                    "height": 76,
                }
            },
            {
                "width": 1636,
                "height": 1284,
            },
        )
        self.assertEqual(ratio, {"x_ratio": 0.3466, "y_ratio": 0.7648})

    def test_derive_dialog_submit_ratio_uses_dialog_ancestor_geometry(self) -> None:
        ratio = self.mod.derive_dialog_submit_ratio(
            {
                "stdout_json": {
                    "click": {
                        "node": {
                            "ancestors": [
                                {
                                    "path_text": "/1/1/1/4/0",
                                    "role": "dialog",
                                    "resolved_extents": {
                                        "x": 1162,
                                        "y": 498,
                                        "width": 728,
                                        "height": 832,
                                    },
                                }
                            ]
                        }
                    }
                }
            },
            {
                "x": 328,
                "y": 128,
                "width": 2396,
                "height": 1536,
            },
        )
        self.assertEqual(ratio, {"x_ratio": 0.5576, "y_ratio": 0.7611})

    def test_derive_dialog_submit_ratio_returns_none_without_dialog(self) -> None:
        ratio = self.mod.derive_dialog_submit_ratio(
            {
                "stdout_json": {
                    "click": {
                        "node": {
                            "ancestors": [
                                {
                                    "path_text": "/1/1/1",
                                    "role": "filler",
                                    "resolved_extents": {
                                        "x": 1162,
                                        "y": 498,
                                        "width": 728,
                                        "height": 832,
                                    },
                                }
                            ]
                        }
                    }
                }
            },
            {
                "x": 328,
                "y": 128,
                "width": 2396,
                "height": 1536,
            },
        )
        self.assertIsNone(ratio)

    def test_summarize_contact_verify_state_prefers_present_contact(self) -> None:
        self.assertEqual(
            self.mod.summarize_contact_verify_state(
                username_visible=True,
                add_button_visible=False,
                edit_button_visible=True,
                delete_button_visible=False,
            ),
            "ui_verify_contact_present",
        )
        self.assertEqual(
            self.mod.summarize_contact_verify_state(
                username_visible=True,
                add_button_visible=True,
                edit_button_visible=False,
                delete_button_visible=False,
            ),
            "ui_verify_add_button_visible",
        )


if __name__ == "__main__":
    unittest.main()
