"""Export search results to CSV, TXT, or JSON."""

import csv
import json
from datetime import datetime, timezone


def _format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    if size_bytes < 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} B"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _format_modified(timestamp: float | int | None) -> str:
    """Convert timestamp to ISO datetime string."""
    if timestamp is None:
        return ""
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    except (OSError, ValueError, OverflowError):
        return ""


def export_to_csv(results: list[tuple], filepath: str) -> bool:
    """Write results to CSV with columns: Name, Path, Extension, Size, Modified.

    Results tuple format: (name, path, ext, size, modified, is_dir, rank)
    """
    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Path", "Extension", "Size", "Modified"])
            for row in results:
                name, path, ext, size, modified, _is_dir, _rank = row
                writer.writerow([
                    name,
                    path,
                    ext,
                    _format_size(size or 0),
                    _format_modified(modified),
                ])
        return True
    except Exception:
        return False


def export_to_txt(results: list[tuple], filepath: str) -> bool:
    """Write plain text, one path per line.

    Results tuple format: (name, path, ext, size, modified, is_dir, rank)
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for row in results:
                _name, path, *_ = row
                f.write(f"{path}\n")
        return True
    except Exception:
        return False


def export_to_json(results: list[tuple], filepath: str) -> bool:
    """Write results as a JSON array.

    Results tuple format: (name, path, ext, size, modified, is_dir, rank)
    """
    try:
        records = []
        for row in results:
            name, path, ext, size, modified, is_dir, rank = row
            records.append({
                "name": name,
                "path": path,
                "extension": ext,
                "size": size,
                "modified": modified,
                "is_dir": bool(is_dir),
                "rank": rank,
            })
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
