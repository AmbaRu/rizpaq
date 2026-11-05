from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication

import ui.i18n as i18n

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


def _detect_with(*probes: str) -> str:

    with mock.patch.object(i18n, "_language_probes", return_value=list(probes)):
        return i18n.detect_language()


class TestMatchLanguage(unittest.TestCase):


    A = i18n.LANGUAGES

    def test_plain_iso_tags(self):
        cases = {
            "de_DE": "de", "ru_RU": "ru", "en_US": "en", "it_IT": "it",
            "fr_FR": "fr", "es_ES": "es", "pt_BR": "pt", "ja_JP": "ja",
            "pl_PL": "pl", "zh_CN": "zh",
        }
        for tag, want in cases.items():
            with self.subTest(tag=tag):
                self.assertEqual(i18n._match_language(tag, self.A), want)

    def test_dash_separator(self):
        self.assertEqual(i18n._match_language("de-DE", self.A), "de")

    def test_encoding_suffix(self):
        self.assertEqual(i18n._match_language("de_DE.UTF-8", self.A), "de")

    def test_modifier(self):
        self.assertEqual(i18n._match_language("de_DE.UTF-8@euro", self.A), "de")

    def test_script_variant(self):
        self.assertEqual(i18n._match_language("zh_Hant_TW", self.A), "zh")

    def test_priority_list(self):

        self.assertEqual(i18n._match_language("sv:da:pl:en", self.A), "pl")

    def test_list_falls_through_to_second(self):
        self.assertEqual(i18n._match_language("sv:fr", self.A), "fr")

    def test_three_letter_iso639_2(self):
        self.assertEqual(i18n._match_language("deu_DE", self.A), "de")
        self.assertEqual(i18n._match_language("fra_FR", self.A), "fr")
        self.assertEqual(i18n._match_language("zho_CN", self.A), "zh")

    def test_bare_code(self):
        self.assertEqual(i18n._match_language("de", self.A), "de")

    def test_uppercase(self):
        self.assertEqual(i18n._match_language("DE_de", self.A), "de")

    def test_windows_native_names_do_not_match(self):
        for tag in ("German_Germany", "French_France", "Russian_Russia",
                    "Spanish_Spain", "Italian_Italy", "Portuguese_Brazil",
                    "Japanese_Japan", "Polish_Poland", "Chinese_China"):
            with self.subTest(tag=tag):
                self.assertIsNone(
                    i18n._match_language(tag, self.A),
                    f"{tag} не должен match-иться: это не ISO-код",
                )

    def test_unmatchable_tags(self):
        for tag in ("C", "POSIX", "", None, "   "):
            with self.subTest(tag=tag):
                self.assertIsNone(i18n._match_language(tag, self.A))

    def test_unsupported_language_returns_none(self):

        self.assertIsNone(i18n._match_language("nl_NL", self.A))

    def test_no_prefix_confusion(self):
        self.assertIsNone(i18n._match_language("zzzz", i18n.LANGUAGES))
        self.assertIsNone(i18n._match_language("xyzzy_QQ", i18n.LANGUAGES))

        self.assertIsNone(i18n._match_language("p", i18n.LANGUAGES))
        self.assertEqual(i18n._match_language("pl", i18n.LANGUAGES), "pl")

    def test_drop_in_language_is_matched(self):

        avail = dict(i18n.LANGUAGES)
        avail["nl"] = "Nederlands"
        self.assertEqual(i18n._match_language("nl_NL", avail), "nl")


class TestDetectLanguage(unittest.TestCase):


    def test_all_ten_languages_detected(self):

        cases = {
            "de_DE": "de", "fr_FR": "fr", "es_ES": "es", "it_IT": "it",
            "pt_BR": "pt", "ja_JP": "ja", "pl_PL": "pl", "zh_CN": "zh",
            "ru_RU": "ru", "en_US": "en",
        }
        for tag, want in cases.items():
            with self.subTest(locale=tag):
                self.assertEqual(_detect_with(tag), want)

    def test_falls_back_to_next_probe(self):
        self.assertEqual(_detect_with("German_Germany", "de_DE"), "de")

    def test_unsupported_locale_gives_english(self):
        self.assertEqual(_detect_with("nl_NL"), "en")

    def test_no_probes_gives_english(self):
        self.assertEqual(_detect_with(), "en")

    def test_empty_probes_give_english(self):
        self.assertEqual(_detect_with("", None), "en")

    def test_real_system_detection_works(self):

        result = i18n.detect_language()
        self.assertIn(result, i18n.LANGUAGES, f"получен неизвестный код {result!r}")


class TestProbesSources(unittest.TestCase):


    def test_qt_locale_is_probed(self):
        probes = i18n._language_probes()
        self.assertTrue(probes, "ни один источник не опробован")

        self.assertRegex(probes[0], r"^[a-z]{2}([_-][A-Za-z]+)?$")

    def test_deprecated_getdefaultlocale_not_used(self):
        import ast

        tree = ast.parse(Path(i18n.__file__).read_text(encoding="utf-8"))
        offenders = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr == "getdefaultlocale":
                    offenders.append(f"строка {node.lineno}")
            if isinstance(node, ast.Name):
                if node.id == "getdefaultlocale":
                    offenders.append(f"строка {node.lineno}")

        self.assertEqual(
            offenders,
            [],
            "locale.getdefaultlocale() больше не должен вызываться: " + str(offenders),
        )

    def test_env_vars_considered(self):
        with mock.patch.dict("os.environ", {"LANG": "fr_FR.UTF-8"}, clear=False):
            probes = i18n._language_probes()
        self.assertIn("fr_FR.UTF-8", probes)

    def test_language_priority_env(self):
        with mock.patch.dict("os.environ", {"LANGUAGE": "pl:de"}, clear=False):
            probes = i18n._language_probes()
        self.assertIn("pl:de", probes)

    def test_getlocale_failure_is_survived(self):
        with mock.patch("ui.i18n.locale.getlocale", side_effect=ValueError("boom")):
            probes = i18n._language_probes()
        self.assertTrue(probes)


if __name__ == "__main__":
    unittest.main()
