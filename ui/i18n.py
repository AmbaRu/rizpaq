from __future__ import annotations

import json
import locale
import os
import sys
from pathlib import Path


load_errors: dict = {}


_ISO639_2 = {
    "eng": "en", "rus": "ru", "ita": "it", "deu": "de", "ger": "de",
    "fra": "fr", "fre": "fr", "spa": "es", "zho": "zh", "chi": "zh",
    "por": "pt", "jpn": "ja", "pol": "pl",
}


LANGUAGES = {
    "en": "English",
    "ru": "Русский",
    "it": "Italiano",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "zh": "中文",
    "pt": "Português",
    "ja": "日本語",
    "pl": "Polski",
}


_current_strings: dict = {}
_current_lang: str = "en"
_locales_dir: Path | None = None


_language_callbacks: list = []


def _find_locales_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
        candidates = [
            base / "locales",
            base / "_internal" / "locales",
        ]
        for c in candidates:
            if c.is_dir():
                return c

    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "locales",
        here / "locales",
    ]
    for c in candidates:
        if c.is_dir():
            return c

    return here.parent / "locales"


def available_languages() -> dict:
    langs = dict(LANGUAGES)
    d = _locales_dir or _find_locales_dir()
    try:
        for path in d.glob("*.json"):
            code = path.stem
            if code in langs or not code.isalpha() or len(code) > 8:
                continue
            try:
                name = json.loads(path.read_text(encoding="utf-8")).get("_meta", {}).get("name")
            except Exception:
                name = None
            langs[code] = name or code
    except Exception:
        pass
    return langs


def _match_language(tag, available) -> str | None:
    if not tag:
        return None

    for candidate in str(tag).split(":"):

        head = candidate.split(".")[0].split("@")[0]
        head = head.replace("_", "-").strip().lower()

        parts = [p for p in head.split("-") if p]
        if not parts:
            continue

        primary = parts[0]
        if primary in available:
            return primary


        three = _ISO639_2.get(primary)
        if three and three in available:
            return three

    return None


def _language_probes() -> list:
    probes: list = []

    try:
        from PySide6.QtCore import QLocale

        name = QLocale.system().name()
        if name:
            probes.append(name)
    except Exception:
        pass

    try:
        loc = locale.getlocale()
        if loc and loc[0]:
            probes.append(loc[0])
    except Exception:
        pass

    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        value = os.environ.get(var)
        if value:
            probes.append(value)

    return probes


def detect_language() -> str:
    try:
        available = available_languages()
    except Exception:
        return "en"

    for tag in _language_probes():
        code = _match_language(tag, available)
        if code:
            return code

    return "en"


def load_locales(locales_dir=None, lang: str | None = None) -> None:
    global _locales_dir

    if locales_dir is not None:
        _locales_dir = Path(locales_dir)
    else:
        _locales_dir = _find_locales_dir()

    if lang is None:
        lang = _current_lang if _current_lang != "en" else detect_language()

    set_language(lang, notify=False)


def _read_language_file(lang: str):
    path = (_locales_dir or _find_locales_dir()) / (lang + ".json")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        load_errors[lang] = "file not found: " + str(path)
        return None
    except Exception as exc:


        load_errors[lang] = "cannot parse " + path.name + ": " + str(exc)
        return None

    strings = data.get("strings")
    if not isinstance(strings, dict):
        load_errors[lang] = path.name + ": no 'strings' object"
        return None

    load_errors.pop(lang, None)
    return strings


def set_language(lang: str, locales_dir=None, notify: bool = True) -> None:
    global _current_strings, _current_lang, _locales_dir

    if locales_dir is not None:
        _locales_dir = Path(locales_dir)

    if _locales_dir is None:
        _locales_dir = _find_locales_dir()

    load_errors.clear()

    if lang not in available_languages():
        lang = "en"

    strings = _read_language_file(lang)

    if strings is None and lang != "en":

        fallback = _read_language_file("en")
        if fallback is not None:
            sys.stderr.write(
                "Rizpaq: cannot load language " + repr(lang) + " ("
                + load_errors.get(lang, "unknown reason")
                + "); falling back to English.\n"
            )
            strings = fallback
            lang = "en"

    if strings is None:


        _current_strings = {}
        _current_lang = "en"
        return

    if lang != "en":

        en_strings = _read_language_file("en")
        if en_strings:
            for k, v in en_strings.items():
                strings.setdefault(k, v)

    _current_strings = strings
    _current_lang = lang

    if notify:
        for cb in _language_callbacks:
            try:
                cb()
            except Exception:
                pass


def on_language_changed(callback) -> None:
    if callback not in _language_callbacks:
        _language_callbacks.append(callback)


def tr(key: str, **kwargs) -> str:
    text = _current_strings.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def current_language() -> str:

    return _current_lang
