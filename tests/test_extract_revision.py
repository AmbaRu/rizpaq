





from __future__ import annotations

import unittest

try:
    from ui.restore_revision_dialog import normalize_date
    from workers.extract_workers import ExtractRevisionWorker

    IMPORT_ERROR = None
except Exception as exc:                               
    ExtractRevisionWorker = None
    normalize_date = None
    IMPORT_ERROR = str(exc)


@unittest.skipIf(
    ExtractRevisionWorker is None,
    f"PySide6/workers import failed: {IMPORT_ERROR}",
)
class TestExtractRevisionWorker(unittest.TestCase):
    def test_date_mode(self):
        w = ExtractRevisionWorker(
            "zpaqfranz", "a.zpaq", None, "date", "2026-01-15 23:59:59", "D:\\out"
        )
        self.assertEqual(
            w.cmd,
            [
                "zpaqfranz", "x", "a.zpaq",
                "-until", "2026-01-15 23:59:59",
                "-to", "D:\\out",
            ],
        )

    def test_all_versions_mode(self):
        w = ExtractRevisionWorker(
            "z", "a.zpaq", "", "all", "", "D:\\out"
        )
        self.assertEqual(
            w.cmd, ["z", "x", "a.zpaq", "-all", "-to", "D:\\out"]
        )

    def test_password_and_all(self):
        w = ExtractRevisionWorker(
            "z", "a.zpaq", "pw", "all", "ignored", "D:\\out"
        )
        self.assertEqual(
            w.cmd,
            ["z", "x", "a.zpaq", "-key", "pw", "-all", "-to", "D:\\out"],
        )

    def test_no_only_filter(self):
        for mode, until in (("date", "2026-01-15 23:59:59"), ("all", "")):
            w = ExtractRevisionWorker("z", "a.zpaq", None, mode, until, "out")
            self.assertNotIn("-only", w.cmd)

    def test_range_mode(self):
        w = ExtractRevisionWorker(
            "z", "downloads_????.zpaq", "pw", "range", "2:5", "D:\\out"
        )
        self.assertEqual(
            w.cmd,
            ["z", "x", "downloads_????.zpaq", "-key", "pw",
             "-range", "2:5", "-to", "D:\\out"],
        )

    def test_range_never_combined_with_until_or_filter(self):
        for spec in ("2:5", "::3", "4"):
            w = ExtractRevisionWorker("z", "a.zpaq", None, "range", spec, "out")
            self.assertNotIn("-until", w.cmd)
            self.assertNotIn("-only", w.cmd)
            self.assertEqual(w.cmd[w.cmd.index("-range") + 1], spec)


@unittest.skipIf(normalize_date is None, f"import failed: {IMPORT_ERROR}")
class TestNormalizeDate(unittest.TestCase):
    def test_day_gets_end_of_day(self):
        self.assertEqual(normalize_date("2026-01-15"), "2026-01-15 23:59:59")

    def test_full_datetime_kept(self):
        self.assertEqual(
            normalize_date("  2026-01-15 12:30:00 "),
            "2026-01-15 12:30:00",
        )

    def test_invalid_values(self):
        for value in ("", "15.01.2026", "2026-13-45", "2026-01-15 99:99"):
            with self.assertRaises(ValueError):
                normalize_date(value)


if __name__ == "__main__":
    unittest.main()
