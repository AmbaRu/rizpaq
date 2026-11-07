

































from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import tasks as T              


class _TmpDir(unittest.TestCase):
    pass

    def setUp(self):
        import shutil

        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_rzp_test_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.path = self.dir / "tasks.rzp"

    def read_raw(self) -> str:
        return self.path.read_text(encoding="utf-8")

    def write_raw(self, text: str) -> None:
        self.path.write_text(text, encoding="utf-8")


class TestContainerBasics(_TmpDir):
    def test_empty_container_has_format_and_version(self):
        c = T.empty_container()
        self.assertEqual(c["format"], T.CONTAINER_FORMAT)
        self.assertEqual(c["version"], T.CONTAINER_VERSION)
        self.assertIsInstance(c["works"], list)
        self.assertEqual(c["works"], [])

    def test_container_name_constant(self):
        pass
        self.assertEqual(T.CONTAINER_NAME, "tasks.rzp")

    def test_container_path_helper(self):
        p = T.container_path(self.dir)
        self.assertEqual(p.name, "tasks.rzp")
        self.assertEqual(p.parent, self.dir)

    def test_missing_file_yields_empty_container(self):
        c = T.load_container(self.path)             
        self.assertEqual(c["works"], [])

    def test_save_then_load_roundtrip(self):
        c = T.empty_container()
        T.add_work(c, "Работа 1", ["D:/docs"], "D:/backup.zpaq")
        T.save_container(self.path, c)

        loaded = T.load_container(self.path)
        self.assertEqual(len(loaded["works"]), 1)
        w = loaded["works"][0]
        self.assertEqual(w["title"], "Работа 1")
        self.assertEqual(w["sources"], ["D:/docs"])
        self.assertEqual(w["dest"], "D:/backup.zpaq")

    def test_file_is_valid_json(self):
        c = T.empty_container()
        T.add_work(c, "x", ["D:/y"], "D:/z.zpaq")
        T.save_container(self.path, c)
        data = json.loads(self.read_raw())
        self.assertEqual(data["format"], T.CONTAINER_FORMAT)

    def test_save_creates_missing_dir(self):
        deep = self.dir / "a" / "b" / "c"
        c = T.empty_container()
        T.add_work(c, "x", ["D:/y"], "D:/z.zpaq")
        T.save_container(T.container_path(deep), c)
        self.assertTrue((deep / "tasks.rzp").is_file())


class TestContainerRobustness(_TmpDir):
    def test_corrupt_json_yields_empty(self):
        self.write_raw("{ this is not json")
        c = T.load_container(self.path)
        self.assertEqual(c["works"], [])

    def test_wrong_format_yields_empty(self):
        self.write_raw(json.dumps({"format": "rizpaq.backup-task", "works": []}))
        c = T.load_container(self.path)
        self.assertEqual(c["works"], [])

    def test_missing_works_list_yields_empty(self):
        self.write_raw(json.dumps({"format": T.CONTAINER_FORMAT, "version": 1}))
        c = T.load_container(self.path)
        self.assertEqual(c["works"], [])

    def test_unknown_fields_ignored(self):
        pass
        self.write_raw(json.dumps({
            "format": T.CONTAINER_FORMAT,
            "version": 999,
            "future_field": "???",
            "works": [{
                "id": "w1",
                "title": "Работа",
                "sources": ["D:/a"],
                "dest": "D:/b.zpaq",
                "future": {"nested": True},
                "jobs": [],
            }],
        }))
        c = T.load_container(self.path)
        self.assertEqual(len(c["works"]), 1)
        self.assertEqual(c["works"][0]["id"], "w1")

    def test_work_without_id_is_dropped(self):
        pass
        self.write_raw(json.dumps({
            "format": T.CONTAINER_FORMAT,
            "version": 1,
            "works": [
                {"title": "без id"},
                {"id": "w1", "title": "с id", "jobs": []},
            ],
        }))
        c = T.load_container(self.path)
        self.assertEqual(len(c["works"]), 1)
        self.assertEqual(c["works"][0]["id"], "w1")

    def test_job_without_id_is_dropped(self):
        self.write_raw(json.dumps({
            "format": T.CONTAINER_FORMAT,
            "version": 1,
            "works": [{
                "id": "w1", "title": "Работа", "jobs": [
                    {"title": "без id"},
                    {"id": "j1", "title": "с id"},
                ],
            }],
        }))
        c = T.load_container(self.path)
        self.assertEqual(len(c["works"][0]["jobs"]), 1)
        self.assertEqual(c["works"][0]["jobs"][0]["id"], "j1")


class TestWorks(_TmpDir):
    def test_add_work(self):
        c = T.empty_container()
        w = T.add_work(
            c, "Docs", ["D:/Docs", "D:/Other"], "D:/backup.zpaq",
            password="secret", only_masks=["*.txt"], not_masks=["*.tmp"],
            comment="weekly",
        )
        self.assertTrue(w["id"])
        self.assertEqual(w["title"], "Docs")
        self.assertEqual(w["sources"], ["D:/Docs", "D:/Other"])
        self.assertEqual(w["dest"], "D:/backup.zpaq")
        self.assertEqual(w["only_masks"], ["*.txt"])
        self.assertEqual(w["not_masks"], ["*.tmp"])
        self.assertEqual(w["comment"], "weekly")
        self.assertIsNotNone(w["password_b64"])
        self.assertEqual(w["jobs"], [])

    def test_password_not_stored_in_clear(self):
        c = T.empty_container()
        T.add_work(c, "x", ["D:/a"], "D:/b.zpaq", password="mysecret")
        T.save_container(self.path, c)
        self.assertNotIn("mysecret", self.read_raw())

    def test_work_title_defaults(self):
        c = T.empty_container()
        w = T.add_work(c, "", ["D:/a"], "D:/b.zpaq")
        self.assertEqual(w["title"], "Работа")

    def test_work_sources_cleaned(self):
        pass
        c = T.empty_container()
        w = T.add_work(c, "x", ["D:/a", "", "  ", "D:/b"], "D:/c.zpaq")
        self.assertEqual(w["sources"], ["D:/a", "D:/b"])

    def test_update_work(self):
        c = T.empty_container()
        w = T.add_work(c, "A", ["D:/a"], "D:/b.zpaq")
        T.update_work(c, w["id"], title="B", comment="new comment")
        self.assertEqual(w["title"], "B")
        self.assertEqual(w["comment"], "new comment")

    def test_update_work_password_via_plain_key(self):
        pass
        c = T.empty_container()
        w = T.add_work(c, "A", ["D:/a"], "D:/b.zpaq")
        self.assertIsNone(w["password_b64"])
        T.update_work(c, w["id"], password="newsecret")
        self.assertIsNotNone(w["password_b64"])
                                                 
        self.assertEqual(T._decode_password(w["password_b64"]), "newsecret")

    def test_update_work_password_cleared_with_empty_string(self):
        pass







        c = T.empty_container()
        w = T.add_work(c, "A", ["D:/a"], "D:/b.zpaq", password="secret")
        self.assertIsNotNone(w["password_b64"])
        T.update_work(c, w["id"], password="")
        self.assertIsNone(w["password_b64"])

    def test_update_work_title_empty_keeps_previous(self):
        pass






        c = T.empty_container()
        w = T.add_work(c, "Original", ["D:/a"], "D:/b.zpaq")
        T.update_work(c, w["id"], title="")
        self.assertEqual(w["title"], "Original")

    def test_update_work_ignores_unknown_fields(self):
        c = T.empty_container()
        w = T.add_work(c, "A", ["D:/a"], "D:/b.zpaq")
        T.update_work(c, w["id"], nonexistent_field="xyz", title="B")
        self.assertNotIn("nonexistent_field", w)
        self.assertEqual(w["title"], "B")

    def test_update_missing_work_returns_none(self):
        c = T.empty_container()
        self.assertIsNone(T.update_work(c, "no-such-id", title="x"))

    def test_remove_work(self):
        c = T.empty_container()
        w1 = T.add_work(c, "A", ["D:/a"], "D:/b.zpaq")
        w2 = T.add_work(c, "B", ["D:/c"], "D:/d.zpaq")
        self.assertTrue(T.remove_work(c, w1["id"]))
        self.assertEqual(len(c["works"]), 1)
        self.assertEqual(c["works"][0]["id"], w2["id"])

    def test_remove_missing_work_returns_false(self):
        c = T.empty_container()
        self.assertFalse(T.remove_work(c, "no-such-id"))

    def test_find_work(self):
        c = T.empty_container()
        w = T.add_work(c, "A", ["D:/a"], "D:/b.zpaq")
        self.assertEqual(T.find_work(c, w["id"]), w)
        self.assertIsNone(T.find_work(c, "no-such-id"))


class TestJobs(_TmpDir):
    def _container_with_work(self):
        c = T.empty_container()
        w = T.add_work(c, "Docs", ["D:/Docs"], "D:/backup.zpaq")
        return c, w

    def test_add_job(self):
        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {
            "title": "Ежедневно",
            "level_key": "m2",
            "level": ["-m2"],
            "verify": "full",
            "task_log_mode": "short",
        })
        self.assertIsNotNone(j)
        self.assertTrue(j["id"])
        self.assertEqual(j["title"], "Ежедневно")
        self.assertEqual(j["level_key"], "m2")
        self.assertEqual(j["verify"], "full")
        self.assertEqual(j["task_log_mode"], "short")
                             
        self.assertIsNone(j["last_run"])
        self.assertIsNone(j["last_status"])
        self.assertEqual(j["run_count"], 0)

    def test_add_job_to_missing_work_returns_none(self):
        c = T.empty_container()
        self.assertIsNone(T.add_job(c, "no-such", {"title": "x"}))

    def test_add_job_ignores_work_fields(self):
        pass



        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {
            "title": "j",
            "sources": ["WRONG"],
            "dest": "WRONG.zpaq",
            "password": "WRONG",
        })
        self.assertNotIn("sources", j)
        self.assertNotIn("dest", j)
        self.assertNotIn("password", j)

    def test_add_job_ignores_runtime_only_keys(self):
        pass
        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {
            "title": "j",
            "params_rows": [("a", "b")],
        })
        self.assertNotIn("params_rows", j)

    def test_task_log_mode_defaults_to_short(self):
        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {"title": "j"})
        self.assertEqual(j["task_log_mode"], T.LOG_MODE_SHORT)

    def test_task_log_mode_unknown_becomes_short(self):
        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {"title": "j", "task_log_mode": "weird"})
        self.assertEqual(j["task_log_mode"], T.LOG_MODE_SHORT)

    def test_update_job(self):
        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {"title": "j", "level_key": "m2"})
        T.update_job(c, j["id"], level_key="m5", title="Renamed")
        self.assertEqual(j["level_key"], "m5")
        self.assertEqual(j["title"], "Renamed")

    def test_update_job_schedule(self):
        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {"title": "j"})
        schedule = {"enabled": True, "frequency": "daily", "time": "02:00",
                    "interval": 1}
        T.update_job(c, j["id"], schedule=schedule)
        self.assertEqual(j["schedule"], schedule)

    def test_update_job_title_empty_keeps_previous(self):
        pass
        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {"title": "Original"})
        T.update_job(c, j["id"], title="")
        self.assertEqual(j["title"], "Original")

    def test_update_missing_job_returns_none(self):
        c, _w = self._container_with_work()
        self.assertIsNone(T.update_job(c, "no-such", title="x"))

    def test_remove_job(self):
        c, w = self._container_with_work()
        j1 = T.add_job(c, w["id"], {"title": "a"})
        j2 = T.add_job(c, w["id"], {"title": "b"})
        self.assertTrue(T.remove_job(c, j1["id"]))
        self.assertEqual(len(w["jobs"]), 1)
        self.assertEqual(w["jobs"][0]["id"], j2["id"])

    def test_remove_missing_job_returns_false(self):
        c, _w = self._container_with_work()
        self.assertFalse(T.remove_job(c, "no-such"))

    def test_find_job(self):
        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {"title": "j"})
        found = T.find_job(c, j["id"])
        self.assertIsNotNone(found)
        fw, fj = found
        self.assertEqual(fw["id"], w["id"])
        self.assertEqual(fj["id"], j["id"])

    def test_find_missing_job_returns_none(self):
        c, _w = self._container_with_work()
        self.assertIsNone(T.find_job(c, "no-such"))


class TestJobAction(_TmpDir):
    pass







    def _container_with_work(self):
        c = T.empty_container()
        w = T.add_work(c, "Docs", ["D:/Docs"], "D:/backup.zpaq")
        return c, w

    def test_action_defaults_to_backup(self):
        pass
        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {"title": "j"})
        self.assertEqual(j["action"], T.ACTION_BACKUP)

    def test_action_test_kept(self):
        pass
        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {"title": "j", "action": "test"})
        self.assertEqual(j["action"], T.ACTION_TEST)

    def test_action_unknown_becomes_backup(self):
        pass






        c, w = self._container_with_work()
        j = T.add_job(c, w["id"], {"title": "j", "action": "weird"})
        self.assertEqual(j["action"], T.ACTION_BACKUP)

    def test_action_survives_save_and_load(self):
        pass
        c = T.empty_container()
        w = T.add_work(c, "Docs", ["D:/a"], "D:/b.zpaq")
        T.add_job(c, w["id"], {"title": "backup job"})
        T.add_job(c, w["id"], {"title": "check job", "action": "test"})
        T.save_container(self.path, c)

        loaded = T.load_container(self.path)
        jobs = loaded["works"][0]["jobs"]
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0]["action"], T.ACTION_BACKUP)
        self.assertEqual(jobs[1]["action"], T.ACTION_TEST)

    def test_legacy_job_without_action_reads_as_backup(self):
        pass
        self.write_raw(json.dumps({
            "format": T.CONTAINER_FORMAT,
            "version": 1,
            "works": [{
                "id": "w1",
                "title": "Old",
                "sources": ["D:/a"],
                "dest": "D:/b.zpaq",
                "jobs": [
                    {"id": "j1", "title": "legacy job"},
                ],
            }],
        }))
        c = T.load_container(self.path)
        job = c["works"][0]["jobs"][0]
        self.assertEqual(job["action"], T.ACTION_BACKUP)


class TestJobTestMode(_TmpDir):
    pass






    def test_test_mode_defaults_to_full(self):
        c = T.empty_container()
        w = T.add_work(c, "Docs", ["D:/a"], "D:/b.zpaq")
        j = T.add_job(c, w["id"], {"title": "j", "action": "test"})
        self.assertEqual(j["test_mode"], T.TEST_MODE_FULL)

    def test_test_mode_known_values_kept(self):
        for mode in ("full", "checksum", "verify", "paranoid"):
            with self.subTest(mode=mode):
                c = T.empty_container()
                w = T.add_work(c, "Docs", ["D:/a"], "D:/b.zpaq")
                j = T.add_job(c, w["id"], {
                    "title": "j",
                    "action": "test",
                    "test_mode": mode,
                })
                self.assertEqual(j["test_mode"], mode)

    def test_test_mode_unknown_becomes_full(self):
        c = T.empty_container()
        w = T.add_work(c, "Docs", ["D:/a"], "D:/b.zpaq")
        j = T.add_job(c, w["id"], {
            "title": "j",
            "action": "test",
            "test_mode": "weird",
        })
        self.assertEqual(j["test_mode"], T.TEST_MODE_FULL)

    def test_test_mode_update_normalized(self):
        c = T.empty_container()
        w = T.add_work(c, "Docs", ["D:/a"], "D:/b.zpaq")
        j = T.add_job(c, w["id"], {"title": "j", "action": "test"})
        T.update_job(c, j["id"], test_mode="paranoid")
        self.assertEqual(j["test_mode"], "paranoid")
        T.update_job(c, j["id"], test_mode="unknown")
        self.assertEqual(j["test_mode"], T.TEST_MODE_FULL)


class TestIteration(_TmpDir):
    def test_iter_jobs_empty(self):
        c = T.empty_container()
        self.assertEqual(T.iter_jobs(c), [])

    def test_iter_jobs_flat(self):
        c = T.empty_container()
        w1 = T.add_work(c, "W1", ["D:/a"], "D:/b.zpaq")
        w2 = T.add_work(c, "W2", ["D:/c"], "D:/d.zpaq")
        j1 = T.add_job(c, w1["id"], {"title": "j1"})
        j2 = T.add_job(c, w1["id"], {"title": "j2"})
        j3 = T.add_job(c, w2["id"], {"title": "j3"})

        flat = T.iter_jobs(c)
        self.assertEqual(len(flat), 3)
        ids = [(w["id"], j["id"]) for w, j in flat]
        self.assertIn((w1["id"], j1["id"]), ids)
        self.assertIn((w1["id"], j2["id"]), ids)
        self.assertIn((w2["id"], j3["id"]), ids)

    def test_iter_jobs_includes_test_jobs(self):
        pass
        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/b.zpaq")
        T.add_job(c, w["id"], {"title": "backup"})
        T.add_job(c, w["id"], {"title": "check", "action": "test"})
        self.assertEqual(len(T.iter_jobs(c)), 2)

    def test_iter_container_meta(self):
        pass




        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/b.zpaq")
        T.add_job(c, w["id"], {"title": "j1"})
        T.add_job(c, w["id"], {"title": "j2"})

        rows = T.iter_container_meta(c)
        self.assertEqual(len(rows), 3)                        
        self.assertEqual(rows[0]["kind"], "work")
        self.assertEqual(rows[0]["work"]["id"], w["id"])
        self.assertEqual(rows[1]["kind"], "job")
        self.assertEqual(rows[1]["work"]["id"], w["id"])
        self.assertEqual(rows[1]["job"]["title"], "j1")
        self.assertEqual(rows[2]["job"]["title"], "j2")

    def test_iter_container_meta_size_for_missing_archive(self):
        pass
        c = T.empty_container()
        T.add_work(c, "W", ["D:/a"], "D:/nonexistent.zpaq")
        rows = T.iter_container_meta(c)
        self.assertIsNone(rows[0]["size"])


class TestJobMeta(_TmpDir):
    def test_update_job_meta_sets_time_and_status(self):
        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/b.zpaq")
        j = T.add_job(c, w["id"], {"title": "j"})

        self.assertTrue(T.update_job_meta(c, j["id"], "ok"))
        self.assertIsNotNone(j["last_run"])
        self.assertEqual(j["last_status"], "ok")
        self.assertEqual(j["run_count"], 1)

    def test_update_job_meta_increments_count(self):
        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/b.zpaq")
        j = T.add_job(c, w["id"], {"title": "j"})
        T.update_job_meta(c, j["id"], "ok")
        T.update_job_meta(c, j["id"], "error")
        T.update_job_meta(c, j["id"], "ok")
        self.assertEqual(j["run_count"], 3)
        self.assertEqual(j["last_status"], "ok")

    def test_update_job_meta_for_test_job(self):
        pass
        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/b.zpaq")
        j = T.add_job(c, w["id"], {"title": "j", "action": "test"})
        T.update_job_meta(c, j["id"], "ok")
        self.assertEqual(j["last_status"], "ok")
        self.assertEqual(j["run_count"], 1)

    def test_update_missing_job_meta_returns_false(self):
        c = T.empty_container()
        self.assertFalse(T.update_job_meta(c, "no-such", "ok"))


class TestRunnableSettings(_TmpDir):
    def test_inherits_work_fields(self):
        c = T.empty_container()
        w = T.add_work(
            c, "W", ["D:/a", "D:/b"], "D:/out.zpaq",
            password="pw", only_masks=["*.txt"], not_masks=["*.bak"],
            comment="weekly",
        )
        j = T.add_job(c, w["id"], {"title": "j", "level_key": "m5"})

        s = T.job_to_runnable_settings(w, j)
        self.assertEqual(s["sources"], ["D:/a", "D:/b"])
        self.assertEqual(s["dest"], "D:/out.zpaq")
        self.assertEqual(s["password"], "pw")
        self.assertEqual(s["only_masks"], ["*.txt"])
        self.assertEqual(s["not_masks"], ["*.bak"])
        self.assertEqual(s["comment"], "weekly")

    def test_overrides_from_job(self):
        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/out.zpaq")
        j = T.add_job(c, w["id"], {
            "title": "j", "level_key": "m5", "verify": "full",
            "task_log_mode": "full",
        })

        s = T.job_to_runnable_settings(w, j)
        self.assertEqual(s["level_key"], "m5")
        self.assertEqual(s["verify"], "full")
        self.assertEqual(s["task_log_mode"], "full")

    def test_password_decoded(self):
        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/out.zpaq", password="secret")
        j = T.add_job(c, w["id"], {"title": "j"})
        s = T.job_to_runnable_settings(w, j)
        self.assertEqual(s["password"], "secret")

    def test_no_password_yields_none(self):
        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/out.zpaq")
        j = T.add_job(c, w["id"], {"title": "j"})
        s = T.job_to_runnable_settings(w, j)
        self.assertIsNone(s["password"])

    def test_schedule_passed_through(self):
        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/out.zpaq")
        schedule = {"enabled": True, "frequency": "daily",
                    "time": "02:00", "interval": 1}
        j = T.add_job(c, w["id"], {"title": "j", "schedule": schedule})
        s = T.job_to_runnable_settings(w, j)
        self.assertEqual(s["schedule"], schedule)

    def test_action_passed_through(self):
        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/out.zpaq")
        j = T.add_job(c, w["id"], {"title": "j", "action": "test"})
        s = T.job_to_runnable_settings(w, j)
        self.assertEqual(s["action"], "test")

    def test_test_mode_passed_through(self):
        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/out.zpaq")
        j = T.add_job(c, w["id"], {
            "title": "j", "action": "test", "test_mode": "paranoid",
        })
        s = T.job_to_runnable_settings(w, j)
        self.assertEqual(s["test_mode"], "paranoid")

    def test_work_title_in_settings(self):
        pass




        c = T.empty_container()
        w = T.add_work(c, "Documents", ["D:/a"], "D:/out.zpaq")
        j = T.add_job(c, w["id"], {"title": "j"})
        s = T.job_to_runnable_settings(w, j)
        self.assertEqual(s["work_title"], "Documents")

    def test_job_title_in_settings(self):
        pass



        c = T.empty_container()
        w = T.add_work(c, "W", ["D:/a"], "D:/out.zpaq")
        j = T.add_job(c, w["id"], {"title": "Daily check", "action": "test"})
        s = T.job_to_runnable_settings(w, j)
        self.assertEqual(s["title"], "Daily check")

    def test_work_title_and_job_title_are_independent(self):
        pass



        c = T.empty_container()
        w = T.add_work(c, "Work A", ["D:/a"], "D:/out.zpaq")
        j = T.add_job(c, w["id"], {"title": "Job B"})
        s = T.job_to_runnable_settings(w, j)
        self.assertEqual(s["work_title"], "Work A")
        self.assertEqual(s["title"], "Job B")


class TestSchedulerName(unittest.TestCase):
    def _job(self, job_id="12345678-1234-1234-1234-123456789abc",
             action="backup"):
        return {"id": job_id, "title": "j", "action": action}

    def test_name_has_prefix(self):
        work = {"id": "w1", "title": "Docs"}
        name = T.scheduler_task_name(work, self._job())
        self.assertTrue(name.startswith("Rizpaq_"))

    def test_backup_name_has_b_prefix(self):
        pass





        work = {"id": "w1", "title": "Docs"}
        name = T.scheduler_task_name(work, self._job(action="backup"))
        self.assertTrue(name.startswith("Rizpaq_b_"),
                        f"нет префикса b_: {name}")

    def test_test_name_has_t_prefix(self):
        work = {"id": "w1", "title": "Docs"}
        name = T.scheduler_task_name(work, self._job(action="test"))
        self.assertTrue(name.startswith("Rizpaq_t_"),
                        f"нет префикса t_: {name}")

    def test_legacy_job_without_action_gets_b_prefix(self):
        pass



        work = {"id": "w1", "title": "Docs"}
        job = {"id": "12345678-1234-1234-1234-123456789abc", "title": "j"}
        name = T.scheduler_task_name(work, job)
        self.assertTrue(name.startswith("Rizpaq_b_"))

    def test_name_includes_work_slug(self):
        pass



        work = {"id": "w1", "title": "Мои документы"}
        name = T.scheduler_task_name(work, self._job())
                                                       
        self.assertNotIn("Мои", name)
        self.assertNotIn(" ", name)
        self.assertIn("moi_dokumenty", name.lower())

    def test_name_stable_across_calls(self):
        work = {"id": "w1", "title": "Docs"}
        job = self._job()
        self.assertEqual(
            T.scheduler_task_name(work, job),
            T.scheduler_task_name(work, job),
        )

    def test_name_differs_for_different_jobs(self):
        work = {"id": "w1", "title": "Docs"}
        j1 = {"id": "aaaaaaaa-1111-1111-1111-111111111111", "title": "a"}
        j2 = {"id": "bbbbbbbb-2222-2222-2222-222222222222", "title": "b"}
        self.assertNotEqual(
            T.scheduler_task_name(work, j1),
            T.scheduler_task_name(work, j2),
        )

    def test_name_differs_for_different_actions_same_id(self):
        pass





        work = {"id": "w1", "title": "Docs"}
        job_id = "aaaaaaaa-1111-1111-1111-111111111111"
        name_b = T.scheduler_task_name(
            work, {"id": job_id, "title": "j", "action": "backup"}
        )
        name_t = T.scheduler_task_name(
            work, {"id": job_id, "title": "j", "action": "test"}
        )
        self.assertNotEqual(name_b, name_t)

    def test_name_differs_for_different_works(self):
        pass
        w1 = {"id": "w1", "title": "Docs"}
        w2 = {"id": "w2", "title": "Docs"}
        job = self._job()
        self.assertNotEqual(
            T.scheduler_task_name(w1, job),
            T.scheduler_task_name(w2, job),
        )

    def test_name_differs_for_different_work_titles(self):
        pass
        job = self._job()
        w1 = {"id": "same", "title": "Docs"}
        w2 = {"id": "same", "title": "Backup"}
        self.assertNotEqual(
            T.scheduler_task_name(w1, job),
            T.scheduler_task_name(w2, job),
        )

    def test_empty_title_gives_work_slug(self):
        pass
        work = {"id": "w1", "title": ""}
        name = T.scheduler_task_name(work, self._job())
        self.assertIn("work", name)


class TestSaveIsAtomic(_TmpDir):
    def test_failed_write_keeps_old_file(self):
        pass
        c = T.empty_container()
        T.add_work(c, "W1", ["D:/a"], "D:/b.zpaq")
        T.save_container(self.path, c)
        before = self.read_raw()

                                               
        import os

        real = os.replace

        def boom(src, dst, *a, **k):
            raise OSError("simulated failure")

        os.replace = boom
        try:
            T.add_work(c, "W2", ["D:/c"], "D:/d.zpaq")
            with self.assertRaises(OSError):
                T.save_container(self.path, c)
        finally:
            os.replace = real

        self.assertEqual(self.read_raw(), before)

    def test_no_leftover_temp_files(self):
        pass
        c = T.empty_container()
        T.add_work(c, "W", ["D:/a"], "D:/b.zpaq")
        T.save_container(self.path, c)

        extra = [p for p in self.dir.iterdir() if p.is_file() and p != self.path]
        self.assertEqual(extra, [], f"лишние файлы: {[p.name for p in extra]}")


class TestWorkSlug(unittest.TestCase):
    def test_latin_title_lowercased(self):
        pass




        self.assertEqual(T.work_slug("Docs"), "docs")

    def test_spaces_become_underscores(self):
        pass
        slug = T.work_slug("my documents")
        self.assertEqual(slug, "my_documents")

    def test_cyrillic_transliterates(self):
        pass
        slug = T.work_slug("Мои документы")
        self.assertEqual(slug, "moi_dokumenty")

    def test_empty_title_returns_fallback(self):
        self.assertEqual(T.work_slug(""), "work")

    def test_only_symbols_returns_fallback(self):
        self.assertEqual(T.work_slug("---...---"), "work")

    def test_length_limited(self):
        long_title = "a" * 100
        self.assertLessEqual(len(T.work_slug(long_title)), 20)

    def test_multiple_spaces_collapsed(self):
        pass
        slug = T.work_slug("a   b")
        self.assertEqual(slug, "a_b")


class TestConstants(unittest.TestCase):
    pass

    def test_actions_constant(self):
        self.assertEqual(T.ACTION_BACKUP, "backup")
        self.assertEqual(T.ACTION_TEST, "test")
        self.assertIn(T.ACTION_BACKUP, T.ACTIONS)
        self.assertIn(T.ACTION_TEST, T.ACTIONS)

    def test_test_modes_constant(self):
        for mode in ("full", "checksum", "verify", "paranoid"):
            with self.subTest(mode=mode):
                self.assertIn(mode, T.TEST_MODES)

    def test_test_mode_constants(self):
        self.assertEqual(T.TEST_MODE_FULL, "full")
        self.assertEqual(T.TEST_MODE_CHECKSUM, "checksum")
        self.assertEqual(T.TEST_MODE_VERIFY, "verify")
        self.assertEqual(T.TEST_MODE_PARANOID, "paranoid")


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
