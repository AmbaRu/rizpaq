










from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ui.archive_actions as aa              
from core.incomplete_archive import incomplete_archive_action              


class _Stub:
    pass

    def __init__(self):
        self.status_messages: list = []
        self.logged: list = []

    def statusBar(self):
        return self

    def showMessage(self, msg):
        self.status_messages.append(msg)

    def log_output(self, text):
        self.logged.append(text)


class _FakeBox:
    pass

    def __init__(self):
        self.calls: list = []

    def warning(self, parent, title, text):
        self.calls.append(("warning", title, text))

    def information(self, parent, title, text):
        self.calls.append(("information", title, text))


class TestIncompleteArchive(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rizpaq_inc_"))
        self.addCleanup(lambda: _rmtree(self.tmp))
        self.stub = _Stub()
        self.box = _FakeBox()
        self._real_box = aa.QMessageBox
        self._real_tr = aa.tr
        aa.QMessageBox = self.box
                                                                            
                                                                        
                                                        
        aa.tr = lambda key, **kw: f"[{key}|{kw}]"
        self.addCleanup(setattr, aa, "QMessageBox", self._real_box)
        self.addCleanup(setattr, aa, "tr", self._real_tr)

    def _call(self, dest, is_update, output=""):
        aa.ArchiveActionsMixin._handle_incomplete_archive(
            self.stub, str(dest), is_update, output)

    def _file(self, name="out.zpaq", size=1024):
        p = self.tmp / name
        p.write_bytes(b"x" * size)
        return p

    def test_missing_file_is_noop(self):
        pass
        self._call(self.tmp / "нет.zpaq", False)
        self.assertEqual(self.box.calls, [], "диалог не должен появляться")
        self.assertEqual(self.stub.status_messages, [])

    def test_new_archive_is_deleted(self):
        pass


        p = self._file()
        self._call(p, False)
        self.assertFalse(p.exists(), "неполный файл обязан быть удалён")
        self.assertEqual(len(self.box.calls), 0,
                         "предупреждать не нужно: удалять безопасно")
        self.assertTrue(self.stub.status_messages,
                        "пользователь должен узнать, что файл удалён")
        self.assertIn("create.incomplete_deleted",
                      self.stub.status_messages[0],
                      "в статус-баре должно быть сказано про удаление")

    def test_existing_archive_is_kept(self):
        pass





        p = self._file()
        engine_text = ("Detected a 'gap' in the archive due to incomplete "
                       "transaction(s) 1\nSuggestion: use the trim command ASAP")
        self._call(p, True, engine_text)
        self.assertTrue(p.exists(),
                        "существовавший архив удалять нельзя — это потеря данных")
        self.assertEqual(len(self.box.calls), 1)
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("trim", text.lower(),
                      "совет движка обязан дойти до пользователя")
        self.assertIn(engine_text[-60:], text,
                      "текст ошибки движка должен быть показан целиком")

    def test_delete_failure_warns_and_keeps(self):
        pass
        p = self._file()
        real_unlink = Path.unlink

        def boom(self, *a, **k):
            raise OSError("доступ запрещён")

        with mock.patch.object(Path, "unlink", boom):
            self._call(p, False)
        self.assertTrue(p.exists(), "при неудаче удаления файл остаётся")
        self.assertEqual(len(self.box.calls), 1)
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("create.incomplete_delete_error", text,
                      "должен быть запрошен ключ про неудачу удаления")
        self.assertIn("доступ запрещён", text,
                      "причина неудачи обязана дойти до пользователя")

    def test_existing_archive_without_engine_text(self):
        pass
        p = self._file()
        self._call(p, True, "")
        self.assertTrue(p.exists())
        self.assertEqual(len(self.box.calls), 1)
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertTrue(text, "пустое предупреждение бесполезно")


class TestIncompleteArchiveDecision(unittest.TestCase):
    pass






    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rizpaq_dec_"))
        self.addCleanup(lambda: _rmtree(self.tmp))

    def test_missing_file_is_nothing(self):
        got = incomplete_archive_action(str(self.tmp / "нет.zpaq"), False)
        self.assertEqual(got["action"], "none")

    def test_new_file_is_deleted(self):
        p = self.tmp / "new.zpaq"
        p.write_bytes(b"x")
        got = incomplete_archive_action(str(p), existed_before=False)
        self.assertEqual(got["action"], "delete")

    def test_existing_file_is_kept(self):
        p = self.tmp / "old.zpaq"
        p.write_bytes(b"x")
        got = incomplete_archive_action(str(p), existed_before=True)
        self.assertEqual(got["action"], "keep",
                         "существовавший архив удалять нельзя")

    def test_directory_is_never_deleted(self):
        d = self.tmp / "папка.zpaq"
        d.mkdir()
        got = incomplete_archive_action(str(d), existed_before=False)
        self.assertEqual(got["action"], "keep",
                         "каталог удалять нельзя ни при каких условиях")
        self.assertTrue(d.exists())

    def test_reason_is_always_present(self):
        pass
        for dest, before in ((self.tmp / "a.zpaq", False),
                             (self.tmp / "b.zpaq", True)):
            dest.write_bytes(b"x")
            got = incomplete_archive_action(str(dest), before)
            self.assertTrue(got["reason"], got)


def _rmtree(p: Path):
    import shutil

    shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
