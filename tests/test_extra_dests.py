
from __future__ import annotations

import os
import unittest

from core import extra_dests, tasks


class TestPrepareDests(unittest.TestCase):
    def test_dedup_and_skip_main(self):
        main = "F:/All.zpaq"
        result = extra_dests.prepare_dests(main, [
            " F:/second.zpaq ",
            "F:/All.zpaq",
            "F:/second.zpaq",
            "",
            "F:/third.zpaq",
        ])
        self.assertEqual(result, ["F:/second.zpaq", "F:/third.zpaq"])

    def test_empty(self):
        self.assertEqual(extra_dests.prepare_dests("F:/a.zpaq", []), [])


class TestRunner(unittest.TestCase):
    def test_runs_each_dest_and_aggregates(self):
        calls = []

        def build_cmd(zpaq, settings, srcs, dest, password):
            calls.append(dest)
            return ["zpaq", "a", dest]

        def runner(cmd):
            return (2 if cmd[2].endswith("bad.zpaq") else 0), "log " + cmd[2]

        ok, log = extra_dests.run_extra_dests(
            "zpaq", {"level": []}, ["D:/src"],
            ["F:/one.zpaq", "F:/bad.zpaq"],
            build_cmd=build_cmd, runner=runner,
        )
        self.assertEqual(calls, ["F:/one.zpaq", "F:/bad.zpaq"])
        self.assertFalse(ok)
        self.assertIn("extra archive", log)
        self.assertIn("log F:/one.zpaq", log)

    def test_exception_from_build_is_reported(self):
        def bad_build(*a, **kw):
            raise RuntimeError("boom")

        ok, log = extra_dests.run_extra_dests(
            "zpaq", {}, [], ["F:/x.zpaq"],
            build_cmd=bad_build, runner=lambda cmd: (0, ""),
        )
        self.assertFalse(ok)
        self.assertIn("boom", log)


class TestContainerField(unittest.TestCase):
    def test_work_normalization_keeps_extra_dests(self):
        raw = {
            "id": "w1",
            "title": "Work",
            "sources": ["D:/src"],
            "dest": "F:/a.zpaq",
            "extra_dests": ["F:/b.zpaq", " "],
        }
        work = tasks._normalise_work(raw)
        self.assertEqual(work["extra_dests"], ["F:/b.zpaq"])
        settings = tasks.job_to_runnable_settings(work, {"id": "j1"})
        self.assertEqual(settings["extra_dests"], ["F:/b.zpaq"])


if __name__ == "__main__":
    unittest.main()
