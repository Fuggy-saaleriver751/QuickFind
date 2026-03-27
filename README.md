# QuickFind

Ultra-fast desktop file search for Windows. Finds files by name, content, and hash in milliseconds. 3-phase parallel indexing makes search ready in seconds.

![QuickFind](quickfind.png)

## Features

### Search
- **40+ Format Support** — Search inside PDF, DOCX, XLSX, PPTX, RTF, EPUB and 35+ plain-text formats
- **FTS5 Full-Text Search** — SQLite FTS5 with BM25 ranking, millisecond results
- **Real-Time Search** — Results appear as you type (300ms debounce)
- **Advanced Operators** — `regex:pattern` `size:>10MB` `modified:today` `folder:name` `content:text` `hash:sha256`
- **Hash-Based Content Search** — Find files by SHA-256 hash, detect all copies instantly
- **Search Within Results** — Ctrl+F to narrow down current results
- **Regex Support** — Full regex search with `regex:` prefix
- **Tab Support** — Up to 8 simultaneous search tabs

### Indexing
- **3-Phase Parallel Indexing** — Phase 1: metadata scan (seconds), Phase 2: content indexing (background), Phase 3: SHA-256 hashing (background)
- **ThreadPoolExecutor** — Parallel drive scanning and content reading
- **Dynamic Drive Detection** — Automatically finds all drives (A:-Z:)
- **Real-Time File Watching** — Index stays current via filesystem events
- **Incremental Updates** — Only re-indexes changed files

### Organization
- **Duplicate Finder** — Find duplicate files using content hashing with min size filter
- **Disk Usage Analyzer** — Bar chart of largest folders
- **Statistics Dashboard** — File type distribution, size histogram, activity timeline
- **Bookmarks** — Star your favorite files for quick access
- **Pinned Results** — Pin important files to top of search results
- **Search History** — Ctrl+H to recall recent searches
- **Recent Files** — Quick access on empty search screen

### Productivity
- **Command Palette** — Ctrl+P for quick actions (VS Code style)
- **Global Hotkey** — Win+Alt+F to toggle QuickFind from anywhere
- **System Tray** — Minimize to tray, stays running in background
- **Drag & Drop** — Drag files from results to other apps
- **Multi-Select** — Select multiple files for bulk copy/export
- **Right-Click Menu** — Open, Copy, Pin, Bookmark, Compare, Export
- **File Comparison** — Select 2 files and compare side-by-side
- **Similar File Detection** — Find files with similar names
- **Export Results** — Save search results as CSV, TXT, or JSON

### UI
- **Material Design 3** — Clean, modern interface
- **5 Themes** — Light, Dark, Turquoise, Purple, System (auto-detect)
- **12 Languages** — English, Turkish, German, French, Spanish, Portuguese, Italian, Japanese, Chinese, Korean, Russian, Arabic
- **Document Preview** — Preview text, code, PDF, DOCX, image content directly
- **Image Thumbnails** — JPG, PNG, GIF, SVG, BMP previews in detail pane
- **Extension Colors** — Color-coded file type icons (30+ types)
- **Portable** — No installation, runs from any folder

## Supported Formats

| Category | Formats |
|---|---|
| Documents | PDF, DOCX, XLSX, PPTX, RTF, EPUB, TXT, MD, CSV |
| Code | PY, JS, TS, HTML, CSS, JAVA, C, C++, C#, GO, RUST, PHP, RB, and more |
| Config | JSON, XML, YAML, TOML, INI, CFG, ENV |
| Images | JPG, PNG, GIF, SVG, BMP, WEBP (thumbnail preview) |
| Archives | ZIP, RAR, 7Z, TAR, GZ, EXE, MSI (metadata only) |
| Text | LOG, RST, SQL, TEX, SRT, SH, BAT, PS1 |

## Installation

### Download (Recommended)

Download **QuickFind.exe** from the [Releases](../../releases/latest) page and run it. No installation needed.

> **Note:** Windows SmartScreen may show a warning for unsigned applications. Click **"More info"** then **"Run anyway"**. The application is fully open source.

### Build from Source

```bash
pip install -r requirements.txt
python main.py
```

To build the standalone exe:

```bash
pip install pyinstaller
pyinstaller QuickFind.spec
```

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Type` | Real-time search (auto) |
| `Enter` | Force search |
| `Ctrl+L` | Focus search bar |
| `Ctrl+F` | Filter within results |
| `Ctrl+T` | New search tab |
| `Ctrl+W` | Close current tab |
| `Ctrl+P` | Command palette |
| `Ctrl+H` | Search history |
| `Ctrl+R` | Reindex all files |
| `Ctrl+1-6` | Switch pages |
| `Win+Alt+F` | Global hotkey (show/hide) |
| `Esc` | Clear search |
| `Double-click` | Open file |
| `Right-click` | Context menu |

## Search Operators

| Operator | Example | Description |
|---|---|---|
| `ext:` | `ext:pdf,docx` | Filter by extension |
| `size:` | `size:>10MB` `size:<1KB` | Filter by file size |
| `modified:` | `modified:today` `modified:thisweek` | Filter by date |
| `folder:` | `folder:Projects` | Filter by folder name |
| `content:` | `content:password` | Search in file content only |
| `hash:` | `hash:a1b2c3...` | Search by SHA-256 hash |
| `regex:` | `regex:^test.*\.py$` | Regular expression search |

## Architecture

```
QuickFind/
├── main.py              # UI (PySide6, Material Design 3)
├── database.py          # 3-phase indexer, SQLite FTS5, file watcher
├── service.pyw          # Background tray service
├── quickfind/
│   ├── search_parser.py     # Advanced query parser
│   ├── user_data.py         # Bookmarks, history, pinned, recent
│   ├── command_palette.py   # VS Code-style Ctrl+P palette
│   ├── hotkeys.py           # Global hotkey (Win+Alt+F)
│   ├── folder_analyzer.py   # Disk usage & statistics
│   ├── file_compare.py      # Side-by-side diff
│   ├── export.py            # CSV/TXT/JSON export
│   └── thumbnails.py        # Image/PDF thumbnail cache
```

- **Search Engine**: SQLite FTS5 with BM25 ranking, directory deduplication, WAL mode
- **Indexing**: 3-phase parallel (ThreadPoolExecutor) — metadata → content → hash
- **Content Extraction**: PyMuPDF, python-docx, openpyxl, python-pptx, striprtf, ebooklib
- **UI Framework**: PySide6 (Qt6) with Material Design 3
- **File Watching**: watchdog for real-time filesystem events

## Requirements (build from source)

- Python 3.13+
- See `requirements.txt` for full dependency list

## License

MIT
