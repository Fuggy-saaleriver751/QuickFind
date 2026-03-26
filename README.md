# QuickFind

Ultra-fast desktop file search for Windows. Searches file names **and** document contents in milliseconds.

![QuickFind](quickfind.png)

## Features

- **40+ Format Support** — Search inside PDF, DOCX, XLSX, PPTX, RTF, EPUB and 35+ plain-text formats
- **FTS5 Full-Text Search** — SQLite FTS5 with BM25 ranking, millisecond results
- **Document Preview** — Preview text, PDF, DOCX, XLSX content directly in the app
- **Material Design 3 UI** — Clean, modern interface with 4 themes (Light, Dark, Turquoise, Purple)
- **12 Languages** — English, Turkish, German, French, Spanish, Portuguese, Italian, Japanese, Chinese, Korean, Russian, Arabic
- **Real-Time File Watching** — Index stays up to date automatically via filesystem events
- **Customizable Settings** — Font size, max results, content indexing depth, and more
- **Background Service** — Optional system tray service for continuous indexing
- **Portable** — No installation required, runs from any folder on any drive

## Supported Formats

| Category | Formats |
|---|---|
| Documents | PDF, DOCX, XLSX, PPTX, RTF, EPUB, TXT, MD, CSV |
| Code | PY, JS, TS, HTML, CSS, JAVA, C, C++, C#, GO, RUST, PHP, RB, and more |
| Config | JSON, XML, YAML, TOML, INI, CFG, ENV |
| Text | LOG, RST, SQL, TEX, SRT, SH, BAT, PS1 |

## Installation

### Download (Recommended)

Download the latest **QuickFind** folder from the [Releases](../../releases) page, extract it, and run `QuickFind.exe`.

> **Note:** Windows SmartScreen may show a warning for unsigned applications. Click **"More info"** then **"Run anyway"**. The application is fully open source.

### Build from Source

```bash
pip install -r requirements.txt
python QuickFind.pyw
```

To build the exe:

```bash
pip install pyinstaller
pyinstaller QuickFind.spec
```

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Enter` | Search |
| `Double-click` | Open file |
| `Ctrl+O` | Open file location in Explorer |
| `Ctrl+R` | Reindex all files |
| `Ctrl+L` | Focus search bar |
| `Ctrl+1/2/3` | Switch pages (Search / Index Status / Settings) |
| `Esc` | Clear search |

## Architecture

- **Search Engine**: SQLite FTS5 with directory deduplication and WAL mode
- **Content Extraction**: PyMuPDF (PDF), python-docx (DOCX), openpyxl (XLSX), python-pptx (PPTX), striprtf (RTF), ebooklib (EPUB)
- **UI Framework**: PySide6 (Qt6) with Material Design 3 theme system
- **File Watching**: watchdog library for real-time filesystem events

## Requirements (build from source)

- Python 3.13+
- PySide6, PyMuPDF, python-docx, openpyxl, python-pptx, striprtf, ebooklib, beautifulsoup4, watchdog

See `requirements.txt` for full list.

## License

MIT
