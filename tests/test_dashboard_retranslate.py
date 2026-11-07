                       








from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QWidget

from ui import i18n

_APP = QApplication.instance() or QApplication(sys.argv)
i18n.set_language("en", notify=False)

from core import tasks as T
from ui.dashboard_page import DashboardPage


def _make_page():
    tmp = Path(tempfile.mkdtemp(prefix="dash_retr_test_"))
    container = T.empty_container()
    work = T.add_work(container, "W", [str(tmp)], str(tmp / "a.zpaq"))
    T.add_job(container, work["id"], {"title": "J", "action": "backup"})
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


class TestDashboardRetranslate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = _make_page()

    @classmethod
    def tearDownClass(cls):
        i18n.set_language("en", notify=False)

    def test_static_texts_switch(self):
        i18n.set_language("en", notify=False)
        self.page.retranslate()                                           
        en = (
            self.page._title_lbl.text(),
            self.page._tile_captions["ok"].text(),
            self.page._table.horizontalHeaderItem(0).text(),
            self.page._card_caps["dashboard.card.par2"].text(),
            self.page._btn_check_all.text(),
        )
        i18n.set_language("ru", notify=False)
        self.page.retranslate()
        ru = (
            self.page._title_lbl.text(),
            self.page._tile_captions["ok"].text(),
            self.page._table.horizontalHeaderItem(0).text(),
            self.page._card_caps["dashboard.card.par2"].text(),
            self.page._btn_check_all.text(),
        )
        for en_text, ru_text in zip(en, ru):
            self.assertNotEqual(en_text, ru_text)
                                                                         
        self.assertNotIn("dashboard.", ru_text)

    def test_legends_switch(self):
        i18n.set_language("en", notify=False)
        self.page.retranslate()
        en_legends = [lbl.text() for lbl, _ in self.page._donut_legend]
        i18n.set_language("ru", notify=False)
        self.page.retranslate()
        ru_legends = [lbl.text() for lbl, _ in self.page._donut_legend]
        self.assertNotEqual(en_legends, ru_legends)

    def test_bridge_calls_retranslate(self):
        pass
        from ui.language_bridge import LanguageBridgeMixin

        bridge = LanguageBridgeMixin.__new__(LanguageBridgeMixin)
        dash = mock.Mock()
                                                       
        bridge.dashboard_page = dash
                                                                       
                                                
        bridge._cfg = mock.Mock(latest_only=False)
        bridge.latest_only_action = None
        bridge._create_actions = mock.Mock()
        bridge._rebuild_versions_menu = mock.Mock()
        bridge.profile_bar = None
        bridge.backup_page = None
        bridge.table = None
        bridge.search_edit = None
        bridge.tree = None
        bridge._update_title = mock.Mock()
        with mock.patch.object(bridge, "latest_only_action",
                               create=True, new=None):
            bridge._retranslate_ui()
        dash.retranslate.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
