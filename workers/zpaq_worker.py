from __future__ import annotations

from PySide6.QtCore import Signal

from workers.streaming import StreamingZpaqThread


class ZpaqWorker(StreamingZpaqThread):
    result = Signal(dict)

    def __init__(self, kind: str, cmd, context=None, parent=None, cwd=None):
        super().__init__(cmd, parent, cwd=cwd)
        self.kind = kind
        self.context = context or {}

    def run(self):
        rc, text = self._run_stream()
        self.result.emit(
            {
                "kind": self.kind,
                "rc": rc,
                "output": text,
                "context": dict(self.context),
                "cancelled": bool(self._cancel),
            }
        )
