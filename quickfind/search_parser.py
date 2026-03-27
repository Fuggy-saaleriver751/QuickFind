"""
Advanced search query parser for QuickFind.

Parses raw search strings into structured SearchQuery objects with support
for operators: regex, size, modified, folder, ext, hash, content.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import ClassVar


# ---------------------------------------------------------------------------
# Size helpers
# ---------------------------------------------------------------------------

_SIZE_UNITS: dict[str, int] = {
    "B": 1,
    "KB": 1024,
    "MB": 1024 ** 2,
    "GB": 1024 ** 3,
}

_SIZE_RE = re.compile(
    r"^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB)$",
    re.IGNORECASE,
)


def _parse_size(raw: str) -> int | None:
    """Convert a human-readable size string to bytes, or return None."""
    m = _SIZE_RE.match(raw.strip())
    if m is None:
        return None
    value = float(m.group(1))
    unit = m.group(2).upper()
    return int(value * _SIZE_UNITS[unit])


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def _parse_date_range(raw: str) -> tuple[float | None, float | None]:
    """Return (date_from, date_to) as timestamps, or (None, None) on failure."""
    now = datetime.now()
    today = _start_of_day(now)
    keyword = raw.strip().lower()

    if keyword == "today":
        return (today.timestamp(), now.timestamp())

    if keyword == "yesterday":
        yesterday = today - timedelta(days=1)
        return (yesterday.timestamp(), _end_of_day(yesterday).timestamp())

    if keyword == "thisweek":
        # Monday of the current week
        monday = today - timedelta(days=today.weekday())
        return (monday.timestamp(), now.timestamp())

    if keyword == "thismonth":
        first = today.replace(day=1)
        return (first.timestamp(), now.timestamp())

    # Explicit range: YYYY-MM-DD..YYYY-MM-DD
    if ".." in raw:
        parts = raw.split("..", maxsplit=1)
        if len(parts) == 2:
            try:
                dt_from = datetime.strptime(parts[0].strip(), "%Y-%m-%d")
                dt_to = datetime.strptime(parts[1].strip(), "%Y-%m-%d")
                return (
                    _start_of_day(dt_from).timestamp(),
                    _end_of_day(dt_to).timestamp(),
                )
            except ValueError:
                pass

    return (None, None)


# ---------------------------------------------------------------------------
# SearchQuery dataclass
# ---------------------------------------------------------------------------

@dataclass
class SearchQuery:
    """Structured representation of a parsed search query."""

    fts_terms: list[str] = field(default_factory=list)
    regex_pattern: re.Pattern[str] | None = None
    min_size: int | None = None
    max_size: int | None = None
    date_from: float | None = None
    date_to: float | None = None
    folder_filter: str | None = None
    ext_filter: list[str] | None = None
    hash_prefix: str | None = None
    content_filter: str | None = None

    # Human-readable labels for the UI
    _SIZE_SUFFIXES: ClassVar[list[tuple[int, str]]] = [
        (1024 ** 3, "GB"),
        (1024 ** 2, "MB"),
        (1024, "KB"),
        (1, "B"),
    ]

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt_size(n: int) -> str:
        for threshold, suffix in SearchQuery._SIZE_SUFFIXES:
            if n >= threshold:
                value = n / threshold
                # Show integer when there are no fractional bytes
                if value == int(value):
                    return f"{int(value)} {suffix}"
                return f"{value:.1f} {suffix}"
        return f"{n} B"

    @staticmethod
    def _fmt_ts(ts: float) -> str:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

    def to_display_string(self) -> str:
        """Return a human-readable summary of all active filters."""
        parts: list[str] = []

        if self.fts_terms:
            parts.append(f'Search: {" ".join(self.fts_terms)}')

        if self.regex_pattern is not None:
            parts.append(f"Regex: {self.regex_pattern.pattern}")

        if self.min_size is not None and self.max_size is not None:
            parts.append(
                f"Size: {self._fmt_size(self.min_size)} – {self._fmt_size(self.max_size)}"
            )
        elif self.min_size is not None:
            parts.append(f"Size: > {self._fmt_size(self.min_size)}")
        elif self.max_size is not None:
            parts.append(f"Size: < {self._fmt_size(self.max_size)}")

        if self.date_from is not None or self.date_to is not None:
            if self.date_from is not None and self.date_to is not None:
                parts.append(
                    f"Modified: {self._fmt_ts(self.date_from)} to {self._fmt_ts(self.date_to)}"
                )
            elif self.date_from is not None:
                parts.append(f"Modified: from {self._fmt_ts(self.date_from)}")
            else:
                assert self.date_to is not None
                parts.append(f"Modified: until {self._fmt_ts(self.date_to)}")

        if self.folder_filter is not None:
            parts.append(f"Folder: {self.folder_filter}")

        if self.ext_filter is not None:
            parts.append(f"Extensions: {', '.join(self.ext_filter)}")

        if self.hash_prefix is not None:
            parts.append(f"Hash: {self.hash_prefix}")

        if self.content_filter is not None:
            parts.append(f"Content: {self.content_filter}")

        if not parts:
            return "No active filters"

        return " | ".join(parts)


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_OPERATOR_RE = re.compile(
    r"^(regex|size|modified|folder|ext|hash|content):(.+)$",
    re.IGNORECASE,
)


def _tokenize(raw: str) -> list[str]:
    """Split the raw query into tokens, respecting quoted strings."""
    try:
        return shlex.split(raw)
    except ValueError:
        # Unbalanced quotes — fall back to simple whitespace split
        return raw.split()


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_query(raw: str) -> SearchQuery:
    """Parse a raw search string into a structured *SearchQuery*.

    Unrecognised or malformed operators are silently treated as plain
    FTS search terms so that the search never fails due to user typos.
    """
    query = SearchQuery()
    tokens = _tokenize(raw.strip())

    for token in tokens:
        m = _OPERATOR_RE.match(token)
        if m is None:
            # Plain search term
            query.fts_terms.append(token)
            continue

        op = m.group(1).lower()
        value = m.group(2)

        try:
            if op == "regex":
                query.regex_pattern = re.compile(value)

            elif op == "size":
                _apply_size(query, value)

            elif op == "modified":
                date_from, date_to = _parse_date_range(value)
                if date_from is not None or date_to is not None:
                    query.date_from = date_from
                    query.date_to = date_to
                else:
                    # Invalid date expression — keep as search term
                    query.fts_terms.append(token)

            elif op == "folder":
                query.folder_filter = value

            elif op == "ext":
                extensions = [
                    e.strip().lstrip(".").lower()
                    for e in value.split(",")
                    if e.strip()
                ]
                if extensions:
                    query.ext_filter = extensions
                else:
                    query.fts_terms.append(token)

            elif op == "hash":
                query.hash_prefix = value.lower()

            elif op == "content":
                query.content_filter = value

            else:
                # Unknown operator — treat as search term
                query.fts_terms.append(token)

        except (re.error, ValueError, OverflowError):
            # Malformed operator value — treat the whole token as a search term
            query.fts_terms.append(token)

    return query


# ---------------------------------------------------------------------------
# Size operator helpers
# ---------------------------------------------------------------------------

def _apply_size(query: SearchQuery, value: str) -> None:
    """Parse a size operator value and set min_size / max_size on *query*.

    Supported forms:
        >10MB   <1KB   10MB-100MB   500KB   (exact match treated as both min and max)
    """
    # Range: 10MB-100MB
    if "-" in value and not value.startswith(">") and not value.startswith("<"):
        lo, hi = value.split("-", maxsplit=1)
        parsed_lo = _parse_size(lo)
        parsed_hi = _parse_size(hi)
        if parsed_lo is not None and parsed_hi is not None:
            query.min_size = parsed_lo
            query.max_size = parsed_hi
            return
        # Fall through to treat as plain term handled by caller

    # Greater-than: >10MB
    elif value.startswith(">"):
        parsed = _parse_size(value[1:])
        if parsed is not None:
            query.min_size = parsed
            return

    # Less-than: <1KB
    elif value.startswith("<"):
        parsed = _parse_size(value[1:])
        if parsed is not None:
            query.max_size = parsed
            return

    # Exact size (treated as both bounds)
    else:
        parsed = _parse_size(value)
        if parsed is not None:
            query.min_size = parsed
            query.max_size = parsed
            return

    # If nothing matched, signal failure so the caller can fall back
    raise ValueError(f"invalid size expression: {value}")
