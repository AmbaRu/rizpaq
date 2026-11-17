                       









from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import copy_ops              


class TestCopyOps(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="copy_ops_")
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.src_dir = self.dir / "src"
        self.src_dir.mkdir()
        self.dst_dir = self.dir / "copy"

    def _archive(self, name: str = "archive.zpaq", data: bytes = b"data") -> Path:
        path = self.src_dir / name
        path.write_bytes(data)
        return path

                                                                          

    def test_single_archive_copied_and_verified(self):
        src = self._archive(data=b"archive payload")
        ok, note = copy_ops.copy_archive(str(src), str(self.dst_dir))
        self.assertTrue(ok, note)
        self.assertIn("1 file(s)", note)
        copied = self.dst_dir / src.name
        self.assertEqual(copied.read_bytes(), b"archive payload")
        self.assertTrue(copy_ops.files_equal(src, copied))
        self.assertFalse((self.dst_dir / (src.name + copy_ops.PART_SUFFIX)).exists())

    def test_mask_copies_every_volume(self):
        first = self._archive("arch_0001.zpaq", b"one")
        second = self._archive("arch_0002.zpaq", b"two")
        (self.src_dir / "notes.txt").write_text("ignore", encoding="utf-8")
        mask = self.src_dir / "arch_????.zpaq"
        ok, note = copy_ops.copy_archive(str(mask), str(self.dst_dir))
        self.assertTrue(ok, note)
        self.assertIn("2 file(s)", note)
        self.assertEqual((self.dst_dir / first.name).read_bytes(), b"one")
        self.assertEqual((self.dst_dir / second.name).read_bytes(), b"two")
        self.assertFalse((self.dst_dir / "notes.txt").exists())

    def test_missing_archive_is_an_error(self):
        ok, note = copy_ops.copy_archive(
            str(self.src_dir / "absent.zpaq"), str(self.dst_dir)
        )
        self.assertFalse(ok)
        self.assertIn("archive file not found", note)

    def test_empty_copy_folder_is_an_error(self):
        src = self._archive()
        ok, note = copy_ops.copy_archive(str(src), "  ")
        self.assertFalse(ok)
        self.assertIn("copy folder is not set", note)

    def test_copy_into_same_folder_is_noop(self):
        src = self._archive(data=b"same")
        ok, note = copy_ops.copy_archive(str(src), str(self.src_dir))
        self.assertTrue(ok)
        self.assertEqual(note, "")
        self.assertEqual(src.read_bytes(), b"same")

    def test_mtime_is_preserved(self):
        src = self._archive()
        old = 1_600_000_000
        os.utime(src, (old, old))
        ok, note = copy_ops.copy_archive(str(src), str(self.dst_dir))
        self.assertTrue(ok, note)
        copied = self.dst_dir / src.name
        self.assertAlmostEqual(copied.stat().st_mtime, old, delta=2)

                                                                          

    def test_mismatch_keeps_previous_copy(self):
        pass
        src = self._archive(data=b"new content")
        self.dst_dir.mkdir()
        previous = self.dst_dir / src.name
        previous.write_bytes(b"previous good copy")

        with mock.patch.object(copy_ops, "files_equal", return_value=False):
            ok, note = copy_ops.copy_archive(str(src), str(self.dst_dir))

        self.assertFalse(ok)
        self.assertIn("copy differs from the source", note)
        self.assertEqual(previous.read_bytes(), b"previous good copy")
        self.assertFalse((self.dst_dir / (src.name + copy_ops.PART_SUFFIX)).exists())

    def test_target_is_a_file_reports_error(self):
        src = self._archive()
        bad_target = self.dir / "not_a_folder"
        bad_target.write_text("file", encoding="utf-8")
        ok, note = copy_ops.copy_archive(str(src), str(bad_target))
        self.assertFalse(ok)
        self.assertIn("not a folder", note)

                                                                          

    def test_files_equal_compares_contents(self):
        first = self._archive("a.bin", b"same")
        second = self.src_dir / "b.bin"
        second.write_bytes(b"same")
        self.assertTrue(copy_ops.files_equal(first, second))
        second.write_bytes(b"diff")
        self.assertFalse(copy_ops.files_equal(first, second))
        second.write_bytes(b"same and longer")
        self.assertFalse(copy_ops.files_equal(first, second))

    def test_copy_sources_handles_plain_and_mask(self):
        src = self._archive()
        self.assertEqual(copy_ops.copy_sources(str(src)), [src])
        self.assertEqual(copy_ops.copy_sources(str(self.src_dir / "no.zpaq")), [])
        self.assertEqual(
            [p.name for p in copy_ops.copy_sources(str(self.src_dir / "*.zpaq"))],
            ["archive.zpaq"],
        )


if __name__ == "__main__":
    unittest.main()
