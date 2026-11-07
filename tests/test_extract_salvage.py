












from __future__ import annotations

import unittest


try:
    from workers.extract_workers import ExtractSalvageWorker
    IMPORT_ERROR = None
except Exception as exc:
    ExtractSalvageWorker = None
    IMPORT_ERROR = str(exc)


@unittest.skipIf(
    ExtractSalvageWorker is None,
    f"PySide6/workers import failed: {IMPORT_ERROR}",
)
class TestSalvageCmd(unittest.TestCase):
    def _cmd(self, password=None, ram_gb=None):
        w = ExtractSalvageWorker(
            "zpaqfranz", "a.zpaq", password, "out", ram_gb
        )
        return w.cmd

    def test_plain(self):
        self.assertEqual(
            self._cmd(),
            ["zpaqfranz", "xx", "a.zpaq", "-force", "-to", "out"],
        )

    def test_password(self):
        self.assertEqual(
            self._cmd(password="pw"),
            [
                "zpaqfranz",
                "xx",
                "a.zpaq",
                "-key",
                "pw",
                "-force",
                "-to",
                "out",
            ],
        )

    def test_ramsize(self):
        self.assertEqual(
            self._cmd(ram_gb=4),
            [
                "zpaqfranz",
                "xx",
                "a.zpaq",
                "-force",
                "-ramsize",
                "4GB",
                "-to",
                "out",
            ],
        )

    def test_no_only_no_until(self):
        cmd = self._cmd(ram_gb=2)
        self.assertNotIn("-only", cmd)
        self.assertNotIn("-until", cmd)

    def test_force_always(self):
                                                                          
        for kwargs in ({}, {"password": "p"}, {"ram_gb": 8}):
            self.assertIn("-force", self._cmd(**kwargs))

    def test_to_points_to_dest(self):
                                                                       
                                                                       
        cmd = self._cmd()
        i = cmd.index("-to")
        self.assertEqual(cmd[i + 1], "out")

    def test_done_dict_shape(self):
                                                                  
                                                                     
        w = ExtractSalvageWorker("zpaqfranz", "a.zpaq", None, "out", 1)
        self.assertEqual(w.dest_folder, "out")
        self.assertEqual(w.ram_gb, 1)


if __name__ == "__main__":
    unittest.main()
