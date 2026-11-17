













from __future__ import annotations

import sys

from PySide6.QtWidgets import QMessageBox

from ui.i18n import tr

_checked = False


def _reset_for_tests() -> None:
    pass
    global _checked
    _checked = False


def should_check() -> bool:
    pass
    if _checked:
        return False
                                                                     
                                                                  
    return bool(getattr(sys, "frozen", False))


def start_check(parent) -> None:
    pass
    global _checked
    if not should_check():
        return
    _checked = True

    try:
        from workers.stale_worker import StaleTaskWorker

        worker = StaleTaskWorker(parent)
        worker.done.connect(
            lambda tasks, p=parent: on_tasks_found(p, tasks)
        )
                                                                 
                                               
        setattr(parent, "_stale_worker", worker)
        worker.start()
    except Exception:
                                                         
        return


def check_on_startup(parent) -> None:
    pass





    global _checked
    if not should_check():
        return
    _checked = True
    try:
        from core.scheduler import find_stale_runner_tasks

        on_tasks_found(parent, find_stale_runner_tasks())
    except Exception:
        return


def on_tasks_found(parent, tasks) -> None:
    pass
    if not tasks:
        return
    try:
        from core.scheduler import container_task_map, create_scheduled_task
        from core.tasks import container_path, load_container

        folder = ""
        try:
            folder = str(parent.tasks_dir() or "")
        except Exception:
            pass
        if not folder:
            return
        path = container_path(folder)
        container = load_container(path)
        if not container:
            return

        items = "\n".join("• " + t.get("name", "") for t in tasks)
        answer = QMessageBox.question(
            parent,
            tr("scheduler.stale_title"),
            tr("scheduler.stale_text", count=len(tasks), items=items),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        known = container_task_map(container)
        ok_count = 0
        fail_count = 0
        for task in tasks:
            name = str(task.get("name") or "")
            found = known.get(name)
            if found is None:
                fail_count += 1
                continue
            work, job = found
            try:
                success = create_scheduled_task(
                    path, work, job, job.get("schedule") or {}
                )
            except Exception:
                success = False
            if success:
                ok_count += 1
            else:
                fail_count += 1

        if ok_count:
            QMessageBox.information(
                parent,
                tr("scheduler.stale_title"),
                tr("scheduler.stale_recreate_ok", count=ok_count),
            )
        if fail_count:
            QMessageBox.warning(
                parent,
                tr("scheduler.stale_title"),
                tr("scheduler.stale_recreate_fail", count=fail_count),
            )
    except Exception:
                                                         
        return
