







from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.headless import _build_create_cmd
from core.zpaq_cli import (
    APPEND_CHECK,
    APPEND_MIN_FREE,
    archive_exists,
    checksize_bytes,
    checksize_for_append,
    checksize_text,
    resolve_checksize,
)

GIB = 1 << 30


class TestChecksizeParsing(unittest.TestCase):
    def test_bytes_from_units(self):
        self.assertEqual(checksize_bytes("10G"), 10 * GIB)
        self.assertEqual(checksize_bytes("500M"), 500 << 20)
        self.assertEqual(checksize_bytes("1T"), 1 << 40)
        self.assertEqual(checksize_bytes("1024"), 1024)
        self.assertEqual(checksize_bytes("1,5G"), int(1.5 * GIB))

    def test_bytes_bad_input(self):
        for bad in ("", None, "abc", "G"):
            self.assertEqual(checksize_bytes(bad), 0)

    def test_text_roundtrip(self):
        self.assertEqual(checksize_text(10 * GIB), "10G")
        self.assertEqual(checksize_text(GIB), "1G")
        self.assertEqual(checksize_text(500 << 20), "500M")

    def test_text_decimal(self):
        value = checksize_bytes("222.59G")
        self.assertEqual(checksize_text(value), "222.59G")


class TestChecksizeForAppend(unittest.TestCase):
    def test_default_floor(self):
        self.assertEqual(checksize_for_append(""), APPEND_CHECK)
        self.assertEqual(checksize_for_append("222.59G"), APPEND_CHECK)

    def test_smaller_user_value_kept(self):
        self.assertEqual(checksize_for_append("500M"), "500M")


class TestResolveChecksize(unittest.TestCase):
    def test_empty_means_no_flag(self):
        self.assertEqual(resolve_checksize("", "F:/a.zpaq"), "")

    def test_new_archive_keeps_full_value(self):
        with mock.patch("core.zpaq_cli.shutil.disk_usage") as usage:
            usage.return_value = mock.Mock(free=200 * GIB)
            self.assertEqual(
                resolve_checksize("222.59G", "F:/a.zpaq", is_update=False),
                "222.59G",
            )
            usage.assert_not_called()

    def test_append_with_room_uses_floor(self):
        with mock.patch("core.zpaq_cli.shutil.disk_usage") as usage:
            usage.return_value = mock.Mock(free=138 * GIB)
            self.assertEqual(
                resolve_checksize("222.59G", "F:/a.zpaq", is_update=True),
                APPEND_CHECK,
            )

    def test_append_on_full_disk_keeps_requirement(self):
        with mock.patch("core.zpaq_cli.shutil.disk_usage") as usage:
            usage.return_value = mock.Mock(free=APPEND_MIN_FREE // 2)
            self.assertEqual(
                resolve_checksize("222.59G", "F:/a.zpaq", is_update=True),
                "222.59G",
            )

    def test_unknown_free_space_keeps_requirement(self):
        with mock.patch("core.zpaq_cli.shutil.disk_usage") as usage:
            usage.side_effect = OSError("no such path")
            self.assertEqual(
                resolve_checksize("222.59G", r"\\server\share\a.zpaq", True),
                "222.59G",
            )


class TestArchiveExists(unittest.TestCase):
    def test_real_file(self):
        fd, path = tempfile.mkstemp(suffix=".zpaq")
        os.close(fd)
        try:
            self.assertTrue(archive_exists(path))
        finally:
            os.unlink(path)

    def test_chunk_template_and_missing(self):
        self.assertFalse(archive_exists("F:/a_????.zpaq"))
        self.assertFalse(archive_exists(""))
        self.assertFalse(archive_exists("F:/no-such-archive.zpaq"))


class TestBuildCreateCmd(unittest.TestCase):
    def _settings(self, checkspace):
        return {"level": [], "checkspace": checkspace}

    def test_new_archive_gets_full_requirement(self):
        dest = Path(tempfile.gettempdir()) / "rizpaq_new_test.zpaq"
        if dest.exists():
            dest.unlink()
        cmd = _build_create_cmd(
            "zpaqfranz", self._settings("222.59G"), ["D:/src"], str(dest), None
        )
        self.assertIn("-checksize", cmd)
        self.assertEqual(cmd[cmd.index("-checksize") + 1], "222.59G")

    def test_existing_archive_gets_floor(self):
        fd, path = tempfile.mkstemp(suffix=".zpaq")
        os.close(fd)
        try:
            cmd = _build_create_cmd(
                "zpaqfranz", self._settings("222.59G"), ["D:/src"], path, None
            )
            self.assertIn("-checksize", cmd)
            self.assertEqual(cmd[cmd.index("-checksize") + 1], APPEND_CHECK)
        finally:
            os.unlink(path)

    def test_no_checkspace_no_flag(self):
        cmd = _build_create_cmd(
            "zpaqfranz", self._settings(""), ["D:/src"], "F:/a.zpaq", None
        )
        self.assertNotIn("-checksize", cmd)


class TestDialogAutoValue(unittest.TestCase):
    def test_auto_value_for_append(self):
        from ui.archive_create_dialog import _auto_checksize

        self.assertEqual(_auto_checksize(200 * GIB, True), APPEND_CHECK)

    def test_auto_value_for_new_archive(self):
        from ui.archive_create_dialog import _auto_checksize

        value = _auto_checksize(200 * GIB, False)
        self.assertNotEqual(value, APPEND_CHECK)
        self.assertGreater(checksize_bytes(value), 200 * GIB)


if __name__ == "__main__":
    unittest.main()
