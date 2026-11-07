











from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.engine_path import move_to_dest              


class TestMoveToDest(unittest.TestCase):
    def setUp(self):
        import shutil
        import tempfile

        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_move_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.staged = self.dir / "черновик.tmp"
        self.dest = self.dir / "Итог" / "файл.txt"

    def test_moves_file(self):
        self.dest.parent.mkdir(parents=True)
        self.staged.write_text("содержимое", encoding="utf-8")

        ok, note = move_to_dest(str(self.staged), str(self.dest))

        self.assertTrue(ok, f"перенос не удался: {note}")
        self.assertTrue(self.dest.exists(), "файл не появился на месте")
        self.assertEqual(self.dest.read_text(encoding="utf-8"), "содержимое")
        self.assertFalse(self.staged.exists(), "черновик не убран")

    def test_does_not_overwrite_existing(self):
        pass





        self.dest.parent.mkdir(parents=True)
        self.dest.write_text("СТАРЫЕ ДАННЫЕ", encoding="utf-8")
        self.staged.write_text("новые данные", encoding="utf-8")

        ok, note = move_to_dest(str(self.staged), str(self.dest))

        self.assertFalse(ok, "перенос затёр существующий файл")
        self.assertEqual(
            self.dest.read_text(encoding="utf-8"), "СТАРЫЕ ДАННЫЕ",
            "содержимое существующего файла изменилось")
        self.assertTrue(
            self.staged.exists(),
            "черновик убран при отказе — извлечённые данные потеряны")
        self.assertIn(str(self.staged), note,
                      "в отказе не назван путь, где лежат данные")

    def test_missing_staged_reported(self):
        ok, note = move_to_dest(str(self.dir / "нет.tmp"), str(self.dest))
        self.assertFalse(ok)
        self.assertIn("черновик не найден", note)

    def test_copy_path_checks_size(self):
        pass




        import core.engine_path as ep

        real_replace = os.replace
                                                                           
        os.replace = lambda *a, **k: (_ for _ in ()).throw(OSError("тома"))
        self.addCleanup(setattr, os, "replace", real_replace)

        self.dest.parent.mkdir(parents=True)
        self.staged.write_text("данные", encoding="utf-8")

                                                                        
        import shutil as _sh

        real_copy = _sh.copy2

        def short_copy(src, dst, *a, **k):
            _sh.copyfile(src, dst)
            with open(dst, "r+b") as fh:
                fh.truncate(2)

        _sh.copy2 = short_copy
        self.addCleanup(setattr, _sh, "copy2", real_copy)

        ok, note = move_to_dest(str(self.staged), str(self.dest))

        self.assertFalse(ok, "несовпадение размера не замечено")
        self.assertIn("размер", note.lower())
        self.assertTrue(
            self.staged.exists(),
            "черновик убран при несовпадении размера — данные потеряны")
        _ = ep                                           

    def test_copy_path_succeeds(self):
        pass
                                                                      
                                                                           
                                                                         
                                                                          
                                                                        
                                                                      
                                                    
        real_replace = os.replace
        os.replace = lambda *a, **k: (_ for _ in ()).throw(OSError("тома"))
        self.addCleanup(setattr, os, "replace", real_replace)

        self.dest.parent.mkdir(parents=True)
        self.staged.write_text("данные", encoding="utf-8")

        ok, note = move_to_dest(str(self.staged), str(self.dest))

        self.assertTrue(ok, f"копирование не удалось: {note}")
        self.assertEqual(self.dest.read_text(encoding="utf-8"), "данные")
        self.assertFalse(self.staged.exists(), "черновик не убран")

    def test_replace_is_actually_restored(self):
        pass





        import shutil as _sh
        import tempfile

        real = os.replace
        d = Path(tempfile.mkdtemp(prefix="rizpaq_restore_"))
        self.addCleanup(_sh.rmtree, d, ignore_errors=True)
        (d / "a").write_text("a", encoding="utf-8")

                                                                         
        for dest in (d / "b", d / "c"):
            staged = d / f"s_{dest.name}"
            staged.write_text("данные", encoding="utf-8")
            move_to_dest(str(staged), str(dest))

        self.assertIs(
            os.replace, real,
            "os.replace не восстановлен — тесты портят чужие тесты")


if __name__ == "__main__":
    unittest.main()
