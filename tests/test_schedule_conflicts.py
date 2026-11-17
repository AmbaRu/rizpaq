






from __future__ import annotations

import unittest
from datetime import datetime

from core.schedule_conflicts import (
    find_conflicts,
    occurrence_minutes,
    schedules_overlap,
)

NOW = datetime(2026, 11, 17, 12, 0, 0)


def sched(freq="hourly", interval=1, time="00:00", enabled=True, **kw):
    d = {"enabled": enabled, "frequency": freq, "interval": interval, "time": time}
    d.update(kw)
    return d


class TestOccurrences(unittest.TestCase):
    def test_disabled_gives_nothing(self):
        self.assertEqual(occurrence_minutes(sched(enabled=False), NOW), set())

    def test_hourly_starts_at_top_of_hour(self):
        minutes = occurrence_minutes(sched("hourly", 1, "00:00"), NOW)
        self.assertIn(0, minutes)
        self.assertIn(60, minutes)
        self.assertNotIn(15, minutes)

    def test_daily_uses_time(self):
        minutes = occurrence_minutes(sched("daily", 1, "10:30"), NOW)
        self.assertIn(10 * 60 + 30, minutes)
        self.assertNotIn(10 * 60, minutes)

    def test_weekly_days(self):
        minutes = occurrence_minutes(
            sched("weekly", 1, "21:15", days=["FRI"]), NOW
        )
        self.assertTrue(minutes)
        for m in minutes:
            self.assertEqual(m % 1440, 21 * 60 + 15)


class TestOverlap(unittest.TestCase):
    def test_two_hourly_conflict(self):
        self.assertTrue(schedules_overlap(sched("hourly"), sched("hourly"), NOW))

    def test_hourly_vs_daily_at_exact_hour(self):
        self.assertTrue(schedules_overlap(
            sched("hourly", 1, "00:00"),
            sched("daily", 1, "10:00"),
            NOW,
        ))

    def test_hourly_vs_21_15_no_conflict(self):
                                                                          
        self.assertFalse(schedules_overlap(
            sched("hourly", 1, "00:00"),
            sched("weekly", 1, "21:15", days=["FRI"]),
            NOW,
        ))

    def test_disabled_other_is_not_a_conflict(self):
        self.assertFalse(schedules_overlap(
            sched("hourly"), sched("hourly", enabled=False), NOW
        ))


class TestFindConflicts(unittest.TestCase):
    def setUp(self):
        self.container = {
            "works": [
                {
                    "id": "w1", "title": "RIZPAQ", "dest": "F:/a.zpaq",
                    "jobs": [
                        {"id": "j1", "title": "Ежечасный", "action": "backup",
                         "schedule": sched("hourly")},
                        {"id": "j2", "title": "Задание", "action": "backup",
                         "schedule": sched("hourly")},
                    ],
                },
                {
                    "id": "w2", "title": "Другая", "dest": "F:/b.zpaq",
                    "jobs": [
                        {"id": "j3", "title": "Чужой архив", "action": "backup",
                         "schedule": sched("hourly")},
                    ],
                },
            ]
        }

    def test_detects_duplicate_in_same_work(self):
        work = self.container["works"][0]
        job = work["jobs"][0]
        found = find_conflicts(self.container, work, job, sched("hourly"), NOW)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["job_id"], "j2")

    def test_other_archive_ignored(self):
        work = self.container["works"][0]
        found = find_conflicts(self.container, work, work["jobs"][0], sched("hourly"), NOW)
        self.assertTrue(all(c["job_id"] != "j3" for c in found))

    def test_test_job_ignored(self):
        self.container["works"][0]["jobs"][1]["action"] = "test"
        work = self.container["works"][0]
        found = find_conflicts(self.container, work, work["jobs"][0], sched("hourly"), NOW)
        self.assertEqual(found, [])

    def test_disabled_schedule_ignored(self):
        work = self.container["works"][0]
        found = find_conflicts(
            self.container, work, work["jobs"][0], sched(enabled=False), NOW
        )
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
