
from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core import restore_drill


class RestoreDrillWorker(QThread):
    pass

    done = Signal(dict)

    def __init__(self, zpaq_bin, archive, password=None, sources=None,
                 context=None, parent=None):
        super().__init__(parent)
        self._zpaq_bin = zpaq_bin
        self._archive = archive
        self._password = password
        self._sources = list(sources or [])
        self._context = dict(context or {})

    def run(self):
        ok, log = restore_drill.run_restore_drill(
            self._zpaq_bin, self._archive, self._password, self._sources
        )
        result = dict(self._context)
        result.update(ok=ok, log=log, archive=self._archive)
        self.done.emit(result)
