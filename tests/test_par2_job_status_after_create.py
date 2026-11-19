






from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from core import headless
from ui.par2_actions import Par2ActionsMixin


class _Res:
    def __init__(self, ok, log="", recorded_size=None):
        self.ok = ok
        self.log = log
        self.recorded_size = recorded_size


class TestHeadlessPar2Result(unittest.TestCase):
    def _args(self):
        return ("D:/tasks.rzp", {}, {}, "D:/a.zpaq", {})

    @mock.patch("core.par2_ops.find_par2", return_value=None)
    def test_no_binary_is_failure(self, _find):
        ok, note = headless._headless_par2(*self._args())
        self.assertFalse(ok)
        self.assertIn("не найден", note)

    @mock.patch("core.par2_ops.find_par2", return_value="par2.exe")
    @mock.patch(
        "core.par2_ops.refresh_par2_set",
        return_value=_Res(False, "disk full", None),
    )
    def test_failed_set_is_failure(self, _refresh, _find):
        ok, note = headless._headless_par2(*self._args())
        self.assertFalse(ok)
        self.assertIn("НЕ создан", note)

    @mock.patch("core.par2_ops.find_par2", return_value="par2.exe")
    @mock.patch(
        "core.par2_ops.refresh_par2_set",
        return_value=_Res(True, "created", 12345),
    )
    def test_success(self, _refresh, _find):
        ok, note = headless._headless_par2(*self._args())
        self.assertTrue(ok)
        self.assertIn("набор создан", note)

    @mock.patch("core.par2_ops.find_par2", return_value="par2.exe")
    @mock.patch(
        "core.par2_ops.refresh_par2_set",
        return_value=_Res(True, "архив не изменился", None),
    )
    def test_unchanged_archive_is_still_protected(self, _refresh, _find):
        ok, note = headless._headless_par2(*self._args())
        self.assertTrue(ok)
        self.assertIn("остался в силе", note)


class TestGuiFinalStatus(unittest.TestCase):
    pass

    def _host(self, result_ok=True, skipped=False):
        host = SimpleNamespace()
        host.calls = []
        host._par2_worker = None
        host._report_gate = None
        host._create_report = None
        host._pending_create_report = None
        host._pending_job_meta = {
            "job_context": {"work_id": "w1", "job_id": "j1"},
            "rc": 0,
            "output": "ARCHIVE LOG",
        }
        host.log_output = lambda *_a, **_kw: None
        host._save_par2_marker = lambda *_a: None
        host._par2_note = lambda *_a: None
        host._report_stage_done = lambda _stage: None
        host._update_job_meta_after_run = (
            lambda *a, **kw: host.calls.append((a, kw))
        )
        host._result_ok = result_ok
        host._skipped = skipped
        return host

    def _run(self, host):
        Par2ActionsMixin._on_par2_done(
            host,
            {"work_id": "w1", "job_id": "j1"},
            {
                "ok": host._result_ok,
                "cancelled": False,
                "log": "",
                "recorded_size": 100,
                "archive_path": "D:/a.zpaq",
                "skipped": host._skipped,
            },
            None,
        )

    def test_protection_created_marks_job_ok(self):
        host = self._host()
        self._run(host)
        self.assertEqual(len(host.calls), 1)
        self.assertEqual(host.calls[0][0][1], "ok")
        self.assertIsNone(host.calls[0][1].get("reason"))
        self.assertIsNone(host._pending_job_meta)

    def test_protection_skipped_marks_job_ok(self):
        host = self._host(skipped=True)
        self._run(host)
        self.assertEqual(host.calls[0][0][1], "ok")

    def test_protection_failed_marks_job_error(self):
        host = self._host(result_ok=False)
        self._run(host)
        self.assertEqual(host.calls[0][0][1], "error")
        self.assertEqual(host.calls[0][1]["reason"], "par2_failed")


if __name__ == "__main__":
    unittest.main()
