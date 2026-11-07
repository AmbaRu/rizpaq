







from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication              

from ui.worker_launch import WorkerLaunchMixin              
from workers import (              
    ExtractFileWorker,
    ExtractFolderBatchWorker,
    ExtractFolderWorker,
    ZpaqWorker,
)
from workers.universal_worker import (              
    UniversalExtractWorker,
    UniversalListWorker,
)

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))



class _FakeStatusBar:
    def __init__(self):
        self.messages: list = []

    def showMessage(self, text, *args, **kwargs):                         
        self.messages.append(text)


class _Harness(WorkerLaunchMixin):
    pass

    def __init__(self, workers):
        self._workers = list(workers)
        self._status = _FakeStatusBar()

    def statusBar(self):                         
        return self._status


class _KeyRecorder:
    pass








    def __init__(self):
        self.keys = []
        self._orig = None

    def __enter__(self):
        import ui.worker_launch as wl

        self._orig = wl.tr
        wl.tr = lambda key, *a, **k: (self.keys.append(key), key)[1]
        return self

    def __exit__(self, *exc):
        import ui.worker_launch as wl

        wl.tr = self._orig
        return False


def _make(cls, *args, **kwargs):
    pass
    return cls(*args, **kwargs)


class TestCancelLongOperations(unittest.TestCase):
    pass

                                                                        
    def test_universal_extract_worker_is_cancelled(self):
        pass


        worker = _make(
            UniversalExtractWorker, "7z.exe", "C:/a.zip", "C:/dest"
        )
        self.assertFalse(worker._cancel, "изначально отмена не выставлена")

        _Harness([worker])._cancel_long_operations()

        self.assertTrue(worker._cancel, "UniversalExtractWorker не отменён")

    def test_all_known_cancellable_workers_are_cancelled(self):
        workers = [
            _make(ExtractFileWorker, "zpaq", "C:/a.zpaq", None, "f.txt", 1, "C:/d"),
            _make(
                ExtractFolderBatchWorker, "zpaq", "C:/a.zpaq", None, "p/", 1, "C:/d"
            ),
            _make(ExtractFolderWorker, "zpaq", "C:/a.zpaq", None, [], Path("C:/d")),
            _make(ZpaqWorker, "test", ["zpaq", "t", "C:/a.zpaq"]),
            _make(UniversalExtractWorker, "7z.exe", "C:/a.rar", "C:/dest"),
        ]
        _Harness(workers)._cancel_long_operations()

        for w in workers:
            with self.subTest(worker=type(w).__name__):
                self.assertTrue(w._cancel, f"{type(w).__name__} не отменён")

    def test_non_cancellable_worker_is_skipped(self):
        pass



        worker = _make(UniversalListWorker, "7z.exe", "C:/a.zip", None)
        self.assertFalse(
            hasattr(worker, "cancel_request"),
            "предположение теста нарушено: воркер не должен иметь cancel_request",
        )

        harness = _Harness([worker])
        with _KeyRecorder() as rec:
            harness._cancel_long_operations()                     

                                                                                
        self.assertIn("status.cancel_none", rec.keys)

    def test_mixed_list_cancels_only_capable(self):
        capable = _make(UniversalExtractWorker, "7z.exe", "C:/a.zip", "C:/d")
        incapable = _make(UniversalListWorker, "7z.exe", "C:/b.zip", None)

        harness = _Harness([capable, incapable])
        with _KeyRecorder() as rec:
            harness._cancel_long_operations()

        self.assertTrue(capable._cancel)
        self.assertIn("status.cancel_requested", rec.keys)

    def test_empty_list_is_safe(self):
        harness = _Harness([])
        harness._cancel_long_operations()                     
        self.assertEqual(len(harness._status.messages), 1)

    def test_duck_typing_picks_up_new_workers(self):
        pass



        from PySide6.QtCore import QThread

        class BrandNewWorker(QThread):
            pass

            def __init__(self):
                super().__init__()
                self.cancelled = False

            def cancel_request(self):
                self.cancelled = True

        worker = BrandNewWorker()
        _Harness([worker])._cancel_long_operations()

        self.assertTrue(worker.cancelled, "новый воркер не отменён")


class TestCancelDoesNotStartThreads(unittest.TestCase):
    pass

    def test_workers_are_not_running(self):
        worker = _make(UniversalExtractWorker, "7z.exe", "C:/a.zip", "C:/d")
        self.assertFalse(
            worker.isRunning(), "воркер не должен быть запущен при создании"
        )


if __name__ == "__main__":
    unittest.main()
