from __future__ import annotations

import unittest


try:
    from workers.extract_workers import ExtractFileWorker, ExtractFolderBatchWorker
    IMPORT_ERROR = None
except Exception as exc:
    ExtractFileWorker = None
    ExtractFolderBatchWorker = None
    IMPORT_ERROR = str(exc)


@unittest.skipIf(
    ExtractFileWorker is None,
    f"PySide6/workers import failed: {IMPORT_ERROR}",
)
class TestExtractFileWorkerCmd(unittest.TestCase):
    def test_plain(self):
        w = ExtractFileWorker(
            "zpaqfranz",
            "a.zpaq",
            None,
            "src/f.txt",
            None,
            r"D:\out\f.txt",
        )

        self.assertEqual(
            w.cmd,
            ["zpaqfranz", "x", "a.zpaq", "src/f.txt", "-to", r"D:\out\f.txt"],
        )

    def test_password_and_version(self):
        w = ExtractFileWorker(
            "z",
            "a.zpaq",
            "pw",
            "src/f.txt",
            3,
            r"D:\o\f.txt",
        )

        self.assertEqual(
            w.cmd,
            [
                "z",
                "x",
                "a.zpaq",
                "-key",
                "pw",
                "src/f.txt",
                "-until",
                "3",
                "-to",
                r"D:\o\f.txt",
            ],
        )

    def test_no_only_flag(self):


        w = ExtractFileWorker("z", "a.zpaq", None, "f.txt", None, "o.txt")
        self.assertNotIn("-only", w.cmd)


@unittest.skipIf(
    ExtractFolderBatchWorker is None,
    f"PySide6/workers import failed: {IMPORT_ERROR}",
)
class TestExtractFolderBatchWorkerCmd(unittest.TestCase):
    def test_with_prefix(self):
        w = ExtractFolderBatchWorker(
            "z",
            "a.zpaq",
            None,
            "C:/data/src",
            None,
            r"D:\out",
        )

        self.assertEqual(
            w.cmd,
            [
                "z",
                "x",
                "a.zpaq",
                "-only",
                "C:/data/src/*",
                "-to",
                r"D:\out",
            ],
        )


        self.assertNotIn("-find", w.cmd)
        self.assertNotIn("-replace", w.cmd)

    def test_without_prefix_no_find(self):
        w = ExtractFolderBatchWorker("z", "a.zpaq", None, "", None, r"D:\out")

        self.assertEqual(
            w.cmd,
            ["z", "x", "a.zpaq", "-only", "*", "-to", r"D:\out"],
        )

        self.assertNotIn("-find", w.cmd)
        self.assertNotIn("-replace", w.cmd)

    def test_version_and_password(self):
        w = ExtractFolderBatchWorker("z", "a.zpaq", "pw", "P", 2, r"D:\o")

        self.assertEqual(
            w.cmd,
            [
                "z",
                "x",
                "a.zpaq",
                "-key",
                "pw",
                "-only",
                "P/*",
                "-until",
                "2",
                "-to",
                r"D:\o",
            ],
        )

        self.assertIn("-until", w.cmd)
        self.assertEqual(w.cmd[w.cmd.index("-until") + 1], "2")
        self.assertEqual(w.cmd[w.cmd.index("-key") + 1], "pw")


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
