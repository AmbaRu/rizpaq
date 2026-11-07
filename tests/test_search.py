






from __future__ import annotations

import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.search import match_query


class TestMatchQuery(unittest.TestCase):
    def test_empty_matches_everything(self):
        self.assertTrue(match_query("", "d:/any/path.txt"))

    def test_whitespace_only_matches_everything(self):
        self.assertTrue(match_query("   ", "d:/any/path.txt"))

    def test_none_query_matches_everything(self):
        self.assertTrue(match_query(None, "d:/any/path.txt"))

    def test_substring_case_insensitive(self):
        self.assertTrue(match_query("PATH", "d:/some/Path/file.txt"))
        self.assertTrue(match_query("file", "d:/some/path/FILE.TXT"))

    def test_substring_over_full_path_cyrillic(self):
        self.assertTrue(match_query("налоги", "d:/Таня/НАЛОГИ, отчеты/x.xlsx"))

    def test_no_match(self):
        self.assertFalse(match_query("zzz", "d:/some/path.txt"))

    def test_glob_star_extension(self):
        self.assertTrue(match_query("*.jpg", "d:/photo/sneg.JPG"))
        self.assertFalse(match_query("*.jpg", "d:/photo/sneg.png"))

    def test_glob_star_middle_cyrillic(self):
        self.assertTrue(match_query("*школа*", "d:/Dasha/школа.jpg"))
        self.assertFalse(match_query("*школа*", "d:/Dasha/работа.doc"))

    def test_glob_question_mark(self):
                                                                   
        self.assertTrue(match_query("file?.txt", "d:/file1.txt"))
        self.assertFalse(match_query("file?.txt", "d:/file12.txt"))

    def test_glob_also_matches_folder_prefix(self):
                                                                           
        self.assertTrue(match_query("d:/tan/*", "d:/tan/x.txt"))
        self.assertTrue(match_query("*/отчеты/*", "d:/Таня/отчеты/x.xlsx"))

    def test_query_is_stripped(self):
        self.assertTrue(match_query("  path  ", "d:/some/path/x"))


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
