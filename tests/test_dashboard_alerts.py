from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import dashboard_alerts as DA
from core.run_history import RunEntry


def _work(work_id="w1", dest="", sources=(), jobs=(), **extra):
    w = {"id": work_id, "title": "Работа " + work_id, "dest": dest,
         "sources": list(sources), "jobs": list(jobs)}
    w.update(extra)
    return w


def _job(job_id="j1", **extra):
    j = {"id": job_id, "title": "Задание " + job_id, "action": "backup"}
    j.update(extra)
    return j


def _entry(job_id="j1", status="ok", minutes_ago=0, action="backup"):
    dt = datetime.now() - timedelta(minutes=minutes_ago)
    return RunEntry(ts=dt.strftime("%Y-%m-%d %H:%M:%S"), ts_dt=dt,
                    work_id="w1", job_id=job_id, job_title="J",
                    action=action, rc=0, status=status)


class TestPar2Outdated(unittest.TestCase):
    def test_outdated_when_grew(self):
        tmp = Path(tempfile.mkdtemp(prefix="alerts_out_"))
        dest = tmp / "a.zpaq"
        dest.write_bytes(b"x" * 1000)
        Path(str(dest) + ".par2").write_bytes(b"x" * 16)
        w = _work(dest=str(dest), par2_size=500, jobs=[_job()])
        kinds = [a.kind for a in DA.collect_alerts(
            {"works": [w]}, [])]
        self.assertIn("par2_outdated", kinds)
        alert = next(a for a in DA.collect_alerts({"works": [w]}, [])
                     if a.kind == "par2_outdated")
        self.assertEqual(alert.work_id, "w1")

    def test_fresh_set_no_alert(self):
        tmp = Path(tempfile.mkdtemp(prefix="alerts_ok_"))
        dest = tmp / "a.zpaq"
        dest.write_bytes(b"x" * 1000)
        Path(str(dest) + ".par2").write_bytes(b"x" * 16)
        w = _work(dest=str(dest), par2_size=2000, jobs=[_job()])
        kinds = [a.kind for a in DA.collect_alerts(
            {"works": [w]}, [])]
        self.assertNotIn("par2_outdated", kinds)

    def test_no_set_no_outdated(self):
        tmp = Path(tempfile.mkdtemp(prefix="alerts_ns_"))
        dest = tmp / "a.zpaq"
        dest.write_bytes(b"x" * 1000)
        w = _work(dest=str(dest), par2_size=1, jobs=[_job()])
        kinds = [a.kind for a in DA.collect_alerts(
            {"works": [w]}, [])]
        self.assertNotIn("par2_outdated", kinds)


class TestMissing(unittest.TestCase):
    def test_source_missing(self):
        w = _work(dest="", sources=[r"Z:\точно\нет\папка"],
                  jobs=[_job()])
        kinds = [a.kind for a in DA.collect_alerts({"works": [w]}, [])]
        self.assertIn("source_missing", kinds)

    def test_source_present_no_alert(self):
        tmp = tempfile.mkdtemp(prefix="alerts_src_")
        w = _work(dest="", sources=[tmp], jobs=[_job()])
        kinds = [a.kind for a in DA.collect_alerts({"works": [w]}, [])]
        self.assertNotIn("source_missing", kinds)

    def test_archive_missing_only_after_run(self):

        w = _work(dest=r"Q:\нет\такого\a.zpaq", jobs=[_job()])
        kinds = [a.kind for a in DA.collect_alerts({"works": [w]}, [])]
        self.assertNotIn("archive_missing", kinds)

        w2 = _work(dest=r"Q:\нет\такого\a.zpaq",
                   jobs=[_job(run_count=3, last_run="2026-10-01 10:00:00")])
        kinds2 = [a.kind for a in DA.collect_alerts({"works": [w2]}, [])]
        self.assertIn("archive_missing", kinds2)


class TestSharedDest(unittest.TestCase):
    def test_two_works_same_dest(self):
        w1 = _work("w1", dest=r"D:\Backup\same.zpaq", jobs=[_job("j1")])
        w2 = _work("w2", dest=r"d:\backup\SAME.zpaq", jobs=[_job("j2")])
        alerts = DA.collect_alerts({"works": [w1, w2]}, [])
        shared = [a for a in alerts if a.kind == "shared_dest"]
        self.assertEqual(len(shared), 2)
        self.assertEqual({a.work_id for a in shared}, {"w1", "w2"})


class TestPar2Check(unittest.TestCase):
    def _with_set(self, tmpname):
        tmp = Path(tempfile.mkdtemp(prefix=tmpname))
        dest = tmp / "a.zpaq"
        dest.write_bytes(b"x" * 100)
        Path(str(dest) + ".par2").write_bytes(b"x" * 16)
        return str(dest)

    def test_never_checked(self):
        dest = self._with_set("alerts_nev_")
        w = _work(dest=dest, par2_size=100, jobs=[_job()])
        kinds = [a.kind for a in DA.collect_alerts({"works": [w]}, [])]
        self.assertIn("par2_check_old", kinds)
        alert = next(a for a in DA.collect_alerts({"works": [w]}, [])
                     if a.kind == "par2_check_old")
        self.assertEqual(alert.text_key, "dashboard.alerts.par2_check_never")

    def test_checked_recently_no_alert(self):
        dest = self._with_set("alerts_rec_")

        j = _job("jpar2", action="test", test_mode="par2",
                 last_run=(datetime.now()
                           - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"))
        w = _work(dest=dest, par2_size=100, jobs=[_job(), j])
        kinds = [a.kind for a in DA.collect_alerts({"works": [w]}, [])]
        self.assertNotIn("par2_check_old", kinds)

    def test_checked_long_ago(self):
        dest = self._with_set("alerts_old_")
        j = _job("jpar2", action="test", test_mode="par2",
                 last_run=(datetime.now()
                           - timedelta(days=45)).strftime("%Y-%m-%d %H:%M:%S"))
        w = _work(dest=dest, par2_size=100, jobs=[j])
        alert = next(a for a in DA.collect_alerts({"works": [w]}, [])
                     if a.kind == "par2_check_old")
        self.assertEqual(alert.params.get("days"), 45)


class TestJobSilent(unittest.TestCase):
    def test_hourly_silent(self):
        j = _job("j1", schedule={"enabled": True, "frequency": "hourly",
                                 "interval": 1})

        history = [_entry("j1", "ok", minutes_ago=48 * 60)]
        alerts = DA.collect_alerts({"works": [_work(jobs=[j])]}, history)
        silent = [a for a in alerts if a.kind == "job_silent"]
        self.assertEqual(len(silent), 1)
        self.assertEqual(silent[0].params["job"], "Задание j1")

    def test_recent_run_no_alert(self):
        j = _job("j1", schedule={"enabled": True, "frequency": "hourly",
                                 "interval": 1})
        history = [_entry("j1", "ok", minutes_ago=30)]
        alerts = DA.collect_alerts({"works": [_work(jobs=[j])]}, history)
        self.assertEqual([a for a in alerts if a.kind == "job_silent"], [])

    def test_disabled_schedule_no_alert(self):
        j = _job("j1", schedule={"enabled": False, "frequency": "hourly"})
        history = [_entry("j1", "ok", minutes_ago=48 * 60)]
        alerts = DA.collect_alerts({"works": [_work(jobs=[j])]}, history)
        self.assertEqual([a for a in alerts if a.kind == "job_silent"], [])


class TestStreaks(unittest.TestCase):
    def test_streaks_basic(self):
        history = [
            _entry("j1", "ok", minutes_ago=30),
            _entry("j1", "ok", minutes_ago=20),
            _entry("j1", "error", minutes_ago=10),
            _entry("j2", "ok", minutes_ago=30),
            _entry("j2", "ok", minutes_ago=20),
            _entry("j2", "ok", minutes_ago=10),
            _entry("j3", "busy", minutes_ago=10),
        ]
        streaks = DA.job_streaks(history)
        self.assertEqual(streaks["j1"], ("error", 1))
        self.assertEqual(streaks["j2"], ("ok", 3))
        self.assertNotIn("j3", streaks)

    def test_order_independent(self):

        history = [
            _entry("j1", "ok", minutes_ago=30),
            _entry("j1", "error", minutes_ago=20),
            _entry("j1", "error", minutes_ago=10),
        ]
        self.assertEqual(DA.job_streaks(history)["j1"], ("error", 2))


class TestIsOutdated(unittest.TestCase):
    def test_helper(self):
        self.assertFalse(DA.is_set_outdated(None, 100))
        self.assertFalse(DA.is_set_outdated(0, 100))
        self.assertFalse(DA.is_set_outdated(100, 100))
        self.assertTrue(DA.is_set_outdated(100, 101))


class TestFreeBytes(unittest.TestCase):
    def test_existing_drive(self):
        tmp = tempfile.mkdtemp(prefix="alerts_free_")
        free = DA.free_bytes(tmp)
        self.assertIsNotNone(free)
        self.assertGreater(free, 0)

    def test_missing_path(self):


        try:
            free = DA.free_bytes(r"Q:\нет\такого")
        except Exception as exc:
            self.fail(f"free_bytes raised: {exc}")
        else:
            self.assertTrue(free is None or free >= 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
