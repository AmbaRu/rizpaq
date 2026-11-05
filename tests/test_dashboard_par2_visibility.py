from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QWidget

from ui import i18n

_APP = QApplication.instance() or QApplication(sys.argv)
i18n.set_language("ru", notify=False)

from core import tasks as T
from ui.dashboard_page import DashboardPage


def _make_page(works_spec):

    tmp = Path(tempfile.mkdtemp(prefix="dash_par2off_"))
    container = T.empty_container()
    for title, par2_enabled, make_set in works_spec:
        dest = tmp / f"{title}.zpaq"
        dest.write_bytes(b"x" * 100)
        if make_set:
            Path(str(dest) + ".par2").write_bytes(b"x" * 16)
        work = T.add_work(container, title, [str(tmp)], str(dest))
        T.add_job(container, work["id"], {
            "title": "Бэкап " + title, "action": "backup",
            "par2_enabled": bool(par2_enabled),
        })
    T.save_container(T.container_path(str(tmp)), container)

    class _Status:
        def showMessage(self, *a, **k):
            pass

    class Host(QWidget):
        _tasks_dir = lambda s: str(tmp)
        backup_page = None

        def _enter_archive(self, p):
            pass

        def _start_par2_verify(self, p):
            return True

        def statusBar(self):
            return _Status()

    page = DashboardPage(host=Host())
    page.refresh()
    return page


def _headers(page):
    out = []
    for wid, _rows, par2_on, par2_ok in page._grouped_visible_rows():
        row = next(r for r in page._rows if r.work_id == wid)
        out.append((wid, par2_on, par2_ok,
                    page._work_header_text(row, par2_on, par2_ok)))
    return out


class TestPar2Disabled(unittest.TestCase):
    @classmethod
    def setUpClass(cls):


        i18n.set_language("ru", notify=False)

        cls.page = _make_page([
            ("Есть набор", True, True),
            ("Отключено", False, False),
            ("Без набора", True, False),
        ])

    def _header_by_title(self, title):
        for wid, par2_on, par2_ok, text in _headers(self.page):
            if title in text:
                return par2_on, par2_ok, text
        self.fail("заголовок не найден: " + title)

    def test_set_present_label(self):
        _, _, text = self._header_by_title("Есть набор")
        self.assertIn("PAR2: набор есть", text)

    def test_disabled_label(self):
        par2_on, _, text = self._header_by_title("Отключено")
        self.assertFalse(par2_on)
        self.assertIn("PAR2: отключено", text)

    def test_missing_set_label(self):
        par2_on, _, text = self._header_by_title("Без набора")
        self.assertTrue(par2_on)
        self.assertIn("PAR2: набора нет", text)

    def test_gauge_counts_all_backups(self):

        self.assertEqual(
            self.page._lbl_gauge.text(),
            "защищено 1 из 3 бэкапов")

    def test_disabled_work_in_gauge_denominator(self):


        page = _make_page([("Только отключено", False, False)])
        self.assertEqual(page._lbl_gauge.text(), "защищено 0 из 1 бэкапов")

    def test_no_backup_jobs_empty(self):

        page = _make_page([])
        self.assertEqual(page._lbl_gauge.text(), "Бэкап-задания отсутствуют")


if __name__ == "__main__":
    unittest.main(verbosity=2)
