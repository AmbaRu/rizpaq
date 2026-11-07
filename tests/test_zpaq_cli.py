


















from __future__ import annotations

import os
import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path

from core.zpaq_cli import (
    decode_bytes,
    looks_like_password_error,
    mask_secrets,
    safe_cmdline,
)


class TestDecodeBytes(unittest.TestCase):
    def test_utf8(self):
        data = "Привет, мир".encode("utf-8")
        self.assertEqual(decode_bytes(data), "Привет, мир")

    def test_empty(self):
        self.assertEqual(decode_bytes(b""), "")

    def test_invalid_bytes_do_not_raise(self):
        result = decode_bytes(b"\xff\xfe\x00\x01")
        self.assertIsInstance(result, str)


class TestSafeCmdline(unittest.TestCase):
    def test_password_masked(self):
        cmd = ["zpaqfranz", "x", "a.zpaq", "-key", "secret123"]
        text = safe_cmdline(cmd, "secret123")

        self.assertIn("***", text)
        self.assertNotIn("secret123", text)

    def test_without_password(self):
        cmd = ["zpaqfranz", "l", "a.zpaq"]
        text = safe_cmdline(cmd)

        self.assertIn("zpaqfranz", text)
        self.assertIn("a.zpaq", text)

    def test_7z_inline_password_masked(self):
        pass
        cmd = ["7z.exe", "l", "-slt", "a.zip", "-psecret123"]
        text = safe_cmdline(cmd, "secret123")

        self.assertNotIn("secret123", text)
        self.assertIn("-p***", text)

    def test_7z_inline_password_unmasked_in_gui_log(self):
        pass



        text = safe_cmdline(["7z.exe", "x", "a.zip", "-pS3cr3t"], "S3cr3t")
        self.assertNotIn("S3cr3t", text)


class TestMaskSecrets(unittest.TestCase):
    pass

    def test_key_flag_masks_next_argument(self):
        self.assertEqual(
            mask_secrets(["zpaqfranz", "-key", "s3cr3t", "a.zpaq"], "s3cr3t"),
            ["zpaqfranz", "-key", "***", "a.zpaq"],
        )

    def test_inline_prefix_form(self):
        self.assertEqual(
            mask_secrets(["7z.exe", "x", "a.zip", "-ps3cr3t"], "s3cr3t"),
            ["7z.exe", "x", "a.zip", "-p***"],
        )

    def test_exact_match_anywhere(self):
        self.assertEqual(
            mask_secrets(["7z.exe", "s3cr3t", "a.zip"], "s3cr3t"),
            ["7z.exe", "***", "a.zip"],
        )

    def test_does_not_clobber_similar_flags(self):
        pass




        cmd = ["7z.exe", "-preclean", "-pmysecret", "-psecret", "a.zip"]
        self.assertEqual(
            mask_secrets(cmd, "secret"),
            ["7z.exe", "-preclean", "-pmysecret", "-p***", "a.zip"],
        )

    def test_keeps_ordinary_arguments(self):
        cmd = ["zpaqfranz", "a", "out.zpaq", "src1", "src2", "-method", "5"]
        self.assertEqual(mask_secrets(cmd, None), cmd)

    def test_empty_and_none_safe(self):
        self.assertEqual(mask_secrets([], "s"), [])
        self.assertEqual(mask_secrets(None, "s"), [])

    def test_trailing_key_flag_does_not_crash(self):
        pass
        self.assertEqual(
            mask_secrets(["zpaqfranz", "-key"], "s3cr3t"),
            ["zpaqfranz", "-key"],
        )

    def test_source_path_equal_to_password_is_masked(self):
        pass
        cmd = ["zpaqfranz", "a", "out.zpaq", "topsecret", "topsecret2"]
        self.assertEqual(
            mask_secrets(cmd, "topsecret"),
            ["zpaqfranz", "a", "out.zpaq", "***", "topsecret2"],
        )

    def test_does_not_mutate_input(self):
        cmd = ["zpaqfranz", "-key", "s3cr3t"]
        mask_secrets(cmd, "s3cr3t")
        self.assertEqual(cmd, ["zpaqfranz", "-key", "s3cr3t"])


class TestLooksLikePasswordError(unittest.TestCase):
    def test_password_errors(self):
        self.assertTrue(looks_like_password_error("Wrong password"))
        self.assertTrue(looks_like_password_error("PASSWORD REQUIRED"))
        self.assertTrue(looks_like_password_error("crypt error"))
        self.assertTrue(looks_like_password_error("invalid key"))

    def test_normal_output(self):
        self.assertFalse(looks_like_password_error("All OK"))
        self.assertFalse(looks_like_password_error(""))


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
