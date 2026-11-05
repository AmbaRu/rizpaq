from __future__ import annotations
from PySide6.QtCore import QThread, QTime, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
)
from ui.i18n import tr


class ScheduleDialog(QDialog):


    def __init__(self, parent=None, initial_schedule=None):
        super().__init__(parent)
        self.setWindowTitle(tr("scheduler.title"))
        self.resize(540, 400)
        self._result = None

        layout = QVBoxLayout(self)


        self._enabled_cb = QCheckBox(tr("scheduler.enable"))
        self._enabled_cb.setChecked(True)
        layout.addWidget(self._enabled_cb)


        group = QGroupBox(tr("scheduler.settings"))
        group_layout = QVBoxLayout()


        row_min = QHBoxLayout()
        self._rb_minute = QRadioButton(tr("scheduler.rb_minute"))
        self._spin_minute = QSpinBox()
        self._spin_minute.setRange(1, 59)
        self._spin_minute.setValue(15)
        self._lbl_minute_unit = QLabel(tr("scheduler.minutes"))
        row_min.addWidget(self._rb_minute)
        row_min.addWidget(QLabel(tr("scheduler.every")))
        row_min.addWidget(self._spin_minute)
        row_min.addWidget(self._lbl_minute_unit)
        row_min.addStretch(1)
        group_layout.addLayout(row_min)


        row_hour = QHBoxLayout()
        self._rb_hour = QRadioButton(tr("scheduler.rb_hour"))
        self._spin_hour = QSpinBox()
        self._spin_hour.setRange(1, 23)
        self._spin_hour.setValue(2)
        self._lbl_hour_unit = QLabel(tr("scheduler.hours"))
        row_hour.addWidget(self._rb_hour)
        row_hour.addWidget(QLabel(tr("scheduler.every")))
        row_hour.addWidget(self._spin_hour)
        row_hour.addWidget(self._lbl_hour_unit)
        row_hour.addStretch(1)
        group_layout.addLayout(row_hour)


        row_day = QHBoxLayout()
        self._rb_daily = QRadioButton(tr("scheduler.rb_daily"))
        self._spin_daily = QSpinBox()
        self._spin_daily.setRange(1, 30)
        self._spin_daily.setValue(1)
        self._lbl_daily_unit = QLabel(tr("scheduler.days_unit"))
        self._time_daily = QTimeEdit()
        self._time_daily.setDisplayFormat("HH:mm")
        self._time_daily.setTime(QTime(10, 0))
        row_day.addWidget(self._rb_daily)
        row_day.addWidget(QLabel(tr("scheduler.every")))
        row_day.addWidget(self._spin_daily)
        row_day.addWidget(self._lbl_daily_unit)
        row_day.addWidget(QLabel(tr("scheduler.at")))
        row_day.addWidget(self._time_daily)
        row_day.addStretch(1)
        group_layout.addLayout(row_day)


        self._rb_weekly = QRadioButton(tr("scheduler.rb_weekly"))
        self._spin_weekly = QSpinBox()
        self._spin_weekly.setRange(1, 52)
        self._spin_weekly.setValue(1)
        self._lbl_weekly_unit = QLabel(tr("scheduler.weeks"))
        self._time_weekly = QTimeEdit()
        self._time_weekly.setDisplayFormat("HH:mm")
        self._time_weekly.setTime(QTime(10, 0))

        row_week_top = QHBoxLayout()
        row_week_top.addWidget(self._rb_weekly)
        row_week_top.addWidget(QLabel(tr("scheduler.every")))
        row_week_top.addWidget(self._spin_weekly)
        row_week_top.addWidget(self._lbl_weekly_unit)
        row_week_top.addWidget(QLabel(tr("scheduler.at")))
        row_week_top.addWidget(self._time_weekly)
        row_week_top.addStretch(1)


        self._days_group = QGroupBox(tr("scheduler.days"))
        days_layout = QHBoxLayout()
        self._day_cbs = {}
        for i, (code, label) in enumerate([
            ("MON", tr("scheduler.mon")),
            ("TUE", tr("scheduler.tue")),
            ("WED", tr("scheduler.wed")),
            ("THU", tr("scheduler.thu")),
            ("FRI", tr("scheduler.fri")),
            ("SAT", tr("scheduler.sat")),
            ("SUN", tr("scheduler.sun")),
        ]):
            cb = QCheckBox(label)
            if i < 5:
                cb.setChecked(True)
            self._day_cbs[code] = cb
            days_layout.addWidget(cb)
        self._days_group.setLayout(days_layout)

        week_vbox = QVBoxLayout()
        week_vbox.addLayout(row_week_top)
        week_vbox.addWidget(self._days_group)
        group_layout.addLayout(week_vbox)


        row_month = QHBoxLayout()
        self._rb_monthly = QRadioButton(tr("scheduler.rb_monthly"))
        self._spin_monthly = QSpinBox()
        self._spin_monthly.setRange(1, 12)
        self._spin_monthly.setValue(1)
        self._lbl_monthly_unit = QLabel(tr("scheduler.months"))
        self._dom_edit = QSpinBox()
        self._dom_edit.setRange(1, 31)
        self._dom_edit.setValue(1)
        self._time_monthly = QTimeEdit()
        self._time_monthly.setDisplayFormat("HH:mm")
        self._time_monthly.setTime(QTime(10, 0))

        row_month.addWidget(self._rb_monthly)
        row_month.addWidget(QLabel(tr("scheduler.every")))
        row_month.addWidget(self._spin_monthly)
        row_month.addWidget(self._lbl_monthly_unit)
        row_month.addWidget(QLabel(tr("scheduler.on_day")))
        row_month.addWidget(self._dom_edit)
        row_month.addWidget(QLabel(tr("scheduler.at")))
        row_month.addWidget(self._time_monthly)
        row_month.addStretch(1)
        group_layout.addLayout(row_month)

        group.setLayout(group_layout)
        layout.addWidget(group)


        hint_label = QLabel(tr("scheduler.time_hint"))
        hint_label.setWordWrap(True)
        hint_label.setObjectName("schedHint")
        layout.addWidget(hint_label)


        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


        self._rb_minute.toggled.connect(self._update_ui_state)
        self._rb_hour.toggled.connect(self._update_ui_state)
        self._rb_daily.toggled.connect(self._update_ui_state)
        self._rb_weekly.toggled.connect(self._update_ui_state)
        self._rb_monthly.toggled.connect(self._update_ui_state)


        if initial_schedule:
            self._apply_schedule(initial_schedule)
        else:
            self._rb_daily.setChecked(True)

        self._update_ui_state()

    def _update_ui_state(self):

        is_min = self._rb_minute.isChecked()
        is_hour = self._rb_hour.isChecked()
        is_day = self._rb_daily.isChecked()
        is_week = self._rb_weekly.isChecked()
        is_month = self._rb_monthly.isChecked()

        self._spin_minute.setEnabled(is_min)
        self._lbl_minute_unit.setEnabled(is_min)

        self._spin_hour.setEnabled(is_hour)
        self._lbl_hour_unit.setEnabled(is_hour)

        self._spin_daily.setEnabled(is_day)
        self._lbl_daily_unit.setEnabled(is_day)
        self._time_daily.setEnabled(is_day)

        self._spin_weekly.setEnabled(is_week)
        self._lbl_weekly_unit.setEnabled(is_week)
        self._time_weekly.setEnabled(is_week)
        self._days_group.setEnabled(is_week)

        self._spin_monthly.setEnabled(is_month)
        self._lbl_monthly_unit.setEnabled(is_month)
        self._dom_edit.setEnabled(is_month)
        self._time_monthly.setEnabled(is_month)

    def _apply_schedule(self, schedule: dict):
        self._enabled_cb.setChecked(schedule.get("enabled", True))
        freq = schedule.get("frequency", "daily")

        if freq == "minute":
            self._rb_minute.setChecked(True)
            self._spin_minute.setValue(schedule.get("interval", 15))
        elif freq == "hourly":
            self._rb_hour.setChecked(True)
            self._spin_hour.setValue(schedule.get("interval", 2))
        elif freq == "daily":
            self._rb_daily.setChecked(True)
            self._spin_daily.setValue(schedule.get("interval", 1))
            self._set_time(self._time_daily, schedule.get("time", "10:00"))
        elif freq == "weekly":
            self._rb_weekly.setChecked(True)
            self._spin_weekly.setValue(schedule.get("interval", 1))
            self._set_time(self._time_weekly, schedule.get("time", "10:00"))
            days = schedule.get("days", [])
            for code, cb in self._day_cbs.items():
                cb.setChecked(code in days)
        elif freq == "monthly":
            self._rb_monthly.setChecked(True)
            self._spin_monthly.setValue(schedule.get("interval", 1))
            self._dom_edit.setValue(schedule.get("day_of_month", 1))
            self._set_time(self._time_monthly, schedule.get("time", "10:00"))

    def _set_time(self, time_edit: QTimeEdit, time_str: str):
        try:
            h, m = map(int, time_str.split(":"))
            time_edit.setTime(QTime(h, m))
        except Exception:
            time_edit.setTime(QTime(10, 0))

    def _validate_and_accept(self):
        if not self._enabled_cb.isChecked():
            self._result = {"enabled": False}
            self.accept()
            return

        schedule = {"enabled": True}

        if self._rb_minute.isChecked():
            schedule.update({
                "frequency": "minute",
                "interval": self._spin_minute.value(),
                "time": "00:00"
            })
        elif self._rb_hour.isChecked():
            schedule.update({
                "frequency": "hourly",
                "interval": self._spin_hour.value(),
                "time": "00:00"
            })
        elif self._rb_daily.isChecked():
            schedule.update({
                "frequency": "daily",
                "interval": self._spin_daily.value(),
                "time": self._time_daily.time().toString("HH:mm")
            })
        elif self._rb_weekly.isChecked():
            days = [code for code, cb in self._day_cbs.items() if cb.isChecked()]
            if not days:
                QMessageBox.warning(self, tr("scheduler.title"), tr("scheduler.no_days"))
                return
            schedule.update({
                "frequency": "weekly",
                "interval": self._spin_weekly.value(),
                "time": self._time_weekly.time().toString("HH:mm"),
                "days": days
            })
        elif self._rb_monthly.isChecked():
            schedule.update({
                "frequency": "monthly",
                "interval": self._spin_monthly.value(),
                "time": self._time_monthly.time().toString("HH:mm"),
                "day_of_month": self._dom_edit.value()
            })

        self._result = schedule
        self.accept()

    def result_schedule(self):
        return self._result


class _TaskListWorker(QThread):


    done = Signal(list)

    def run(self):
        from core.scheduler import list_rizpaq_tasks

        try:
            tasks = list_rizpaq_tasks()
        except Exception:
            tasks = []
        self.done.emit(list(tasks or []))


class _TaskRemoveWorker(QThread):


    done = Signal(str, bool)

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self._name = name

    def run(self):
        from core.scheduler import remove_scheduled_task_by_name

        try:
            ok = bool(remove_scheduled_task_by_name(self._name))
        except Exception:
            ok = False
        self.done.emit(self._name, ok)


class SchedulerManagerDialog(QDialog):

    def __init__(self, parent=None, container_provider=None):
        super().__init__(parent)
        self.setWindowTitle(tr("scheduler.manager_title"))
        self.resize(760, 460)

        self._container_provider = container_provider

        layout = QVBoxLayout(self)


        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels([
            tr("scheduler.table.name"),
            tr("scheduler.table.status"),
            tr("scheduler.table.next_run"),
            tr("scheduler.table.link"),
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self._table, 1)


        btn_layout = QHBoxLayout()
        self._refresh_btn = QPushButton(tr("scheduler.refresh"))
        self._refresh_btn.clicked.connect(self._load_tasks)
        btn_layout.addWidget(self._refresh_btn)

        self._orphans_btn = QPushButton(tr("scheduler.orphans_button"))
        self._orphans_btn.clicked.connect(self._remove_orphans)
        btn_layout.addWidget(self._orphans_btn)

        self._sync_btn = QPushButton(tr("scheduler.sync_button"))
        self._sync_btn.clicked.connect(self._open_sync_dialog)
        btn_layout.addWidget(self._sync_btn)

        self._remove_btn = QPushButton(tr("scheduler.remove"))
        self._remove_btn.clicked.connect(self._remove_selected)
        btn_layout.addWidget(self._remove_btn)

        btn_layout.addStretch(1)

        close_btn = QPushButton(tr("scheduler.close"))
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)


        self._list_worker = None
        self._remove_worker = None
        try:
            self._remove_btn.setEnabled(False)
        except Exception:
            pass
        QTimer.singleShot(0, self._load_tasks)


    def _current_container(self) -> dict:
        if self._container_provider is None:
            return {}
        try:
            result = self._container_provider()
            return result if isinstance(result, dict) else {}
        except Exception:
            return {}

    def _current_rzp_path(self):
        try:
            from core.tasks import container_path

            page = getattr(self.parent(), "backup_page", None)
            if page is not None:
                folder = page.tasks_dir()
                if folder:
                    return container_path(folder)
            cfg = getattr(self.parent(), "_cfg", None)
            if cfg is not None:
                folder = getattr(cfg, "tasks_dir", None)
                if folder:
                    return container_path(folder)
        except Exception:
            pass
        return None


    def _load_tasks(self):
        if getattr(self, "_list_worker", None) is not None:


            return
        worker = _TaskListWorker(self)
        self._list_worker = worker
        worker.done.connect(self._apply_tasks, Qt.QueuedConnection)
        worker.finished.connect(self._on_list_finished)
        worker.start()

    def _apply_tasks(self, tasks: list):
        if not self.isVisible():
            return

        container = self._current_container()
        try:
            from core.scheduler import container_task_map
            task_map = container_task_map(container)
        except Exception:
            task_map = {}

        self._table.setRowCount(0)
        for t in tasks:
            row = self._table.rowCount()
            self._table.insertRow(row)
            name = t.get("name", "")
            self._table.setItem(row, 0, QTableWidgetItem(name))
            self._table.setItem(row, 1, QTableWidgetItem(t.get("status", "")))
            self._table.setItem(row, 2, QTableWidgetItem(t.get("next_run", "")))


            entry = task_map.get(name)
            if entry is None:
                link_text = tr("scheduler.link.orphan")
            else:
                work, job = entry
                link_text = tr(
                    "scheduler.link.job",
                    work=str(work.get("title") or ""),
                    job=str(job.get("title") or ""),
                )
            self._table.setItem(row, 3, QTableWidgetItem(link_text))

    def _on_list_finished(self):
        self._list_worker = None
        if not self.isVisible():
            return
        try:
            self._remove_btn.setEnabled(True)
        except Exception:
            pass


    def _remove_selected(self):
        row = self._table.currentRow()
        if row < 0:
            return
        task_name = self._table.item(row, 0).text()
        ans = QMessageBox.question(
            self,
            tr("scheduler.manager_title"),
            tr("scheduler.confirm_remove", name=task_name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return


        if getattr(self, "_remove_worker", None) is not None:
            return
        try:
            self._remove_btn.setEnabled(False)
        except Exception:
            pass

        worker = _TaskRemoveWorker(task_name, self)
        self._remove_worker = worker
        worker.done.connect(self._apply_remove, Qt.QueuedConnection)
        worker.finished.connect(self._on_remove_finished)
        worker.start()

    def _apply_remove(self, task_name: str, ok: bool):
        if not self.isVisible():
            return
        if ok:
            self._load_tasks()
        else:
            QMessageBox.warning(
                self, tr("scheduler.manager_title"),
                tr("scheduler.remove_failed"),
            )

    def _on_remove_finished(self):
        self._remove_worker = None
        if not self.isVisible():
            return
        try:
            self._remove_btn.setEnabled(True)
        except Exception:
            pass


    def _remove_orphans(self):
        container = self._current_container()
        try:
            from core.scheduler import find_orphan_tasks
            orphans = find_orphan_tasks(container)
        except Exception:
            orphans = []

        if not orphans:
            QMessageBox.information(
                self,
                tr("scheduler.orphans_title"),
                tr("scheduler.orphans_empty"),
            )
            return


        names_text = "\n".join("• " + (o.get("name") or "") for o in orphans)
        ans = QMessageBox.question(
            self,
            tr("scheduler.orphans_title"),
            tr("scheduler.orphans_text", count=len(orphans))
            + "\n\n" + names_text,
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return


        try:
            from core.scheduler import remove_scheduled_task_by_name
        except Exception:
            QMessageBox.warning(
                self, tr("scheduler.orphans_title"),
                tr("scheduler.remove_failed"),
            )
            return

        failed = 0
        for o in orphans:
            name = o.get("name")
            if not name:
                continue
            try:
                if not remove_scheduled_task_by_name(name):
                    failed += 1
            except Exception:
                failed += 1

        removed = len(orphans) - failed
        if failed:
            QMessageBox.warning(
                self,
                tr("scheduler.orphans_title"),
                tr("scheduler.orphans_deleted", count=removed)
                + "\n"
                + tr("scheduler.orphans_failed", count=failed),
            )
        else:
            QMessageBox.information(
                self,
                tr("scheduler.orphans_title"),
                tr("scheduler.orphans_deleted", count=removed),
            )


        self._load_tasks()


    def _open_sync_dialog(self):
        from ui.scheduler_sync_dialog import SchedulerSyncDialog

        container = self._current_container()
        rzp_path = self._current_rzp_path()
        if rzp_path is None:
            QMessageBox.warning(
                self,
                tr("scheduler.sync_title"),
                tr("scheduler.sync_no_rzp"),
            )
            return

        dlg = SchedulerSyncDialog(rzp_path, container, parent=self)
        result = dlg.exec()


        _ = result
        self._load_tasks()
