                       














from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dedup import archive_size_on_disk, dedup_stats


class TestDedupStats(unittest.TestCase):
    def test_empty_versions(self):
        stats = dedup_stats([], 100)
        self.assertEqual(stats["logical"], 0)
        self.assertEqual(stats["actual"], 100)
        self.assertEqual(stats["saved"], -100)
        self.assertEqual(stats["ratio"], 0.0)

    def test_none_versions(self):
        stats = dedup_stats(None, None)
        self.assertEqual(stats["logical"], 0)
        self.assertIsNone(stats["actual"])
        self.assertIsNone(stats["saved"])
        self.assertIsNone(stats["ratio"])

    def test_sums_bytes_added_from_objects(self):
        versions = [
            SimpleNamespace(bytes_added=100),
            SimpleNamespace(bytes_added=200),
            SimpleNamespace(bytes_added=300),
        ]
        stats = dedup_stats(versions, 300)
        self.assertEqual(stats["logical"], 600)
        self.assertEqual(stats["actual"], 300)
        self.assertEqual(stats["saved"], 300)
        self.assertEqual(stats["ratio"], 2.0)

    def test_accepts_dicts(self):
        versions = [{"bytes_added": 10}, {"bytes_added": 90}]
        stats = dedup_stats(versions, 50)
        self.assertEqual(stats["logical"], 100)
        self.assertEqual(stats["saved"], 50)
        self.assertEqual(stats["ratio"], 2.0)

    def test_bad_values_count_as_zero(self):
        versions = [
            SimpleNamespace(bytes_added="garbage"),
            SimpleNamespace(bytes_added=None),
            SimpleNamespace(bytes_added=-50),
            {"bytes_added": "???"},
            SimpleNamespace(bytes_added=7),
        ]
        stats = dedup_stats(versions, 10)
        self.assertEqual(stats["logical"], 7)

    def test_missing_bytes_added_attribute(self):
        stats = dedup_stats([SimpleNamespace(other=1)], None)
        self.assertEqual(stats["logical"], 0)

    def test_unknown_actual_keeps_saved_and_ratio_none(self):
        stats = dedup_stats([SimpleNamespace(bytes_added=100)], None)
        self.assertEqual(stats["logical"], 100)
        self.assertIsNone(stats["actual"])
        self.assertIsNone(stats["saved"])
        self.assertIsNone(stats["ratio"])

    def test_zero_actual_keeps_saved_and_ratio_none(self):
        pass
        stats = dedup_stats([SimpleNamespace(bytes_added=100)], 0)
        self.assertEqual(stats["actual"], 0)
        self.assertIsNone(stats["saved"])
        self.assertIsNone(stats["ratio"])

    def test_negative_actual_is_clamped(self):
        stats = dedup_stats([SimpleNamespace(bytes_added=100)], -5)
        self.assertEqual(stats["actual"], 0)
        self.assertIsNone(stats["saved"])

    def test_bool_is_not_a_size(self):
        stats = dedup_stats([SimpleNamespace(bytes_added=100)], True)
        self.assertIsNone(stats["actual"])

    def test_saved_can_be_negative(self):
        pass
        stats = dedup_stats([SimpleNamespace(bytes_added=10)], 50)
        self.assertEqual(stats["saved"], -40)
        self.assertEqual(stats["ratio"], 0.2)


class TestArchiveSizeOnDisk(unittest.TestCase):
    def _tmp(self):
        return tempfile.TemporaryDirectory(prefix="dedup_test_")

    def test_existing_file(self):
        with self._tmp() as tmp:
            path = Path(tmp) / "archive.zpaq"
            path.write_bytes(b"x" * 123)
            self.assertEqual(archive_size_on_disk(path), 123)

    def test_missing_file(self):
        with self._tmp() as tmp:
            path = Path(tmp) / "missing.zpaq"
            self.assertIsNone(archive_size_on_disk(path))

    def test_empty_path(self):
        self.assertIsNone(archive_size_on_disk(""))
        self.assertIsNone(archive_size_on_disk(None))

    def test_multivolume_sums_all_parts(self):
        with self._tmp() as tmp:
            base = Path(tmp)
            (base / "arc_0001.zpaq").write_bytes(b"a" * 10)
            (base / "arc_0002.zpaq").write_bytes(b"b" * 20)
            (base / "arc_0003.zpaq").write_bytes(b"c" * 30)
            (base / "other.zpaq").write_bytes(b"z" * 999)
            size = archive_size_on_disk(base / "arc_????.zpaq")
            self.assertEqual(size, 60)

    def test_multivolume_no_parts(self):
        with self._tmp() as tmp:
            size = archive_size_on_disk(Path(tmp) / "arc_????.zpaq")
            self.assertIsNone(size)

    def test_non_volume_path_with_wildcard_in_name(self):
        pass
        with self._tmp() as tmp:
            size = archive_size_on_disk(Path(tmp) / "arc_*.zpaq")
            self.assertIsNone(size)

    def test_star_mask(self):
        with self._tmp() as tmp:
            base = Path(tmp)
            (base / "one.zpaq").write_bytes(b"x" * 5)
            (base / "two.zpaq").write_bytes(b"x" * 7)
            self.assertEqual(
                archive_size_on_disk(base / "*.zpaq"), 12
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
