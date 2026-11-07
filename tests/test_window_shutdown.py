
















from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QThread              
from PySide6.QtGui import QCloseEvent              
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget              

from ui.window_shell import WindowShellMixin              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))



def _close_event() -> QCloseEvent:
    pass
    ev = QCloseEvent()
    ev.accept()
    return ev


def _wait_until_stopped(worker, timeout: float = 10.0) -> bool:
    pass
    deadline = time.monotonic() + timeout
    while worker.isRunning() and time.monotonic() < deadline:
        _APP.processEvents()
        time.sleep(0.02)
    return not worker.isRunning()


class _Worker(QThread):
    pass








    def __init__(self, lifetime_ms: int = 5000, honour_cancel: bool = True):
        super().__init__(None)
        self._lifetime = lifetime_ms
        self._honour = honour_cancel
        self.cancel_called = False
        self.stopped_by_cancel = False

    def cancel_request(self):
        self.cancel_called = True

    def run(self):
                                                             
        deadline = time.monotonic() + self._lifetime / 1000.0
        while time.monotonic() < deadline:
            if self.isInterruptionRequested():
                return
            if self.cancel_called and self._honour:
                self.stopped_by_cancel = True
                return
            time.sleep(0.01)


class _PlainBase(QWidget):
    pass

    def closeEvent(self, ev):
        pass


class _Window(WindowShellMixin, _PlainBase):
    pass







                                                        
    zpaq_bin = ""
    latest_only_action = None
    mode = "fs"
    fs_path = None
    last_extract_dir = None

    def __init__(self, workers=None):
        QWidget.__init__(self)
        self._workers = list(workers or [])


class _Dialogs:
    pass

    def __init__(self, answer):
        self.answer = answer
        self.calls = []
        self._q = QMessageBox.question
        self._w = QMessageBox.warning

    def __enter__(self):
        def patched(parent, title, text, buttons=None, *a, **k):
            self.calls.append((title, text))
            return self.answer

        QMessageBox.question = patched
        QMessageBox.warning = patched
        return self

    def __exit__(self, *exc):
        QMessageBox.question = self._q
        QMessageBox.warning = self._w
        return False


class TestShutdownWorkers(unittest.TestCase):
    def test_stops_worker_and_reports_none_stuck(self):
        w = _Worker(lifetime_ms=60000)
        w.start()
        time.sleep(0.1)

        stuck = _Window([w])._shutdown_workers([w], timeout_ms=5000)

        self.assertEqual(stuck, [], "уважающий отмену воркер должен завершиться")
        self.assertTrue(w.cancel_called, "cancel_request() не вызван")
        self.assertTrue(w.stopped_by_cancel, "воркер должен выйти по отмене")

    def test_stubborn_worker_is_reported_stuck(self):
        pass
        w = _Worker(lifetime_ms=60000, honour_cancel=False)
        w.start()
        time.sleep(0.1)

        t0 = time.monotonic()
        stuck = _Window([w])._shutdown_workers([w], timeout_ms=300)
        waited = time.monotonic() - t0

        self.assertEqual(stuck, [w], "застрявший воркер должен быть в списке")
        self.assertTrue(w.cancel_called, "cancel_request() всё равно вызывается")
        self.assertLess(waited, 5.0, "ожидание должно быть ограничено таймаутом")

        w.requestInterruption()
        self.assertTrue(_wait_until_stopped(w), "тестовый поток должен завершиться")

    def test_stuck_workers_stay_in_list(self):
        w = _Worker(lifetime_ms=60000, honour_cancel=False)
        w.start()
        time.sleep(0.1)

        win = _Window([w])
        win._shutdown_workers([w], timeout_ms=200)
        self.assertIn(w, win._workers, "застрявший воркер не должен теряться")

        w.requestInterruption()
        _wait_until_stopped(w)

    def test_finished_worker_is_removed_from_list(self):
        w = _Worker(lifetime_ms=50)
        w.start()
        self.assertTrue(_wait_until_stopped(w))

        win = _Window([w])
        win._shutdown_workers([w], timeout_ms=2000)
        self.assertNotIn(w, win._workers, "завершившийся воркер должен уйти из списка")

    def test_running_workers_detected(self):
        w = _Worker(lifetime_ms=3000)
        w.start()
        time.sleep(0.1)
        self.assertEqual(_Window([w])._running_workers(), [w])
        w.requestInterruption()
        _wait_until_stopped(w)

    def test_no_workers_means_nothing_running(self):
        self.assertEqual(_Window([])._running_workers(), [])


class _DummyCfg:
    pass

    zpaq_path = ""
    latest_only = False
    last_fs_path = ""
    last_extract_dir = ""
    window_geometry = None
    window_maximized = False
    right_sort_column = None
    right_sort_desc = False


class _ConfigGuard:
    pass

    def __init__(self):
        self.saved = []
        self._load = None
        self._save = None

    def __enter__(self):
        import ui.window_shell as ws

        self._load = ws._load_cfg
        self._save = ws._save_cfg
        ws._load_cfg = lambda *a, **k: _DummyCfg()
        ws._save_cfg = lambda cfg: self.saved.append(cfg)
        return self

    def __exit__(self, *exc):
        import ui.window_shell as ws

        ws._load_cfg = self._load
        ws._save_cfg = self._save
        return False


class TestCloseEventDecision(unittest.TestCase):
    pass




    def setUp(self):
        self._cfg = _ConfigGuard()
        self._cfg.__enter__()

    def tearDown(self):
        self._cfg.__exit__()

    def test_close_is_ignored_when_user_says_no(self):
        w = _Worker(lifetime_ms=5000)
        w.start()
        time.sleep(0.1)

        with _Dialogs(QMessageBox.StandardButton.No) as dlg:
            ev = _close_event()
            _Window([w]).closeEvent(ev)

        self.assertFalse(ev.isAccepted(), "закрытие должно быть отменено")
        self.assertFalse(w.cancel_called, "отмена операций не запрашивалась")
        self.assertTrue(w.isRunning(), "воркер не должен быть тронут")
        self.assertEqual(len(dlg.calls), 1, "пользователю должен быть задан вопрос")

        w.requestInterruption()
        _wait_until_stopped(w)

    def test_close_is_ignored_when_worker_stuck(self):
        pass
        w = _Worker(lifetime_ms=60000, honour_cancel=False)
        w.start()
        time.sleep(0.1)

        with _Dialogs(QMessageBox.StandardButton.Yes) as dlg:
            ev = _close_event()
            _Window([w]).closeEvent(ev)

        self.assertFalse(ev.isAccepted(), "окно должно остаться открытым")
        self.assertTrue(w.cancel_called, "отмена должна быть запрошена")
        self.assertEqual(len(dlg.calls), 2, "нужно предупреждение о зависшем потоке")

        w.requestInterruption()
        _wait_until_stopped(w)

    def test_close_proceeds_when_no_workers(self):
        with _Dialogs(QMessageBox.StandardButton.No) as dlg:
            ev = _close_event()
            _Window([]).closeEvent(ev)

        self.assertTrue(ev.isAccepted(), "при отсутствии операций закрытие должно идти")
        self.assertEqual(dlg.calls, [], "спрашивать не о чем")

    def test_close_proceeds_after_successful_stop(self):
        w = _Worker(lifetime_ms=60000)
        w.start()
        time.sleep(0.1)

        with _Dialogs(QMessageBox.StandardButton.Yes):
            ev = _close_event()
            _Window([w]).closeEvent(ev)

        self.assertTrue(ev.isAccepted(), "операция остановлена — закрываемся")
        self.assertTrue(w.cancel_called)
        self.assertFalse(w.isRunning())


if __name__ == "__main__":
    unittest.main()
