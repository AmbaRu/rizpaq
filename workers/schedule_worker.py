from __future__ import annotations

from PySide6.QtCore import QThread, Signal


class ScheduleCreateWorker(QThread):


    done = Signal(bool, str)

    def __init__(self, rzp_path, work, job, schedule, parent=None):
        super().__init__(parent)
        self._rzp_path = rzp_path
        self._work = work
        self._job = job
        self._schedule = schedule

    def run(self):
        try:
            from core.scheduler import create_scheduled_task

            ok = bool(create_scheduled_task(
                self._rzp_path,
                self._work,
                self._job,
                self._schedule,
            ))
            self.done.emit(ok, "")
        except Exception as exc:


            self.done.emit(False, f"{type(exc).__name__}: {exc}")


class ScheduleRemoveWorker(QThread):

    done = Signal(list, list)

    def __init__(self, task_names, parent=None):
        super().__init__(parent)


        self._names = [
            str(n) for n in (task_names or []) if str(n).strip()
        ]

    def run(self):
        ok: list = []
        failed: list = []
        try:
            from core.scheduler import remove_scheduled_task_by_name
        except Exception:


            self.done.emit([], list(self._names))
            return

        for name in self._names:
            try:
                if remove_scheduled_task_by_name(name):
                    ok.append(name)
                else:
                    failed.append(name)
            except Exception:
                failed.append(name)

        self.done.emit(ok, failed)
