
from __future__ import annotations

import unittest

from core.par2_progress import Par2Progress, format_speed


class _Clock:
    def __init__(self, start=0.0):
        self.value = start

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class TestParsing(unittest.TestCase):
    def test_typical_output(self):
        p = Par2Progress(archive_size=1000000)
        lines = [
            "Block size: 4",
            "Source file count: 1",
            "Source block count: 21",
            "Recovery block count: 1",
            "Recovery file count: 1",
            "Opening: All.zpaq",
            "Processing: 4.8%",
            "Processing: 100.0%",
            "Writing recovery packets",
            "Wrote 12345 bytes to disk",
            "Writing verification packets",
            "Done",
        ]
        for line in lines:
            p.feed(line)
        self.assertEqual(p.phase, "done")
        self.assertTrue(p.done)
        self.assertEqual(p.percent, 100.0)
        self.assertEqual(p.source_blocks, 21)
        self.assertEqual(p.recovery_blocks, 1)
        self.assertEqual(p.block_size, 4)
        self.assertEqual(p.written, 12345)

    def test_russian_comma_decimal_and_phase_order(self):
        p = Par2Progress()
        p.feed("Processing: 12,5%")
        self.assertEqual(p.percent, 12.5)
        p.feed("Writing verification packets")
        self.assertEqual(p.phase, "verification")
        p.feed("Writing recovery packets")
        self.assertEqual(p.phase, "writing")

    def test_percent_clamped(self):
        p = Par2Progress()
        p.feed("Processing: 250%")
        self.assertEqual(p.percent, 100.0)


class TestSpeedAndEta(unittest.TestCase):
    def test_eta_from_percent_and_archive_size(self):
        clock = _Clock()
        p = Par2Progress(archive_size=1000000, redundancy=5, clock=clock)
        p.feed("Processing: 0%")
        clock.advance(10)
        p.feed("Processing: 10%")
                                                                       
        snap = p.snapshot()
        self.assertAlmostEqual(snap["speed"], 10000.0)
        self.assertAlmostEqual(snap["eta_s"], 90)
        self.assertEqual(snap["read"], 100000)
        self.assertEqual(snap["eta"], "1:30")

    def test_snapshot_updates_without_new_lines(self):
        pass
        clock = _Clock()
        p = Par2Progress(archive_size=1000000, clock=clock)
        p.feed("Processing: 0%")
        clock.advance(10)
        p.feed("Processing: 50%")
        first = p.snapshot()
        clock.advance(5)
        second = p.snapshot()
        self.assertEqual(first["eta_s"], second["eta_s"])
        self.assertEqual(first["read"], second["read"])
                                                       
        self.assertIsNotNone(second["speed"])
        self.assertIsNotNone(second["eta"])

    def test_no_eta_without_size(self):
        clock = _Clock()
        p = Par2Progress(archive_size=0, clock=clock)
        p.feed("Processing: 20%")
        self.assertIsNone(p.snapshot()["eta_s"])

    def test_write_speed(self):
        clock = _Clock()
        p = Par2Progress(clock=clock)
        p.feed("Writing recovery packets")
        p.feed("Wrote 1000 bytes to disk")
        clock.advance(2)
        p.feed("Wrote 2000 bytes to disk")
        self.assertEqual(p.written, 3000)
        self.assertGreater(p.snapshot()["write_speed"], 0)


class TestFormatSpeed(unittest.TestCase):
    def test_units(self):
        self.assertEqual(format_speed(5 << 20), "5.0 MB/s")
        self.assertEqual(format_speed(1536), "1.5 KB/s")
        self.assertIn("B/s", format_speed(100))
        self.assertEqual(format_speed(0), "—")


if __name__ == "__main__":
    unittest.main()
