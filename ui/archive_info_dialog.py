





from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ui.i18n import tr
from ui.presentation import format_size
from ui.qt_compat import HEADER_STRETCH, NO_EDIT, SELECT_ROWS


class ArchiveInfoDialog(QDialog):
    pass

    def __init__(
        self,
        archive_path,
        summary=None,
        versions=None,
        password_set: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("archive_info.title"))
        self.resize(860, 560)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

                               
        path_label = QLabel(str(archive_path))
        path_label.setObjectName("archive_info_path")
        path_label.setWordWrap(True)
        lay.addWidget(path_label)

                        
        summary_label = QLabel(self._summary_text(summary, password_set))
        summary_label.setObjectName("archive_info_summary")
        summary_label.setWordWrap(True)
        lay.addWidget(summary_label)

                        
        versions = sorted(versions or [], key=lambda v: v.number)

        if versions:
            table = QTableWidget()
            table.setColumnCount(7)
            table.setHorizontalHeaderLabels(
                [
                    tr("archive_info.table.version"),
                    tr("archive_info.table.date"),
                    tr("archive_info.table.time"),
                    tr("archive_info.table.added"),
                    tr("archive_info.table.removed"),
                    tr("archive_info.table.size"),
                    tr("archive_info.table.comment"),
                ]
            )
            table.horizontalHeader().setSectionResizeMode(6, HEADER_STRETCH)
            table.setSelectionBehavior(SELECT_ROWS)
            table.setEditTriggers(NO_EDIT)
            table.setAlternatingRowColors(True)
            table.verticalHeader().setVisible(False)
            table.setSortingEnabled(False)

            for v in versions:
                row = table.rowCount()
                table.insertRow(row)

                table.setItem(row, 0, QTableWidgetItem(str(v.number)))
                table.setItem(row, 1, QTableWidgetItem(getattr(v, "date", "")))
                table.setItem(row, 2, QTableWidgetItem(getattr(v, "time", "")))
                table.setItem(row, 3, QTableWidgetItem(str(getattr(v, "added", ""))))
                table.setItem(row, 4, QTableWidgetItem(str(getattr(v, "removed", ""))))
                table.setItem(
                    row, 5, QTableWidgetItem(format_size(getattr(v, "bytes_added", 0)))
                )
                table.setItem(
                    row, 6, QTableWidgetItem(getattr(v, "comment", "") or "")
                )

            lay.addWidget(table, 1)
        else:
            hint = QLabel(tr("archive_info.versions_not_loaded"))
            hint.setWordWrap(True)
            lay.addWidget(hint)
            lay.addStretch(1)

                                 
        bottom = QHBoxLayout()
        bottom.addStretch(1)

        btn_close = QPushButton(tr("archive_info.close"))
        btn_close.clicked.connect(self.accept)
        bottom.addWidget(btn_close)

        lay.addLayout(bottom)

    @staticmethod
    def _summary_text(summary, password_set: bool) -> str:
        lines = []

        if summary:
            lines.append(
                tr("archive_info.summary_versions", versions=summary.versions)
            )
            lines.append(tr("archive_info.summary_files", files=summary.files))
            lines.append(
                tr("archive_info.summary_size", size=format_size(summary.size))
            )
        else:
            lines.append(tr("archive_info.summary_not_loaded"))

        lines.append(
            tr("archive_info.password_set")
            if password_set
            else tr("archive_info.password_not_set")
        )

        return "\n".join(lines)
