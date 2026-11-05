from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.parser import parse_csv_list_reported
from ui.archive_loader import ArchiveLoaderMixin

GOOD7 = "#2026-09-26 18:35:48\tA....\t30\t720%\t0001\t+\tфайл.txt#"
BAD5 = "#2026-09-26 18:35:48\tA....\t30\tплохая.txt#"


class FakeStatusBar:
    def __init__(self):
        self.messages = []

    def showMessage(self, text, *a, **k):
        self.messages.append(text)


class FakeTree:
    def build_archive_subtree(self, path, entries):
        self.entries = entries


class FakeLoader:


    def __init__(self):
        from ui import i18n

        i18n.set_language("ru", notify=False)
        self.logged = []
        self._status = FakeStatusBar()
        self.tree = FakeTree()
        self.cached = {}
        self.navigated = []
        self.status_refreshes = 0


        self._busy_calls = 0


    def log_command(self, cmd):
        pass

    def log_output(self, text):
        self.logged.append(text)

    def statusBar(self):
        return self._status

    def _stop_busy(self):
        self._busy_calls += 1


    def _cache(self, path):


        return self.cached.setdefault(
            path, {"entries": None, "loaded": False, "info_loaded": False}
        )

    def _activate_archive(self, path):
        pass

    def navigate_archive(self, inner, from_tree=False):
        self.navigated.append(inner)

    def navigate_fs(self, path):
        pass

    def _load_info(self, path):
        pass

    def _refresh_status_for_current_mode(self):
        self.status_refreshes += 1

    def _index_store_if_unchanged(self, ctx, entries):
        pass


    _on_streaming_list_result = ArchiveLoaderMixin._on_streaming_list_result
    _apply_list_entries = ArchiveLoaderMixin._apply_list_entries
    _report_list_loss = ArchiveLoaderMixin._report_list_loss


def run_handler(text, make_active=False, rc=0):
    entries, report = parse_csv_list_reported(text)
    result = {
        "path": str(ROOT / "backup.zpaq"),
        "make_active": make_active,
        "inner": "",
        "file_stamp": None,
        "rc": rc,
        "cancelled": False,
        "entries": entries,
        "report": report,
        "tail": "",
    }
    loader = FakeLoader()
    loader._on_streaming_list_result(result)
    return loader


class TestHandlerShowsLoss(unittest.TestCase):

    def test_loss_is_announced(self):
        text = "\n".join([GOOD7, GOOD7, BAD5, BAD5])
        loader = run_handler(text)

        self.assertEqual(len(loader._status.messages), 1,
                         "строка состояния молчит при потере строк")
        self.assertIn("2", loader._status.messages[0])
        self.assertNotIn("status.", loader._status.messages[0],
                         "в строке состояния ключ перевода")

    def test_loss_is_logged_with_samples(self):
        loader = run_handler("\n".join([GOOD7, BAD5]))
        joined = "\n".join(loader.logged)
        self.assertIn("плохая", joined,
                      "в журнале нет примера строки — разбирать будет нечем")

    def test_entries_still_built(self):
        loader = run_handler("\n".join([GOOD7, GOOD7, BAD5]))
        cached = list(loader.cached.values())[0]
        self.assertTrue(cached.get("loaded"))
        self.assertEqual(len(cached.get("entries")), 2)

    def test_no_loss_no_announcement(self):
        loader = run_handler("\n".join([GOOD7, GOOD7]))
        announced = [m for m in loader._status.messages
                     if "список" in m.lower()]
        self.assertEqual(announced, [], f"шум без повода: {announced}")

    def test_announcement_survives_activation(self):
        loader = run_handler("\n".join([GOOD7, BAD5]), make_active=True)
        self.assertTrue(loader.navigated, "переход внутрь не выполнен")
        announced = [m for m in loader._status.messages
                     if "список" in m.lower()]
        self.assertEqual(
            len(announced), 1,
            f"после перехода предупреждение пропало: {loader._status.messages}")


class TestHandlerEmpty(unittest.TestCase):


    def test_no_entries_shows_dialog_path(self):
        import ui.archive_loader as loader_mod

        calls = []

        class FakeBox:
            @staticmethod
            def warning(parent, title, text, *a, **k):
                calls.append((title, text))

            @staticmethod
            def critical(parent, title, text, *a, **k):
                calls.append((title, text))

        real = loader_mod.QMessageBox
        loader_mod.QMessageBox = FakeBox
        try:
            loader = run_handler("")
        finally:
            loader_mod.QMessageBox = real

        self.assertTrue(calls, "диалог «нет данных» не показан")
        entries, report = parse_csv_list_reported("")
        self.assertTrue(report.ok)

        announced = [m for m in loader._status.messages
                     if "список" in m.lower()]
        self.assertEqual(announced, [],
                         f"пустой вывод дал сообщение о неполном разборе: "
                         f"{announced}")


if __name__ == "__main__":
    unittest.main()
