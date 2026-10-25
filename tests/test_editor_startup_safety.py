"""Static safeguards for editor-startup behavior; never execute workspace tasks."""

import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class EditorStartupSafetyTests(unittest.TestCase):
    def test_no_automatic_folder_open_task(self):
        tasks = (ROOT / ".vscode" / "tasks.json").read_text(encoding="utf-8")
        for task in json.loads(tasks).get("tasks", []):
            self.assertNotEqual(
                task.get("runOptions", {}).get("runOn"),
                "folderOpen",
                f"Task {task.get('label', '<unnamed>')} must not run on folderOpen",
            )
        self.assertIsNone(re.search(r"\bnode\s+[^\n]*public/fonts/", tasks))

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
