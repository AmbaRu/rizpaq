                       





















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
                        password: str = None) -> str:
        container = T.empty_container("live")
        work = T.add_work(
            container, "Работа", [str(self.src)], str(self.dest),
            password=password,
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

    def _run(self, action: str, extra: dict = None, fake_run=None):
        pass
        job_id = self._make_container(action, extra)
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

    def test_test_action_builds_t_command(self):
        rc, calls, _ = self._run("test")
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0][1], "t")
        self.assertEqual(calls[0][2], str(self.dest))

    def test_crop_action_builds_crop_command(self):
        rc, calls, _ = self._run("crop")
        self.assertEqual(rc, 0)
        self.assertEqual(
            calls[0], [ZPAQ, "crop", str(self.dest), "-kill", "-to", str(self.dest)]
        )

    def test_consolidate_action_builds_consolidate_command(self):
        rc, calls, _ = self._run("consolidate")
        self.assertEqual(rc, 0)
        self.assertEqual(
            calls[0], [ZPAQ, "consolidate", str(self.dest), "-to", str(self.dest)]
        )

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
