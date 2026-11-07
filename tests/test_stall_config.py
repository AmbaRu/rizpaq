














import tempfile
import unittest
from pathlib import Path

from core import config as cfg
from core.proc_health import effective_stall_timeout


def _write_config(tmp: str, **fields) -> Path:
    p = Path(tmp) / "settings.json"
    cfg.save(cfg.Settings(**fields), p)
    return p


class TestEngineStallTimeout(unittest.TestCase):
    def test_none_returns_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_config(tmp, engine_stall_timeout=None)
            self.assertEqual(cfg.engine_stall_timeout(90, p), 90.0)

    def test_valid_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_config(tmp, engine_stall_timeout=120)
            self.assertEqual(cfg.engine_stall_timeout(90, p), 120.0)

    def test_clamped_low(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_config(tmp, engine_stall_timeout=1)
            self.assertEqual(cfg.engine_stall_timeout(90, p), 5.0)

    def test_clamped_high(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_config(tmp, engine_stall_timeout=999999)
            self.assertEqual(cfg.engine_stall_timeout(90, p), 3600.0)

    def test_broken_value_returns_default(self):
                                                                      
                                                                    
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "settings.json"
            p.write_text('{"engine_stall_timeout": "много"}', encoding="utf-8")
            self.assertEqual(cfg.engine_stall_timeout(90, p), 90.0)

    def test_missing_file_returns_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "нет_такого.json"
            self.assertEqual(cfg.engine_stall_timeout(90, p), 90.0)


class TestEffectiveStallTimeout(unittest.TestCase):
    def test_patched_module_value_wins_over_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_config(tmp, engine_stall_timeout=120)
                                                                    
                                                                     
            self.assertEqual(effective_stall_timeout(90, 1, p), 1.0)

    def test_config_used_when_module_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_config(tmp, engine_stall_timeout=120)
            self.assertEqual(effective_stall_timeout(90, 90, p), 120.0)

    def test_default_when_no_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_config(tmp)
            self.assertEqual(effective_stall_timeout(90, 90, p), 90.0)


class TestDefaultsInSync(unittest.TestCase):
    pass

    def test_all_defaults_are_90(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from core import zpaq_cli
        from workers import list_worker
        from workers import streaming
        for mod in (zpaq_cli, streaming, list_worker):
            self.assertEqual(
                mod.STALL_TIMEOUT, mod.DEFAULT_STALL_TIMEOUT,
                f"{mod.__name__}: константа разошлась с дефолтом",
            )
            self.assertEqual(mod.DEFAULT_STALL_TIMEOUT, 90)


if __name__ == "__main__":
    unittest.main()
