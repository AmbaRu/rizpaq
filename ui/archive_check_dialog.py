
























































from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from ui.i18n import tr
from ui.test_modes import combo_entries as test_mode_combo_entries


class ArchiveCheckDialog(QDialog):
    pass

    def __init__(
        self,
        work: dict,
        parent=None,
        initial_settings=None,
        edit_work_id=None,
        edit_job_id=None,
        add_to_work_id=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("check.dialog_title"))
        self.setMinimumWidth(520)

        self._work = dict(work or {})
        self._result = None
        self._schedule = None

        self._edit_work_id = edit_work_id
        self._edit_job_id = edit_job_id
        self._add_to_work_id = add_to_work_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

                                                         
        info = QFormLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(6)

        dest = str(self._work.get("dest") or "")
        dest_label = QLabel(dest or tr("check.dest_missing"))
        dest_label.setWordWrap(True)
        info.addRow(tr("check.archive"), dest_label)

                                                                    
                                                                      
                                                
        pw_set = bool(self._work.get("password_b64"))
        pw_label = QLabel(
            tr("check.password_set") if pw_set else tr("check.password_not_set")
        )
        info.addRow(tr("check.password"), pw_label)

        layout.addLayout(info)

                                       
        form = QFormLayout()
        form.setContentsMargins(0, 8, 0, 0)
        form.setSpacing(8)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText(tr("check.title_placeholder"))
        form.addRow(tr("check.title"), self._title_edit)

        self._mode_combo = QComboBox()
                                                                     
                                                                   
                                         
         
                                                                     
                                                              
        for mode, label in test_mode_combo_entries():
            self._mode_combo.addItem(label, mode)
        form.addRow(tr("check.mode"), self._mode_combo)

        hint = QLabel(tr("check.mode_hint"))
        hint.setWordWrap(True)
                                                                  
                                                                
                           
        hint.setObjectName("schedHint")
        form.addRow("", hint)

        self._log_combo = QComboBox()
        self._log_combo.addItem(tr("check.log_short"), "short")
        self._log_combo.addItem(tr("check.log_full"), "full")
        self._log_combo.addItem(tr("check.log_none"), "none")
        form.addRow(tr("check.log_mode"), self._log_combo)

        layout.addLayout(form)

        layout.addStretch(1)

                        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        for std in (QDialogButtonBox.Ok, QDialogButtonBox.Cancel):
            b = buttons.button(std)
            if b:
                b.setAutoDefault(False)
                b.setDefault(False)

        btn_sched = QPushButton("📅 " + tr("scheduler.schedule_button"))
        btn_sched.setAutoDefault(False)
        btn_sched.setDefault(False)
        btn_sched.clicked.connect(self._on_schedule)
        buttons.addButton(btn_sched, QDialogButtonBox.ActionRole)

                                                                
                                                           
                                                        
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if initial_settings:
            self._apply_settings(initial_settings)

                         

    def _apply_settings(self, s: dict):
        pass
        title = str(s.get("title") or "").strip()
        if title:
            self._title_edit.setText(title)

        mode = str(s.get("test_mode") or "full")
        for i in range(self._mode_combo.count()):
            if self._mode_combo.itemData(i) == mode:
                self._mode_combo.setCurrentIndex(i)
                break

        log_mode = str(s.get("task_log_mode") or "short")
        for i in range(self._log_combo.count()):
            if self._log_combo.itemData(i) == log_mode:
                self._log_combo.setCurrentIndex(i)
                break

        self._schedule = s.get("schedule")

    def _collect_settings(self) -> dict:
        pass
















        s = {
            "action": "test",
            "test_mode": self._mode_combo.currentData() or "full",
            "title": self._title_edit.text().strip(),
            "sources": list(self._work.get("sources") or []),
            "dest": self._work.get("dest") or "",
            "only_masks": list(self._work.get("only_masks") or []),
            "not_masks": list(self._work.get("not_masks") or []),
            "comment": self._work.get("comment") or "",
            "task_log_mode": self._log_combo.currentData() or "short",
        }
        if self._schedule:
            s["schedule"] = self._schedule
        return s

                        

    def _validate_settings(self, s: dict) -> bool:
        pass







        if not s.get("dest"):
            QMessageBox.warning(
                self,
                tr("check.dialog_title"),
                tr("check.dest_missing"),
            )
            return False
        return True

                                     

    def _save(self, settings: dict) -> bool:
        pass





        host = self.parent()
        try:
            if self._edit_work_id and self._edit_job_id:
                handler = getattr(host, "_save_edited_job", None)
                if not callable(handler):
                    QMessageBox.warning(
                        self, tr("task.save_title"),
                        tr("task.save_error", error="host method not found"),
                    )
                    return False
                return bool(
                    handler(settings, self._edit_work_id, self._edit_job_id)
                )

            if self._add_to_work_id:
                handler = getattr(host, "_save_new_job", None)
                if not callable(handler):
                    QMessageBox.warning(
                        self, tr("task.save_title"),
                        tr("task.save_error", error="host method not found"),
                    )
                    return False
                return bool(handler(settings, work_id=self._add_to_work_id))

            QMessageBox.warning(
                self, tr("task.save_title"),
                tr("task.save_error", error="no save context"),
            )
            return False
        except Exception as exc:
            QMessageBox.warning(
                self, tr("task.save_title"),
                tr("task.save_error", error=str(exc)),
            )
            return False

    def _on_accept(self):
        pass
        settings = self._collect_settings()
        if not self._validate_settings(settings):
            return
        if self._save(settings):
            self._result = settings
            self.accept()

    def _on_schedule(self):
        pass






        settings = self._collect_settings()
        if not self._validate_settings(settings):
            return

        from ui.scheduler_dialog import ScheduleDialog

        dlg = ScheduleDialog(self, initial_schedule=self._schedule)
        if dlg.exec() != QDialog.Accepted:
            return
        schedule = dlg.result_schedule()
        if not schedule:
            return

        settings["schedule"] = schedule
        self._schedule = schedule

        if self._save(settings):
            self._result = settings
            self.accept()

    def result_settings(self):
        pass







        return self._result
