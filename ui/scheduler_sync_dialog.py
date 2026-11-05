from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
)

from ui.i18n import tr


class SchedulerSyncDialog(QDialog):

    def __init__(self, rzp_path, container, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("scheduler.sync_title"))
        self.setMinimumWidth(560)
        self.setMinimumHeight(520)

        self._rzp_path = rzp_path
        self._container = container
        self._stats = {"added": 0, "disabled": 0, "removed": 0, "failed": 0}


        from core.scheduler import compute_sync_actions

        try:
            self._actions = compute_sync_actions(container, rzp_path)
        except Exception:
            self._actions = {"add": [], "remove": [], "disable": []}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self._add_list = None
        self._disable_list = None
        self._remove_list = None

        self._build_section(
            layout,
            group_key="scheduler.sync_add_group",
            items=self._actions.get("add") or [],
            kind="add",
        )
        self._build_section(
            layout,
            group_key="scheduler.sync_disable_group",
            items=self._actions.get("disable") or [],
            kind="disable",
        )
        self._build_section(
            layout,
            group_key="scheduler.sync_remove_group",
            items=self._actions.get("remove") or [],
            kind="remove",
        )


        if not any((self._actions.get("add"),
                    self._actions.get("disable"),
                    self._actions.get("remove"))):
            empty = QLabel(tr("scheduler.sync_none"))
            empty.setWordWrap(True)
            layout.addWidget(empty)

        layout.addStretch(1)


        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        if ok_btn is not None:
            ok_btn.setText(tr("scheduler.sync_apply"))
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        if cancel_btn is not None:
            cancel_btn.setText(tr("scheduler.close"))
        buttons.accepted.connect(self._apply_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


    def _build_section(self, layout, group_key: str, items: list, kind: str) -> None:
        if not items:
            return

        group = QGroupBox(f"{tr(group_key)} ({len(items)})")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(4)

        list_widget = QListWidget(group)
        list_widget.setSelectionMode(QListWidget.NoSelection)
        list_widget.setFocusPolicy(Qt.NoFocus)

        for entry in items:
            item = QListWidgetItem(self._format_entry(entry, kind))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, entry)
            list_widget.addItem(item)

        group_layout.addWidget(list_widget)
        layout.addWidget(group)


        if kind == "add":
            self._add_list = list_widget
        elif kind == "disable":
            self._disable_list = list_widget
        elif kind == "remove":
            self._remove_list = list_widget

    @staticmethod
    def _format_entry(entry, kind: str) -> str:
        if kind == "remove":
            name = ""
            if isinstance(entry, dict):
                name = str(entry.get("name") or "")
            return name or "?"


        try:
            work, job = entry
            work_title = str(work.get("title") or "")
            job_title = str(job.get("title") or "")
            if work_title and job_title:
                return f"{work_title} / {job_title}"
            return job_title or work_title or "?"
        except Exception:
            return "?"


    def _checked_entries(self, list_widget) -> list:

        if list_widget is None:
            return []
        out = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item is None:
                continue
            if item.checkState() == Qt.Checked:
                out.append(item.data(Qt.UserRole))
        return out

    def _apply_and_accept(self) -> None:
        try:
            from core.scheduler import (
                create_scheduled_task,
                remove_scheduled_task,
                remove_scheduled_task_by_name,
            )
        except Exception:
            QMessageBox.warning(
                self,
                tr("scheduler.sync_title"),
                tr("scheduler.sync_failed", count=0),
            )
            self.reject()
            return


        for entry in self._checked_entries(self._remove_list):
            name = ""
            if isinstance(entry, dict):
                name = str(entry.get("name") or "")
            if not name:
                self._stats["failed"] += 1
                continue
            try:
                if remove_scheduled_task_by_name(name):
                    self._stats["removed"] += 1
                else:
                    self._stats["failed"] += 1
            except Exception:
                self._stats["failed"] += 1


        for entry in self._checked_entries(self._add_list):
            try:
                work, job = entry
                schedule = job.get("schedule") or {}
                ok = create_scheduled_task(self._rzp_path, work, job, schedule)
                if ok:
                    self._stats["added"] += 1
                else:
                    self._stats["failed"] += 1
            except Exception:
                self._stats["failed"] += 1


        for entry in self._checked_entries(self._disable_list):
            try:
                work, job = entry
                ok = remove_scheduled_task(work, job)
                if ok:
                    self._stats["disabled"] += 1
                else:
                    self._stats["failed"] += 1
            except Exception:
                self._stats["failed"] += 1


        if self._stats["failed"]:
            QMessageBox.warning(
                self,
                tr("scheduler.sync_title"),
                tr(
                    "scheduler.sync_done",
                    added=self._stats["added"],
                    disabled=self._stats["disabled"],
                    removed=self._stats["removed"],
                )
                + "\n"
                + tr("scheduler.sync_failed", count=self._stats["failed"]),
            )
        else:
            QMessageBox.information(
                self,
                tr("scheduler.sync_title"),
                tr(
                    "scheduler.sync_done",
                    added=self._stats["added"],
                    disabled=self._stats["disabled"],
                    removed=self._stats["removed"],
                ),
            )

        self.accept()

    def result_stats(self) -> dict:
        return dict(self._stats)
