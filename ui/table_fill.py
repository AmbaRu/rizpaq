from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTableWidgetItem

from core.archive_ops import slice_at_version
from core.search import match_query as _match_query
from ui.i18n import tr
from ui.qt_compat import (
    ASCENDING_ORDER,
    DATE_RAW_ROLE,
    DESCENDING_ORDER,
    K_ARC_DIR,
    K_ARC_FILE,
    K_FS_ARC,
    K_FS_DIR,
    K_FS_FILE,
    K_FS_UNI_ARC,
    K_UP,
    KIND_ROLE,
    NAME_SORT_ROLE,
    SIZE_RAW_ROLE,
    USER_ROLE,
    VERSION_RAW_ROLE,
)
from ui.presentation import format_size


from ui.skins import color as skin_color

_MAX_SEARCH_ROWS = 2000


UNI_EXTS = (".zip", ".7z", ".rar")


def _safe_format(value: object) -> str:
    return str(value).replace("{", "{{").replace("}", "}}")


def _strip_emoji_prefix(name: str) -> str:

    for prefix in ("📂 ", "📄 ", "🗜 "):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


class TableFillMixin:


    def _is_latest_only(self) -> bool:

        try:
            if self.latest_only_action is not None:
                return bool(self.latest_only_action.isChecked())
        except Exception:
            pass
        return False


    def _set_row(self, kind, name, size, date, version, path, payload,
                 bold=False, color=None,
                 size_raw=None, date_raw=None, version_raw=None):
        row = self.table.rowCount()
        self.table.insertRow(row)


        n = QTableWidgetItem(name)
        if bold:
            n.setFont(self._bold_font)
        if color is not None:
            n.setForeground(color)
        n.setData(USER_ROLE, payload)
        n.setData(KIND_ROLE, kind)
        n.setData(NAME_SORT_ROLE, _strip_emoji_prefix(name))
        self.table.setItem(row, 0, n)


        size_item = QTableWidgetItem(size)
        if size_raw is not None:
            size_item.setData(SIZE_RAW_ROLE, size_raw)
        self.table.setItem(row, 1, size_item)


        date_item = QTableWidgetItem(date)
        if date_raw is not None:
            date_item.setData(DATE_RAW_ROLE, date_raw)
        self.table.setItem(row, 2, date_item)


        version_item = QTableWidgetItem(version)
        if version_raw is not None:
            version_item.setData(VERSION_RAW_ROLE, version_raw)
        self.table.setItem(row, 3, version_item)


        self.table.setItem(row, 4, QTableWidgetItem(path))

    def _populate_right_fs(self):
        self.table.setRowCount(0)
        path = self.fs_path
        if path is None or not path.is_dir():
            self._set_row(K_UP, "⬆ ..", "", "", "", "", None)
            self._set_row(
                K_FS_FILE,
                tr("table.folder_unavailable"),
                "", "", "",
                str(path),
                None,
            )
            self._apply_current_sort()
            return

        is_root = (path == path.parent)
        if not is_root:
            up = QTableWidgetItem("⬆ ..")


            up.setForeground(QColor(skin_color("TEXT_MUTED_LIGHT")))
            up.setData(USER_ROLE, None)
            up.setData(KIND_ROLE, K_UP)
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, up)
            for c in range(1, 5):
                self.table.setItem(row, c, QTableWidgetItem(""))

        dirs, files = [], []
        try:
            with os.scandir(path) as it:
                for e in it:
                    try:
                        if e.is_dir():
                            dirs.append((e.name, e.path))
                        else:
                            st = e.stat()
                            files.append((e.name, e.path, st.st_size, st.st_mtime))
                    except OSError:
                        continue
        except OSError as exc:
            self._set_row(
                K_FS_FILE,
                tr("table.read_error", error=_safe_format(exc)),
                "", "", "",
                str(path),
                None,
            )
            self._apply_current_sort()
            return

        dirs.sort(key=lambda x: os.path.normcase(x[0]))
        files.sort(key=lambda x: os.path.normcase(x[0]))

        for name, full in dirs:
            self._set_row(K_FS_DIR, f"📂 {name}", "", "", "", full, full, bold=True)


        arc_color = QColor(skin_color("ARC_BLUE"))
        for name, full, size, mtime in files:
            dt = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            name_low = name.lower()
            if name_low.endswith(".zpaq"):
                self._set_row(
                    K_FS_ARC,
                    f"🗜 {name}",
                    format_size(size),
                    dt,
                    "",
                    full,
                    full,
                    color=arc_color,
                    size_raw=size,
                    date_raw=dt,
                )
            elif name_low.endswith(UNI_EXTS):
                self._set_row(
                    K_FS_UNI_ARC,
                    f"🗜 {name}",
                    format_size(size),
                    dt,
                    "",
                    full,
                    full,
                    color=arc_color,
                    size_raw=size,
                    date_raw=dt,
                )
            else:
                self._set_row(
                    K_FS_FILE,
                    f"📄 {name}",
                    format_size(size),
                    dt,
                    "",
                    full,
                    full,
                    size_raw=size,
                    date_raw=dt,
                )

        self._apply_current_sort()

    def _populate_right_archive(self):
        self.table.setRowCount(0)
        inner = self.archive_inner or ""
        prefix = inner + "/" if inner else ""
        query = (self._search_query or "").strip()

        if self.version_slice is not None:
            base = slice_at_version(self.entries, self.version_slice)
        else:
            base = self.entries

        if query:
            files = [e for e in base if not e.is_dir and e.flag != "-"]
            if self._is_latest_only():
                latest = {}
                for e in files:
                    old = latest.get(e.path)
                    if old is None or (e.version or 0, e.datetime) > (old.version or 0, old.datetime):
                        latest[e.path] = e
                files = list(latest.values())

            total = len(files)
            matched = [e for e in files if _match_query(query, e.path)]
            n_match = len(matched)
            shown = matched[:_MAX_SEARCH_ROWS]

            for entry in sorted(shown, key=lambda x: (x.path.lower(), x.version or 0)):
                self._set_row(
                    K_ARC_FILE,
                    entry.name,
                    format_size(entry.size),
                    entry.datetime,
                    str(entry.version) if entry.version is not None else "",
                    entry.path,
                    entry,
                    size_raw=entry.size,
                    date_raw=entry.datetime,
                    version_raw=entry.version,
                )

            if n_match == 0:
                self._set_row(
                    K_FS_FILE,
                    tr("table.not_found", query=_safe_format(query)),
                    "", "", "", "",
                    None,
                )
            elif n_match > _MAX_SEARCH_ROWS:
                self._set_row(
                    K_FS_FILE,
                    tr("table.truncated", max=_MAX_SEARCH_ROWS, count=n_match),
                    "", "", "", "",
                    None,
                )

            if n_match > _MAX_SEARCH_ROWS:
                self.search_count.setText(
                    tr("search.count_shown_of", found=n_match, shown=_MAX_SEARCH_ROWS)
                )
            else:
                self.search_count.setText(
                    tr("search.count_found_of", found=n_match, total=total)
                )

            self._apply_current_sort()
            return

        self.search_count.setText("")

        up = QTableWidgetItem("⬆ ..")


        up.setForeground(QColor(skin_color("TEXT_MUTED_LIGHT")))
        up.setData(USER_ROLE, None)
        up.setData(KIND_ROLE, K_UP)
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, up)
        for c in range(1, 5):
            self.table.setItem(row, c, QTableWidgetItem(""))

        folders = {}
        file_entries = []
        for entry in base:
            if not entry.path.startswith(prefix):
                continue
            rest = entry.path[len(prefix):]
            if not rest:
                continue
            parts = rest.split("/")
            if len(parts) > 1 or entry.is_dir:
                folder_name = parts[0]
                folders[prefix + folder_name] = folder_name
            if not entry.is_dir and len(parts) == 1 and entry.flag != "-":
                file_entries.append(entry)

        if self._is_latest_only():
            latest2 = {}
            for entry in file_entries:
                old = latest2.get(entry.path)
                if old is None:
                    latest2[entry.path] = entry
                    continue
                if (entry.version or 0, entry.datetime) > (old.version or 0, old.datetime):
                    latest2[entry.path] = entry
            file_entries = list(latest2.values())

        for folder_path, folder_name in sorted(folders.items(), key=lambda x: x[1].lower()):
            self._set_row(K_ARC_DIR, f"📂 {folder_name}", "", "", "", folder_path, folder_path, bold=True)

        for entry in sorted(file_entries, key=lambda x: (x.path.lower(), x.version or 0, x.datetime)):
            self._set_row(
                K_ARC_FILE,
                f"📄 {entry.name}",
                format_size(entry.size),
                entry.datetime,
                str(entry.version) if entry.version is not None else "",
                entry.path,
                entry,
                size_raw=entry.size,
                date_raw=entry.datetime,
                version_raw=entry.version,
            )

        self._apply_current_sort()


    def _on_search_text_changed(self, _text):
        self._search_timer.start()

    def _apply_search(self):
        if self.mode != "archive" and self.mode != "universal":
            return
        self._search_query = self.search_edit.text()
        self._populate_right_archive()

    def _clear_search(self):
        self.search_edit.clear()

    def _focus_search(self):
        if self.mode != "archive" and self.mode != "universal":
            self.statusBar().showMessage(tr("status.search_only_archive"))
            return
        self.search_edit.setFocus()
        self.search_edit.selectAll()


    def _on_right_header_clicked(self, column: int):

        if column < 0 or column > 4:
            return

        if self._right_sort_column == column:

            self._right_sort_desc = not self._right_sort_desc
        else:

            self._right_sort_column = column
            self._right_sort_desc = False

        self._sort_right_table()


        order = DESCENDING_ORDER if self._right_sort_desc else ASCENDING_ORDER
        self.table.horizontalHeader().setSortIndicator(column, order)

    def _apply_current_sort(self):

        if self._right_sort_column is None:

            self._right_sort_column = 0
            self._right_sort_desc = False

        self._sort_right_table()


        order = DESCENDING_ORDER if self._right_sort_desc else ASCENDING_ORDER
        header = self.table.horizontalHeader()
        header.setSortIndicator(self._right_sort_column, order)
        header.setSortIndicatorShown(True)

    def _sort_right_table(self):

        table = self.table
        row_count = table.rowCount()
        if row_count <= 1:
            return


        selected_payloads = []
        for row in range(row_count):
            item = table.item(row, 0)
            if item and item.isSelected():
                payload = item.data(USER_ROLE)
                if payload is not None:
                    selected_payloads.append(payload)


        up_items = None
        data_rows = []
        for row in range(row_count):
            kind = None
            item0 = table.item(row, 0)
            if item0:
                kind = item0.data(KIND_ROLE)
            if kind == K_UP:
                up_items = [table.takeItem(row, c) for c in range(5)]
            else:
                items = [table.takeItem(row, c) for c in range(5)]
                data_rows.append(items)


        groups = {}
        for items in data_rows:
            kind = items[0].data(KIND_ROLE) if items[0] else None
            priority = self._kind_group_priority(kind)
            groups.setdefault(priority, []).append(items)


        col = self._right_sort_column
        desc = self._right_sort_desc
        sorted_rows = []
        for priority in sorted(groups.keys()):
            group = groups[priority]
            sorted_group = self._sort_group(group, col, desc)
            sorted_rows.extend(sorted_group)


        table.setUpdatesEnabled(False)
        table.setRowCount(0)


        if up_items is not None:
            row = table.rowCount()
            table.insertRow(row)
            for c in range(5):
                table.setItem(row, c, up_items[c])


        for items in sorted_rows:
            row = table.rowCount()
            table.insertRow(row)
            for c in range(5):
                table.setItem(row, c, items[c])

        table.setUpdatesEnabled(True)


        if selected_payloads:
            for row in range(table.rowCount()):
                item = table.item(row, 0)
                if item:
                    payload = item.data(USER_ROLE)
                    if payload is not None and payload in selected_payloads:
                        table.selectRow(row)

    def _kind_group_priority(self, kind) -> int:

        if kind == K_UP:
            return 0
        elif kind in (K_FS_DIR, K_ARC_DIR):
            return 1
        elif kind in (K_FS_ARC, K_FS_UNI_ARC):
            return 2
        else:
            return 3

    def _sort_group(self, items_list, column: int, desc: bool):
        non_empty = []
        empty = []
        for items in items_list:
            if self._is_empty_sort_value(items, column):
                empty.append(items)
            else:
                non_empty.append(items)

        non_empty.sort(key=lambda items: self._sort_key(items, column), reverse=desc)
        return non_empty + empty

    def _is_empty_sort_value(self, items, column: int) -> bool:

        if column == 0:
            return False
        elif column == 1:
            item = items[1]
            if item:
                return item.data(SIZE_RAW_ROLE) is None
            return True
        elif column == 2:
            item = items[2]
            if item:
                return item.data(DATE_RAW_ROLE) is None
            return True
        elif column == 3:
            item = items[3]
            if item:
                return item.data(VERSION_RAW_ROLE) is None
            return True
        elif column == 4:
            item = items[4]
            if item:
                return not item.text().strip()
            return True
        return True

    def _sort_key(self, items, column: int):

        if column == 0:

            item = items[0]
            if item:
                name = item.data(NAME_SORT_ROLE)
                if name is None:
                    name = _strip_emoji_prefix(item.text())
                return name.casefold()
            return ""
        elif column == 1:

            item = items[1]
            if item:
                raw = item.data(SIZE_RAW_ROLE)
                if raw is not None:
                    return raw
            return -1
        elif column == 2:

            item = items[2]
            if item:
                raw = item.data(DATE_RAW_ROLE)
                if raw is not None:
                    return raw
            return ""
        elif column == 3:

            item = items[3]
            if item:
                raw = item.data(VERSION_RAW_ROLE)
                if raw is not None:
                    return raw
            return -1
        elif column == 4:

            item = items[4]
            if item:
                return item.text().casefold()
            return ""
        return ""
