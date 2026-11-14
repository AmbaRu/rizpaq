





































from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication              

import ui.i18n as i18n              
from ui.i18n import set_language, tr              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ROOT / "locales"

                                                          
                                                             
                                                       
ALL_LANGS = ("de", "en", "es", "fr", "it", "ja", "pl", "pt", "ru", "zh")

                                                                   
                                                            
                                                 
BASE_LANGS = ("ru", "en")


class TestLocaleFilesAreValidJson(unittest.TestCase):
    pass

    def test_all_locale_files_parse(self):
        broken = []
        for path in sorted(LOCALES.glob("*.json")):
            with self.subTest(locale=path.name):
                try:
                    json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    broken.append(f"{path.name}: {exc}")
        self.assertEqual(
            broken, [], f"НЕВАЛИДНЫЙ JSON в локалях:\n" + "\n".join(broken)
        )

    def test_every_declared_language_has_file(self):
        for code in ALL_LANGS:
            with self.subTest(lang=code):
                self.assertTrue(
                    (LOCALES / f"{code}.json").is_file(),
                    f"нет файла локали для языка {code}",
                )

    def test_locales_have_strings_object(self):
        for path in sorted(LOCALES.glob("*.json")):
            with self.subTest(locale=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertIn("strings", data, f"{path.name}: нет 'strings'")
                self.assertIsInstance(data["strings"], dict)


class TestNoMissingTranslations(unittest.TestCase):
    pass





    @staticmethod
    def _keys_used_in_code() -> set:
        pass













        literal_re = re.compile(r"\btr\(\s*[\"']([^\"']+)[\"']")
                                                                     
                                                                      
                                                     
                                                                    
        text_key_re = re.compile(r"\btext_key\s*=\s*[\"']([^\"']+)[\"']")
        skip_dirs = {"__pycache__", "build", "dist", "locales", "tools", "tests"}
        root = ROOT
        used = set()
        for path in root.rglob("*.py"):
            if any(part in skip_dirs for part in path.relative_to(root).parts):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            used |= set(literal_re.findall(text))
            used |= set(text_key_re.findall(text))

                                                                  
                                                         
        used = {
            k for k in used
            if k and k.strip() and k != "..." and " " not in k
        }
        return used

    def test_every_used_key_is_translated_in_all_languages(self):
        used = self._keys_used_in_code()
        problems = []
        for code in ALL_LANGS:
            path = LOCALES / f"{code}.json"
            strings = json.loads(path.read_text(encoding="utf-8"))["strings"]
            for key in sorted(used - set(strings)):
                problems.append(f"{code}: нет перевода для {key}")
        self.assertEqual(problems, [], "\n".join(problems))

    def test_new_keys_present_explicitly(self):
        pass








        explicit = (
                           
            "check.archive",
            "check.dest_missing",
            "check.dialog_title",
            "check.log_full",
            "check.log_mode",
            "check.log_none",
            "check.log_short",
            "check.mode",
            "check.mode_checksum",
            "check.mode_full",
            "check.mode_hint",
            "check.mode_paranoid",
            "check.mode_verify",
            "check.password",
            "check.password_not_set",
            "check.password_set",
            "check.title",
            "check.title_placeholder",
                         
            "work.dialog_title",
            "work.edit_title",
            "work.password_clear",
            "work.password_confirm",
            "work.password_enter",
            "work.password_set",
                                     
            "context.edit_work",
            "context.add_backup_job",
            "context.add_check_job",
                                          
            "create.work_title",
            "create.work_title_placeholder",
            "create.job_title",
            "create.job_title_placeholder",
        )
        problems = []
        for code in ALL_LANGS:
            strings = json.loads(
                (LOCALES / f"{code}.json").read_text(encoding="utf-8")
            )["strings"]
            for key in explicit:
                if key not in strings:
                    problems.append(f"{code}: нет ключа {key}")
        self.assertEqual(
            problems, [],
            "Ключи из явного списка должны быть во всех языках:\n"
            + "\n".join(problems),
        )

    def test_placeholders_match_english(self):
        pass





        en_strings = json.loads(
            (LOCALES / "en.json").read_text(encoding="utf-8")
        )["strings"]
        ph_re = re.compile(r"\{([A-Za-z0-9_]+)\}")

        problems = []
        for code in ALL_LANGS:
            if code == "en":
                continue
            strings = json.loads(
                (LOCALES / f"{code}.json").read_text(encoding="utf-8")
            )["strings"]
            for key, value in strings.items():
                if key in en_strings and (
                    set(ph_re.findall(value))
                    != set(ph_re.findall(en_strings[key]))
                ):
                    problems.append(f"{code}: плейсхолдеры {key}")
        self.assertEqual(problems, [], "\n".join(problems))

    def test_no_empty_translation_values(self):
        pass
        problems = []
        for code in ALL_LANGS:
            strings = json.loads(
                (LOCALES / f"{code}.json").read_text(encoding="utf-8")
            )["strings"]
            for key, value in strings.items():
                if not isinstance(value, str) or not value.strip():
                    problems.append(f"{code}: пустое значение для {key}")
        self.assertEqual(problems, [], "\n".join(problems))


class TestBaseLanguagesAlwaysLoad(unittest.TestCase):
    pass





    def setUp(self):
        self._lang = i18n._current_lang
        self._strings = i18n._current_strings

    def tearDown(self):
        i18n._current_lang = self._lang
        i18n._current_strings = self._strings

    def test_base_languages_not_empty(self):
        for code in BASE_LANGS:
            with self.subTest(lang=code):
                set_language(code, locales_dir=str(LOCALES), notify=False)
                self.assertGreater(
                    len(i18n._current_strings), 0,
                    f"язык {code} загрузился пустым",
                )

    def test_base_languages_have_all_used_keys(self):
        pass







        used = TestNoMissingTranslations._keys_used_in_code()
        problems = []
        for code in BASE_LANGS:
            strings = json.loads(
                (LOCALES / f"{code}.json").read_text(encoding="utf-8")
            )["strings"]
            for key in sorted(used - set(strings)):
                problems.append(f"{code}: нет перевода для {key}")
        self.assertEqual(problems, [], "\n".join(problems))


class TestEveryLanguageLoadsText(unittest.TestCase):
    pass

    def setUp(self):
        self._lang = i18n._current_lang
        self._strings = i18n._current_strings

    def tearDown(self):
        i18n._current_lang = self._lang
        i18n._current_strings = self._strings

    def _probes(self):
        pass





        en = json.loads(
            (LOCALES / "en.json").read_text(encoding="utf-8")
        )["strings"]
        bin_key = next((k for k, v in en.items() if "{bin}" in v), None)
        probes = [
            ("status.cancel_none", {}),
            ("menu.file.exit", {}),
            ("open.nonlatin_offer_text", {"old": "A", "new": "B"}),
            ("table.not_found", {"query": "x"}),
                                                                   
                      
            ("check.dialog_title", {}),
            ("check.mode_full", {}),
            ("work.password_set", {}),
            ("context.edit_work", {}),
            ("create.work_title", {}),
        ]
        if bin_key:
            probes.append((bin_key, {"bin": "7z.exe"}))
        return probes

    def test_languages_produce_text(self):
        probes = self._probes()
        problems = []
        for code in ALL_LANGS:
            set_language(code, locales_dir=str(LOCALES), notify=False)
            for key, ph in probes:
                got = tr(key, **ph)
                if got == key:
                    problems.append(f"{code}: {key} вернул сам ключ")
        self.assertEqual(problems, [], "\n".join(problems))

    def test_no_language_loads_empty(self):
        pass
        for code in ALL_LANGS:
            with self.subTest(lang=code):
                set_language(code, locales_dir=str(LOCALES), notify=False)
                self.assertGreater(
                    len(i18n._current_strings),
                    0,
                    f"язык {code} загрузился пустым",
                )

    def test_active_language_sticks(self):
        for code in ALL_LANGS:
            with self.subTest(lang=code):
                set_language(code, locales_dir=str(LOCALES), notify=False)
                self.assertEqual(
                    i18n._current_lang,
                    code,
                    f"после set_language({code}) активен {i18n._current_lang}",
                )

    def test_all_declared_languages_available(self):
        pass



        available = i18n.available_languages()
        for code in ALL_LANGS:
            with self.subTest(lang=code):
                self.assertIn(
                    code, available,
                    f"язык {code} не виден в available_languages()",
                )


class TestBrokenLanguageFallsBackToEnglish(unittest.TestCase):
    pass





    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / "en.json").write_text(
            (LOCALES / "en.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def _broken(self, code: str = "xx") -> Path:
                                                                         
        p = self.dir / f"{code}.json"
        p.write_text(
            '{"_meta":{"name":"Broken"},'
            '"strings":{"a":"broken "quote" here"}}',
            encoding="utf-8",
        )
        return p

    def test_broken_language_falls_back_to_english(self):
        self._broken()
        set_language("xx", locales_dir=self.dir, notify=False)

        self.assertEqual(i18n._current_lang, "en")
        self.assertGreater(len(i18n._current_strings), 0)
        self.assertNotEqual(
            tr("status.cancel_none"),
            "status.cancel_none",
            "интерфейс показывает сырые ключи вместо английского текста",
        )

    def test_broken_language_is_reported(self):
        self._broken()
        set_language("xx", locales_dir=self.dir, notify=False)

        self.assertIn(
            "xx", i18n.load_errors, "причина отказа не записана в load_errors"
        )

    def test_healthy_language_does_not_report_error(self):
        (self.dir / "yy.json").write_text(
            '{"_meta":{"name":"Fine"},"strings":{"status.cancel_none":"ok"}}',
            encoding="utf-8",
        )
        set_language("yy", locales_dir=self.dir, notify=False)

        self.assertEqual(i18n._current_lang, "yy")
        self.assertEqual(i18n.load_errors, {})

    def test_missing_english_is_not_fatal(self):
        pass
        (self.dir / "en.json").unlink()
        set_language("en", locales_dir=self.dir, notify=False)
        self.assertEqual(i18n._current_lang, "en")

    def test_missing_keys_come_from_english(self):
        pass
        (self.dir / "zz.json").write_text(
            '{"_meta":{"name":"Tiny"},"strings":{"menu.file.exit":"EXIT"}}',
            encoding="utf-8",
        )
        set_language("zz", locales_dir=self.dir, notify=False)

        self.assertEqual(i18n._current_lang, "zz")
        self.assertEqual(tr("menu.file.exit"), "EXIT")
                                                                              
        self.assertNotEqual(tr("status.cancel_none"), "status.cancel_none")


if __name__ == "__main__":
    unittest.main()
