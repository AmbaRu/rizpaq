                       

from __future__ import annotations

import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from core import multipart_par2 as mp
from core import par2_ops
from core.paths import BACKUP_INDEX_SIGNATURE


class _Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="mp_par2_")
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.mask = self.dir / "multi_????.zpaq"
        self.files = []
        for n in (1, 2):
            p = self.dir / ("multi_%04d.zpaq" % n)
            p.write_bytes(b"volume %d" % n)
            self.files.append(str(p))

    def stamp_set(self, file: str, mtime: float = None) -> None:
        pass
        main = par2_ops.par2_main_name(file)
        Path(main).write_text("par2 index\n", encoding="utf-8")
        vol = str(file) + ".vol000+01.par2"
        Path(vol).write_bytes(b"recovery")
        if mtime is not None:
            for p in (main, vol):
                os.utime(p, (mtime, mtime))


class TestArchiveFiles(_Case):
    def test_mask_expands_to_concrete_volumes(self):
        self.assertEqual(mp.archive_files(str(self.mask)), sorted(self.files))

    def test_backup_set_includes_parts_and_indexes(self):
        base = self.dir / "arc.zpaq"
        for n in (1, 2):
            (self.dir / ("arc_%08d.zpaq" % n)).write_bytes(b"part")
        (self.dir / "arc_00000000_backup.txt").write_text(
            BACKUP_INDEX_SIGNATURE + "index\n", encoding="utf-8"
        )
        (self.dir / "arc_00000000_backup.index").write_bytes(b"idx")
        (self.dir / "arc_00000000.pid").write_bytes(b"1")
        names = [Path(x).name for x in mp.archive_files(str(base))]
        self.assertIn("arc_00000001.zpaq", names)
        self.assertIn("arc_00000002.zpaq", names)
        self.assertIn("arc_00000000_backup.txt", names)
        self.assertIn("arc_00000000_backup.index", names)
        self.assertNotIn("arc_00000000.pid", names)


class TestPlan(_Case):
    def test_new_volume_needs_protection(self):
        plan = mp.plan(str(self.mask))
        self.assertEqual([x[1] for x in plan],
                         [mp.ACTION_CREATE, mp.ACTION_CREATE])

    def test_unchanged_volume_is_skipped(self):
        for f in self.files:
            self.stamp_set(f, os.path.getmtime(f) + 10)
        self.assertEqual([x[1] for x in mp.plan(str(self.mask))],
                         [mp.ACTION_SKIP, mp.ACTION_SKIP])

    def test_changed_volume_is_refreshed(self):
        f = self.files[0]
        self.stamp_set(f, os.path.getmtime(f) - 10)
        time.sleep(0.01)
        os.utime(f, None)
        actions = {Path(x[0]).name: x[1] for x in mp.plan(str(self.mask))}
        self.assertEqual(actions["multi_0001.zpaq"], mp.ACTION_REFRESH)
        self.assertEqual(actions["multi_0002.zpaq"], mp.ACTION_CREATE)

    def test_incomplete_set_is_recreated(self):
        f = self.files[0]
        Path(par2_ops.par2_main_name(f)).write_text("only index\n",
                                                     encoding="utf-8")
        actions = {Path(x[0]).name: x[1] for x in mp.plan(str(self.mask))}
        self.assertEqual(actions["multi_0001.zpaq"], mp.ACTION_CREATE)

    def test_service_file_marked(self):
        base = self.dir / "arc.zpaq"
        (self.dir / "arc_00000001.zpaq").write_bytes(b"part")
        (self.dir / "arc_00000000_backup.txt").write_text(
            BACKUP_INDEX_SIGNATURE + "x\n", encoding="utf-8"
        )
        plan = mp.plan(str(base))
        svc = {Path(x[0]).name: x[2] for x in plan}
        self.assertTrue(svc["arc_00000000_backup.txt"])
        self.assertFalse(svc["arc_00000001.zpaq"])


class TestHeadlessPar2(_Case):
    def test_headless_uses_per_volume_protection(self):
        from unittest import mock

        from core import headless

        with mock.patch("core.par2_ops.find_par2", return_value="par2.exe"), \
                mock.patch("core.multipart_par2.protect", return_value={
                    "ok": True, "created": 2, "refreshed": 0,
                    "skipped": 0, "failed": 0, "sets": [],
                    "log": "[par2] ok\n",
                }):
            ok, note = headless._headless_par2(
                "C:/tasks.rzp", {"id": "w"}, {}, str(self.mask),
                {"par2_enabled": True},
            )
        self.assertTrue(ok, note)
        self.assertIn("защита по томам", note)


@unittest.skipUnless(par2_ops.find_par2(), "par2.exe не найден")
class TestRealPar2(_Case):
    def test_protect_then_verify_and_skip(self):
        bin_path = par2_ops.find_par2()
        opts = {"redundancy": 5}
        first = mp.protect(bin_path, str(self.mask), opts)
        self.assertTrue(first["ok"], first["log"])
        self.assertEqual(first["created"], 2)
        verified = mp.verify(bin_path, str(self.mask))
        self.assertTrue(verified["ok"], verified["log"])
        second = mp.protect(bin_path, str(self.mask), opts)
        self.assertEqual(second["skipped"], 2, second["log"])

    def test_new_volume_only_protects_new_file(self):
        bin_path = par2_ops.find_par2()
        opts = {"redundancy": 5}
        self.assertTrue(mp.protect(bin_path, str(self.mask), opts)["ok"])
        third = self.dir / "multi_0003.zpaq"
        third.write_bytes(b"volume 3")
        res = mp.protect(bin_path, str(self.mask), opts)
        self.assertTrue(res["ok"], res["log"])
        self.assertEqual(res["created"], 1)
        actions = {Path(x["file"]).name: x["action"] for x in res["sets"]}
        self.assertEqual(actions["multi_0001.zpaq"], mp.ACTION_SKIP)
        self.assertEqual(actions["multi_0003.zpaq"], mp.ACTION_CREATE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
