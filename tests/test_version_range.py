







from __future__ import annotations

import unittest

from core.index_refresh import build_list_cmd
from core.version_range import expand_range, is_valid_range, normalize_range


class TestNormalizeRange(unittest.TestCase):
    def test_examples_from_documentation(self):
        for text in ("2:5", "::3", "4", "2:", ":5", "2::5"):
            with self.subTest(text=text):
                self.assertEqual(normalize_range(text), text)
                self.assertTrue(is_valid_range(text))

    def test_whitespace_is_stripped(self):
        self.assertEqual(normalize_range("  2:5 \n"), "2:5")

    def test_empty_means_no_filter(self):
        self.assertIsNone(normalize_range(""))
        self.assertIsNone(normalize_range("   "))
        self.assertIsNone(normalize_range(None))
        self.assertFalse(is_valid_range(""))

    def test_rejects_anything_else(self):
        bad = (
            "2:5 -to C:\\", "2;5", "abc", "2:5:6:7", ":" * 3,
            "x" * 33, "2:5; echo hi", "--range", "2 -key pw",
        )
        for text in bad:
            with self.subTest(text=text):
                self.assertIsNone(normalize_range(text))
                self.assertFalse(is_valid_range(text))


class TestListCommandRange(unittest.TestCase):
    FLAGS = ["-all", "-terse", "-csv", "\t", "-csvhf", "#", "-utf", "-noeta"]

    def test_no_range_by_default(self):
        self.assertEqual(
            build_list_cmd("z", "a.zpaq", "pw"),
            ["z", "l", "a.zpaq", *self.FLAGS, "-key", "pw"],
        )

    def test_range_goes_before_password(self):
        self.assertEqual(
            build_list_cmd("z", "downloads_????.zpaq", "pw", "2:5"),
            ["z", "l", "downloads_????.zpaq", *self.FLAGS,
             "-range", "2:5", "-key", "pw"],
        )

    def test_range_without_password(self):
        self.assertEqual(
            build_list_cmd("z", "a.zpaq", None, "::3"),
            ["z", "l", "a.zpaq", *self.FLAGS, "-range", "::3"],
        )


class TestExpandRange(unittest.TestCase):
    VERSIONS = [1, 2, 3, 4, 5]

    def test_single_version(self):
        self.assertEqual(expand_range("4", self.VERSIONS), [4])

    def test_closed_interval(self):
        self.assertEqual(expand_range("2:4", self.VERSIONS), [2, 3, 4])

    def test_open_ends(self):
        self.assertEqual(expand_range("3:", self.VERSIONS), [3, 4, 5])
        self.assertEqual(expand_range(":2", self.VERSIONS), [1, 2])

    def test_last_n(self):
        self.assertEqual(expand_range("::3", self.VERSIONS), [3, 4, 5])

    def test_only_existing_versions(self):
        self.assertEqual(expand_range("2:9", self.VERSIONS), [2, 3, 4, 5])
        self.assertEqual(expand_range("7:9", self.VERSIONS), [])

    def test_bad_spec_or_empty_archive(self):
        self.assertEqual(expand_range("abc", self.VERSIONS), [])
        self.assertEqual(expand_range("", self.VERSIONS), [])
        self.assertEqual(expand_range("2:5", []), [])


if __name__ == "__main__":
    unittest.main()
