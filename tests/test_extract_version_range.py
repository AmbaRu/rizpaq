






from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from core.models import ArchiveEntry
from ui.extraction import ExtractionMixin


class _Host(ExtractionMixin):
    def __init__(self):
        self.calls = []
        self.messages = []
        self.last_done = None

    def statusBar(self):
        return self

    def showMessage(self, text):
        self.messages.append(text)

    def _initial_extract_dir(self):
        return Path(".")

    def _can_start_extract(self):
        return True

    def _start_extract_file_worker(self, entry, dest, open_after=False, on_done=None):
        self.calls.append(("file", entry.version, dest))
        self.last_done = on_done

    def _start_extract_folder_batch_worker(self, prefix, version, dest, on_done=None):
        self.calls.append(("folder", version, dest))
        self.last_done = on_done


@patch("ui.extraction.tr", side_effect=lambda key, **kw: key)
class TestExtractRangeQueue(unittest.TestCase):
    def test_file_versions_run_one_by_one(self, _tr):
        host = _Host()
        entry = ArchiveEntry("docs/report.docx", 10, "2026-01-01", 3, "", False)
        queue = [(2, "out/report_v2.docx"), (3, "out/report_v3.docx")]
        host._start_range_step("file", entry, queue, Path("out"))

        self.assertEqual(host.calls, [("file", 2, "out/report_v2.docx")])
        self.assertEqual(entry.version, 3, "исходная запись не меняется")

        host.last_done({"success": True})
        self.assertEqual(
            host.calls,
            [
                ("file", 2, "out/report_v2.docx"),
                ("file", 3, "out/report_v3.docx"),
            ],
        )

        host.last_done({"success": True})
        self.assertEqual(len(host.calls), 2)
        self.assertEqual(host.messages[-1], "status.extract_range_done")

    def test_folder_versions_run_one_by_one(self, _tr):
        host = _Host()
        queue = [(2, "out/00000002"), (3, "out/00000003")]
        host._start_range_step("folder", "docs", queue, Path("out"))

        self.assertEqual(host.calls, [("folder", 2, "out/00000002")])
        host.last_done({"success": True})
        self.assertEqual(
            host.calls,
            [("folder", 2, "out/00000002"), ("folder", 3, "out/00000003")],
        )


if __name__ == "__main__":
    unittest.main()
