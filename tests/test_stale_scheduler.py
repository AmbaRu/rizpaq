




from __future__ import annotations

import unittest
from unittest import mock

from core import scheduler


def _csv(name: str, command: str) -> bytes:
    row = ["HOST", name, "17.11.2026 20:00", "Ready", "", "", "", "RiV",
           '"' + command + '"']
    return ("\ufeff" + ",".join(row) + "\n").encode("utf-8")


OLD = r'"C:\Python\python.exe" "D:\src\main.py" --task "D:\Backup\tasks.rzp" --job "abc"'
NEW = r'"D:\Backup\Rizpaq\rizpaq_task.exe" --task "D:\Backup\tasks.rzp" --job "def"'


class TestStaleCommand(unittest.TestCase):
    def test_python_source_is_stale(self):
        self.assertTrue(scheduler.is_stale_runner_command(OLD))

    def test_installed_exe_is_not_stale(self):
        self.assertFalse(scheduler.is_stale_runner_command(NEW))
        self.assertFalse(scheduler.is_stale_runner_command(""))


class TestFindStaleTasks(unittest.TestCase):
    def test_only_rizpaq_tasks(self):
        stdout = (
            _csv("Rizpaq_b_old_12345678", OLD)
            + _csv("Rizpaq_b_new_87654321", NEW)
            + _csv("SomeOtherApp", OLD)
        )
        done = mock.Mock(returncode=0, stdout=stdout)

        with mock.patch.object(scheduler, "_run_schtasks", return_value=done), \
             mock.patch.object(scheduler.os, "name", "nt"):
            stale = scheduler.find_stale_runner_tasks()

        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]["name"], "Rizpaq_b_old_12345678")
        self.assertIn("main.py", stale[0]["command"])

    def test_no_output_gives_empty(self):
        with mock.patch.object(scheduler, "_run_schtasks", return_value=None), \
             mock.patch.object(scheduler.os, "name", "nt"):
            self.assertEqual(scheduler.find_stale_runner_tasks(), [])


if __name__ == "__main__":
    unittest.main()
