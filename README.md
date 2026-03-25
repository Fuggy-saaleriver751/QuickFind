# QuickFind

Ultra-fast file search application for Windows with a modern glassmorphism UI.

![QuickFind](quickfind.png)

## Features

- **FTS5 Content Search** — Full-text search across file names and contents using SQLite FTS5
- **Glassmorphism UI** — Modern dark/light theme with smooth animations
- **Instant Results** — Millisecond-level search powered by SQLite
- **Lightweight** — Runs quietly in the background with minimal resource usage

## Installation

### Download (Recommended)

Download the latest `QuickFind.exe` from the [Releases](../../releases) page and run it.

> **Note:** Windows SmartScreen may show a warning for unsigned applications. Click "More info" → "Run anyway" to proceed. The application is open source and safe to use.

### Build from Source

```bash
pip install -r requirements.txt
python QuickFind.pyw
```

## Requirements (build from source)

- Python 3.12+
- PySide6
- Pillow

## License

MIT
