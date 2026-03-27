"""Persistent user data management for QuickFind."""

import json
import os
import threading
from datetime import datetime


class SearchHistory:
    """Stores last 50 unique search queries."""

    MAX_ENTRIES = 50

    def __init__(self, data_dir: str) -> None:
        self._path = os.path.join(data_dir, "history.json")
        self._lock = threading.Lock()

    def _load(self) -> list[dict]:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    def _save(self, data: list[dict]) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add(self, query: str) -> None:
        with self._lock:
            data = self._load()
            data = [e for e in data if e.get("query") != query]
            data.insert(0, {"query": query, "timestamp": datetime.now().isoformat()})
            data = data[: self.MAX_ENTRIES]
            self._save(data)

    def get_recent(self, limit: int = 20) -> list[str]:
        with self._lock:
            data = self._load()
            return [e["query"] for e in data[:limit] if "query" in e]

    def clear(self) -> None:
        with self._lock:
            self._save([])

    def remove(self, query: str) -> None:
        with self._lock:
            data = self._load()
            data = [e for e in data if e.get("query") != query]
            self._save(data)


class Bookmarks:
    """Stores starred/favorited file paths."""

    def __init__(self, data_dir: str) -> None:
        self._path = os.path.join(data_dir, "bookmarks.json")
        self._lock = threading.Lock()

    def _load(self) -> list[dict]:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    def _save(self, data: list[dict]) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def toggle(self, path: str, label: str = "") -> None:
        with self._lock:
            data = self._load()
            existing = [e for e in data if e.get("path") == path]
            if existing:
                data = [e for e in data if e.get("path") != path]
            else:
                data.append({
                    "path": path,
                    "added_at": datetime.now().isoformat(),
                    "label": label,
                })
            self._save(data)

    def is_bookmarked(self, path: str) -> bool:
        with self._lock:
            data = self._load()
            return any(e.get("path") == path for e in data)

    def get_all(self) -> list[dict]:
        with self._lock:
            return self._load()

    def remove(self, path: str) -> None:
        with self._lock:
            data = self._load()
            data = [e for e in data if e.get("path") != path]
            self._save(data)

    def count(self) -> int:
        with self._lock:
            return len(self._load())


class PinnedResults:
    """Stores pinned file paths that appear at top of search results."""

    def __init__(self, data_dir: str) -> None:
        self._path = os.path.join(data_dir, "pinned.json")
        self._lock = threading.Lock()

    def _load(self) -> list[dict]:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    def _save(self, data: list[dict]) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def toggle(self, path: str) -> None:
        with self._lock:
            data = self._load()
            existing = [e for e in data if e.get("path") == path]
            if existing:
                data = [e for e in data if e.get("path") != path]
            else:
                data.append({
                    "path": path,
                    "pinned_at": datetime.now().isoformat(),
                })
            self._save(data)

    def is_pinned(self, path: str) -> bool:
        with self._lock:
            data = self._load()
            return any(e.get("path") == path for e in data)

    def get_all(self) -> list[dict]:
        with self._lock:
            return self._load()

    def get_paths(self) -> set[str]:
        with self._lock:
            data = self._load()
            return {e["path"] for e in data if "path" in e}

    def count(self) -> int:
        with self._lock:
            return len(self._load())


class RecentFiles:
    """Tracks last 30 files opened via QuickFind."""

    MAX_ENTRIES = 30

    def __init__(self, data_dir: str) -> None:
        self._path = os.path.join(data_dir, "recent.json")
        self._lock = threading.Lock()

    def _load(self) -> list[dict]:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    def _save(self, data: list[dict]) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add(self, path: str) -> None:
        with self._lock:
            data = self._load()
            data = [e for e in data if e.get("path") != path]
            data.insert(0, {"path": path, "opened_at": datetime.now().isoformat()})
            data = data[: self.MAX_ENTRIES]
            self._save(data)

    def get_recent(self, limit: int = 15) -> list[dict]:
        with self._lock:
            data = self._load()
            # Lazy cleanup: remove entries for files that no longer exist
            cleaned = [e for e in data if "path" in e and os.path.exists(e["path"])]
            if len(cleaned) != len(data):
                self._save(cleaned)
            return cleaned[:limit]

    def clear(self) -> None:
        with self._lock:
            self._save([])

    def count(self) -> int:
        with self._lock:
            return len(self._load())


class UserDataManager:
    """Facade that creates all user data stores with the same data directory."""

    def __init__(self, data_dir: str) -> None:
        self._data_dir = data_dir
        try:
            os.makedirs(data_dir, exist_ok=True)
        except Exception:
            pass

        self._history = SearchHistory(data_dir)
        self._bookmarks = Bookmarks(data_dir)
        self._pinned = PinnedResults(data_dir)
        self._recent = RecentFiles(data_dir)

    @property
    def history(self) -> SearchHistory:
        return self._history

    @property
    def bookmarks(self) -> Bookmarks:
        return self._bookmarks

    @property
    def pinned(self) -> PinnedResults:
        return self._pinned

    @property
    def recent(self) -> RecentFiles:
        return self._recent
