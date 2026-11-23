
from __future__ import annotations

import os
import unittest
from unittest import mock

from ui import archive_table


class TestDragExtraction(unittest.TestCase):
    def test_to_folder_has_trailing_separator(self):
        seen = {}

        def fake_run(cmd, **kwargs):
            seen["cmd"] = cmd
            target = None
            if "-to" in cmd:
                target = cmd[cmd.index("-to") + 1]
            os.makedirs(target, exist_ok=True)
            with open(os.path.join(target, "x.txt"), "wb") as out:
                out.write(b"x")
            return mock.Mock(returncode=0, stdout=b"")

        with mock.patch.object(archive_table.subprocess, "run",
                               side_effect=fake_run):
            urls, folder, notes = archive_table._extract_for_drag(
                "zpaq", "F:/a.zpaq", None, [("x.txt", False)]
            )
        self.assertTrue(seen["cmd"][seen["cmd"].index("-to") + 1]
                        .endswith(("\\", "/")))
        self.assertTrue(urls)
        self.assertNotIn("failed_chunks", notes)

    def test_engine_error_is_not_silent(self):
        def fake_run(cmd, **kwargs):
            return mock.Mock(returncode=2, stdout=b"engine: use -force")

        with mock.patch.object(archive_table.subprocess, "run",
                               side_effect=fake_run):
            _urls, _folder, notes = archive_table._extract_for_drag(
                "zpaq", "F:/a.zpaq", None, [("x.txt", False)]
            )
        self.assertEqual(notes.get("failed_chunks"), 1)
        self.assertIn("use -force", notes.get("error", ""))


if __name__ == "__main__":
    unittest.main()
