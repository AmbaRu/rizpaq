
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from core import archive_index as idx
from core import disk_forecast

DAY = 24 * 3600


class TestGrowth(unittest.TestCase):
    def test_not_enough_data(self):
        self.assertIsNone(disk_forecast.daily_growth([]))
        self.assertIsNone(disk_forecast.daily_growth([(0, 100)]))
        self.assertIsNone(disk_forecast.daily_growth([(0, 100), (100, 200)]))

    def test_constant_growth(self):
        samples = [(0, 1000), (DAY, 1000 + 500), (2 * DAY, 1000 + 1000)]
        self.assertEqual(disk_forecast.daily_growth(samples), 500.0)

    def test_shrink_is_zero(self):
        self.assertEqual(
            disk_forecast.daily_growth([(0, 5000), (3 * DAY, 1000)]), 0.0
        )

    def test_days_to_full(self):
        self.assertEqual(disk_forecast.days_to_full(5000, 500), 10)
        self.assertIsNone(disk_forecast.days_to_full(0, 500))
        self.assertIsNone(disk_forecast.days_to_full(5000, 0))

    def test_forecast_size(self):
        self.assertEqual(disk_forecast.forecast_size(1000, 500, 3), 2500)
        self.assertIsNone(disk_forecast.forecast_size(1000, None, 3))


class TestSizeHistory(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.mkdtemp(prefix="rizpaq_size_hist_")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.path = Path(tmp) / "index.sqlite"
        idx._set_index_path_for_tests(self.path)
        self.addCleanup(idx.close)
        self.addCleanup(idx._set_index_path_for_tests, None)

    def test_record_and_load(self):
        import time

        now = int(time.time())
        archive = "F:/All.zpaq"
        idx.record_size(archive, 1000, 10)
        idx.record_size(archive, 2000, 11)
                                                               
        idx.record_size(archive, 2500, 12)
        history = idx.load_size_history(archive)
                                                                     
                                                      
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[-1][1], 2500)
        self.assertGreaterEqual(history[-1][0], now)

    def test_unsupported_paths(self):
        idx.record_size("F:/a_????.zpaq", 100)
        idx.record_size("", 100)
        self.assertEqual(idx.load_size_history("F:/a_????.zpaq"), [])
        self.assertEqual(idx.load_size_history(""), [])

    def test_survives_cache_migration(self):
        pass
        import time

        idx.record_size("F:/photo.zpaq", 5000, 5)
        old_version = idx.SCHEMA_VERSION
        idx.SCHEMA_VERSION = old_version + 1
        self.addCleanup(setattr, idx, "SCHEMA_VERSION", old_version)
        idx.close()
        history = idx.load_size_history("F:/photo.zpaq")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][1], 5000)


if __name__ == "__main__":
    unittest.main()
