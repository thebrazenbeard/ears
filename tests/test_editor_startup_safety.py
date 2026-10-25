"""Static safeguards for editor-startup behavior; never execute workspace tasks."""

import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def task_literal(value):
    """Resolve VS Code task string or {value, quoting} literal without execution."""
    if isinstance(value, dict):
        value = value.get("value")
    return value if isinstance(value, str) else None


class EditorStartupSafetyTests(unittest.TestCase):
    def test_no_automatic_folder_open_task(self):
        tasks = (ROOT / ".vscode" / "tasks.json").read_text(encoding="utf-8")
        parsed_tasks = json.loads(tasks)
        for task in parsed_tasks.get("tasks", []):
            # Platform-specific properties override the same task's base fields.
            variants = [task]
            for platform in ("windows", "linux", "osx"):
                override = task.get(platform)
                if isinstance(override, dict):
                    variants.append({**task, **override})
            for variant in variants:
                self.assertNotEqual(
                    variant.get("runOptions", {}).get("runOn"),
                    "folderOpen",
                    f"Task {task.get('label', '<unnamed>')} must not run on folderOpen",
                )
                command = task_literal(variant.get("command"))
                if command is not None:
                    args = variant.get("args", [])
                    direct_node = re.match(
                        r"^\s*(?:\S*[/\\])?node(?:\.exe)?(?:\s|$)",
                        command,
                        re.IGNORECASE,
                    )
                    if direct_node and isinstance(args, list):
                        command = " ".join(
                            [command] + [text for arg in args if (text := task_literal(arg)) is not None]
                        )
                    # Decoded JSON whitespace, escapes and OS overrides stay intact.
                    self.assertIsNone(
                        re.search(
                            r"\bnode(?:\.exe)?\s+[^\r\n]*public[/\\]fonts[/\\]",
                            command,
                            re.IGNORECASE,
                        )
                    )

    def test_json_escaped_run_on_in_secondary_task_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            editor = Path(temp_dir) / ".vscode"
            editor.mkdir()
            (editor / "tasks.json").write_text(
                (
                    '{"version":"2.0.0","tasks":['
                    '{"label":"regular","type":"shell","command":"echo safe"},'
                    r'{"label":"secondary","type":"shell","command":"echo safe","runOptions":{"run\u004fn":"folderOpen"}}]}'
                ),
                encoding="utf-8",
            )
            with mock.patch.dict(globals(), {"ROOT": Path(temp_dir)}):
                with self.assertRaisesRegex(AssertionError, "folderOpen"):
                    self.test_no_automatic_folder_open_task()

    def test_json_escaped_node_font_command_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            editor = Path(temp_dir) / ".vscode"
            editor.mkdir()
            with mock.patch.dict(globals(), {"ROOT": Path(temp_dir)}):
                for command in (
                    r"node public\u002ffonts\u002fhidden.woff2",
                    r"n\u006fde public/fonts/hidden.woff2",
                    r"node\u0009public/fonts/hidden.woff2",
                    r"NODE.EXE public\\fonts\\hidden.woff2",
                ):
                    with self.subTest(command=command):
                        (editor / "tasks.json").write_text(
                            '{"version":"2.0.0","tasks":['
                            f'{{"label":"secondary","type":"shell","command":"{command}"}}]}}',
                            encoding="utf-8",
                        )
                        with self.assertRaises(AssertionError):
                            self.test_no_automatic_folder_open_task()

    def test_unrelated_editor_task_strings_are_not_a_font_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            editor = Path(temp_dir) / ".vscode"
            editor.mkdir()
            (editor / "tasks.json").write_text(
                '{"version":"2.0.0","tasks":['
                '{"label":"node benign","type":"shell","command":"echo hello"},'
                '{"label":"assets public/fonts/note","type":"shell","command":"echo ready"}]}',
                encoding="utf-8",
            )
            with mock.patch.dict(globals(), {"ROOT": Path(temp_dir)}):
                self.test_no_automatic_folder_open_task()

    def test_echo_args_mentioning_node_and_fonts_are_not_an_invocation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            editor = Path(temp_dir) / ".vscode"
            editor.mkdir()
            (editor / "tasks.json").write_text(
                json.dumps({"version": "2.0.0", "tasks": [{
                    "label": "text-only",
                    "type": "shell",
                    "command": "echo",
                    "args": ["node", "public/fonts/explanation.txt"],
                }]}),
                encoding="utf-8",
            )
            with mock.patch.dict(globals(), {"ROOT": Path(temp_dir)}):
                self.test_no_automatic_folder_open_task()

    def test_platform_override_with_inherited_node_command_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            editor = Path(temp_dir) / ".vscode"
            editor.mkdir()
            (editor / "tasks.json").write_text(
                '{"version":"2.0.0","tasks":['
                '{"label":"platform","type":"shell","command":"node",'
                '"windows":{"args":["public/fonts/hidden.woff2"]}}]}',
                encoding="utf-8",
            )
            with mock.patch.dict(globals(), {"ROOT": Path(temp_dir)}):
                with self.assertRaises(AssertionError):
                    self.test_no_automatic_folder_open_task()

    def test_quoted_literal_node_command_or_arg_is_rejected(self):
        commands = (
            {"command": "node", "args": [{"value": "public/fonts/hidden.woff2", "quoting": "strong"}]},
            {"command": {"value": "node", "quoting": "strong"}, "args": ["public/fonts/hidden.woff2"]},
            {"command": "echo safe", "windows": {
                "command": {"value": "node", "quoting": "weak"},
                "args": [{"value": "public/fonts/hidden.woff2", "quoting": "weak"}],
            }},
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            editor = Path(temp_dir) / ".vscode"
            editor.mkdir()
            with mock.patch.dict(globals(), {"ROOT": Path(temp_dir)}):
                for command in commands:
                    with self.subTest(command=command):
                        task = {"label": "quoted", "type": "shell", **command}
                        (editor / "tasks.json").write_text(
                            json.dumps({"version": "2.0.0", "tasks": [task]}),
                            encoding="utf-8",
                        )
                        with self.assertRaises(AssertionError):
                            self.test_no_automatic_folder_open_task()

    def test_workspace_does_not_claim_control_of_user_automatic_tasks(self):
        settings = json.loads(
            (ROOT / ".vscode" / "settings.json").read_text(encoding="utf-8")
        )
        # This is a VS Code user/application setting, not a workspace switch.
        self.assertNotIn("task.allowAutomaticTasks", settings)
        self.assertNotIn("tasks", settings)

    def test_disguised_executable_font_is_absent(self):
        self.assertFalse((ROOT / "public/fonts/fa-solid-500.woff2").exists())


if __name__ == "__main__":
    unittest.main()
