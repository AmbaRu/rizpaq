














from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core import copy_ops, extra_dests, paths, tasks
from core.headless import (
    _build_create_cmd,
    _build_test_cmd,
    _precheck_blocked_reason,
)

SIGNATURE = paths.BACKUP_INDEX_SIGNATURE


class _BackupSetCase(unittest.TestCase):
    pass

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.base = self.dir / "data.zpaq"

    def tearDown(self):
        self._tmp.cleanup()

    def make_set(self, parts=(1, 2), index=True, binary=True, pid=False):
        for n in parts:
            (self.dir / ("data_%08d.zpaq" % n)).write_bytes(b"part %d" % n)
        if index:
            (self.dir / "data_00000000_backup.txt").write_text(
                SIGNATURE + "something\nformat 1\n", encoding="utf-8"
            )
        if binary:
            (self.dir / "data_00000000_backup.index").write_bytes(b"index")
        if pid:
            (self.dir / "data.pid").write_bytes(b"1")
        return self.base


class TestPaths(_BackupSetCase):
    def test_multipart_pattern_eight_digits(self):
        self.assertEqual(
            paths.multipart_pattern(str(self.dir / "data_00000001.zpaq")),
            str(self.dir / "data_????????.zpaq"),
        )
                                                                      
        self.assertEqual(
            paths.multipart_pattern(str(self.dir / "data_00001.zpaq")),
            str(self.dir / "data_00001.zpaq"),
        )

    def test_base_from_base_part_and_mask(self):
        expected = str(self.base)
        for name in ("data.zpaq", "data_00000001.zpaq",
                     "data_????????.zpaq"):
            with self.subTest(name=name):
                self.assertEqual(
                    paths.multipart_base(str(self.dir / name)), expected
                )
                self.assertEqual(
                    paths.backup_base(str(self.dir / name)), expected
                )

    def test_five_digit_suffix_is_not_a_part(self):
                                                                        
                                           
        path = str(self.dir / "data_00001.zpaq")
        self.assertEqual(paths.multipart_base(path), path)
        self.assertEqual(paths.backup_base(path), path)

    def test_index_and_mask_paths(self):
        self.assertEqual(
            paths.backup_index_path(str(self.base)),
            str(self.dir / "data_00000000_backup.txt"),
        )
        self.assertEqual(
            paths.backup_binary_index_path(str(self.base)),
            str(self.dir / "data_00000000_backup.index"),
        )
        self.assertEqual(
            paths.backup_mask(str(self.base)),
            str(self.dir / "data_????????.zpaq"),
        )

    def test_is_backup_set_by_index_signature(self):
        self.make_set()
        for name in ("data.zpaq", "data_00000001.zpaq",
                     "data_????????.zpaq"):
            with self.subTest(name=name):
                self.assertTrue(
                    paths.is_backup_set(str(self.dir / name))
                )

    def test_is_backup_set_ignores_eight_digits_without_index(self):
                                                                
                                                                        
        self.make_set(index=False)
        self.assertFalse(paths.is_backup_set(str(self.base)))
                                                                
        self.assertTrue(paths.backup_set_exists(str(self.base)))

    def test_base_with_trailing_digits_is_recognized(self):
                                                                       
                                                                    
                               
        base = self.dir / "photo_2024.zpaq"
        for n in (1, 2):
            (self.dir / ("photo_2024_%08d.zpaq" % n)).write_bytes(b"p")
        (self.dir / "photo_2024_00000000_backup.txt").write_text(
            SIGNATURE + "something\n", encoding="utf-8"
        )
        mask = str(self.dir / "photo_2024_????????.zpaq")
        for name in ("photo_2024.zpaq", "photo_2024_00000001.zpaq"):
            with self.subTest(name=name):
                path = str(self.dir / name)
                self.assertTrue(paths.is_backup_set(path))
                self.assertEqual(paths.backup_base(path), str(base))
                self.assertEqual(paths.archive_alias(path), mask)
                self.assertEqual(paths.multipart_pattern(path), mask)
        self.assertEqual(
            [p.name for p in paths.backup_parts(str(base))],
            ["photo_2024_00000001.zpaq", "photo_2024_00000002.zpaq"],
        )

    def test_is_backup_set_rejects_foreign_index(self):
        self.make_set(index=False)
        (self.dir / "data_00000000_backup.txt").write_text(
            "not a backup file\n", encoding="utf-8"
        )
        self.assertFalse(paths.is_backup_set(str(self.base)))

    def test_archive_alias_uses_mask_for_backup(self):
        self.make_set()
        mask = str(self.dir / "data_????????.zpaq")
        for name in ("data.zpaq", "data_00000001.zpaq"):
            with self.subTest(name=name):
                self.assertEqual(
                    paths.archive_alias(str(self.dir / name)), mask
                )

    def test_archive_alias_keeps_ordinary_volumes(self):
        self.assertEqual(
            paths.archive_alias(str(self.dir / "plain_0001.zpaq")),
            str(self.dir / "plain_????.zpaq"),
        )


class TestTaskCreateMode(_BackupSetCase):
    def test_norm_create_mode(self):
        norm = tasks._norm_create_mode
        self.assertEqual(norm("backup"), tasks.CREATE_MODE_BACKUP)
        self.assertEqual(norm(" BACKUP "), tasks.CREATE_MODE_BACKUP)
        self.assertEqual(norm("a"), tasks.CREATE_MODE_A)
        self.assertEqual(norm(None), tasks.CREATE_MODE_A)
        self.assertEqual(norm("weird"), tasks.CREATE_MODE_A)

    def test_add_work_keeps_create_mode(self):
        c = tasks.empty_container()
        work = tasks.add_work(
            c, "W", ["D:/src"], "D:/data.zpaq", create_mode="backup"
        )
        self.assertEqual(work["create_mode"], "backup")
                                                  
        other = tasks.add_work(
            c, "V", ["D:/src"], "D:/v.zpaq", create_mode="nonsense"
        )
        self.assertEqual(other["create_mode"], "a")

    def test_job_to_runnable_settings_passes_create_mode(self):
        c = tasks.empty_container()
        work = tasks.add_work(
            c, "W", ["D:/src"], "D:/data.zpaq", create_mode="backup"
        )
        job = tasks.add_job(c, work["id"], {"action": "backup"})
        settings = tasks.job_to_runnable_settings(work, job)
        self.assertEqual(settings["create_mode"], "backup")


class TestHeadlessCommands(_BackupSetCase):
    def test_create_backup_uses_backup_command_without_mask(self):
        cmd = _build_create_cmd(
            "zpaq", {"create_mode": "backup", "sfx": "x.sfx"},
            ["D:/src"], "D:/data.zpaq", None,
        )
        self.assertEqual(cmd[1], "backup")
        self.assertEqual(cmd[2], "D:/data.zpaq")
        self.assertNotIn("-sfx", cmd)
        self.assertNotIn("_????????", cmd[2])
                                                                        
                                                                
        self.assertNotIn("-open", cmd)

    def test_create_plain_archive_still_uses_a(self):
        cmd = _build_create_cmd(
            "zpaq", {"create_mode": "a"}, ["D:/src"], "D:/data.zpaq", None
        )
        self.assertEqual(cmd[1], "a")
        self.assertIn("-open", cmd)

    def test_test_backup_uses_testbackup_and_base(self):
        self.make_set()
        cmd = _build_test_cmd("zpaq", str(self.base), None, "full")
        self.assertEqual(cmd[:3], ["zpaq", "testbackup", str(self.base)])

    def test_test_backup_verify_modes_add_verify(self):
        self.make_set()
        for mode in ("checksum", "verify", "paranoid"):
            with self.subTest(mode=mode):
                cmd = _build_test_cmd("zpaq", str(self.base), None, mode)
                self.assertEqual(cmd[1], "testbackup")
                self.assertIn("-verify", cmd)
                self.assertNotIn("-paranoid", cmd)
                self.assertNotIn("-to", cmd)

    def test_sync_and_verify_fs_use_mask(self):
        self.make_set()
        mask = str(self.dir / "data_????????.zpaq")
        sync = _build_test_cmd(
            "zpaq", str(self.base), None, "sync", sources=["D:/src"]
        )
        self.assertEqual(sync[1:3], ["sync", mask])
        verify = _build_test_cmd("zpaq", str(self.base), None, "verify_fs")
        self.assertEqual(verify[1:3], ["v", mask])

    def test_precheck_allows_backup_with_chunk(self):
        self.make_set()
        reason = _precheck_blocked_reason(
            {"create_mode": "backup", "chunk": "1G"}, str(self.base)
        )
        self.assertEqual(reason, "")


class TestCopyAndPar2(_BackupSetCase):
    def test_copy_sources_copies_parts_and_indexes_without_pid(self):
        base = self.make_set(parts=(1, 2, 3), pid=True)
        names = [p.name for p in copy_ops.copy_sources(str(base))]
        self.assertEqual(names, [
            "data_00000001.zpaq",
            "data_00000002.zpaq",
            "data_00000003.zpaq",
            "data_00000000_backup.txt",
            "data_00000000_backup.index",
        ])
        self.assertNotIn("data.pid", names)

    def test_extra_dests_protects_backup_with_par2(self):
        calls = []

        def fake_par2(rzp_path, work, job, dest, settings):
            calls.append(dest)
            return True, "[par2] по томам: создано 1\n"

        with mock.patch("core.headless._headless_par2",
                        side_effect=fake_par2):
            ok, log = extra_dests.run_extra_dests(
                "zpaq",
                {"create_mode": "backup", "par2_enabled": True},
                ["D:/src"],
                ["F:/one.zpaq"],
                build_cmd=lambda *a: ["zpaq", "backup", a[3]],
                runner=lambda cmd: (0, "archived"),
                work={"title": "W"},
                rzp_path="C:/tasks.rzp",
            )
        self.assertTrue(ok)
        self.assertEqual(calls, ["F:/one.zpaq"])
        self.assertIn("по томам", log)


class TestLocales(unittest.TestCase):
    KEYS = (
        "create.mode",
        "create.mode_a",
        "create.mode_backup",
        "tip.create_mode",
        "tip.create_mode_no_sfx",
        "tip.create_mode_par2_volumes",
        "retention.backup",
        "consolidate.backup_name",
    )

    def test_keys_present_in_all_locales(self):
        locales = Path(__file__).resolve().parent.parent / "locales"
        for path in sorted(locales.glob("*.json")):
            strings = json.loads(path.read_text(encoding="utf-8"))["strings"]
            for key in self.KEYS:
                with self.subTest(locale=path.stem, key=key):
                    self.assertIn(key, strings)
                    self.assertTrue(strings[key].strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
