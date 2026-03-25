# QuickFind

Ultra-fast file search engine for Windows. Searches file names **and** document contents in milliseconds.

![QuickFind](quickfind.png)

## Features

- **40+ Format Support** — Search inside PDF, DOCX, XLSX, PPTX, RTF, EPUB and 35+ plain-text formats
- **FTS5 Full-Text Search** — Powered by SQLite FTS5 with BM25 ranking
- **Cyberpunk UI** — Neon glassmorphism interface with dark/light themes, animated grid background, and glow effects
- **Real-Time File Watching** — Index stays up to date automatically via filesystem events
- **Instant Results** — Millisecond-level search across millions of files
- **Lightweight** — Runs quietly in the background with minimal resource usage

## Supported Formats

| Category | Formats |
|---|---|
| Documents | PDF, DOCX, DOC, XLSX, XLS, PPTX, PPT, RTF, EPUB |
| Code | PY, JS, TS, HTML, CSS, JAVA, C, C++, C#, GO, RUST, PHP, RB, KT, and more |
| Config | JSON, XML, YAML, TOML, INI, CFG, ENV |
| Text | TXT, MD, RST, LOG, CSV, SQL, TEX, SRT |

## Installation

### Download (Recommended)

Download the latest `QuickFind.exe` from the [Releases](../../releases) page and run it. No installation required.

> **Note:** Windows SmartScreen may show a warning for unsigned applications. Click **"More info"** → **"Run anyway"** to proceed. The application is open source and safe to use.

### Build from Source

```bash
pip install -r requirements.txt
python QuickFind.pyw
```

## Configuration

### Content Indexing Limits

QuickFind indexes a portion of each file's content to keep the database size manageable. The defaults are:

| Setting | Default | File |
|---|---|---|
| `MAX_CONTENT_BYTES` | 1024 (1KB) | `database.py` — max bytes read from plain-text files |
| `MAX_CONTENT_CHARS` | 512 | `database.py` — max characters stored from rich documents (PDF, DOCX, etc.) |
| `MAX_RICH_FILE_SIZE` | 50MB | `database.py` — skip rich documents larger than this |

You can increase these values in `database.py` to index more content per file. This will improve search accuracy for deep content searches, but the database will grow significantly larger. For example:

```python
# Deep content indexing (larger database, ~1-2GB+)
MAX_CONTENT_BYTES = 8192   # 8KB per text file
MAX_CONTENT_CHARS = 4096   # 4096 chars per document

# Light indexing (smaller database, ~200-400MB)
MAX_CONTENT_BYTES = 512    # 512 bytes per text file
MAX_CONTENT_CHARS = 256    # 256 chars per document
```

The database is stored at `D:\QuickFind_Index\`.

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Enter` | Search |
| `Double-click` | Open file |
| `Ctrl+O` | Open file location in Explorer |
| `Ctrl+R` | Reindex all files |
| `Ctrl+D` | Toggle dark/light theme |
| `Ctrl+L` | Focus search bar |
| `Esc` | Clear search |

## Requirements (build from source)

- Python 3.13+
- PySide6
- PyMuPDF, python-docx, openpyxl, python-pptx, striprtf, ebooklib, beautifulsoup4
- watchdog

See `requirements.txt` for full list.

## License

MIT
