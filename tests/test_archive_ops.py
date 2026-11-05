from __future__ import annotations

import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.archive_ops import slice_at_version, version_numbers
from core.models import ArchiveEntry


def _f(path: str, version: int, flag: str = "+", dt: str = "2026-01-01 00:00:00") -> ArchiveEntry:
    return ArchiveEntry(
        path=path, size=100, datetime=dt, version=version,
        flag=flag, is_dir=False,
    )


def _d(path: str, version: int, flag: str = "#") -> ArchiveEntry:
    return ArchiveEntry(
        path=path, size=0, datetime="2026-01-01 00:00:00", version=version,
        flag=flag, is_dir=True,
    )


ENTRIES = [
    _f("d:/a", 1, "+", "2026-01-01 10:00:00"),
    _f("d:/a", 2, "+", "2026-01-02 10:00:00"),
    _f("d:/a", 3, "-", "2026-01-03 10:00:00"),
    _f("d:/b", 1, "+", "2026-01-01 10:00:00"),
    _f("d:/b", 2, "+", "2026-01-02 10:00:00"),
    _f("d:/c", 2, "+", "2026-01-02 10:00:00"),
    _d("d:/dir", 1),
]


def _paths(slice_: list) -> set:
    return {e.path for e in slice_}


def _file_version(slice_: list, path: str) -> int:
    for e in slice_:
        if e.path == path and not e.is_dir:
            return e.version
    raise KeyError(path)


class TestSliceAtVersion(unittest.TestCase):
    def test_version_1(self):
        s = slice_at_version(ENTRIES, 1)

        self.assertEqual(_paths(s) & {"d:/a", "d:/b", "d:/c"}, {"d:/a", "d:/b"})
        self.assertIn("d:/dir", _paths(s))
        self.assertEqual(_file_version(s, "d:/a"), 1)

    def test_version_2(self):
        s = slice_at_version(ENTRIES, 2)
        self.assertEqual(_paths(s) & {"d:/a", "d:/b", "d:/c"}, {"d:/a", "d:/b", "d:/c"})
        self.assertEqual(_file_version(s, "d:/a"), 2)
        self.assertEqual(_file_version(s, "d:/c"), 2)

    def test_version_3_drops_deleted(self):
        s = slice_at_version(ENTRIES, 3)

        self.assertNotIn("d:/a", _paths(s))
        self.assertIn("d:/b", _paths(s))
        self.assertIn("d:/c", _paths(s))
        self.assertEqual(_file_version(s, "d:/b"), 2)

    def test_dir_excluded_when_deleted(self):
        extra = ENTRIES + [_d("d:/tmp", 1), _d("d:/tmp", 2, "-")]
        s = slice_at_version(extra, 2)
        self.assertNotIn("d:/tmp", _paths(s))

    def test_dir_excluded_when_created_later(self):
        extra = ENTRIES + [_d("d:/late", 5)]
        s = slice_at_version(extra, 2)
        self.assertNotIn("d:/late", _paths(s))

    def test_empty_when_before_everything(self):
        s = slice_at_version(ENTRIES, 0)
        self.assertEqual(s, [])


class TestVersionNumbers(unittest.TestCase):
    def test_sorted_unique(self):
        self.assertEqual(version_numbers(ENTRIES), [1, 2, 3])


if __name__ == "__main__":
    unittest.main(verbosity=2)
