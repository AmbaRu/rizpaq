from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from core.paths import (
    find_extracted_path,
    is_inside,
    is_root,
    is_temp_path,
    is_top_level_drive,
    merge_tree,
    nearest_existing,
    retarget_path,
    same_name,
    sanitize_filename,
    valid_filename,
)


SYSTEM_ROOT = os.environ.get("SystemRoot", "C:\\Windows")


class TestSanitizeFilename(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(sanitize_filename(""), "extracted")

    def test_drive_letter(self):
        self.assertEqual(sanitize_filename("d:"), "D")
        self.assertEqual(sanitize_filename("D:"), "D")

    def test_invalid_chars_replaced(self):
        name = sanitize_filename('a:b*c?d"e<f>g|h')
        self.assertNotIn(":", name)
        self.assertNotIn("*", name)
        self.assertNotIn("?", name)
        self.assertNotIn('"', name)
        self.assertNotIn("<", name)
        self.assertNotIn(">", name)
        self.assertNotIn("|", name)

    def test_reserved_names(self):
        self.assertTrue(sanitize_filename("CON").startswith("_"))
        self.assertTrue(sanitize_filename("com1.txt").startswith("_"))

    def test_normal_name_kept(self):
        self.assertEqual(sanitize_filename("отчёт 2026.txt"), "отчёт 2026.txt")


class TestIsTopLevelDrive(unittest.TestCase):
    def test_bare_drive(self):
        self.assertTrue(is_top_level_drive("d:"))
        self.assertTrue(is_top_level_drive("D:"))

    def test_drive_with_slash(self):
        self.assertTrue(is_top_level_drive("d:/"))
        self.assertTrue(is_top_level_drive("D:\\"))

    def test_not_top_level(self):
        self.assertFalse(is_top_level_drive("d:/111"))
        self.assertFalse(is_top_level_drive("d:\\111"))
        self.assertFalse(is_top_level_drive("d:/111/222"))


class TestIsRoot(unittest.TestCase):
    def test_drive_root(self):
        self.assertTrue(is_root("C:\\"))
        self.assertTrue(is_root("c:/"))
        self.assertTrue(is_root("C:"))

    def test_posix_root(self):
        self.assertTrue(is_root("/"))

    def test_unc_root(self):
        self.assertTrue(is_root(r"\\server\share"))

    def test_not_root(self):
        self.assertFalse(is_root("C:\\data"))
        self.assertFalse(is_root("C:\\data\\sub"))
        self.assertFalse(is_root("/home"))


class TestIsInside(unittest.TestCase):
    def test_inside(self):
        self.assertTrue(is_inside(r"C:\data\sub\a.txt", r"C:\data"))

    def test_case_insensitive(self):
        self.assertTrue(is_inside(r"c:\DATA\sub\a.txt", r"C:\data"))

    def test_slashes(self):
        self.assertTrue(is_inside("C:/data/sub", "C:\\data"))

    def test_not_inside_self(self):
        self.assertFalse(is_inside(r"C:\data", r"C:\data"))

    def test_not_inside_sibling(self):
        self.assertFalse(is_inside(r"C:\data2\a.txt", r"C:\data"))

    def test_not_inside_drive_root_prefix(self):
        self.assertTrue(is_inside(r"C:\data", "C:\\"))
        self.assertFalse(is_inside("C:\\", r"C:\data"))

    def test_different_drives(self):
        self.assertFalse(is_inside(r"D:\data", r"C:\data"))


class TestNearestExisting(unittest.TestCase):
    @unittest.skipUnless(os.path.isdir(SYSTEM_ROOT), "Requires Windows system root")
    def test_existing_path(self):
        self.assertTrue(
            same_name(
                str(nearest_existing(SYSTEM_ROOT)),
                SYSTEM_ROOT,
            )
        )

    @unittest.skipUnless(os.path.isdir(SYSTEM_ROOT), "Requires Windows system root")
    def test_missing_child_falls_back_to_existing(self):
        missing = os.path.join(SYSTEM_ROOT, "no_such_dir_rizpaq_test", "deeper")
        self.assertTrue(
            same_name(
                str(nearest_existing(missing)),
                SYSTEM_ROOT,
            )
        )

    def test_missing_drive(self):
        self.assertIsNone(nearest_existing(r"Q:\nope"))


class TestValidFilename(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(valid_filename("otchet.zpaq"))
        self.assertTrue(valid_filename("Архив 2026.zpaq"))
        self.assertTrue(valid_filename("a.b.c.txt"))

    def test_empty_and_dots(self):
        self.assertFalse(valid_filename(""))
        self.assertFalse(valid_filename("   "))
        self.assertFalse(valid_filename("."))
        self.assertFalse(valid_filename(".."))

    def test_invalid_chars(self):
        bad_names = (
            "a<b",
            "a>b",
            "a:b",
            'a"b',
            "a/b",
            "a\\b",
            "a|b",
            "a?b",
            "a*b",
        )

        for bad in bad_names:
            self.assertFalse(valid_filename(bad), bad)

    def test_trailing_dot_space(self):
        self.assertFalse(valid_filename("name."))
        self.assertTrue(valid_filename("name "))

    def test_reserved(self):
        self.assertFalse(valid_filename("CON"))
        self.assertFalse(valid_filename("com1.txt"))
        self.assertTrue(valid_filename("console.txt"))


class TestRetargetPath(unittest.TestCase):
    def test_same_path(self):
        self.assertEqual(
            retarget_path(
                r"C:\data\arc.zpaq",
                r"C:\Data\arc.zpaq",
                r"C:\data\new.zpaq",
            ),
            r"C:\data\new.zpaq",
        )

    def test_inside(self):
        self.assertEqual(
            retarget_path(
                r"C:\data\sub\arc.zpaq",
                r"C:\Data",
                r"C:\newdata",
            ),
            os.path.join(r"C:\newdata", "sub", "arc.zpaq"),
        )

    def test_unrelated(self):
        self.assertIsNone(retarget_path(r"D:\x", r"C:\data", r"C:\newdata"))

    def test_sibling_prefix(self):
        self.assertIsNone(
            retarget_path(r"C:\data2\a", r"C:\data", r"C:\newdata")
        )


class TestIsTempPath(unittest.TestCase):
    def test_tempdir_itself(self):
        self.assertTrue(is_temp_path(tempfile.gettempdir()))
        self.assertTrue(
            is_temp_path(os.path.join(tempfile.gettempdir(), "x", "y"))
        )

    def test_not_temp(self):
        self.assertFalse(is_temp_path(SYSTEM_ROOT))
        self.assertFalse(is_temp_path(tempfile.gettempdir() + "_suffix"))


class TestSameName(unittest.TestCase):
    def test_case(self):
        self.assertTrue(same_name("AbC.txt", "abc.txt"))


class TestFindExtractedPath(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="rizpaq_paths_test_"))

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def _touch(self, path: Path, text: str = "x") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_empty_inner_returns_root(self):
        self.assertEqual(find_extracted_path(self.base, ""), self.base)

    def test_direct_drive_underscore(self):
        target = self.base / "d_" / "1" / "2" / "4"
        self._touch(target / "file.txt")

        found = find_extracted_path(self.base, "d:/1/2/4", want_dir=True)
        self.assertIsNotNone(found)
        self.assertEqual(Path(found), target)

    def test_inner_with_backslashes(self):
        target = self.base / "d_" / "1" / "2" / "4"
        self._touch(target / "file.txt")

        found = find_extracted_path(self.base, "d:\\1\\2\\4", want_dir=True)
        self.assertIsNotNone(found)
        self.assertEqual(Path(found), target)

    def test_case_insensitive_suffix(self):
        target = self.base / "D_" / "A" / "B"
        self._touch(target / "file.txt")

        found = find_extracted_path(self.base, "d:/a/b", want_dir=True)
        self.assertIsNotNone(found)
        self.assertEqual(Path(found), target)

    def test_want_dir_false_finds_file(self):
        file_path = self.base / "d_" / "1" / "2" / "4" / "file.txt"
        self._touch(file_path)

        found = find_extracted_path(
            self.base,
            "d:/1/2/4/file.txt",
            want_dir=False,
        )

        self.assertIsNotNone(found)
        self.assertEqual(Path(found), file_path)

    def test_want_dir_true_does_not_return_file(self):
        file_path = self.base / "d_" / "1" / "2" / "4" / "file.txt"
        self._touch(file_path)

        found = find_extracted_path(
            self.base,
            "d:/1/2/4/file.txt",
            want_dir=True,
        )

        self.assertIsNone(found)


class TestMergeTree(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="rizpaq_merge_test_"))

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_move_to_missing_dest(self):
        src = self.base / "src"
        dest = self.base / "dest"

        (src / "sub").mkdir(parents=True)
        (src / "sub" / "file.txt").write_text("hello", encoding="utf-8")

        merge_tree(src, dest)

        self.assertFalse(src.exists())
        self.assertTrue((dest / "sub" / "file.txt").is_file())

    def test_move_to_empty_dest(self):
        src = self.base / "src"
        dest = self.base / "dest"

        src.mkdir(parents=True)
        dest.mkdir(parents=True)

        (src / "file.txt").write_text("hello", encoding="utf-8")

        merge_tree(src, dest)

        self.assertFalse(src.exists())
        self.assertTrue((dest / "file.txt").is_file())

    def test_merge_into_non_empty_dest(self):
        src = self.base / "src"
        dest = self.base / "dest"

        src.mkdir(parents=True)
        dest.mkdir(parents=True)

        (dest / "old.txt").write_text("old", encoding="utf-8")
        (dest / "common.txt").write_text("old-common", encoding="utf-8")

        (src / "new.txt").write_text("new", encoding="utf-8")
        (src / "common.txt").write_text("new-common", encoding="utf-8")

        merge_tree(src, dest)

        self.assertFalse(src.exists())

        self.assertTrue((dest / "old.txt").is_file())
        self.assertTrue((dest / "new.txt").is_file())
        self.assertEqual(
            (dest / "common.txt").read_text(encoding="utf-8"),
            "new-common",
        )

    def test_dest_file_raises(self):
        src = self.base / "src"
        dest_file = self.base / "dest.txt"

        src.mkdir(parents=True)
        dest_file.write_text("file", encoding="utf-8")

        with self.assertRaises(NotADirectoryError):
            merge_tree(src, dest_file)


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
