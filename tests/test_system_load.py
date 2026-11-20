
from __future__ import annotations

import unittest

from core.system_load import SystemLoadSampler, format_percent, format_rate


class TestFormatting(unittest.TestCase):
    def test_rate(self):
        self.assertEqual(format_rate(155 << 20), "155.0 МБ/с")
        self.assertEqual(format_rate(1 << 30), "1.0 ГБ/с")
        self.assertEqual(format_rate(0), "0 МБ/с")
        self.assertEqual(format_rate(None), "0 МБ/с")

    def test_percent(self):
        self.assertEqual(format_percent(23.456), "23.5%")
        self.assertEqual(format_percent(150), "100.0%")
        self.assertEqual(format_percent(None), "—")


class TestSampler(unittest.TestCase):
    def test_sample_always_has_all_keys(self):
        sampler = SystemLoadSampler()
        try:
            sample = sampler.sample()
            self.assertEqual(
                set(sample),
                {"cpu", "memory", "disk_read", "disk_write", "disk_busy"},
            )
            for value in sample.values():
                self.assertTrue(value is None or value >= 0)
        finally:
            sampler.close()

    def test_close_is_idempotent(self):
        sampler = SystemLoadSampler()
        sampler.close()
        sampler.close()
        self.assertEqual(sampler.sample()["cpu"], None)


if __name__ == "__main__":
    unittest.main()
