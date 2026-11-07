










from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication              

from workers.universal_worker import UniversalExtractWorker              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))



class TestUniversalExtractResult(unittest.TestCase):
    def setUp(self):
        self.dest = Path(tempfile.mkdtemp(prefix="rizpaq_uni_"))
        self.addCleanup(shutil.rmtree, self.dest, ignore_errors=True)

    def _run(self, rc: int = 0, files=None, cancel=False):
        worker = UniversalExtractWorker(
            "7z.exe", "a.7z", str(self.dest), None, files
        )
        worker._run_stream = lambda: (rc, "Everything is Ok")
        if cancel:
            worker.cancel_request()

        got: list = []
        worker.done.connect(got.append)
        worker.run()
        return got[0]

                                                                               
    def test_empty_destination_is_not_success(self):
        pass
        result = self._run(rc=0)

        self.assertFalse(result["ok"])

    def test_missing_destination_is_not_success(self):
        shutil.rmtree(self.dest)
        result = self._run(rc=0)

        self.assertFalse(result["ok"])

                                                                                
    def test_extracted_file_is_success(self):
        (self.dest / "file.txt").write_text("data", encoding="utf-8")

        self.assertTrue(self._run(rc=0)["ok"])

    def test_extracted_directory_is_success(self):
        pass
        (self.dest / "sub").mkdir()

        self.assertTrue(self._run(rc=0)["ok"])

                                                                               
    def test_named_files_must_exist(self):
        (self.dest / "a.txt").write_text("data", encoding="utf-8")

        self.assertTrue(self._run(rc=0, files=["a.txt"])["ok"])
        self.assertFalse(self._run(rc=0, files=["b.txt"])["ok"])

    def test_wildcard_falls_back_to_non_empty(self):
        pass
        (self.dest / "b.txt").write_text("data", encoding="utf-8")

        self.assertTrue(self._run(rc=0, files=["*.txt"])["ok"])

                                                                                
    def test_nonzero_rc_is_failure_even_with_content(self):
        (self.dest / "file.txt").write_text("data", encoding="utf-8")

        self.assertFalse(self._run(rc=1)["ok"])

    def test_cancel_is_not_success(self):
        (self.dest / "file.txt").write_text("data", encoding="utf-8")

        result = self._run(rc=0, cancel=True)

        self.assertFalse(result["ok"])
        self.assertTrue(result["cancelled"])


if __name__ == "__main__":
    unittest.main()
