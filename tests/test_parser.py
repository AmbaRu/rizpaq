from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path


_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.parser import clean_csv_line, parse_csv_list, parse_info, parse_size


LIST_ALL = "07_list_all_terse_csv_tab_csvhf_utf.txt"
LIST_LAST = "08_list_last_terse_csv_tab_csvhf_utf.txt"
INFO = "01_info_comment.txt"


def _candidate_dirs() -> list:
    roots = [_HERE]
    p = _HERE
    for _ in range(6):
        p = p.parent
        roots.append(p)
    extras = [
        "probe_out",
        "zpaq_gui_probe",
        os.path.join("zpaq_gui_probe", "probe_out"),
    ]
    dirs = []
    env = os.environ.get("ZPAQ_PROBE_DIR")
    if env:
        dirs.append(Path(env))
    for r in roots:
        dirs.append(r)
        for ex in extras:
            dirs.append(r / ex)
    return dirs


def _locate(names) -> dict:
    found = {}
    for n in names:
        for d in _candidate_dirs():
            f = d / n
            if f.is_file():
                found[n] = f
                break
    return found


PROBE = _locate([LIST_ALL, LIST_LAST, INFO])
HAVE_ALL = LIST_ALL in PROBE
HAVE_LAST = LIST_LAST in PROBE
HAVE_INFO = INFO in PROBE


def _read(name: str) -> str:
    return PROBE[name].read_text(encoding="utf-8", errors="replace")


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


def _raw_data_lines(text: str) -> list:
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cleaned = clean_csv_line(line)
        if _DATE_RE.match(cleaned):
            out.append((line, cleaned))
    return out


def _analyze_skips(text: str) -> list:
    skipped = []
    for raw, cleaned in _raw_data_lines(text):
        parts = cleaned.split("\t")
        if len(parts) == 7:
            path = parts[6].strip()
            if not path:
                skipped.append((raw, cleaned, "empty_path"))
                continue
            try:
                int(parts[4])
            except ValueError:
                skipped.append((raw, cleaned, "bad_version"))
                continue

        elif len(parts) == 6:
            path = parts[5].strip()
            if not path:
                skipped.append((raw, cleaned, "empty_path"))
                continue

        else:
            skipped.append((raw, cleaned, f"bad_col_count={len(parts)}"))
    return skipped


def _expected_parsed_count(text: str) -> tuple:

    raw = _raw_data_lines(text)
    skipped = _analyze_skips(text)
    return len(raw) - len(skipped), len(raw), skipped


class TestParseSize(unittest.TestCase):
    def test_thousand_separators(self):
        self.assertEqual(parse_size("4.371"), 4371)
        self.assertEqual(parse_size("39.551.238"), 39551238)
        self.assertEqual(parse_size("42.365.169"), 42365169)

    def test_empty_and_none(self):
        self.assertEqual(parse_size(""), 0)
        self.assertEqual(parse_size(None), 0)
        self.assertEqual(parse_size("   "), 0)

    def test_plain(self):
        self.assertEqual(parse_size("0"), 0)
        self.assertEqual(parse_size("9396"), 9396)


class TestCleanCsvLine(unittest.TestCase):
    def test_strips_both_markers(self):
        self.assertEqual(clean_csv_line("#x#"), "x")

    def test_strips_leading(self):
        self.assertEqual(clean_csv_line("#x"), "x")

    def test_strips_trailing(self):
        self.assertEqual(clean_csv_line("x#"), "x")

    def test_no_markers(self):
        self.assertEqual(clean_csv_line("x"), "x")


@unittest.skipUnless(HAVE_ALL, f"фикстура не найдена: {LIST_ALL}")
class TestParseCsvListAll(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = _read(LIST_ALL)
        cls.entries = parse_csv_list(text)
        cls.expected, cls.raw_n, cls.skipped = _expected_parsed_count(text)

    def test_no_silent_drops(self):

        self.assertEqual(len(self.entries), self.expected)

    def test_counts_sanity(self):
        self.assertGreaterEqual(len(self.entries), 130)
        self.assertLessEqual(len(self.entries), self.raw_n)
        dirs = sum(1 for e in self.entries if e.is_dir)
        files = sum(1 for e in self.entries if not e.is_dir)
        self.assertEqual(files + dirs, len(self.entries))
        self.assertEqual(dirs, 1)
        self.assertGreaterEqual(files, 130)

    def test_dir_entry(self):
        dirs = [e for e in self.entries if e.is_dir]
        self.assertEqual(len(dirs), 1)
        d = dirs[0]
        self.assertEqual(d.path, "d:/1000/Распечатано")
        self.assertEqual(d.size, 39551238)
        self.assertEqual(d.version, 1)

    def test_known_xlsx(self):
        x = [e for e in self.entries if e.path.endswith("ошибки.xlsx")]
        self.assertEqual(len(x), 1)
        self.assertFalse(x[0].is_dir)
        self.assertEqual(x[0].size, 9396)

    def test_known_small_json(self):
        x = [e for e in self.entries
             if e.path == "d:/1000/04ee2e9d-eb6e-470c-bfcc-4fe34cde01de.json"]
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0].size, 4371)

    def test_cyrillic_preserved(self):
        self.assertTrue(any("Распечатано" in e.path for e in self.entries))
        self.assertTrue(any("ошибки" in e.path for e in self.entries))

    def test_single_version(self):
        self.assertTrue(all(e.version == 1 for e in self.entries))

    def test_all_under_d1000(self):
        self.assertTrue(all(e.path.startswith("d:/1000") for e in self.entries))

    def test_no_empty_paths(self):
        self.assertTrue(all(e.path for e in self.entries))


@unittest.skipUnless(HAVE_LAST, f"фикстура не найдена: {LIST_LAST}")
class TestParseCsvListLast(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = _read(LIST_LAST)
        cls.entries = parse_csv_list(text)
        cls.expected, cls.raw_n, cls.skipped = _expected_parsed_count(text)

    def test_no_silent_drops(self):
        self.assertEqual(len(self.entries), self.expected)

    def test_counts_sanity(self):
        self.assertGreaterEqual(len(self.entries), 130)
        dirs = sum(1 for e in self.entries if e.is_dir)
        files = sum(1 for e in self.entries if not e.is_dir)
        self.assertEqual(files + dirs, len(self.entries))
        self.assertEqual(dirs, 1)
        self.assertGreaterEqual(files, 130)

    def test_versions_are_none(self):
        self.assertTrue(all(e.version is None for e in self.entries))

    def test_dir_still_detected(self):
        dirs = [e for e in self.entries if e.is_dir]
        self.assertEqual(len(dirs), 1)
        self.assertEqual(dirs[0].path, "d:/1000/Распечатано")


@unittest.skipUnless(HAVE_ALL and HAVE_LAST, "нужны обе list-фикстуры")
class TestCrossList(unittest.TestCase):
    def test_all_and_last_same_row_count(self):

        a = parse_csv_list(_read(LIST_ALL))
        b = parse_csv_list(_read(LIST_LAST))
        self.assertEqual(len(a), len(b))


@unittest.skipUnless(HAVE_INFO, f"фикстура не найдена: {INFO}")
class TestParseInfo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary, cls.versions = parse_info(_read(INFO))

    def test_summary_present(self):
        self.assertIsNotNone(self.summary)

    def test_summary_counts(self):
        self.assertEqual(self.summary.versions, 1)
        self.assertEqual(self.summary.files, 137)
        self.assertEqual(self.summary.size, 42365169)

    def test_one_version(self):
        self.assertEqual(len(self.versions), 1)

    def test_version_fields(self):
        v = self.versions[0]
        self.assertEqual(v.number, 1)
        self.assertEqual(v.date, "2026-06-12")
        self.assertEqual(v.time, "20:25:10")
        self.assertEqual(v.added, 137)
        self.assertEqual(v.removed, 0)
        self.assertEqual(v.bytes_added, 42365169)


def _print_skip_diagnostics() -> None:
    print()
    print("=== skip diagnostics (why raw data lines did not become entries) ===")
    any_fixture = False
    for name in (LIST_ALL, LIST_LAST):
        if name not in PROBE:
            continue
        any_fixture = True
        text = _read(name)
        expected, raw_n, skipped = _expected_parsed_count(text)
        parsed = parse_csv_list(text)
        print(f"\n[{name}]")
        print(f"  raw data lines : {raw_n}")
        print(f"  parsed entries : {len(parsed)}  (expected by analysis: {expected})")
        by_reason = {}
        for _r, _c, reason in skipped:
            by_reason[reason] = by_reason.get(reason, 0) + 1
        print(f"  skipped        : {len(skipped)}  by reason: {by_reason or 'none'}")

        empty = [s for s in skipped if s[2] == "empty_path"]
        for raw, cleaned, reason in empty:
            print(f"    [expected/-utf empty path] {raw.strip()[:140]}")

        bugs = [s for s in skipped if s[2] != "empty_path"]
        if bugs:
            print("  !! SKIPPED WITH NON-EMPTY PATH (possible PARSER BUG):")
            for raw, cleaned, reason in bugs:
                print(f"     reason={reason}  raw={raw.strip()[:160]}")
        else:
            print("  no parser-bug skips (all skips are -utf empty-path artifacts or none)")
    if not any_fixture:
        print("  (no list fixtures found)")
    print()


if __name__ == "__main__":
    print("Probe fixtures:")
    if PROBE:
        for n, p in PROBE.items():
            print(f"  [ok]   {n}  ->  {p}")
    else:
        print("  [none] not found (set ZPAQ_PROBE_DIR or place probe_out nearby)")
    _print_skip_diagnostics()
    unittest.main(verbosity=2, exit=False)
