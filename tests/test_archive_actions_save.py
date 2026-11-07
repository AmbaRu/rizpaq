
























































from __future__ import annotations

import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QMessageBox              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from core.tasks import (              
    ACTION_TEST,
    JOB_FIELDS,
    add_job,
    add_work,
    container_path,
    empty_container,
    load_container,
    save_container,
    scheduler_task_name,
)
from ui.archive_actions import ArchiveActionsMixin              


class _FakeBackupPage:
    pass

    def __init__(self, tasks_dir):
        self._dir = tasks_dir

    def tasks_dir(self):
        return str(self._dir) if self._dir else None


class _Host(ArchiveActionsMixin):
    pass











    zpaq_available = True
    zpaq_bin = "zpaqfranz"

    def __init__(self, tasks_dir):
        self.backup_page = _FakeBackupPage(tasks_dir)
        self._cfg = type("Cfg", (), {"tasks_dir": str(tasks_dir) if tasks_dir else None})()
        self._status = []
        self._workers = []

    def statusBar(self):
        return self

    def showMessage(self, text):
        self._status.append(text)

    def _cleanup_worker(self, worker):
        pass
        if worker in self._workers:
            self._workers.remove(worker)

    def wait_for_workers(self, timeout_ms: int = 5000) -> None:
        pass












                               
        for w in list(self._workers):
            try:
                w.wait(timeout_ms)
            except Exception:
                pass

                                                             
        deadline = time.monotonic() + timeout_ms / 1000.0
        while self._workers and time.monotonic() < deadline:
            QApplication.processEvents()
            time.sleep(0.005)
                                                                         
                                             
        QApplication.processEvents()


class _TmpMixin(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_aa_save_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def container_path(self):
        return container_path(self.dir)

    def write_container(self, works_spec=None):
        c = empty_container()
        for spec in works_spec or []:
            w = add_work(
                c,
                title=spec.get("title", "W"),
                sources=spec.get("sources") or ["D:/src"],
                dest=spec.get("dest") or "D:/out.zpaq",
                password=spec.get("password"),
                only_masks=spec.get("only_masks"),
                not_masks=spec.get("not_masks"),
                comment=spec.get("comment") or "",
            )
            for j_spec in spec.get("jobs") or []:
                add_job(c, w["id"], j_spec)
        save_container(self.container_path(), c)
        return c


                                                                          

class TestSaveNewJobCreatesWork(_TmpMixin):
    pass

    def test_new_work_and_job_saved(self):
        host = _Host(self.dir)
        settings = {
            "sources": ["D:/docs"],
            "dest": "D:/backup.zpaq",
            "comment": "",
            "only_masks": [],
            "not_masks": [],
            "level_key": "m2",
            "level": ["-m2"],
            "task_log_mode": "short",
        }
        with mock.patch("core.scheduler.create_scheduled_task"), \
             mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            ok = host._save_new_job(settings)
        self.assertTrue(ok)

        c = load_container(self.container_path())
        self.assertEqual(len(c["works"]), 1)
        work = c["works"][0]
        self.assertEqual(work["sources"], ["D:/docs"])
        self.assertEqual(work["dest"], "D:/backup.zpaq")
        self.assertEqual(len(work["jobs"]), 1)
        self.assertEqual(work["jobs"][0]["level_key"], "m2")
        self.assertEqual(work["jobs"][0]["task_log_mode"], "short")
                                       
        self.assertEqual(work["jobs"][0]["action"], "backup")

    def test_work_title_from_dest_stem(self):
        pass





        host = _Host(self.dir)
        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            host._save_new_job({
                "sources": ["D:/a"],
                "dest": "D:/my backup.zpaq",
                "task_log_mode": "short",
            })
        c = load_container(self.container_path())
        self.assertEqual(c["works"][0]["title"], "my backup")

    def test_work_title_from_settings_overrides_dest(self):
        pass



        host = _Host(self.dir)
        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            host._save_new_job({
                "work_title": "Документы",
                "sources": ["D:/a"],
                "dest": "D:/something-else.zpaq",
                "task_log_mode": "short",
            })
        c = load_container(self.container_path())
        self.assertEqual(c["works"][0]["title"], "Документы")

    def test_job_title_from_settings(self):
        pass
        host = _Host(self.dir)
        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            host._save_new_job({
                "title": "Ежедневный бэкап",
                "sources": ["D:/a"],
                "dest": "D:/b.zpaq",
                "task_log_mode": "short",
            })
        c = load_container(self.container_path())
        self.assertEqual(c["works"][0]["jobs"][0]["title"], "Ежедневный бэкап")

    def test_empty_job_title_becomes_default(self):
        pass
        host = _Host(self.dir)
        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            host._save_new_job({
                "sources": ["D:/a"],
                "dest": "D:/b.zpaq",
                "task_log_mode": "short",
            })
        c = load_container(self.container_path())
        self.assertEqual(c["works"][0]["jobs"][0]["title"], "Задание")

    def test_password_saved_encoded(self):
        host = _Host(self.dir)
        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            host._save_new_job({
                "sources": ["D:/a"],
                "dest": "D:/b.zpaq",
                "password": "topsecret",
                "task_log_mode": "short",
            })
        c = load_container(self.container_path())
        self.assertIsNotNone(c["works"][0]["password_b64"])

    def test_no_tasks_dir_reports_failure(self):
        host = _Host(None)

        with mock.patch.object(QMessageBox, "warning") as warn:
            ok = host._save_new_job({"sources": ["D:/a"], "dest": "D:/b.zpaq"})
        self.assertFalse(ok)
        warn.assert_called_once()

    def test_save_test_job_as_new_work(self):
        pass





        host = _Host(self.dir)
        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            host._save_new_job({
                "action": ACTION_TEST,
                "test_mode": "paranoid",
                "title": "Проверка",
                "sources": ["D:/a"],
                "dest": "D:/b.zpaq",
                "task_log_mode": "short",
            })
        c = load_container(self.container_path())
        job = c["works"][0]["jobs"][0]
        self.assertEqual(job["action"], ACTION_TEST)
        self.assertEqual(job["test_mode"], "paranoid")


class TestEveryJobFieldReachesContainer(_TmpMixin):
    pass























    def _settings_with_par2(self):
        return {
            "sources": ["D:/docs"],
            "dest": "D:/backup.zpaq",
            "work_title": "Работа 1",
            "title": "Задание 1",
            "action": "backup",
            "test_mode": None,
            "level_key": "m2",
            "level": ["-m2"],
            "schedule": {"kind": "daily", "time": "03:00"},
            "task_log_mode": "short",
            "par2_enabled": True,
            "par2_options": {"redundancy": 5, "block_size": None},
        }

    def test_par2_reaches_container(self):
        pass
        host = _Host(self.dir)
        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            host._save_new_job(self._settings_with_par2())

        job = load_container(self.container_path())["works"][0]["jobs"][0]
        self.assertIs(job.get("par2_enabled"), True)
        self.assertEqual(job.get("par2_options"),
                         {"redundancy": 5, "block_size": None})

    def test_par2_edited_job_keeps_flag(self):
        pass
        host = _Host(self.dir)
                                                               
                                                                   
                       
        c = self.write_container([{
            "title": "Работа 1",
            "sources": ["D:/docs"],
            "dest": "D:/backup.zpaq",
            "jobs": [{
                "title": "Задание 1",
                "action": "backup",
                "par2_enabled": False,
                "par2_options": {},
            }],
        }])
        work_id = c["works"][0]["id"]
        job_id = c["works"][0]["jobs"][0]["id"]
                                                                  
                                                           
        self.assertIs(
            load_container(self.container_path())["works"][0]["jobs"][0]
            ["par2_enabled"],
            False,
        )

        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            ok = host._save_edited_job(
                self._settings_with_par2(), work_id, job_id
            )
        self.assertTrue(ok)

        job = load_container(self.container_path())["works"][0]["jobs"][0]
        self.assertIs(job.get("par2_enabled"), True)
        self.assertEqual(job.get("par2_options"),
                         {"redundancy": 5, "block_size": None})

    def test_schedule_and_job_title_survive(self):
        pass







        host = _Host(self.dir)
        with mock.patch("core.scheduler.create_scheduled_task"), \
             mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            host._save_new_job(self._settings_with_par2())

        c = load_container(self.container_path())
        job = c["works"][0]["jobs"][0]
        self.assertEqual(job.get("title"), "Задание 1")
        self.assertEqual(job.get("schedule"),
                         {"kind": "daily", "time": "03:00"})
        self.assertEqual(job.get("task_log_mode"), "short")

    def test_every_job_field_is_copied(self):
        pass







        host = _Host(self.dir)
        sentinel = {
            "level": ["-m2"],
            "level_key": "m2",
            "hash": True,
            "hash_key": "sha256",
            "vss": False,
            "checkspace": True,
            "chunk": None,
            "copy": False,
            "sfx": False,
            "par2_options": {"redundancy": 5},
        }
        settings = {
            "sources": ["D:/a"],
            "dest": "D:/a.zpaq",
            "task_log_mode": "short",
        }
        for key in JOB_FIELDS:
            settings[key] = sentinel.get(key, None)

        _work, job_fields = host._split_settings_work_job(settings)

        missing = [k for k in JOB_FIELDS
                   if k in settings and k not in job_fields]
        self.assertEqual(
            missing, [],
            f"поля задания потеряны при разрезании настроек: {missing}",
        )
                                                           
        self.assertEqual(job_fields["level"], ["-m2"])
        self.assertEqual(job_fields["par2_options"], {"redundancy": 5})
        self.assertEqual(job_fields["chunk"], None)


class TestSaveNewJobToExistingWork(_TmpMixin):
    pass

    def test_job_added_not_new_work_created(self):
        c = self.write_container([{"title": "Docs", "jobs": []}])
        work_id = c["works"][0]["id"]
        host = _Host(self.dir)

        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            ok = host._save_new_job(
                {
                    "sources": ["D:/docs"],
                    "dest": "D:/out.zpaq",
                    "task_log_mode": "short",
                },
                work_id=work_id,
            )
        self.assertTrue(ok)

        c2 = load_container(self.container_path())
        self.assertEqual(len(c2["works"]), 1)
        self.assertEqual(c2["works"][0]["id"], work_id)
        self.assertEqual(len(c2["works"][0]["jobs"]), 1)

    def test_job_added_to_work_with_existing_job(self):
        c = self.write_container([{
            "title": "Docs",
            "jobs": [{"title": "Daily", "level_key": "m2"}],
        }])
        work_id = c["works"][0]["id"]
        host = _Host(self.dir)

        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            ok = host._save_new_job(
                {
                    "sources": ["D:/docs"],
                    "dest": "D:/out.zpaq",
                    "level_key": "m5",
                    "task_log_mode": "short",
                },
                work_id=work_id,
            )
        self.assertTrue(ok)

        c2 = load_container(self.container_path())
        self.assertEqual(len(c2["works"]), 1)
        self.assertEqual(len(c2["works"][0]["jobs"]), 2)

    def test_add_test_job_to_existing_work(self):
        pass





        c = self.write_container([{"title": "Docs", "jobs": []}])
        work_id = c["works"][0]["id"]
        host = _Host(self.dir)

        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            ok = host._save_new_job(
                {
                    "action": ACTION_TEST,
                    "test_mode": "checksum",
                    "title": "Месячная проверка",
                    "sources": ["D:/docs"],
                    "dest": "D:/out.zpaq",
                    "task_log_mode": "short",
                },
                work_id=work_id,
            )
        self.assertTrue(ok)

        c2 = load_container(self.container_path())
        self.assertEqual(len(c2["works"]), 1)
        self.assertEqual(len(c2["works"][0]["jobs"]), 1)
        job = c2["works"][0]["jobs"][0]
        self.assertEqual(job["action"], ACTION_TEST)
        self.assertEqual(job["test_mode"], "checksum")
        self.assertEqual(job["title"], "Месячная проверка")

    def test_renaming_work_through_add_job(self):
        pass




        c = self.write_container([{"title": "Old name", "jobs": []}])
        work_id = c["works"][0]["id"]
        host = _Host(self.dir)

        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch.object(QMessageBox, "information"):
            ok = host._save_new_job(
                {
                    "work_title": "New name",
                    "sources": ["D:/docs"],
                    "dest": "D:/out.zpaq",
                    "task_log_mode": "short",
                },
                work_id=work_id,
            )
        self.assertTrue(ok)

        c2 = load_container(self.container_path())
        self.assertEqual(c2["works"][0]["title"], "New name")

    def test_missing_work_id_reports_failure(self):
        self.write_container([{"title": "Docs", "jobs": []}])
        host = _Host(self.dir)

        with mock.patch.object(QMessageBox, "warning") as warn:
            ok = host._save_new_job(
                {"sources": ["D:/a"], "dest": "D:/b.zpaq"},
                work_id="no-such-id",
            )
        self.assertFalse(ok)
        warn.assert_called_once()


                                                                             

class TestSaveEditedJob(_TmpMixin):
    pass

    def _setup(self):
        c = self.write_container([{
            "title": "Docs",
            "jobs": [{
                "title": "Daily",
                "level_key": "m2",
                "schedule": {"enabled": True, "frequency": "daily",
                             "time": "02:00", "interval": 1},
            }],
        }])
        work = c["works"][0]
        job = work["jobs"][0]
        return work["id"], job["id"]

    def test_job_fields_updated(self):
        work_id, job_id = self._setup()
        host = _Host(self.dir)

        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch("core.scheduler.create_scheduled_task"):
            ok = host._save_edited_job(
                {
                    "sources": ["D:/docs"],
                    "dest": "D:/out.zpaq",
                    "level_key": "m5",
                    "level": ["-m5"],
                    "task_log_mode": "full",
                },
                work_id, job_id,
            )
        self.assertTrue(ok)

        c = load_container(self.container_path())
        job = c["works"][0]["jobs"][0]
        self.assertEqual(job["level_key"], "m5")
        self.assertEqual(job["task_log_mode"], "full")

    def test_work_fields_updated(self):
        work_id, job_id = self._setup()
        host = _Host(self.dir)

        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch("core.scheduler.create_scheduled_task"):
            ok = host._save_edited_job(
                {
                    "sources": ["D:/new-src"],
                    "dest": "D:/new-dest.zpaq",
                    "comment": "obnovleno",
                    "level_key": "m2",
                    "level": ["-m2"],
                },
                work_id, job_id,
            )
        self.assertTrue(ok)

        c = load_container(self.container_path())
        work = c["works"][0]
        self.assertEqual(work["sources"], ["D:/new-src"])
        self.assertEqual(work["dest"], "D:/new-dest.zpaq")
        self.assertEqual(work["comment"], "obnovleno")

    def test_job_title_updated(self):
        pass
        work_id, job_id = self._setup()
        host = _Host(self.dir)

        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch("core.scheduler.create_scheduled_task"):
            ok = host._save_edited_job(
                {
                    "title": "Renamed job",
                    "sources": ["D:/docs"],
                    "dest": "D:/out.zpaq",
                    "level_key": "m2",
                    "level": ["-m2"],
                },
                work_id, job_id,
            )
        self.assertTrue(ok)

        c = load_container(self.container_path())
        self.assertEqual(c["works"][0]["jobs"][0]["title"], "Renamed job")

    def test_work_title_updated(self):
        pass




        work_id, job_id = self._setup()
        host = _Host(self.dir)

        with mock.patch.object(QMessageBox, "warning"), \
             mock.patch("core.scheduler.create_scheduled_task"):
            ok = host._save_edited_job(
                {
                    "work_title": "Renamed work",
                    "sources": ["D:/docs"],
                    "dest": "D:/out.zpaq",
                    "level_key": "m2",
                    "level": ["-m2"],
                },
                work_id, job_id,
            )
        self.assertTrue(ok)

        c = load_container(self.container_path())
        self.assertEqual(c["works"][0]["title"], "Renamed work")

    def test_missing_work_reports_failure(self):
        _work_id, job_id = self._setup()
        host = _Host(self.dir)

        with mock.patch.object(QMessageBox, "warning") as warn:
            ok = host._save_edited_job(
                {"sources": ["D:/a"], "dest": "D:/b.zpaq"},
                "no-such-work", job_id,
            )
        self.assertFalse(ok)
        warn.assert_called_once()

    def test_missing_job_reports_failure(self):
        work_id, _job_id = self._setup()
        host = _Host(self.dir)

        with mock.patch.object(QMessageBox, "warning") as warn:
            ok = host._save_edited_job(
                {"sources": ["D:/a"], "dest": "D:/b.zpaq"},
                work_id, "no-such-job",
            )
        self.assertFalse(ok)
        warn.assert_called_once()

    def test_no_schedule_does_not_touch_scheduler(self):
        pass







        work_id, job_id = self._setup()
        host = _Host(self.dir)

        with mock.patch("core.scheduler.create_scheduled_task") as c, \
             mock.patch("core.scheduler.remove_scheduled_task_by_name") as rem, \
             mock.patch.object(QMessageBox, "warning"):
            host._save_edited_job(
                {
                    "sources": ["D:/a"],
                    "dest": "D:/b.zpaq",
                    "level_key": "m2",
                    "level": ["-m2"],
                },
                work_id, job_id,
            )
            host.wait_for_workers()
        c.assert_not_called()
        rem.assert_not_called()

    def test_renaming_work_removes_old_scheduler_task(self):
        pass




        work_id, job_id = self._setup()
        host = _Host(self.dir)

                                                                          
        c_before = load_container(self.container_path())
        work_before = c_before["works"][0]
        job_before = work_before["jobs"][0]
        old_task_name = scheduler_task_name(work_before, job_before)

        with mock.patch("core.scheduler.create_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task_by_name") as rem, \
             mock.patch.object(QMessageBox, "warning"):
            host._save_edited_job(
                {
                    "work_title": "Renamed",
                    "sources": ["D:/docs"],
                    "dest": "D:/out.zpaq",
                    "level_key": "m2",
                    "level": ["-m2"],
                },
                work_id, job_id,
            )

                                                                   
                                    
        calls = [str(a) for a in rem.call_args_list]
        self.assertTrue(
            any(old_task_name in c for c in calls),
            f"старое имя {old_task_name!r} не снято. Вызовы: {calls}",
        )

    def test_renaming_test_job_does_not_change_scheduler_name(self):
        pass



        c = self.write_container([{
            "title": "Docs",
            "jobs": [{"title": "Old check", "action": "test"}],
        }])
        work_id = c["works"][0]["id"]
        job_id = c["works"][0]["jobs"][0]["id"]
        host = _Host(self.dir)

        with mock.patch("core.scheduler.create_scheduled_task"), \
             mock.patch("core.scheduler.remove_scheduled_task_by_name") as rem, \
             mock.patch.object(QMessageBox, "warning"):
            host._save_edited_job(
                {
                    "title": "New check",
                    "sources": ["D:/docs"],
                    "dest": "D:/out.zpaq",
                    "action": ACTION_TEST,
                    "test_mode": "full",
                },
                work_id, job_id,
            )
                                                       
        rem.assert_not_called()


class TestTaskNameHelper(_TmpMixin):
    pass







    def test_name_changes_with_work_title(self):
        c = self.write_container([{
            "title": "Old Name",
            "jobs": [{"title": "Daily"}],
        }])
        work = c["works"][0]
        job = work["jobs"][0]
        host = _Host(self.dir)

        name_before = host._task_name_for(c, work["id"], job["id"])
        self.assertTrue(name_before)

        work["title"] = "New Name"
        name_after = host._task_name_for(c, work["id"], job["id"])
        self.assertTrue(name_after)
        self.assertNotEqual(name_before, name_after)

    def test_name_for_test_job_has_t_prefix(self):
        pass



        c = self.write_container([{
            "title": "Docs",
            "jobs": [{"title": "Check", "action": "test"}],
        }])
        work = c["works"][0]
        job = work["jobs"][0]
        host = _Host(self.dir)
        name = host._task_name_for(c, work["id"], job["id"])
        self.assertIn("_t_", name)

    def test_name_for_backup_job_has_b_prefix(self):
        c = self.write_container([{
            "title": "Docs",
            "jobs": [{"title": "Backup"}],
        }])
        work = c["works"][0]
        job = work["jobs"][0]
        host = _Host(self.dir)
        name = host._task_name_for(c, work["id"], job["id"])
        self.assertIn("_b_", name)

    def test_missing_work_or_job_gives_empty(self):
        host = _Host(self.dir)
        c = empty_container()
        self.assertEqual(host._task_name_for(c, "no", "no"), "")

    def test_name_matches_scheduler_task_name(self):
        c = self.write_container([{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
        work = c["works"][0]
        job = work["jobs"][0]
        host = _Host(self.dir)
        self.assertEqual(
            host._task_name_for(c, work["id"], job["id"]),
            scheduler_task_name(work, job),
        )


                                                                            

class TestApplySchedule(_TmpMixin):
    pass









    def _work_job(self):
        c = self.write_container([{
            "title": "Docs",
            "jobs": [{"title": "Daily"}],
        }])
        return c["works"][0], c["works"][0]["jobs"][0]

    def test_none_schedule_does_nothing(self):
        host = _Host(self.dir)
        work, job = self._work_job()
        with mock.patch("core.scheduler.create_scheduled_task") as c:
            host._apply_schedule(work, job, None)
            host.wait_for_workers()
        c.assert_not_called()
        self.assertEqual(host._workers, [],
                         "при schedule=None воркер не должен создаваться")

    def test_enabled_schedule_calls_create(self):
        host = _Host(self.dir)
        work, job = self._work_job()
        sched = {"enabled": True, "frequency": "daily",
                 "time": "02:00", "interval": 1}
        with mock.patch("core.scheduler.create_scheduled_task",
                        return_value=True) as c, \
             mock.patch.object(QMessageBox, "warning"):
            host._apply_schedule(work, job, sched)
            host.wait_for_workers()
        c.assert_called_once()
        args, _ = c.call_args
        self.assertEqual(args[1], work)
        self.assertEqual(args[2], job)
        self.assertEqual(args[3], sched)

    def test_disabled_schedule_still_calls_create_for_delegation(self):
        pass





        host = _Host(self.dir)
        work, job = self._work_job()
        sched = {"enabled": False}
        with mock.patch("core.scheduler.create_scheduled_task",
                        return_value=True) as c:
            host._apply_schedule(work, job, sched)
            host.wait_for_workers()
        c.assert_called_once_with(
            container_path(self.dir), work, job, sched
        )

    def test_failed_create_shows_warning_only_when_enabled(self):
        host = _Host(self.dir)
        work, job = self._work_job()
        with mock.patch("core.scheduler.create_scheduled_task",
                        return_value=False), \
             mock.patch.object(QMessageBox, "warning") as warn:
            host._apply_schedule(work, job, {"enabled": True})
            host.wait_for_workers()
        warn.assert_called_once()

    def test_failed_disabled_does_not_warn(self):
        pass
        host = _Host(self.dir)
        work, job = self._work_job()
        with mock.patch("core.scheduler.create_scheduled_task",
                        return_value=False), \
             mock.patch.object(QMessageBox, "warning") as warn:
            host._apply_schedule(work, job, {"enabled": False})
            host.wait_for_workers()
        warn.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
