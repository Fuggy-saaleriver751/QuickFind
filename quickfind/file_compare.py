"""Side-by-side file comparison using difflib."""

import difflib
from dataclasses import dataclass


@dataclass
class DiffLine:
    """Represents a single line in a diff comparison."""

    line_num_left: int | None
    line_num_right: int | None
    text_left: str
    text_right: str
    status: str  # "added", "removed", "changed", "same"


def compare_files(path1: str, path2: str, max_lines: int = 2000) -> list[DiffLine]:
    """Compare two files and return a list of DiffLine entries.

    Reads files as UTF-8. Returns empty list on error.
    """
    try:
        with open(path1, "r", encoding="utf-8", errors="replace") as f:
            lines1 = f.readlines()[:max_lines]
        with open(path2, "r", encoding="utf-8", errors="replace") as f:
            lines2 = f.readlines()[:max_lines]
    except Exception:
        return []

    try:
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        result: list[DiffLine] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    text = lines1[i1 + k].rstrip("\n\r")
                    result.append(DiffLine(
                        line_num_left=i1 + k + 1,
                        line_num_right=j1 + k + 1,
                        text_left=text,
                        text_right=text,
                        status="same",
                    ))
            elif tag == "replace":
                left_count = i2 - i1
                right_count = j2 - j1
                pairs = max(left_count, right_count)
                for k in range(pairs):
                    left_text = lines1[i1 + k].rstrip("\n\r") if k < left_count else ""
                    right_text = lines2[j1 + k].rstrip("\n\r") if k < right_count else ""
                    left_num = (i1 + k + 1) if k < left_count else None
                    right_num = (j1 + k + 1) if k < right_count else None
                    result.append(DiffLine(
                        line_num_left=left_num,
                        line_num_right=right_num,
                        text_left=left_text,
                        text_right=right_text,
                        status="changed",
                    ))
            elif tag == "insert":
                for k in range(j2 - j1):
                    result.append(DiffLine(
                        line_num_left=None,
                        line_num_right=j1 + k + 1,
                        text_left="",
                        text_right=lines2[j1 + k].rstrip("\n\r"),
                        status="added",
                    ))
            elif tag == "delete":
                for k in range(i2 - i1):
                    result.append(DiffLine(
                        line_num_left=i1 + k + 1,
                        line_num_right=None,
                        text_left=lines1[i1 + k].rstrip("\n\r"),
                        text_right="",
                        status="removed",
                    ))

        return result
    except Exception:
        return []


def get_diff_stats(diff_lines: list[DiffLine]) -> dict:
    """Return counts of each diff status.

    Returns {added: int, removed: int, changed: int, same: int}.
    """
    stats = {"added": 0, "removed": 0, "changed": 0, "same": 0}
    for line in diff_lines:
        if line.status in stats:
            stats[line.status] += 1
    return stats
