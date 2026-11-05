from __future__ import annotations

from typing import List

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.archive_ops import slice_at_version
from core.diffops import (
    ADDED,
    CHANGED,
    REMOVED,
    UNCHANGED,
    DiffRecord,
    diff_slices,
    summarize,
)
from ui.i18n import tr
from ui.presentation import format_size
from ui.qt_compat import HEADER_STRETCH, NO_EDIT, SELECT_ROWS
from ui.skins import color as skin_color


_DIFF_STATUS_TOKENS = {
    ADDED:     "DIFF_ADDED",
    REMOVED:   "DIFF_REMOVED",
    CHANGED:   "DIFF_CHANGED",
    UNCHANGED: "DIFF_UNCHANGED",
}


MAX_ROWS = 10000


def _diff_color(status: str) -> QColor:
    token = _DIFF_STATUS_TOKENS.get(status, "DIFF_UNCHANGED")
    return QColor(skin_color(token))


class DiffDialog(QDialog):
    def __init__(self, entries: list, versions: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("diff.title"))
        self.resize(960, 640)

        self._entries = entries
        self._versions = sorted(versions, key=lambda v: v.number)
        self._records: List[DiffRecord] = []

        self._create_ui()


        if len(self._versions) >= 2:
            self.combo_a.setCurrentIndex(len(self._versions) - 2)
            self.combo_b.setCurrentIndex(len(self._versions) - 1)
            self._run_compare()

    def _create_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)


        top = QHBoxLayout()
        top.setSpacing(8)

        top.addWidget(QLabel(tr("diff.version_a")))

        self.combo_a = QComboBox()
        self._fill_combo(self.combo_a)
        top.addWidget(self.combo_a, 1)

        top.addWidget(QLabel(tr("diff.version_b")))

        self.combo_b = QComboBox()
        self._fill_combo(self.combo_b)
        top.addWidget(self.combo_b, 1)

        self.btn_compare = QPushButton(tr("diff.compare_button"))
        self.btn_compare.clicked.connect(self._run_compare)
        top.addWidget(self.btn_compare)

        lay.addLayout(top)


        self.lbl_summary = QLabel("")


        self.lbl_summary.setObjectName("diff_summary")
        lay.addWidget(self.lbl_summary)


        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [
                tr("diff.table.status"),
                tr("diff.table.name"),
                tr("diff.table.path"),
                tr("diff.table.size"),
                tr("diff.table.date"),
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(2, HEADER_STRETCH)
        self.table.setSelectionBehavior(SELECT_ROWS)
        self.table.setEditTriggers(NO_EDIT)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table, 1)

    def _fill_combo(self, combo: QComboBox):
        combo.clear()

        for v in self._versions:
            label = f"v{v.number} · {v.date}"

            if getattr(v, "time", ""):
                label += f" {v.time}"

            comment = (getattr(v, "comment", "") or "").strip()
            if comment:
                label += f" · {comment[:30]}"

            combo.addItem(label, v.number)

    def _run_compare(self):
        va = self.combo_a.currentData()
        vb = self.combo_b.currentData()

        if va is None or vb is None:
            return

        if va > vb:
            va, vb = vb, va

        slice_a = slice_at_version(self._entries, va)
        slice_b = slice_at_version(self._entries, vb)

        self._records = diff_slices(slice_a, slice_b)

        self._populate_table()

        s = summarize(self._records)
        total = len(self._records)

        text = tr(
            "diff.summary",
            a=va,
            b=vb,
            added=s[ADDED],
            changed=s[CHANGED],
            removed=s[REMOVED],
        )

        if total == 0:
            text = tr("diff.no_changes", a=va, b=vb)
        elif total > MAX_ROWS:
            text += "   " + tr("diff.truncated", max=MAX_ROWS, total=total)

        self.lbl_summary.setText(text)

    def _populate_table(self):
        self.table.setRowCount(0)

        for rec in self._records[:MAX_ROWS]:
            row = self.table.rowCount()
            self.table.insertRow(row)


            color = _diff_color(rec.status)

            it_status = QTableWidgetItem(tr(f"diff.status.{rec.status}"))
            it_status.setForeground(color)
            self.table.setItem(row, 0, it_status)

            it_name = QTableWidgetItem(rec.name)
            it_name.setForeground(color)
            self.table.setItem(row, 1, it_name)

            self.table.setItem(row, 2, QTableWidgetItem(rec.path))

            sa = format_size(rec.entry_a.size) if rec.entry_a else "—"
            sb = format_size(rec.entry_b.size) if rec.entry_b else "—"
            self.table.setItem(row, 3, QTableWidgetItem(f"{sa} → {sb}"))

            da = rec.entry_a.datetime if rec.entry_a else "—"
            db = rec.entry_b.datetime if rec.entry_b else "—"
            self.table.setItem(row, 4, QTableWidgetItem(f"{da} → {db}"))
