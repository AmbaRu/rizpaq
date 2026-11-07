







from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.config import Settings, load, save, update


class _TmpCfg:
    pass

    def __init__(self):
        import tempfile
        self._dir = tempfile.mkdtemp(prefix="zpaq_cfg_test_")
        self.path = Path(self._dir) / "cfg.json"

    def cleanup(self):
        import shutil
        shutil.rmtree(self._dir, ignore_errors=True)


class TestDefaults(unittest.TestCase):
    def test_missing_file_returns_defaults(self):
        t = _TmpCfg()
        try:
            s = load(t.path)                  
            self.assertIsInstance(s, Settings)
            self.assertIsNone(s.zpaq_path)
            self.assertIsNone(s.last_fs_path)
            self.assertIsNone(s.last_extract_dir)
            self.assertFalse(s.latest_only)
            self.assertFalse(s.window_maximized)
            self.assertIsNone(s.window_geometry)
            self.assertIsNone(s.left_split)
        finally:
            t.cleanup()

    def test_associations_asked_default_false(self):
        pass



        t = _TmpCfg()
        try:
            s = load(t.path)
            self.assertFalse(s.associations_asked)
        finally:
            t.cleanup()


class TestRoundTrip(unittest.TestCase):
    def test_save_then_load(self):
        t = _TmpCfg()
        try:
            s = Settings(
                zpaq_path=r"C:\tools\zpaqfranz.exe",
                last_fs_path=r"D:\Python",
                last_extract_dir=r"F:\restore",
                latest_only=True,
                window_geometry=[100, 200, 1320, 820],
                window_maximized=True,
                left_split=[240, 460],
            )
            save(s, t.path)
            r = load(t.path)
            self.assertEqual(r.zpaq_path, r"C:\tools\zpaqfranz.exe")
            self.assertEqual(r.last_fs_path, r"D:\Python")
            self.assertEqual(r.last_extract_dir, r"F:\restore")
            self.assertTrue(r.latest_only)
            self.assertTrue(r.window_maximized)
            self.assertEqual(r.window_geometry, [100, 200, 1320, 820])
            self.assertEqual(r.left_split, [240, 460])
        finally:
            t.cleanup()

    def test_file_is_valid_json_after_save(self):
        t = _TmpCfg()
        try:
            save(Settings(zpaq_path="x"), t.path)
            data = json.loads(t.path.read_text(encoding="utf-8"))
            self.assertIsInstance(data, dict)
            self.assertEqual(data["zpaq_path"], "x")
        finally:
            t.cleanup()

    def test_associations_asked_round_trip(self):
        pass




        t = _TmpCfg()
        try:
                                                                              
            update(t.path, associations_asked=True)
            self.assertTrue(load(t.path).associations_asked)

            data = json.loads(t.path.read_text(encoding="utf-8"))
            self.assertIs(data.get("associations_asked"), True)

                                                           
            update(t.path, associations_asked=False)
            self.assertFalse(load(t.path).associations_asked)
        finally:
            t.cleanup()


class TestRobustness(unittest.TestCase):
    def test_corrupt_json_yields_defaults(self):
        t = _TmpCfg()
        try:
            t.path.write_text("{ this is not json ::: ", encoding="utf-8")
            s = load(t.path)
            self.assertIsInstance(s, Settings)
            self.assertIsNone(s.zpaq_path)
            self.assertFalse(s.associations_asked)
        finally:
            t.cleanup()

    def test_wrong_types_are_coerced_to_defaults(self):
        t = _TmpCfg()
        try:
            t.path.write_text(
                json.dumps({
                    "zpaq_path": 12345,                       
                    "latest_only": "maybe",                 
                    "window_geometry": [1, 2],                     
                    "left_split": [1, 2, 3, 4],                     
                    "window_maximized": True,          
                }),
                encoding="utf-8",
            )
            s = load(t.path)
            self.assertIsNone(s.zpaq_path)
            self.assertFalse(s.latest_only)                                 
            self.assertIsNone(s.window_geometry)               
            self.assertIsNone(s.left_split)                    
            self.assertTrue(s.window_maximized)                          
        finally:
            t.cleanup()

    def test_associations_asked_wrong_type_is_false(self):
        pass





        t = _TmpCfg()
        try:
            t.path.write_text(
                json.dumps({"associations_asked": "yes"}),
                encoding="utf-8",
            )
            s = load(t.path)
            self.assertFalse(s.associations_asked)
        finally:
            t.cleanup()

    def test_unknown_keys_ignored(self):
        t = _TmpCfg()
        try:
            t.path.write_text(
                json.dumps({"zpaq_path": "ok", "future_field": "???"}),
                encoding="utf-8",
            )
            s = load(t.path)
            self.assertEqual(s.zpaq_path, "ok")
        finally:
            t.cleanup()

    def test_empty_strings_become_none(self):
        t = _TmpCfg()
        try:
            t.path.write_text(json.dumps({"zpaq_path": "   "}), encoding="utf-8")
            s = load(t.path)
            self.assertIsNone(s.zpaq_path)
        finally:
            t.cleanup()


class TestUpdate(unittest.TestCase):
    def test_update_changes_only_known_fields(self):
        t = _TmpCfg()
        try:
            update(t.path, zpaq_path="a", latest_only=True)
            update(t.path, latest_only=False, totally_unknown="x")
            s = load(t.path)
            self.assertEqual(s.zpaq_path, "a")                                    
            self.assertFalse(s.latest_only)                    
        finally:
            t.cleanup()


if __name__ == "__main__":
                                                                            
                                                  
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
