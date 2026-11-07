

















from __future__ import annotations

import re
import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from ui.i18n import tr
from ui.presentation import format_size


                                                                      
                                           
                                                               

PROGRESS_WINDOW_MIN_WIDTH = 620
PROGRESS_WINDOW_MIN_HEIGHT = 280

PROGRESS_WINDOW_WIDTH = 680
PROGRESS_WINDOW_HEIGHT = 320


_PROGRESS_LINE_RE = re.compile(r"\d{1,3}(?:[.,]\d+)?\s*%")


def _elide_mid(text: str, n: int) -> str:
    pass
    if not text:
        return ""

    text = str(text)

    if len(text) <= n:
        return text

    half = max(1, (n - 1) // 2)
    return text[:half] + "…" + text[-half:]


def _fmt_time(seconds: int) -> str:
    pass
    if seconds < 0:
        return "—"

    if seconds < 60:
        return f"{seconds}s"

    m, s = divmod(seconds, 60)

    if m < 60:
        return f"{m}:{s:02d}"

    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}"


def _fmt_eta(seconds: int) -> str:
    pass
    if seconds < 0:
        return "—"

    return "~" + _fmt_time(seconds)


class OperationProgressDialog(QDialog):
    pass















    cancelRequested = Signal()

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)

        self._base_title = title or tr("progress.title")
        self._finished = True
        self._mode = "generic"

        self._start_time = 0.0
        self._last_pct = 0
        self._engine_eta = ""

                                                                  
        self._auto_close_on_ok = False

        self.setWindowTitle(self._base_title)
        self.setModal(False)

        try:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowContextHelpButtonHint
            )
        except Exception:
            pass

                                                   
        self.setMinimumSize(
            PROGRESS_WINDOW_MIN_WIDTH,
            PROGRESS_WINDOW_MIN_HEIGHT,
        )
        self.resize(
            PROGRESS_WINDOW_WIDTH,
            PROGRESS_WINDOW_HEIGHT,
        )

        self._create_ui()

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_timer)

        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self.accept)

                                                                     
    def _create_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

                    
        self._title = QLabel(self._base_title)
        self._title.setObjectName("opTitle")
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

                                 
        bar_row = QHBoxLayout()
        bar_row.setSpacing(8)

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(14)
        bar_row.addWidget(self._bar, 1)

        self._pct_label = QLabel("")
        self._pct_label.setObjectName("opPct")
        self._pct_label.setFixedWidth(48)
        self._pct_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bar_row.addWidget(self._pct_label)

        layout.addLayout(bar_row)

                               
        grid = QGridLayout()
        grid.setContentsMargins(0, 2, 0, 2)
        grid.setSpacing(5)
        self._info_grid = grid
        self._info_pairs = []

        self._files_label = QLabel("—")
        self._dirs_label = QLabel("—")
        self._size_label = QLabel("—")
        self._speed_label = QLabel("—")
        self._elapsed_label = QLabel("0s")
        self._eta_label = QLabel("—")

        for w in (
            self._files_label,
            self._dirs_label,
            self._size_label,
            self._speed_label,
            self._elapsed_label,
            self._eta_label,
        ):
            w.setObjectName("opFieldValue")

        def add_pair(row: int, col: int, label_text: str, value_widget):
            lbl = QLabel(label_text)
            lbl.setObjectName("opFieldLabel")
            grid.addWidget(lbl, row, col, Qt.AlignRight)
            grid.addWidget(value_widget, row, col + 1)
                                                                     
                                                                        
                                                                      
                                                         
            self._info_pairs.append((lbl, value_widget))

                       
        add_pair(0, 0, tr("create.progress_files"), self._files_label)
        add_pair(0, 2, tr("create.progress_dirs"), self._dirs_label)

                           
        add_pair(1, 0, tr("table.header.size"), self._size_label)
        add_pair(1, 2, tr("create.progress_speed"), self._speed_label)

                           
        add_pair(2, 0, tr("create.progress_elapsed"), self._elapsed_label)
        add_pair(2, 2, tr("create.progress_eta"), self._eta_label)

        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        layout.addLayout(grid)

                                
        self._current = QLabel("")
        self._current.setObjectName("opCurrent")
        self._current.setWordWrap(False)
        layout.addWidget(self._current)

                                     
        self._log = QPlainTextEdit()
        self._log.setObjectName("opLog")
        self._log.setReadOnly(True)
        self._log.setFixedHeight(84)
        self._log.setMaximumBlockCount(800)
        self._log.setVisible(False)
        layout.addWidget(self._log)

                                                      
        bottom = QHBoxLayout()
        bottom.setSpacing(6)

        self._log_btn = QToolButton()
        self._log_btn.setText("▸")
        self._log_btn.setCheckable(True)
        self._log_btn.setChecked(False)
        self._log_btn.setFixedWidth(20)
        self._log_btn.setToolTip(tr("create.errorlog"))
        self._log_btn.clicked.connect(self._toggle_log)
        bottom.addWidget(self._log_btn)

        bottom.addStretch(1)

        self._btn = QPushButton(tr("progress.cancel"))
        self._btn.clicked.connect(self._on_button)
        bottom.addWidget(self._btn)

        layout.addLayout(bottom)

    @staticmethod
    def _repolish(w) -> None:
        pass






        try:
            w.style().unpolish(w)
            w.style().polish(w)
        except Exception:
            pass

                                                                         
    def begin(self, title: str = "", status: str = "") -> None:
        pass
        self._close_timer.stop()

        if title:
            self._base_title = title

        self.setWindowTitle(self._base_title)
        self._title.setText(self._base_title)

        self._finished = False
                                                                       
        self._title.setProperty("state", "")
        self._repolish(self._title)
        self._start_time = time.monotonic()
        self._last_pct = 0
        self._engine_eta = ""

        self._bar.setRange(0, 0)
        self._bar.setValue(0)
        self._pct_label.setText("")

        self._files_label.setText("—")
        self._dirs_label.setText("—")
        self._size_label.setText("—")
        self._speed_label.setText("—")
        self._elapsed_label.setText("0s")
        self._eta_label.setText("—")

        self._current.setText(
            _elide_mid(status or tr("progress.preparing"), 160)
        )

        self._log.clear()

        self._log_btn.setChecked(False)
        self._log_btn.setText("▸")
        self._log.setVisible(False)

        self._btn.setEnabled(True)
        self._btn.setText(tr("progress.cancel"))

        self._timer.start()

        self.show()
        self.raise_()
        self.activateWindow()

    def next_stage(self, title: str = "", status: str = "") -> None:
        pass










        self._close_timer.stop()

        if title:
            self._base_title = title

        self.setWindowTitle(self._base_title)
        self._title.setText(self._base_title)
        self._title.setProperty("state", "")
        self._repolish(self._title)

        self._finished = False
        self._start_time = time.monotonic()
        self._last_pct = 0
        self._engine_eta = ""

        self._bar.setRange(0, 0)
        self._bar.setValue(0)
        self._pct_label.setText("")

        self._current.setText(
            _elide_mid(status or tr("progress.preparing"), 160)
        )

        self._btn.setEnabled(True)
        self._btn.setText(tr("progress.cancel"))

        self._timer.start()

        self.raise_()

    def set_percent(self, pct: int) -> None:
        pass
        if self._finished:
            return

                                                           
        if self._mode == "files":
            return

        try:
            p = max(0, min(100, int(pct)))
        except Exception:
            return

        if self._bar.minimum() != 0 or self._bar.maximum() != 100:
            self._bar.setRange(0, 100)

        self._bar.setValue(p)
        self._pct_label.setText(f"{p}%")
        self._last_pct = p

        if not self._engine_eta:
            self._update_eta()

    def update_info(self, info: dict) -> None:
        pass
        if self._finished or not isinstance(info, dict):
            return

        speed = info.get("speed")
        if speed:
            self._speed_label.setText(str(speed))

        eta = info.get("eta")
        if eta:
            self._engine_eta = str(eta)
            self._eta_label.setText("~" + self._engine_eta)

        files_total = info.get("files_total")
        if files_total is not None and self._mode != "files":
            try:
                self._files_label.setText(
                    f"{int(files_total):,}".replace(",", " ")
                )
            except Exception:
                self._files_label.setText(str(files_total))

        dirs_total = info.get("dirs_total")
        if dirs_total is not None:
            try:
                self._dirs_label.setText(
                    f"{int(dirs_total):,}".replace(",", " ")
                )
            except Exception:
                self._dirs_label.setText(str(dirs_total))

        bytes_total = info.get("bytes_total")
        if bytes_total is not None:
            try:
                self._size_label.setText(format_size(int(bytes_total)))
            except Exception:
                self._size_label.setText(str(bytes_total))

    def hide_info_fields(self, keep=()) -> None:
        pass










        names = {
            "files": self._files_label,
            "dirs": self._dirs_label,
            "size": self._size_label,
            "speed": self._speed_label,
            "elapsed": self._elapsed_label,
            "eta": self._eta_label,
        }
        keep = set(keep) & set(names)
                                                                      
                                  
        for lbl, val in self._info_pairs:
            field = next((k for k, v in names.items() if v is val), None)
            if field is None or field in keep:
                continue
            lbl.setVisible(False)
            val.setVisible(False)

    def append_output(self, text: str) -> None:
        pass
        if self._finished or not text:
            return

        text = str(text).rstrip()
        if not text:
            return

                                                              
                                              
        if _PROGRESS_LINE_RE.search(text) and len(text) <= 220:
            self._current.setText(_elide_mid(text, 160))
            return

        self._current.setText(_elide_mid(text, 160))
        self._log.appendPlainText(text)

    def tick(self, i: int, total: int, path: str) -> None:
        pass
        if self._finished or self._mode != "files":
            return

        try:
            i = int(i)
            total = int(total)
        except Exception:
            return

        self._files_label.setText(f"{i} / {max(total, 0)}")

        if total > 0:
            pct = int(i * 100 / total)
            pct = max(0, min(100, pct))
            self._pct_label.setText(f"{pct}%")
            self._bar.setValue(i)

        self._current.setText(_elide_mid(path or "", 160))

    def finish(self, ok: bool, message: str = "") -> None:
        pass
        if self._finished:
            return

        self._finished = True
        self._timer.stop()
        self._close_timer.stop()

        self._bar.setRange(0, 100)

        if ok:
            self._bar.setValue(100)
            self._pct_label.setText("100%")
            self._title.setText(tr("progress.done"))
            self._title.setProperty("state", "ok")
            self._repolish(self._title)
        else:
            self._title.setText(tr("progress.errors"))
            self._title.setProperty("state", "err")
            self._repolish(self._title)
                                              
            self._log_btn.setChecked(True)
            self._log.setVisible(True)
            self._log_btn.setText("▾")

        self._current.setText(_elide_mid(message or "", 160))

        self._btn.setEnabled(True)
        self._btn.setText(tr("archive_info.close"))

        if ok and self._auto_close_on_ok:
            self._close_timer.start(900)

                                                                           
    def _on_timer(self) -> None:
        if self._finished:
            return

        elapsed = int(time.monotonic() - self._start_time)
        self._elapsed_label.setText(_fmt_time(elapsed))

        if not self._engine_eta:
            self._update_eta()

    def _update_eta(self) -> None:
        pct = self._last_pct

        if pct <= 0:
            self._eta_label.setText("—")
            return

        if pct >= 100:
            self._eta_label.setText("0s")
            return

        elapsed = time.monotonic() - self._start_time
        if elapsed <= 0:
            self._eta_label.setText("—")
            return

        total_est = elapsed * 100.0 / pct
        remaining = total_est - elapsed

        self._eta_label.setText(_fmt_eta(int(remaining)))

    def _toggle_log(self) -> None:
        checked = bool(self._log_btn.isChecked())
        self._log.setVisible(checked)
        self._log_btn.setText("▾" if checked else "▸")

    def _on_button(self) -> None:
        if self._finished:
            self.accept()
            return

        self._btn.setEnabled(False)
        self.cancelRequested.emit()

    def closeEvent(self, ev) -> None:
                                                        
        if not self._finished:
            self.cancelRequested.emit()

        super().closeEvent(ev)
