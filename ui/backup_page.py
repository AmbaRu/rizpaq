

































































































































































































































from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.tasks import (
    ACTION_TEST,
    CONTAINER_NAME,
    ContainerLockBusy,
    JOB_STATUS_BUSY,
    JOB_STATUS_ERROR,
    JOB_STATUS_OK,
    container_path,
    find_job,
    find_work,
    iter_container_meta,
    load_container,
    remove_job,
    remove_work,
    scheduler_task_name,
    update_container,
)
from ui.config_bridge import _merge_cfg
from ui.i18n import tr
from ui.presentation import format_schedule, format_size
from ui.qt_compat import CUSTOM_CONTEXT, HEADER_STRETCH, NO_EDIT


                                                                
                                                                    
                                                                          
 
                                                                     
                                                                    
_STATUS_TOKENS = {
    JOB_STATUS_OK: "OK_GREEN",
    JOB_STATUS_ERROR: "WARN_ORANGE",
    JOB_STATUS_BUSY: "BUSY_STEEL",
    "never": "TEXT_MUTED_LIGHT",
    "read_error": "DIFF_REMOVED",
}

                                                                        
                                                                         
_COL_NAME = 0
_COL_SCHEDULE = 1
_COL_NEXT_RUN = 2
_COL_LAST_RUN = 3
_COL_STATUS = 4
_COL_SIZE = 5

                
_COL_COUNT = 6

                                                                             
_PAYLOAD_ROLE = Qt.UserRole + 200

                                                                   
                                                                    
                                                                       
                                                          
_WATCH_DELAY_MS = 250


def _status_color(token_name: str) -> QColor:
    pass












    try:
        from ui.skins import color
        return QColor(color(token_name))
    except Exception:
        return QColor(Qt.GlobalColor.gray)


def _job_icon(job: dict) -> str:
    pass












    if str(job.get("action") or "").strip().lower() == ACTION_TEST:
        return "🔍"
    return "⚙"


class _ScheduleWorker(QThread):
    pass




















    done = Signal(dict)                                                       

    def __init__(self, container: dict, parent=None):
        super().__init__(parent)
        self._container = container
        self._cancel = False

    def cancel_request(self):
        pass










        self._cancel = True
        try:
            self.requestInterruption()
        except Exception:
            pass

    def run(self):
        try:
            from core.scheduler import schedule_info_for_container

            info = schedule_info_for_container(self._container)
        except Exception:
            info = {}
                                                                 
                                                                 
                                                                  
                                                                
                                  
        if self._cancel:
            return
        self.done.emit(dict(info or {}))


class BackupPage(QWidget):
    pass











    def __init__(self, host, parent=None):
        super().__init__(parent)
        self._host = host

                                                                      
                                
        self._schedule_worker = None

                                                              
        self._schedule_info: dict = {}

                                                                      
                                                                       
                                                                    
        self._container: dict = {}

                                                                
                                                                  
                                                                
                                                                        
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_watch_trigger)
        self._watcher.directoryChanged.connect(self._on_watch_trigger)

                                                              
                                                                 
                                                            
                                                                
        self._watch_timer = QTimer(self)
        self._watch_timer.setSingleShot(True)
        self._watch_timer.setInterval(_WATCH_DELAY_MS)
        self._watch_timer.timeout.connect(self._on_watch_timeout)

                                                                      
                                                                         
                                                                     
                                                               
        self._last_snapshot = None

        self.setObjectName("backupPage")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._build_top_bar(outer)
        self._build_body(outer)

        self.refresh()

                                                                           

    def _build_top_bar(self, parent_layout):
        pass
        bar = QWidget(self)
        bar.setObjectName("backupTopBar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(8)

        self._path_label = QLabel("", bar)
        self._path_label.setObjectName("backupPathLabel")
        self._path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self._path_label, 1)

        self._refresh_btn = QPushButton(tr("backup.refresh"), bar)
        self._refresh_btn.setAutoDefault(False)
        self._refresh_btn.setDefault(False)
        self._refresh_btn.clicked.connect(self.refresh)
        lay.addWidget(self._refresh_btn)

        parent_layout.addWidget(bar)

    def _build_body(self, parent_layout):
        pass
        self._stack = QStackedWidget(self)
        self._stack.setObjectName("backupStack")

        self._tree = self._build_tree()
        self._stack.addWidget(self._tree)

        self._empty_page = QWidget(self)
        empty_lay = QVBoxLayout(self._empty_page)
        empty_lay.setContentsMargins(24, 24, 24, 24)
        empty_lay.setSpacing(12)
        empty_lay.addStretch(1)

        self._empty_label = QLabel("", self._empty_page)
        self._empty_label.setObjectName("backupEmptyLabel")
        self._empty_label.setWordWrap(True)
        self._empty_label.setAlignment(Qt.AlignCenter)
        empty_lay.addWidget(self._empty_label)

        self._choose_btn = QPushButton(tr("backup.choose_dir"), self._empty_page)
        self._choose_btn.setAutoDefault(False)
        self._choose_btn.setDefault(False)
        self._choose_btn.clicked.connect(self.select_dir)
        empty_lay.addWidget(self._choose_btn, 0, Qt.AlignCenter)

        empty_lay.addStretch(1)
        self._stack.addWidget(self._empty_page)

        parent_layout.addWidget(self._stack, 1)

    def _build_tree(self) -> QTreeWidget:
        pass







        tree = QTreeWidget(self)
        tree.setObjectName("backupTree")
        tree.setColumnCount(_COL_COUNT)
        tree.setHeaderLabels(self._header_labels())

        header = tree.header()
        for col in range(_COL_COUNT):
            header.setSectionResizeMode(col, HEADER_STRETCH)
        header.setStretchLastSection(False)

        tree.setEditTriggers(NO_EDIT)
        tree.setAlternatingRowColors(True)
        tree.setRootIsDecorated(True)
        tree.setIndentation(18)
        tree.setContextMenuPolicy(CUSTOM_CONTEXT)
        tree.customContextMenuRequested.connect(self._on_context_menu)
        tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        return tree

    @staticmethod
    def _header_labels() -> list:
        pass



        return [
            tr("backup.table.name"),
            tr("backup.table.schedule"),
            tr("scheduler.table.next_run"),
            tr("backup.table.last_run"),
            tr("backup.table.status"),
            tr("backup.table.size"),
        ]

    @staticmethod
    def _align_cells(item: QTreeWidgetItem) -> None:
        pass

















        item.setTextAlignment(_COL_NAME, Qt.AlignLeft | Qt.AlignVCenter)
        for col in range(1, _COL_COUNT):
            item.setTextAlignment(col, Qt.AlignCenter)

                                                                         

    def tasks_dir(self):
        pass
        cfg = getattr(self._host, "_cfg", None)
        if cfg is None:
            return None
        try:
            value = getattr(cfg, "tasks_dir", None)
        except Exception:
            return None
        if not value:
            return None
        return str(value)

    def select_dir(self):
        pass
        start = self.tasks_dir() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(
            self, tr("menu.settings.tasks_dir"), start
        )
        if not chosen:
            return
        try:
            if getattr(self._host, "_cfg", None) is not None:
                self._host._cfg.tasks_dir = chosen
        except Exception:
            pass
        try:
            _merge_cfg(tasks_dir=chosen)
        except Exception:
            pass
        try:
            self._host.statusBar().showMessage(
                tr("status.tasks_dir_changed", path=chosen)
            )
        except Exception:
            pass
        self.refresh()

    def retranslate(self) -> None:
        pass






        try:
            self._tree.setHeaderLabels(self._header_labels())
        except Exception:
            pass
        try:
            self._refresh_btn.setText(tr("backup.refresh"))
        except Exception:
            pass
        try:
            self._choose_btn.setText(tr("backup.choose_dir"))
        except Exception:
            pass
        self.refresh()

    def refresh(self):
        pass














        folder = self.tasks_dir()
        self._update_path_label(folder)

        if not folder:
            self._container = {}
            self._schedule_info = {}
            self._fill_tree({})
            self._show_empty_or_tree(False, folder)
        else:
                                                                 
                                                     
            self._container = load_container(container_path(folder))

                                                                              
            self._schedule_info = {}

            has_rows = self._fill_tree(self._container)
            self._show_empty_or_tree(has_rows, folder)

            if has_rows:
                self._load_schedule(self._container)

                                                                   
                                                                      
                                        
        self._update_snapshot()
        self._refresh_watcher()

    def _update_path_label(self, folder):
        if folder:
            self._path_label.setText(tr("backup.path", path=folder))
            self._path_label.setToolTip(folder)
        else:
            self._path_label.setText(tr("backup.no_dir"))
            self._path_label.setToolTip("")

    def _show_empty_or_tree(self, has_rows: bool, folder):
        pass






        if has_rows:
            self._stack.setCurrentWidget(self._tree)
            return
        if folder:
            self._empty_label.setText(tr("backup.empty"))
            self._choose_btn.setVisible(False)
        else:
            self._empty_label.setText(tr("backup.no_dir"))
            self._choose_btn.setVisible(True)
        self._stack.setCurrentWidget(self._empty_page)

    def _fill_tree(self, container: dict) -> bool:
        pass















        self._tree.clear()
        self._tree.setUpdatesEnabled(False)

        rows = iter_container_meta(container)
        if not rows:
            self._tree.setUpdatesEnabled(True)
            return False

                                                                
        work_items: dict = {}

        for row in rows:
            kind = row.get("kind")
            if kind == "work":
                work = row["work"]
                item = self._make_work_item(work, row.get("size"))
                self._tree.addTopLevelItem(item)
                work_items[work.get("id")] = item
            elif kind == "job":
                work = row["work"]
                job = row["job"]
                parent = work_items.get(work.get("id"))
                if parent is None:
                    continue
                child = self._make_job_item(job, row.get("size"),
                                            work_id=work.get("id"))
                parent.addChild(child)

                                                                
                                                             
        if len(work_items) <= 3:
            for item in work_items.values():
                item.setExpanded(True)

        self._tree.setUpdatesEnabled(True)
        return True

    def _make_work_item(self, work: dict, size) -> QTreeWidgetItem:
        pass









        title = str(work.get("title") or "—")
        cells = [f"🗂 {title}"] + [""] * (_COL_COUNT - 1)
        item = QTreeWidgetItem(cells)
        item.setData(_COL_NAME, _PAYLOAD_ROLE,
                     {"kind": "work", "work_id": work.get("id")})

        self._align_cells(item)

                                                                   
        font = item.font(_COL_NAME)
        font.setBold(True)
        item.setFont(_COL_NAME, font)

        if isinstance(size, int):
            item.setText(_COL_SIZE, format_size(size))

        return item

    def _make_job_item(self, job: dict, size, work_id=None) -> QTreeWidgetItem:
        pass















        title = str(job.get("title") or "—")
        schedule_text = format_schedule(job.get("schedule"))
        icon = _job_icon(job)
        cells = [f"{icon} {title}", schedule_text, "…", "", "", ""]
        item = QTreeWidgetItem(cells)
        item.setData(_COL_NAME, _PAYLOAD_ROLE, {
            "kind": "job",
            "job_id": job.get("id"),
            "work_id": str(work_id or ""),
        })

                           
        last = job.get("last_run") or "—"
        item.setText(_COL_LAST_RUN, str(last))

                                
        text, token = self._status_text_and_token(job)
        item.setText(_COL_STATUS, text)
        item.setForeground(_COL_STATUS, _status_color(token))

                                                               
                                                                 
                                                       
        tip = self._status_tooltip(job)
        if tip:
            item.setToolTip(_COL_STATUS, tip)

                                                        
        if isinstance(size, int):
            item.setText(_COL_SIZE, format_size(size))

        self._align_cells(item)

        return item

    @staticmethod
    def _status_text_and_token(job: dict):
        pass













        status = job.get("last_status")
        if status == JOB_STATUS_OK:
            return tr("backup.status.ok"), _STATUS_TOKENS[JOB_STATUS_OK]
        if status == JOB_STATUS_ERROR:
            text = tr("backup.status.error")
            reason = job.get("last_reason")
            if reason:
                                                                  
                                                                      
                                                             
                key = "backup.reason." + str(reason)
                detail = tr(key)
                if detail != key:
                    text += " — " + detail
            return text, _STATUS_TOKENS[JOB_STATUS_ERROR]
        if status == JOB_STATUS_BUSY:
            return tr("backup.status.busy"), _STATUS_TOKENS[JOB_STATUS_BUSY]
        return tr("backup.status.never"), _STATUS_TOKENS["never"]

    @staticmethod
    def _status_tooltip(job: dict) -> str:
        pass













        if job.get("last_status") != JOB_STATUS_ERROR:
            return ""
        reason = job.get("last_reason")
        if not reason:
            return ""
        key = "backup.reason_full." + str(reason)
        full = tr(key)
        if full == key:
            return ""
        tip = full
        last = job.get("last_run")
        if last:
            tip += "\n" + tr("backup.tooltip.last_run", last=str(last))
        return tip

                                                                                     

    def _container_snapshot(self):
        pass







        folder = self.tasks_dir()
        if not folder:
            return None
        p = container_path(folder)
        try:
            st = p.stat()
            return (st.st_mtime_ns, st.st_size)
        except OSError:
                                                                 
                                                
            return None

    def _update_snapshot(self):
        pass
        self._last_snapshot = self._container_snapshot()

    def _refresh_watcher(self):
        pass




















                             
        for p in list(self._watcher.files()):
            try:
                self._watcher.removePath(p)
            except Exception:
                pass
        for p in list(self._watcher.directories()):
            try:
                self._watcher.removePath(p)
            except Exception:
                pass

        folder = self.tasks_dir()
        if not folder:
            return

                         
        try:
            self._watcher.addPath(str(Path(folder)))
        except Exception:
            pass

                                                              
                                    
        p = container_path(folder)
        if p.is_file():
            try:
                self._watcher.addPath(str(p))
            except Exception:
                pass

    def _on_watch_trigger(self, _path: str):
        pass







        self._watch_timer.start()

    def _on_watch_timeout(self):
        pass










        current = self._container_snapshot()
        if current == self._last_snapshot:
            return
        self.refresh()

                                                                                          

    def _load_schedule(self, container: dict):
        pass

























        if self._schedule_worker is not None:
            return
        from core.tasks import iter_jobs

        if not list(iter_jobs(container)):
            self._schedule_info = {}
            return

                                                                      
                                                                 
                                                   
        try:
            worker = _ScheduleWorker(container, self._host)
        except Exception:
            worker = None

        if worker is None:
                                                      
            try:
                from core.scheduler import schedule_info_for_container

                info = schedule_info_for_container(container)
            except Exception:
                info = {}
            self._apply_schedule(dict(info or {}))
            return

                                              
        self._schedule_worker = worker
        worker.done.connect(self._apply_schedule)
        worker.finished.connect(self._on_schedule_finished)

        cleanup = getattr(self._host, "_cleanup_worker", None)
        if callable(cleanup):
            def _on_finished(w=worker):
                try:
                    cleanup(w)
                except Exception:
                    pass
            try:
                worker.finished.connect(_on_finished)
            except Exception:
                pass

        workers_list = getattr(self._host, "_workers", None)
        if isinstance(workers_list, list):
            try:
                workers_list.append(worker)
            except Exception:
                pass

        worker.start()

    def _on_schedule_finished(self):
        self._schedule_worker = None

    def _apply_schedule(self, info: dict):
        pass














        try:
            self._schedule_info = dict(info or {})

            if not self.isVisible():
                return

            self._walk_jobs(
                lambda item, work, job: self._apply_schedule_for_job(item, job)
            )
        except RuntimeError:
                                                 
            pass
        except Exception:
            pass

    def _apply_schedule_for_job(self, item: QTreeWidgetItem, job: dict):
        pass
        job_id = str(job.get("id") or "")
        if not job_id:
            return
        sched = self._schedule_info.get(job_id)

        if sched and sched.get("scheduled") and (sched.get("next_run") or ""):
            self._set_schedule_cell(item, scheduled=True,
                                    next_run=sched.get("next_run") or "",
                                    job_id=job_id)
        else:
            self._set_schedule_cell(item, scheduled=False, next_run="",
                                    job_id=job_id)

    def _set_schedule_cell(self, item: QTreeWidgetItem, scheduled: bool,
                           next_run: str, job_id: str):
        pass






        tree = self._tree

                                                                    
        try:
            tree.setItemWidget(item, _COL_NEXT_RUN, None)
        except Exception:
            pass
        item.setText(_COL_NEXT_RUN, "")

        if scheduled and next_run:
            item.setText(_COL_NEXT_RUN, str(next_run))
            item.setTextAlignment(_COL_NEXT_RUN, Qt.AlignCenter)
            return

                        
        btn = QPushButton(tr("backup.schedule_action"))
                                                                             
                                                                          
        btn.setObjectName("backupScheduleLink")
        btn.setFlat(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setAutoDefault(False)
        btn.setDefault(False)
        btn.clicked.connect(lambda checked=False, jid=job_id: self._schedule_job(jid))

        wrap = QWidget()
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addStretch(1)
        lay.addWidget(btn)
        lay.addStretch(1)

        tree.setItemWidget(item, _COL_NEXT_RUN, wrap)

                                                                            

    def selected_job(self):
        pass














        try:
            if not self.isVisible():
                return None
            if self._stack.currentWidget() is not self._tree:
                return None
        except Exception:
            return None

        item = self._tree.currentItem()
        if item is None:
            return None
        payload = item.data(_COL_NAME, _PAYLOAD_ROLE)
        if not isinstance(payload, dict):
            return None
        if payload.get("kind") != "job":
            return None
        if not payload.get("job_id"):
            return None
        return {
            "work_id": str(payload.get("work_id") or ""),
            "job_id": str(payload["job_id"]),
        }

    def selected_work(self):
        pass







        item = self._tree.currentItem()
        if item is None:
            return None
        payload = item.data(_COL_NAME, _PAYLOAD_ROLE)
        if not isinstance(payload, dict):
            return None
        if payload.get("kind") == "work":
            return str(payload.get("work_id") or "")
        if payload.get("kind") == "job":
                                                               
                                              
            work_id = str(payload.get("work_id") or "")
            if work_id:
                return work_id
                                                       
            parent = item.parent()
            if parent is not None:
                p_payload = parent.data(_COL_NAME, _PAYLOAD_ROLE)
                if isinstance(p_payload, dict):
                    return str(p_payload.get("work_id") or "")
        return None

    def reveal_job(self, work_id: str, job_id: str):
        pass









        try:
            if not self.isVisible():
                return
        except Exception:
            return

        found = []

        def _cb(item, work, job):
            if (str(work.get("id") or "") == str(work_id)
                    and str(job.get("id") or "") == str(job_id)):
                found.append(item)

        self._walk_jobs(_cb)
        if not found:
            return
        item = found[0]
        self._tree.setCurrentItem(item)
        self._tree.scrollToItem(item)
                                                       
        parent = item.parent()
        if parent is not None:
            parent.setExpanded(True)

                                                                        

    def _walk_jobs(self, callback):
        pass
        for i in range(self._tree.topLevelItemCount()):
            work_item = self._tree.topLevelItem(i)
            work_payload = work_item.data(_COL_NAME, _PAYLOAD_ROLE)
            if not isinstance(work_payload, dict):
                continue
            work_id = work_payload.get("work_id")
            if not work_id:
                continue
            for j in range(work_item.childCount()):
                job_item = work_item.child(j)
                job_payload = job_item.data(_COL_NAME, _PAYLOAD_ROLE)
                if not isinstance(job_payload, dict):
                    continue
                job_id = job_payload.get("job_id")
                if not job_id:
                    continue
                found = find_job(self._container, job_id)
                if found is None:
                    continue
                work, job = found
                callback(job_item, work, job)

                                                                           

    def _on_item_double_clicked(self, item: QTreeWidgetItem, _column: int):
        payload = item.data(_COL_NAME, _PAYLOAD_ROLE)
        if not isinstance(payload, dict):
            return
        if payload.get("kind") == "job":
            self._run_job(payload.get("job_id"))

    def _on_context_menu(self, pos):
        pass










        item = self._tree.itemAt(pos)
        if item is None:
            return
        self._tree.setCurrentItem(item)
        payload = item.data(_COL_NAME, _PAYLOAD_ROLE)
        if not isinstance(payload, dict):
            return

        menu = QMenu(self)

        if payload.get("kind") == "work":
            work_id = payload.get("work_id")

                                                                        
                                                                     
                                                  
            act_edit_work = menu.addAction(tr("context.edit_work"))
            act_edit_work.triggered.connect(lambda: self._edit_work(work_id))

            menu.addSeparator()

                                                                   
                                                                    
                                                                      
                          
            act_add_backup = menu.addAction(tr("context.add_backup_job"))
            act_add_backup.triggered.connect(lambda: self._add_job(work_id))

            act_add_check = menu.addAction(tr("context.add_check_job"))
            act_add_check.triggered.connect(lambda: self._add_check_job(work_id))

            act_add_check_par2 = menu.addAction(
                tr("context.add_check_par2_job")
            )
            act_add_check_par2.triggered.connect(
                lambda: self._add_check_par2_job(work_id)
            )

            archive_path = self._archive_path_for_work(work_id)
            act_open = menu.addAction(tr("context.open_archive"))
            act_open.setEnabled(bool(archive_path))
            act_open.triggered.connect(lambda: self._open_archive_for_work(work_id))

                                                                     
                                                                   
                                                          
            par2_path = ""
            if archive_path:
                from core.par2_ops import par2_main_name

                candidate = par2_main_name(archive_path)
                if os.path.isfile(candidate):
                    par2_path = candidate

            if par2_path:
                act_repair = menu.addAction(tr("par2.repair"))
                act_repair.triggered.connect(
                    lambda: self._repair_par2(archive_path)
                )

            menu.addSeparator()
            act_delete = menu.addAction(tr("context.delete_work"))
            act_delete.triggered.connect(lambda: self._delete_work(work_id))

        elif payload.get("kind") == "job":
            job_id = payload.get("job_id")
            work_id = payload.get("work_id")

            act_run = menu.addAction(tr("backup.run"))
            act_run.triggered.connect(lambda: self._run_job(job_id))

            act_edit = menu.addAction(tr("task.edit_menu"))
            act_edit.triggered.connect(lambda: self._edit_job(job_id))

            menu.addSeparator()

            archive_path = self._archive_path_for_work(work_id)
            act_open = menu.addAction(tr("context.open_archive"))
            act_open.setEnabled(bool(archive_path))
            act_open.triggered.connect(lambda: self._open_archive_for_work(work_id))

            act_test = menu.addAction(tr("menu.test.full"))
            act_test.setEnabled(bool(archive_path))
            act_test.triggered.connect(lambda: self._test_archive_for_work(work_id))

            act_test_par2 = menu.addAction(tr("par2.quick_check"))
            act_test_par2.setEnabled(bool(archive_path))
            act_test_par2.triggered.connect(
                lambda: self._test_par2_for_work(work_id)
            )

            menu.addSeparator()

            act_del = menu.addAction(tr("context.delete_job"))
            act_del.triggered.connect(lambda: self._delete_job(job_id))

        else:
            return

        try:
            global_pos = self._tree.viewport().mapToGlobal(pos)
        except Exception:
            global_pos = self._tree.mapToGlobal(pos)
        try:
            menu.exec(global_pos)
        except AttributeError:
            menu.exec_(global_pos)

                                                                                 

    def _archive_path_for_work(self, work_id):
        pass
        work = find_work(self._container, str(work_id or ""))
        if work is None:
            return None
        dest = work.get("dest")
        return str(dest) if dest else None

    def _open_archive_for_work(self, work_id):
        path = self._archive_path_for_work(work_id)
        if not path:
            return
        handler = getattr(self._host, "_enter_archive", None)
        if callable(handler):
            try:
                handler(path)
            except Exception:
                pass

    def _repair_par2(self, archive_path: str):
        pass








        handler = getattr(self._host, "_start_par2_repair", None)
        if callable(handler):
            try:
                handler(archive_path)
            except Exception:
                pass

    def _test_par2_for_work(self, work_id: str):
        pass








        archive_path = self._archive_path_for_work(work_id)
        if not archive_path:
            return
        handler = getattr(self._host, "_start_par2_verify", None)
        if callable(handler):
            try:
                handler(archive_path)
            except Exception:
                pass

    def _run_job(self, job_id):
        if not job_id:
            return
        payload = self.selected_job() or {}
        work_id = payload.get("work_id")
        if not work_id:
            work_id = self.selected_work()
        if not work_id:
            return
        handler = getattr(self._host, "_run_job", None)
        if callable(handler):
            try:
                handler(str(work_id), str(job_id))
            except Exception:
                pass

    def _edit_job(self, job_id):
        work_id = self.selected_work()
        if not work_id or not job_id:
            return
        handler = getattr(self._host, "_edit_job", None)
        if callable(handler):
            try:
                handler(str(work_id), str(job_id))
            except Exception:
                pass

    def _edit_work(self, work_id):
        pass







        if not work_id:
            return
        handler = getattr(self._host, "_edit_work", None)
        if callable(handler):
            try:
                handler(str(work_id))
            except Exception:
                pass

    def _add_job(self, work_id):
        pass
        if not work_id:
            return
        handler = getattr(self._host, "_on_add_job_to_work", None)
        if callable(handler):
            try:
                handler(str(work_id))
            except Exception:
                pass

    def _add_check_job(self, work_id):
        pass







        if not work_id:
            return
        handler = getattr(self._host, "_on_add_check_to_work", None)
        if callable(handler):
            try:
                handler(str(work_id))
            except Exception:
                pass

    def _add_check_par2_job(self, work_id):
        pass





        if not work_id:
            return
        handler = getattr(self._host, "_on_add_check_par2_to_work", None)
        if callable(handler):
            try:
                handler(str(work_id))
            except Exception:
                pass

                                                                                   

    def _launch_background_worker(self, worker) -> bool:
        pass


























        try:
            worker.setParent(self._host)
        except Exception:
            return False

        cleanup = getattr(self._host, "_cleanup_worker", None)
        if callable(cleanup):
            def _on_finished(w=worker):
                try:
                    cleanup(w)
                except Exception:
                    pass
            try:
                worker.finished.connect(_on_finished)
            except Exception:
                pass

        workers_list = getattr(self._host, "_workers", None)
        if isinstance(workers_list, list):
            try:
                workers_list.append(worker)
            except Exception:
                pass

        try:
            worker.start()
        except Exception:
            return False

        return True

                                                                           

    def _show_container_busy(self, path) -> None:
        pass






        handler = getattr(self._host, "_show_container_busy", None)
        if callable(handler):
            try:
                handler(path)
                return
            except Exception:
                pass
        try:
            QMessageBox.information(
                self,
                tr("container.lock_busy_title"),
                tr("container.lock_busy_text", path=str(path)),
            )
        except Exception:
            pass

    def _show_container_save_error(self, path, exc) -> None:
        pass
        handler = getattr(self._host, "_show_container_save_error", None)
        if callable(handler):
            try:
                handler(path, exc)
                return
            except Exception:
                pass
        try:
            QMessageBox.warning(
                self,
                tr("backup.save_error"),
                tr("backup.save_error", error=str(exc)),
            )
        except Exception:
            pass

    def _delete_work(self, work_id):
        pass

























        if not work_id:
            return

        work = find_work(self._container, str(work_id))
        if work is None:
            return

        title = str(work.get("title") or "")

        from ui.qt_compat import YES_BUTTON, YES_NO_BUTTONS
        ans = QMessageBox.question(
            self,
            tr("context.delete_work"),
            tr("backup.confirm_delete_work", name=title),
            YES_NO_BUTTONS,
        )
        if ans != YES_BUTTON:
            return

        folder = self.tasks_dir()
        if not folder:
            return
        path = container_path(folder)

                                                                        
                                                                         
                                                                        
                                                                     
                                                                   
        try:
            task_names = []
            for job in work.get("jobs") or []:
                try:
                    nm = scheduler_task_name(work, job)
                except Exception:
                    nm = ""
                if nm:
                    task_names.append(nm)
        except Exception:
            task_names = []

        def _continue_with_delete():
            pass






            def mutate(container):
                remove_work(container, str(work_id))

            try:
                update_container(path, mutate)
            except ContainerLockBusy:
                self._show_container_busy(path)
                return
            except Exception as exc:
                self._show_container_save_error(path, exc)
                return

            self.refresh()

        if not task_names:
                                                                    
                                                            
            _continue_with_delete()
            return

        try:
            from workers.schedule_worker import ScheduleRemoveWorker

            worker = ScheduleRemoveWorker(task_names)
            worker.done.connect(
                lambda _ok, _failed: _continue_with_delete(),
                Qt.QueuedConnection,
            )
            if not self._launch_background_worker(worker):
                                                                        
                                                                   
                                              
                try:
                    from core.scheduler import remove_scheduled_task_by_name
                    for nm in task_names:
                        try:
                            remove_scheduled_task_by_name(nm)
                        except Exception:
                            pass
                except Exception:
                    pass
                _continue_with_delete()
                return
        except Exception:
                                                                  
                                                                   
            try:
                from core.scheduler import remove_scheduled_task_by_name
                for nm in task_names:
                    try:
                        remove_scheduled_task_by_name(nm)
                    except Exception:
                        pass
            except Exception:
                pass
            _continue_with_delete()

    def _delete_job(self, job_id):
        pass







        if not job_id:
            return

        found = find_job(self._container, str(job_id))
        if found is None:
            return
        work, job = found

        from ui.qt_compat import YES_BUTTON, YES_NO_BUTTONS
        ans = QMessageBox.question(
            self,
            tr("context.delete_job"),
            tr("backup.confirm_delete_job", name=str(job.get("title") or "")),
            YES_NO_BUTTONS,
        )
        if ans != YES_BUTTON:
            return

        folder = self.tasks_dir()
        if not folder:
            return
        path = container_path(folder)

                                                                     
                                                            
                                                                  
                                                                    
        try:
            task_name = scheduler_task_name(work, job)
        except Exception:
            task_name = ""

        def _continue_with_remove():
            def mutate(container):
                remove_job(container, str(job_id))

            try:
                update_container(path, mutate)
            except ContainerLockBusy:
                self._show_container_busy(path)
                return
            except Exception as exc:
                self._show_container_save_error(path, exc)
                return

            self.refresh()

        if not task_name:
            _continue_with_remove()
            return

        try:
            from workers.schedule_worker import ScheduleRemoveWorker

            worker = ScheduleRemoveWorker([task_name])
            worker.done.connect(
                lambda _ok, _failed: _continue_with_remove(),
                Qt.QueuedConnection,
            )
            if not self._launch_background_worker(worker):
                                                                      
                           
                try:
                    from core.scheduler import remove_scheduled_task_by_name
                    try:
                        remove_scheduled_task_by_name(task_name)
                    except Exception:
                        pass
                except Exception:
                    pass
                _continue_with_remove()
                return
        except Exception:
            try:
                from core.scheduler import remove_scheduled_task_by_name
                try:
                    remove_scheduled_task_by_name(task_name)
                except Exception:
                    pass
            except Exception:
                pass
            _continue_with_remove()

                                                                               

    def _schedule_job(self, job_id: str):
        pass

























        if not job_id:
            return

        found = find_job(self._container, str(job_id))
        if found is None:
            return
        work, job = found

        from PySide6.QtWidgets import QDialog
        from ui.scheduler_dialog import ScheduleDialog

        dlg = ScheduleDialog(self, initial_schedule=job.get("schedule"))
        if dlg.exec() != QDialog.Accepted:
            return
        schedule = dlg.result_schedule()
        if schedule is None:
            return

        folder = self.tasks_dir()
        if not folder:
            return
        path = container_path(folder)

                                                                         
                                                                        
                                                  
        result = {"work": None, "job": None}

        def mutate(container):
            from core.tasks import update_job as _update_job
            _update_job(container, str(job_id), schedule=schedule)
            work_after = find_work(container, str(work.get("id") or ""))
            found_after = find_job(container, str(job_id))
            if work_after is not None and found_after is not None:
                result["work"] = work_after
                result["job"] = found_after[1]

        try:
            update_container(path, mutate)
        except ContainerLockBusy:
            self._show_container_busy(path)
            return
        except Exception as exc:
            self._show_container_save_error(path, exc)
            return

                                                                          
        work_now = result["work"] or work
        job_now = result["job"] or job

                                                               
        job_name = str(job_now.get("title") or "")

        try:
            from workers.schedule_worker import ScheduleCreateWorker

            worker = ScheduleCreateWorker(path, work_now, job_now, schedule)
            worker.done.connect(
                lambda ok, err, s=schedule, n=job_name:
                    self._on_schedule_create_done(ok, err, s, n),
                Qt.QueuedConnection,
            )
            if not self._launch_background_worker(worker):
                                                                   
                                                           
                try:
                    from core.scheduler import create_scheduled_task
                    ok = bool(create_scheduled_task(
                        path, work_now, job_now, schedule
                    ))
                    self._on_schedule_create_done(ok, "", schedule, job_name)
                except Exception as exc:
                    self._on_schedule_create_done(
                        False, str(exc), schedule, job_name
                    )
        except Exception as exc:
            self._on_schedule_create_done(
                False, str(exc), schedule, job_name
            )

        self.refresh()

    def _on_schedule_create_done(
        self, ok: bool, err: str, schedule, name: str
    ):
        pass



















        if not schedule or not schedule.get("enabled"):
            return

        try:
            if ok:
                self._host.statusBar().showMessage(
                    tr("scheduler.scheduled_ok", path=CONTAINER_NAME)
                )
                return
        except Exception:
            pass

        try:
            text = tr("scheduler.scheduled_failed")
            if err:
                text = text + "\n\n" + err
            QMessageBox.warning(self, tr("scheduler.title"), text)
        except Exception:
            pass
