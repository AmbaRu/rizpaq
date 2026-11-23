
from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core import extra_dests
from core.headless import _build_create_cmd
from core.zpaq_cli import run_zpaq


class ExtraDestsWorker(QThread):
    pass

    done = Signal(dict)

    def __init__(self, zpaq_bin, settings, srcs, dests, password=None,
                 work=None, rzp_path="", parent=None):
        super().__init__(parent)
        self._zpaq_bin = zpaq_bin
        self._settings = dict(settings or {})
        self._srcs = list(srcs or [])
        self._dests = list(dests or [])
        self._password = password
        self._work = work
        self._rzp_path = rzp_path

    def run(self):
        ok, log = extra_dests.run_extra_dests(
            self._zpaq_bin,
            self._settings,
            self._srcs,
            self._dests,
            self._password,
            build_cmd=_build_create_cmd,
            runner=run_zpaq,
            work=self._work,
            rzp_path=self._rzp_path,
        )
        self.done.emit({"ok": bool(ok), "log": log})
