import tempfile
import unittest
from pathlib import Path

from core.run_history import log_path_for, load_history, parse_log

_SAMPLE = """--- Rizpaq task run 2026-10-26 10:00:00.100000 ---
Task file: D:\\tasks\\tasks.rzp
Work id:   w1
Work:      Docs
Job id:    j1
Job:       Daily backup
Action:    backup
Return code: 0
Status: OK
==================================================

--- Rizpaq task run 2026-10-26 11:00:00.000000 ---
Task file: D:\\tasks\\tasks.rzp
Work id:   w1
Work:      Docs
Job id:    j2
Job:       Verify
Action:    test
Return code: 2
Status: ERROR (rc=2)
--- Last output lines ---
error line one
error line two
==================================================

--- Rizpaq task run 2026-10-26 12:00:00.500000 ---
Task file: D:\\tasks\\tasks.rzp
Work id:   w2
Work:      Photos
Job id:    j3
Job:       Nightly
Action:    backup
Return code: 0
==================================================

"""

_FULL_MODE = """--- Rizpaq task run 2026-10-26 13:00:00.000000 ---
Task file: D:\\tasks\\tasks.rzp
Work id:   w9
Work:      Big
Job id:    j9
Job:       Full log run
Action:    backup
Return code: 3
some engine output line
another engine output line
==================================================
"""


class TestParseLog(unittest.TestCase):
    def test_newest_first(self):
        entries = parse_log(_SAMPLE)
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].job_id, "j3")
        self.assertEqual(entries[-1].job_id, "j1")

    def test_fields(self):
        e = parse_log(_SAMPLE)[-1]
        self.assertEqual(e.work_id, "w1")
        self.assertEqual(e.work_title, "Docs")
        self.assertEqual(e.job_id, "j1")
        self.assertEqual(e.job_title, "Daily backup")
        self.assertEqual(e.action, "backup")
        self.assertEqual(e.rc, 0)
        self.assertEqual(e.status, "ok")
        self.assertEqual(e.ts, "2026-10-26 10:00:00.100000")

    def test_error_tail(self):
        e = parse_log(_SAMPLE)[1]
        self.assertEqual(e.status, "error")
        self.assertEqual(e.rc, 2)
        self.assertEqual(e.tail, ("error line one", "error line two"))

    def test_full_mode_rc_fallback(self):

        bad = parse_log(_FULL_MODE)[0]
        self.assertEqual(bad.status, "error")
        self.assertEqual(bad.rc, 3)
        ok_text = _FULL_MODE.replace("Return code: 3", "Return code: 0")
        good = parse_log(ok_text)[0]
        self.assertEqual(good.status, "ok")

    def test_empty_and_garbage(self):
        self.assertEqual(parse_log(""), [])
        self.assertEqual(parse_log("мусор без заголовков\n===\n"), [])

        weird = _SAMPLE + "--- Rizpaq task run 2026-10-27 09:00:00 ---\n???\n"
        self.assertEqual(len(parse_log(weird)), 4)

    def test_load_history_missing_log(self):

        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_history(tmp), [])
            self.assertTrue(
                str(log_path_for(tmp)).endswith(".rzp.log")
            )

    def test_load_history_reads_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = log_path_for(tmp)
            log.write_text(_SAMPLE, encoding="utf-8")
            entries = load_history(tmp)
            self.assertEqual(len(entries), 3)
            self.assertEqual(entries[0].job_id, "j3")
            limited = load_history(tmp, limit=1)
            self.assertEqual([e.job_id for e in limited], ["j3"])


if __name__ == "__main__":
    unittest.main()
