"""Static safeguards for editor-startup behavior; never execute workspace tasks."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EditorStartupSafetyTests(unittest.TestCase):
    def test_no_automatic_folder_open_task(self):
        tasks = (ROOT / ".vscode" / "tasks.json").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r'"runOn"\s*:\s*"folderOpen"', tasks))
        self.assertIsNone(re.search(r"\bnode\s+[^\n]*public/fonts/", tasks))

    def test_workspace_disables_automatic_tasks(self):
        settings = json.loads(
            (ROOT / ".vscode" / "settings.json").read_text(encoding="utf-8")
        )
        self.assertIs(settings.get("task.allowAutomaticTasks"), False)
        self.assertNotIn("tasks", settings)

    def test_disguised_executable_font_is_absent(self):
        self.assertFalse((ROOT / "public/fonts/fa-solid-500.woff2").exists())


if __name__ == "__main__":
    unittest.main()
