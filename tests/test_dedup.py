                       
















from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dedup import archive_size_on_disk, dedup_stats
from core.parser import parse_info_stat


class TestDedupStats(unittest.TestCase):
    def test_plain_archive(self):
        pass
        stats = dedup_stats(1_000_000, 300_000)
        self.assertEqual(stats["logical"], 1_000_000)
        self.assertEqual(stats["actual"], 300_000)
        self.assertEqual(stats["saved"], 700_000)
        self.assertAlmostEqual(stats["ratio"], 1_000_000 / 300_000, places=6)

    def test_no_compression(self):
        stats = dedup_stats(500, 500)
        self.assertEqual(stats["saved"], 0)
        self.assertEqual(stats["ratio"], 1.0)

    def test_unknown_size_keeps_saved_and_ratio_none(self):
        stats = dedup_stats(1000, None)
        self.assertEqual(stats["logical"], 1000)
        self.assertIsNone(stats["actual"])
        self.assertIsNone(stats["saved"])
        self.assertIsNone(stats["ratio"])

    def test_zero_size_keeps_saved_and_ratio_none(self):
        pass
        stats = dedup_stats(1000, 0)
        self.assertEqual(stats["actual"], 0)
        self.assertIsNone(stats["saved"])
        self.assertIsNone(stats["ratio"])

    def test_negative_size_is_clamped(self):
        stats = dedup_stats(1000, -5)
        self.assertEqual(stats["actual"], 0)
        self.assertIsNone(stats["saved"])

    def test_bool_is_not_a_size(self):
        stats = dedup_stats(1000, True)
        self.assertIsNone(stats["actual"])

    def test_none_uncompressed_is_zero(self):
        stats = dedup_stats(None, 500)
        self.assertEqual(stats["logical"], 0)
        self.assertEqual(stats["saved"], -500)

    def test_saved_can_be_negative(self):
        pass
        stats = dedup_stats(10, 50)
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

    def test_star_mask(self):
        with self._tmp() as tmp:
            base = Path(tmp)
            (base / "one.zpaq").write_bytes(b"x" * 5)
            (base / "two.zpaq").write_bytes(b"x" * 7)
            self.assertEqual(
                archive_size_on_disk(base / "*.zpaq"), 12
            )


class TestParseInfoStat(unittest.TestCase):
    pass





    REAL = """zpaqfranz v65.5g-JIT8+M,SFTP,RES-L,HW BLK3,SHA1/2,4,SFX64 55.1,(2026-09-28)

<<C:/tmp/arc.zpaq>>:
3 versions, 4 files, 3.667 bytes (3.58 KB)
Windows path                   4
----------------------------------------------------------------------------------------------
<  Ver  > <  date  > <  time  > <  added > <removed> <    uncompressed   > <    compressed     >
----------------------------------------------------------------------------------------------
V00000001 2026-11-12 22:57:42  +00000002 -00000000                  700 [               1.234]
V00000002 2026-11-12 22:57:58  +00000001 -00000000                2.500 [               1.215]
V00000003 2026-11-12 22:58:04  +00000001 -00000000                  850 [               1.218]
----------------------------------------------------------------------------------------------
               3.667                                              4.050                 3.667
0.000s (00:00:00,35.17KB) (all OK)
"""

    def test_totals_are_summed(self):
        stat = parse_info_stat(self.REAL)
        self.assertIsNotNone(stat)
        self.assertEqual(stat["versions"], 3)
        self.assertEqual(stat["uncompressed"], 4050)
        self.assertEqual(stat["compressed"], 3667)

    def test_thousands_separators_are_parsed(self):
        pass
        text = (
            "V00000001 2026-11-13 18:23:58  +00005011 -00000000"
            "            1.053.890 [             309.463]\n"
        )
        stat = parse_info_stat(text)
        self.assertEqual(stat["uncompressed"], 1_053_890)
        self.assertEqual(stat["compressed"], 309_463)

    def test_empty_output_gives_none(self):
        self.assertIsNone(parse_info_stat(""))
        self.assertIsNone(parse_info_stat("no versions here"))

    def test_ordinary_info_output_gives_none(self):
        pass
        text = (
            "V00000001 2026-11-12 22:57:42  +00000002 -00000000 ->"
            "                1.234\n"
        )
        self.assertIsNone(parse_info_stat(text))

    def test_stats_feed_the_report(self):
        pass
        stat = parse_info_stat(self.REAL)
        stats = dedup_stats(stat["uncompressed"], 3667)
        self.assertEqual(stats["logical"], 4050)
        self.assertEqual(stats["actual"], 3667)
        self.assertEqual(stats["saved"], 383)
        self.assertAlmostEqual(stats["ratio"], 4050 / 3667, places=6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
