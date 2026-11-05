from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.universal_ops import list_universal
from workers.streaming import StreamingZpaqThread


class UniversalListWorker(QThread):

    listed = Signal(list, str)

    def __init__(
        self,
        bin_path: str,
        archive_path: str,
        password: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.bin_path = bin_path
        self.archive_path = archive_path
        self.password = password

    def run(self):
        entries, log = list_universal(
            self.bin_path, self.archive_path, self.password
        )
        self.listed.emit(entries, log)


class UniversalExtractWorker(StreamingZpaqThread):

    done = Signal(dict)

    def __init__(
        self,
        bin_path: str,
        archive_path: str,
        dest_dir: str,
        password: str | None = None,
        files: list | None = None,
        parent=None,
    ):

        cmd = [bin_path, "x", archive_path, f"-o{dest_dir}", "-sccUTF-8", "-y"]
        if password:


            cmd += [f"-p{password}"]
        if files:
            cmd.extend(files)


        super().__init__(cmd, parent)
        self.dest_dir = dest_dir
        self.files = list(files) if files else None

    def _destination_filled(self) -> bool:
        try:
            dest = Path(self.dest_dir)
            if not dest.is_dir():
                return False
            if self.files:
                literal = [
                    f for f in self.files if "*" not in f and "?" not in f
                ]
                if len(literal) == len(self.files):
                    return all((dest / f).exists() for f in literal)
            return next(dest.iterdir(), None) is not None
        except OSError:
            return False

    def run(self):


        rc, text = self._run_stream()

        self.done.emit({


            "ok": rc == 0 and not self._cancel and self._destination_filled(),
            "cancelled": bool(self._cancel),
            "log": text,
            "dest_dir": self.dest_dir,
        })
