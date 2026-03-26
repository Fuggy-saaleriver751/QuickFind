"""
QuickFind — Database, Indexer & File Watcher
SQLite FTS5 · Content indexing · Real-time file watching
Supports: PDF, DOCX, XLSX, PPTX, RTF, EPUB + 35 plain-text formats

Optimizations:
- Directory deduplication (dirs table) — paths stored once, referenced by id
- FTS indexes name + extension + folder_name + content only (no full path)
- No directory entries in files table (files only)
- WAL auto-checkpoint + TRUNCATE after batch
- VACUUM on indexing complete
"""

import sqlite3
import os
import time
import threading
import json
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


TEXT_EXTENSIONS = {
    ".txt", ".md", ".rst", ".log", ".cfg", ".ini", ".conf",
    ".py", ".pyw", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte",
    ".html", ".htm", ".css", ".scss", ".less",
    ".java", ".kt", ".scala",
    ".c", ".cpp", ".cc", ".h", ".hpp",
    ".cs", ".go", ".rs", ".rb", ".php",
    ".sh", ".bash", ".bat", ".cmd", ".ps1",
    ".json", ".xml", ".yaml", ".yml", ".toml",
    ".csv", ".sql", ".env", ".gitignore",
    ".tex", ".bib", ".srt",
}

RICH_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".pptx", ".rtf", ".epub",
}

ALL_CONTENT_EXTENSIONS = TEXT_EXTENSIONS | RICH_EXTENSIONS

MAX_RICH_FILE_SIZE = 50_000_000

# ── Content indexing presets ──
PRESETS = {
    "minimal":  {"text_bytes": 128,   "rich_chars": 128,   "label": "Minimal (~50-80 MB) *"},
    "standard": {"text_bytes": 512,   "rich_chars": 512,   "label": "Standard (~80-150 MB) *"},
    "deep":     {"text_bytes": 4096,  "rich_chars": 4096,  "label": "Deep (~200-500 MB) *"},
    "maximum":  {"text_bytes": 0,     "rich_chars": 0,     "label": "Maximum (~500 MB+) *"},
    # * estimates — actual size varies depending on file count
}

import sys as _sys
if getattr(_sys, 'frozen', False):
    _SCRIPT_DIR = os.path.dirname(_sys.executable)
else:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(_SCRIPT_DIR, "QuickFind_Index")
DB_PATH = os.path.join(DB_DIR, "index.db")
CONFIG_PATH = os.path.join(DB_DIR, "config.json")


def _load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"preset": "minimal"}

def _save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def get_preset_name():
    return _load_config().get("preset", "minimal")

def set_preset_name(name):
    cfg = _load_config()
    cfg["preset"] = name
    _save_config(cfg)
    _reset_limits_cache()

_limits_cache = None

def _get_limits():
    global _limits_cache
    if _limits_cache is None:
        preset = get_preset_name()
        p = PRESETS.get(preset, PRESETS["minimal"])
        _limits_cache = (p["text_bytes"], p["rich_chars"])
    return _limits_cache

def _reset_limits_cache():
    global _limits_cache
    _limits_cache = None


# ══════════════════════════════════════════════════════════════
#  RICH DOCUMENT READERS
# ══════════════════════════════════════════════════════════════

_READ_LIMIT = 8192  # Internal read limit for readers — final trim in read_content

def _read_pdf(path):
    try:
        import fitz
        doc = fitz.open(path)
        parts = []
        for page in doc:
            parts.append(page.get_text())
            if sum(len(t) for t in parts) > _READ_LIMIT:
                break
        doc.close()
        return "".join(parts)[:_READ_LIMIT]
    except Exception:
        return ""

def _read_docx(path):
    try:
        from docx import Document
        doc = Document(path)
        parts, total = [], 0
        for para in doc.paragraphs:
            parts.append(para.text)
            total += len(para.text)
            if total > _READ_LIMIT: break
        return "\n".join(parts)[:_READ_LIMIT]
    except Exception:
        return ""

def _read_xlsx(path):
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path, read_only=True, data_only=True)
        parts, total = [], 0
        for sheet in wb.sheetnames:
            for row in wb[sheet].iter_rows(values_only=True):
                vals = [str(c) for c in row if c is not None]
                if vals:
                    line = " ".join(vals)
                    parts.append(line)
                    total += len(line)
                    if total > _READ_LIMIT: break
            if total > _READ_LIMIT: break
        wb.close()
        return "\n".join(parts)[:_READ_LIMIT]
    except Exception:
        return ""

def _read_pptx(path):
    try:
        from pptx import Presentation
        prs = Presentation(path)
        parts, total = [], 0
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        parts.append(para.text)
                        total += len(para.text)
                        if total > _READ_LIMIT: break
                if total > _READ_LIMIT: break
            if total > _READ_LIMIT: break
        return "\n".join(parts)[:_READ_LIMIT]
    except Exception:
        return ""

def _read_rtf(path):
    try:
        from striprtf.striprtf import rtf_to_text
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read(_READ_LIMIT * 4)
        return rtf_to_text(raw)[:_READ_LIMIT]
    except Exception:
        return ""

def _read_epub(path):
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        book = epub.read_epub(path, options={"ignore_ncx": True})
        parts, total = [], 0
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            parts.append(text)
            total += len(text)
            if total > _READ_LIMIT: break
        return "\n".join(parts)[:_READ_LIMIT]
    except Exception:
        return ""

RICH_READERS = {
    ".pdf": _read_pdf, ".docx": _read_docx, ".xlsx": _read_xlsx,
    ".pptx": _read_pptx, ".rtf": _read_rtf, ".epub": _read_epub,
}


# ══════════════════════════════════════════════════════════════
#  DATABASE — with directory deduplication
# ══════════════════════════════════════════════════════════════

class FileDatabase:
    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-32000")
        self.conn.execute("PRAGMA wal_autocheckpoint=100")
        self.conn.execute("PRAGMA page_size=4096")
        self.lock = threading.Lock()
        self._dir_cache = {}  # path -> dir_id (in-memory cache)
        self._create_tables()

    def _create_tables(self):
        with self.lock:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS dirs (
                    id INTEGER PRIMARY KEY,
                    path TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    dir_id INTEGER NOT NULL REFERENCES dirs(id),
                    extension TEXT,
                    size INTEGER DEFAULT 0,
                    modified REAL DEFAULT 0,
                    folder_name TEXT DEFAULT '',
                    content_text TEXT DEFAULT '',
                    UNIQUE(dir_id, name)
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                    name,
                    extension,
                    folder_name,
                    content_text,
                    content='files',
                    content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                );

                CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
                    INSERT INTO files_fts(rowid, name, extension, folder_name, content_text)
                    VALUES (new.id, new.name, new.extension, new.folder_name, new.content_text);
                END;

                CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
                    INSERT INTO files_fts(files_fts, rowid, name, extension, folder_name, content_text)
                    VALUES ('delete', old.id, old.name, old.extension, old.folder_name, old.content_text);
                END;

                CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
                    INSERT INTO files_fts(files_fts, rowid, name, extension, folder_name, content_text)
                    VALUES ('delete', old.id, old.name, old.extension, old.folder_name, old.content_text);
                    INSERT INTO files_fts(rowid, name, extension, folder_name, content_text)
                    VALUES (new.id, new.name, new.extension, new.folder_name, new.content_text);
                END;

                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_files_ext ON files(extension);
                CREATE INDEX IF NOT EXISTS idx_files_dir ON files(dir_id);
            """)
            self.conn.commit()

    def _get_dir_id(self, dir_path):
        """Get or create directory entry, cached in memory."""
        if dir_path in self._dir_cache:
            return self._dir_cache[dir_path]
        cur = self.conn.execute("SELECT id FROM dirs WHERE path=?", (dir_path,))
        row = cur.fetchone()
        if row:
            self._dir_cache[dir_path] = row[0]
            return row[0]
        cur = self.conn.execute("INSERT OR IGNORE INTO dirs(path) VALUES(?)", (dir_path,))
        self.conn.commit()
        cur = self.conn.execute("SELECT id FROM dirs WHERE path=?", (dir_path,))
        row = cur.fetchone()
        self._dir_cache[dir_path] = row[0]
        return row[0]

    def get_meta(self, key):
        cur = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def set_meta(self, key, value):
        with self.lock:
            self.conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (key, str(value)))
            self.conn.commit()

    def get_file_count(self):
        cur = self.conn.execute("SELECT COUNT(*) FROM files")
        return cur.fetchone()[0]

    def clear(self):
        with self.lock:
            self.conn.executescript("""
                DELETE FROM files;
                DELETE FROM dirs;
                INSERT INTO files_fts(files_fts) VALUES('rebuild');
            """)
            self.conn.commit()
            self._dir_cache.clear()

    def insert_batch(self, file_list):
        """file_list: [(name, dir_path, ext, size, modified, folder_name, content_text), ...]"""
        with self.lock:
            rows = []
            for name, dir_path, ext, size, modified, folder_name, content_text in file_list:
                dir_id = self._get_dir_id(dir_path)
                rows.append((name, dir_id, ext, size, modified, folder_name, content_text))
            self.conn.executemany(
                "INSERT OR IGNORE INTO files(name, dir_id, extension, size, modified, folder_name, content_text) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                rows
            )
            self.conn.commit()
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def upsert_file(self, name, dir_path, ext, size, modified, folder_name="", content_text=""):
        with self.lock:
            dir_id = self._get_dir_id(dir_path)
            self.conn.execute(
                "INSERT INTO files(name, dir_id, extension, size, modified, folder_name, content_text) "
                "VALUES(?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(dir_id, name) DO UPDATE SET "
                "extension=excluded.extension, size=excluded.size, "
                "modified=excluded.modified, folder_name=excluded.folder_name, "
                "content_text=excluded.content_text",
                (name, dir_id, ext, size, modified, folder_name, content_text)
            )
            self.conn.commit()

    def delete_by_path(self, full_path):
        dir_path = os.path.dirname(full_path)
        name = os.path.basename(full_path)
        with self.lock:
            dir_id = self._dir_cache.get(dir_path)
            if dir_id is None:
                cur = self.conn.execute("SELECT id FROM dirs WHERE path=?", (dir_path,))
                row = cur.fetchone()
                if not row:
                    return
                dir_id = row[0]
            self.conn.execute("DELETE FROM files WHERE dir_id=? AND name=?", (dir_id, name))
            self.conn.commit()

    def delete_by_dir_prefix(self, dir_prefix):
        """Delete all files under a directory prefix."""
        with self.lock:
            self.conn.execute("""
                DELETE FROM files WHERE dir_id IN (
                    SELECT id FROM dirs WHERE path = ? OR path LIKE ?
                )
            """, (dir_prefix, dir_prefix + "\\%"))
            self.conn.commit()

    SORT_OPTIONS = {
        "relevance": "rank",
        "name_asc":  "f.name ASC",
        "name_desc": "f.name DESC",
        "size_asc":  "f.size ASC",
        "size_desc": "f.size DESC",
        "date_new":  "f.modified DESC",
        "date_old":  "f.modified ASC",
    }

    def search(self, query, limit=200, ext_filter=None, sort="relevance"):
        """Search files. ext_filter: list of extensions. sort: relevance|name_asc|name_desc|size_asc|size_desc|date_new|date_old"""
        query = query.strip() if query else ""

        # Parse search syntax: ext:pdf, ext:docx,xlsx, folder:name
        parsed_exts = []
        search_terms = []
        for term in query.split():
            if term.lower().startswith("ext:"):
                for e in term[4:].split(","):
                    e = e.strip().lower()
                    if not e.startswith("."):
                        e = "." + e
                    parsed_exts.append(e)
            else:
                search_terms.append(term)

        # Combine parsed exts with filter param
        all_exts = parsed_exts
        if ext_filter:
            all_exts = ext_filter if not parsed_exts else parsed_exts

        if not search_terms and not all_exts:
            return []
        if not query and not ext_filter:
            return []

        # Build extension WHERE clause
        ext_clause = ""
        ext_params = []
        if all_exts:
            placeholders = ",".join("?" * len(all_exts))
            ext_clause = f"AND f.extension IN ({placeholders})"
            ext_params = list(all_exts)

        order = self.SORT_OPTIONS.get(sort, "rank")

        if search_terms:
            fts_query = " AND ".join(f'"{t}"*' for t in search_terms if t)
            try:
                cur = self.conn.execute(f"""
                    SELECT f.name, d.path || '\\' || f.name, f.extension, f.size, f.modified, 0,
                           bm25(files_fts, 10.0, 5.0, 3.0, 2.0) as rank
                    FROM files_fts
                    JOIN files f ON f.id = files_fts.rowid
                    JOIN dirs d ON d.id = f.dir_id
                    WHERE files_fts MATCH ? {ext_clause}
                    ORDER BY {order}
                    LIMIT ?
                """, [fts_query] + ext_params + [limit])
                return cur.fetchall()
            except Exception:
                like = f"%{search_terms[0]}%"
                fallback_order = order if order != "rank" else "f.name ASC"
                cur = self.conn.execute(f"""
                    SELECT f.name, d.path || '\\' || f.name, f.extension, f.size, f.modified, 0, 0
                    FROM files f
                    JOIN dirs d ON d.id = f.dir_id
                    WHERE f.name LIKE ? {ext_clause}
                    ORDER BY {fallback_order}
                    LIMIT ?
                """, [like] + ext_params + [limit])
                return cur.fetchall()
        else:
            no_fts_order = order if order != "rank" else "f.modified DESC"
            cur = self.conn.execute(f"""
                SELECT f.name, d.path || '\\' || f.name, f.extension, f.size, f.modified, 0, 0
                FROM files f
                JOIN dirs d ON d.id = f.dir_id
                WHERE 1=1 {ext_clause}
                ORDER BY {no_fts_order}
                LIMIT ?
            """, ext_params + [limit])
            return cur.fetchall()

    def close(self):
        self.conn.close()

    def get_db_size_mb(self):
        total = 0
        for f in os.listdir(DB_DIR):
            fp = os.path.join(DB_DIR, f)
            if os.path.isfile(fp) and f.startswith("index.db"):
                total += os.path.getsize(fp)
        return total / (1024 * 1024)


# ══════════════════════════════════════════════════════════════
#  FILE INDEXER
# ══════════════════════════════════════════════════════════════

class FileIndexer:
    SKIP_DIRS = {
        '$Recycle.Bin', '$WinREAgent', 'System Volume Information',
        'Windows', 'ProgramData', 'Recovery', 'PerfLogs',
        '.git', 'node_modules', '__pycache__', '.venv', 'venv',
        'AppData', '.cache', '.npm', '.nuget', 'packages',
        'Windows.old', 'Config.Msi', 'QuickFind_Index',
    }

    SKIP_EXTENSIONS = {
        '.tmp', '.log', '.bak', '.dmp', '.etl', '.evtx',
        '.dat', '.db-journal', '.db-shm', '.db-wal',
    }

    def __init__(self, db: FileDatabase, progress_callback=None, status_callback=None):
        self.db = db
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self._stop_event = threading.Event()
        self._thread = None
        self.total_indexed = 0

    def start(self, drives=None, reindex=False):
        if self._thread and self._thread.is_alive():
            return
        if drives is None:
            drives = self._get_drives()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._index_worker, args=(drives, reindex), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def _get_drives(self):
        drives = []
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives

    def _status(self, msg):
        if self.status_callback:
            self.status_callback(msg)

    def _progress(self, count):
        if self.progress_callback:
            self.progress_callback(count)

    @staticmethod
    def read_content(path, ext, size=0):
        text_bytes, rich_chars = _get_limits()
        # 0 = unlimited
        if text_bytes == 0: text_bytes = 1_000_000
        if rich_chars == 0: rich_chars = 1_000_000
        if ext in RICH_EXTENSIONS:
            if size > MAX_RICH_FILE_SIZE:
                return ""
            reader = RICH_READERS.get(ext)
            if reader:
                try:
                    return reader(path)[:rich_chars]
                except Exception:
                    return ""
        elif ext in TEXT_EXTENSIONS:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read(text_bytes)
            except (PermissionError, OSError):
                return ""
        return ""

    def _index_worker(self, drives, reindex):
        start_time = time.time()
        _reset_limits_cache()

        if reindex:
            self._status("Clearing old index...")
            self.db.clear()

        self.total_indexed = 0
        batch = []
        batch_size = 1000

        for drive in drives:
            if self._stop_event.is_set():
                break
            self._status(f"Scanning: {drive}")
            self._scan_directory(drive, batch, batch_size)

        if batch:
            self.db.insert_batch(batch)
            batch.clear()

        elapsed = time.time() - start_time
        self.db.set_meta("last_index_time", datetime.now().isoformat())
        self.db.set_meta("total_files", str(self.total_indexed))
        self.db.set_meta("index_duration", f"{elapsed:.1f}")

        self._status("Compacting database...")
        try:
            with self.db.lock:
                # Force WAL flush: switch to DELETE mode (removes WAL), then back to WAL
                self.db.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                self.db.conn.execute("PRAGMA journal_mode=DELETE")
                self.db.conn.execute("VACUUM")
                self.db.conn.execute("PRAGMA journal_mode=WAL")
                self.db.conn.execute("PRAGMA wal_autocheckpoint=100")
        except Exception:
            pass

        count = self.db.get_file_count()
        db_size = self.db.get_db_size_mb()
        self._status(f"Ready! {count:,} files ({db_size:.0f} MB) — {elapsed:.1f}s")
        self._progress(count)

    def _scan_directory(self, root, batch, batch_size):
        try:
            for entry in os.scandir(root):
                if self._stop_event.is_set():
                    return
                try:
                    name = entry.name

                    if entry.is_dir(follow_symlinks=False):
                        if name in self.SKIP_DIRS or name.startswith('.'):
                            continue
                        try:
                            self._scan_directory(entry.path, batch, batch_size)
                        except (PermissionError, OSError):
                            pass
                    else:
                        ext = Path(name).suffix.lower()
                        if ext in self.SKIP_EXTENSIONS:
                            continue
                        try:
                            stat = entry.stat()
                            size = stat.st_size
                            modified = stat.st_mtime
                        except (OSError, PermissionError):
                            size = 0
                            modified = 0

                        folder_name = os.path.basename(root)
                        dir_path = root.rstrip("\\")

                        content = ""
                        if ext in RICH_EXTENSIONS:
                            if size < MAX_RICH_FILE_SIZE:
                                content = self.read_content(entry.path, ext, size)
                        elif ext in TEXT_EXTENSIONS and size < 500_000:
                            content = self.read_content(entry.path, ext, size)

                        # (name, dir_path, ext, size, modified, folder_name, content_text)
                        batch.append((name, dir_path, ext, size, modified, folder_name, content))
                        self.total_indexed += 1

                    if len(batch) >= batch_size:
                        self.db.insert_batch(batch)
                        batch.clear()
                        self._progress(self.total_indexed)
                        if self.total_indexed % 25000 == 0:
                            self._status(f"Scanning... {self.total_indexed:,} files")

                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            pass


# ══════════════════════════════════════════════════════════════
#  FILE WATCHER
# ══════════════════════════════════════════════════════════════

class QuickFindEventHandler(FileSystemEventHandler):
    def __init__(self, db: FileDatabase, status_callback=None):
        super().__init__()
        self.db = db
        self.status_callback = status_callback

    def _should_skip(self, path):
        parts = path.replace("/", "\\").split("\\")
        for p in parts:
            if p in FileIndexer.SKIP_DIRS or p.startswith('.'):
                return True
        ext = Path(path).suffix.lower()
        return ext in FileIndexer.SKIP_EXTENSIONS

    def _status(self, msg):
        if self.status_callback:
            self.status_callback(msg)

    def _index_single(self, path):
        if self._should_skip(path):
            return
        try:
            if os.path.isdir(path):
                return
            name = os.path.basename(path)
            ext = Path(name).suffix.lower()
            try:
                stat = os.stat(path)
                size = stat.st_size
                modified = stat.st_mtime
            except OSError:
                size = 0
                modified = 0
            dir_path = os.path.dirname(path)
            folder_name = os.path.basename(dir_path)
            content = FileIndexer.read_content(path, ext, size)
            self.db.upsert_file(name, dir_path, ext, size, modified, folder_name, content)
        except Exception:
            pass

    def on_created(self, event):
        if self._should_skip(event.src_path):
            return
        self._index_single(event.src_path)
        self._status(f"Added: {os.path.basename(event.src_path)}")

    def on_deleted(self, event):
        if self._should_skip(event.src_path):
            return
        if event.is_directory:
            self.db.delete_by_dir_prefix(event.src_path)
        else:
            self.db.delete_by_path(event.src_path)
        self._status(f"Removed: {os.path.basename(event.src_path)}")

    def on_modified(self, event):
        if event.is_directory or self._should_skip(event.src_path):
            return
        self._index_single(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            self.db.delete_by_dir_prefix(event.src_path)
        else:
            self.db.delete_by_path(event.src_path)
        if not self._should_skip(event.dest_path):
            self._index_single(event.dest_path)
            self._status(f"Moved: {os.path.basename(event.dest_path)}")


class FileWatcher:
    def __init__(self, db: FileDatabase, status_callback=None):
        self.db = db
        self.handler = QuickFindEventHandler(db, status_callback)
        self.observer = Observer()
        self._running = False

    def start(self):
        if self._running:
            return
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    self.observer.schedule(self.handler, drive, recursive=True)
                except Exception:
                    pass
        self.observer.daemon = True
        self.observer.start()
        self._running = True

    def stop(self):
        if self._running:
            self.observer.stop()
            self.observer.join(timeout=5)
            self._running = False

    def is_running(self):
        return self._running
