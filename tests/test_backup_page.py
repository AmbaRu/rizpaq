



















































from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt              
from PySide6.QtWidgets import QApplication, QPushButton              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


                                                               
                                                                
                                                            
                                                                 
                         
from ui.i18n import set_language              

set_language("ru", notify=False)

from core.tasks import (              
    ACTION_TEST,
    add_job,
    add_work,
    container_path,
    empty_container,
    save_container,
)
from ui.backup_page import (              
    BackupPage,
    _COL_LAST_RUN,
    _COL_NAME,
    _COL_NEXT_RUN,
    _COL_SCHEDULE,
    _COL_SIZE,
    _COL_STATUS,
    _PAYLOAD_ROLE,
)


class _Host:
    pass
















    def __init__(self, tasks_dir=None):
        cfg = type("Cfg", (), {"tasks_dir": tasks_dir})()
        self._cfg = cfg
        self._status = []
                                                                     
        self.calls = []
                                                                
                                                                    
                                                              
                                                                 
        self._workers = []

    def statusBar(self):
        return self

    def showMessage(self, text):
        self._status.append(text)

    def _cleanup_worker(self, worker):
        pass








        if worker in self._workers:
            self._workers.remove(worker)

                                                           
    def _enter_archive(self, path):
        self.calls.append(("_enter_archive", path))

    def _run_job(self, work_id, job_id):
        self.calls.append(("_run_job", work_id, job_id))

    def _edit_job(self, work_id, job_id):
        self.calls.append(("_edit_job", work_id, job_id))

    def _edit_work(self, work_id):
        self.calls.append(("_edit_work", work_id))

    def _on_add_job_to_work(self, work_id):
        self.calls.append(("_on_add_job_to_work", work_id))

    def _on_add_check_to_work(self, work_id):
        self.calls.append(("_on_add_check_to_work", work_id))

    def _on_test_archive(self, path=None, mode="full", from_create=False,
                         job_context=None):
        self.calls.append(("_on_test_archive", path, mode, job_context))


class _HostWithoutEditWork(_Host):
    pass











    _edit_work = None


class _HostWithoutCheckJob(_Host):
    pass

    _on_add_check_to_work = None


class _TmpMixin(unittest.TestCase):
    def setUp(self):
        import shutil

        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_bp_test_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def write_container(self, works=None):
        pass





        c = empty_container()
        for w_spec in (works or []):
            w = add_work(
                c,
                title=w_spec.get("work_title", "W"),
                sources=w_spec.get("sources") or ["D:/src"],
                dest=w_spec.get("dest") or "D:/out.zpaq",
                password=w_spec.get("password"),
                only_masks=w_spec.get("only_masks"),
                not_masks=w_spec.get("not_masks"),
                comment=w_spec.get("comment") or "",
            )
            for j_spec in (w_spec.get("jobs") or []):
                add_job(c, w["id"], j_spec)
        save_container(container_path(self.dir), c)
        return c

    def make_page(self, works=None, patch_schedule=True):
        pass





        container = self.write_container(works)
        host = _Host(tasks_dir=str(self.dir))
        if patch_schedule:
            with mock.patch.object(BackupPage, "_load_schedule"):
                page = BackupPage(host)
        else:
            page = BackupPage(host)
        self.addCleanup(self._dispose_page, page)
        return page, container

    def _dispose_page(self, page):
        pass




































        try:
            page._watch_timer.stop()
        except Exception:
            pass
        try:
            page._watcher.setPaths([])
        except Exception:
            pass

                                                                 
        worker = getattr(page, "_schedule_worker", None)
        if worker is not None:
            try:
                worker.cancel_request()
            except Exception:
                pass
            try:
                worker.wait(5000)
            except Exception:
                pass

        page.close()
        page.deleteLater()

    def make_page_with_worker_mock(self, works=None):
        pass




        container = self.write_container(works)
        host = _Host(tasks_dir=str(self.dir))
        with mock.patch("ui.backup_page._ScheduleWorker") as worker_cls:
            page = BackupPage(host)
        self.addCleanup(self._dispose_page, page)
        return page, container, worker_cls


def _top_level_work_items(page):
    tree = page._tree
    return [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]


def _payload(item):
    return item.data(_COL_NAME, _PAYLOAD_ROLE)


def _cell_widget(item, page):
    pass
    return page._tree.itemWidget(item, _COL_NEXT_RUN)


def _force_visible(page):
    pass






    page.isVisible = lambda: True
    page._stack.setCurrentWidget(page._tree)


def _select_item(page, item):
    pass







    parent = item.parent()
    while parent is not None:
        parent.setExpanded(True)
        parent = parent.parent()
    _APP.processEvents()
    page._tree.setCurrentItem(item)
    _APP.processEvents()


                                                                    


class TestRefreshAndEmptyState(_TmpMixin):
    def test_no_tasks_dir_shows_empty_page(self):
        host = _Host(tasks_dir=None)
        with mock.patch.object(BackupPage, "_load_schedule"):
            page = BackupPage(host)
        self.assertIs(page._stack.currentWidget(), page._empty_page)
        self.assertFalse(page._choose_btn.isHidden(),
                         "кнопка выбора папки должна быть видна")

    def test_empty_container_shows_empty_page(self):
        page, _ = self.make_page(works=[])
        self.assertIs(page._stack.currentWidget(), page._empty_page)
        self.assertTrue(page._choose_btn.isHidden(),
                        "папка выбрана — кнопка выбора прячется")

    def test_container_with_works_shows_tree(self):
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        self.assertIs(page._stack.currentWidget(), page._tree)
        self.assertEqual(page._tree.topLevelItemCount(), 1)


                                                                   


class TestTreeStructure(_TmpMixin):
    def test_six_columns(self):
        pass
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "j"}]},
        ])
        self.assertEqual(page._tree.columnCount(), 6)

    def test_work_and_jobs_present(self):
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [
                {"title": "Daily"},
                {"title": "Weekly"},
            ]},
        ])
        work_items = _top_level_work_items(page)
        self.assertEqual(len(work_items), 1)
        work_item = work_items[0]
        self.assertEqual(work_item.childCount(), 2)
        self.assertTrue(work_item.child(0).text(_COL_NAME).endswith("Daily"))
        self.assertTrue(work_item.child(1).text(_COL_NAME).endswith("Weekly"))

    def test_work_payload(self):
        page, c = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        work_item = _top_level_work_items(page)[0]
        payload = _payload(work_item)
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["kind"], "work")
        self.assertEqual(payload["work_id"], c["works"][0]["id"])

    def test_job_payload(self):
        page, c = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        work_item = _top_level_work_items(page)[0]
        job_item = work_item.child(0)
        payload = _payload(job_item)
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["kind"], "job")
        self.assertEqual(payload["job_id"], c["works"][0]["jobs"][0]["id"])
        self.assertEqual(payload["work_id"], c["works"][0]["id"])

    def test_next_run_starts_as_ellipsis(self):
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        self.assertEqual(job_item.text(_COL_NEXT_RUN), "…",
                         "до ответа воркера в колонке стоит «…»")

    def test_work_row_has_no_next_run(self):
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        work_item = _top_level_work_items(page)[0]
        self.assertEqual(work_item.text(_COL_NEXT_RUN), "",
                         "у работы нет своего расписания — колонка пуста")

    def test_work_row_has_no_schedule(self):
        pass
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        work_item = _top_level_work_items(page)[0]
        self.assertEqual(work_item.text(_COL_SCHEDULE), "")

    def test_job_status_never_when_not_run(self):
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        self.assertTrue(job_item.text(_COL_STATUS),
                        "статус должен быть заполнен даже для новой задачи")

    def test_no_worker_started_when_no_jobs(self):
        pass
        _, _, worker_cls = self.make_page_with_worker_mock(works=[
            {"work_title": "Docs", "jobs": []},
        ])
        worker_cls.assert_not_called()

    def test_worker_started_when_jobs_present(self):
        pass
        _, _, worker_cls = self.make_page_with_worker_mock(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        worker_cls.assert_called_once()


class TestJobIcons(_TmpMixin):
    pass







    def test_backup_job_has_gear_icon(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [
                {"title": "Daily", "action": "backup"},
            ]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        text = job_item.text(_COL_NAME)
        self.assertTrue(text.startswith("⚙"),
                        f"у бэкапа должен быть значок ⚙: {text!r}")

    def test_check_job_has_magnifier_icon(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [
                {"title": "Monthly", "action": ACTION_TEST},
            ]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        text = job_item.text(_COL_NAME)
        self.assertTrue(text.startswith("🔍"),
                        f"у проверки должен быть значок 🔍: {text!r}")

    def test_legacy_job_without_action_gets_backup_icon(self):
        pass




        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "Old job"}]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        text = job_item.text(_COL_NAME)
        self.assertTrue(text.startswith("⚙"),
                        f"legacy-задание — это бэкап: {text!r}")

    def test_two_jobs_one_work_have_different_icons(self):
        pass
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [
                {"title": "Backup", "action": "backup"},
                {"title": "Check", "action": ACTION_TEST},
            ]},
        ])
        work_item = _top_level_work_items(page)[0]
        text_backup = work_item.child(0).text(_COL_NAME)
        text_check = work_item.child(1).text(_COL_NAME)
        self.assertTrue(text_backup.startswith("⚙"))
        self.assertTrue(text_check.startswith("🔍"))
        self.assertNotEqual(text_backup[0], text_check[0])


class TestScheduleColumn(_TmpMixin):
    pass







    def test_empty_schedule_shows_dash(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "j"}]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        self.assertEqual(job_item.text(_COL_SCHEDULE), "—")

    def test_disabled_schedule_shows_dash(self):
        pass
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{
                "title": "j",
                "schedule": {"enabled": False},
            }]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        self.assertEqual(job_item.text(_COL_SCHEDULE), "—")

    def test_daily_schedule_shows_text(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{
                "title": "j",
                "schedule": {
                    "enabled": True,
                    "frequency": "daily",
                    "time": "02:00",
                    "interval": 1,
                },
            }]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        text = job_item.text(_COL_SCHEDULE)
        self.assertNotEqual(text, "—")
        self.assertNotIn("sched.fmt", text,
                         "локализация сломалась — в ячейке ключ, а не текст")
        self.assertIn("02:00", text)

    def test_weekly_schedule_shows_days(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{
                "title": "j",
                "schedule": {
                    "enabled": True,
                    "frequency": "weekly",
                    "time": "10:00",
                    "interval": 1,
                    "days": ["MON", "WED", "FRI"],
                },
            }]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        text = job_item.text(_COL_SCHEDULE)
        self.assertNotEqual(text, "—")
        self.assertIn("10:00", text)
        self.assertEqual(text.count(","), 2,
                         "должно быть три дня недели через запятую")

    def test_unknown_frequency_shows_dash(self):
        pass
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{
                "title": "j",
                "schedule": {"enabled": True, "frequency": "weird"},
            }]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        self.assertEqual(job_item.text(_COL_SCHEDULE), "—")


                                                                      


class TestSelectedJob(_TmpMixin):
    def test_none_when_nothing_selected(self):
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        self.assertIsNone(page.selected_job())

    def test_none_when_page_hidden(self):
        pass





        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        _APP.processEvents()
        self.assertIsNone(page.selected_job())

    def test_none_when_empty_state_shown(self):
        page, _ = self.make_page(works=[])
        self.assertIsNone(page.selected_job())

    def test_returns_job_when_job_selected(self):
        page, c = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        _force_visible(page)

        work_item = _top_level_work_items(page)[0]
        job_item = work_item.child(0)
        _select_item(page, job_item)

        sel = page.selected_job()
        self.assertIsNotNone(sel,
                             "после setCurrentItem currentItem вернул None")
        self.assertEqual(sel["work_id"], c["works"][0]["id"])
        self.assertEqual(sel["job_id"], c["works"][0]["jobs"][0]["id"])

    def test_returns_job_for_test_job(self):
        pass



        page, c = self.make_page(works=[
            {"work_title": "Docs", "jobs": [
                {"title": "Check", "action": ACTION_TEST},
            ]},
        ])
        _force_visible(page)

        job_item = _top_level_work_items(page)[0].child(0)
        _select_item(page, job_item)

        sel = page.selected_job()
        self.assertIsNotNone(sel)
        self.assertEqual(sel["job_id"], c["works"][0]["jobs"][0]["id"])

    def test_none_when_work_selected(self):
        pass
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        _force_visible(page)

        work_item = _top_level_work_items(page)[0]
        _select_item(page, work_item)

        self.assertIsNone(page.selected_job())


class TestSelectedWork(_TmpMixin):
    def test_none_when_nothing_selected(self):
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        self.assertIsNone(page.selected_work())

    def test_returns_work_when_work_selected(self):
        page, c = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        work_item = _top_level_work_items(page)[0]
        _select_item(page, work_item)
        self.assertEqual(page.selected_work(), c["works"][0]["id"])

    def test_returns_parent_work_when_job_selected(self):
        pass
        page, c = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        _select_item(page, job_item)
        self.assertEqual(page.selected_work(), c["works"][0]["id"])


                                                                              


class TestScheduleCell(_TmpMixin):
    def test_scheduled_sets_text_no_widget(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "Daily"}]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        job_id = _payload(job_item)["job_id"]

        page._set_schedule_cell(job_item, scheduled=True,
                                next_run="2026-10-03 02:00", job_id=job_id)

        self.assertEqual(job_item.text(_COL_NEXT_RUN), "2026-10-03 02:00")
        self.assertIsNone(_cell_widget(job_item, page),
                          "у ячейки с датой не должно быть виджета")

    def test_not_scheduled_sets_widget_no_text(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "Daily"}]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        job_id = _payload(job_item)["job_id"]

        page._set_schedule_cell(job_item, scheduled=False,
                                next_run="", job_id=job_id)

        self.assertEqual(job_item.text(_COL_NEXT_RUN), "",
                         "вместе с кнопкой не должно остаться текст")
        widget = _cell_widget(job_item, page)
        self.assertIsNotNone(widget, "кнопка не поставлена в ячейку")

    def test_button_has_link_object_name(self):
        pass





        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "Daily"}]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        job_id = _payload(job_item)["job_id"]

        page._set_schedule_cell(job_item, scheduled=False,
                                next_run="", job_id=job_id)

        widget = _cell_widget(job_item, page)
        buttons = widget.findChildren(QPushButton)
        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0].objectName(), "backupScheduleLink")

    def test_toggle_text_to_widget(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "Daily"}]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        job_id = _payload(job_item)["job_id"]

        page._set_schedule_cell(job_item, scheduled=True,
                                next_run="2026-10-03 02:00", job_id=job_id)
        page._set_schedule_cell(job_item, scheduled=False,
                                next_run="", job_id=job_id)

        self.assertEqual(job_item.text(_COL_NEXT_RUN), "")
        self.assertIsNotNone(_cell_widget(job_item, page))

    def test_toggle_widget_to_text(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "Daily"}]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        job_id = _payload(job_item)["job_id"]

        page._set_schedule_cell(job_item, scheduled=False,
                                next_run="", job_id=job_id)
        page._set_schedule_cell(job_item, scheduled=True,
                                next_run="2026-10-03 02:00", job_id=job_id)

        self.assertIsNone(_cell_widget(job_item, page),
                          "старая кнопка не снята")
        self.assertEqual(job_item.text(_COL_NEXT_RUN), "2026-10-03 02:00")


                                                                                  


class TestApplySchedule(_TmpMixin):
    def test_hidden_page_stores_info_but_does_not_update_cells(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "Daily"}]},
        ])
        job_item = _top_level_work_items(page)[0].child(0)
        job_id = _payload(job_item)["job_id"]

        info = {job_id: {"scheduled": True,
                         "next_run": "2026-10-03 02:00",
                         "sched_status": "Ready"}}
        page._apply_schedule(info)

        self.assertEqual(page._schedule_info, info)
        self.assertEqual(job_item.text(_COL_NEXT_RUN), "…")

    def test_visible_page_applies_next_run(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "Daily"}]},
        ])
        page.isVisible = lambda: True
        job_item = _top_level_work_items(page)[0].child(0)
        job_id = _payload(job_item)["job_id"]

        page._apply_schedule({job_id: {
            "scheduled": True,
            "next_run": "2026-10-03 02:00",
            "sched_status": "Ready",
        }})

        self.assertEqual(job_item.text(_COL_NEXT_RUN), "2026-10-03 02:00")

    def test_visible_page_puts_button_when_unscheduled(self):
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "Daily"}]},
        ])
        page.isVisible = lambda: True
        job_item = _top_level_work_items(page)[0].child(0)
        job_id = _payload(job_item)["job_id"]

        page._apply_schedule({job_id: {
            "scheduled": False, "next_run": "", "sched_status": "",
        }})

        self.assertIsNotNone(_cell_widget(job_item, page))

    def test_visible_page_puts_button_when_job_missing_from_info(self):
        pass
        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{"title": "Daily"}]},
        ])
        page.isVisible = lambda: True
        job_item = _top_level_work_items(page)[0].child(0)

        page._apply_schedule({})

        self.assertIsNotNone(_cell_widget(job_item, page))

    def test_schedule_column_not_touched_by_worker_result(self):
        pass





        page, _ = self.make_page(works=[
            {"work_title": "W", "jobs": [{
                "title": "j",
                "schedule": {
                    "enabled": True,
                    "frequency": "daily",
                    "time": "02:00",
                    "interval": 1,
                },
            }]},
        ])
        page.isVisible = lambda: True
        job_item = _top_level_work_items(page)[0].child(0)
        before = job_item.text(_COL_SCHEDULE)
        self.assertNotEqual(before, "—")

        page._apply_schedule({})
        self.assertEqual(job_item.text(_COL_SCHEDULE), before)


                                                                          

class TestWorkOrderIsPreserved(_TmpMixin):
    def test_works_kept_in_file_order(self):
        pass
        page, c = self.make_page(works=[
            {"work_title": "First", "jobs": [{"title": "A"}]},
            {"work_title": "Second", "jobs": [{"title": "B"}]},
        ])
        works = _top_level_work_items(page)
        self.assertEqual(len(works), 2)
        self.assertEqual(_payload(works[0])["work_id"], c["works"][0]["id"])
        self.assertEqual(_payload(works[1])["work_id"], c["works"][1]["id"])


                                                                          


class TestMenuActions(_TmpMixin):
    pass









    def test_edit_work_calls_host(self):
        page, c = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        work_id = c["works"][0]["id"]
        page._edit_work(work_id)
        self.assertIn(("_edit_work", work_id), page._host.calls)

    def test_add_backup_job_calls_host(self):
        page, c = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        work_id = c["works"][0]["id"]
        page._add_job(work_id)
        self.assertIn(("_on_add_job_to_work", work_id), page._host.calls)

    def test_add_check_job_calls_host(self):
        page, c = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        work_id = c["works"][0]["id"]
        page._add_check_job(work_id)
        self.assertIn(("_on_add_check_to_work", work_id), page._host.calls)

    def test_edit_work_empty_id_does_nothing(self):
        pass
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        before = list(page._host.calls)
        page._edit_work("")
        self.assertEqual(page._host.calls, before)

    def test_add_backup_job_empty_id_does_nothing(self):
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        before = list(page._host.calls)
        page._add_job("")
        self.assertEqual(page._host.calls, before)

    def test_add_check_job_empty_id_does_nothing(self):
        page, _ = self.make_page(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        before = list(page._host.calls)
        page._add_check_job("")
        self.assertEqual(page._host.calls, before)

    def test_edit_work_missing_host_method_is_safe(self):
        pass












        container = self.write_container(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        host = _HostWithoutEditWork(tasks_dir=str(self.dir))
        with mock.patch.object(BackupPage, "_load_schedule"):
            page = BackupPage(host)
                            
        page._edit_work(container["works"][0]["id"])

    def test_add_check_job_missing_host_method_is_safe(self):
        pass



        container = self.write_container(works=[
            {"work_title": "Docs", "jobs": [{"title": "Daily"}]},
        ])
        host = _HostWithoutCheckJob(tasks_dir=str(self.dir))
        with mock.patch.object(BackupPage, "_load_schedule"):
            page = BackupPage(host)
                            
        page._add_check_job(container["works"][0]["id"])


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
