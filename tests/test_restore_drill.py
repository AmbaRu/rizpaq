
from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

from core import restore_drill
from core.models import ArchiveEntry


def _entry(path, size=100, version=2, flag="", is_dir=False):
    return ArchiveEntry(
        path=path, size=size, datetime="", version=version,
        flag=flag, is_dir=is_dir,
    )


class TestPickEntry(unittest.TestCase):
    def test_filters_and_prefers_latest(self):
        entries = [
            _entry("old.txt", version=1),
            _entry("new.txt", version=2),
            _entry("folder/", is_dir=True, version=2),
            _entry("deleted.txt", flag="-", version=2),
            _entry("huge.bin", size=restore_drill.MAX_DRILL_SIZE + 1,
                   version=2),
            _entry("empty.txt", size=0, version=2),
        ]
        picked = restore_drill.pick_entry(entries)
        self.assertEqual(picked.path, "new.txt")

    def test_no_candidates(self):
        self.assertIsNone(
            restore_drill.pick_entry([_entry("x", is_dir=True)])
        )

    def test_custom_chooser(self):
        entries = [_entry("a.txt", version=3), _entry("b.txt", version=3)]
        picked = restore_drill.pick_entry(
            entries, choose=lambda items: items[-1]
        )
        self.assertEqual(picked.path, "b.txt")


class TestExtractCmd(unittest.TestCase):
    def test_command_shape(self):
        cmd = restore_drill.extract_cmd(
            "zpaqfranz", "F:/a.zpaq", _entry("dir/file.txt", version=7),
            "D:/tmp", "secret",
        )
                                                                         
                                                                      
        self.assertEqual(
            cmd,
            ["zpaqfranz", "x", "F:/a.zpaq", "-key", "secret",
             "dir/file.txt", "-until", "7", "-to", "D:/tmp" + os.sep],
        )

    def test_target_with_separator_is_unchanged(self):
        for target in ("D:/tmp/", "D:/tmp\\"):
            cmd = restore_drill.extract_cmd(
                "zpaq", "F:/a.zpaq", _entry("x.txt"), target
            )
            self.assertEqual(cmd[-1], target)


class TestHashing(unittest.TestCase):
    def test_sha256_of(self):
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "x.bin"
            path.write_bytes(b"abc")
            self.assertEqual(
                restore_drill.sha256_of(path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )
            self.assertIsNone(restore_drill.sha256_of(Path(folder) / "no"))


class TestDrill(unittest.TestCase):
    def test_source_hash_match(self):
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "photo.jpg"
            source.write_bytes(b"original")
            entry = _entry(source.name)

            def fake_run(cmd, *a, **kw):
                target = Path(cmd[cmd.index("-to") + 1])
                target.mkdir(parents=True, exist_ok=True)
                (target / entry.path).write_bytes(source.read_bytes())
                return 0, "extracted"

            with mock.patch.object(
                restore_drill, "load_entries", return_value=[entry]
            ), mock.patch.object(
                restore_drill, "run_zpaq", side_effect=fake_run
            ):
                ok, log = restore_drill.run_restore_drill(
                    "zpaq", "F:/a.zpaq", sources=[folder]
                )
        self.assertTrue(ok)
        self.assertIn("вердикт: OK", log)
        self.assertIn("сравнение с исходником", log)

    def test_mismatch_detected(self):
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "data.bin"
            source.write_bytes(b"original")

            def fake_run(cmd, *a, **kw):
                target = Path(cmd[cmd.index("-to") + 1])
                target.mkdir(parents=True, exist_ok=True)
                (target / "data.bin").write_bytes(b"corrupted")
                return 0, "extracted"

            with mock.patch.object(
                restore_drill, "load_entries",
                return_value=[_entry("data.bin")],
            ), mock.patch.object(
                restore_drill, "run_zpaq", side_effect=fake_run
            ):
                ok, log = restore_drill.run_restore_drill(
                    "zpaq", "F:/a.zpaq", sources=[folder]
                )
        self.assertFalse(ok)
        self.assertIn("MISMATCH", log)

    def test_fallback_second_extraction(self):
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            def fake_run(cmd, *a, **kw):
                target = Path(cmd[cmd.index("-to") + 1])
                target.mkdir(parents=True, exist_ok=True)
                (target / "x.bin").write_bytes(b"same")
                return 0, "extracted"

            with mock.patch.object(
                restore_drill, "load_entries",
                return_value=[_entry("x.bin")],
            ), mock.patch.object(
                restore_drill, "run_zpaq", side_effect=fake_run
            ):
                ok, log = restore_drill.run_restore_drill(
                    "zpaq", "F:/a.zpaq", sources=[]
                )
        self.assertTrue(ok)
        self.assertIn("повторное извлечение", log)


if __name__ == "__main__":
    unittest.main()
