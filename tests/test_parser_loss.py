











from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.parser import (              
    ParseReport,
    parse_csv_list,
    parse_csv_list_reported,
)

                                                                     
                                      
GOOD7 = "#2026-09-26 18:35:48\tA....\t30\t720%\t0001\t+\tфайл.txt#"
GOOD_DIR7 = "#2026-09-26 18:35:48\tD....\t30\tdir\t0001\t#\tпапка/#"
GOOD6 = "#2026-09-26 18:35:48\tA....\t30\t720%\t+\tфайл.txt#"


class TestNoLossOnGoodInput(unittest.TestCase):
    pass

    def test_seven_columns(self):
        entries, report = parse_csv_list_reported(
            "\n".join([GOOD7, GOOD7.replace("файл", "другой")])
        )
        self.assertEqual(len(entries), 2)
        self.assertTrue(report.ok)
        self.assertEqual(report.dropped, 0)
        self.assertEqual(report.data_lines, 2)
        self.assertEqual(report.parsed, 2)

    def test_six_columns(self):
        entries, report = parse_csv_list_reported(GOOD6)
        self.assertEqual(len(entries), 1)
        self.assertTrue(report.ok)
        self.assertIsNone(entries[0].version)

    def test_directory_entry(self):
        entries, report = parse_csv_list_reported(GOOD_DIR7)
        self.assertTrue(report.ok)
        self.assertTrue(entries[0].is_dir)
        self.assertEqual(entries[0].path, "папка")

    def test_blank_lines_are_not_losses(self):
        pass





        _entries, report = parse_csv_list_reported(
            "\n\n" + GOOD7 + "\n\n\n" + GOOD7 + "\n"
        )
        self.assertTrue(report.ok, f"пустые строки посчитаны потерями: {report}")
        self.assertEqual(report.dropped, 0)
        self.assertEqual(report.data_lines, 2)

    def test_header_line_is_not_a_loss(self):
        pass






        _entries, report = parse_csv_list_reported(
            "<<C:/путь/backup.zpaq>>:\n" + GOOD7
        )
        self.assertEqual(report.service, 1)
        self.assertEqual(report.data_lines, 1)
        self.assertTrue(report.ok, "служебная строка посчитана потерей")


class TestLossesAreCounted(unittest.TestCase):
    pass

    def test_wrong_column_count(self):
        bad5 = "#2026-09-26 18:35:48\tA....\t30\tфайл.txt#"
        bad8 = GOOD7 + "\tхвост#"

        for bad, label in ((bad5, "5 колонок"), (bad8, "8 колонок")):
            entries, report = parse_csv_list_reported(bad)
            self.assertEqual(len(entries), 0, f"{label}: строка разобрана")
            self.assertEqual(report.dropped, 1, f"{label}: потеря не посчитана")
            self.assertEqual(report.reasons.get("columns"), 1, label)
            self.assertFalse(report.ok, f"{label}: отчёт считает, что всё в порядке")

    def test_version_not_a_number(self):
        bad = GOOD7.replace("\t0001\t", "\tХ\t")
        entries, report = parse_csv_list_reported(bad)
        self.assertEqual(len(entries), 0)
        self.assertEqual(report.reasons.get("version"), 1)
        self.assertEqual(report.dropped, 1)

    def test_empty_path(self):
        bad = "#2026-09-26 18:35:48\tA....\t30\t720%\t0001\t+\t#"
        entries, report = parse_csv_list_reported(bad)
        self.assertEqual(len(entries), 0)
        self.assertEqual(report.reasons.get("empty_path"), 1)

    def test_mixed_input_counts_only_lost(self):
        pass





        text = "\n".join([
            GOOD7,
            "#2026-09-26 18:35:48\tA....\t30\t720%\t0001\t+\tдва.txt#",
            "#2026-09-26 18:35:48\tA....\t30\tплохая.txt#",
            "#2026-09-26 18:35:48\tA....\t30\t720%\tХ\t+\tплохая2.txt#",
            GOOD6,
        ])
        entries, report = parse_csv_list_reported(text)
        self.assertEqual(len(entries), 3)
        self.assertEqual(report.data_lines, 5)
        self.assertEqual(report.dropped, 2)
        self.assertEqual(report.parsed, 3)
        self.assertEqual(report.reasons.get("columns"), 1)
        self.assertEqual(report.reasons.get("version"), 1)

    def test_many_losses_all_counted(self):
        pass



        bad = "#2026-09-26 18:35:48\tA....\t30\tплохая.txt#"
        _entries, report = parse_csv_list_reported("\n".join([bad] * 20))
        self.assertEqual(report.dropped, 20)
        self.assertEqual(len(report.samples), 5,
                         "примеров должно быть не больше пяти")


class TestReportText(unittest.TestCase):
    pass

    def build(self):
        text = "\n".join([
            "#2026-09-26 18:35:48\tA....\t30\t720%\t0001\t+\tхороший.txt#",
            "#2026-09-26 18:35:48\tA....\t30\tплохая.txt#",
            "#2026-09-26 18:35:48\tA....\t30\tплохая2.txt#",
            "#2026-09-26 18:35:48\tA....\t30\tплохая3.txt#",
        ])
        return parse_csv_list_reported(text)[1]

    def test_text_names_counts(self):
        report = self.build()
        out = report.log_text()
        self.assertIn("3", out)
        self.assertIn("4", out, "не названо общее число строк данных")
        self.assertIn("1", out)

    def test_text_contains_sample(self):
        report = self.build()
        out = report.log_text()
        self.assertIn("плохая", out, "в журнале нет примера строки")

    def test_text_has_no_traceback_or_exception(self):
        pass
        out = self.build().log_text()
        for bad in ("Traceback", "Exception", "None"):
            self.assertNotIn(bad, out)

    def test_reasons_sorted_by_frequency(self):
        report = ParseReport()
        for _ in range(5):
            report.note_drop("columns", "a")
        for _ in range(2):
            report.note_drop("version", "b")
        lines = report.reason_lines()
        self.assertEqual(len(lines), 2)
        self.assertIn("5", lines[0])
        self.assertIn("2", lines[1])

    def test_empty_report_text(self):
        report = ParseReport()
        self.assertTrue(report.ok)
        self.assertEqual(report.dropped, 0)
        self.assertEqual(report.reason_lines(), [])


class TestPlainApiKept(unittest.TestCase):
    pass






    def test_returns_list(self):
        out = parse_csv_list(GOOD7)
        self.assertIsInstance(out, list)
        self.assertEqual(len(out), 1)

    def test_empty_text(self):
        out = parse_csv_list("")
        self.assertEqual(out, [])
        entries, report = parse_csv_list_reported("")
        self.assertEqual(entries, [])
        self.assertTrue(report.ok)


if __name__ == "__main__":
    unittest.main()
