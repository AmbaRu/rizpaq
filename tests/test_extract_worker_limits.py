from __future__ import annotations

import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication

import workers.extract_workers as ew
from workers.extract_workers import ExtractFolderWorker

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


class _FakeProc:

    def __init__(self, payload: bytes = b"", rc: int = 0, hang: bool = False):
        self._r, self._w = os.pipe()
        if payload:
            os.write(self._w, payload)
        if not hang:
            os.close(self._w)
        self.stdout = os.fdopen(self._r, "rb", buffering=0)
        self.returncode = None if hang else rc
        self.killed = False
        self.pid = 0

    def poll(self):
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9
        try:
            os.close(self._w)
        except OSError:
            pass

    def wait(self, timeout=None):
        return self.returncode


class ExtractWorkerTestBase(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_exw_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.tasks = [("f.txt", 1, str(self.dir / "f.txt"))]

    def _worker(self):
        return ExtractFolderWorker(
            "zpaq", "a.zpaq", None, list(self.tasks), self.dir
        )

    def _run(self, worker):
        got: list = []
        worker.done.connect(got.append)
        worker.run()
        return got[0]

    def _patch_popen(self, **kwargs):
        return mock.patch(
            "workers.extract_workers.subprocess.Popen", **kwargs
        )


class TestStallAndCancel(ExtractWorkerTestBase):
    def test_silent_process_is_stopped(self):

        fake = _FakeProc(hang=True)
        self.addCleanup(fake.stdout.close)

        with self._patch_popen(return_value=fake), mock.patch.object(
            ew, "STALL_TIMEOUT", 0.3
        ):
            t0 = time.monotonic()
            result = self._run(self._worker())
            elapsed = time.monotonic() - t0

        fake.stdout.close()

        self.assertTrue(fake.killed, "молчащий процесс не убит")
        self.assertLess(elapsed, 10.0, "воркер ждал слишком долго")
        self.assertEqual(result["ok"], 0)
        self.assertEqual(result["errors"], ["f.txt"])
        self.assertIn("движок не отвечал", result["error_logs"][0])

    def test_cancel_kills_current_file(self):

        fake = _FakeProc(hang=True)
        self.addCleanup(fake.stdout.close)

        worker = self._worker()

        def cancel_when_started():
            for _ in range(300):
                if worker._proc is not None:
                    break
                time.sleep(0.01)
            worker.cancel_request()

        timer = threading.Timer(0.05, cancel_when_started)
        timer.start()
        try:
            with self._patch_popen(return_value=fake), mock.patch.object(
                ew, "STALL_TIMEOUT", 30
            ):
                result = self._run(worker)
        finally:
            timer.cancel()

        fake.stdout.close()

        self.assertTrue(fake.killed, "процесс не убит по отмене")
        self.assertTrue(result["cancelled"])


class TestFailureReason(ExtractWorkerTestBase):
    def test_missing_engine_keeps_reason(self):

        with self._patch_popen(side_effect=FileNotFoundError("нет движка")):
            result = self._run(self._worker())

        self.assertEqual(result["ok"], 0)
        self.assertEqual(result["errors"], ["f.txt"])
        self.assertIn("ERROR", result["error_logs"][0])
        self.assertIn("нет движка", result["error_logs"][0])


class TestErrorLogsAreBounded(ExtractWorkerTestBase):
    def test_logs_are_capped_and_truncated(self):

        self.tasks = [
            (f"f{i}.txt", 1, str(self.dir / f"f{i}.txt"))
            for i in range(ew.MAX_ERROR_LOGS + 2)
        ]
        payload = b"x" * 1000
        procs = []

        def make_proc(*_args, **_kwargs):
            proc = _FakeProc(payload=payload, rc=1)
            procs.append(proc)
            return proc

        with self._patch_popen(side_effect=make_proc), mock.patch.object(
            ew, "MAX_ERROR_LOG_CHARS", 100
        ):
            result = self._run(self._worker())

        for proc in procs:
            proc.stdout.close()

        self.assertEqual(result["ok"], 0)
        self.assertEqual(len(result["errors"]), ew.MAX_ERROR_LOGS + 2)
        self.assertEqual(len(result["error_logs"]), ew.MAX_ERROR_LOGS)
        for text in result["error_logs"]:
            self.assertLessEqual(len(text), 100)


if __name__ == "__main__":
    unittest.main()
