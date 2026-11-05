import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from tests.test_par2_launch import _Host, _TmpCase
from ui.backup_page import BackupPage
from ui.i18n import set_language, tr

set_language("ru", str(ROOT / "locales"))


class TestPar2JobStatus(_TmpCase):
    class _MetaHost(_Host):


        def __init__(self, container=None):
            super().__init__(container=container)
            self.meta_calls = []

        def _update_job_meta_after_run(self, job_context, status, reason=None,
                                       rc=None, output=None):
            self.meta_calls.append(
                (dict(job_context or {}), status, reason)
            )

    def _host_with_meta(self):
        return self._MetaHost(container=None)

    def _done(self, host, state, job_context=None):
        host._on_par2_verify_done(
            job_context,
            {
                "state": state,
                "log": "",
                "cancelled": False,
                "archive_path": str(self.arch),
            },
        )

    def test_ok_records_ok(self):

        host = self._host_with_meta()
        ctx = {"work_id": "w1", "job_id": "j1"}
        self._done(host, "ok", ctx)
        self.assertEqual(host.meta_calls, [(ctx, "ok", None)])

    def test_damaged_records_error(self):

        host = self._host_with_meta()
        ctx = {"work_id": "w1", "job_id": "j1"}
        self._done(host, "damaged", ctx)
        self.assertEqual(
            host.meta_calls, [(ctx, "error", "par2_damaged")]
        )

    def test_unrepairable_records_error(self):
        host = self._host_with_meta()
        ctx = {"work_id": "w1", "job_id": "j1"}
        self._done(host, "unrepairable", ctx)
        self.assertEqual(
            host.meta_calls, [(ctx, "error", "par2_unrepairable")]
        )

    def test_missing_records_error(self):

        host = self._host_with_meta()
        ctx = {"work_id": "w1", "job_id": "j1"}
        self._done(host, "missing", ctx)
        self.assertEqual(
            host.meta_calls, [(ctx, "error", "par2_missing")]
        )

    def test_broken_records_error(self):

        host = self._host_with_meta()
        ctx = {"work_id": "w1", "job_id": "j1"}
        self._done(host, "broken", ctx)
        self.assertEqual(
            host.meta_calls, [(ctx, "error", "par2_broken")]
        )

    def test_without_job_context_no_meta_call(self):

        host = self._host_with_meta()
        self._done(host, "ok", None)
        self.assertEqual(host.meta_calls, [])

    def test_cancelled_records_nothing(self):

        host = self._host_with_meta()
        ctx = {"work_id": "w1", "job_id": "j1"}
        host._on_par2_verify_done(
            ctx,
            {
                "state": "ok",
                "log": "",
                "cancelled": True,
                "archive_path": str(self.arch),
            },
        )
        self.assertEqual(host.meta_calls, [])


class TestPar2ReasonDisplay(_TmpCase):

    def test_error_with_reason_in_column_text(self):
        job = {"last_status": "error", "last_reason": "par2_missing"}
        text, _ = BackupPage._status_text_and_token(job)
        self.assertIn(tr("backup.status.error"), text)
        self.assertIn(tr("backup.reason.par2_missing"), text)

    def test_error_without_reason_unchanged(self):
        job = {"last_status": "error", "last_reason": None}
        text, _ = BackupPage._status_text_and_token(job)
        self.assertEqual(text, tr("backup.status.error"))

    def test_unknown_reason_falls_back_to_plain_error(self):

        job = {"last_status": "error", "last_reason": "quantum_fluctuation"}
        text, _ = BackupPage._status_text_and_token(job)
        self.assertEqual(text, tr("backup.status.error"))

    def test_ok_has_no_reason_text(self):
        job = {"last_status": "ok", "last_reason": None}
        text, _ = BackupPage._status_text_and_token(job)
        self.assertEqual(text, tr("backup.status.ok"))

    def test_tooltip_full_text_and_last_run(self):
        job = {
            "last_status": "error",
            "last_reason": "par2_missing",
            "last_run": "2026-10-26 22:07:47",
        }
        tip = BackupPage._status_tooltip(job)
        self.assertIn(tr("backup.reason_full.par2_missing"), tip)
        self.assertIn("2026-10-26 22:07:47", tip)

    def test_tooltip_empty_for_plain_error(self):

        job = {"last_status": "error", "last_reason": None}
        self.assertEqual(BackupPage._status_tooltip(job), "")

    def test_tooltip_empty_for_ok(self):
        job = {"last_status": "ok", "last_reason": None}
        self.assertEqual(BackupPage._status_tooltip(job), "")

    def test_tooltip_unknown_reason_is_empty(self):
        job = {"last_status": "error", "last_reason": "quantum_fluctuation"}
        self.assertEqual(BackupPage._status_tooltip(job), "")


class TestUpdateJobMetaReason(_TmpCase):

    def _container_with_job(self):
        from core.tasks import add_job, add_work, empty_container

        c = empty_container()
        w = add_work(c, title="w", sources=[], dest="d:/x.zpaq")
        j = add_job(c, w["id"], {})
        return c, j["id"]

    def test_error_keeps_reason(self):
        from core.tasks import update_job_meta

        c, jid = self._container_with_job()
        self.assertTrue(update_job_meta(c, jid, "error", reason="par2_missing"))
        job = c["works"][0]["jobs"][0]
        self.assertEqual(job["last_status"], "error")
        self.assertEqual(job["last_reason"], "par2_missing")

    def test_ok_clears_reason(self):
        from core.tasks import update_job_meta

        c, jid = self._container_with_job()
        update_job_meta(c, jid, "error", reason="par2_damaged")
        update_job_meta(c, jid, "ok")
        job = c["works"][0]["jobs"][0]
        self.assertEqual(job["last_status"], "ok")
        self.assertIsNone(job["last_reason"])

    def test_unknown_reason_dropped(self):
        from core.tasks import update_job_meta

        c, jid = self._container_with_job()
        update_job_meta(c, jid, "error", reason="weird")
        job = c["works"][0]["jobs"][0]
        self.assertEqual(job["last_status"], "error")
        self.assertIsNone(job["last_reason"])

    def test_reason_without_value_is_none(self):

        from core.tasks import update_job_meta

        c, jid = self._container_with_job()
        update_job_meta(c, jid, "error", reason="par2_broken")
        update_job_meta(c, jid, "error")
        job = c["works"][0]["jobs"][0]
        self.assertIsNone(job["last_reason"])

    def test_normalise_job_reads_reason(self):

        import io, os, tempfile
        from core.tasks import (
            add_job,
            add_work,
            empty_container,
            load_container,
            save_container,
            update_job_meta,
        )

        c, jid = self._container_with_job()
        update_job_meta(c, jid, "error", reason="par2_unrepairable")
        fd, path = tempfile.mkstemp(suffix=".rzp")
        os.close(fd)
        try:
            save_container(path, c)
            loaded = load_container(path)
            _w, job = next(
                (wk, jj)
                for wk, jj in
                [(w, j) for w in loaded["works"] for j in w["jobs"]]
                if jj["id"] == jid
            )
            self.assertEqual(job["last_reason"], "par2_unrepairable")
        finally:
            os.unlink(path)

    def test_normalise_job_unknown_reason_becomes_none(self):
        import io, os, tempfile
        from core.tasks import (
            add_job,
            add_work,
            empty_container,
            load_container,
            save_container,
        )

        c, jid = self._container_with_job()
        c["works"][0]["jobs"][0]["last_reason"] = "from_the_future"
        fd, path = tempfile.mkstemp(suffix=".rzp")
        os.close(fd)
        try:
            save_container(path, c)
            loaded = load_container(path)
            job = loaded["works"][0]["jobs"][0]
            self.assertIsNone(job["last_reason"])
        finally:
            os.unlink(path)


class TestQuickCheckRefusal(_TmpCase):

    class _RefuseHost(_Host):


        def __init__(self, container=None):
            super().__init__(container=container)
            self.refuse_calls = []

        def _par2_refuse(self, archive_path, text_key, warn=False):
            self.refuse_calls.append((str(archive_path), text_key, warn))
            return False

    def test_missing_set_shows_dialog(self):

        host = self._RefuseHost(container=None)
        started = host._start_par2_verify(str(self.arch))
        self.assertFalse(started)
        self.assertEqual(len(host.refuse_calls), 1)
        path, key, warn = host.refuse_calls[0]
        self.assertEqual(path, str(self.arch))
        self.assertEqual(key, "backup.reason_full.par2_missing")
        self.assertFalse(warn)
        self.assertIsNone(host._par2_verify_dialog)

    def test_missing_engine_shows_warning(self):

        host = self._RefuseHost(container=None)
        import unittest.mock as m
        with m.patch("core.par2_ops.find_par2", return_value=None):
            started = host._start_par2_verify(str(self.arch))
        self.assertFalse(started)
        _path, key, warn = host.refuse_calls[0]
        self.assertEqual(key, "backup.reason_full.par2_failed")
        self.assertTrue(warn)

    def test_real_refuse_writes_note_and_box(self):
        import unittest.mock as m

        host = _Host(container=None)
        with m.patch("PySide6.QtWidgets.QMessageBox") as box:
            ok = host._par2_refuse(str(self.arch), "backup.reason_full.par2_missing")
        self.assertFalse(ok)
        self.assertIn(
            tr("backup.reason_full.par2_missing"),
            " ".join(host.status_messages),
        )
        self.assertTrue(box.information.called)

    def test_real_refuse_warn_uses_warning(self):
        import unittest.mock as m

        host = _Host(container=None)
        with m.patch("PySide6.QtWidgets.QMessageBox") as box:
            host._par2_refuse(
                str(self.arch), "backup.reason_full.par2_failed", warn=True
            )
        self.assertTrue(box.warning.called)
        self.assertFalse(box.information.called)


if __name__ == "__main__":
    unittest.main()
