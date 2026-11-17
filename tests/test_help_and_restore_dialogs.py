






from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    from PySide6.QtWidgets import QApplication

    from core import zpaq_help
    from ui.command_help_dialog import CommandHelpDialog
    from ui.restore_revision_dialog import RestoreRevisionDialog

    IMPORT_ERROR = None
except Exception as exc:
    QApplication = None
    CommandHelpDialog = None
    RestoreRevisionDialog = None
    IMPORT_ERROR = str(exc)

MD = """# Справочник

## Команды

### a - Добавить файлы в архив

Текст про команду a.

### cloud - Выгрузка через SFTP

Текст про облако.
"""

BUILTIN = """zpaqfranz v65.20
CMD a               (add) / добавить файлы
CMD grep            Поиск текста в файлах
--------------------------
"""


@unittest.skipIf(QApplication is None, f"PySide6 import failed: {IMPORT_ERROR}")
class TestNewDialogs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_command_help_dialog(self):
        with tempfile.TemporaryDirectory() as td:
            doc = Path(td) / "doc"
            doc.mkdir()
            (doc / zpaq_help.REFERENCE_NAME).write_text(MD, encoding="utf-8")
            (doc / zpaq_help.BUILTIN_NAME).write_text(BUILTIN, encoding="utf-8")
            with mock.patch.object(zpaq_help, "_project_doc", return_value=doc), \
                 mock.patch.object(
                     zpaq_help, "_exe_dir", return_value=Path(td) / "nowhere"
                 ):
                dlg = CommandHelpDialog()
                self.assertGreater(dlg.list.count(), 2)
                self.assertIn("a", dlg.text.toPlainText().lower())

                dlg.search.setText("cloud")
                self.assertGreaterEqual(dlg.list.count(), 1)
                self.assertIn("cloud", dlg.list.item(0).text().lower())

    def test_restore_revision_dialog(self):
        dlg = RestoreRevisionDialog()
        self.assertEqual(dlg.mode(), "date")
        dlg.date_edit.setText("2026-01-15")
        self.assertEqual(dlg.until(), "2026-01-15 23:59:59")

        dlg.all_radio.setChecked(True)
        self.assertEqual(dlg.mode(), "all")
        self.assertEqual(dlg.until(), "")


if __name__ == "__main__":
    unittest.main()
