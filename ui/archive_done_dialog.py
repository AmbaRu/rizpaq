from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
)

from ui.i18n import tr
from ui.skins import color
from ui.presentation import format_size


class ArchiveDoneDialog(QDialog):


    def __init__(self, report, summary, versions, parent=None):
        super().__init__(parent)

        is_update = bool(report.get("is_update"))
        ok = bool(report.get("ok", True))

        title = tr("create.done.updated") if is_update else tr("create.done.new")
        self.setWindowTitle(title)
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)


        status_text = tr("create.done.ok") if ok else tr("create.done.error")
        icon = "✓" if ok else "!"
        status_label = QLabel(f"{icon}  {title} — {status_text}")
        status_label.setWordWrap(True)


        status_color = color("OK_GREEN") if ok else color("WARN_ORANGE")
        status_label.setStyleSheet(
            f"color: {status_color}; font-weight: 700; font-size: 13px;"
        )
        layout.addWidget(status_label)


        grid = QFormLayout()

        dest = report.get("dest", "")
        dest_label = QLabel(dest)
        dest_label.setWordWrap(True)
        dest_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        grid.addRow(tr("create.done.archive"), dest_label)


        if versions:
            try:
                vobj = max(versions, key=lambda v: v.number)
                vt = f"v{vobj.number}  ·  {vobj.date} {vobj.time}"
                if getattr(vobj, "comment", ""):
                    vt += f"  ·  {vobj.comment}"
                grid.addRow(tr("create.done.version"), QLabel(vt))
            except Exception:
                pass


        stats = report.get("stats")
        if stats:
            original = stats.get("original", 0)
            compressed = stats.get("compressed", 0)

            grid.addRow(
                tr("create.done.original_size"),
                QLabel(format_size(original)),
            )
            grid.addRow(
                tr("create.done.archive_size"),
                QLabel(format_size(compressed)),
            )

            if original > 0:
                ratio_pct = compressed / original * 100
                grid.addRow(
                    tr("create.done.compression"),
                    QLabel(f"{ratio_pct:.1f}%"),
                )


        if summary:
            grid.addRow(tr("create.done.versions"), QLabel(str(summary.versions)))
            grid.addRow(tr("create.done.files"), QLabel(str(summary.files)))
            grid.addRow(tr("create.done.size"), QLabel(format_size(summary.size)))


        test_rc = report.get("test_rc")
        if test_rc is not None:
            if test_rc == 0:
                test_label = QLabel(tr("create.done.test_ok"))


                test_label.setStyleSheet(f"color: {color('OK_GREEN')};")
            else:
                test_label = QLabel(tr("create.done.test_fail"))
                test_label.setStyleSheet(f"color: {color('WARN_ORANGE')};")
            grid.addRow(tr("create.opt_test"), test_label)

        layout.addLayout(grid)


        params_rows = report.get("params_rows") or []
        if params_rows:
            grp = QGroupBox(tr("create.done.params"))
            pg = QFormLayout(grp)
            for label, value in params_rows:
                v = QLabel(str(value))
                v.setWordWrap(True)
                v.setTextInteractionFlags(Qt.TextSelectableByMouse)
                pg.addRow(label, v)
            layout.addWidget(grp)


        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
