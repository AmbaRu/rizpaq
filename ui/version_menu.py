from __future__ import annotations

from PySide6.QtGui import QAction, QActionGroup
from ui.diff_dialog import DiffDialog
from ui.i18n import tr


class VersionMenuMixin:


    def _set_archive_dependent_actions(self, enabled: bool) -> None:

        for attr in (
            "compare_action",
            "archive_info_action",
            "search_action",
            "_versions_menu",
            "_test_menu",
            "_unpack_menu",
        ):
            try:
                widget = getattr(self, attr, None)
                if widget is not None:
                    widget.setEnabled(enabled)
            except Exception:
                pass

    def _rebuild_versions_menu(self) -> None:
        menu = self._versions_menu

        if menu is None:
            return
        menu.clear()


        old_group = getattr(self, "_ver_group", None)
        if old_group is not None:
            try:
                old_group.deleteLater()
            except Exception:
                pass
        self._ver_group = None

        has_zpaq_archive = self.mode == "archive" and self.archive_path is not None
        is_universal = self.mode == "universal" and self.archive_path is not None


        self._set_archive_dependent_actions(has_zpaq_archive)


        try:
            if hasattr(self, "convert_action") and self.convert_action is not None:
                self.convert_action.setEnabled(is_universal)
        except Exception:
            pass

        if not has_zpaq_archive or not self.versions:
            menu.setEnabled(False)
            return

        menu.setEnabled(True)

        grp = QActionGroup(self)
        grp.setExclusive(True)
        self._ver_group = grp

        act_all = menu.addAction(tr("status.version_all"))
        act_all.setCheckable(True)
        act_all.setData(None)
        grp.addAction(act_all)
        act_all.triggered.connect(self._on_version_menu_triggered)

        menu.addSeparator()

        for v in sorted(self.versions, key=lambda x: x.number):
            label = f"v{v.number} · {v.date}"
            if getattr(v, "time", ""):
                label += f" {v.time}"
            comment = (getattr(v, "comment", "") or "").strip()
            if comment:
                label += f" · {comment[:40]}"
            a = menu.addAction(label)
            a.setCheckable(True)
            a.setData(v.number)
            grp.addAction(a)
            a.triggered.connect(self._on_version_menu_triggered)
            if self.version_slice == v.number:
                a.setChecked(True)

        if self.version_slice is None:
            act_all.setChecked(True)

    def _on_version_menu_triggered(self) -> None:
        act = self.sender()
        if not isinstance(act, QAction):
            return
        self._on_version_slice(act.data())

    def _on_version_slice(self, n):
        self.version_slice = n
        self._populate_right_archive()
        if n is None:
            self.statusBar().showMessage(tr("status.version_all"))
        else:
            self.statusBar().showMessage(tr("status.version_slice", version=n))

    def _on_compare_versions(self):
        if self.mode != "archive" or self.archive_path is None:
            self.statusBar().showMessage(tr("status.compare_only_archive"))
            return
        if not self.entries:
            self.statusBar().showMessage(tr("status.compare_list_not_loaded"))
            return
        if len(self.versions) < 2:
            self.statusBar().showMessage(tr("status.compare_need_two_versions"))
            return
        dlg = DiffDialog(self.entries, self.versions, parent=self)
        dlg.exec()
