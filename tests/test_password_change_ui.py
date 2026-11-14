                       








from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ui import i18n              

i18n.set_language("ru", notify=False)

import ui.archive_actions as aa              


class PasswordChangeUiTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.archive = base / "arc.zpaq"
        self.archive.write_bytes(b"old archive")
        self.target = base / "arc.new.zpaq"
        self.target.write_bytes(b"new archive")

        host = aa.ArchiveActionsMixin.__new__(aa.ArchiveActionsMixin)
        host._stop_busy = lambda: None
        host.statusBar = lambda: host
        host.showMessage = lambda *a, **k: None
        host.log_output = lambda *a, **k: None
        host._on_refresh = lambda: None
        self.cache = {}
        host._cache = lambda _p: self.cache
        self.host = host

    def _result(self, rc=0, output=""):
        return {
            "rc": rc,
            "output": output,
            "context": {
                "path": str(self.archive),
                "target": str(self.target),
                "new_password": "newpass",
                "job_context": None,
            },
        }

    def test_success_replaces_archive_and_stores_new_password(self):
        with mock.patch.object(aa, "set_password") as store, \
                mock.patch.object(aa.QMessageBox, "information"), \
                mock.patch.object(aa.QMessageBox, "warning"):
            self.host._on_password_result(self._result())

        self.assertEqual(self.archive.read_bytes(), b"new archive")
        self.assertFalse(self.target.exists())
        store.assert_called_once_with(str(self.archive), "newpass")
        self.assertEqual(self.cache["password"], "newpass")

    def test_failure_removes_temp_and_keeps_archive(self):
        with mock.patch.object(aa, "set_password") as store, \
                mock.patch.object(aa.QMessageBox, "information"), \
                mock.patch.object(aa.QMessageBox, "warning"):
            self.host._on_password_result(self._result(rc=1, output="boom"))

        self.assertEqual(self.archive.read_bytes(), b"old archive")
        self.assertFalse(self.target.exists())
        store.assert_not_called()

    def test_replace_failure_keeps_archive_and_reports_error(self):
        with mock.patch.object(
                aa.os, "replace", side_effect=OSError("busy")) as replace, \
                mock.patch.object(aa, "set_password") as store, \
                mock.patch.object(aa.QMessageBox, "information") as info, \
                mock.patch.object(aa.QMessageBox, "warning") as warn:
            self.host._on_password_result(self._result())

        replace.assert_called_once()
        self.assertEqual(self.archive.read_bytes(), b"old archive")
        store.assert_not_called()
        info.assert_not_called()
        warn.assert_called_once()
        self.assertIn("cannot replace", warn.call_args[0][2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
