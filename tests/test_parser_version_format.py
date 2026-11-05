from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.parser import (
    VERSION_LINE_RE,
    parse_info,
    parse_size,
)


class TestVersionLineFormat(unittest.TestCase):

    REAL_SMALL = "V1 2026-06-12 20:25:10 +137 -0 -> 42.365.169 probe"

    REAL_BIG = "V00000001 2026-09-26 11:35:39  +00001201 -00000000 ->               71.985"
    REAL_BIG_2 = "V00000002 2026-09-26 11:35:40  +00001201 -00000000 ->               71.190"

    def test_small_line_matches(self):
        m = VERSION_LINE_RE.match(self.REAL_SMALL)
        self.assertIsNotNone(m, "строка из фикстуры должна разбираться")
        self.assertEqual(int(m.group("num")), 1)
        self.assertEqual(m.group("date"), "2026-06-12")
        self.assertEqual(m.group("time"), "20:25:10")

    def test_four_digit_version_count_parsed(self):
        summary, versions = parse_info(
            f"2 versions, 2.402 files, 143.175 bytes\n{self.REAL_BIG}\n{self.REAL_BIG_2}\n"
        )
        self.assertEqual(summary.versions, 2)
        self.assertEqual(summary.files, 2402, "точечные разделители в сводке")
        self.assertEqual(summary.size, 143175)

        self.assertEqual(
            len(versions), 2, "версии с 1201 добавленными файлами должны разбираться"
        )
        self.assertEqual(versions[0].number, 1)
        self.assertEqual(versions[0].added, 1201, "числа с ведущими нулями")
        self.assertEqual(versions[0].removed, 0)
        self.assertEqual(versions[0].bytes_added, 71985, "точки в поле байт")
        self.assertEqual(versions[1].number, 2)
        self.assertEqual(versions[1].bytes_added, 71190)

    def test_removed_with_large_count(self):
        line = "V00000003 2026-09-26 12:00:00  +0 -00123456 ->                    1.234"
        m = VERSION_LINE_RE.match(line)
        self.assertIsNotNone(m)
        self.assertEqual(parse_size(m.group("removed")), 123456)

    def test_leading_zeros_in_version_number(self):
        line = "V00000123 2026-09-26 12:00:00  +1 -0 -> 10"
        summary, versions = parse_info(line)
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0].number, 123, "ведущие нули должны сниматься")

    def test_comment_is_captured(self):
        summary, versions = parse_info(self.REAL_SMALL)
        self.assertEqual(versions[0].comment, "probe")

    def test_line_without_comment(self):
        line = "V00000001 2026-09-26 11:35:39  +00001201 -00000000 ->               71.985"
        summary, versions = parse_info(line)
        self.assertEqual(versions[0].comment, "")

    def test_why_dot_separators_absent_here(self):
        self.assertIsNotNone(
            VERSION_LINE_RE.match(self.REAL_BIG),
            "формат с ведущими нулями обязан разбираться",
        )


        self.assertIsNone(
            VERSION_LINE_RE.match(
                "V1 2026-06-12 20:25:10 +1.201 -0 -> 42.365.169"
            ),
            "точечный разделитель в added движком не выдаётся, "
            "принимать его не нужно",
        )


class TestSummaryFormat(unittest.TestCase):


    def test_dotted_counts(self):
        s, _ = parse_info("1.064 versions, 119.064 files, 42.365.169 bytes")
        self.assertEqual(s.versions, 1064)
        self.assertEqual(s.files, 119064)
        self.assertEqual(s.size, 42365169)

    def test_plain_counts(self):
        s, _ = parse_info("2 versions, 137 files, 42.365.169 bytes")
        self.assertEqual(s.versions, 2)
        self.assertEqual(s.files, 137)

    def test_singular_and_plural(self):
        for text in ("1 version, 1 file, 1 byte",
                     "1 versions, 1 files, 1 bytes",
                     "2 versions, 2 files, 2 bytes"):
            with self.subTest(text=text):
                s, _ = parse_info(text)
                self.assertIsNotNone(s, f"не разобрано: {text}")

    def test_engine_always_uses_plural(self):

        s, _ = parse_info("1 versions, 2 files, 894 bytes (894.00  B)")
        self.assertIsNotNone(s)
        self.assertEqual(s.versions, 1)
        self.assertEqual(s.files, 2)
        self.assertEqual(s.size, 894)

    def test_bytes_with_kb_suffix(self):

        s, _ = parse_info("2 versions, 2.402 files, 143.175 bytes (139.82 KB)")
        self.assertEqual(s.size, 143175)


class TestParseSize(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(parse_size("42"), 42)

    def test_dotted(self):
        self.assertEqual(parse_size("42.365.169"), 42365169)

    def test_zero_padded(self):
        self.assertEqual(parse_size("00001201"), 1201)

    def test_empty_and_junk(self):
        self.assertEqual(parse_size(""), 0)
        self.assertEqual(parse_size("   "), 0)


class TestNoSilentVersionLoss(unittest.TestCase):

    def test_count_matches_input(self):
        lines = [
            "V00000001 2026-09-26 11:35:39  +00001201 -00000000 ->               71.985",
            "V00000002 2026-09-26 11:35:40  +00001201 -00000000 ->               71.190",
            "V00000003 2026-09-26 12:00:00  +00000001 -00123456 ->                1.234",
        ]
        summary, versions = parse_info("\n".join(lines))
        self.assertEqual(
            len(versions),
            len(lines),
            "число разобранных версий должно совпадать с числом строк",
        )


if __name__ == "__main__":
    unittest.main()
