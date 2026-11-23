
from __future__ import annotations

import unittest
from unittest import mock

from core import heartbeat, scheduler


class TestHeartbeatTaskCommand(unittest.TestCase):
    def test_command_has_heartbeat_flag(self):
        cmd = scheduler.heartbeat_cmd()
        self.assertIn("--heartbeat", cmd)
        self.assertNotIn("--task", cmd)
        self.assertNotIn("rizpaq_task.exe", cmd)

    def test_create_task_uses_daily_schedule(self):
        seen = {}

        def fake_run(cmd):
            seen["cmd"] = cmd
            return mock.Mock(returncode=0)

        with mock.patch.object(scheduler, "_run_schtasks", side_effect=fake_run):
            self.assertTrue(scheduler.create_heartbeat_task(13))
        cmd = seen["cmd"]
        self.assertIn("/create", cmd)
        self.assertIn(scheduler.HEARTBEAT_TASK_NAME, cmd)
        self.assertIn("/sc", cmd)
        self.assertIn("DAILY", cmd)
        self.assertIn("13:00", cmd)

    def test_failed_registration(self):
        with mock.patch.object(
            scheduler, "_run_schtasks", return_value=mock.Mock(returncode=1)
        ):
            self.assertFalse(scheduler.create_heartbeat_task())

    def test_remove_and_query(self):
        with mock.patch.object(
            scheduler, "_run_schtasks", return_value=mock.Mock(returncode=0)
        ) as run:
            self.assertTrue(scheduler.remove_heartbeat_task())
            self.assertTrue(scheduler.is_heartbeat_task_scheduled())
        self.assertIn("/delete", run.call_args_list[0].args[0])
        self.assertIn("/query", run.call_args_list[1].args[0])


class TestHeartbeatCli(unittest.TestCase):
    def test_disabled_returns_zero(self):
        cfg = heartbeat.config_mod.Settings(mail_report_enabled=False)
        with mock.patch.object(
            heartbeat.config_mod, "load", return_value=cfg
        ), mock.patch.object(
            heartbeat, "send_if_needed", return_value=(0, "")
        ) as send:
            self.assertEqual(heartbeat.run_cli(), 0)
        send.assert_called_once()

    def test_failed_send_returns_one(self):
        cfg = heartbeat.config_mod.Settings(mail_report_enabled=True)
        with mock.patch.object(
            heartbeat.config_mod, "load", return_value=cfg
        ), mock.patch.object(
            heartbeat, "send_if_needed", return_value=(1, "smtp error")
        ):
            self.assertEqual(heartbeat.run_cli(), 1)


if __name__ == "__main__":
    unittest.main()
