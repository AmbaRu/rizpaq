import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from core.run_history import log_path_for
from core.startup_digest import DEFAULT_SINCE_DAYS, Digest, collect_digest

_NOW = datetime(2026, 11, 4, 12, 0, 0)


def _entry(text_block: str) -> str:
    return text_block + "=" * 50 + "\n\n"


def _run(ts: str, action: str = "backup", status: str = "OK",
         tail: str = "") -> str:
    st = f"Status: {status}"
    if status == "OK" or status == "BUSY":
        st = f"Status: {status}"
    else:
        st = f"Status: ERROR (rc=2)"
    tail_block = ""
    if tail:
        tail_block = "--- Last output lines ---\n" + tail + "\n"
    return (
        f"--- Rizpaq task run {ts} ---\n"
        f"Task file: D:\\tasks\\tasks.rzp\n"
        f"Work id:   w1\n"
        f"Work:      Docs\n"
        f"Job id:    j1\n"
        f"Job:       Daily\n"
        f"Action:    {action}\n"
        f"Return code: 0\n"
        f"{st}\n"
        f"{tail_block}"
    )


class StartupDigestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rizpaq_digest_"))
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_log(self, text: str) -> str:
        log = log_path_for(self.tmp)
        log.write_text(text, encoding="utf-8")
        return str(self.tmp)


    def test_counts_new_entries_since_last_close(self):

        log = (
            _entry(_run("2026-11-03 08:00:00"))
            + _entry(_run("2026-11-04 09:00:00"))
            + _entry(_run("2026-11-04 10:00:00", action="test",
                          status="ERROR", tail="par2: damaged"))
        )
        tasks = self._write_log(log)
        since = int(datetime(2026, 11, 3, 20, 0, 0).timestamp())
        d = collect_digest(tasks, since=since, now=_NOW)
        self.assertIsNotNone(d)
        self.assertEqual(d.backups_ok, 1)
        self.assertEqual(d.tests_err, 1)
        self.assertTrue(d.has_problem)
        self.assertIsNotNone(d.last_error)
        self.assertEqual(d.last_error.tail, ("par2: damaged",))
        self.assertEqual(len(d.entries), 2)

    def test_nothing_new_returns_none(self):
        log = _entry(_run("2026-11-01 08:00:00"))
        tasks = self._write_log(log)
        since = int(datetime(2026, 11, 3, 20, 0, 0).timestamp())
        self.assertIsNone(collect_digest(tasks, since=since, now=_NOW))

    def test_counts_busy_and_mixed_groups(self):
        log = (
            _entry(_run("2026-11-04 08:00:00", status="BUSY"))
            + _entry(_run("2026-11-04 09:00:00", action="test"))
            + _entry(_run("2026-11-04 09:30:00", action="test",
                          status="BUSY"))
            + _entry(_run("2026-11-04 10:30:00"))
        )
        tasks = self._write_log(log)
        since = int((_NOW - timedelta(hours=6)).timestamp())
        d = collect_digest(tasks, since=since, now=_NOW)
        self.assertEqual((d.backups_busy, d.backups_ok), (1, 1))
        self.assertEqual((d.tests_ok, d.tests_busy), (1, 1))
        self.assertTrue(d.has_problem)


    def test_no_since_defaults_to_week_window(self):

        old_ts = (_NOW - timedelta(days=DEFAULT_SINCE_DAYS + 1)
                  ).strftime("%Y-%m-%d %H:%M:%S")
        new_ts = (_NOW - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        log = _entry(_run(old_ts)) + _entry(_run(new_ts))
        tasks = self._write_log(log)
        d = collect_digest(tasks, since=None, now=_NOW)
        self.assertEqual(len(d.entries), 1)


        d2 = collect_digest(tasks, since="мусор", now=_NOW)
        self.assertEqual(len(d2.entries), 1)

    def test_since_older_than_all_returns_none(self):
        log = _entry(_run("2026-11-04 11:00:00"))
        tasks = self._write_log(log)

        since = int(_NOW.timestamp())
        self.assertIsNone(collect_digest(tasks, since=since, now=_NOW))


    def test_no_log_returns_none(self):
        self.assertIsNone(collect_digest(str(self.tmp), since=None,
                                         now=_NOW))
        self.assertIsNone(collect_digest(None, since=None, now=_NOW))
        self.assertIsNone(collect_digest(123, since=1, now=_NOW))

    def test_broken_timestamps_are_skipped(self):

        log = _entry("--- Rizpaq task run не время ---\nAction: backup\n") \
            + _entry(_run("2026-11-04 09:00:00"))
        tasks = self._write_log(log)
        since = int((_NOW - timedelta(hours=6)).timestamp())
        d = collect_digest(tasks, since=since, now=_NOW)
        self.assertEqual(len(d.entries), 1)
        self.assertEqual(d.backups_ok, 1)

    def test_digest_is_empty_flag(self):
        d = Digest()
        self.assertTrue(d.is_empty)
        self.assertFalse(d.has_problem)


if __name__ == "__main__":
    unittest.main()
