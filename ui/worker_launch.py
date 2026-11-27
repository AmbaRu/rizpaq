

















from __future__ import annotations

from pathlib import Path

from ui.i18n import tr
from workers import (
    ExtractFileWorker,
    ExtractFolderBatchWorker,
    ExtractFolderWorker,
    ExtractSalvageWorker,
    ExtractRevisionWorker,
)


class WorkerLaunchMixin:
    pass

                                                                          
    def _can_start_extract(self) -> bool:
        pass






        check = getattr(self, "_ensure_extract_password", None)
        if not callable(check):
            return True
        try:
            return bool(check())
        except Exception:
                                                                  
                                                                   
                                                          
            return True

    def _connect_extract_stream(self, worker) -> None:
        pass




        try:
            worker.progress_info.connect(self._ui_extract_info)
        except Exception:
            pass

        try:
            worker.line_received.connect(self._ui_extract_output)
        except Exception:
            pass

                                                                          
    def _start_extract_file_worker(self, entry, dest: str, open_after: bool = False):
        if not self.archive_path or not self._can_start_extract():
            return

        worker = ExtractFileWorker(
            self.zpaq_bin,
            self.archive_path,
            self.password,
            entry.path,
            entry.version,
            dest,
        )

        def retry():
                                                                   
                                                   
                                                                     
                                                                      
                                  
            if open_after:
                try:
                    Path(dest).parent.mkdir(parents=True, exist_ok=True)
                except OSError:
                    pass
            self._start_extract_file_worker(entry, dest, open_after)

        name = getattr(entry, "name", "") or Path(entry.path).name

                                                                    
                                                                  
                                                            
        worker.worker_started.connect(lambda n=name: self._ui_file_started(n))
        worker.percent.connect(self._ui_folder_percent)

        self._connect_extract_stream(worker)

                                                                       
                              
        if open_after:
            worker.done.connect(
                lambda r, d=str(dest): self._open_extracted_if_ok(r, d)
            )

        worker.done.connect(
            lambda r, cb=retry: self._on_extract_done(r, cb)
        )
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))

        self._workers.append(worker)
        worker.start()

    def _start_extract_folder_worker(self, tasks: list, dest_folder: Path):
        if not self.archive_path or not self._can_start_extract():
            return

        worker = ExtractFolderWorker(
            self.zpaq_bin,
            self.archive_path,
            self.password,
            tasks,
            dest_folder,
        )

        retry = lambda: self._start_extract_folder_worker(              
            tasks, dest_folder
        )

        worker.worker_started.connect(self._ui_folder_started)
        worker.tick.connect(self._ui_folder_tick)
        worker.done.connect(
            lambda r, cb=retry: self._on_extract_done(r, cb)
        )
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))

        self._workers.append(worker)
        worker.start()

    def _start_extract_folder_batch_worker(
        self,
        inner_prefix: str,
        version,
        dest_folder: str,
    ):
        if not self.archive_path or not self._can_start_extract():
            return

        worker = ExtractFolderBatchWorker(
            self.zpaq_bin,
            self.archive_path,
            self.password,
            inner_prefix,
            version,
            dest_folder,
        )

        retry = lambda: self._start_extract_folder_batch_worker(              
            inner_prefix, version, dest_folder
        )

        worker.worker_started.connect(self._ui_folder_batch_started)
        worker.percent.connect(self._ui_folder_percent)

        self._connect_extract_stream(worker)

        worker.done.connect(
            lambda r, cb=retry: self._on_extract_done(r, cb)
        )
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))

        self._workers.append(worker)
        worker.start()

    def _start_extract_revision_worker(
        self, mode: str, until: str, dest_folder: str
    ):
        pass






        if not self.archive_path or not self._can_start_extract():
            return

        worker = ExtractRevisionWorker(
            self.zpaq_bin,
            self.archive_path,
            self.password,
            mode,
            until,
            dest_folder,
        )

        retry = lambda: self._start_extract_revision_worker(              
            mode, until, dest_folder
        )

        worker.worker_started.connect(self._ui_folder_batch_started)
        worker.percent.connect(self._ui_folder_percent)
        self._connect_extract_stream(worker)

        worker.done.connect(
            lambda r, cb=retry: self._on_extract_done(r, cb)
        )
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))

        self._workers.append(worker)
        worker.start()

    def _start_salvage_worker(self, dest_folder: str, ram_gb):
        pass






        if not self.archive_path or not self._can_start_extract():
            return

        worker = ExtractSalvageWorker(
            self.zpaq_bin,
            self.archive_path,
            self.password,
            dest_folder,
            ram_gb,
        )

        retry = lambda: self._start_salvage_worker(              
            dest_folder, ram_gb
        )

        worker.worker_started.connect(self._ui_folder_batch_started)
        worker.percent.connect(self._ui_folder_percent)

        self._connect_extract_stream(worker)

        worker.done.connect(
            lambda r, cb=retry: self._on_salvage_done(r, cb)
        )
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))

        self._workers.append(worker)
        worker.start()

                                                                          
    def _cleanup_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)

                                                                         
    def _cancel_long_operations(self):
        pass













        cancelled_any = False

        for worker in list(self._workers):
            cancel = getattr(worker, "cancel_request", None)
            if not callable(cancel):
                continue

            try:
                cancel()
                cancelled_any = True
            except Exception:
                pass

        try:
            if cancelled_any:
                self.statusBar().showMessage(tr("status.cancel_requested"))
            else:
                self.statusBar().showMessage(tr("status.cancel_none"))
        except Exception:
            pass