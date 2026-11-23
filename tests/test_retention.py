
from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from core import retention


class TestRetentionCommands(unittest.TestCase):
    def test_preview_and_apply(self):
        preview = retention.preview_cmd("zpaq", "F:/a.zpaq", "7d4w12my", "pw")
        self.assertEqual(preview, [
            "zpaq", "repack", "F:/a.zpaq", "7d4w12my", "-test",
            "-key", "pw",
        ])
        apply = retention.apply_cmd("zpaq", "F:/a.zpaq", "7d4w12my", "F:/t.zpaq")
        self.assertEqual(apply, [
            "zpaq", "repack", "F:/a.zpaq", "7d4w12my", "-to", "F:/t.zpaq",
        ])
        self.assertEqual(
            retention.verify_cmd("zpaq", "F:/t.zpaq"),
            ["zpaq", "i", "F:/t.zpaq"],
        )

    def test_policy_validation(self):
        self.assertTrue(retention.valid_policy("7d4w12my"))
        self.assertTrue(retention.valid_policy("10last"))
        self.assertFalse(retention.valid_policy(""))
        self.assertFalse(retention.valid_policy("a; rm -rf /"))


class TestRunApply(unittest.TestCase):
    def setUp(self):
        self._tmp = mock.Mock()
        import tempfile

        self._tmp = tempfile.TemporaryDirectory(prefix="retention_test_")
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.arc = self.dir / "a.zpaq"
        self.arc.write_bytes(b"original")

    def test_replaces_only_after_verify(self):
        seen = []

        def runner(cmd):
            seen.append(list(cmd))
            if cmd[1] == "repack":
                Path(cmd[cmd.index("-to") + 1]).write_bytes(b"new")
                return 0, "repack ok"
            return 0, "info ok"

        ok, text = retention.run_apply("zpaq", str(self.arc), "7d4w12my",
                                       runner=runner)
        self.assertTrue(ok)
        self.assertEqual(self.arc.read_bytes(), b"new")
        self.assertEqual([c[1] for c in seen], ["repack", "i"])
        self.assertIn("архив заменён", text)

    def test_verify_failure_keeps_original(self):
        def runner(cmd):
            if cmd[1] == "repack":
                Path(cmd[cmd.index("-to") + 1]).write_bytes(b"new")
                return 0, "repack ok"
            return 1, "info failed"

        ok, text = retention.run_apply("zpaq", str(self.arc), "7d4w12my",
                                       runner=runner)
        self.assertFalse(ok)
        self.assertEqual(self.arc.read_bytes(), b"original")
        self.assertIn("info failed", text)

    def test_repack_failure_keeps_original(self):
        def runner(cmd):
            return 2, "repack failed"

        ok, _text = retention.run_apply("zpaq", str(self.arc), "7d4w12my",
                                        runner=runner)
        self.assertFalse(ok)
        self.assertEqual(self.arc.read_bytes(), b"original")


if __name__ == "__main__":
    unittest.main()
