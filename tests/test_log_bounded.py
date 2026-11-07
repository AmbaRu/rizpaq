












from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QPlainTextEdit              

import ui.window_layout as wl              

APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
APP = QApplication.instance()
if APP is not None:
    APP.setFont(QFont("Segoe UI", 9))


SRC = (ROOT / "ui" / "window_layout.py").read_text(encoding="utf-8")


class TestLimitIsApplied(unittest.TestCase):
    def test_limit_defined(self):
        self.assertTrue(
            hasattr(wl, "LOG_MAX_BLOCKS"),
            "предел журнала не объявлен")
        self.assertGreater(wl.LOG_MAX_BLOCKS, 0)

    def test_limit_set_on_document(self):
        pass






        self.assertIn(
            "self.log.document().setMaximumBlockCount(", SRC,
            "предел не применяется к документу журнала")

    def test_limit_really_binds(self):
        pass






        w = QPlainTextEdit()
        w.document().setMaximumBlockCount(wl.LOG_MAX_BLOCKS)

                                                                   
                                     
        total = wl.LOG_MAX_BLOCKS + 500
                                                                          
        for _ in range(total // 500 + 1):
            w.appendPlainText("\n".join(["строка журнала"] * 500))
            APP.processEvents()

        self.assertLessEqual(
            w.blockCount(), wl.LOG_MAX_BLOCKS + 600,
            f"предел не сработал: блоков {w.blockCount()} при пределе "
            f"{wl.LOG_MAX_BLOCKS}")
        w.close()


class TestLimitIsSensible(unittest.TestCase):
    pass







    def test_not_so_small_it_throttles(self):
        pass






        self.assertGreaterEqual(
            wl.LOG_MAX_BLOCKS, 30000,
            "предел слишком мал: по замеру документ начнёт переполняться "
            "за несколько открытий, а журнал замедлится в разы")

    def test_not_so_large_it_does_not_bound(self):
        pass






        self.assertLessEqual(
            wl.LOG_MAX_BLOCKS, 80000,
            "предел слишком велик: по замеру это десятки мегабайт и то же "
            "замедление при переполнении")

    def test_bounded_memory_in_megabytes(self):
        pass






        per_block_kb = 0.384
        expected = wl.LOG_MAX_BLOCKS * per_block_kb / 1024
        self.assertLess(expected, 32,
                        f"предел означает {expected:.1f} МБ — многовато "
                        f"для журнала")
        self.assertGreater(expected, 4,
                           f"предел означает лишь {expected:.1f} МБ — "
                           f"на диагностику маловато")

    def test_existing_call_site_limits_kept(self):
        pass











        import re

        acts = (ROOT / "ui" / "archive_actions.py").read_text(encoding="utf-8")
        for name in ("_TEST_LOG_LIMIT", "_CREATE_LOG_LIMIT"):
            m = re.search(rf"{name}\s*=\s*(\d+)", acts)
            self.assertIsNotNone(m, f"{name}: объявление не найдено")
            value = int(m.group(1))
            self.assertGreater(
                value, 0,
                f"{name} = {value}: вывод обрезается целиком, в журнале "
                f"не останется ничего")
            self.assertGreaterEqual(
                value, 1000,
                f"{name} = {value}: слишком мало для хвоста вывода движка")


class TestDiagnosticsSurvive(unittest.TestCase):
    pass







    def test_report_fits_in_the_window(self):
        from core.parser import parse_csv_list_reported

        good = "#2026-09-26 18:35:48\tA....\t30\t720%\t0001\t+\tфайл.txt#"
        bad = "#2026-09-26 18:35:48\tA....\t30\tплохая.txt#"
        _entries, report = parse_csv_list_reported(
            "\n".join([good] + [bad] * 3)
        )
        report_lines = report.log_text().splitlines()

        self.assertTrue(report_lines, "отчёт пуст")
        self.assertLess(
            len(report_lines), wl.LOG_MAX_BLOCKS // 100,
            "отчёт о потерях занимает заметную часть окна журнала")

    def test_log_still_holds_recent_work(self):
        pass





        w = QPlainTextEdit()
        w.document().setMaximumBlockCount(100)
        w.appendPlainText("старое")
                                                                     
                                                           
        for _ in range(300):
            w.appendPlainText("свежее")
        APP.processEvents()
        text = w.toPlainText()
        self.assertIn("свежее", text, "последние записи вытеснены")
        self.assertNotIn("старое", text,
                         "старые записи не вытеснены — окно не работает")
        w.close()


if __name__ == "__main__":
    unittest.main()
