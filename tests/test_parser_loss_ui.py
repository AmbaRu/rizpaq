from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.parser import ParseReport
from ui.archive_loader import ArchiveLoaderMixin

GOOD7 = "#2026-09-26 18:35:48\tA....\t30\t720%\t0001\t+\tфайл.txt#"
BAD5 = "#2026-09-26 18:35:48\tA....\t30\tплохая.txt#"


class FakeStatusBar:
    def __init__(self):
        self.messages = []

    def showMessage(self, text, *a, **k):
        self.messages.append(text)


class FakeLoader:


    def __init__(self):
        self.logged = []
        self._status = FakeStatusBar()

    def log_output(self, text):
        self.logged.append(text)

    def statusBar(self):
        return self._status


    _report_list_loss = ArchiveLoaderMixin._report_list_loss


class TestLossIsShown(unittest.TestCase):
    def setUp(self):


        from ui import i18n

        i18n.set_language("ru", notify=False)

    def _report_with_loss(self):
        from core.parser import parse_csv_list_reported

        _entries, report = parse_csv_list_reported(
            "\n".join([GOOD7, BAD5, BAD5])
        )
        return report

    def test_warning_written_to_log(self):
        loader = FakeLoader()
        loader._report_list_loss(self._report_with_loss())
        self.assertEqual(len(loader.logged), 1, "в журнал ничего не записано")
        self.assertIn("2", loader.logged[0], "в журнале нет числа потерь")
        self.assertIn("плохая", loader.logged[0], "в журнале нет примера")

    def test_status_bar_shows_count(self):
        loader = FakeLoader()
        loader._report_list_loss(self._report_with_loss())
        self.assertEqual(len(loader._status.messages), 1)
        self.assertIn("2", loader._status.messages[0])

    def test_status_bar_text_is_human(self):
        loader = FakeLoader()
        loader._report_list_loss(self._report_with_loss())
        shown = loader._status.messages[0]
        self.assertNotIn("status.", shown,
                         f"в строке состояния ключ перевода: {shown!r}")
        self.assertNotIn("{", shown,
                         f"в строке состояния не подставлено число: {shown!r}")
        self.assertIn("список", shown.lower(),
                      f"текст не похож на сообщение о неполном списке: {shown!r}")

    def test_status_bar_text_is_not_a_raw_key(self):
        import json

        key = "status.list_partially_parsed"
        for code in ("en", "ru", "de", "fr", "es", "it", "zh", "pt", "ja", "pl"):
            path = ROOT / "locales" / f"{code}.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn(key, data["strings"], f"{code}: ключа нет в переводе")
            self.assertIn("{count}", data["strings"][key],
                          f"{code}: нет плейсхолдера {{count}}")

    def test_silence_when_nothing_lost(self):
        from core.parser import parse_csv_list_reported

        _entries, report = parse_csv_list_reported("\n".join([GOOD7, GOOD7]))
        self.assertTrue(report.ok)

        loader = FakeLoader()
        loader._report_list_loss(report)
        self.assertEqual(loader.logged, [], "журнал пишется без повода")
        self.assertEqual(loader._status.messages, [],
                         "строка состояния трогается без повода")

    def test_none_report_tolerated(self):
        loader = FakeLoader()
        loader._report_list_loss(None)
        self.assertEqual(loader.logged, [])
        self.assertEqual(loader._status.messages, [])

    def test_broken_sink_does_not_crash(self):

        class Broken(FakeLoader):
            def log_output(self, text):
                raise RuntimeError("журнал недоступен")

            def statusBar(self):
                raise RuntimeError("нет строки состояния")

        loader = Broken()
        loader._report_list_loss(self._report_with_loss())


class TestReportReachable(unittest.TestCase):

    def test_streaming_worker_uses_reported_parser(self):
        worker_src = (
            ROOT / "workers" / "list_worker.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "parse_csv_line_reported", worker_src,
            "потоковый воркер не зовёт разбор с отчётом — потеря снова "
            "станет молчаливой")

    def test_loader_does_not_parse_listing_itself(self):
        loader_src = (
            ROOT / "ui" / "archive_loader.py"
        ).read_text(encoding="utf-8")
        for forbidden in ("parse_csv_list_reported", "parse_csv_line_reported"):
            self.assertNotIn(
                forbidden, loader_src,
                f"{forbidden} вернулся в архивный загрузчик — разбор "
                f"должен жить в workers/list_worker.py")

    def test_warning_is_placed_after_navigation(self):
        src = (ROOT / "ui" / "archive_loader.py").read_text(encoding="utf-8")
        start = src.index("def _apply_list_entries")

        nxt = src.find("    def ", start + 1)
        body = src[start:nxt] if nxt > 0 else src[start:]
        self.assertIn(
            "_report_list_loss", body,
            "предупреждение не вызывается из постобработки листинга")
        last_navigate = body.rfind("navigate_archive")
        last_refresh = body.rfind("_refresh_status_for_current_mode")
        call = body.rfind("_report_list_loss")
        self.assertGreater(
            call, max(last_navigate, last_refresh),
            "предупреждение вызывается до перехода внутрь архива и будет "
            "затёрто строкой состояния")


if __name__ == "__main__":
    unittest.main()
