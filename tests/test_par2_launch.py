

























from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import (              
    QApplication,
    QDialog,
    QMessageBox,
    QWidget,
)

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from ui.i18n import set_language, tr              
from ui.par2_actions import Par2ActionsMixin              
from ui.presentation import format_size              

                                                                    
                                                                       
                         
set_language("ru", str(ROOT / "locales"))


class _FakeWorker:
    pass

    def __init__(self, bin_path, archive_path, options=None,
                 unchanged_size=None, parent=None):
        self.bin_path = bin_path
        self.archive_path = archive_path
        self.options = dict(options or {})
        self.unchanged_size = unchanged_size
        self.done = mock.Mock()
        self.finished = mock.Mock()
        self.started = False

    def start(self):
        self.started = True


class _Host(Par2ActionsMixin, QWidget):
    pass















    def __init__(self, container=None):
        QWidget.__init__(self)
        self.status_messages = []
        self.logged = []
        self._workers = []
        self._container = container
        self.markers = []
        self._par2_verify_dialog = None
        self._par2_verify_worker = None

    def _load_container(self):
        if self._container is None:
            return None, None
        return self._container, "fake.rzp"

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

    def _save_par2_marker(self, job_context, size):
        self.markers.append((job_context, size))


def _assert_create_called_for(start_mock, path, recreate=False):
    pass






    start_mock.assert_called_once()
    args, kwargs = start_mock.call_args
    called_path = args[0] if args else kwargs.get("archive_path")
    assert called_path == path, f"создание звали для {called_path!r}"
    got = kwargs.get("recreate", False)
    assert got == recreate, f"recreate={got!r}, ждали {recreate!r}"


def _container_with(par2_enabled=True, options=None, work_id="w1",
                    job_id="j1"):
    pass
    return {
        "works": [{
            "id": work_id,
            "par2_size": 4242,
            "jobs": [{
                "id": job_id,
                "par2_enabled": par2_enabled,
                "par2_options": options if options is not None
                else {"redundancy": 5},
            }],
        }],
    }


class _TmpCase(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_par2_launch_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.arch = self.dir / "backup.zpaq"
        self.arch.write_bytes(b"Z" * 4096)


class TestStartDecision(_TmpCase):
    pass

    def _run(self, host, job_context, fallback):
        pass
        created = []

        def make_worker(bin_path, archive_path, options=None,
                        unchanged_size=None, parent=None):
            w = _FakeWorker(bin_path, archive_path, options,
                            unchanged_size, parent)
            created.append(w)
            return w

        with mock.patch("core.par2_ops.find_par2",
                        return_value="par2.exe"), \
             mock.patch("ui.par2_actions.Par2CreateWorker",
                        side_effect=make_worker):
            started = host._start_par2_worker(
                job_context, str(self.arch), fallback
            )
        return started, created

                                                                    

    def test_starts_without_job_context(self):
        pass





        host = _Host(container=None)
        fallback = {"enabled": True, "options": {"redundancy": 5}}

        started, created = self._run(host, None, fallback)

        self.assertTrue(started, "набор не запущен без job_context")
        self.assertEqual(len(created), 1)
        self.assertTrue(created[0].started)
        self.assertEqual(created[0].options, {"redundancy": 5})
                                                                     
                                                                  
        self.assertIsNone(created[0].unchanged_size)

    def test_starts_with_empty_job_context(self):
        pass
        host = _Host(container=None)
        fallback = {"enabled": True, "options": {"redundancy": 10}}

        started, created = self._run(host, {}, fallback)

        self.assertTrue(started)
        self.assertEqual(created[0].options, {"redundancy": 10})

    def test_fallback_disabled_starts_nothing(self):
        pass
        host = _Host(container=_container_with(par2_enabled=True))
        fallback = {"enabled": False, "options": {}}

        started, created = self._run(
            host, {"work_id": "w1", "job_id": "j1"}, fallback
        )

        self.assertFalse(started)
        self.assertEqual(created, [])

                                                                          

    def test_fallback_overrides_container(self):
        pass






        host = _Host(container=_container_with(par2_enabled=True))
        ctx = {"work_id": "w1", "job_id": "j1"}

        started, created = self._run(
            host, ctx, {"enabled": False, "options": {}}
        )
        self.assertFalse(started)
        self.assertEqual(created, [])

        host2 = _Host(container=_container_with(
            par2_enabled=False, options={"redundancy": 1}
        ))
        started2, created2 = self._run(
            host2, ctx, {"enabled": True, "options": {"redundancy": 9}}
        )
        self.assertTrue(started2)
        self.assertEqual(created2[0].options, {"redundancy": 9})

    def test_container_used_when_no_fallback(self):
        pass
        host = _Host(container=_container_with(
            par2_enabled=True, options={"redundancy": 3}
        ))

        started, created = self._run(
            host, {"work_id": "w1", "job_id": "j1"}, None
        )

        self.assertTrue(started)
        self.assertEqual(created[0].options, {"redundancy": 3})
                                                      
        self.assertEqual(created[0].unchanged_size, 4242)

    def test_container_disabled_starts_nothing(self):
        pass
        host = _Host(container=_container_with(par2_enabled=False))

        started, created = self._run(
            host, {"work_id": "w1", "job_id": "j1"}, None
        )

        self.assertFalse(started)
        self.assertEqual(created, [])

                                                                      

    def test_no_fallback_and_no_container_starts_nothing(self):
        pass
        host = _Host(container=None)
        started, created = self._run(host, None, None)
        self.assertFalse(started)
        self.assertEqual(created, [])

    def test_missing_archive_starts_nothing(self):
        pass
        host = _Host(container=None)
        missing = str(self.dir / "нет-такого.zpaq")
        with mock.patch("core.par2_ops.find_par2",
                        return_value="par2.exe"), \
             mock.patch("ui.par2_actions.Par2CreateWorker",
                        side_effect=_FakeWorker):
            started = host._start_par2_worker(
                None, missing, {"enabled": True, "options": {}}
            )
        self.assertFalse(started)

    def test_no_engine_reports_and_starts_nothing(self):
        pass





        host = _Host(container=None)
        with mock.patch("core.par2_ops.find_par2", return_value=None), \
             mock.patch("ui.par2_actions.Par2CreateWorker",
                        side_effect=_FakeWorker):
            started = host._start_par2_worker(
                None, str(self.arch), {"enabled": True, "options": {}}
            )
        self.assertFalse(started)
        self.assertTrue(host.status_messages, "пользователю не сказали")


class TestUnchangedArchiveIsReportedAsSkipped(_TmpCase):
    pass








    def test_core_marks_skip(self):
        pass
        from core import par2_ops

        real_bin = None
        with mock.patch("core.par2_ops.find_par2", return_value="par2.exe"), \
             mock.patch("core.par2_ops.create_parset") as fake_create:
            fake_create.return_value = par2_ops.Par2Result(
                True, par2_ops.STATE_OK, "создан"
            )
            real_bin = "par2.exe"

            res = par2_ops.refresh_par2_set(
                "par2.exe",
                str(self.arch),
                skip_if_unchanged=True,
                unchanged_size=self.arch.stat().st_size,
            )

        self.assertTrue(res.ok)
        self.assertTrue(res.skipped, "пропуск не помечен")
        fake_create.assert_not_called()

    def test_worker_passes_skip_through(self):
        pass
        from workers import par2_worker

        worker = par2_worker.Par2CreateWorker.__new__(
            par2_worker.Par2CreateWorker
        )
        worker._cancel = False
        worker._proc = None
        worker._bin_path = "par2.exe"
        worker._archive_path = str(self.arch)
        worker._options = {}
        worker._unchanged_size = None
        worker._register_proc = lambda p: None
                                                                    
                                                                   
        worker.done = mock.Mock()

        from core import par2_ops

        with mock.patch.object(
            par2_ops, "refresh_par2_set",
            return_value=par2_ops.Par2Result(
                True, par2_ops.STATE_OK, "не изменился",
                recorded_size=123, skipped=True,
            ),
        ):
            worker.run()

        worker.done.emit.assert_called_once()
        result = worker.done.emit.call_args[0][0]
        self.assertTrue(result.get("skipped"), "воркер потерял флаг пропуска")

    def test_ui_says_skipped_not_created(self):
        pass
        host = _Host(container=None)
        host._on_par2_done(
            None,
            {
                "ok": True,
                "cancelled": False,
                "skipped": True,
                "state": "ok",
                "log": "",
                "recorded_size": 4096,
                "archive_path": str(self.arch),
            },
        )
        joined = " ".join(host.status_messages)
        self.assertIn(tr("par2.create_skipped"), joined)


class TestVerifyMessageRouting(_TmpCase):
    pass










    def _note(self, state):
        host = _Host(container=None)
        host._on_par2_verify_done(None, {
            "state": state,
            "log": "",
            "cancelled": False,
            "archive_path": str(self.arch),
        })
        return " ".join(host.status_messages)

    def test_ok_says_verified(self):
        self.assertIn(tr("par2.verify_ok"), self._note("ok"))

    def test_damaged_says_repair_possible(self):
        self.assertIn(tr("par2.verify_damaged"), self._note("damaged"))

    def test_unrepairable_has_its_own_message(self):
        pass





        msg = self._note("unrepairable")
        self.assertIn(tr("par2.verify_unrepairable"), msg)
        self.assertNotIn(tr("par2.verify_damaged"), msg)
        self.assertNotIn(tr("par2.verify_missing"), msg)

    def test_missing_says_no_set(self):
        self.assertIn(tr("par2.verify_missing"), self._note("missing"))

    def test_broken_says_unreadable(self):
        self.assertIn(tr("par2.verify_broken"), self._note("broken"))


class TestRepairRefusesWrongState(_TmpCase):
    pass






    def _start(self, state):
        from core import par2_ops
        from core.par2_ops import par2_main_name

                                                                   
                                                                
                                                                 
        Path(par2_main_name(str(self.arch))).write_bytes(b"PADDING")

        host = _Host(container=None)
        with mock.patch("core.par2_ops.find_par2",
                        return_value="par2.exe"), \
             mock.patch("core.par2_ops.verify_parset") as vf:
            vf.return_value = par2_ops.Par2Result(
                False, state, "log", recorded_size=100
            )
            with mock.patch("ui.par2_actions.QMessageBox") as mb:
                started = host._start_par2_repair(str(self.arch))
        msg = " ".join(host.status_messages)
        asked = mb.question.called
        return started, msg, asked

    def test_refuses_when_not_damaged(self):
        started, msg, asked = self._start("ok")
        self.assertFalse(started)
        self.assertFalse(asked, "задан вопрос там, где восстанавливать нечего")
        self.assertIn(tr("par2.repair_not_needed"), msg)

    def test_refuses_when_unrepairable(self):
        pass






        started, msg, asked = self._start("unrepairable")
        self.assertFalse(started)
        self.assertFalse(asked, "задан вопрос про невозможное восстановление")
        self.assertIn(tr("par2.repair_impossible"), msg)
        self.assertNotIn(tr("par2.repair_not_needed"), msg)


class TestVerifyDialog(_TmpCase):
    pass













    def _host(self):
        return _Host(container=None)

    def _make_set_file(self):
        from core.par2_ops import par2_main_name

        Path(par2_main_name(str(self.arch))).write_bytes(b"P")

    def _start(self, host):
        pass
        self._make_set_file()
        worker = mock.Mock()
        worker.done = mock.Mock()
        worker.finished = mock.Mock()
        worker.cancel_request = mock.Mock()
        with mock.patch("core.par2_ops.find_par2",
                        return_value="par2.exe"), \
             mock.patch("ui.par2_actions.Par2VerifyWorker",
                        return_value=worker):
            host._start_par2_verify(str(self.arch))
        host._workers.append(worker)
        return worker

    def _done(self, host, state, log="All files are correct."):
        pass







        worker = host._par2_verify_worker
        host._on_par2_verify_done(
            None,
            {
                "state": state,
                "log": log,
                "cancelled": False,
                "archive_path": str(self.arch),
            },
            host._par2_verify_dialog,
        )
        if worker is not None and worker in host._workers:
            host._workers.remove(worker)

    def test_dialog_opens(self):
        host = self._host()
        self._start(host)
        dlg = getattr(host, "_par2_verify_dialog", None)
        self.assertIsNotNone(dlg, "окно проверки не создалось")
        self.assertFalse(dlg._finished)

    def test_dialog_shows_running_text(self):
        pass
        host = self._host()
        self._start(host)
        dlg = host._par2_verify_dialog
        self.assertEqual(dlg._current.text().strip(),
                         tr("par2.verify_running").strip())

    def test_dialog_does_not_close_itself(self):
        pass







        host = self._host()
        self._start(host)
        dlg = host._par2_verify_dialog
        self._done(host, "ok")
                                                           
                                                                
                                                                        
                                                          
        self.assertFalse(
            dlg._close_timer.isActive(),
            "окно закрылось бы само — вердикт опять мигнёт и исчезнет",
        )

    def test_meanless_fields_hidden(self):
        pass







        host = self._host()
        self._start(host)
        dlg = host._par2_verify_dialog
        self.assertFalse(dlg._files_label.isVisibleTo(dlg))
        self.assertFalse(dlg._dirs_label.isVisibleTo(dlg))
        self.assertFalse(dlg._size_label.isVisibleTo(dlg))
        self.assertFalse(dlg._speed_label.isVisibleTo(dlg))
        self.assertFalse(dlg._eta_label.isVisibleTo(dlg))
        self.assertTrue(dlg._elapsed_label.isVisibleTo(dlg))

    def test_verdict_not_duplicated(self):
        pass






        host = self._host()
        self._start(host)
        dlg = host._par2_verify_dialog
        worker = host._par2_verify_worker
        host._on_par2_verify_done(
            None,
            {
                "state": "ok",
                "log": "",
                "cancelled": False,
                "recorded_size": 4096,
                "archive_path": str(self.arch),
            },
            dlg,
        )
        if worker in host._workers:
            host._workers.remove(worker)

                                                                 
        self.assertNotIn(dlg._title.text().strip(),
                         dlg._current.text())
                                                         
        self.assertIn(tr("par2.verify_size", size=format_size(4096)),
                      dlg._current.text())

    def test_status_line_empty_without_recorded_size(self):
        pass





        host = self._host()
        self._start(host)
        dlg = host._par2_verify_dialog
        worker = host._par2_verify_worker
        host._on_par2_verify_done(
            None,
            {
                "state": "missing",
                "log": "",
                "cancelled": False,
                "recorded_size": None,
                "archive_path": str(self.arch),
            },
            dlg,
        )
        if worker in host._workers:
            host._workers.remove(worker)
        self.assertEqual(dlg._current.text().strip(), "")

    def test_dialog_survives_until_closed(self):
        pass







        host = self._host()
        worker = self._start(host)
        dlg = host._par2_verify_dialog
        self._done(host, "ok")
        self.assertIs(
            host._par2_verify_dialog, dlg,
            "ссылка на окно отпущена сразу после итога — окно может "
            "быть собрано сборщиком мусора и исчезнуть",
        )

                                                         
                                                                           
        dlg.finished.emit(0)
        self.assertIsNone(
            host._par2_verify_dialog,
            "закрытое окно продолжает висеть ссылкой на хосте",
        )

    def test_release_ignores_other_dialog(self):
        pass






        host = self._host()
        self._start(host)
        old = host._par2_verify_dialog

                                          
        self._start(host)
        second = host._par2_verify_dialog
        self.assertIsNot(second, old)

        host._release_verify_dialog(old)
        self.assertIs(
            host._par2_verify_dialog, second,
            "закрытие старого окна унесло ссылку на новое",
        )

    def test_cancel_kills_process(self):
        pass





        host = self._host()
        worker = self._start(host)
        dlg = host._par2_verify_dialog
        dlg.cancelRequested.emit()
        self.assertTrue(worker.cancel_request.called)

                                                                      
    def test_verdict_for_each_state(self):
        cases = {
            "ok": "par2.verify_ok",
            "damaged": "par2.verify_damaged",
            "unrepairable": "par2.verify_unrepairable",
            "missing": "par2.verify_missing",
            "broken": "par2.verify_broken",
        }
        for state, key in cases.items():
            with self.subTest(state=state):
                host = self._host()
                self._start(host)
                dlg = host._par2_verify_dialog
                self._done(host, state)
                                       
                self.assertIn(
                    tr(key, name=self.arch.name),
                    (dlg._title.text(), dlg._current.text()),
                    f"состояние {state}: вердикт не показан в окне",
                )

    def test_intact_is_marked_ok(self):
        pass





        host = self._host()
        self._start(host)
        dlg = host._par2_verify_dialog
        self._done(host, "ok")
        self.assertEqual(dlg._title.property("state"), "ok")

        host2 = self._host()
        self._start(host2)
        dlg2 = host2._par2_verify_dialog
        self._done(host2, "damaged")
        self.assertEqual(dlg2._title.property("state"), "err")

    def test_engine_log_inside_dialog(self):
        pass
        host = self._host()
        self._start(host)
        dlg = host._par2_verify_dialog
        self._done(host, "ok", log='All files are correct.\nRepair is not '
                                  'required.')
        text = dlg._log.toPlainText()
        self.assertIn("All files are correct", text)

    def test_status_bar_still_gets_message(self):
        pass





        host = self._host()
        self._start(host)
        self._done(host, "damaged")
        self.assertTrue(host.status_messages)
        self.assertIn(tr("par2.verify_damaged", name=self.arch.name),
                      " ".join(host.status_messages))

    def test_done_without_dialog_still_works(self):
        pass





        host = self._host()
        host._on_par2_verify_done(None, {
            "state": "ok", "log": "", "cancelled": False,
            "archive_path": str(self.arch),
        })
        self.assertTrue(host.status_messages)


class _MenuProbe(QWidget):
    pass





    def __init__(self):
        QWidget.__init__(self)
        self.archive_path = None
        self.captured = None

    def _enter_archive(self, p):
        pass

    def _on_create_archive_paths(self, s):
        pass

    def _on_test_archive(self, *a, **k):
        pass

    def _start_par2_repair(self, p):
        pass

    def _start_par2_create(self, p):
        pass

    def _rename_fs_path(self, p):
        pass

    def _delete_fs_path(self, p):
        pass

    def _on_archive_info(self):
        pass

    def _exec_menu(self, menu, pos):
        self.captured = menu


class TestManualSetCreation(_TmpCase):
    pass











    def setUp(self):
        super().setUp()
        self.host = _Host(container=None)
        self.host._par2_create_dialog = None

    def _make_set(self):
        from core.par2_ops import par2_main_name

        Path(par2_main_name(str(self.arch))).write_bytes(b"P")

    def _menu_texts(self):
        pass





        from ui.qt_compat import KIND_ROLE, TCOL, USER_ROLE
        from ui.tree_events import TreeEventsMixin

        class _Item:
            def __init__(self, path, kind):
                self._path, self._kind = path, kind

            def data(self, col, role):
                if col != TCOL:
                    return None
                if role == USER_ROLE:
                    return self._path
                if role == KIND_ROLE:
                    return self._kind
                return None

        captured = {}

        host = _MenuProbe()
        TreeEventsMixin._fs_archive_context_menu(
            host, _Item(str(self.arch), "fs_arc"), None
        )
        captured = getattr(host, "captured", None)
        return [a.text() for a in captured.actions()] if captured else []

                                                                        
    def test_menu_offers_create_without_set(self):
        self.assertIn(tr("par2.create_now"), self._menu_texts())
        self.assertNotIn(tr("par2.repair"), self._menu_texts())

    def test_menu_offers_restore_with_set(self):
        self._make_set()
        self.assertIn(tr("par2.repair"), self._menu_texts())
        self.assertNotIn(tr("par2.create_now"), self._menu_texts())

    def test_menu_offers_recreate_with_set(self):
        pass








        self._make_set()
        self.assertIn(tr("par2.recreate_now"), self._menu_texts())

    def test_menu_offers_restore_and_recreate_together(self):
        pass



        self._make_set()
        texts = self._menu_texts()
        self.assertIn(tr("par2.repair"), texts)
        self.assertIn(tr("par2.recreate_now"), texts)

    def test_menu_without_set_has_no_recreate(self):
        pass
        self.assertNotIn(tr("par2.recreate_now"), self._menu_texts())

                                                                    
    def _start(self, container=None):
        host = _Host(container=container)
        host._par2_create_dialog = None
        worker = mock.Mock()
        worker.done = mock.Mock()
        worker.finished = mock.Mock()
        worker.cancel_request = mock.Mock()
        with mock.patch("core.par2_ops.find_par2",
                        return_value="par2.exe"), \
             mock.patch("ui.par2_actions.Par2CreateWorker",
                        return_value=worker), \
             _set_dialog_patch():
            started = host._start_par2_create(str(self.arch))
        if started:
            host._workers.append(worker)
        return host, worker, started

    def test_starts_and_opens_dialog(self):
        host, worker, started = self._start()
        self.assertTrue(started)
        self.assertIsNotNone(host._par2_create_dialog)
        self.assertEqual(host._par2_create_dialog._current.text().strip(),
                         tr("par2.create_running").strip())

    def test_refuses_when_set_exists(self):
        pass







        self._make_set()
        host, _worker, started = self._start()
        self.assertFalse(started)
        self.assertIn(tr("par2.already_exists"), " ".join(host.status_messages))

    def test_refuses_without_archive(self):
        host = _Host(container=None)
        missing = str(self.dir / "нет.zpaq")
        with mock.patch("core.par2_ops.find_par2",
                        return_value="par2.exe"), \
             mock.patch("ui.par2_actions.Par2CreateWorker"):
            self.assertFalse(host._start_par2_create(missing))

    def test_refuses_without_engine(self):
        with mock.patch("core.par2_ops.find_par2", return_value=None):
            self.assertFalse(self.host._start_par2_create(str(self.arch)))
        self.assertIn(tr("par2.not_found"),
                      " ".join(self.host.status_messages))

    def test_cancel_kills_process(self):
        pass
        host, worker, started = self._start()
        self.assertTrue(started)
        host._par2_create_dialog.cancelRequested.emit()
        self.assertTrue(worker.cancel_request.called)

    def test_dialog_survives_until_closed(self):
        pass
        host, _worker, started = self._start()
        self.assertTrue(started)
        dlg = host._par2_create_dialog
        host._on_par2_done(None, {
            "ok": True, "cancelled": False, "skipped": False,
            "log": "", "recorded_size": 4096,
            "archive_path": str(self.arch),
        }, dlg)
        self.assertIs(host._par2_create_dialog, dlg)
        dlg.finished.emit(0)
        self.assertIsNone(host._par2_create_dialog)

                                                                       
    def test_options_from_job(self):
        pass





        container = {
            "works": [{
                "id": "w1",
                "dest": str(self.arch),
                "jobs": [{
                    "id": "j1",
                    "par2_enabled": True,
                    "par2_options": {"redundancy": 17},
                }],
            }],
        }
        host = _Host(container=container)
        ctx, options, _size = host._par2_job_for(str(self.arch))
        self.assertEqual(options, {"redundancy": 17})
        self.assertEqual(ctx, {"work_id": "w1", "job_id": "j1"})

    def test_options_default_without_container(self):
        pass





        host = _Host(container=None)
        ctx, options, _size = host._par2_job_for(str(self.arch))
        self.assertIsNone(ctx)
        self.assertEqual(options, {})

        from core.par2_ops import default_options

        self.assertEqual(default_options()["redundancy"], 5)
        self.assertIsNone(default_options()["block_size"])

    def test_path_match_case_insensitive(self):
        pass






        container = {
            "works": [{
                "id": "w1",
                "dest": str(self.arch).upper(),
                "jobs": [{
                    "id": "j1",
                    "par2_enabled": True,
                    "par2_options": {"redundancy": 3},
                }],
            }],
        }
        host = _Host(container=container)
        _ctx, options, _size = host._par2_job_for(str(self.arch))
        self.assertEqual(options, {"redundancy": 3})

                                                                  
    def test_verdicts(self):
        pass
        cases = {
            (True, False, False): ("par2.created_ok", True),
            (True, True, False): ("par2.create_skipped", False),
            (False, False, True): ("par2.cancelled", False),
            (False, False, False): ("par2.create_failed", False),
        }
        for (ok, skipped, cancelled), (key, want_ok) in cases.items():
            with self.subTest(ok=ok, skipped=skipped, cancelled=cancelled):
                host, _w, started = self._start()
                self.assertTrue(started)
                dlg = host._par2_create_dialog
                host._on_par2_done(None, {
                    "ok": ok, "cancelled": cancelled, "skipped": skipped,
                    "log": "строка движка", "recorded_size": 4096,
                    "archive_path": str(self.arch),
                }, dlg)
                self.assertEqual(dlg._title.text().strip(),
                                 tr(key).strip())
                self.assertEqual(dlg._title.property("state"),
                                 "ok" if want_ok else "err")


class TestTopMenuPar2(_TmpCase):
    pass















    def setUp(self):
        super().setUp()
        from PySide6.QtGui import QAction

        self.host = _Host(container=None)
        self.host.archive_path = None
                                                                  
                                                                     
                                                                        
                                  
        self.host._par2_menu_create_action = QAction("create")
        self.host._par2_menu_verify_action = QAction("verify")
        self.host._par2_menu_repair_action = QAction("repair")

    def _enabled(self):
        host = self.host
        host._refresh_par2_menu()
        return tuple(
            a.isEnabled()
            for a in (
                host._par2_menu_create_action,
                host._par2_menu_verify_action,
                host._par2_menu_repair_action,
            )
        )

    def test_no_archive_enables_all(self):
        self.host.archive_path = None
        self.assertEqual(self._enabled(), (True, True, True))

    def test_archive_without_set_enables_create_only(self):
        self.host.archive_path = str(self.arch)
        self.assertEqual(self._enabled(), (True, False, False))

    def test_archive_with_set_enables_verify_and_repair(self):
        pass







        from core.par2_ops import par2_main_name

        Path(par2_main_name(str(self.arch))).write_bytes(b"P")
        self.host.archive_path = str(self.arch)
        self.assertEqual(self._enabled(), (True, True, True))

    def test_menu_uses_current_archive(self):
        pass





        self.host.archive_path = str(self.arch)
        with mock.patch.object(
            self.host, "_start_par2_create"
        ) as start:
            self.host._par2_menu_create()
        _assert_create_called_for(start, str(self.arch))

    def test_menu_asks_when_no_archive(self):
        pass
        self.host.archive_path = None
        with mock.patch.object(
            self.host, "_par2_target_from_menu", return_value=str(self.arch)
        ) as pick, mock.patch.object(self.host, "_start_par2_create") as start:
            self.host._par2_menu_create()
        self.assertTrue(pick.called)
        _assert_create_called_for(start, str(self.arch))

    def test_menu_asks_for_recreate_when_set_exists(self):
        pass






        from core.par2_ops import par2_main_name

        Path(par2_main_name(str(self.arch))).write_bytes(b"P")
        self.host.archive_path = str(self.arch)
        with mock.patch.object(self.host, "_start_par2_create") as start:
            self.host._par2_menu_create()
        _assert_create_called_for(start, str(self.arch), recreate=True)

    def test_menu_cancelled_asks_nothing(self):
        pass
        self.host.archive_path = None
        with mock.patch.object(
            self.host, "_par2_target_from_menu", return_value=""
        ), mock.patch.object(self.host, "_start_par2_create") as start, \
             mock.patch.object(self.host, "_start_par2_verify"), \
             mock.patch.object(self.host, "_start_par2_repair"):
            self.host._par2_menu_create()
            self.host._par2_menu_verify()
            self.host._par2_menu_repair()
        start.assert_not_called()

    def test_refresh_tolerates_missing_actions(self):
        pass






        host = _Host(container=None)
        host.archive_path = str(self.arch)
        host._refresh_par2_menu()


class _FakeIndex:
    def __init__(self, row):
        self._row = row

    def row(self):
        return self._row


class _FakeItem:
    pass







    def __init__(self, kind, payload):
        self._kind = kind
        self._payload = payload

    def data(self, role):
        from ui.qt_compat import KIND_ROLE, USER_ROLE

        if role == USER_ROLE:
            return self._payload
        if role == KIND_ROLE:
            return self._kind
        return None


class _FakeTable:
    pass






    def __init__(self, rows):
        self._rows = rows

    def selectedIndexes(self):
        return [_FakeIndex(r) for r, _item in self._rows]

    def item(self, row, col):
        for r, it in self._rows:
            if r == row:
                return it
        return None


class TestTargetResolution(_TmpCase):
    pass











    def _host_with_selection(self, kind, payload):
        host = _Host(container=None)
        host.archive_path = None
                                                                 
                                                                        
                                
        item = _FakeItem(kind, payload)
        host.table = _FakeTable([(0, item)])
        return host

    def test_selected_archive_wins(self):
        pass
        from ui.qt_compat import K_FS_ARC

        host = self._host_with_selection(K_FS_ARC, str(self.arch))
        host.archive_path = str(self.dir / "другой.zpaq")
        self.assertEqual(host._par2_current_target(), str(self.arch))

    def test_selection_used_when_nothing_open(self):
        pass




        from ui.qt_compat import K_FS_ARC

        host = self._host_with_selection(K_FS_ARC, str(self.arch))
        host.archive_path = None
        self.assertEqual(host._par2_current_target(), str(self.arch))

    def test_menu_create_uses_selection_without_asking(self):
        from ui.qt_compat import K_FS_ARC

        host = self._host_with_selection(K_FS_ARC, str(self.arch))
        with mock.patch(
            "PySide6.QtWidgets.QFileDialog.getOpenFileName"
        ) as dlg, mock.patch.object(host, "_start_par2_create") as start:
            host._par2_menu_create()
        _assert_create_called_for(start, str(self.arch))
        self.assertFalse(
            dlg.called,
            "диалог выбора файла открылся, хотя человек уже указал "
            "архив выделением",
        )

    def test_non_archive_selection_falls_back(self):
        pass
        host = self._host_with_selection("что-то другое", str(self.dir))
        host.archive_path = None
        self.assertEqual(host._par2_current_target(), "")

    def test_open_archive_used_without_selection(self):
        pass
        host = _Host(container=None)
        host.archive_path = str(self.arch)
        host.table = _FakeTable([])
        self.assertEqual(host._par2_current_target(), str(self.arch))

    def test_menu_state_follows_selection(self):
        pass





        from PySide6.QtGui import QAction
        from ui.qt_compat import K_FS_ARC

        host = self._host_with_selection(K_FS_ARC, str(self.arch))
        host._par2_menu_create_action = QAction("c")
        host._par2_menu_verify_action = QAction("v")
        host._par2_menu_repair_action = QAction("r")

        host._refresh_par2_menu()
                                                 
        self.assertTrue(host._par2_menu_create_action.isEnabled())
        self.assertFalse(host._par2_menu_verify_action.isEnabled())

        from core.par2_ops import par2_main_name

        Path(par2_main_name(str(self.arch))).write_bytes(b"P")
        host._refresh_par2_menu()
                                                                      
                                                               
                                                                 
                                  
        self.assertTrue(host._par2_menu_create_action.isEnabled())
        self.assertEqual(host._par2_menu_create_action.text(),
                         tr("par2.recreate_now"))
        self.assertTrue(host._par2_menu_verify_action.isEnabled())
        self.assertTrue(host._par2_menu_repair_action.isEnabled())

    def test_create_label_says_create_without_set(self):
        pass
        from PySide6.QtGui import QAction

        host = _Host(container=None)
        host.archive_path = str(self.arch)
        host._par2_menu_create_action = QAction("c")
        host._par2_menu_verify_action = QAction("v")
        host._par2_menu_repair_action = QAction("r")
        host._refresh_par2_menu()
        self.assertEqual(host._par2_menu_create_action.text(),
                         tr("par2.create_now"))

    def test_missing_widgets_tolerated(self):
        pass
        host = _Host(container=None)
        host.archive_path = ""
        self.assertEqual(host._par2_current_target(), "")


class _StubSetDialog:
    pass







                                                                   
    chosen = None
                                   
    seen_prefill = None
                                          
    result = None

    def __init__(self, archive_name="", options=None, parent=None):
        type(self).seen_prefill = dict(options or {})
        self.archive_name = archive_name
        self.deleted = False

    def exec(self):
        return QDialog.Accepted if _StubSetDialog.result is None \
            else _StubSetDialog.result

    def options(self):
        if _StubSetDialog.chosen is not None:
            return dict(_StubSetDialog.chosen)
        return dict(type(self).seen_prefill)

    def deleteLater(self):
        self.deleted = True


def _set_dialog_patch(**attrs):
    pass
    for key, value in attrs.items():
        setattr(_StubSetDialog, key, value)
    return mock.patch("ui.par2_actions.Par2SetDialog", _StubSetDialog)


class _StubBox:
    pass








    Yes = QMessageBox.Yes
    No = QMessageBox.No
                                                                
                                                                      
                                              
    answer = QMessageBox.Yes
    last_text = ""

    @staticmethod
    def question(*a, **k):
                                                                       
                                                      
        _StubBox.last_text = (str(a[2]) if len(a) > 2
                              else str(k.get("text", "")))
        return _StubBox.answer


class TestStaleSetHonesty(_TmpCase):
    pass













    def setUp(self):
        super().setUp()
                                                                       
                                                                       
                                                              
        self.arch.write_bytes(b"Z" * 20000)

    def _verdict(self, recorded):
        pass
        from core.par2_ops import STATE_DAMAGED

        host = _Host(container=None)
        host._par2_verify_dialog = None
        with mock.patch("ui.par2_verify_dialog.Par2VerifyDialog") as dlg_cls, \
             mock.patch("PySide6.QtWidgets.QMessageBox") as box:
                                                                    
                                                                   
                                                                  
            dlg = mock.Mock()
            dlg_cls.return_value = dlg
            host._start_par2_verify(str(self.arch))
            host._on_par2_verify_done(None, {
                "state": STATE_DAMAGED,
                "log": "",
                "cancelled": False,
                "archive_path": str(self.arch),
                "recorded_size": recorded,
            }, dlg)
        return dlg, " ".join(host.status_messages)

    def test_shrank_file_reports_stale_set(self):
        pass





        actual = self.arch.stat().st_size
        dlg, _note = self._verdict(actual + 5000)
        title = dlg.finish_verdict.call_args[0][1]
        self.assertIn("устарел", title)

    def test_grew_file_reports_stale_set(self):
        dlg, _note = self._verdict(self.arch.stat().st_size - 5000)
        title = dlg.finish_verdict.call_args[0][1]
        self.assertIn("устарел", title)

    def test_same_size_reports_damage(self):
        pass






        dlg, _note = self._verdict(self.arch.stat().st_size)
        title = dlg.finish_verdict.call_args[0][1]
        self.assertEqual(title, tr("par2.verify_damaged"))

    def test_stale_message_has_real_numbers(self):
        pass
        actual = self.arch.stat().st_size
        dlg, _note = self._verdict(actual + 5000)
        title = dlg.finish_verdict.call_args[0][1]
        self.assertNotIn("{", title, f"в вердикте остались плейсхолдеры: "
                                     f"{title!r}")
        self.assertIn(str(actual + 5000), title)

    def test_status_bar_says_the_same_as_window(self):
        pass





        actual = self.arch.stat().st_size
        _dlg, note = self._verdict(actual + 5000)
        self.assertIn("устарел", note)
        self.assertNotIn(tr("par2.verify_damaged"), note)

    def test_unknown_recorded_size_is_not_stale(self):
        pass




        dlg, _note = self._verdict(None)
        title = dlg.finish_verdict.call_args[0][1]
        self.assertEqual(title, tr("par2.verify_damaged"))


class TestRepairRefusesStaleSet(_TmpCase):
    pass








    def setUp(self):
        super().setUp()
        from core.par2_ops import par2_main_name

        Path(par2_main_name(str(self.arch))).write_bytes(b"P")
        self.host = _Host(container=None)
        self.host._par2_repair_dialog = None

    def _start(self, recorded, actual):
        from core import par2_ops

        worker = mock.Mock()
        with mock.patch("core.par2_ops.find_par2", return_value="par2.exe"), \
             mock.patch("core.par2_ops.verify_parset") as vf, \
             mock.patch("ui.par2_actions.Par2RepairWorker",
                        return_value=worker), \
             mock.patch("ui.par2_actions.QMessageBox", _StubBox), \
             mock.patch("core.par2_ops.os.path.getsize", return_value=actual):
            vf.return_value = par2_ops.Par2Result(
                False, par2_ops.STATE_DAMAGED, "log",
                recorded_size=recorded,
            )
            _StubBox.last_text = ""
            started = self.host._start_par2_repair(str(self.arch))
        return started

    def test_blocked_when_file_shrank(self):
        pass
        started = self._start(10_000, 4_096)
        self.assertFalse(started)
        self.assertIn("устарел", self.host._par2_repair_dialog._title.text())

    def test_blocked_when_file_grew(self):
        started = self._start(4_096, 10_000)
        self.assertFalse(started)

    def test_blocked_without_asking_anything(self):
        pass



        self._start(10_000, 4_096)
        self.assertEqual(_StubBox.last_text, "")

    def test_allowed_when_sizes_match(self):
        pass



        size = self.arch.stat().st_size
        self.assertTrue(self._start(size, size))

    def test_same_size_question_says_it_may_be_another_version(self):
        pass






        size = self.arch.stat().st_size
        self._start(size, size)
        self.assertIn(tr("par2.repair_confirm_same_size",
                         name=self.arch.name, actual=size, recorded=size),
                      _StubBox.last_text)

    def test_mismatched_sizes_never_reach_the_question(self):
        pass
        self._start(10_000, 4_096)
        self.assertEqual(_StubBox.last_text, "")


class TestRepairDialog(_TmpCase):
    pass








    def setUp(self):
        super().setUp()
        from core.par2_ops import par2_main_name

        Path(par2_main_name(str(self.arch))).write_bytes(b"P")
        self.host = _Host(container=None)
        self.host._par2_repair_dialog = None

    def _start(self, verify_state, recorded=4096, actual=None, answer=True):
        from core import par2_ops

        host = self.host
        if actual is None:
            actual = self.arch.stat().st_size
        worker = mock.Mock()
        worker.done = mock.Mock()
        worker.finished = mock.Mock()
        worker.cancel_request = mock.Mock()

        with mock.patch("core.par2_ops.find_par2",
                        return_value="par2.exe"), \
             mock.patch("core.par2_ops.verify_parset") as vf, \
             mock.patch("ui.par2_actions.Par2RepairWorker",
                        return_value=worker), \
             mock.patch("ui.par2_actions.QMessageBox", _StubBox), \
             mock.patch("core.par2_ops.os.path.getsize",
                        return_value=actual):
            vf.return_value = par2_ops.Par2Result(
                False, verify_state, "log", recorded_size=recorded
            )
            started = host._start_par2_repair(str(self.arch))
        if started:
            host._workers.append(worker)
        return started, worker

    def test_window_is_shown_by_construction(self):
        pass









        from ui.par2_verify_dialog import Par2RepairDialog

        dlg = Par2RepairDialog("backup.zpaq")
        self.assertFalse(dlg.isHidden(), "окно создано, но не показано")
        dlg.close()

    def test_window_opens_even_when_refusing(self):
        pass






        self._start("ok")
        self.assertIsNotNone(self.host._par2_repair_dialog)

    def test_intact_archive_says_not_needed(self):
        self._start("ok")
        dlg = self.host._par2_repair_dialog
        self.assertEqual(dlg._title.text().strip(),
                         tr("par2.repair_not_needed").strip())

    def test_not_needed_is_not_painted_as_error(self):
        pass





        self._start("ok")
        dlg = self.host._par2_repair_dialog
        self.assertEqual(dlg._title.property("state"), "ok")

    def test_real_problem_is_painted_as_error(self):
        pass
        self._start("unrepairable")
        dlg = self.host._par2_repair_dialog
        self.assertEqual(dlg._title.property("state"), "err")

    def test_no_confirmation_asked_when_nothing_to_do(self):
        pass
        with mock.patch("ui.par2_actions.QMessageBox") as mb:
            with mock.patch("core.par2_ops.verify_parset") as vf, \
                 mock.patch("core.par2_ops.find_par2",
                            return_value="par2.exe"):
                from core import par2_ops

                vf.return_value = par2_ops.Par2Result(
                    True, par2_ops.STATE_OK, "", recorded_size=1
                )
                self.host._start_par2_repair(str(self.arch))
        self.assertFalse(mb.question.called)

    def test_running_text_after_confirmation(self):
        pass






        self._start("damaged")
        dlg = self.host._par2_repair_dialog
        self.assertEqual(dlg._current.text().strip(),
                         tr("par2.repair_running").strip())

    def test_ok_repair_refreshes_listing_index(self):
        pass






        self._start("damaged")
        self.host._refresh_index_after_create = mock.Mock()
        self.host._on_par2_repair_done({
            "ok": True, "cancelled": False,
            "log": "Repair complete.",
            "archive_path": str(self.arch),
        })
        self.host._refresh_index_after_create.assert_called_once_with(
            str(self.arch))

    def test_cancelled_repair_does_not_refresh(self):
        pass

        self._start("damaged")
        self.host._refresh_index_after_create = mock.Mock()
        self.host._on_par2_repair_done({
            "ok": False, "cancelled": True,
            "log": "",
            "archive_path": str(self.arch),
        })
        self.host._refresh_index_after_create.assert_not_called()

    def test_cancel_kills_process(self):
        self._start("damaged")
        worker = self.host._par2_repair_worker
        self.host._par2_repair_dialog.cancelRequested.emit()
        self.assertTrue(worker.cancel_request.called)

    def test_verdict_shown_after_repair(self):
        self._start("damaged")
        worker = self.host._par2_repair_worker
        dlg = self.host._par2_repair_dialog
        self.host._on_par2_repair_done({
            "ok": True, "cancelled": False, "log": "Repair complete.",
            "archive_path": str(self.arch),
        }, dlg)
        if worker in self.host._workers:
            self.host._workers.remove(worker)
        self.assertEqual(dlg._title.text().strip(),
                         tr("par2.repair_ok").strip())
        self.assertIn("Repair complete", dlg._log.toPlainText())

    def test_failed_repair_is_error(self):
        self._start("damaged")
        worker = self.host._par2_repair_worker
        dlg = self.host._par2_repair_dialog
        self.host._on_par2_repair_done({
            "ok": False, "cancelled": False, "log": "Repair is not possible.",
            "archive_path": str(self.arch),
        }, dlg)
        if worker in self.host._workers:
            self.host._workers.remove(worker)
        self.assertEqual(dlg._title.property("state"), "err")

    def test_dialog_survives_until_closed(self):
        pass
        self._start("damaged")
        dlg = self.host._par2_repair_dialog
        self.assertIs(self.host._par2_repair_dialog, dlg)
        dlg.finished.emit(0)
        self.assertIsNone(self.host._par2_repair_dialog)

    def test_stale_set_refuses_without_question(self):
        pass
        self._start("damaged", recorded=100, actual=99999)
        dlg = self.host._par2_repair_dialog
        self.assertIn(tr("par2.repair_stale", actual=99999, recorded=100),
                      dlg._title.text())


class TestRecreateSet(_TmpCase):
    pass










    def setUp(self):
        super().setUp()
        from core.par2_ops import par2_main_name

                                                                 
                                           
        main = Path(par2_main_name(str(self.arch)))
        main.write_bytes(b"P")
        main.with_suffix(".vol000+01.par2").write_bytes(b"V")
        self.main_set = main
        self.vol = main.with_suffix(".vol000+01.par2")

    def _run(self, answer=True, remove_fails=False):
        host = _Host(container=None)
        host._par2_create_dialog = None
        worker = mock.Mock()
        worker.done = mock.Mock()
        worker.finished = mock.Mock()
        worker.cancel_request = mock.Mock()

        _StubBox.answer = QMessageBox.Yes if answer else QMessageBox.No
        try:
            with mock.patch("core.par2_ops.find_par2",
                            return_value="par2.exe"), \
                 mock.patch("ui.par2_actions.Par2CreateWorker",
                            return_value=worker), \
                 mock.patch("ui.par2_actions.QMessageBox", _StubBox), \
                 _set_dialog_patch():
                started = host._start_par2_create(str(self.arch),
                                                   recreate=True)
        finally:
            _StubBox.answer = QMessageBox.Yes
        if started:
            host._workers.append(worker)
        return host, worker, started

    def test_recreate_creates_set(self):
        pass
        _host, _worker, started = self._run()
        self.assertTrue(started)

    def test_recreate_asks_before_deleting_anything(self):
        pass





        host = _Host(container=None)
        host._par2_create_dialog = None
        _StubBox.answer = QMessageBox.No
        try:
            with mock.patch("core.par2_ops.find_par2",
                            return_value="par2.exe"), \
                 mock.patch("ui.par2_actions.Par2CreateWorker"), \
                 mock.patch("ui.par2_actions.QMessageBox", _StubBox):
                host._start_par2_create(str(self.arch), recreate=True)
        finally:
            _StubBox.answer = QMessageBox.Yes
        self.assertNotEqual(
            _StubBox.last_text, "",
            "пересоздание без вопроса не делается",
        )
        self.assertTrue(self.main_set.exists(),
                        "набор удалили, хотя человек отказался")

    def test_declined_keeps_old_set(self):
        _host, _worker, started = self._run(answer=False)
        self.assertFalse(started)
        self.assertTrue(self.main_set.exists())
        self.assertTrue(self.vol.exists())

    def test_old_set_removed_before_creating(self):
        pass






        self._run()
        self.assertFalse(self.main_set.exists())
        self.assertFalse(self.vol.exists())

    def test_blocked_when_old_set_cannot_be_removed(self):
        pass





        host = _Host(container=None)
        host._par2_create_dialog = None
        worker = mock.Mock()
        with mock.patch("core.par2_ops.find_par2",
                        return_value="par2.exe"), \
             mock.patch("ui.par2_actions.Par2CreateWorker",
                        return_value=worker), \
             mock.patch("ui.par2_actions.QMessageBox", _StubBox), \
             mock.patch.object(_Host, "_remove_par2_set",
                               side_effect=OSError("занято другим "
                                                   "процессом")):
            started = host._start_par2_create(str(self.arch), recreate=True)
        self.assertFalse(started)
        self.assertIn(tr("par2.recreate_blocked", error="занято другим "
                                                        "процессом"),
                      " ".join(host.status_messages))
        self.assertIsNone(host._par2_create_dialog,
                          "окно создания открылось, хотя пересоздание "
                          "заблокировано")

    def test_create_flag_off_still_refuses(self):
        pass





        host = _Host(container=None)
        with mock.patch("core.par2_ops.find_par2",
                        return_value="par2.exe"), \
             mock.patch("ui.par2_actions.Par2CreateWorker"):
            self.assertFalse(host._start_par2_create(str(self.arch)))


class TestPar2SettingsWithoutContext(_TmpCase):
    pass

    def test_none_context_returns_empty(self):
        host = _Host(container=_container_with(par2_enabled=True))
        self.assertEqual(host._par2_settings(None), (False, {}, None))

    def test_missing_container_returns_empty(self):
        host = _Host(container=None)
        self.assertEqual(host._par2_settings(None), (False, {}, None))

    def test_context_reads_container(self):
        host = _Host(container=_container_with(
            par2_enabled=True, options={"redundancy": 7}
        ))
        enabled, options, size = host._par2_settings(
            {"work_id": "w1", "job_id": "j1"}
        )
        self.assertTrue(enabled)
        self.assertEqual(options, {"redundancy": 7})
        self.assertEqual(size, 4242)


if __name__ == "__main__":
    unittest.main()
