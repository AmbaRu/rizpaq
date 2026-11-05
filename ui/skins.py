from __future__ import annotations

from collections import OrderedDict


SOFT_AZURE = {

    "WINDOW_BG":          "#eef3fa",
    "BASE_BG":            "#ffffff",
    "ALT_BASE_BG":        "#eef3fa",
    "BUTTON_BG":          "#e7eef7",
    "TOOLTIP_BG":         "#fffdf2",


    "TEXT_WINDOW":        "#1f3a5c",
    "TEXT_MAIN":          "#26405e",
    "TEXT_HEADER":        "#244a78",
    "TEXT_BUTTON":        "#244a78",
    "TEXT_TOOLTIP":       "#33414f",
    "TEXT_MUTED":         "#5a6b82",
    "TEXT_MUTED_LIGHT":   "#8a9bb3",
    "TEXT_DISABLED":      "#9fb0c4",
    "PLACEHOLDER":        "#8a9bb3",
    "TEXT_SELECTED":      "#f5f8fc",
    "TEXT_ON_ACCENT":     "#f4f8fc",


    "HEADER_TEXT":        "#f4f8fc",
    "STATUS_TEXT":        "#eaf1fa",
    "LOG_TEXT":           "#3a4d66",
    "HINT_TEXT":          "#718096",


    "ACCENT":             "#2f6db5",
    "ACCENT_LIGHT":       "#86b4e6",
    "LINK":               "#2e63a6",
    "LINK_VISITED":       "#5b7bb0",
    "HIGHLIGHT_TEXT":     "#ffffff",


    "BORDER":             "#c3d2e6",
    "BORDER_SOFT":        "#d3deec",
    "BORDER_GRID":        "#e3e6ec",


    "STEEL":              "#5d83b1",
    "STEEL_HOVER":        "#7ba0cb",
    "STEEL_DARK":         "#4f74a3",
    "ROW_HOVER":          "#e4eefb",
    "ROW_ALT_TREE":       "#f0f2f6",
    "ROW_ALT_TABLE":      "#f6f7fa",


    "HEADER_BG":          "#5680b0",
    "STATUS_BG":          "#5680b0",
    "TOOLBAR_BG":         "#6e94c1",
    "TOOLBAR_BUTTON_BG":  "#5d83b1",
    "TOOLBAR_BORDER":     "#88a8cf",
    "TOOLBAR_TEXT":       "#f4f8fc",


    "BREADCRUMB_BG":      "#eef3fa",
    "BREADCRUMB_BORDER":  "#d3deec",
    "CRUMB_LABEL":        "#333333",
    "CRUMB_LINK":         "#2a6db5",
    "CRUMB_LINK_HOVER":   "#1a4d85",
    "CRUMB_TEXT":         "#dce8f7",


    "CRUMB_SEP":          "#999999",
    "CRUMB_ICON":         "#9fb9da",
    "CRUMB_LAST":         "#a9cdf2",


    "OK_GREEN":           "#2f9e6f",
    "WARN_ORANGE":        "#c47a1e",


    "BUSY_STEEL":         "#5a7a9c",
    "ARC_BLUE":           "#2e63a6",
    "DIFF_ADDED":         "#1e7a3c",
    "DIFF_REMOVED":       "#b3382c",
    "DIFF_CHANGED":       "#b07d1a",
    "DIFF_UNCHANGED":     "#5a6b82",


    "DISABLED_BG":        "#e9eef5",
    "DISABLED_BASE":      "#eef2f8",
    "DISABLED_BUTTON":    "#e1e8f1",
    "DISABLED_HIGHLIGHT": "#9bb6d6",


    "LIGHT":              "#ffffff",
    "MIDLIGHT":           "#dde7f3",
    "MID":                "#c3d2e6",
    "DARK":               "#9fb2cb",
    "SHADOW":             "#7d92ad",


    "EXTRACT_BAR_BOTTOM": "#e4ecf7",


    "EXBAR_PATH":          "#6a7c95",
    "PROGRESS_TRACK":     "#d7e0ee",
    "PROGRESS_GRAD_END":  "#6f9bd0",
    "BUTTON_HOVER":       "#d6e2f2",
    "MENU_SEP":           "#dce5f1",
    "NOTICE_TRACK":       "#e6edf6",
    "NOTICE_HINT":        "#a8761e",
}


WHITE_AIR = {
    "WINDOW_BG":          "#f4f6f8",
    "BASE_BG":            "#ffffff",
    "ALT_BASE_BG":        "#fafbfc",
    "BUTTON_BG":          "#fbfcfd",
    "TOOLTIP_BG":         "#ffffff",

    "TEXT_WINDOW":        "#1c2024",
    "TEXT_MAIN":          "#22262b",
    "TEXT_HEADER":        "#1c2024",
    "TEXT_BUTTON":        "#22262b",
    "TEXT_TOOLTIP":       "#22262b",
    "TEXT_MUTED":         "#6b7480",


    "TEXT_MUTED_LIGHT":   "#7c858e",
    "TEXT_DISABLED":      "#b3bac2",
    "PLACEHOLDER":        "#9aa3ad",

    "TEXT_SELECTED":      "#1c2024",
    "TEXT_ON_ACCENT":     "#ffffff",
    "HEADER_TEXT":        "#2a2f35",
    "STATUS_TEXT":        "#2a2f35",
    "LOG_TEXT":           "#3d444b",
    "HINT_TEXT":          "#6b7480",

    "ACCENT":             "#3d7fa6",
    "ACCENT_LIGHT":       "#a8c8dc",
    "LINK":               "#2f6f96",
    "LINK_VISITED":       "#6a8ba3",
    "HIGHLIGHT_TEXT":     "#ffffff",

    "BORDER":             "#e0e4e8",
    "BORDER_SOFT":        "#eaedf0",
    "BORDER_GRID":        "#f0f2f4",


    "STEEL":              "#dde7ee",
    "STEEL_HOVER":        "#cfdde8",
    "STEEL_DARK":         "#5b7d96",
    "ROW_HOVER":          "#f0f5f8",
    "ROW_ALT_TREE":       "#fafbfc",
    "ROW_ALT_TABLE":      "#fbfcfd",

    "HEADER_BG":          "#e9edf1",
    "STATUS_BG":          "#e9edf1",
    "TOOLBAR_BG":         "#e4eaef",
    "TOOLBAR_BUTTON_BG":  "#e2e8ed",
    "TOOLBAR_BORDER":     "#cdd4db",
    "TOOLBAR_TEXT":       "#2a2f35",

    "BREADCRUMB_BG":      "#eceff2",
    "BREADCRUMB_BORDER":  "#e0e4e8",
    "CRUMB_LABEL":        "#22262b",
    "CRUMB_LINK":         "#3d7fa6",
    "CRUMB_LINK_HOVER":   "#24536c",
    "CRUMB_TEXT":         "#6b7480",
    "CRUMB_SEP":          "#9aa3ad",
    "CRUMB_ICON":         "#b3bac2",
    "CRUMB_LAST":         "#3d7fa6",

    "OK_GREEN":           "#2f8f63",
    "WARN_ORANGE":        "#b8791f",


    "BUSY_STEEL":         "#5f7c92",
    "ARC_BLUE":           "#2f6f96",
    "DIFF_ADDED":         "#1e7a3c",
    "DIFF_REMOVED":       "#b3382c",
    "DIFF_CHANGED":       "#a0761c",
    "DIFF_UNCHANGED":     "#6b7480",

    "DISABLED_BG":        "#f0f2f4",
    "DISABLED_BASE":      "#f7f8f9",
    "DISABLED_BUTTON":    "#eef0f2",
    "DISABLED_HIGHLIGHT": "#9fb0bd",

    "LIGHT":              "#ffffff",
    "MIDLIGHT":           "#e6eaed",
    "MID":                "#d8dde2",
    "DARK":               "#a9b1b9",
    "SHADOW":             "#8b949c",

    "EXTRACT_BAR_BOTTOM": "#f7f9fa",
    "EXBAR_PATH":          "#7b8794",
    "PROGRESS_TRACK":     "#e8ecef",
    "PROGRESS_GRAD_END":  "#6ea3c0",
    "BUTTON_HOVER":       "#eef2f6",
    "MENU_SEP":           "#e6eaed",
    "NOTICE_TRACK":       "#e8ecef",
    "NOTICE_HINT":        "#9a6f1e",
}


SKINS: "OrderedDict[str, dict]" = OrderedDict(
    [
        ("soft_azure", SOFT_AZURE),
        ("white_air", WHITE_AIR),
    ]
)

DEFAULT_SKIN = "soft_azure"

_current = DEFAULT_SKIN


def skin_names() -> list:

    return list(SKINS.keys())


def has_skin(name: str) -> bool:
    return name in SKINS


def skin(name: str = None) -> dict:
    if name and name in SKINS:
        return SKINS[name]
    return SKINS[_current if _current in SKINS else DEFAULT_SKIN]


def current_name() -> str:

    return _current


def set_current(name: str) -> str:
    global _current
    if name in SKINS:
        _current = name
    return _current


def color(token: str) -> str:
    return skin().get(token, "#ff00ff")


def missing_tokens(name: str) -> list:

    ref = SKINS[DEFAULT_SKIN]
    return sorted(t for t in ref if t not in SKINS[name])


def extra_tokens(name: str) -> list:

    ref = SKINS[DEFAULT_SKIN]
    return sorted(t for t in SKINS[name] if t not in ref)
