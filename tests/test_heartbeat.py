
from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from core import config as config_mod
from core import heartbeat
from core.dashboard_alerts import Alert


class _TempState(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._dir = tempfile.mkdtemp(prefix="rizpaq_hb_")
        self.path = Path(self._dir) / "state.json"
        patcher = mock.patch.object(
            heartbeat, "state_path", return_value=self.path
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        import shutil

        self.addCleanup(shutil.rmtree, self._dir, ignore_errors=True)


class TestDayGuard(_TempState):
    def test_send_once_per_day(self):
        self.assertTrue(heartbeat.should_send())
        heartbeat.mark_sent()
        self.assertFalse(heartbeat.should_send())
        self.assertTrue(heartbeat.should_send(force=True))
        self.assertEqual(
            self.path.read_text(encoding="utf-8").strip().count("last_date"),
            1,
        )


class TestReport(_TempState):
    def test_alerts_are_localized_with_titles(self):
        container = {"works": [{
            "id": "w1", "title": "All", "dest": "F:/All.zpaq",
            "jobs": [{"id": "j1", "title": "Еженедельный"}],
        }]}
        alert = Alert(
            "job_silent", "w1", "j1",
            "dashboard.alerts.job_silent", {"days": 9},
        )
        with mock.patch.object(
            heartbeat.tasks, "load_container", return_value=container
        ), mock.patch.object(
            heartbeat.tasks, "container_path", return_value=Path("x.rzp")
        ), mock.patch.object(
            heartbeat.run_history, "load_history", return_value=[]
        ), mock.patch.object(
            heartbeat.dashboard_alerts, "collect_alerts", return_value=[alert]
        ):
            lines = heartbeat.build_report("D:/fake")
        self.assertEqual(len(lines), 1)
        self.assertIn("All", lines[0])
        self.assertIn("Еженедельный", lines[0])


class TestSend(_TempState):
    def _cfg(self, enabled=True):
        return config_mod.Settings(
            mail_report_enabled=enabled,
            mail_heartbeat_enabled=enabled,
            mail_smtp_server="smtp.example.com",
            mail_from="me@example.com",
            mail_to="me@example.com",
            tasks_dir="D:/fake",
        )

    def test_disabled_sends_nothing(self):
        with mock.patch.object(
            heartbeat.mail_report, "send_log_email"
        ) as send:
            rc, out = heartbeat.send_if_needed("zpaq", self._cfg(False))
        self.assertEqual((rc, out), (0, ""))
        send.assert_not_called()

    def test_sends_and_marks(self):
        cfg = self._cfg()
        with mock.patch.object(
            heartbeat, "build_report", return_value=["- problem"]
        ), mock.patch.object(
            heartbeat.mail_report, "send_log_email",
            return_value=(0, "sent"),
        ) as send:
            rc, out = heartbeat.send_if_needed("zpaq", cfg)
        self.assertEqual((rc, out), (0, "sent"))
        subject = send.call_args.args[2]
        self.assertIn("1", subject)
        self.assertFalse(heartbeat.should_send())

    def test_no_alerts_means_no_mail(self):
        with mock.patch.object(
            heartbeat, "build_report", return_value=[]
        ), mock.patch.object(
            heartbeat.mail_report, "send_log_email"
        ) as send:
            rc, out = heartbeat.send_if_needed("zpaq", self._cfg())
        self.assertEqual((rc, out), (0, ""))
        send.assert_not_called()

    def test_forced_empty_report_still_sends(self):
        with mock.patch.object(
            heartbeat, "build_report", return_value=[]
        ), mock.patch.object(
            heartbeat.mail_report, "send_log_email", return_value=(0, "sent")
        ) as send:
            rc, out = heartbeat.send_if_needed("zpaq", self._cfg(), force=True)
        self.assertEqual(rc, 0)
        body = send.call_args.args[3]
        self.assertIn("Проблем не обнаружено", body)


if __name__ == "__main__":
    unittest.main()
