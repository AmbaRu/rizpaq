







from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from ui.extraction import ExtractionMixin
from workers.extract_workers import ExtractFolderBatchWorker

MASK = "downloads_????.zpaq"


class TestRangeExtractCommand(unittest.TestCase):
    def test_file_range(self):
        w = ExtractFolderBatchWorker(
            "z", MASK, None, "a.txt", None, "out",
            range_spec="2:3", only_pattern="*a.txt",
        )
        self.assertEqual(
            w.cmd,
            ["z", "x", MASK, "-only", "*a.txt", "-all",
             "-range", "2:3", "-to", "out"],
        )

    def test_folder_range_with_password(self):
        w = ExtractFolderBatchWorker(
            "z", MASK, "pw", "dir1", None, "out",
            range_spec="2:3", only_pattern="*dir1/*",
        )
        self.assertEqual(
            w.cmd,
            ["z", "x", MASK, "-key", "pw", "-only", "*dir1/*", "-all",
             "-range", "2:3", "-to", "out"],
        )

    def test_without_range_keeps_old_until_contract(self):
        w = ExtractFolderBatchWorker("z", MASK, None, "dir1", 3, "out")
        self.assertEqual(
            w.cmd,
            ["z", "x", MASK, "-only", "dir1/*", "-until", "3", "-to", "out"],
        )


class _Host(ExtractionMixin):
    def __init__(self):
        self.calls = []
        self.messages = []

    def statusBar(self):
        return self

    def showMessage(self, text):
        self.messages.append(text)

    def _start_extract_folder_batch_worker(
        self, prefix, version, dest, range_spec=None, only_pattern=None
    ):
        self.calls.append((prefix, version, dest, range_spec, only_pattern))


@patch("ui.extraction.tr", side_effect=lambda key, **kw: key)
class TestRangePatternFromUi(unittest.TestCase):
    def test_file_pattern_starts_with_star(self, _tr):
        host = _Host()
        host._start_range_worker("a.txt", "2:3", Path("out"), True)
        self.assertEqual(
            host.calls,
            [("a.txt", None, "out", "2:3", "*a.txt")],
        )

    def test_folder_pattern_starts_with_star(self, _tr):
        host = _Host()
        host._start_range_worker("dir1", "2:3", Path("out"), False)
        self.assertEqual(
            host.calls,
            [("dir1", None, "out", "2:3", "*dir1/*")],
        )


if __name__ == "__main__":
    unittest.main()
