from __future__ import annotations

import re
from typing import Optional

from .models import ArchiveEntry, ArchiveSummary, ArchiveVersion


_REPORT_SAMPLES = 5


_REASONS = {
    "columns": "число колонок не 6 и не 7",
    "version": "номер версии не целое число",
    "empty_path": "путь пустой",
}


class ParseReport:

    def __init__(self) -> None:
        self.data_lines = 0
        self.parsed = 0
        self.service = 0
        self.reasons: dict = {}
        self.samples: list = []

    @property
    def dropped(self) -> int:

        return self.data_lines - self.parsed

    @property
    def ok(self) -> bool:
        return self.dropped == 0

    def note_drop(self, reason: str, line: str) -> None:
        self.reasons[reason] = self.reasons.get(reason, 0) + 1
        if len(self.samples) < _REPORT_SAMPLES:
            self.samples.append(line)

    def reason_lines(self) -> list:

        out = []
        for reason, count in sorted(
            self.reasons.items(), key=lambda kv: -kv[1]
        ):
            text = _REASONS.get(reason, reason)
            out.append(f"    {text}: {count}")
        return out

    def log_text(self) -> str:
        parts = [
            f"[rizpaq] список разобран не полностью: не распознано "
            f"{self.dropped} из {self.data_lines} строк данных, "
            f"разобрано {self.parsed}"
        ]
        parts.extend(self.reason_lines())
        for sample in self.samples:
            shown = sample if len(sample) <= 160 else sample[:157] + "..."
            parts.append(f"    пример: {shown!r}")
        return "\n".join(parts)


def parse_size(value: Optional[str]) -> int:
    if not value:
        return 0

    value = value.strip().replace(".", "").replace(",", "")
    if not value:
        return 0

    try:
        return int(value)
    except ValueError:
        return 0


def clean_csv_line(line: str) -> str:

    line = line.rstrip("\n")

    if line.startswith("#"):
        line = line[1:]
    if line.endswith("#"):
        line = line[:-1]

    return line


def parse_csv_line_reported(
    raw_line: str, report: ParseReport
) -> Optional[ArchiveEntry]:
    if not raw_line.strip():
        return None


    if raw_line.strip().startswith("<<"):
        report.service += 1
        return None

    line = clean_csv_line(raw_line)
    if not line:
        return None

    report.data_lines += 1
    parts = line.split("\t")

    if len(parts) == 7:
        dt, attr, size_s, ratio, version_s, flag, path = parts
        try:
            version = int(version_s)
        except ValueError:


            report.note_drop("version", raw_line)
            return None
    elif len(parts) == 6:
        dt, attr, size_s, ratio, flag, path = parts
        version = None
    else:


        report.note_drop("columns", raw_line)
        return None

    path = path.strip()
    if not path:
        report.note_drop("empty_path", raw_line)
        return None

    is_dir = (
        attr.upper().startswith("D")
        or ratio.strip().lower() == "dir"
        or path.endswith("/")
    )
    if is_dir:
        path = path.rstrip("/")

    report.parsed += 1
    return ArchiveEntry(
        path=path,
        size=parse_size(size_s),
        datetime=dt.strip(),
        version=version,
        flag=flag.strip(),
        is_dir=is_dir,
        attr=attr.strip(),
        ratio=ratio.strip(),
        raw=line,
    )


def parse_csv_list_reported(text: str) -> tuple:
    entries: list = []
    report = ParseReport()

    for raw_line in text.splitlines():
        entry = parse_csv_line_reported(raw_line, report)
        if entry is not None:
            entries.append(entry)

    return entries, report


def parse_csv_list(text: str) -> list:
    entries, _report = parse_csv_list_reported(text)
    return entries


SUMMARY_RE = re.compile(
    r"(?P<versions>[\d.]+)\s+versions?,\s+"
    r"(?P<files>[\d.]+)\s+files?,\s+"
    r"(?P<bytes>[\d.]+)\s+bytes?",
    re.IGNORECASE,
)

VERSION_LINE_RE = re.compile(
    r"^V(?P<num>\d+)\s+"
    r"(?P<date>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"\+(?P<added>\d+)\s+"
    r"-(?P<removed>\d+)\s+"
    r"->\s+"
    r"(?P<bytes>[\d.]+)"
    r"(?:\s+(?P<comment>.*))?$"
)


def parse_info(text: str) -> tuple:
    summary: Optional[ArchiveSummary] = None
    versions: list = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        sm = SUMMARY_RE.search(line)
        if sm and summary is None:
            summary = ArchiveSummary(
                versions=parse_size(sm.group("versions")),
                files=parse_size(sm.group("files")),
                size=parse_size(sm.group("bytes")),
                raw=line,
            )

        vm = VERSION_LINE_RE.match(line)
        if vm:
            versions.append(
                ArchiveVersion(
                    number=int(vm.group("num")),
                    date=vm.group("date"),
                    time=vm.group("time"),
                    added=parse_size(vm.group("added")),
                    removed=parse_size(vm.group("removed")),
                    bytes_added=parse_size(vm.group("bytes")),
                    comment=(vm.group("comment") or "").strip(),
                    raw=line,
                )
            )

    return summary, versions


CREATE_STATS_RE = re.compile(
    r"\(\s*(?P<original>[\d.]+)\s*->\s*"
    r"(?P<after_dedup>[\d.]+)\s*->\s*"
    r"(?P<compressed>[\d.]+)\s*\)"
)


def parse_create_stats(text: str) -> Optional[dict]:
    if not text:
        return None

    result = None
    for raw_line in text.splitlines():
        m = CREATE_STATS_RE.search(raw_line)
        if m:
            result = {
                "original": parse_size(m.group("original")),
                "after_dedup": parse_size(m.group("after_dedup")),
                "compressed": parse_size(m.group("compressed")),
            }

    return result
