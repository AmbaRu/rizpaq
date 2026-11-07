












from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.run_history import RunEntry
from ui import skins
from ui.i18n import tr

                                                                    
                                                       
_STATUS_TOKEN = {
    "ok": "OK_GREEN",
    "error": "DIFF_REMOVED",
    "busy": "BUSY_STEEL",
}

                                                                     
                                                                     
MAX_ITEMS = 40


def _status_color(status: str) -> QColor:
    return QColor(skins.color(_STATUS_TOKEN.get(status or "ok", "TEXT_MUTED")))


def _status_caption(entry: RunEntry) -> str:
    pass
    caption = tr(f"dashboard.status.{entry.status}")
    if entry.status == "error" and entry.tail:
                                                                   
                                                    
        first = (entry.tail[0] or "").strip()
        if first:
            caption = f"{caption} · {first}"
    return caption


class _RunItem(QFrame):
    pass

    clicked = Signal(str, str)                                         

    def __init__(self, entry: RunEntry, parent=None):
        super().__init__(parent)
        self.setObjectName("dashFeedItem")
        self.setCursor(Qt.PointingHandCursor)
        self._work_id = entry.work_id
        self._job_id = entry.job_id

        color = _status_color(entry.status).name()
        self.setStyleSheet(f"""
            QFrame#dashFeedItem {{
                background: {skins.color('BASE_BG')};
                border: 1px solid {skins.color('BORDER_SOFT')};
                border-left: 3px solid {color};
                border-radius: 6px;
            }}
            QFrame#dashFeedItem:hover {{
                background: {skins.color('ROW_HOVER')};
                border: 1px solid {skins.color('BORDER')};
                border-left: 3px solid {color};
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 5, 8, 5)
        lay.setSpacing(1)

        top = QHBoxLayout()
        top.setSpacing(6)
                                                                 
                                                                    
        if entry.ts_dt is not None:
            time_text = entry.ts_dt.strftime("%d.%m %H:%M")
        else:
            time_text = entry.ts or "—"
        time_lbl = QLabel(time_text)
        time_lbl.setStyleSheet(f"color: {skins.color('TEXT_MUTED')};")
        top.addWidget(time_lbl)
        title = f"{entry.work_title} · {entry.job_title}".strip(" ·")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {skins.color('TEXT_MAIN')};")
        title_lbl.setTextInteractionFlags(Qt.NoTextInteraction)
        top.addWidget(title_lbl, stretch=1)
        lay.addLayout(top)

        caption = _status_caption(entry)
        cap_lbl = QLabel(caption)
        cap_lbl.setStyleSheet(
            f"color: {skins.color(_STATUS_TOKEN.get(entry.status, 'TEXT_MUTED'))};"
        )
        cap_lbl.setWordWrap(True)
        lay.addWidget(cap_lbl)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._work_id, self._job_id)


class RunFeed(QScrollArea):
    pass








    jobActivated = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        self._lay = QVBoxLayout(body)
        self._lay.setContentsMargins(0, 0, 4, 0)
        self._lay.setSpacing(4)
        self._lay.addStretch()
        self.setWidget(body)

    def set_entries(self, entries: list) -> None:
        pass
                                                                   
        while self._lay.count() > 1:
            item = self._lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not entries:
            empty = QLabel(tr("dashboard.cards.empty"))
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            empty.setStyleSheet(f"color: {skins.color('TEXT_MUTED')};")
            empty.setContentsMargins(8, 16, 8, 16)
            self._lay.insertWidget(0, empty)
            return

        for entry in list(entries)[:MAX_ITEMS]:
            item = _RunItem(entry)
            item.clicked.connect(self.jobActivated)
            self._lay.insertWidget(self._lay.count() - 1, item)
