






from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core import zpaq_help

MD = """# Справочник

## Основные команды

### a - Добавить файлы в архив

Текст про `a`.

### gui / tui - Текстовый интерфейс

Текст про GUI.
"""

BUILTIN = """zpaqfranz v65.20
CMD a               (add) / добавить файлы
-verbose            Подробный вывод
--------------------------
CMD cloud           Выгрузка через SFTP
CMD grep            Поиск текста в файлах
--------------------------
"""


class TestZpaqHelp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.doc = self.base / "doc"
        self.doc.mkdir()
        (self.doc / zpaq_help.REFERENCE_NAME).write_text(MD, encoding="utf-8")
        (self.doc / zpaq_help.BUILTIN_NAME).write_text(BUILTIN, encoding="utf-8")

        self.patches = [
            mock.patch.object(zpaq_help, "_project_doc", return_value=self.doc),
            mock.patch.object(
                zpaq_help, "_exe_dir", return_value=self.base / "nowhere"
            ),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_find_root_and_paths(self):
        self.assertEqual(zpaq_help.find_reference_root(), self.doc)
        self.assertTrue(zpaq_help.reference_path().name.endswith(".md"))
        self.assertTrue(
            zpaq_help.builtin_path().name.endswith("builtin-ru.txt")
        )

    def test_no_files_returns_none(self):
        with mock.patch.object(zpaq_help, "_project_doc", return_value=self.base / "x"), \
             mock.patch.object(zpaq_help, "_exe_dir", return_value=self.base / "y"):
            self.assertIsNone(zpaq_help.find_reference_root())
            self.assertIsNone(zpaq_help.lookup("a"))

    def test_commands_merge_both_sources(self):
        names = dict(zpaq_help.commands())
        self.assertIn("a", names)
        self.assertIn("cloud", names)
        self.assertIn("gui", names)
        self.assertIn("tui", names)
                                                                           
        self.assertIn("Добавить файлы в архив", names["a"])

    def test_lookup_from_markdown(self):
        found = zpaq_help.lookup("a")
        self.assertIsNotNone(found)
        self.assertEqual(found["source"], zpaq_help.REFERENCE_NAME)
        self.assertIn("Текст про `a`", found["text"])
        self.assertNotIn("### a -", found["text"])

    def test_lookup_alias_and_builtin_fallback(self):
        gui = zpaq_help.lookup("tui")
        self.assertEqual(gui["source"], zpaq_help.REFERENCE_NAME)
        cloud = zpaq_help.lookup("cloud")
        self.assertEqual(cloud["source"], zpaq_help.BUILTIN_NAME)
        self.assertIn("SFTP", cloud["title"])

    def test_lookup_ignores_dash_and_extra_words(self):
        self.assertIsNotNone(zpaq_help.lookup("a -verbose"))
        self.assertIsNone(zpaq_help.lookup(""))
        self.assertIsNone(zpaq_help.lookup("no_such_command"))

    def test_search(self):
        self.assertTrue(zpaq_help.search("a"))
        names = {item["name"] for item in zpaq_help.search("sftp")}
        self.assertIn("cloud", names)
        self.assertEqual(zpaq_help.search("nothing-here-123"), [])


if __name__ == "__main__":
    unittest.main()
