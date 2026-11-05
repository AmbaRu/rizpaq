from __future__ import annotations

import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import archive_index as idx
from core.models import ArchiveEntry


def _entry(
    path: str,
    size: int = 100,
    version=None,
    flag: str = "+",
    is_dir: bool = False,
    dt: str = "2026-10-09 12:00:00",
) -> ArchiveEntry:

    return ArchiveEntry(
        path=path,
        size=size,
        datetime=dt,
        version=version,
        flag=flag,
        is_dir=is_dir,
    )


class IndexTestBase(unittest.TestCase):


    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="rizpaq_index_test_"))
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.path = self._tmp / "archive_index.sqlite"
        idx._set_index_path_for_tests(self.path)


        self.addCleanup(idx.close)
        self.addCleanup(idx._set_index_path_for_tests, None)

    def _store(self, archive: str, entries: list,
               mtime_ns: int = 111, size: int = 222) -> None:
        idx.store_entries(str(archive), mtime_ns, size, entries)

    def _load(self, archive: str):
        return idx.load_entries(str(archive))


class TestIndexPath(unittest.TestCase):
    def test_in_config_dir_by_default(self):

        idx._set_index_path_for_tests(None)
        p = idx.index_path()
        self.assertEqual(p.name, idx.INDEX_FILENAME)

        try:
            from core.config import default_path

            self.assertEqual(p.parent, default_path().parent)
        except Exception:


            self.assertTrue(p.name.endswith(".sqlite"))


class TestEmptyIndex(IndexTestBase):
    def test_load_returns_none_when_nothing_stored(self):

        self.assertIsNone(self._load("C:/arc.zpaq"))

    def test_is_fresh_false_when_nothing_stored(self):
        self.assertFalse(idx.is_fresh("C:/arc.zpaq", 1, 1))


class TestStoreLoad(IndexTestBase):
    def test_roundtrip_preserves_all_fields(self):
        entries = [
            _entry("d:/a.txt", size=10, version=1),
            _entry("d:/b.txt", size=20, version=2),
            _entry("d:/folder", size=0, version=1, is_dir=True),
        ]
        self._store("C:/arc.zpaq", entries)

        loaded = self._load("C:/arc.zpaq")
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded), 3)


        self.assertEqual(loaded[0].path, "d:/a.txt")
        self.assertEqual(loaded[1].path, "d:/b.txt")
        self.assertEqual(loaded[2].path, "d:/folder")

        self.assertEqual(loaded[0].size, 10)
        self.assertEqual(loaded[0].version, 1)
        self.assertTrue(loaded[2].is_dir)
        self.assertEqual(loaded[2].version, 1)

    def test_version_none_roundtrips(self):
        entries = [_entry("d:/a.txt", size=10, version=None)]
        self._store("C:/arc.zpaq", entries)

        loaded = self._load("C:/arc.zpaq")
        self.assertEqual(len(loaded), 1)
        self.assertIsNone(loaded[0].version)

    def test_empty_list_stores_and_loads_as_empty(self):
        self._store("C:/arc.zpaq", [])

        loaded = self._load("C:/arc.zpaq")
        self.assertIsNotNone(loaded, "запись есть, значит не None")
        self.assertEqual(loaded, [])

    def test_different_archives_do_not_mix(self):
        a = [_entry("d:/a.txt")]
        b = [_entry("d:/b.txt"), _entry("d:/c.txt")]
        self._store("C:/arc1.zpaq", a)
        self._store("C:/arc2.zpaq", b)

        self.assertEqual([e.path for e in self._load("C:/arc1.zpaq")], ["d:/a.txt"])
        self.assertEqual(
            [e.path for e in self._load("C:/arc2.zpaq")],
            ["d:/b.txt", "d:/c.txt"],
        )

    def test_unicode_paths_survive(self):

        entries = [
            _entry("d:/Документы/отчёт.xlsx"),
            _entry("d:/Музыка/песня.mp3"),
        ]
        self._store("C:/архив.zpaq", entries)

        loaded = self._load("C:/архив.zpaq")
        self.assertEqual(
            [e.path for e in loaded],
            ["d:/Документы/отчёт.xlsx", "d:/Музыка/песня.mp3"],
        )


class TestStoreOverwrites(IndexTestBase):
    def test_second_store_replaces_previous(self):
        self._store("C:/arc.zpaq", [_entry("d:/old1.txt"), _entry("d:/old2.txt")])
        self._store("C:/arc.zpaq", [_entry("d:/new.txt")])

        loaded = self._load("C:/arc.zpaq")
        self.assertEqual([e.path for e in loaded], ["d:/new.txt"])

    def test_store_with_empty_replaces_data(self):

        self._store("C:/arc.zpaq", [_entry("d:/a.txt")])
        self._store("C:/arc.zpaq", [])

        loaded = self._load("C:/arc.zpaq")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded, [])

    def test_position_resets_on_overwrite(self):
        self._store(
            "C:/arc.zpaq",
            [_entry("d:/x.txt"), _entry("d:/y.txt"), _entry("d:/z.txt")],
        )
        self._store(
            "C:/arc.zpaq",
            [_entry("d:/z.txt"), _entry("d:/y.txt"), _entry("d:/x.txt")],
        )
        loaded = self._load("C:/arc.zpaq")
        self.assertEqual([e.path for e in loaded],
                         ["d:/z.txt", "d:/y.txt", "d:/x.txt"])


class TestDuplicatePathInside(IndexTestBase):

    def test_versions_of_same_file_all_stored(self):
        entries = [
            _entry("d:/a.txt", size=10, version=1),
            _entry("d:/a.txt", size=20, version=2),
            _entry("d:/a.txt", size=30, version=3),
        ]
        self._store("C:/arc.zpaq", entries)

        loaded = self._load("C:/arc.zpaq")
        self.assertIsNotNone(loaded, "запись не сохранилась вовсе")
        self.assertEqual(len(loaded), 3, "должны сохраниться все три версии")

        versions = sorted(e.version for e in loaded)
        self.assertEqual(versions, [1, 2, 3])

    def test_mixed_duplicates_and_unique_paths(self):
        entries = [
            _entry("d:/a.txt", size=10, version=1),
            _entry("d:/b.txt", size=20, version=1),
            _entry("d:/a.txt", size=11, version=2),
            _entry("d:/c.txt", size=30, version=1),
            _entry("d:/b.txt", size=21, version=2),
        ]
        self._store("C:/arc.zpaq", entries)

        loaded = self._load("C:/arc.zpaq")
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded), 5)

        paths = [e.path for e in loaded]
        self.assertEqual(paths.count("d:/a.txt"), 2)
        self.assertEqual(paths.count("d:/b.txt"), 2)
        self.assertEqual(paths.count("d:/c.txt"), 1)

    def test_position_keeps_original_order(self):
        entries = [
            _entry("d:/a.txt", size=10, version=1),
            _entry("d:/a.txt", size=20, version=2),
            _entry("d:/a.txt", size=30, version=3),
        ]
        self._store("C:/arc.zpaq", entries)

        loaded = self._load("C:/arc.zpaq")
        self.assertEqual([e.version for e in loaded], [1, 2, 3])
        self.assertEqual([e.size for e in loaded], [10, 20, 30])


class TestFreshness(IndexTestBase):
    def test_fresh_after_store(self):
        self._store("C:/arc.zpaq", [_entry("d:/a.txt")],
                    mtime_ns=1000, size=5000)
        self.assertTrue(idx.is_fresh("C:/arc.zpaq", 1000, 5000))

    def test_stale_when_mtime_differs(self):
        self._store("C:/arc.zpaq", [_entry("d:/a.txt")],
                    mtime_ns=1000, size=5000)
        self.assertFalse(idx.is_fresh("C:/arc.zpaq", 1001, 5000))
        self.assertFalse(idx.is_fresh("C:/arc.zpaq", 999, 5000))

    def test_stale_when_size_differs(self):
        self._store("C:/arc.zpaq", [_entry("d:/a.txt")],
                    mtime_ns=1000, size=5000)
        self.assertFalse(idx.is_fresh("C:/arc.zpaq", 1000, 5001))
        self.assertFalse(idx.is_fresh("C:/arc.zpaq", 1000, 4999))

    def test_different_path_is_not_fresh(self):
        self._store("C:/arc1.zpaq", [_entry("d:/a.txt")],
                    mtime_ns=1000, size=5000)
        self.assertFalse(idx.is_fresh("C:/arc2.zpaq", 1000, 5000))


class TestForget(IndexTestBase):
    def test_forget_removes_archive_and_entries(self):
        self._store("C:/arc1.zpaq", [_entry("d:/a.txt")])
        self._store("C:/arc2.zpaq", [_entry("d:/b.txt")])

        idx.forget("C:/arc1.zpaq")

        self.assertIsNone(self._load("C:/arc1.zpaq"))
        self.assertFalse(idx.is_fresh("C:/arc1.zpaq", 111, 222))

        self.assertIsNotNone(self._load("C:/arc2.zpaq"))

    def test_forget_missing_is_silent(self):

        idx.forget("C:/no-such.zpaq")

    def test_forget_all_clears_everything(self):
        self._store("C:/arc1.zpaq", [_entry("d:/a.txt")])
        self._store("C:/arc2.zpaq", [_entry("d:/b.txt")])

        idx.forget_all()

        self.assertIsNone(self._load("C:/arc1.zpaq"))
        self.assertIsNone(self._load("C:/arc2.zpaq"))


class TestMultipartNotIndexed(IndexTestBase):

    def test_store_is_ignored(self):
        idx.store_entries(
            "C:/backup_????.zpaq", 1000, 5000, [_entry("d:/a.txt")]
        )


        self.assertIsNone(self._load("C:/backup_????.zpaq"))
        self.assertFalse(idx.is_fresh("C:/backup_????.zpaq", 1000, 5000))

    def test_load_and_fresh_skip_multipart(self):

        self.assertIsNone(self._load("C:/backup_????.zpaq"))
        self.assertFalse(idx.is_fresh("C:/backup_????.zpaq", 0, 0))

    def test_empty_path_is_skipped(self):

        self.assertIsNone(idx.load_entries(""))
        self.assertFalse(idx.is_fresh("", 0, 0))
        idx.store_entries("", 0, 0, [_entry("d:/a.txt")])


class TestConcurrentStores(IndexTestBase):

    def test_two_threads_write_different_archives(self):
        a_entries = [_entry(f"d:/a/{i}.txt", size=i) for i in range(50)]
        b_entries = [_entry(f"d:/b/{i}.txt", size=i) for i in range(50)]

        errors: list = []

        def write_a():
            try:
                idx.store_entries("C:/a.zpaq", 10, 20, a_entries)
            except Exception as exc:
                errors.append(("a", exc))

        def write_b():
            try:
                idx.store_entries("C:/b.zpaq", 30, 40, b_entries)
            except Exception as exc:
                errors.append(("b", exc))

        t1 = threading.Thread(target=write_a)
        t2 = threading.Thread(target=write_b)
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        self.assertEqual(errors, [])
        self.assertEqual(len(self._load("C:/a.zpaq")), 50)
        self.assertEqual(len(self._load("C:/b.zpaq")), 50)


class TestReopen(IndexTestBase):

    def test_data_survives_close_and_reopen(self):
        entries = [_entry("d:/a.txt", size=10, version=1)]
        self._store("C:/arc.zpaq", entries, mtime_ns=1000, size=5000)

        idx.close()

        loaded = self._load("C:/arc.zpaq")
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].path, "d:/a.txt")
        self.assertTrue(idx.is_fresh("C:/arc.zpaq", 1000, 5000))

    def test_schema_is_idempotent(self):
        self._store("C:/arc.zpaq", [_entry("d:/a.txt")])
        idx.close()
        self._store("C:/arc.zpaq", [_entry("d:/b.txt")])
        loaded = self._load("C:/arc.zpaq")
        self.assertEqual([e.path for e in loaded], ["d:/b.txt"])


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
