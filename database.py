"""
QuickFind — Database, Indexer & File Watcher
SQLite FTS5 · Content indexing · Real-time file watching
Supports: PDF, DOCX, XLSX, PPTX, RTF, EPUB + 35 plain-text formats
"""

import sqlite3
import os
import time
import threading
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

MAX_CONTENT_BYTES = 8192   # First 8KB for plain text files
MAX_CONTENT_CHARS = 4096   # Max chars to store from rich documents
MAX_RICH_FILE_SIZE = 50_000_000  # Skip rich docs larger than 50MB

DB_DIR = "D:\\QuickFind_Index"
DB_PATH = os.path.join(DB_DIR, "index.db")


# ══════════════════════════════════════════════════════════════
#  RICH DOCUMENT READERS
# ══════════════════════════════════════════════════════════════

def _read_pdf(path):
    try:
        import fitz  # pymupdf
        doc = fitz.open(path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
            if len("".join(text_parts)) > MAX_CONTENT_CHARS:
                break
        doc.close()
        return "".join(text_parts)[:MAX_CONTENT_CHARS]
    except Exception:
        return ""


def _read_docx(path):
    try:
        from docx import Document
        doc = Document(path)
        text_parts = []
        total = 0
        for para in doc.paragraphs:
            text_parts.append(para.text)
            total += len(para.text)
            if total > MAX_CONTENT_CHARS:
                break
        return "\n".join(text_parts)[:MAX_CONTENT_CHARS]
    except Exception:
        return ""


def _read_xlsx(path):
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path, read_only=True, data_only=True)
        text_parts = []
        total = 0
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            for row in ws.iter_rows(values_only=True):
                vals = [str(c) for c in row if c is not None]
                if vals:
                    line = " ".join(vals)
                    text_parts.append(line)
                    total += len(line)
                    if total > MAX_CONTENT_CHARS:
                        break
            if total > MAX_CONTENT_CHARS:
                break
        wb.close()
        return "\n".join(text_parts)[:MAX_CONTENT_CHARS]
    except Exception:
        return ""


def _read_pptx(path):
    try:
        from pptx import Presentation
        prs = Presentation(path)
        text_parts = []
        total = 0
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        text_parts.append(para.text)
                        total += len(para.text)
                        if total > MAX_CONTENT_CHARS:
                            break
                if total > MAX_CONTENT_CHARS:
                    break
            if total > MAX_CONTENT_CHARS:
                break
        return "\n".join(text_parts)[:MAX_CONTENT_CHARS]
    except Exception:
        return ""


def _read_rtf(path):
    try:
        from striprtf.striprtf import rtf_to_text
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read(MAX_CONTENT_BYTES * 4)
        return rtf_to_text(raw)[:MAX_CONTENT_CHARS]
    except Exception:
        return ""


def _read_epub(path):
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        book = epub.read_epub(path, options={"ignore_ncx": True})
        text_parts = []
        total = 0
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            text_parts.append(text)
            total += len(text)
            if total > MAX_CONTENT_CHARS:
                break
        return "\n".join(text_parts)[:MAX_CONTENT_CHARS]
    except Exception:
        return ""


RICH_READERS = {
    ".pdf": _read_pdf,
    ".docx": _read_docx,
    ".xlsx": _read_xlsx,
    ".pptx": _read_pptx,
    ".rtf": _read_rtf,
    ".epub": _read_epub,
}


# ══════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════

class FileDatabase:
    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-64000")
        self.lock = threading.Lock()
        self._create_tables()

    def _create_tables(self):
        with self.lock:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL UNIQUE,
                    extension TEXT,
                    size INTEGER DEFAULT 0,
                    modified REAL DEFAULT 0,
                    is_dir INTEGER DEFAULT 0,
                    content_text TEXT DEFAULT ''
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                    name,
                    path,
                    extension,
                    content_text,
                    content='files',
                    content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                );

                CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
                    INSERT INTO files_fts(rowid, name, path, extension, content_text)
                    VALUES (new.id, new.name, new.path, new.extension, new.content_text);
                END;

                CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
                    INSERT INTO files_fts(files_fts, rowid, name, path, extension, content_text)
                    VALUES ('delete', old.id, old.name, old.path, old.extension, old.content_text);
                END;

                CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
                    INSERT INTO files_fts(files_fts, rowid, name, path, extension, content_text)
                    VALUES ('delete', old.id, old.name, old.path, old.extension, old.content_text);
                    INSERT INTO files_fts(rowid, name, path, extension, content_text)
                    VALUES (new.id, new.name, new.path, new.extension, new.content_text);
                END;

                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_files_ext ON files(extension);
                CREATE INDEX IF NOT EXISTS idx_files_name ON files(name);
                CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
            """)
            self.conn.commit()

    def get_meta(self, key):
        cur = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def set_meta(self, key, value):
        with self.lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)",
                (key, str(value))
            )
            self.conn.commit()

    def get_file_count(self):
        cur = self.conn.execute("SELECT COUNT(*) FROM files")
        return cur.fetchone()[0]

    def clear(self):
        with self.lock:
            self.conn.executescript("""
                DELETE FROM files;
                INSERT INTO files_fts(files_fts) VALUES('rebuild');
            """)
            self.conn.commit()

    def insert_batch(self, file_list):
        with self.lock:
            self.conn.executemany(
                "INSERT OR IGNORE INTO files(name, path, extension, size, modified, is_dir, content_text) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                file_list
            )
            self.conn.commit()

    def upsert_file(self, name, path, ext, size, modified, is_dir, content_text=""):
        with self.lock:
            self.conn.execute(
                "INSERT INTO files(name, path, extension, size, modified, is_dir, content_text) "
                "VALUES(?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(path) DO UPDATE SET "
                "name=excluded.name, extension=excluded.extension, "
                "size=excluded.size, modified=excluded.modified, "
                "content_text=excluded.content_text",
                (name, path, ext, size, modified, is_dir, content_text)
            )
            self.conn.commit()

    def delete_file(self, path):
        with self.lock:
            self.conn.execute("DELETE FROM files WHERE path=?", (path,))
            self.conn.commit()

    def rename_file(self, old_path, new_path):
        self.delete_file(old_path)

    def path_exists(self, path):
        cur = self.conn.execute("SELECT 1 FROM files WHERE path=?", (path,))
        return cur.fetchone() is not None

    def search(self, query, limit=200):
        if not query or not query.strip():
            return []

        query = query.strip()
        terms = query.split()
        fts_query = " AND ".join(f'"{t}"*' for t in terms if t)

        try:
            cur = self.conn.execute("""
                SELECT f.name, f.path, f.extension, f.size, f.modified, f.is_dir,
                       bm25(files_fts, 10.0, 1.0, 5.0, 2.0) as rank
                FROM files_fts
                JOIN files f ON f.id = files_fts.rowid
                WHERE files_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (fts_query, limit))
            return cur.fetchall()
        except Exception:
            like = f"%{query}%"
            cur = self.conn.execute("""
                SELECT name, path, extension, size, modified, is_dir, 0
                FROM files WHERE name LIKE ?
                ORDER BY CASE WHEN name LIKE ? THEN 0 ELSE 1 END, name
                LIMIT ?
            """, (like, f"{query}%", limit))
            return cur.fetchall()

    def close(self):
        self.conn.close()

    def get_db_size_mb(self):
        total = 0
        for f in os.listdir(DB_DIR):
            fp = os.path.join(DB_DIR, f)
            if os.path.isfile(fp):
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
        """Read content from any supported file type."""
        if ext in RICH_EXTENSIONS:
            if size > MAX_RICH_FILE_SIZE:
                return ""
            reader = RICH_READERS.get(ext)
            if reader:
                try:
                    return reader(path)
                except Exception:
                    return ""
        elif ext in TEXT_EXTENSIONS:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read(MAX_CONTENT_BYTES)
            except (PermissionError, OSError):
                return ""
        return ""

    def _index_worker(self, drives, reindex):
        start_time = time.time()

        if reindex:
            self._status("Clearing old index...")
            self.db.clear()

        self.total_indexed = 0
        batch = []
        batch_size = 3000

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
                        batch.append((name, entry.path, "", 0, 0, 1, ""))
                        self.total_indexed += 1
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

                        content = ""
                        if ext in RICH_EXTENSIONS:
                            if size < MAX_RICH_FILE_SIZE:
                                content = self.read_content(entry.path, ext, size)
                        elif ext in TEXT_EXTENSIONS and size < 500_000:
                            content = self.read_content(entry.path, ext, size)

                        batch.append((name, entry.path, ext, size, modified, 0, content))
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
        self._debounce = {}
        self._lock = threading.Lock()

    def _should_skip(self, path):
        parts = path.replace("/", "\\").split("\\")
        skip = FileIndexer.SKIP_DIRS
        for p in parts:
            if p in skip or p.startswith('.'):
                return True
        ext = Path(path).suffix.lower()
        if ext in FileIndexer.SKIP_EXTENSIONS:
            return True
        return False

    def _status(self, msg):
        if self.status_callback:
            self.status_callback(msg)

    def _index_single(self, path):
        if self._should_skip(path):
            return
        try:
            name = os.path.basename(path)
            if os.path.isdir(path):
                self.db.upsert_file(name, path, "", 0, 0, 1, "")
            else:
                ext = Path(name).suffix.lower()
                try:
                    stat = os.stat(path)
                    size = stat.st_size
                    modified = stat.st_mtime
                except OSError:
                    size = 0
                    modified = 0
                content = FileIndexer.read_content(path, ext, size)
                self.db.upsert_file(name, path, ext, size, modified, 0, content)
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
        self.db.delete_file(event.src_path)
        if event.is_directory:
            with self.db.lock:
                self.db.conn.execute(
                    "DELETE FROM files WHERE path LIKE ?",
                    (event.src_path + "%",)
                )
                self.db.conn.commit()
        self._status(f"Removed: {os.path.basename(event.src_path)}")

    def on_modified(self, event):
        if event.is_directory:
            return
        if self._should_skip(event.src_path):
            return
        self._index_single(event.src_path)

    def on_moved(self, event):
        if self._should_skip(event.src_path):
            self._index_single(event.dest_path)
            return
        self.db.delete_file(event.src_path)
        if event.is_directory:
            with self.db.lock:
                self.db.conn.execute(
                    "DELETE FROM files WHERE path LIKE ?",
                    (event.src_path + "%",)
                )
                self.db.conn.commit()
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
