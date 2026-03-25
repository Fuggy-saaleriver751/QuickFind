"""
QuickFind — Database, Indexer & File Watcher
SQLite FTS5 · İçerik indeksleme · Gerçek zamanlı dosya izleme
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

MAX_CONTENT_BYTES = 2048  # İlk 2KB (indeks boyutunu küçük tutar)

# İndeks konumu: D:\QuickFind_Index
DB_DIR = "D:\\QuickFind_Index"
DB_PATH = os.path.join(DB_DIR, "index.db")


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
        """file_list: [(name, path, ext, size, modified, is_dir, content_text), ...]"""
        with self.lock:
            self.conn.executemany(
                "INSERT OR IGNORE INTO files(name, path, extension, size, modified, is_dir, content_text) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                file_list
            )
            self.conn.commit()

    # ─── Tekil dosya işlemleri (watcher için) ─────────────

    def upsert_file(self, name, path, ext, size, modified, is_dir, content_text=""):
        """Tek dosya ekle veya güncelle"""
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
        """Tek dosya sil"""
        with self.lock:
            self.conn.execute("DELETE FROM files WHERE path=?", (path,))
            self.conn.commit()

    def rename_file(self, old_path, new_path):
        """Dosya taşıma/yeniden adlandırma"""
        self.delete_file(old_path)
        # Yeni dosyayı ekle (watcher zaten created event de gönderecek)

    def path_exists(self, path):
        cur = self.conn.execute("SELECT 1 FROM files WHERE path=?", (path,))
        return cur.fetchone() is not None

    # ─── Arama ────────────────────────────────────────────

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
        """İndeks dosya boyutunu MB olarak döndür"""
        total = 0
        for f in os.listdir(DB_DIR):
            fp = os.path.join(DB_DIR, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
        return total / (1024 * 1024)


# ══════════════════════════════════════════════════════════════
#  FILE INDEXER (İlk tam tarama)
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
    def read_content(path, ext):
        if ext not in TEXT_EXTENSIONS:
            return ""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(MAX_CONTENT_BYTES)
        except (PermissionError, OSError):
            return ""

    def _index_worker(self, drives, reindex):
        start_time = time.time()

        if reindex:
            self._status("Eski indeks temizleniyor...")
            self.db.clear()

        self.total_indexed = 0
        batch = []
        batch_size = 3000

        for drive in drives:
            if self._stop_event.is_set():
                break
            self._status(f"Taranıyor: {drive}")
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
        self._status(f"Hazır! {count:,} dosya ({db_size:.0f} MB) — {elapsed:.1f}s")
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
                        if size < 500_000:
                            content = self.read_content(entry.path, ext)

                        batch.append((name, entry.path, ext, size, modified, 0, content))
                        self.total_indexed += 1

                    if len(batch) >= batch_size:
                        self.db.insert_batch(batch)
                        batch.clear()
                        self._progress(self.total_indexed)
                        if self.total_indexed % 25000 == 0:
                            self._status(f"Taranıyor... {self.total_indexed:,} dosya")

                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            pass


# ══════════════════════════════════════════════════════════════
#  FILE WATCHER (Gerçek zamanlı dosya izleme)
# ══════════════════════════════════════════════════════════════

class QuickFindEventHandler(FileSystemEventHandler):
    """Dosya sistemi değişikliklerini yakalayıp indeksi günceller"""

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
        """Tek bir dosya/klasörü indeksle"""
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
                content = ""
                if size < 500_000:
                    content = FileIndexer.read_content(path, ext)
                self.db.upsert_file(name, path, ext, size, modified, 0, content)
        except Exception:
            pass

    def on_created(self, event):
        if self._should_skip(event.src_path):
            return
        self._index_single(event.src_path)
        self._status(f"Eklendi: {os.path.basename(event.src_path)}")

    def on_deleted(self, event):
        if self._should_skip(event.src_path):
            return
        self.db.delete_file(event.src_path)
        # Klasör silindiğinde alt dosyaları da temizle
        if event.is_directory:
            with self.db.lock:
                self.db.conn.execute(
                    "DELETE FROM files WHERE path LIKE ?",
                    (event.src_path + "%",)
                )
                self.db.conn.commit()
        self._status(f"Silindi: {os.path.basename(event.src_path)}")

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
        # Eski yolu sil
        self.db.delete_file(event.src_path)
        if event.is_directory:
            with self.db.lock:
                self.db.conn.execute(
                    "DELETE FROM files WHERE path LIKE ?",
                    (event.src_path + "%",)
                )
                self.db.conn.commit()
        # Yeni yolu ekle
        if not self._should_skip(event.dest_path):
            self._index_single(event.dest_path)
            self._status(f"Taşındı: {os.path.basename(event.dest_path)}")


class FileWatcher:
    """Tüm diskleri gerçek zamanlı izler"""

    def __init__(self, db: FileDatabase, status_callback=None):
        self.db = db
        self.handler = QuickFindEventHandler(db, status_callback)
        self.observer = Observer()
        self._running = False

    def start(self):
        if self._running:
            return

        # Mevcut tüm diskleri izle
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
