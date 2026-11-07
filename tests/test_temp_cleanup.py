





from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.temp_cleanup import (
    TEMP_PREFIXES,
    cleanup_stale_temp,
    is_stale,
    remove_temp_dir,
)


def _age(path: Path, seconds: float) -> None:
    pass
    t = time.time() - seconds
    os.utime(path, (t, t))


class TestCleanupStaleTemp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _make(self, name: str) -> Path:
        p = self.root / name
        p.mkdir(parents=True, exist_ok=True)
        return p

    def test_removes_old_rizpaq_dir(self):
        d = self._make("rizpaq_open_abc")
        (d / "file.txt").write_text("data", encoding="utf-8")
        _age(d, 7200)

        removed = cleanup_stale_temp(max_age=3600, temp_root=str(self.root))

        self.assertIn(str(d), removed)
        self.assertFalse(d.exists(), "старая папка должна быть удалена")

    def test_keeps_fresh_dir(self):
        pass
        d = self._make("rizpaq_open_fresh")

        cleanup_stale_temp(max_age=3600, temp_root=str(self.root))

        self.assertTrue(d.exists(), "свежая папка не должна удаляться")

    def test_keeps_foreign_dir(self):
        pass
        d = self._make("some_other_app_data")
        _age(d, 7200)

        cleanup_stale_temp(max_age=3600, temp_root=str(self.root))

        self.assertTrue(d.exists(), "чужая папка не должна удаляться")

    def test_ignores_nested_rizpaq_dir(self):
        pass
        outer = self._make("container")
        inner = outer / "rizpaq_open_nested"
        inner.mkdir()
        _age(inner, 7200)

        cleanup_stale_temp(max_age=3600, temp_root=str(self.root))

        self.assertTrue(inner.exists(), "вложенная папка не должна удаляться")

    def test_ignores_files_with_prefix(self):
        pass
        f = self.root / "rizpaq_open_file.txt"
        f.write_text("x", encoding="utf-8")
        _age(f, 7200)

        cleanup_stale_temp(max_age=3600, temp_root=str(self.root))

        self.assertTrue(f.exists(), "файл не должен удаляться")

    def test_ignores_prefix_lookalike(self):
        pass



        d = self._make("my_rizpaq_open_x")
        _age(d, 7200)

        cleanup_stale_temp(max_age=3600, temp_root=str(self.root))

        self.assertTrue(d.exists(), "папка с префиксом не в начале не наша")

    def test_dry_run_reports_but_keeps(self):
        d = self._make("rizpaq_open_dry")
        _age(d, 7200)

        removed = cleanup_stale_temp(max_age=3600, temp_root=str(self.root), dry_run=True)

        self.assertIn(str(d), removed)
        self.assertTrue(d.exists(), "dry_run не должен ничего удалять")

    def test_custom_prefixes(self):
        d = self._make("custom_app_temp")
        _age(d, 7200)

        removed = cleanup_stale_temp(
            max_age=3600, prefixes=("custom_app_",), temp_root=str(self.root)
        )

        self.assertIn(str(d), removed)
        self.assertFalse(d.exists())

    def test_missing_root_is_not_fatal(self):
        removed = cleanup_stale_temp(
            max_age=3600, temp_root=str(self.root / "does_not_exist")
        )
        self.assertEqual(removed, [])

    def test_real_temp_dir_used_by_default(self):
        pass
        removed = cleanup_stale_temp(max_age=999999)
        self.assertIsInstance(removed, list)

    def test_covers_all_known_prefixes(self):
        pass



        for prefix in TEMP_PREFIXES:
            with self.subTest(prefix=prefix):
                d = self._make(prefix + "case")
                _age(d, 7200)

                cleanup_stale_temp(max_age=3600, temp_root=str(self.root))

                self.assertFalse(
                    d.exists(), f"папка с префиксом {prefix} не была удалена"
                )


class TestIsStale(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_fresh_not_stale(self):
        self.assertFalse(is_stale(self.root, 3600))

    def test_old_is_stale(self):
        _age(self.root, 7200)
        self.assertTrue(is_stale(self.root, 3600))

    def test_missing_path_not_stale(self):
        self.assertFalse(is_stale(self.root / "nope", 3600))


class TestRemoveTempDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_removes_owned_dir(self):
        d = self.root / "rizpaq_open_now"
        d.mkdir()
        (d / "f.txt").write_text("x", encoding="utf-8")

                                             
        import core.temp_cleanup as tc

        original = tc.tempfile.gettempdir
        tc.tempfile.gettempdir = lambda: str(self.root)
        try:
            ok = remove_temp_dir(d)
        finally:
            tc.tempfile.gettempdir = original

        self.assertTrue(ok)
        self.assertFalse(d.exists())

    def test_refuses_foreign_dir(self):
        d = self.root / "not_ours"
        d.mkdir()

        import core.temp_cleanup as tc

        original = tc.tempfile.gettempdir
        tc.tempfile.gettempdir = lambda: str(self.root)
        try:
            ok = remove_temp_dir(d)
        finally:
            tc.tempfile.gettempdir = original

        self.assertFalse(ok, "чужая папка не должна удаляться")
        self.assertTrue(d.exists())

    def test_refuses_path_outside_temp(self):
        pass
        import core.temp_cleanup as tc

        original = tc.tempfile.gettempdir
        tc.tempfile.gettempdir = lambda: str(self.root / "other_temp")
        try:
            ok = remove_temp_dir(self.root / "rizpaq_open_outside")
        finally:
            tc.tempfile.gettempdir = original

        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
