
from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from core import size_trend

NOW = datetime(2026, 11, 23, 12, 0)


def _ts(days_ago: int, hour=10) -> int:
    return int((NOW - timedelta(days=days_ago)).replace(hour=hour).timestamp())


class TestSeries(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(size_trend.build_series([], now=NOW), [])

    def test_fills_gaps_and_labels(self):
        samples = [
            (_ts(9), 1000, 1),
            (_ts(4), 2000, 2),
            (_ts(0), 3000, 3),
        ]
        series = size_trend.build_series(samples, days=10, now=NOW)
        self.assertEqual(len(series), 10)
        self.assertEqual(series[0][1], 1000)
                                                        
        self.assertEqual(series[1][1], 1000)
        self.assertEqual(series[5][1], 2000)
        self.assertEqual(series[-1][1], 3000)
        self.assertEqual(series[-1][0], "23.11")

    def test_uses_value_before_window(self):
        samples = [(_ts(20), 500, 1), (_ts(1), 900, 2)]
        series = size_trend.build_series(samples, days=3, now=NOW)
        self.assertEqual(len(series), 3)
        self.assertEqual(series[0][1], 500)
        self.assertEqual(series[-1][1], 900)


class TestSaving(unittest.TestCase):
    def test_ratio(self):
        self.assertEqual(size_trend.saving_text(300, 100), 3.0)
        self.assertIsNone(size_trend.saving_text(0, 100))
        self.assertIsNone(size_trend.saving_text(100, 0))


if __name__ == "__main__":
    unittest.main()
