                       





















from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import headless as H
from core import tasks as T

ZPAQ = "zpaq_test_engine"


class TestHeadlessActions(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="headless_actions_")
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.src = self.dir / "src"
        self.src.mkdir()
        (self.src / "a.txt").write_text("data\n", encoding="utf-8")
        self.dest = self.dir / "arc.zpaq"
        self.rzp = self.dir / "tasks.rzp"

                                                                         

    def _make_container(self, action: str, extra: dict = None,
                        password: str = None,
                        work_extra: dict = None) -> str:
        container = T.empty_container("live")
        work = T.add_work(
            container, "Работа", [str(self.src)], str(self.dest),
            password=password,
            **(work_extra or {}),
        )
        settings = {
            "title": "Задание",
            "action": action,
            "task_log_mode": "full",
        }
        settings.update(extra or {})
        job = T.add_job(container, work["id"], settings)
        T.save_container(self.rzp, container)
        return job["id"]

    def _run(self, action: str, extra: dict = None, fake_run=None,
             work_extra: dict = None):
        pass
        job_id = self._make_container(action, extra, work_extra=work_extra)
        calls = []

        def fake_run_zpaq(cmd, is_cancelled=None, set_proc=None):
            calls.append(list(cmd))
            if fake_run is not None:
                return fake_run(cmd)
            return 0, "engine output\n"

                                                                       
                                                                       
        cfg_path = self.dir / "test_config.json"
        cfg_path.write_text(
            json.dumps({"notify_mode": "off"}), encoding="utf-8"
        )

        with mock.patch.dict(
            os.environ,
            {"ZPAQ_BIN": ZPAQ, "ZPAQ_GUI_CONFIG": str(cfg_path)},
        ), mock.patch(
            "core.zpaq_cli.run_zpaq", fake_run_zpaq
        ), mock.patch(
            "core.index_refresh.refresh_index_sync", lambda *a, **k: None
        ):
            rc = H._headless_task([str(self.rzp), "--job", job_id])
        return rc, calls, job_id

    def _job_state(self, job_id: str) -> dict:
        container = T.load_container(self.rzp)
        for work in container.get("works") or []:
            for job in work.get("jobs") or []:
                if job.get("id") == job_id:
                    return job
        return {}

                                                                        

    def test_backup_action_runs(self):
        pass
        rc, calls, job_id = self._run("backup")
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], ZPAQ)
        self.assertEqual(calls[0][1], "a")
        state = self._job_state(job_id)
        self.assertEqual(state.get("last_status"), "ok")
        self.assertEqual(state.get("run_count"), 1)
        self.assertTrue(state.get("last_run"))

    def test_backup_verify_after_create(self):
        pass
        rc, calls, job_id = self._run("backup", {"verify": "full"})
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][1], "a")
        self.assertEqual(calls[1][1], "t")
        self.assertEqual(self._job_state(job_id).get("last_status"), "ok")

    def test_unknown_verify_mode_is_ignored(self):
        rc, calls, _job = self._run("backup", {"verify": "nonsense"})
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 1)

    def test_scheduled_backup_makes_second_copy(self):
        pass
        copy_dir = self.dir / "copy"

        def fake_run(cmd):
            Path(cmd[2]).write_bytes(b"archive payload")
            return 0, "engine output\n"

        rc, calls, job_id = self._run(
            "backup", {"copy": str(copy_dir)}, fake_run=fake_run
        )
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 1)
        copied = copy_dir / self.dest.name
        self.assertTrue(copied.is_file())
        self.assertEqual(copied.read_bytes(), b"archive payload")
        state = self._job_state(job_id)
        self.assertEqual(state.get("last_status"), "ok")
        self.assertIsNone(state.get("last_reason"))
        log_text = Path(str(self.rzp) + ".log").read_text(encoding="utf-8")
        self.assertIn("second copy", log_text)

    def test_copy_failure_marks_job_error_but_keeps_backup(self):
        pass
        bad_target = self.dir / "not_a_folder"
        bad_target.write_text("file", encoding="utf-8")

        def fake_run(cmd):
            Path(cmd[2]).write_bytes(b"archive payload")
            return 0, "engine output\n"

        rc, calls, job_id = self._run(
            "backup", {"copy": str(bad_target)}, fake_run=fake_run
        )
        self.assertEqual(rc, 1)
        self.assertEqual(len(calls), 1)
        self.assertTrue(self.dest.is_file(), "архив должен остаться")
        state = self._job_state(job_id)
        self.assertEqual(state.get("last_status"), "error")
        self.assertEqual(state.get("last_reason"), T.REASON_COPY_FAILED)
        log_text = Path(str(self.rzp) + ".log").read_text(encoding="utf-8")
        self.assertIn("second copy failed", log_text)
        self.assertIn("Return code: 1", log_text)

    def _fake_run_with_archive(self, cmd):
        Path(cmd[2]).write_bytes(b"archive payload")
        return 0, "engine output\n"

    def test_par2_failure_makes_short_log_an_error(self):
        pass







        with mock.patch(
            "core.headless._headless_par2",
            return_value=(False, "[par2] set not created\n"),
        ):
            rc, _calls, job_id = self._run(
                "backup",
                {"par2_enabled": True, "task_log_mode": "short"},
                fake_run=self._fake_run_with_archive,
            )
        self.assertEqual(rc, 1)
        self.assertEqual(self._job_state(job_id).get("last_status"), "error")
        log_text = Path(str(self.rzp) + ".log").read_text(encoding="utf-8")
        self.assertIn("Status: ERROR (rc=1)", log_text)
        self.assertNotIn("Status: OK", log_text)

    def test_extra_archive_failure_makes_short_log_an_error(self):
        pass
        with mock.patch(
            "core.extra_dests.prepare_dests",
            return_value=[str(self.dir / "extra.zpaq")],
        ), mock.patch(
            "core.extra_dests.run_extra_dests",
            return_value=(False, "[extra archives] FAIL\n"),
        ):
            rc, _calls, job_id = self._run(
                "backup",
                {"task_log_mode": "short"},
                fake_run=self._fake_run_with_archive,
                work_extra={"extra_dests": [str(self.dir / "extra.zpaq")]},
            )
        self.assertEqual(rc, 1)
        self.assertEqual(self._job_state(job_id).get("last_status"), "error")
        log_text = Path(str(self.rzp) + ".log").read_text(encoding="utf-8")
        self.assertIn("Status: ERROR (rc=1)", log_text)

    def test_test_action_builds_t_command(self):
        rc, calls, _ = self._run("test")
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0][1], "t")
        self.assertEqual(calls[0][2], str(self.dest))

    def test_crop_action_uses_repack_with_verify(self):
        def fake_run(cmd):
            if "-to" in cmd:
                Path(cmd[cmd.index("-to") + 1]).write_bytes(b"new archive")
            return 0, "engine output\n"

        rc, calls, job_id = self._run("crop", fake_run=fake_run)
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0][1], "repack")
        self.assertIn("-to", calls[0])
        self.assertEqual(calls[1][1], "i")
        self.assertEqual(self._job_state(job_id).get("last_status"), "ok")

    def test_consolidate_action_uses_merge_command(self):
        self.dest = self.dir / "multi_????.zpaq"
        rc, calls, _ = self._run("consolidate")
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0][1], "m")
        self.assertEqual(calls[0][2], str(self.dest))
        self.assertTrue(calls[0][3].endswith("multi.zpaq"))
        self.assertIn("-verify", calls[0])

    def test_consolidate_rejects_single_archive(self):
        rc, calls, _ = self._run("consolidate")
        self.assertEqual(rc, 1)
        self.assertEqual(calls, [])

    def test_sfx_action_builds_sfx_command(self):
        rc, calls, _ = self._run("sfx")
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0][1], "sfx")
        self.assertEqual(calls[0][2], str(self.dest))
        self.assertTrue(calls[0][3].endswith(".exe"))

    def test_info_action_builds_info_command(self):
        rc, calls, _ = self._run("info")
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0], [ZPAQ, "i", str(self.dest), "-comment"])

    def test_checkpassword_action_builds_checkpassword_command(self):
        rc, calls, _ = self._run("checkpassword")
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0][1], "checkpassword")
        self.assertIn("-key", calls[0])

    def test_password_action_without_new_password_fails_cleanly(self):
        pass
        rc, calls, job_id = self._run("password")
        self.assertEqual(rc, 1)
        self.assertEqual(calls, [])
        state = self._job_state(job_id)
        self.assertEqual(state.get("last_status"), "error")

    def test_password_action_writes_separate_file_and_replaces(self):
        pass



        self.dest.write_bytes(b"old encrypted archive")
        job_id = self._make_container(
            "password",
            {"new_password": "newpass"},
            password="oldpass",
        )

        def fake_run(cmd):
            target = Path(cmd[3])
            self.assertNotEqual(target, self.dest, "цель не должна совпадать с исходником")
            target.write_bytes(b"new encrypted archive")
            return 0, "password changed\n"

        cfg_path = self.dir / "test_config.json"
        cfg_path.write_text(
            json.dumps({"notify_mode": "off"}), encoding="utf-8"
        )
        calls = []

        def fake_run_zpaq(cmd, is_cancelled=None, set_proc=None):
            calls.append(list(cmd))
            return fake_run(cmd)

        with mock.patch.dict(
            os.environ,
            {"ZPAQ_BIN": ZPAQ, "ZPAQ_GUI_CONFIG": str(cfg_path)},
        ), mock.patch(
            "core.zpaq_cli.run_zpaq", fake_run_zpaq
        ), mock.patch(
            "core.index_refresh.refresh_index_sync", lambda *a, **k: None
        ):
            rc = H._headless_task([str(self.rzp), "--job", job_id])

        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 1)
        cmd = calls[0]
        self.assertEqual(cmd[1], "password")
        self.assertEqual(cmd[2], str(self.dest))
        self.assertIn("-force", cmd)
        self.assertIn("oldpass", cmd)
        self.assertIn("newpass", cmd)
        self.assertEqual(self.dest.read_bytes(), b"new encrypted archive")
        self.assertFalse(Path(cmd[3]).exists(), "временный файл должен исчезнуть")
        self.assertEqual(self._job_state(job_id).get("last_status"), "ok")

    def test_all_actions_are_imported(self):
        pass





        import core.headless as module

        for name in (
            "ACTION_TEST",
            "ACTION_CROP",
            "ACTION_CONSOLIDATE",
            "ACTION_SFX",
            "ACTION_INFO",
            "ACTION_PASSWORD",
            "ACTION_CHECKPASSWORD",
        ):
            with self.subTest(name=name):
                self.assertTrue(hasattr(module, name), f"{name} не импортирован")


if __name__ == "__main__":
    unittest.main(verbosity=2)
