from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QMetaMethod, QThread
from PySide6.QtWidgets import QApplication

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


def _make_workers():
    from workers.extract_workers import (
        ExtractFileWorker,
        ExtractFolderBatchWorker,
        ExtractFolderWorker,
    )


    fw = ExtractFileWorker(
        "zpaqfranz", "C:/a.zpaq", None, "inner/file.txt", None, "C:/out.txt"
    )


    bw = ExtractFolderBatchWorker(
        "zpaqfranz", "C:/a.zpaq", None, "", None, "C:/out"
    )

    fow = ExtractFolderWorker(
        "zpaqfranz", "C:/a.zpaq", None, [], Path("C:/out")
    )
    return fw, bw, fow


def _own_signals(worker) -> list:

    mo = worker.metaObject()
    return [
        mo.method(i).methodSignature().data().decode()
        for i in range(mo.methodOffset(), mo.methodCount())
        if mo.method(i).methodType() == QMetaMethod.MethodType.Signal
    ]


def _all_signals_including_inherited(worker) -> list:

    mo = worker.metaObject()
    own = [
        mo.method(i).methodSignature().data().decode()
        for i in range(mo.methodOffset(), mo.methodCount())
    ]
    inherited = [
        mo.method(i).methodSignature().data().decode()
        for i in range(0, mo.methodOffset())
        if mo.method(i).methodType() == QMetaMethod.MethodType.Signal
    ]
    return own + inherited


class TestExtractWorkerSignals(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        cls.file_worker, cls.batch_worker, cls.folder_worker = _make_workers()
        cls.workers = [
            ("ExtractFileWorker", cls.file_worker),
            ("ExtractFolderBatchWorker", cls.batch_worker),
            ("ExtractFolderWorker", cls.folder_worker),
        ]

    def test_all_are_qthread_subclasses(self):
        self.assertIsInstance(self.file_worker, QThread)
        self.assertIsInstance(self.batch_worker, QThread)
        self.assertIsInstance(self.folder_worker, QThread)

    def test_worker_started_signal_declared(self):
        for name, worker in self.workers:
            with self.subTest(worker=name):
                own = _own_signals(worker)
                self.assertTrue(
                    any(sig.startswith("worker_started(") for sig in own),
                    f"{name}: сигнал worker_started не объявлен. "
                    f"Свои сигналы: {own}",
                )

    def test_worker_started_signatures(self):
        cases = [
            ("ExtractFileWorker", self.file_worker, "worker_started()"),
            ("ExtractFolderBatchWorker", self.batch_worker, "worker_started()"),
            ("ExtractFolderWorker", self.folder_worker, "worker_started(int)"),
        ]
        for name, worker, expected in cases:
            with self.subTest(worker=name):
                own = _own_signals(worker)
                self.assertIn(
                    expected, own,
                    f"{name}: ожидался сигнал {expected!r}. "
                    f"Свои сигналы: {own}",
                )

    def test_does_not_define_started_signal(self):
        for name, worker in self.workers:
            with self.subTest(worker=name):
                own = _own_signals(worker)
                self.assertFalse(
                    any(sig.startswith("started(") for sig in own),
                    f"{name}: класс снова объявляет свой сигнал `started` "
                    f"(перекрывает QThread.started). Свои сигналы: {own}",
                )

    def test_started_is_inherited_qthread_signal(self):
        for name, worker in self.workers:
            with self.subTest(worker=name):
                all_sig = _all_signals_including_inherited(worker)
                self.assertIn(
                    "started()", all_sig,
                    f"{name}: QThread.started не найден в метаобъекте. "
                    f"Все сигналы: {all_sig}",
                )

    def test_does_not_define_finished_signal(self):
        for name, worker in self.workers:
            with self.subTest(worker=name):
                own = _own_signals(worker)
                self.assertFalse(
                    any(sig.startswith("finished(") for sig in own),
                    f"{name}: класс объявляет свой `finished` "
                    f"(перекрывает QThread.finished). Свои сигналы: {own}",
                )

    def test_finished_is_inherited_qthread_signal(self):

        for name, worker in self.workers:
            with self.subTest(worker=name):
                all_sig = _all_signals_including_inherited(worker)
                self.assertIn(
                    "finished()", all_sig,
                    f"{name}: QThread.finished не найден в метаобъекте. "
                    f"Все сигналы: {all_sig}",
                )

    def test_two_subscribers_different_arity_dont_collide(self):
        got = {}

        def on_started():
            got["started"] = True

        def on_worker_started(total):
            got["worker_started"] = total


        w = self.folder_worker
        w.started.connect(on_started)
        w.worker_started.connect(on_worker_started)


        w.started.emit()
        w.worker_started.emit(42)

        self.assertIs(got.get("started"), True,
                      "QThread.started не дошёл до подписчика")
        self.assertEqual(got.get("worker_started"), 42,
                         "worker_started(int) не дошёл до подписчика")


if __name__ == "__main__":
    unittest.main()
