from __future__ import annotations

import os
import tempfile
from string import Template

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPalette, QImage, QPainter, QPolygon

from ui import skins
from ui.skins import color


def build_palette(colors: dict) -> QPalette:

    P = QPalette
    pal = QPalette()

    def _set(role, name: str):
        pal.setColor(role, QColor(colors[name]))

    _set(P.Window,          "WINDOW_BG")
    _set(P.WindowText,          "TEXT_WINDOW")
    _set(P.Base,          "BASE_BG")
    _set(P.AlternateBase,          "ALT_BASE_BG")
    _set(P.Text,          "TEXT_MAIN")
    _set(P.PlaceholderText,          "PLACEHOLDER")
    _set(P.Button,          "BUTTON_BG")
    _set(P.ButtonText,          "TEXT_BUTTON")
    _set(P.Highlight,          "ACCENT")
    _set(P.HighlightedText,          "HIGHLIGHT_TEXT")
    _set(P.Link,          "LINK")
    _set(P.LinkVisited,          "LINK_VISITED")
    _set(P.BrightText,          "LIGHT")
    _set(P.ToolTipBase,          "TOOLTIP_BG")
    _set(P.ToolTipText,          "TEXT_TOOLTIP")
    _set(P.Light,          "LIGHT")
    _set(P.Midlight,          "MIDLIGHT")
    _set(P.Mid,          "MID")
    _set(P.Dark,          "DARK")
    _set(P.Shadow,          "SHADOW")

    pal.setColor(P.Disabled, P.Window,          QColor(colors["DISABLED_BG"]))
    pal.setColor(P.Disabled, P.WindowText,      QColor(colors["TEXT_DISABLED"]))
    pal.setColor(P.Disabled, P.Base,            QColor(colors["DISABLED_BASE"]))
    pal.setColor(P.Disabled, P.Text,            QColor(colors["TEXT_DISABLED"]))
    pal.setColor(P.Disabled, P.Button,          QColor(colors["DISABLED_BUTTON"]))
    pal.setColor(P.Disabled, P.ButtonText,      QColor(colors["TEXT_DISABLED"]))
    pal.setColor(P.Disabled, P.Highlight,       QColor(colors["DISABLED_HIGHLIGHT"]))
    pal.setColor(P.Disabled, P.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))

    return pal


_STYLE_TEMPLATE = Template("""
/* ============================================================
   Rizpaq: Soft Azure — единый QSS приложения
   ============================================================ */

QMainWindow, QDialog {
    background: $window_bg;
}

QWidget {
    font-family: "Segoe UI", "Bahnschrift", sans-serif;
    color: $text_main;
}

QToolTip {
    background: $tooltip_bg;
    color: $text_tooltip;
    border: 1px solid $border;
    padding: 4px;
}

/* ---------- generic controls ---------- */

QPushButton {
    background: $button_bg;
    color: $text_button;
    border: 1px solid $border;
    border-radius: 5px;
    padding: 5px 12px;
}
QPushButton:hover {
    background: $button_hover;
}
QPushButton:pressed {
    background: $accent;
    color: $text_on_accent;
    border-color: $accent;
}
QPushButton:disabled {
    background: $disabled_button;
    color: $text_disabled;
    border-color: $border_soft;
}

QLineEdit {
    background: $base_bg;
    border: 1px solid $border;
    border-radius: 5px;
    padding: 4px 8px;
    color: $text_main;
}
QLineEdit:focus {
    border: 1px solid $accent;
}

QComboBox {
    background: $base_bg;
    border: 1px solid $border;
    border-radius: 5px;
    padding: 4px 8px;
    color: $text_main;
}
QComboBox:hover {
    border-color: $accent;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background: $base_bg;
    color: $text_main;
    border: 1px solid $border;
    selection-background-color: $accent;
    selection-color: $text_on_accent;
}

/* ---------- menu ---------- */

QMenuBar {
    background: $window_bg;
    color: $text_header;
    border: none;
    border-bottom: 1px solid $border_soft;
    padding: 2px 6px;
    font-size: 13px;
    font-weight: 600;
}
QMenuBar::item {
    background: transparent;
    padding: 5px 11px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background: $steel;
    color: $text_selected;
}
QMenuBar::item:pressed {
    background: $accent;
    color: $text_on_accent;
}

QMenu {
    background: $base_bg;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 5px 0px;
}
QMenu::item {
    color: $text_main;
    padding: 6px 30px 6px 26px;
    font-size: 13px;
}
QMenu::item:selected {
    background: $accent;
    color: $text_on_accent;
}
QMenu::item:disabled {
    color: $text_disabled;
}
QMenu::separator {
    height: 1px;
    background: $menu_sep;
    margin: 5px 10px;
}
QMenu::indicator {
    width: 14px;
    height: 14px;
    margin-left: 6px;
}

/* ---------- profile bar ---------- */

QWidget#profileBar {
    background: $window_bg;
    border: none;
    border-bottom: 1px solid $border_soft;
}
QWidget#profileSwitchRow,
QWidget#profileActionsRow {
    background: transparent;
}

/* Сегмент [ Архиватор | Бэкап | Дашборд ]. У левой кнопки скруглены
   только левые углы (правый борт убран), у средней нет скруглений и
   оба борта, у правой — только правые углы (левый борт убран).
   Внутренние границы между соседями заменяет борт средней кнопки. */
QPushButton#profileSwitchLeft,
QPushButton#profileSwitchMiddle,
QPushButton#profileSwitchRight {
    background: $base_bg;
    color: $text_main;
    border: 1px solid $border;
    border-radius: 0px;
    padding: 4px 18px;
    font-size: 12px;
    font-weight: 500;
    min-width: 84px;
}
QPushButton#profileSwitchLeft {
    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
    border-right: none;
}
QPushButton#profileSwitchMiddle {
    border-radius: 0px;
}
QPushButton#profileSwitchRight {
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    border-left: none;
}
QPushButton#profileSwitchLeft:hover,
QPushButton#profileSwitchMiddle:hover,
QPushButton#profileSwitchRight:hover {
    background: $button_hover;
}
QPushButton#profileSwitchLeft:checked,
QPushButton#profileSwitchMiddle:checked,
QPushButton#profileSwitchRight:checked {
    background: $accent;
    color: $text_on_accent;
    border-color: $accent;
}
QPushButton#profileSwitchLeft:checked:hover,
QPushButton#profileSwitchMiddle:checked:hover,
QPushButton#profileSwitchRight:checked:hover {
    background: $accent_light;
    border-color: $accent_light;
}

/* Кнопки действий.
   Активная — обычная кнопка: фон, рамка, скругление.
   Неактивная — бледный текст без фона и без рамки. */
QPushButton#profileActionButton {
    background: $button_bg;
    color: $text_button;
    border: 1px solid $border;
    border-radius: 5px;
    padding: 5px 14px;
    font-size: 12px;
}
QPushButton#profileActionButton:hover {
    background: $button_hover;
}
QPushButton#profileActionButton:pressed {
    background: $accent;
    color: $text_on_accent;
    border-color: $accent;
}
QPushButton#profileActionButton[active="false"] {
    background: transparent;
    color: $text_muted_light;
    border: 1px solid transparent;
}
QPushButton#profileActionButton[active="false"]:hover {
    background: transparent;
}
QPushButton#profileActionButton[active="false"]:pressed {
    background: transparent;
    color: $text_muted_light;
    border-color: transparent;
}

/* ---------- backup page ---------- */

QWidget#backupPage {
    background: $window_bg;
}

QWidget#backupTopBar {
    background: $window_bg;
    border: none;
    border-bottom: 1px solid $border_soft;
}
QLabel#backupPathLabel {
    color: $text_muted;
    font-size: 11px;
}
QLabel#backupEmptyLabel {
    color: $text_muted;
    font-size: 13px;
}

/* Страница стека: прозрачный фон, чтобы не перекрывать фон страницы
   бэкапа и не создавать «рамку в рамке». */
QStackedWidget#backupStack,
QStackedWidget#mainStack {
    background: transparent;
    border: none;
}
QWidget#archivePage {
    background: transparent;
}

/* Дерево работ и заданий в профиле «Бэкап».
   До 2.1.0 здесь была обычная таблица — плоский список задач формата
   .rzt. С версии 2.1.0 задачи живут в контейнере .rzp и показываются
   деревом: работа верхним уровнем, её задания — детьми. Правила те же
   по смыслу, но селектор — QTreeWidget. */
QTreeWidget#backupTree {
    background: $base_bg;
    alternate-background-color: $row_alt_table;
    gridline-color: $border_grid;
    border: 1px solid $border_soft;
    font-size: 13px;
}
QTreeWidget#backupTree::item:selected {
    background: $steel;
    color: $text_selected;
}
QTreeWidget#backupTree::item:selected:hover {
    background: $toolbar_bg;
    color: $text_selected;
}
QTreeWidget#backupTree::item:hover {
    background: $row_hover;
    color: $text_main;
}
QTreeWidget#backupTree:focus {
    border: 1px solid $accent;
}

/* Кнопка-ссылка «Запланировать выполнение» в колонке «Следующий запуск».
   Плоская, без рамки, подчёркнутая, как ссылка. Не спорит с кнопками
   на полосе профиля и читается как действие в строке таблицы. */
QPushButton#backupScheduleLink {
    background: transparent;
    border: none;
    color: $accent;
    text-decoration: underline;
    padding: 0px 4px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton#backupScheduleLink:hover {
    color: $accent_light;
    background: transparent;
}
QPushButton#backupScheduleLink:pressed {
    color: $steel_dark;
    background: transparent;
}

/* ---------- search bar ---------- */

QFrame#searchbar {
    background: transparent;
    border: none;
}
QLineEdit#searchedit {
    background: $base_bg;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
    color: $text_main;
}
QLineEdit#searchedit:focus {
    border: 1px solid $accent;
}
QLabel#searchcount {
    color: $text_muted;
    font-size: 11px;
    font-weight: 600;
}

/* ---------- tree / table / log ---------- */

QTreeWidget, QTableWidget, QPlainTextEdit {
    background: $base_bg;
    border: 1px solid $border_soft;
    font-size: 13px;
}
QTreeWidget {
    alternate-background-color: $row_alt_tree;
}
QTableWidget {
    alternate-background-color: $row_alt_table;
    gridline-color: $border_grid;
}
QHeaderView::section {
    background: $header_bg;
    color: $header_text;
    padding: 6px;
    border: none;
    font-weight: 700;
}
QTreeWidget::item:selected,
QTableWidget::item:selected {
    background: $steel;
    color: $text_selected;
}
QTreeWidget::item:selected:hover,
QTableWidget::item:selected:hover {
    background: $toolbar_bg;
    color: $text_selected;
}
QTreeWidget::item:hover,
QTableWidget::item:hover {
    background: $row_hover;
    color: $text_main;
}
QTreeWidget:focus,
QTableWidget:focus {
    border: 1px solid $accent;
}
QPlainTextEdit {
    color: $log_text;
    font-family: Consolas, "Courier New", monospace;
}

/* ---------- status bar ---------- */

QStatusBar {
    background: $status_bg;
    color: $status_text;
}
QStatusBar QLabel {
    color: $status_text;
}
QStatusBar QPushButton {
    background: $steel;
    color: $toolbar_text;
    border: 1px solid $toolbar_border;
    border-radius: 5px;
    padding: 3px 10px;
}
QStatusBar QPushButton:hover {
    background: $steel_hover;
}
QStatusBar QPushButton:pressed {
    background: $accent;
    border-color: $accent;
}

/* ---------- extract progress panel ---------- */

QFrame#extractbar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 $window_bg, stop:1 $extract_bar_bottom);
    border: none;
    border-top: 1px solid $border;
}
QLabel#exbar_icon {
    font-size: 18px;
    min-width: 22px;
}
QLabel#exbar_icon[run="1"] {
    color: $accent;
}
QLabel#exbar_icon[ok="1"] {
    color: $ok_green;
}
QLabel#exbar_icon[err="1"] {
    color: $warn_orange;
}
QLabel#exbar_title {
    color: $text_header;
    font-family: "Bahnschrift", "Segoe UI Semibold", "Segoe UI";
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#exbar_title[ok="1"] {
    color: $ok_green;
}
QLabel#exbar_title[err="1"] {
    color: $warn_orange;
}
QLabel#exbar_counter {
    color: $accent;
    font-family: "Bahnschrift", "Segoe UI Semibold", "Segoe UI";
    font-size: 13px;
    font-weight: 700;
    min-width: 64px;
}
QLabel#exbar_path {
    color: $exbar_path;
    font-family: "Segoe UI", sans-serif;
    font-size: 10px;
}
QProgressBar#exbar_track {
    border: none;
    border-radius: 6px;
    background: $progress_track;
    text-align: center;
    height: 12px;
}
QProgressBar#exbar_track::chunk {
    border-radius: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 $accent, stop:1 $progress_grad_end);
}
QPushButton#exbar_cancel {
    color: $toolbar_text;
    background: $steel;
    border: 1px solid $toolbar_border;
    border-radius: 5px;
    padding: 4px 14px;
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#exbar_cancel:hover {
    background: $steel_hover;
}
QPushButton#exbar_cancel:pressed {
    background: $accent;
    border-color: $accent;
}
QPushButton#exbar_cancel:focus {
    outline: none;
    border: 1px solid $accent;
}
QPushButton#exbar_cancel:disabled {
    background: $text_muted_light;
    border-color: $text_muted_light;
    color: $window_bg;
}

/* ---------- archive info dialog ---------- */

QLabel#archive_info_path {
    color: $text_header;
    font-weight: 600;
}
QLabel#archive_info_summary {
    color: $text_main;
}

/* ---------- diff dialog ---------- */

QLabel#diff_summary {
    color: $text_header;
    font-weight: 600;
}

/* ---------- хлебные крошки ---------- */

QFrame#breadcrumb {
    background: $breadcrumb_bg;
    border: none;
}
QFrame#breadcrumb QPushButton {
    color: $crumb_link;
    background: transparent;
    border: none;
    padding: 2px 4px;
}
QFrame#breadcrumb QPushButton:hover {
    color: $crumb_link_hover;
    text-decoration: underline;
}
QFrame#breadcrumb QLabel#crumb_last {
    color: $crumb_label;
    font-weight: bold;
    padding: 2px 4px;
}
QFrame#breadcrumb QLabel#sep {
    color: $crumb_sep;
    padding: 0 2px;
}

/* ---------- окошко «идёт операция» ---------- */

QWidget#noticeCard {
    background: $base_bg;
    border: 1px solid $border;
    border-radius: 10px;
}
QLabel#noticeTitle {
    font-weight: 700;
    font-size: 13px;
    color: $text_header;
    background: transparent;
}
QProgressBar#noticeBar {
    border: none;
    background: $notice_track;
    border-radius: 5px;
    height: 10px;
}
QProgressBar#noticeBar::chunk {
    background: $accent;
    border-radius: 5px;
}
QLabel#noticeElapsed {
    color: $text_muted;
    font-size: 11px;
    background: transparent;
}
QLabel#noticeHint {
    color: $notice_hint;
    font-size: 11px;
    background: transparent;
}

/* ---------- окно прогресса операции ---------- */

QLabel#opTitle {
    font-weight: 700;
    font-size: 13px;
    color: $text_header;
}
QLabel#opTitle[state="ok"] {
    color: $ok_green;
}
QLabel#opTitle[state="err"] {
    color: $warn_orange;
}
QLabel#opPct {
    font-weight: 700;
    color: $accent;
    font-size: 12px;
}
QLabel#opFieldValue {
    color: $text_main;
    font-size: 11px;
}
QLabel#opFieldLabel {
    color: $text_muted;
    font-size: 11px;
}
QLabel#opCurrent {
    color: $text_main;
    font-size: 11px;
}
QPlainTextEdit#opLog {
    font-family: Consolas, "Courier New", monospace;
    font-size: 10px;
    color: $log_text;
}

/* ---------- подписи в диалогах ---------- */

QLabel#methodPreview {
    color: $text_muted;
    font-family: Consolas, monospace;
    font-size: 11px;
}
QLabel#assocWarn {
    color: $warn_orange;
    font-size: 11px;
}
QLabel#schedHint {
    color: $hint_text;
    font-size: 11px;
    font-style: italic;
}

""")

def build_style(colors: dict) -> str:
    tokens = {k.lower(): v for k, v in colors.items()}
    return _STYLE_TEMPLATE.safe_substitute(**tokens)


STYLE = build_style(skins.skin())


_ARROW_PATHS: dict = {}


def _ensure_combo_arrow() -> str:
    skin_name = skins.current_name()
    cached = _ARROW_PATHS.get(skin_name)
    if cached and os.path.isfile(cached):
        return cached

    path_out = ""
    try:
        img = QImage(12, 8, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(color("STEEL_DARK")))
        p.drawPolygon(QPolygon([QPoint(1, 1), QPoint(11, 1), QPoint(6, 7)]))
        p.end()
        path = os.path.join(
            tempfile.gettempdir(), f"rizpaq_combo_arrow_{skin_name}.png"
        )
        if img.save(path, "PNG"):
            path_out = path
    except Exception:
        path_out = ""

    _ARROW_PATHS[skin_name] = path_out
    return path_out


def _combo_arrow_qss() -> str:

    arrow = _ensure_combo_arrow()
    if not arrow:
        return ""
    url = arrow.replace("\\", "/")
    return f"""
QComboBox::down-arrow {{
    image: url({url});
    width: 12px;
    height: 8px;
}}
QComboBox::down-arrow:disabled {{
    image: url({url});
    opacity: 0.4;
}}
"""


def _paint(app, colors: dict) -> None:

    try:
        app.setStyle("Fusion")
    except Exception:
        pass
    app.setPalette(build_palette(colors))
    app.setStyleSheet(build_style(colors) + _combo_arrow_qss())


def apply_theme(app, skin_name: str = None) -> str:
    if skin_name:
        skins.set_current(skin_name)
    colors = skins.skin(skins.current_name())
    _paint(app, colors)
    return skins.current_name()


def refresh_theme(app) -> str:
    return apply_theme(app, skins.current_name())
