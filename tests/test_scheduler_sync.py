






























from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import scheduler as S              
from core.tasks import (              
    ACTION_TEST,
    add_job,
    add_work,
    empty_container,
    scheduler_task_name,
)


def _make_container(works_spec) -> dict:
    pass






    c = empty_container()
    for w_spec in works_spec:
        w = add_work(
            c,
            title=w_spec["title"],
            sources=w_spec.get("sources") or ["D:/src"],
            dest=w_spec.get("dest") or "D:/out.zpaq",
        )
        for j_spec in w_spec.get("jobs") or []:
            add_job(c, w["id"], j_spec)
    return c


def _scheduler_entry(work: dict, job: dict, status="Ready",
                     next_run="2026-10-05 02:00") -> dict:
    pass
    return {
        "name": scheduler_task_name(work, job),
        "status": status,
        "next_run": next_run,
    }


def _patch_tasks(tasks):
    pass
    return mock.patch.object(S, "list_rizpaq_tasks", return_value=list(tasks))


                                                                               

class TestContainerTaskMap(unittest.TestCase):
    def test_empty_container_gives_empty_map(self):
        self.assertEqual(S.container_task_map({}), {})

    def test_container_without_jobs(self):
        c = _make_container([{"title": "W", "jobs": []}])
        self.assertEqual(S.container_task_map(c), {})

    def test_single_job(self):
        c = _make_container([{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
        m = S.container_task_map(c)
        self.assertEqual(len(m), 1)
        name, pair = next(iter(m.items()))
        work, job = pair
        self.assertEqual(work["title"], "Docs")
        self.assertEqual(job["title"], "Daily")
                                                             
        self.assertEqual(name, scheduler_task_name(work, job))

    def test_several_jobs_one_work(self):
        c = _make_container([{
            "title": "Docs",
            "jobs": [{"title": "Daily"}, {"title": "Weekly"}],
        }])
        self.assertEqual(len(S.container_task_map(c)), 2)

    def test_jobs_of_different_works_do_not_collide(self):
        c = _make_container([
            {"title": "Docs", "jobs": [{"title": "Daily"}]},
            {"title": "Photos", "jobs": [{"title": "Daily"}]},
        ])
        self.assertEqual(len(S.container_task_map(c)), 2)

    def test_mixed_actions_in_one_work(self):
        pass



        c = _make_container([{
            "title": "Docs",
            "jobs": [
                {"title": "Backup", "action": "backup"},
                {"title": "Check", "action": ACTION_TEST},
            ],
        }])
        m = S.container_task_map(c)
        self.assertEqual(len(m), 2)
        names = list(m.keys())
        self.assertTrue(any("_b_" in n for n in names),
                        f"нет имени с префиксом b_: {names}")
        self.assertTrue(any("_t_" in n for n in names),
                        f"нет имени с префиксом t_: {names}")

    def test_test_job_name_matches_scheduler_task_name(self):
        pass




        c = _make_container([{
            "title": "Docs",
            "jobs": [{"title": "Check", "action": ACTION_TEST}],
        }])
        m = S.container_task_map(c)
        name, pair = next(iter(m.items()))
        work, job = pair
        self.assertEqual(name, scheduler_task_name(work, job))
        self.assertEqual(job["action"], ACTION_TEST)

    def test_outside_windows_gives_empty_map(self):
        real_name = S.os.name
        try:
            S.os.name = "posix"
            c = _make_container([{
                "title": "Docs",
                "jobs": [{"title": "Daily"}],
            }])
            self.assertEqual(S.container_task_map(c), {})
        finally:
            S.os.name = real_name


                                                                              

class TestFindOrphanTasks(unittest.TestCase):
    def test_no_orphans_when_all_match(self):
        c = _make_container([{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
        work = c["works"][0]
        job = work["jobs"][0]
        with _patch_tasks([_scheduler_entry(work, job)]):
            self.assertEqual(S.find_orphan_tasks(c), [])

    def test_test_job_in_scheduler_is_not_orphan(self):
        pass




        c = _make_container([{
            "title": "Docs",
            "jobs": [{"title": "Check", "action": ACTION_TEST}],
        }])
        work = c["works"][0]
        job = work["jobs"][0]
        with _patch_tasks([_scheduler_entry(work, job)]):
            self.assertEqual(S.find_orphan_tasks(c), [])

    def test_all_orphans_when_container_empty(self):
        c = empty_container()
        task = {"name": "Rizpaq_b_old_aaaaaaaa_bbbbbbbb",
                "status": "Ready", "next_run": ""}
        with _patch_tasks([task]):
            orphans = S.find_orphan_tasks(c)
            self.assertEqual(len(orphans), 1)
            self.assertEqual(orphans[0]["name"], task["name"])

    def test_only_unmatched_are_orphans(self):
        c = _make_container([{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
        work = c["works"][0]
        job = work["jobs"][0]
        known = _scheduler_entry(work, job)
        orphan = {"name": "Rizpaq_b_ghost_00000000_11111111",
                  "status": "", "next_run": ""}
        with _patch_tasks([known, orphan]):
            result = S.find_orphan_tasks(c)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["name"], orphan["name"])

    def test_orphan_ignores_non_rizpaq_prefix(self):
        pass





        c = empty_container()
                                                                         
        with _patch_tasks([]):
            self.assertEqual(S.find_orphan_tasks(c), [])

    def test_outside_windows_gives_empty_list(self):
        real_name = S.os.name
        try:
            S.os.name = "posix"
            c = empty_container()
            task = {"name": "Rizpaq_b_x_12345678_abcdef00",
                    "status": "", "next_run": ""}
            with _patch_tasks([task]):
                self.assertEqual(S.find_orphan_tasks(c), [])
        finally:
            S.os.name = real_name


                                                                                 

class TestComputeSyncActions(unittest.TestCase):
    def _empty_actions(self):
        return {"add": [], "remove": [], "disable": []}

    def test_outside_windows_returns_empty(self):
        real_name = S.os.name
        try:
            S.os.name = "posix"
            self.assertEqual(
                S.compute_sync_actions({}, "D:/tasks.rzp"),
                self._empty_actions(),
            )
        finally:
            S.os.name = real_name

    def test_no_differences(self):
        c = _make_container([{
            "title": "Docs",
            "jobs": [{
                "title": "Daily",
                "schedule": {"enabled": True, "frequency": "daily",
                             "time": "02:00", "interval": 1},
            }],
        }])
        work = c["works"][0]
        job = work["jobs"][0]
        with _patch_tasks([_scheduler_entry(work, job)]):
            actions = S.compute_sync_actions(c, "D:/tasks.rzp")
            self.assertEqual(actions["add"], [])
            self.assertEqual(actions["remove"], [])
            self.assertEqual(actions["disable"], [])

    def test_add_when_enabled_but_missing_in_scheduler(self):
        c = _make_container([{
            "title": "Docs",
            "jobs": [{
                "title": "Daily",
                "schedule": {"enabled": True, "frequency": "daily",
                             "time": "02:00", "interval": 1},
            }],
        }])
        with _patch_tasks([]):
            actions = S.compute_sync_actions(c, "D:/tasks.rzp")
            self.assertEqual(len(actions["add"]), 1)
            work, job = actions["add"][0]
            self.assertEqual(job["title"], "Daily")
            self.assertEqual(actions["remove"], [])
            self.assertEqual(actions["disable"], [])

    def test_add_test_job_with_enabled_schedule(self):
        pass




        c = _make_container([{
            "title": "Docs",
            "jobs": [{
                "title": "Check",
                "action": ACTION_TEST,
                "schedule": {"enabled": True, "frequency": "daily",
                             "time": "03:00", "interval": 1},
            }],
        }])
        with _patch_tasks([]):
            actions = S.compute_sync_actions(c, "D:/tasks.rzp")
            self.assertEqual(len(actions["add"]), 1)
            work, job = actions["add"][0]
            self.assertEqual(job["action"], ACTION_TEST)

    def test_disable_when_schedule_off_but_still_in_scheduler(self):
        pass




        c = _make_container([{
            "title": "Docs",
            "jobs": [{
                "title": "Daily",
                "schedule": {"enabled": False},
            }],
        }])
        work = c["works"][0]
        job = work["jobs"][0]
        with _patch_tasks([_scheduler_entry(work, job)]):
            actions = S.compute_sync_actions(c, "D:/tasks.rzp")
            self.assertEqual(len(actions["disable"]), 1)
            work2, job2 = actions["disable"][0]
            self.assertEqual(job2["title"], "Daily")
            self.assertEqual(actions["add"], [])
            self.assertEqual(actions["remove"], [])

    def test_remove_when_task_has_no_job(self):
        c = _make_container([{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
                                                       
        orphan_entry = {
            "name": "Rizpaq_b_ghost_00000000_deadbeef",
            "status": "", "next_run": "",
        }
        with _patch_tasks([orphan_entry]):
            actions = S.compute_sync_actions(c, "D:/tasks.rzp")
            self.assertEqual(len(actions["remove"]), 1)
            self.assertEqual(actions["remove"][0]["name"],
                             orphan_entry["name"])
                                                                        
                                                                       
                                        
            self.assertEqual(actions["add"], [])
            self.assertEqual(actions["disable"], [])

    def test_all_three_categories_at_once(self):
        pass



        c = _make_container([
            {"title": "Docs", "jobs": [{
                "title": "Daily",
                "schedule": {"enabled": True, "frequency": "daily",
                             "time": "02:00", "interval": 1},
            }]},
            {"title": "Photos", "jobs": [{
                "title": "Weekly",
                "schedule": {"enabled": False},
            }]},
        ])
                                                                        
        docs_work = c["works"][0]
        docs_job = docs_work["jobs"][0]
        daily_entry = _scheduler_entry(docs_work, docs_job)

                                                                  
                    
        photos_work = c["works"][1]
        photos_job = photos_work["jobs"][0]
        photos_entry = _scheduler_entry(photos_work, photos_job)

                               
        ghost = {"name": "Rizpaq_b_ghost_00000000_deadbeef",
                 "status": "", "next_run": ""}

                                                                     
                                    
                                                         
        extra = add_work(c, "Videos", ["D:/video"], "D:/video.zpaq")
        add_job(c, extra["id"], {
            "title": "Hourly",
            "schedule": {"enabled": True, "frequency": "hourly",
                         "time": "00:00", "interval": 1},
        })

        with _patch_tasks([daily_entry, photos_entry, ghost]):
            actions = S.compute_sync_actions(c, "D:/tasks.rzp")
            self.assertEqual(len(actions["add"]), 1)
            self.assertEqual(actions["add"][0][1]["title"], "Hourly")
            self.assertEqual(len(actions["disable"]), 1)
            self.assertEqual(actions["disable"][0][1]["title"], "Weekly")
            self.assertEqual(len(actions["remove"]), 1)
            self.assertEqual(actions["remove"][0]["name"], ghost["name"])

    def test_remove_uses_name_not_tuple(self):
        pass



        c = empty_container()
        ghost = {"name": "Rizpaq_b_x_00000000_00000000",
                 "status": "Ready", "next_run": "2026-10-05 02:00"}
        with _patch_tasks([ghost]):
            actions = S.compute_sync_actions(c, "D:/tasks.rzp")
            self.assertEqual(len(actions["remove"]), 1)
            self.assertIsInstance(actions["remove"][0], dict)
            self.assertIn("name", actions["remove"][0])

    def test_two_jobs_same_work_do_not_cross(self):
        pass



        c = _make_container([{
            "title": "Docs",
            "jobs": [
                {"title": "Enabled", "schedule": {
                    "enabled": True, "frequency": "daily",
                    "time": "02:00", "interval": 1,
                }},
                {"title": "Disabled", "schedule": {"enabled": False}},
            ],
        }])
        work = c["works"][0]
        disabled_job = work["jobs"][1]
                                                                 
        with _patch_tasks([_scheduler_entry(work, disabled_job)]):
            actions = S.compute_sync_actions(c, "D:/tasks.rzp")
            self.assertEqual(len(actions["add"]), 1)
            self.assertEqual(actions["add"][0][1]["title"], "Enabled")
            self.assertEqual(len(actions["disable"]), 1)
            self.assertEqual(actions["disable"][0][1]["title"], "Disabled")
            self.assertEqual(actions["remove"], [])

    def test_two_jobs_one_work_different_actions(self):
        pass




        c = _make_container([{
            "title": "Docs",
            "jobs": [
                {"title": "Backup", "action": "backup",
                 "schedule": {"enabled": True, "frequency": "daily",
                              "time": "02:00", "interval": 1}},
                {"title": "Check", "action": ACTION_TEST,
                 "schedule": {"enabled": True, "frequency": "daily",
                              "time": "03:00", "interval": 1}},
            ],
        }])
        with _patch_tasks([]):
            actions = S.compute_sync_actions(c, "D:/tasks.rzp")
            self.assertEqual(len(actions["add"]), 2)
            titles = {job["title"] for _w, job in actions["add"]}
            self.assertEqual(titles, {"Backup", "Check"})

    def test_test_job_in_scheduler_is_matched(self):
        pass



        c = _make_container([{
            "title": "Docs",
            "jobs": [{
                "title": "Check",
                "action": ACTION_TEST,
                "schedule": {"enabled": True, "frequency": "daily",
                             "time": "03:00", "interval": 1},
            }],
        }])
        work = c["works"][0]
        job = work["jobs"][0]
        with _patch_tasks([_scheduler_entry(work, job)]):
            actions = S.compute_sync_actions(c, "D:/tasks.rzp")
            self.assertEqual(actions["add"], [])
            self.assertEqual(actions["remove"], [])
            self.assertEqual(actions["disable"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
