














from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLineEdit,
    QMessageBox,
)

                                                                            

try:
    VERTICAL = Qt.Orientation.Vertical
except AttributeError:
    VERTICAL = Qt.Vertical

try:
    HORIZONTAL = Qt.Orientation.Horizontal
except AttributeError:
    HORIZONTAL = Qt.Horizontal

                                                                            

try:
    USER_ROLE = int(Qt.ItemDataRole.UserRole)
except Exception:
    try:
        USER_ROLE = int(Qt.UserRole)
    except Exception:
        USER_ROLE = Qt.UserRole

KIND_ROLE = USER_ROLE + 1
ARC_OWNER_ROLE = KIND_ROLE + 1

                                     
SIZE_RAW_ROLE = ARC_OWNER_ROLE + 1
DATE_RAW_ROLE = ARC_OWNER_ROLE + 2
VERSION_RAW_ROLE = ARC_OWNER_ROLE + 3
NAME_SORT_ROLE = ARC_OWNER_ROLE + 4

                                                               
TCOL = 0

                                                                           

try:
    CUSTOM_CONTEXT = Qt.ContextMenuPolicy.CustomContextMenu
except AttributeError:
    CUSTOM_CONTEXT = Qt.CustomContextMenu

try:
    MATCH_RECURSIVE = Qt.MatchFlag.MatchRecursive
except AttributeError:
    MATCH_RECURSIVE = Qt.MatchRecursive

try:
    HEADER_STRETCH = QHeaderView.ResizeMode.Stretch
except AttributeError:
    HEADER_STRETCH = QHeaderView.Stretch

try:
    SELECT_ROWS = QAbstractItemView.SelectionBehavior.SelectRows
except AttributeError:
    SELECT_ROWS = QAbstractItemView.SelectRows

try:
    NO_EDIT = QAbstractItemView.EditTrigger.NoEditTriggers
except AttributeError:
    NO_EDIT = QAbstractItemView.NoEditTriggers

try:
    PASSWORD_ECHO = QLineEdit.EchoMode.Password
except AttributeError:
    PASSWORD_ECHO = QLineEdit.Password

try:
    YES_BUTTON = QMessageBox.StandardButton.Yes
    YES_NO_BUTTONS = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
except AttributeError:
    YES_BUTTON = QMessageBox.Yes
    YES_NO_BUTTONS = QMessageBox.Yes | QMessageBox.No

try:
    WAIT_CURSOR = Qt.CursorShape.WaitCursor
except AttributeError:
    WAIT_CURSOR = Qt.WaitCursor

try:
    WINDOW_SHORTCUT = Qt.ShortcutContext.WindowShortcut
except AttributeError:
    WINDOW_SHORTCUT = Qt.WindowShortcut

                                                                            
try:
    WIDGET_SHORTCUT = Qt.ShortcutContext.WidgetShortcut
except AttributeError:
    try:
        WIDGET_SHORTCUT = Qt.WidgetShortcut
    except AttributeError:
        WIDGET_SHORTCUT = WINDOW_SHORTCUT

                                                                            

try:
    ASCENDING_ORDER = Qt.SortOrder.AscendingOrder
    DESCENDING_ORDER = Qt.SortOrder.DescendingOrder
except AttributeError:
    try:
        ASCENDING_ORDER = Qt.AscendingOrder
        DESCENDING_ORDER = Qt.DescendingOrder
    except AttributeError:
        ASCENDING_ORDER = 0
        DESCENDING_ORDER = 1

                                                                            

                                                                   
                                                                
                                                                    
from core.paths import (                                               
    MULTIPART_RE as _MULTIPART_RE,
    multipart_pattern,
)

                                              
MULTIPART_RE = _MULTIPART_RE


                                                                            

K_FS = "fs"                                               
K_ARC = "arc"                                         
K_FS_ARC = "fs_arc"                                                                  
K_FS_UNI_ARC = "fs_uni_arc"                                                                 
K_PLACE = "place"                                     
K_UP = "up"                                    
K_FS_DIR = "fs_dir"                               
K_FS_FILE = "fs_file"                            
K_ARC_DIR = "arc_dir"                                  
K_ARC_FILE = "arc_file"                               

PLACEHOLDER = "placeholder"
