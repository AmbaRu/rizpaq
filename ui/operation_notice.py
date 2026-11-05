from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.i18n import tr


NOTICE_DELAY_MS = 400


NOTICE_TICK_MS = 1000


NOTICE_WIDTH = 400
NOTICE_HEIGHT = 132


NOTICE_HINT_AFTER_MS = NOTICE_DELAY_MS * 3


def _fmt_elapsed(seconds: int) -> str:

    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}:{s:02d}"
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}"


class OperationNotice(QWidget):

    cancelRequested = Signal()

    def __init__(self, parent=None, cancel_enabled: bool = False):
        super().__init__(parent)

        self._shown = False
        self._step_text = ""
        self._elapsed_base = time.monotonic()

        self.setWindowTitle(tr("notice.title"))


        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.FramelessWindowHint
            | Qt.Dialog
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setFixedSize(NOTICE_WIDTH, NOTICE_HEIGHT)

        self._build_ui(cancel_enabled)


        self._delay_timer = QTimer(self)
        self._delay_timer.setSingleShot(True)
        self._delay_timer.timeout.connect(self._do_show)


        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(NOTICE_TICK_MS)
        self._tick_timer.timeout.connect(self._on_tick)

        self.hide()


    def _build_ui(self, cancel_enabled: bool) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)


        card = QWidget(self)
        card.setObjectName("noticeCard")
        outer.addWidget(card)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(8)


        self._title = QLabel(card)
        self._title.setWordWrap(True)
        self._title.setObjectName("noticeTitle")
        lay.addWidget(self._title)


        self._bar = QProgressBar(card)
        self._bar.setObjectName("noticeBar")
        self._bar.setRange(0, 0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(10)
        lay.addWidget(self._bar)


        row = QHBoxLayout()
        row.setSpacing(8)

        self._elapsed = QLabel(card)
        self._elapsed.setObjectName("noticeElapsed")
        row.addWidget(self._elapsed)
        row.addStretch(1)

        self._cancel_btn = QPushButton(tr("progress.cancel"), card)
        self._cancel_btn.setFixedHeight(26)
        self._cancel_btn.setVisible(cancel_enabled)
        self._cancel_btn.clicked.connect(self._on_cancel)
        row.addWidget(self._cancel_btn)

        lay.addLayout(row)


        self._hint = QLabel(card)
        self._hint.setObjectName("noticeHint")
        self._hint.setText(tr("notice.long"))
        self._hint.setWordWrap(True)
        self._hint.setVisible(False)
        lay.addWidget(self._hint)

    def retranslate(self) -> None:

        self.setWindowTitle(tr("notice.title"))
        self._cancel_btn.setText(tr("progress.cancel"))
        self._hint.setText(tr("notice.long"))
        self._title.setText(self._step_text)
        self._on_tick()


    def show_notice(self, step_text: str = "") -> None:

        if step_text:
            self.set_step(step_text)

        self._elapsed_base = time.monotonic()
        self._tick_timer.stop()
        self._tick_timer.start()
        self._on_tick()

        if not self._shown:
            self._delay_timer.start(NOTICE_DELAY_MS)

    def update_step(self, text: str) -> None:

        self.set_step(text)

    def set_step(self, text: str) -> None:
        self._step_text = text or ""
        self._title.setText(self._step_text)

    def set_cancel_enabled(self, enabled: bool) -> None:
        self._cancel_btn.setVisible(bool(enabled))

    def is_visible_notice(self) -> bool:

        return self._shown

    def hide_notice(self) -> None:

        self._delay_timer.stop()
        self._tick_timer.stop()
        if self._shown:
            self._shown = False
            self.hide()


    def _do_show(self) -> None:
        if self._shown:
            return
        self._shown = True
        self._center_on_screen()
        self.show()
        self.raise_()

    def _center_on_screen(self) -> None:

        try:
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                return
            area = screen.availableGeometry()
            x = area.x() + (area.width() - self.width()) // 2
            y = area.y() + (area.height() - self.height()) // 2
            self.move(max(area.x(), x), max(area.y(), y))
        except Exception:
            pass

    def _on_tick(self) -> None:
        secs = int(time.monotonic() - self._elapsed_base)
        self._elapsed.setText(f"{tr('create.progress_elapsed')} {_fmt_elapsed(secs)}")
        self._hint.setVisible(secs * 1000 >= NOTICE_HINT_AFTER_MS)

    def _on_cancel(self) -> None:
        self.cancelRequested.emit()
        self.hide_notice()
