








from __future__ import annotations


class DragDropMixin:
    pass

    def _setup_drag_drop(self):
        pass
        try:
            self.setAcceptDrops(True)
        except Exception:
            pass

    def dragEnterEvent(self, event):
        try:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
                return
        except Exception:
            pass
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        try:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
                return
        except Exception:
            pass
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        try:
            urls = event.mimeData().urls()
            paths = []
            for url in urls:
                try:
                    if url.isLocalFile():
                        p = url.toLocalFile()
                        if p:
                            paths.append(p)
                except Exception:
                    continue
            if paths:
                event.acceptProposedAction()
                self._on_create_archive_paths(paths)
                return
        except Exception:
            pass
        super().dropEvent(event)
