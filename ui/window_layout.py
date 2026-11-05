from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.archive_table import ArchiveTable
from ui.backup_page import BackupPage
from ui.breadcrumb import BreadcrumbBar
from ui.dashboard_page import DashboardPage
from ui.extract_progress import ExtractProgressBar
from ui.i18n import tr
from ui.profile_bar import ProfileBar
from ui.qt_compat import (
    CUSTOM_CONTEXT,
    HEADER_STRETCH,
    HORIZONTAL,
    NO_EDIT,
    SELECT_ROWS,
    VERTICAL,
)
from ui.tree_views import ArchiveTree


LOG_MAX_BLOCKS = 50000


class WindowLayoutMixin:


    def _apply_persisted_geometry(self):
        try:
            if self._cfg.window_maximized:
                self.showMaximized()
            elif self._cfg.window_geometry and len(self._cfg.window_geometry) == 4:
                x, y, w, h = self._cfg.window_geometry
                if w > 0 and h > 0:
                    self.setGeometry(x, y, w, h)
        except Exception:
            pass

    def _create_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)


        try:
            self.profile_bar = ProfileBar(host=self, parent=self)
            layout.addWidget(self.profile_bar)
        except Exception:
            self.profile_bar = None

        self.crumb = BreadcrumbBar()
        layout.addWidget(self.crumb)


        self._main_stack = QStackedWidget()
        self._main_stack.setObjectName("mainStack")


        self._archive_page = QWidget()
        self._archive_page.setObjectName("archivePage")
        archive_lay = QVBoxLayout(self._archive_page)
        archive_lay.setContentsMargins(0, 0, 0, 0)
        archive_lay.setSpacing(0)

        splitter = QSplitter(VERTICAL)

        top = QSplitter(HORIZONTAL)
        self.tree = ArchiveTree()
        self.tree.setHeaderLabel(tr("tree.header"))

        right_col = QWidget()
        right_lay = QVBoxLayout(right_col)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(4)

        self.search_bar = QFrame()
        self.search_bar.setObjectName("searchbar")
        sb_lay = QHBoxLayout(self.search_bar)
        sb_lay.setContentsMargins(2, 4, 2, 2)
        sb_lay.setSpacing(8)

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchedit")
        self.search_edit.setPlaceholderText(tr("search.placeholder"))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        sb_lay.addWidget(self.search_edit, 1)

        self.search_count = QLabel("")
        self.search_count.setObjectName("searchcount")
        sb_lay.addWidget(self.search_count)

        self.search_bar.setVisible(False)
        right_lay.addWidget(self.search_bar)

        self.table = ArchiveTable()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [
                tr("table.header.name"),
                tr("table.header.size"),
                tr("table.header.date"),
                tr("table.header.version"),
                tr("table.header.path"),
            ]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, HEADER_STRETCH)
        header.setSectionResizeMode(4, HEADER_STRETCH)
        header.setStretchLastSection(True)

        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(self._on_right_header_clicked)

        self.table.setSelectionBehavior(SELECT_ROWS)
        self.table.setEditTriggers(NO_EDIT)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setContextMenuPolicy(CUSTOM_CONTEXT)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)
        self.table.doubleClicked.connect(lambda *_: self._on_table_double_click())
        right_lay.addWidget(self.table, 1)

        top.addWidget(self.tree)
        top.addWidget(right_col)
        top.setStretchFactor(0, 1)
        top.setStretchFactor(1, 3)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)


        self.log.document().setMaximumBlockCount(LOG_MAX_BLOCKS)

        splitter.addWidget(top)
        splitter.addWidget(self.log)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        archive_lay.addWidget(splitter)
        self._main_stack.addWidget(self._archive_page)


        try:
            self.backup_page = BackupPage(host=self)
            self._main_stack.addWidget(self.backup_page)
        except Exception:
            self.backup_page = None


        try:
            self.dashboard_page = DashboardPage(host=self)
            self._main_stack.addWidget(self.dashboard_page)
        except Exception:
            self.dashboard_page = None

        layout.addWidget(self._main_stack, 1)


        self.extract_bar = ExtractProgressBar()
        layout.addWidget(self.extract_bar)

        self.statusBar().showMessage(tr("status.ready"))
