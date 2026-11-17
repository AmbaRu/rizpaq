






from __future__ import annotations

from PySide6.QtCore import QThread, Signal


class StaleTaskWorker(QThread):
    pass

    done = Signal(list)

    def run(self):
        tasks = []
        try:
            from core.scheduler import find_stale_runner_tasks

            tasks = find_stale_runner_tasks() or []
        except Exception:
            tasks = []
        if not self.isInterruptionRequested():
            self.done.emit(tasks)
