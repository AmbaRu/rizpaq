from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QCoreApplication, QMetaMethod, QThread, Signal
from PySide6.QtWidgets import QApplication

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


class TestUniversalListWorkerSignals(unittest.TestCase):
    def setUp(self):
        from workers.universal_worker import UniversalListWorker

        self.cls = UniversalListWorker
        self.worker = UniversalListWorker("7z.exe", "x.zip", None)

    def _own_signals(self) -> list:
        mo = self.worker.metaObject()
        return [
            mo.method(i).methodSignature().data().decode()
            for i in range(mo.methodOffset(), mo.methodCount())
            if mo.method(i).methodType() == QMetaMethod.MethodType.Signal
        ]

    def test_result_signal_is_named_listed(self):

        self.assertIn("listed(QVariantList,QString)", self._own_signals())

    def test_does_not_define_finished_signal(self):

        self.assertNotIn("finished()", self._own_signals())

    def test_finished_is_inherited_qthread_signal(self):

        self.assertIsInstance(self.worker.finished, Signal)

        self.assertNotIn("finished", vars(self.cls))


        mo = self.worker.metaObject()
        all_signals = [
            mo.method(i).methodSignature().data().decode()
            for i in range(mo.methodOffset(), mo.methodCount())
        ]
        all_signals += [
            mo.method(i).methodSignature().data().decode()
            for i in range(0, mo.methodOffset())
            if mo.method(i).methodType() == QMetaMethod.MethodType.Signal
        ]
        self.assertIn("finished()", all_signals)

    def test_both_slots_receive_expected_arity(self):
        got: dict = {}

        self.worker.listed.connect(
            lambda entries, log: got.update(listed=(entries, log))
        )
        self.worker.finished.connect(lambda w=None: got.update(finished=True))

        self.worker.listed.emit([1, 2], "raw log")
        self.worker.finished.emit()

        self.assertEqual(got.get("listed"), ([1, 2], "raw log"))
        self.assertIs(got.get("finished"), True)

    def test_is_qthread_subclass(self):
        self.assertTrue(issubclass(self.cls, QThread))


if __name__ == "__main__":
    unittest.main()
