from __future__ import annotations

from pathlib import Path, PurePosixPath

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from ui.i18n import tr


class _CrumbButton(QPushButton):


    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)


class BreadcrumbBar(QFrame):


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)

        self.setObjectName("breadcrumb")

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(6, 2, 6, 2)
        self._layout.setSpacing(2)
        self._layout.addStretch()


        self._on_fs = None
        self._on_archive = None

    def set_callbacks(self, on_fs=None, on_archive=None):

        self._on_fs = on_fs
        self._on_archive = on_archive

    def update_state(self, mode, fs_path, archive_name, archive_inner):

        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if mode == "fs":
            self._build_fs_crumbs(fs_path)
        elif mode == "archive":
            self._build_archive_crumbs(archive_name, archive_inner)

        self._layout.addStretch()

    def _build_fs_crumbs(self, fs_path):

        if fs_path is None:
            return

        fs_path = Path(fs_path)


        parts = []
        p = fs_path
        while True:
            parts.append(p)
            if p.parent == p:
                break
            p = p.parent

        parts.reverse()

        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            label = part.name or str(part)

            if is_last:


                lbl = QLabel(label)
                lbl.setObjectName("crumb_last")
                self._layout.addWidget(lbl)
            else:


                path_str = str(part)
                btn = _CrumbButton(label)
                btn.clicked.connect(
                    lambda checked=False, p=path_str: self._on_fs_clicked(p)
                )
                self._layout.addWidget(btn)
                self._add_separator()

    def _build_archive_crumbs(self, archive_name, archive_inner):


        if not archive_inner:
            lbl = QLabel(f"{archive_name} :: /")


            lbl.setObjectName("crumb_last")
            self._layout.addWidget(lbl)
            return


        btn = _CrumbButton(archive_name)
        btn.clicked.connect(
            lambda checked=False: self._on_archive_clicked("")
        )
        self._layout.addWidget(btn)
        self._add_separator()


        inner_parts = PurePosixPath(archive_inner).parts
        for i, part in enumerate(inner_parts):
            is_last = i == len(inner_parts) - 1

            seg_path = "/".join(inner_parts[: i + 1])

            if is_last:
                lbl = QLabel(part)


                lbl.setObjectName("crumb_last")
                self._layout.addWidget(lbl)
            else:
                btn = _CrumbButton(part)
                btn.clicked.connect(
                    lambda checked=False, p=seg_path: self._on_archive_clicked(p)
                )
                self._layout.addWidget(btn)
                self._add_separator()

    def _add_separator(self):

        sep = QLabel("›")
        sep.setObjectName("sep")
        self._layout.addWidget(sep)

    def _on_fs_clicked(self, path_str: str):

        if self._on_fs:
            self._on_fs(path_str)

    def _on_archive_clicked(self, inner: str):

        if self._on_archive:
            self._on_archive(inner)
