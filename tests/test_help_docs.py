from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QMessageBox

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from core import help_docs


class _FakeBox:


    def __init__(self):
        self.calls: list = []

    def warning(self, parent, title, text):
        self.calls.append(("warning", title, text))

    def information(self, parent, title, text):
        self.calls.append(("information", title, text))


class TestFindManualRoot(unittest.TestCase):
    def test_finds_project_doc(self):
        root = help_docs.find_manual_root()
        self.assertTrue(root is None or isinstance(root, Path))

    def test_prefers_exe_dir_when_it_has_index(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "help" / "ru").mkdir(parents=True)
            (d / "help" / "ru" / "index.html").write_text("x", encoding="utf-8")
            with mock.patch.object(help_docs, "_exe_dir", return_value=d):
                found = help_docs.find_manual_root()
            self.assertIsNotNone(found)
            self.assertEqual(Path(found), d / "help")

    def test_exe_dir_without_index_is_skipped(self):

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "help").mkdir()
            with mock.patch.object(help_docs, "_exe_dir", return_value=d), \
                 mock.patch.object(help_docs, "_project_doc",
                                   return_value=Path(td) / "no_doc"):
                found = help_docs.find_manual_root()
            self.assertIsNone(found)


class TestPickManual(unittest.TestCase):
    def test_current_language_wins(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            for lang in ("ru", "en"):
                (d / lang).mkdir()
                (d / lang / "index.html").write_text("x", encoding="utf-8")
            with mock.patch.object(help_docs, "find_manual_root",
                                   return_value=d), \
                 mock.patch("ui.i18n.current_language", return_value="en"):
                path, lang = help_docs.pick_manual("en")
            self.assertEqual(lang, "en")
            self.assertEqual(Path(path).name, "index.html")
            self.assertEqual(Path(path).parent.name, "en")

    def test_falls_back_to_available(self):

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "ru").mkdir()
            (d / "ru" / "index.html").write_text("x", encoding="utf-8")
            with mock.patch.object(help_docs, "find_manual_root",
                                   return_value=d), \
                 mock.patch("ui.i18n.current_language",
                            return_value="de"):
                path, lang = help_docs.pick_manual("de")
            self.assertEqual(lang, "ru", "немецкого нет, должна взяться русская")
            self.assertEqual(Path(path).parent.name, "ru")

    def test_flat_layout_is_supported(self):

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "index.html").write_text("x", encoding="utf-8")
            with mock.patch.object(help_docs, "find_manual_root",
                                   return_value=d):
                path, _lang = help_docs.pick_manual("ru")
            self.assertIsNotNone(path)
            self.assertEqual(Path(path), d / "index.html")

    def test_no_manual_at_all(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(help_docs, "find_manual_root",
                                   return_value=Path(td)):
                path, lang = help_docs.pick_manual("ru")
            self.assertIsNone(path)
            self.assertEqual(lang, "")

    def test_find_root_none_gives_empty_result(self):
        with mock.patch.object(help_docs, "find_manual_root",
                               return_value=None):
            path, lang = help_docs.pick_manual("ru")
        self.assertIsNone(path)
        self.assertEqual(lang, "")


class TestOnlineUrl(unittest.TestCase):
    def test_online_url_built_from_base_and_lang(self):
        url = help_docs._online_url("ru")
        self.assertTrue(url.startswith(help_docs.ONLINE_BASE))
        self.assertIn("/ru/", url)
        self.assertIn("index.html", url)

    def test_online_url_for_unknown_lang_still_returns(self):

        url = help_docs._online_url("xx")
        self.assertTrue(url.startswith(help_docs.ONLINE_BASE))
        self.assertIn("/xx/", url)


class TestOpenManual(unittest.TestCase):
    def test_opens_local_html_when_found(self):
        with tempfile.TemporaryDirectory() as td:
            html = Path(td) / "index.html"
            html.write_text("<html></html>", encoding="utf-8")
            with mock.patch.object(help_docs, "pick_manual",
                                   return_value=(str(html), "ru")), \
                 mock.patch.object(help_docs.webbrowser, "open") as wb:
                ok, what = help_docs.open_manual("ru")
            self.assertTrue(ok)
            wb.assert_called_once()
            self.assertIn("index.html", wb.call_args[0][0])
            self.assertEqual(what, str(html))

    def test_falls_back_to_online_when_no_local(self):

        with mock.patch.object(help_docs, "pick_manual",
                               return_value=(None, "")), \
             mock.patch.object(help_docs.webbrowser, "open") as wb:
            ok, what = help_docs.open_manual("ru")
        self.assertTrue(ok)
        wb.assert_called_once()
        url = wb.call_args[0][0]
        self.assertTrue(url.startswith(help_docs.ONLINE_BASE))
        self.assertIn("/ru/", url)
        self.assertEqual(what, url)

    def test_fallback_to_other_language_when_current_fails(self):
        calls = []

        def _webbrowser_open(url):
            calls.append(url)

            return "/de/" not in url

        with mock.patch.object(help_docs, "pick_manual",
                               return_value=(None, "")), \
             mock.patch.object(help_docs.webbrowser, "open",
                               side_effect=_webbrowser_open):
            ok, what = help_docs.open_manual("de")

        self.assertTrue(ok, "fallback не сработал")
        self.assertEqual(len(calls), 2, "ожидались попытки de и ru")
        self.assertIn("/de/", calls[0])
        self.assertIn("/ru/", calls[1])
        self.assertIn("/ru/", what)

    def test_returns_failure_when_nothing_opened(self):
        with mock.patch.object(help_docs, "pick_manual",
                               return_value=(None, "")), \
             mock.patch.object(help_docs.webbrowser, "open",
                               side_effect=OSError("нет браузера")):
            ok, what = help_docs.open_manual("ru")
        self.assertFalse(ok)

        self.assertTrue(what.startswith(help_docs.ONLINE_BASE))

    def test_returns_failure_when_open_returns_false(self):
        with mock.patch.object(help_docs, "pick_manual",
                               return_value=(None, "")), \
             mock.patch.object(help_docs.webbrowser, "open",
                               return_value=False):
            ok, what = help_docs.open_manual("ru")
        self.assertFalse(ok, "False от webbrowser.open принят за успех")
        self.assertTrue(what.startswith(help_docs.ONLINE_BASE))

    def test_returns_failure_when_local_open_returns_false(self):
        with tempfile.TemporaryDirectory() as td:
            html = Path(td) / "index.html"
            html.write_text("<html></html>", encoding="utf-8")
            with mock.patch.object(help_docs, "pick_manual",
                                   return_value=(str(html), "ru")), \
                 mock.patch.object(help_docs.webbrowser, "open",
                                   return_value=False):
                ok, _what = help_docs.open_manual("ru")
            self.assertFalse(ok)


class TestMenuWiring(unittest.TestCase):

    def test_handler_exists_on_mixin(self):
        from ui.app_services import AppServicesMixin

        self.assertTrue(hasattr(AppServicesMixin, "_on_open_manual"),
                        "обработчик _on_open_manual отсутствует")

    def test_menu_actions_reference_the_handler(self):
        src = (ROOT / "ui" / "menu_actions.py").read_text(encoding="utf-8")
        self.assertIn('tr("menu.help.guide")', src,
                      "пункт меню «Руководство» не создан")
        self.assertIn("self._on_open_manual)", src,
                      "пункт меню не подключён к обработчику")

    def test_locale_keys_exist_in_target_languages(self):
        import json

        for lang in ("ru", "en"):
            data = json.loads(
                (ROOT / "locales" / f"{lang}.json").read_text(encoding="utf-8"))
            strings = data.get("strings", {})
            self.assertIn("menu.help.guide", strings,
                          f"{lang}: нет ключа menu.help.guide")
            self.assertIn("manual.not_found", strings,
                          f"{lang}: нет ключа manual.not_found")


class TestOpenManualHandler(unittest.TestCase):

    def setUp(self):
        from PySide6.QtWidgets import QMessageBox

        self.app = QApplication.instance() or QApplication([])
        self.box = _FakeBox()
        self._real = QMessageBox.warning
        QMessageBox.warning = self.box.warning
        self.addCleanup(setattr, QMessageBox, "warning", self._real)

        from ui.app_services import AppServicesMixin


        import ui.app_services as _aas
        self._real_tr = _aas.tr
        _aas.tr = lambda key, **kw: f"[{key}|{kw}]"
        self.addCleanup(setattr, _aas, "tr", self._real_tr)

        class _Stub(AppServicesMixin):
            def __init__(self):
                self.status_messages = []

            def statusBar(self):
                return self

            def showMessage(self, msg):
                self.status_messages.append(msg)

        self.stub = _Stub()

    def test_missing_manual_shows_warning(self):
        with mock.patch("core.help_docs.open_manual",
                        return_value=(False, "/нет/справки")):
            self.stub._on_open_manual()
        self.assertEqual(len(self.box.calls), 1,
                         "при отсутствии справки должно быть предупреждение")
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("menu.help.guide", title)
        self.assertIn("manual.not_found", text)
        self.assertIn("/нет/справки", text,
                      "путь, где искали, обязан быть показан")

    def test_found_manual_shows_nothing(self):

        with mock.patch("core.help_docs.open_manual",
                        return_value=(True, "/где/справка.html")):
            self.stub._on_open_manual()
        self.assertEqual(self.box.calls, [],
                         "при успехе диалогов быть не должно")


if __name__ == "__main__":
    unittest.main()
