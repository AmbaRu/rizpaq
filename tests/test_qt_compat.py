from __future__ import annotations

import unittest


try:
    from ui.qt_compat import (
        ARC_OWNER_ROLE,
        DATE_RAW_ROLE,
        K_ARC,
        K_ARC_DIR,
        K_ARC_FILE,
        K_FS,
        K_FS_ARC,
        K_FS_DIR,
        K_FS_FILE,
        K_PLACE,
        K_UP,
        KIND_ROLE,
        NAME_SORT_ROLE,
        SIZE_RAW_ROLE,
        USER_ROLE,
        VERSION_RAW_ROLE,
        multipart_pattern,
    )
    IMPORT_ERROR = None
except Exception as exc:
    IMPORT_ERROR = str(exc)


@unittest.skipIf(
    IMPORT_ERROR is not None,
    f"PySide6/ui.qt_compat import failed: {IMPORT_ERROR}",
)
class TestRoles(unittest.TestCase):
    def test_roles_are_unique(self):
        roles = [
            USER_ROLE,
            KIND_ROLE,
            ARC_OWNER_ROLE,
            SIZE_RAW_ROLE,
            DATE_RAW_ROLE,
            VERSION_RAW_ROLE,
            NAME_SORT_ROLE,
        ]

        self.assertEqual(len(roles), len(set(roles)))

    def test_roles_are_not_none(self):
        for role in (
            USER_ROLE,
            KIND_ROLE,
            ARC_OWNER_ROLE,
            SIZE_RAW_ROLE,
            DATE_RAW_ROLE,
            VERSION_RAW_ROLE,
            NAME_SORT_ROLE,
        ):
            self.assertIsNotNone(role)


@unittest.skipIf(
    IMPORT_ERROR is not None,
    f"PySide6/ui.qt_compat import failed: {IMPORT_ERROR}",
)
class TestKindConstants(unittest.TestCase):
    def test_kind_constants_are_unique(self):
        kinds = [
            K_FS,
            K_ARC,
            K_FS_ARC,
            K_PLACE,
            K_UP,
            K_FS_DIR,
            K_FS_FILE,
            K_ARC_DIR,
            K_ARC_FILE,
        ]

        self.assertEqual(len(kinds), len(set(kinds)))


@unittest.skipIf(
    IMPORT_ERROR is not None,
    f"PySide6/ui.qt_compat import failed: {IMPORT_ERROR}",
)
class TestMultipartPattern(unittest.TestCase):
    def test_plain_archive_not_changed(self):
        self.assertEqual(
            multipart_pattern(r"D:\backup.zpaq"),
            r"D:\backup.zpaq",
        )

    def test_multipart_part_replaced(self):
        self.assertEqual(
            multipart_pattern(r"D:\backup_0001.zpaq"),
            r"D:\backup_????.zpaq",
        )

    def test_multipart_part_uppercase_extension(self):
        self.assertEqual(
            multipart_pattern(r"D:\backup_0001.ZPAQ"),
            r"D:\backup_????.zpaq",
        )

    def test_five_digits_not_replaced(self):
        self.assertEqual(
            multipart_pattern(r"D:\backup_12345.zpaq"),
            r"D:\backup_12345.zpaq",
        )

    def test_three_digits_not_replaced(self):
        self.assertEqual(
            multipart_pattern(r"D:\backup_123.zpaq"),
            r"D:\backup_123.zpaq",
        )

    def test_no_underscore_not_replaced(self):
        self.assertEqual(
            multipart_pattern(r"D:\backup0001.zpaq"),
            r"D:\backup0001.zpaq",
        )

    def test_empty_path(self):
        self.assertEqual(multipart_pattern(""), "")

    def test_none_path(self):
        self.assertIsNone(multipart_pattern(None))


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
