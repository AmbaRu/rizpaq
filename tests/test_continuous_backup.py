                       



















from __future__ import annotations

import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import dashboard_alerts as DA
from core import headless as H
from core import scheduler as S
from ui import presentation as P


def _work():
    return {"id": "w1", "title": "Документы"}


def _job():
    return {"id": "job-12345678", "title": "Бэкап", "action": "backup"}


def _value_after(cmd, option):
    return cmd[cmd.index(option) + 1]


class TestExecCmd(unittest.TestCase):
    def test_plain_command(self):
        with mock.patch.object(
            S, "_rizpaq_cmd", return_value=r'"C:\Rz\Rizpaq.exe"'
        ):
            cmd = S._exec_cmd_for(r"C:\tasks\мой.rzp", "abc")
        self.assertEqual(
            cmd,
            r'"C:\Rz\Rizpaq.exe" --task "C:\tasks\мой.rzp" --job "abc"',
        )
        self.assertNotIn("--if-changed", cmd)

    def test_if_changed_flag(self):
        with mock.patch.object(
            S, "_rizpaq_cmd", return_value=r'"C:\Rz\Rizpaq.exe"'
        ):
            cmd = S._exec_cmd_for(r"C:\tasks\t.rzp", "abc", if_changed=True)
        self.assertTrue(cmd.endswith(' --if-changed'))
        self.assertIn('"C:\\tasks\\t.rzp"', cmd)
        self.assertIn('--job "abc"', cmd)

    def test_path_with_spaces_stays_quoted(self):
        with mock.patch.object(S, "_rizpaq_cmd", return_value="rizpaq"):
            cmd = S._exec_cmd_for(r"C:\My Tasks\tasks.rzp", "j1")
        self.assertIn('--task "C:\\My Tasks\\tasks.rzp"', cmd)


class TestCreateScheduledTaskContinuous(unittest.TestCase):
    def setUp(self):
        self._real_name = S.os.name
        S.os.name = "nt"
        self.addCleanup(self._restore_os_name)

    def _restore_os_name(self):
        S.os.name = self._real_name

    def _create(self, schedule):
        with mock.patch.object(
            S, "_schtasks_bin", return_value="schtasks.exe"
        ), mock.patch.object(
            S, "_rizpaq_cmd", return_value=r'"C:\Rz\Rizpaq.exe"'
        ), mock.patch.object(
            S, "_run_schtasks", return_value=SimpleNamespace(returncode=0)
        ) as run:
            ok = S.create_scheduled_task(
                r"C:\tasks\t.rzp", _work(), _job(), schedule
            )
        return ok, (run.call_args[0][0] if run.call_args else None)

    def test_continuous_uses_minute_schedule_and_if_changed(self):
        ok, cmd = self._create({
            "enabled": True,
            "frequency": "continuous",
            "interval": 5,
            "time": "00:00",
        })
        self.assertTrue(ok)
        self.assertEqual(_value_after(cmd, "/sc"), "minute")
        self.assertEqual(_value_after(cmd, "/mo"), "5")
        self.assertEqual(_value_after(cmd, "/st"), "00:00")
        self.assertIn("--if-changed", _value_after(cmd, "/tr"))
        self.assertIn("/f", cmd)

    def test_continuous_interval_is_clamped(self):
        for given, expected in ((0, "1"), (-10, "1"), (999, "60")):
            with self.subTest(given=given):
                ok, cmd = self._create({
                    "enabled": True,
                    "frequency": "continuous",
                    "interval": given,
                })
                self.assertTrue(ok)
                self.assertEqual(_value_after(cmd, "/mo"), expected)

    def test_continuous_without_time_defaults_to_midnight(self):
        ok, cmd = self._create({
            "enabled": True,
            "frequency": "continuous",
            "interval": 3,
        })
        self.assertTrue(ok)
        self.assertEqual(_value_after(cmd, "/st"), "00:00")

    def test_other_schedules_do_not_get_if_changed(self):
        cases = [
            {"frequency": "minute", "interval": 15},
            {"frequency": "hourly", "interval": 2},
            {"frequency": "daily", "interval": 1, "time": "10:00"},
        ]
        for schedule in cases:
            with self.subTest(frequency=schedule["frequency"]):
                schedule = dict(schedule, enabled=True)
                ok, cmd = self._create(schedule)
                self.assertTrue(ok)
                self.assertNotIn("--if-changed", _value_after(cmd, "/tr"))

    def test_disabled_schedule_removes_task(self):
        with mock.patch.object(
            S, "remove_scheduled_task", return_value=True
        ) as remove, mock.patch.object(S, "_run_schtasks") as run:
            ok = S.create_scheduled_task(
                r"C:\tasks\t.rzp", _work(), _job(), {"enabled": False}
            )
        self.assertTrue(ok)
        remove.assert_called_once()
        run.assert_not_called()

    def test_empty_schedule_removes_task(self):
        with mock.patch.object(
            S, "remove_scheduled_task", return_value=True
        ) as remove:
            ok = S.create_scheduled_task(
                r"C:\tasks\t.rzp", _work(), _job(), {}
            )
        self.assertTrue(ok)
        remove.assert_called_once()


class TestHasTaskFlag(unittest.TestCase):
    def test_finds_flag_anywhere(self):
        rest = [r"C:\tasks\t.rzp", "--job", "j1", "--if-changed"]
        self.assertTrue(H._has_task_flag(rest, "--if-changed"))

    def test_case_insensitive(self):
        self.assertTrue(
            H._has_task_flag(["--IF-CHANGED"], "--if-changed")
        )

    def test_whitespace_around_flag(self):
        self.assertTrue(
            H._has_task_flag(["  --if-changed  "], "--if-changed")
        )

    def test_missing_or_empty(self):
        self.assertFalse(H._has_task_flag([], "--if-changed"))
        self.assertFalse(H._has_task_flag(None, "--if-changed"))
        self.assertFalse(
            H._has_task_flag(["--job", "j1"], "--if-changed")
        )

    def test_exact_match_only(self):
        self.assertFalse(
            H._has_task_flag(["--if-changed=1"], "--if-changed")
        )
        self.assertFalse(
            H._has_task_flag([r"C:\--if-changed"], "--if-changed")
        )

    def test_empty_flag_never_matches(self):
        self.assertFalse(H._has_task_flag(["--if-changed"], ""))


class TestContinuousPrecheck(unittest.TestCase):
    def _run(self, rc, log="", sources=None, password=None):
        with mock.patch(
            "core.zpaq_cli.run_zpaq", return_value=(rc, log)
        ) as run:
            result = H._continuous_precheck(
                "zpaq",
                r"C:\arc\a.zpaq",
                password,
                sources if sources is not None else [r"D:\Docs"],
            )
        return result, run

    def test_rc_zero_means_skip(self):
        (decision, rc, log, cmd), run = self._run(0, "same")
        self.assertEqual(decision, "skip")
        self.assertEqual(rc, 0)
        self.assertEqual(log, "same")
        self.assertEqual(cmd[:3], ["zpaq", "sync", r"C:\arc\a.zpaq"])
        self.assertEqual(cmd[-1], r"D:\Docs")
        run.assert_called_once()

    def test_rc_two_means_run(self):
        (decision, rc, log, cmd), _ = self._run(2, "differences")
        self.assertEqual(decision, "run")
        self.assertEqual(rc, 2)

    def test_other_rc_means_error(self):
        for rc in (1, 3, 128):
            with self.subTest(rc=rc):
                (decision, got_rc, log, cmd), _ = self._run(rc, "boom")
                self.assertEqual(decision, "error")
                self.assertEqual(got_rc, rc)
                self.assertEqual(log, "boom")

    def test_all_sources_are_passed(self):
        sources = [r"D:\Photos", r"D:\Docs"]
        (decision, rc, log, cmd), _ = self._run(2, sources=sources)
        self.assertEqual(decision, "run")
        self.assertEqual(cmd[3:], sources)

    def test_password_is_kept(self):
        (decision, rc, log, cmd), _ = self._run(2, password="secret")
        self.assertEqual(decision, "run")
        self.assertEqual(cmd[-2:], ["-key", "secret"])

    def test_empty_log_becomes_empty_string(self):
        (decision, rc, log, cmd), _ = self._run(0, None)
        self.assertEqual(log, "")


class TestContinuousPresentation(unittest.TestCase):
    @staticmethod
    def _fake_tr(key, **params):
        if not params:
            return key
        parts = ",".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{key}|{parts}"

    def _format(self, schedule):
        with mock.patch.object(P, "tr", self._fake_tr):
            return P.format_schedule(schedule)

    def test_continuous_every_minute(self):
        self.assertEqual(
            self._format({
                "enabled": True,
                "frequency": "continuous",
                "interval": 1,
            }),
            "sched.fmt.continuous_one",
        )

    def test_continuous_interval(self):
        self.assertEqual(
            self._format({
                "enabled": True,
                "frequency": "continuous",
                "interval": 5,
            }),
            "sched.fmt.continuous_n|n=5",
        )

    def test_invalid_interval_falls_back_to_one(self):
        self.assertEqual(
            self._format({
                "enabled": True,
                "frequency": "continuous",
                "interval": "bad",
            }),
            "sched.fmt.continuous_one",
        )

    def test_disabled_is_dash(self):
        self.assertEqual(
            self._format({
                "enabled": False,
                "frequency": "continuous",
                "interval": 5,
            }),
            "sched.fmt.none",
        )

    def test_unknown_frequency_is_dash(self):
        self.assertEqual(
            self._format({
                "enabled": True,
                "frequency": "future",
            }),
            "sched.fmt.none",
        )


class TestDashboardSilence(unittest.TestCase):
    def test_continuous_is_a_minute_interval(self):
        pass
        self.assertEqual(DA._INTERVAL_SECONDS["continuous"], 60)


if __name__ == "__main__":
    unittest.main(verbosity=2)
