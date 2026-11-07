

















from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication              

from ui.profile_bridge import (              
    DEFAULT_PROFILE,
    PROFILES,
    ProfileBridgeMixin,
    profile_title,
)

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))



class _FakeCfg:
    pass

    def __init__(self, profile=None):
        self.profile = profile


class _FakeStatusBar:
    def __init__(self):
        self.messages = []

    def showMessage(self, text, *a, **k):
        self.messages.append(text)


class _Host(ProfileBridgeMixin):
    pass






    def __init__(self, profile=None):
        self._cfg = _FakeCfg(profile)
        self._status = _FakeStatusBar()
        self._profile = None
        self._profile_actions = None

    def statusBar(self):
        return self._status


class TestDefaults(unittest.TestCase):
    pass

    def test_profiles_tuple_is_stable(self):
        pass
        self.assertEqual(PROFILES, ("archive", "backup"))

    def test_default_is_archive(self):
        pass







        self.assertEqual(DEFAULT_PROFILE, "archive")

    def test_missing_profile_falls_back_to_default(self):
        h = _Host(profile=None)
        self.assertEqual(h._init_profile(), "archive")
        self.assertEqual(h.current_profile(), "archive")

    def test_unknown_profile_falls_back_to_default(self):
        pass





        h = _Host(profile="hybrid")
        self.assertEqual(h._init_profile(), "archive")
        self.assertEqual(h.current_profile(), "archive")

    def test_known_profiles_are_kept(self):
        for code in PROFILES:
            with self.subTest(profile=code):
                h = _Host(profile=code)
                self.assertEqual(h._init_profile(), code)
                self.assertEqual(h.current_profile(), code)

    def test_current_profile_survives_missing_attribute(self):
        pass



        h = _Host(profile=None)
        if hasattr(h, "_profile"):
            del h._profile
        self.assertEqual(h.current_profile(), "archive")


class TestSwitching(unittest.TestCase):
    pass

    def test_switch_updates_current(self):
        h = _Host(profile="archive")
        h._init_profile()
        self.assertEqual(h._switch_profile("backup"), "backup")
        self.assertEqual(h.current_profile(), "backup")

    def test_switch_persists_to_config(self):
        h = _Host(profile="archive")
        h._init_profile()
        h._switch_profile("backup")
        self.assertEqual(h._cfg.profile, "backup")

    def test_switch_to_unknown_is_ignored(self):
        pass
        h = _Host(profile="archive")
        h._init_profile()
        before = h.current_profile()
        result = h._switch_profile("hybrid")
        self.assertEqual(result, before)
        self.assertEqual(h.current_profile(), before)
        self.assertEqual(h._cfg.profile, "archive")

    def test_switch_reports_in_status(self):
        pass
        h = _Host(profile="archive")
        h._init_profile()
        h._switch_profile("backup")
        self.assertTrue(h._status.messages, "статусбар не тронут")
                                                                   
                                                                   
        self.assertTrue(h._status.messages[0])

    def test_switch_is_idempotent(self):
        pass
        h = _Host(profile="backup")
        h._init_profile()
        self.assertEqual(h._switch_profile("backup"), "backup")
        self.assertEqual(h.current_profile(), "backup")


class TestProfileTitle(unittest.TestCase):
    pass

    def test_known_codes_return_text(self):
        for code in PROFILES:
            with self.subTest(profile=code):
                title = profile_title(code)
                self.assertTrue(title, "пустой заголовок профиля")
                                                                    
                self.assertNotIn("{", title)

    def test_unknown_code_returns_code(self):
        pass
        self.assertEqual(profile_title("nonexistent"), "nonexistent")


class TestLocaleKeys(unittest.TestCase):
    pass








    KEYS = (
        "menu.settings.profile",
        "profile.archive",
        "profile.backup",
        "status.profile_changed",
    )

    def test_keys_exist_in_all_languages(self):
        locales = ROOT / "locales"
        for path in sorted(locales.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            strings = data.get("strings", {})
            for key in self.KEYS:
                with self.subTest(locale=path.stem, key=key):
                    self.assertIn(
                        key, strings,
                        f"{path.name}: нет ключа {key}",
                    )
                    self.assertTrue(
                        strings[key],
                        f"{path.name}: ключ {key} пустой",
                    )

    def test_placeholders_match_english(self):
        pass





        locales = ROOT / "locales"
        en = json.loads(
            (locales / "en.json").read_text(encoding="utf-8")
        )["strings"]
        ref = en["status.profile_changed"]
        self.assertIn("{name}", ref, "в английском потерян плейсхолдер")

        for path in sorted(locales.glob("*.json")):
            if path.stem == "en":
                continue
            strings = json.loads(path.read_text(encoding="utf-8"))["strings"]
            with self.subTest(locale=path.stem):
                self.assertIn(
                    "{name}", strings["status.profile_changed"],
                    f"{path.name}: нет плейсхолдера {{name}}",
                )


class TestConfigRoundtrip(unittest.TestCase):
    pass






    def _tmp(self):
        d = tempfile.mkdtemp(prefix="rizpaq_profile_test_")
        return Path(d) / "cfg.json"

    def test_field_exists(self):
        from core.config import Settings
        s = Settings()
        self.assertTrue(
            hasattr(s, "profile"),
            "в настройках нет поля profile — выбор не сохранится",
        )
        self.assertIsNone(s.profile, "по умолчанию профиль должен быть None")

    def test_save_and_load(self):
        from core.config import load, update
        path = self._tmp()
        update(path, profile="backup")
        self.assertEqual(load(path).profile, "backup")

    def test_unknown_value_survives_roundtrip(self):
        pass





        from core.config import load, update
        path = self._tmp()
        update(path, profile="hybrid")
        self.assertEqual(load(path).profile, "hybrid")

    def test_empty_string_is_none(self):
        pass
        from core.config import Settings
        from core.config import _from_dict
        s = _from_dict({"profile": "   "})
        self.assertIsNone(s.profile)


if __name__ == "__main__":
    unittest.main()
