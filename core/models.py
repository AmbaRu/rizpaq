from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ArchiveEntry:

    path: str
    size: int
    datetime: str
    version: Optional[int]
    flag: str
    is_dir: bool
    attr: str = ""
    ratio: str = ""
    raw: str = ""

    @property
    def name(self) -> str:
        if not self.path:
            return ""
        return self.path.rstrip("/").split("/")[-1]


@dataclass
class ArchiveSummary:

    versions: int = 0
    files: int = 0
    size: int = 0
    raw: str = ""


@dataclass
class ArchiveVersion:

    number: int
    date: str
    time: str
    added: int
    removed: int
    bytes_added: int
    comment: str = ""
    raw: str = ""

    @property
    def datetime(self) -> str:
        return f"{self.date} {self.time}"
