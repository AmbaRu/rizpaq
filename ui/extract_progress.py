







from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.i18n import tr

try:
    _EASE_OUT = QEasingCurve.Type.OutCubic
except AttributeError:
    try:
        _EASE_OUT = QEasingCurve.OutCubic
    except AttributeError:
        _EASE_OUT = QEasingCurve.Linear

_TARGET_H = 80
_VALUE_MS = 130
_HOLD_MS = 1700
_PULSE_MS = 950
_SCAN_MS = 60
_SEC_MS = 1000



def _elide_mid(text: str, n: int) -> str:
    if not text:
        return ""

    if len(text) <= n:
        return text

    half = max(1, (n - 1) // 2)
    return text[:half] + "…" + text[-half:]


def _fmt_seconds(s: int) -> str:
    if s < 60:
        return f"{s}s"
    m, ss = divmod(s, 60)
    return f"{m}:{ss:02d}"


class ExtractProgressBar(QFrame):
    pass

    cancelRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("extractbar")
                                                                            
                                                                    
                                                                    
                                 
        self.setFixedHeight(0)
        self.setVisible(False)

        self._mode = "idle"                                 
        self._percent_mode = False
        self._seconds = 0
        self._scan = 0
        self._scan_dir = 1

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 8, 12, 9)
        outer.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(9)

        self._icon = QLabel("↓")
        self._icon.setObjectName("exbar_icon")
        self._icon.setProperty("run", "1")
        self._icon.setAlignment(Qt.AlignCenter)

        self._icon_eff = QGraphicsOpacityEffect(self._icon)
        self._icon.setGraphicsEffect(self._icon_eff)

        top.addWidget(self._icon)

        self._title = QLabel(tr("progress.title"))
        self._title.setObjectName("exbar_title")
        top.addWidget(self._title)

        top.addStretch(1)

        self._counter = QLabel("")
        self._counter.setObjectName("exbar_counter")
        self._counter.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top.addWidget(self._counter)

        self._cancel = QPushButton(tr("progress.cancel"))
        self._cancel.setObjectName("exbar_cancel")
        self._cancel.setVisible(False)
        self._cancel.clicked.connect(lambda _=False: self.cancelRequested.emit())
        top.addWidget(self._cancel)

        outer.addLayout(top)

        self._bar = QProgressBar()
        self._bar.setObjectName("exbar_track")
        self._bar.setTextVisible(False)
        self._bar.setRange(0, 1)
        self._bar.setValue(0)
        outer.addWidget(self._bar)

        self._path = QLabel("")
        self._path.setObjectName("exbar_path")
        outer.addWidget(self._path)

        self._val_anim = QPropertyAnimation(self._bar, b"value")
        self._val_anim.setDuration(_VALUE_MS)
        self._val_anim.setEasingCurve(_EASE_OUT)

        self._pulse = QPropertyAnimation(self._icon_eff, b"opacity")
        self._pulse.setDuration(_PULSE_MS)
        self._pulse.setStartValue(1.0)
        self._pulse.setEndValue(0.35)
        self._pulse.setLoopCount(-1)
        self._pulse.setEasingCurve(QEasingCurve.InOutSine)

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._hide_now)

        self._sec_timer = QTimer(self)
        self._sec_timer.setInterval(_SEC_MS)
        self._sec_timer.timeout.connect(self._on_sec)

        self._scan_timer = QTimer(self)
        self._scan_timer.setInterval(_SCAN_MS)
        self._scan_timer.timeout.connect(self._on_scan)

                                                                             
    def begin_folder(self, total: int) -> None:
        self._reset_for_run()
        self._mode = "files"
        self._set_state_run()

        self._title.setText(tr("progress.title_folder"))
        self._counter.setText(f"0 / {max(total, 0)}")
        self._path.setText(tr("progress.preparing"))

        self._bar.setRange(0, max(total, 1))
        self._bar.setValue(0)

        self._cancel.setVisible(True)
        self._show_now()
        self._sec_timer.start()

    def tick(self, i: int, total: int, path: str) -> None:
        if self._mode != "files":
            return

        self._counter.setText(f"{i} / {max(total, 0)}")
        self._path.setText(_elide_mid(path or "", 96))

        self._val_anim.stop()
        self._val_anim.setStartValue(self._bar.value())
        self._val_anim.setEndValue(int(i))
        self._val_anim.start()

    def begin_batch(self) -> None:
        self._reset_for_run()
        self._mode = "batch"
        self._set_state_run()

        self._title.setText(tr("progress.title_folder"))
        self._counter.setText("0s")
        self._path.setText(tr("progress.batch_pass"))

        self._bar.setRange(0, 100)
        self._bar.setValue(0)

        self._cancel.setVisible(True)
        self._show_now()
        self._sec_timer.start()
        self._scan_timer.start()

    def begin_file(self, name: str = "") -> None:
        self._reset_for_run()
        self._mode = "single"
        self._set_state_run()

        self._title.setText(tr("progress.title_file"))
        self._counter.setText("0s")
        self._path.setText(_elide_mid(name or "", 96))

        self._bar.setRange(0, 100)
        self._bar.setValue(0)

        self._cancel.setVisible(True)
        self._show_now()
        self._sec_timer.start()
        self._scan_timer.start()

    def set_percent(self, pct: int) -> None:
        pass
        if self._mode == "idle":
            return

        try:
            p = max(0, min(100, int(pct)))
        except (TypeError, ValueError):
            return

        self._percent_mode = True
        self._scan_timer.stop()
        self._bar.setRange(0, 100)
        self._bar.setValue(p)
        self._counter.setText(f"{p}%")

    def finish(self, ok: bool, total: int, msg: str) -> None:
        self._dismiss_timer.stop()
        self._stop_run_timers()
        self._stop_pulse()
        self._val_anim.stop()

        mode = self._mode

        self._bar.setRange(0, 1)
        self._bar.setValue(1 if ok else 0)

        self._icon.setProperty("run", "0")
        self._icon.setProperty("ok", "1" if ok else "0")
        self._icon.setProperty("err", "0" if ok else "1")
        self._icon.setText("✓" if ok else "!")
        self._repolish(self._icon)
        self._icon_eff.setOpacity(1.0)

        self._title.setProperty("ok", "1" if ok else "0")
        self._title.setProperty("err", "0" if ok else "1")
        self._title.setText(tr("progress.done") if ok else tr("progress.errors"))
        self._repolish(self._title)

        if mode in ("batch", "single"):
            self._counter.setText(_fmt_seconds(self._seconds) if ok else "—")
        elif mode == "files" and total and total > 0:
            self._counter.setText(f"{total} / {total}" if ok else f"? / {total}")

        self._path.setText(_elide_mid(msg or "", 96))

        self._cancel.setVisible(False)
        self._dismiss_timer.start(_HOLD_MS)

                                                                             
    def _on_sec(self) -> None:
        self._seconds += 1

                                                                      
        if self._mode == "files":
            return

        if not self._percent_mode:
            self._counter.setText(_fmt_seconds(self._seconds))

    def _on_scan(self) -> None:
        if self._percent_mode:
            return

        self._scan += 2 * self._scan_dir
        if self._scan >= 100:
            self._scan = 100
            self._scan_dir = -1
        elif self._scan <= 0:
            self._scan = 0
            self._scan_dir = 1

        self._bar.setValue(self._scan)

    def _show_now(self) -> None:
        self._dismiss_timer.stop()
        self.setVisible(True)
        self.setFixedHeight(_TARGET_H)
        self.update()

    def _hide_now(self) -> None:
        self._mode = "idle"
        self._cancel.setVisible(False)
        self.setVisible(False)
        self.setFixedHeight(0)

    def _reset_for_run(self) -> None:
        self._dismiss_timer.stop()
        self._stop_run_timers()
        self._val_anim.stop()
        self._seconds = 0
        self._scan = 0
        self._scan_dir = 1
        self._percent_mode = False

    def _stop_run_timers(self) -> None:
        self._sec_timer.stop()
        self._scan_timer.stop()

    def _set_state_run(self) -> None:
        self._icon.setProperty("run", "1")
        self._icon.setProperty("ok", "0")
        self._icon.setProperty("err", "0")
        self._icon.setText("↓")
        self._repolish(self._icon)

        self._title.setProperty("ok", "0")
        self._title.setProperty("err", "0")
        self._repolish(self._title)

        self._icon_eff.setOpacity(1.0)

        if self._pulse.state() != QPropertyAnimation.Running:
            self._pulse.start()

    def _stop_pulse(self) -> None:
        self._pulse.stop()

    @staticmethod
    def _repolish(w: QWidget) -> None:
        w.style().unpolish(w)
        w.style().polish(w)
