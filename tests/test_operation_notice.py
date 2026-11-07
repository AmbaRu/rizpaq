












from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt, QTimer              
from PySide6.QtWidgets import QApplication, QMainWindow              

import ui.i18n as i18n              
from ui.operation_notice import (              
    NOTICE_DELAY_MS,
    OperationNotice,
    _fmt_elapsed,
)

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))

i18n.set_language("ru", notify=False)


def _pump(ms: int) -> None:
    pass
    end = time.monotonic() + ms / 1000.0
    while time.monotonic() < end:
        _APP.processEvents()
        time.sleep(0.005)


                                                                        
                                                                       
                                                                 
                                                                  
                                          
                                                                        

from ui.app_services import AppServicesMixin              


class _BusyHost(AppServicesMixin, QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self._busy_base = ""
        self._busy_n = 0
        self._busy_depth = 0
        self._notice = None
        self._wait_cursor = False
        self.cancelled = 0
        self._busy_timer = QTimer(self)
        self._busy_timer.setInterval(350)
        self._busy_timer.timeout.connect(self._tick_busy)

    def _cancel_long_operations(self):
        self.cancelled += 1

    def close(self):
        if self._notice is not None:
            self._notice.hide_notice()
        self._busy_timer.stop()
        super().close()


class TestElapsedFormat(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(_fmt_elapsed(0), "0s")
        self.assertEqual(_fmt_elapsed(59), "59s")

    def test_minutes(self):
        self.assertEqual(_fmt_elapsed(60), "1:00")
        self.assertEqual(_fmt_elapsed(125), "2:05")

    def test_hours(self):
        self.assertEqual(_fmt_elapsed(3600), "1:00:00")
        self.assertEqual(_fmt_elapsed(3725), "1:02:05")


class TestNoticeBasics(unittest.TestCase):
    def setUp(self):
        self.n = OperationNotice(cancel_enabled=True)
        self.addCleanup(self.n.hide_notice)

    def test_starts_hidden(self):
        self.assertFalse(self.n.is_visible_notice())
        self.assertFalse(self.n.isVisible())

    def test_does_not_show_before_delay(self):
        pass


        self.n.show_notice("Чтение архива")
        _pump(NOTICE_DELAY_MS // 2)
        self.assertFalse(
            self.n.is_visible_notice(),
            "окно показалось раньше задержки — будет мигать на каждом открытии",
        )
        _pump(NOTICE_DELAY_MS)
        self.assertTrue(
            self.n.is_visible_notice(), "после задержки окно обязано появиться"
        )

    def test_hide_before_delay_prevents_show(self):
        pass
        self.n.show_notice("Быстрая операция")
        _pump(NOTICE_DELAY_MS // 3)
        self.n.hide_notice()
        _pump(NOTICE_DELAY_MS * 2)
        self.assertFalse(
            self.n.is_visible_notice(),
            "окно показалось после скрытия — быстрые операции будут мигать",
        )

    def test_is_not_modal(self):
        pass



        self.assertFalse(self.n.isModal(), "окно не должно быть модальным")

    def test_does_not_accept_focus(self):
        self.assertTrue(
            bool(self.n.windowFlags() & Qt.WindowDoesNotAcceptFocus),
            "окно должно работать в фоне, не забирая фокус",
        )

    def test_stays_on_top(self):
        self.assertTrue(
            bool(self.n.windowFlags() & Qt.WindowStaysOnTopHint),
            "окно должно быть поверх главного",
        )

    def test_frameless_and_small(self):
        pass
        self.assertTrue(bool(self.n.windowFlags() & Qt.FramelessWindowHint))
        self.assertLessEqual(self.n.width(), 460)
        self.assertLessEqual(self.n.height(), 160)

    def test_update_step_changes_text(self):
        self.n.show_notice("Чтение списка файлов")
        self.n.update_step("Получение информации об архиве")
        self.assertEqual(self.n._step_text, "Получение информации об архиве")
        self.assertIn("информации", self.n._title.text())

    def test_hide_stops_timers(self):
        self.n.show_notice("Чтение")
        _pump(NOTICE_DELAY_MS + 100)
        self.assertTrue(self.n.is_visible_notice())

        self.n.hide_notice()
        self.assertFalse(self.n._delay_timer.isActive())
        self.assertFalse(self.n._tick_timer.isActive())
        self.assertFalse(self.n.isVisible())

    def test_hide_notice_is_idempotent(self):
        self.n.hide_notice()
        self.n.hide_notice()                     

    def test_repeated_show_updates_text(self):
        self.n.show_notice("Первая операция")
        _pump(NOTICE_DELAY_MS + 50)
        self.n.show_notice("Вторая операция")
        self.assertEqual(self.n._step_text, "Вторая операция")
        self.assertTrue(self.n.is_visible_notice(), "повторный show не должен гасить окно")


class TestNoticeCancel(unittest.TestCase):
    def test_cancel_emits_signal(self):
        n = OperationNotice(cancel_enabled=True)
        got = []
        n.cancelRequested.connect(lambda: got.append(1))

        n.show_notice("Операция")
        _pump(NOTICE_DELAY_MS + 50)
        self.assertTrue(n.is_visible_notice())

        n._on_cancel()
        self.assertEqual(got, [1], "нажатие «Отмена» не дошло до обработчика")
        self.assertFalse(n.is_visible_notice(), "после отмены окно должно скрыться")
        n.hide_notice()

    def test_cancel_button_hidden_when_disabled(self):
        n = OperationNotice(cancel_enabled=False)
        self.assertFalse(n._cancel_btn.isVisible())
        n.hide_notice()


class TestBusyCounter(unittest.TestCase):
    pass




    def setUp(self):
        self.w = _BusyHost()
        self.addCleanup(self.w.close)

    def test_depth_grows_and_shrinks(self):
        self.w._start_busy("Чтение списка")
        self.assertEqual(self.w._busy_depth, 1)

        self.w._start_busy("Информация об архиве")
        self.assertEqual(
            self.w._busy_depth, 2, "вторая операция должна увеличить счётчик"
        )

        self.w._stop_busy()
        self.assertEqual(
            self.w._busy_depth, 1, "после первой остановки операция ещё идёт"
        )

        self.w._stop_busy()
        self.assertEqual(self.w._busy_depth, 0)

    def test_notice_survives_the_gap_between_phases(self):
        pass



        self.w._start_busy("Чтение списка файлов")
        _pump(NOTICE_DELAY_MS + 80)
        self.assertTrue(self.w._notice.is_visible_notice())

                                      
        self.w._start_busy("Информация об архиве")
        self.w._stop_busy()                      

        self.assertEqual(self.w._busy_depth, 1, "запрос информации ещё идёт")
        self.assertTrue(
            self.w._notice.is_visible_notice(),
            "окно скрылось между фазами — будет мигание",
        )
        self.assertIn("Информация", self.w._notice._step_text)

    def test_notice_hidden_when_all_done(self):
        self.w._start_busy("Чтение списка файлов")
        _pump(NOTICE_DELAY_MS + 80)
        self.w._start_busy("Информация об архиве")
        self.w._stop_busy()
        self.w._stop_busy()

        self.assertFalse(
            self.w._notice.is_visible_notice(),
            "после завершения обеих фаз окно должно скрыться",
        )

    def test_cursor_not_restored_too_early(self):
        self.w._start_busy("Одна")
        self.w._start_busy("Две")
        self.w._stop_busy()
        self.assertTrue(
            self.w._wait_cursor,
            "курсор ожидания снят, хотя вторая операция ещё идёт",
        )
        self.w._stop_busy()
        self.assertFalse(self.w._wait_cursor)

    def test_stop_without_start_is_safe(self):
        self.w._stop_busy()
        self.assertGreaterEqual(self.w._busy_depth, 0, "счётчик ушёл в минус")

    def test_second_operation_replaces_phase_text(self):
        pass



        self.w._start_busy("Чтение списка файлов")
        _pump(NOTICE_DELAY_MS + 50)
        self.assertEqual(self.w._notice._step_text, "Чтение списка файлов")

        self.w._start_busy("Информация об архиве")
        self.assertEqual(
            self.w._notice._step_text, "Информация об архиве",
            "окошко продолжает показывать первую фазу",
        )

    def test_notice_is_created_lazily(self):
        self.assertIsNone(self.w._notice, "окно не должно создаваться заранее")
        self.w._start_busy("Операция")
        self.assertIsNotNone(self.w._notice)

    def test_notice_cancel_stops_operations(self):
        self.w._ensure_notice()
        self.assertIsNotNone(self.w._notice)

                                                                       
                                                                       
        self.assertFalse(
            self.w._notice._cancel_btn.isHidden(),
            "кнопка «Отмена» скрыта — отменить долгую операцию нечем",
        )

        self.w._notice._on_cancel()
        self.assertEqual(
            self.w.cancelled, 1, "отмена в окошке не гасит фоновые операции"
        )


class TestLocaleKeys(unittest.TestCase):
    def test_notice_keys_exist_in_all_languages(self):
        root = Path(__file__).resolve().parent.parent / "locales"
        for path in sorted(root.glob("*.json")):
            with self.subTest(locale=path.stem):
                strings = json.loads(path.read_text(encoding="utf-8"))["strings"]
                for key in ("notice.title", "notice.long"):
                    self.assertIn(key, strings, f"{path.name}: нет ключа {key}")

    def test_notice_uses_translated_text(self):
        i18n.set_language("de", notify=False)
        try:
            n = OperationNotice()
            self.assertNotEqual(n.windowTitle(), "notice.title")
            self.assertEqual(n.windowTitle(), i18n.tr("notice.title"))
            self.assertNotEqual(n._hint.text(), "notice.long")
            n.hide_notice()
        finally:
            i18n.set_language("ru", notify=False)


if __name__ == "__main__":
    unittest.main()
