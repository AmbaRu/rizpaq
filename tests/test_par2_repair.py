from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QWidget


_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from core import par2_ops
from core.par2_ops import (
    STATE_DAMAGED,
    STATE_FAILED,
    STATE_OK,
    Par2Result,
    create_parset,
    find_par2,
    needs_subst,
    par2_main_name,
    par2_set_files,
    read_recorded_size,
    repair_parset,
    set_is_stale,
    verify_parset,
)
from workers import Par2RepairWorker
from ui.par2_actions import Par2ActionsMixin
from ui.i18n import set_language

PAR2_BIN = find_par2()
HAVE_PAR2 = bool(PAR2_BIN) and os.path.isfile(PAR2_BIN)

requires_par2 = unittest.skipUnless(
    HAVE_PAR2, "par2.exe не найден — живые тесты пропущены"
)


class _TempCase(unittest.TestCase):


    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="par2_repair_test_"))
        self.arch = self.base / "backup.zpaq"
        self.good = b"A" * 120000
        self.arch.write_bytes(self.good)


        self.fake_bin = self.base / "par2.exe"
        self.fake_bin.write_bytes(b"not a real binary")

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def damage(self, count=9000, step=300):
        d = bytearray(self.arch.read_bytes())
        for off in range(0, count, step):
            d[off] ^= 0xFF
        self.arch.write_bytes(bytes(d))


class TestRollbackGuard(unittest.TestCase):

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="par2_guard_"))
        self.arch = self.base / "backup.zpaq"
        self.arch.write_bytes(b"x" * 1000)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_grown_archive_is_stale(self):
        self.assertTrue(set_is_stale(str(self.arch), 500))

    def test_same_size_is_not_stale(self):
        self.assertFalse(set_is_stale(str(self.arch), 1000))

    def test_smaller_file_is_not_stale(self):

        self.assertFalse(set_is_stale(str(self.arch), 5000))

    def test_missing_size_is_unknown_not_false(self):
        self.assertIsNone(set_is_stale(str(self.arch), None))

    def test_missing_file_is_unknown(self):
        self.assertIsNone(
            set_is_stale(str(self.base / "нет.zpaq"), 100)
        )


class TestRepairRefusesWithoutSize(_TempCase):


    def setUp(self):
        super().setUp()


        self.main = self.base / "backup.zpaq.par2"
        self.main.write_bytes(b"x")

    def test_refuses_when_size_unknown(self):
        with mock.patch.object(par2_ops, "_run", return_value=(0, "ok")):
            r = repair_parset(
                str(self.fake_bin), par2_main_name(str(self.arch)),
                archive_path=str(self.arch), recorded_size=None,
            )
        self.assertFalse(r.ok)
        self.assertEqual(r.state, STATE_FAILED)

    def test_refuses_when_archive_path_unknown(self):
        with mock.patch.object(par2_ops, "_run", return_value=(0, "ok")):
            r = repair_parset(
                str(self.fake_bin), par2_main_name(str(self.arch)),
                archive_path=None, recorded_size=1000,
            )
        self.assertFalse(r.ok)

    def test_engine_never_started_when_blocked(self):
        with mock.patch.object(
            par2_ops, "_run", side_effect=AssertionError("движок запущен")
        ):
            r = repair_parset(
                str(self.fake_bin), par2_main_name(str(self.arch)),
                archive_path=str(self.arch), recorded_size=500,
            )
        self.assertFalse(r.ok)

    def test_error_text_explains_why(self):

        self.arch.write_bytes(b"x" * 100000)
        with mock.patch.object(par2_ops, "_run", return_value=(0, "ok")):
            r = repair_parset(
                str(self.fake_bin), par2_main_name(str(self.arch)),
                archive_path=str(self.arch), recorded_size=1000,
            )
        self.assertIn("устарел", r.log)
        self.assertIn("откат", r.log)


class TestRepairCommand(unittest.TestCase):


    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="par2_cmd_"))
        self.arch = self.base / "backup.zpaq"
        self.arch.write_bytes(b"x" * 1000)
        self.main = self.base / "backup.zpaq.par2"
        self.main.write_bytes(b"x")
        self.fake_bin = self.base / "par2.exe"
        self.fake_bin.write_bytes(b"not a real binary")

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_uses_repair_subcommand(self):
        with mock.patch.object(
            par2_ops, "_run", return_value=(0, "ok")
        ) as m:
            repair_parset(
                str(self.fake_bin), str(self.main),
                archive_path=str(self.arch), recorded_size=1000,
            )
        args = m.call_args[0][1]
        self.assertEqual(args[0], "r")
        self.assertIn(str(self.main), args)

    def test_process_is_registered_for_cancel(self):
        seen = {}

        def fake_run(bin_path, args, timeout, register=None):
            seen["register"] = register
            return 0, "ok"

        def my_register(proc):
            return None

        with mock.patch.object(par2_ops, "_run", side_effect=fake_run):
            repair_parset(
                str(self.fake_bin), str(self.main),
                archive_path=str(self.arch), recorded_size=1000,
                register=my_register,
            )
        self.assertIs(seen.get("register"), my_register)


class _RepairHost(Par2ActionsMixin, QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.status_messages = []
        self.logged = []
        self._workers = []
        self.started = []
        self._par2_repair_dialog = None
        self._par2_repair_worker = None

    def statusBar(self):
        return self

    def showMessage(self, msg):
        self.status_messages.append(msg)

    def log_output(self, text):
        self.logged.append(text)

    def _cleanup_worker(self, worker):
        pass

    def _on_refresh(self):
        pass


@requires_par2
class TestConfirmationRequired(_TempCase):

    def setUp(self):
        super().setUp()


        set_language("ru", str(ROOT / "locales"))
        create_parset(PAR2_BIN, str(self.arch))
        self.damage()
        self.host = _RepairHost()

    def test_no_question_when_set_is_stale(self):

        self.arch.write_bytes(self.good + b"NEW-VERSION" * 500)

        with mock.patch(
            "ui.par2_actions.QMessageBox.question",
            side_effect=AssertionError("задан вопрос при устаревшем наборе"),
        ) as q:
            with mock.patch("ui.par2_actions.Par2RepairWorker"):
                started = self.host._start_par2_repair(str(self.arch))

        self.assertFalse(started)
        q.assert_not_called()

    def test_stale_message_mentions_both_sizes(self):
        self.arch.write_bytes(self.good + b"NEW" * 9000)
        with mock.patch("ui.par2_actions.QMessageBox.question"):
            with mock.patch("ui.par2_actions.Par2RepairWorker"):
                self.host._start_par2_repair(str(self.arch))

        text = " ".join(self.host.status_messages)
        self.assertIn("заблокировано", text)

    def test_declined_by_user_does_not_start(self):

        with mock.patch(
            "ui.par2_actions.QMessageBox.question", return_value=0
        ) as q:
            with mock.patch("ui.par2_actions.Par2RepairWorker") as wcls:
                started = self.host._start_par2_repair(str(self.arch))

        self.assertFalse(started)
        q.assert_called_once()
        wcls.assert_not_called()

    def test_confirmed_starts_worker_with_recorded_size(self):
        with mock.patch(
            "ui.par2_actions.QMessageBox.question", return_value=0x4000
        ):
            with mock.patch("ui.par2_actions.Par2RepairWorker") as wcls:
                started = self.host._start_par2_repair(str(self.arch))

        self.assertTrue(started)
        _, kwargs = wcls.call_args
        self.assertEqual(kwargs["recorded_size"], len(self.good))

    def test_healthy_set_does_not_offer_repair(self):

        self.arch.write_bytes(self.good)
        with mock.patch(
            "ui.par2_actions.QMessageBox.question",
            side_effect=AssertionError("задан вопрос при целом наборе"),
        ):
            with mock.patch("ui.par2_actions.Par2RepairWorker"):
                started = self.host._start_par2_repair(str(self.arch))
        self.assertFalse(started)

    def test_missing_set_is_not_offered(self):
        for p in par2_set_files(str(self.arch)):
            os.remove(p)
        with mock.patch("ui.par2_actions.QMessageBox.question"):
            with mock.patch("ui.par2_actions.Par2RepairWorker") as wcls:
                started = self.host._start_par2_repair(str(self.arch))
        self.assertFalse(started)
        wcls.assert_not_called()


class TestWorkerAlwaysEmits(unittest.TestCase):

    def test_emits_done_when_ops_raise(self):
        base = Path(tempfile.mkdtemp(prefix="par2_wf_"))
        try:
            arch = base / "backup.zpaq"
            arch.write_bytes(b"x" * 100)
            worker = Par2RepairWorker("/bin/par2", str(arch), 100)

            seen = []
            worker.done.connect(seen.append)

            with mock.patch.object(
                par2_ops, "repair_parset",
                side_effect=RuntimeError("сломалось"),
            ):
                worker.run()

            self.assertEqual(len(seen), 1, "done обязан прийти всегда")
            self.assertFalse(seen[0]["ok"])
            self.assertIn("сломалось", seen[0]["log"])
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def test_reports_actual_and_recorded_sizes(self):
        base = Path(tempfile.mkdtemp(prefix="par2_ws_"))
        try:
            arch = base / "backup.zpaq"
            arch.write_bytes(b"x" * 555)
            worker = Par2RepairWorker("/bin/par2", str(arch), 100)

            seen = []
            worker.done.connect(seen.append)
            with mock.patch.object(
                par2_ops, "repair_parset",
                return_value=Par2Result(True, STATE_OK, "ok"),
            ):
                worker.run()

            self.assertEqual(seen[0]["actual_size"], 555)
            self.assertEqual(seen[0]["recorded_size"], 100)
        finally:
            shutil.rmtree(base, ignore_errors=True)


@requires_par2
class TestLiveRepair(_TempCase):


    def test_repairs_real_damage(self):
        create_parset(PAR2_BIN, str(self.arch))
        self.damage()

        v = verify_parset(PAR2_BIN, par2_main_name(str(self.arch)))
        self.assertEqual(v.state, STATE_DAMAGED, v.log)

        r = repair_parset(
            PAR2_BIN, par2_main_name(str(self.arch)),
            archive_path=str(self.arch), recorded_size=v.recorded_size,
        )
        self.assertTrue(r.ok, r.log)
        self.assertEqual(self.arch.read_bytes(), self.good)

    def test_stale_set_cannot_roll_back(self):
        create_parset(PAR2_BIN, str(self.arch))
        grown = self.good + b"SECOND" * 2000
        self.arch.write_bytes(grown)
        size_before = self.arch.stat().st_size

        v = verify_parset(PAR2_BIN, par2_main_name(str(self.arch)))
        self.assertTrue(set_is_stale(str(self.arch), v.recorded_size))

        r = repair_parset(
            PAR2_BIN, par2_main_name(str(self.arch)),
            archive_path=str(self.arch), recorded_size=v.recorded_size,
        )

        self.assertFalse(r.ok, "устаревший набор нельзя применять")
        self.assertEqual(self.arch.stat().st_size, size_before)
        self.assertEqual(self.arch.read_bytes(), grown)

    def test_recorded_size_matches_archive(self):
        create_parset(PAR2_BIN, str(self.arch))
        v = verify_parset(PAR2_BIN, par2_main_name(str(self.arch)))
        self.assertEqual(v.recorded_size, self.arch.stat().st_size)
        self.assertFalse(set_is_stale(str(self.arch), v.recorded_size))


if __name__ == "__main__":
    unittest.main()
