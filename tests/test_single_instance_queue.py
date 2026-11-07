





























from __future__ import annotations

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


from core.single_instance import SingleInstance              


class _SI(unittest.TestCase):
    def _make(self) -> SingleInstance:
        si = SingleInstance()
        self.addCleanup(si.deleteLater)
        return si


class TestPendingQueue(_SI):
    def test_commands_accumulate_before_receiver(self):
        si = self._make()
        si._deliver(["a1"])
        si._deliver(["a2"])
        self.assertEqual(si._pending, [["a1"], ["a2"]])

    def test_pending_order_preserved(self):
        pass
        si = self._make()
        for i in range(5):
            si._deliver([f"n{i}"])
        received = []
        si.connect_command_receiver(received.append)
        self.assertEqual(received, [[f"n{i}"] for i in range(5)])

    def test_connect_drains_pending_and_clears(self):
        si = self._make()
        received = []
        si._deliver(["x"])
        si._deliver(["y"])

        si.connect_command_receiver(received.append)

        self.assertEqual(received, [["x"], ["y"]])
        self.assertEqual(si._pending, [],
                         "_pending не очищен после раздачи — при "
                         "следующем приёме продублируется")

    def test_pending_list_is_copied_not_aliased(self):
        pass




        si = self._make()
        original = ["a", "b"]
        si._deliver(original)
        original.append("c")

        received = []
        si.connect_command_receiver(received.append)

        self.assertEqual(received, [["a", "b"]],
                         "аргумент _deliver сохраняется по ссылке — "
                         "изменения извне попадают в очередь")


class TestReceiverReplacesSignal(_SI):
    def test_receiver_gets_commands_after_connect(self):
        pass
        si = self._make()
        received = []
        si.connect_command_receiver(received.append)
        si._deliver(["z"])
        self.assertEqual(received, [["z"]])
        self.assertEqual(si._pending, [])

    def test_signal_not_emitted_when_receiver_set(self):
        pass





        si = self._make()
        signal_received = []
        si.command_received.connect(signal_received.append)

        receiver_received = []
        si.connect_command_receiver(receiver_received.append)

        si._deliver(["z"])

        self.assertEqual(receiver_received, [["z"]])
        self.assertEqual(signal_received, [],
                         "command_received эмитится при установленном "
                         "приёмнике — старый подписчик получит дубль")

    def test_signal_emitted_when_no_receiver(self):
        pass





        si = self._make()
        signal_received = []
        si.command_received.connect(signal_received.append)

        si._deliver(["z"])

        self.assertEqual(signal_received, [["z"]])

    def test_second_connect_replaces_receiver(self):
        si = self._make()
        first = []
        second = []
        si.connect_command_receiver(first.append)
        si.connect_command_receiver(second.append)
        si._deliver(["x"])
        self.assertEqual(first, [], "первый приёмник продолжает вызываться")
        self.assertEqual(second, [["x"]])


class TestReceiverFailure(_SI):
    def test_receiver_exception_does_not_break_queue(self):
        pass



        si = self._make()
        calls = []

        def bad(args):
            calls.append(args)
            if len(calls) == 1:
                raise RuntimeError("boom")

        si.connect_command_receiver(bad)
        si._deliver(["x"])
        si._deliver(["y"])

        self.assertEqual(calls, [["x"], ["y"]],
                         "после исключения в приёмнике следующая "
                         "команда не дошла")


class TestSignalAndReceiverInterleaved(_SI):
    def test_signal_before_connect_then_receiver_after(self):
        pass







        si = self._make()
        si._deliver(["a"])

        received = []
        si.connect_command_receiver(received.append)

        self.assertEqual(received, [["a"]],
                         "команда, пришедшая до подписки, потеряна")


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
