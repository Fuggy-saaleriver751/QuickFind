"""
QuickFind — Ultra-Fast File Search
PySide6 · Glassmorphism · Dark/Light · FTS5 Content Search
Supports: PDF, DOCX, XLSX, PPTX, RTF, EPUB + 35 plain-text formats
"""

import sys, os, subprocess, time, ctypes
from datetime import datetime

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("dgknk.QuickFind.1")

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QListView, QPushButton, QStatusBar,
    QStyledItemDelegate, QStyle, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QFrame
)
from PySide6.QtCore import (
    Qt, QSize, QRect, QThread, Signal, QModelIndex,
    QAbstractListModel, QPoint, QTimer, QPropertyAnimation,
    QEasingCurve, QSequentialAnimationGroup, QParallelAnimationGroup,
    Property, QRectF
)
from PySide6.QtGui import (
    QColor, QPainter, QFont, QFontMetrics, QPen, QBrush,
    QIcon, QPainterPath, QLinearGradient, QPixmap, QPalette,
    QCursor, QRadialGradient, QConicalGradient
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════
#  THEMES — Premium color palette
# ══════════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        "bg":               QColor(8, 8, 16),
        "bg_gradient_end":  QColor(14, 10, 28),
        "surface":          QColor(16, 16, 32),
        "surface_elevated": QColor(22, 20, 42),
        "card":             QColor(20, 18, 38),
        "card_hover":       QColor(28, 24, 52),
        "card_selected":    QColor(38, 28, 80),
        "card_border":      QColor(40, 36, 72),
        "card_border_hover": QColor(80, 60, 160),
        "search_bg":        QColor(14, 12, 28),
        "search_border":    QColor(50, 44, 90),
        "search_focus":     QColor(120, 80, 255),
        "accent":           QColor(120, 80, 255),
        "accent_secondary": QColor(200, 80, 255),
        "accent_hover":     QColor(145, 110, 255),
        "accent_glow":      QColor(120, 80, 255, 40),
        "text":             QColor(235, 235, 245),
        "text_sec":         QColor(155, 155, 185),
        "text_muted":       QColor(85, 80, 115),
        "badge_bg":         QColor(30, 22, 65),
        "badge_text":       QColor(155, 130, 255),
        "badge_green_bg":   QColor(15, 40, 25),
        "badge_green_text": QColor(80, 220, 140),
        "badge_blue_bg":    QColor(15, 25, 50),
        "badge_blue_text":  QColor(80, 160, 255),
        "badge_orange_bg":  QColor(45, 30, 10),
        "badge_orange_text": QColor(255, 180, 60),
        "divider":          QColor(28, 24, 48),
        "scrollbar":        QColor(36, 32, 64),
        "scrollbar_hover":  QColor(60, 52, 100),
        "green":            QColor(74, 222, 128),
        "yellow":           QColor(251, 191, 36),
        "red":              QColor(248, 113, 113),
        "blue":             QColor(96, 165, 250),
        "glow_primary":     QColor(120, 80, 255, 20),
        "glow_secondary":   QColor(200, 80, 255, 12),
    },
    "light": {
        "bg":               QColor(245, 244, 252),
        "bg_gradient_end":  QColor(238, 236, 248),
        "surface":          QColor(255, 255, 255),
        "surface_elevated": QColor(255, 255, 255),
        "card":             QColor(255, 255, 255),
        "card_hover":       QColor(248, 246, 255),
        "card_selected":    QColor(238, 232, 255),
        "card_border":      QColor(220, 216, 236),
        "card_border_hover": QColor(160, 130, 240),
        "search_bg":        QColor(255, 255, 255),
        "search_border":    QColor(210, 206, 230),
        "search_focus":     QColor(100, 60, 220),
        "accent":           QColor(100, 60, 220),
        "accent_secondary": QColor(180, 60, 220),
        "accent_hover":     QColor(120, 80, 240),
        "accent_glow":      QColor(100, 60, 220, 20),
        "text":             QColor(20, 18, 40),
        "text_sec":         QColor(80, 75, 110),
        "text_muted":       QColor(140, 136, 165),
        "badge_bg":         QColor(240, 236, 252),
        "badge_text":       QColor(100, 60, 220),
        "badge_green_bg":   QColor(230, 248, 236),
        "badge_green_text": QColor(22, 140, 74),
        "badge_blue_bg":    QColor(230, 240, 252),
        "badge_blue_text":  QColor(37, 99, 235),
        "badge_orange_bg":  QColor(255, 245, 230),
        "badge_orange_text": QColor(200, 120, 0),
        "divider":          QColor(228, 224, 240),
        "scrollbar":        QColor(210, 206, 226),
        "scrollbar_hover":  QColor(180, 176, 206),
        "green":            QColor(22, 163, 74),
        "yellow":           QColor(202, 138, 4),
        "red":              QColor(220, 38, 38),
        "blue":             QColor(37, 99, 235),
        "glow_primary":     QColor(100, 60, 220, 10),
        "glow_secondary":   QColor(180, 60, 220, 6),
    }
}

EXT_ICONS = {
    ".pdf": ("", "red"),      ".doc": ("", "blue"),     ".docx": ("", "blue"),
    ".xls": ("", "green"),    ".xlsx": ("", "green"),   ".csv": ("", "green"),
    ".ppt": ("", "yellow"),   ".pptx": ("", "yellow"),
    ".txt": ("", "text_muted"), ".md": ("", "text_muted"),
    ".py": ("", "yellow"),    ".js": ("", "yellow"),    ".ts": ("", "blue"),
    ".html": ("", "red"),     ".css": ("", "blue"),
    ".java": ("", "red"),     ".cpp": ("", "blue"),     ".c": ("", "blue"),
    ".cs": ("", "accent"),    ".go": ("", "blue"),      ".rs": ("", "red"),
    ".json": ("", "yellow"),  ".xml": ("", "red"),      ".yaml": ("", "red"),
    ".jpg": ("", "green"),    ".jpeg": ("", "green"),   ".png": ("", "green"),
    ".gif": ("", "yellow"),   ".svg": ("", "yellow"),   ".webp": ("", "green"),
    ".mp4": ("", "red"),      ".avi": ("", "red"),      ".mkv": ("", "red"),
    ".mov": ("", "red"),      ".mp3": ("", "accent"),   ".wav": ("", "accent"),
    ".flac": ("", "accent"),
    ".zip": ("", "yellow"),   ".rar": ("", "yellow"),   ".7z": ("", "yellow"),
    ".tar": ("", "yellow"),   ".gz": ("", "yellow"),
    ".exe": ("", "red"),      ".msi": ("", "red"),      ".bat": ("", "green"),
    ".ps1": ("", "blue"),     ".sh": ("", "green"),
    ".sql": ("", "blue"),     ".db": ("", "blue"),
    ".rtf": ("", "blue"),     ".epub": ("", "green"),
}

# Extension to display label
EXT_LABELS = {
    ".pdf": "PDF", ".docx": "DOCX", ".doc": "DOC", ".xlsx": "XLSX",
    ".xls": "XLS", ".pptx": "PPTX", ".ppt": "PPT", ".csv": "CSV",
    ".py": "PY", ".js": "JS", ".ts": "TS", ".html": "HTML",
    ".css": "CSS", ".java": "JAVA", ".cpp": "C++", ".c": "C",
    ".cs": "C#", ".go": "GO", ".rs": "RUST", ".json": "JSON",
    ".xml": "XML", ".yaml": "YAML", ".md": "MD", ".txt": "TXT",
    ".jpg": "JPG", ".png": "PNG", ".gif": "GIF", ".svg": "SVG",
    ".mp4": "MP4", ".mp3": "MP3", ".zip": "ZIP", ".rar": "RAR",
    ".exe": "EXE", ".sql": "SQL", ".rtf": "RTF", ".epub": "EPUB",
}


def fmt_size(s):
    if not s:
        return ""
    for u in ("B", "KB", "MB", "GB", "TB"):
        if s < 1024:
            return f"{s:.0f} {u}" if u == "B" else f"{s:.1f} {u}"
        s /= 1024
    return f"{s:.1f} PB"


def fmt_time(ts):
    if not ts:
        return ""
    try:
        dt = datetime.fromtimestamp(ts)
        d = (datetime.now() - dt).days
        if d == 0:
            return f"Today {dt:%H:%M}"
        if d == 1:
            return f"Yesterday {dt:%H:%M}"
        if d < 7:
            return f"{d}d ago"
        if d < 30:
            return f"{d // 7}w ago"
        if d < 365:
            return f"{d // 30}mo ago"
        return f"{dt:%d.%m.%Y}"
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════
#  DATA MODEL
# ══════════════════════════════════════════════════════════════

class ResultModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    PathRole = Qt.UserRole + 2
    ExtRole = Qt.UserRole + 3
    SizeRole = Qt.UserRole + 4
    ModifiedRole = Qt.UserRole + 5
    IsDirRole = Qt.UserRole + 6

    def __init__(self):
        super().__init__()
        self._data = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._data):
            return None
        row = self._data[index.row()]
        if role == self.NameRole:     return row[0]
        if role == self.PathRole:     return row[1]
        if role == self.ExtRole:      return row[2]
        if role == self.SizeRole:     return row[3]
        if role == self.ModifiedRole: return row[4]
        if role == self.IsDirRole:    return row[5]
        if role == Qt.DisplayRole:    return row[0]
        return None

    def set_results(self, results):
        self.beginResetModel()
        self._data = results
        self.endResetModel()

    def clear(self):
        self.beginResetModel()
        self._data = []
        self.endResetModel()

    def get_path(self, index):
        if 0 <= index < len(self._data):
            return self._data[index][1]
        return None


# ══════════════════════════════════════════════════════════════
#  DELEGATE — Premium card rendering
# ══════════════════════════════════════════════════════════════

CARD_HEIGHT = 72
CARD_MARGIN = 3
CARD_RADIUS = 14

class ResultDelegate(QStyledItemDelegate):
    def __init__(self, theme_getter, parent=None):
        super().__init__(parent)
        self._theme = theme_getter

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), CARD_HEIGHT + CARD_MARGIN)

    def paint(self, painter, option, index):
        T = self._theme()
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        r = option.rect.adjusted(10, CARD_MARGIN, -10, 0)

        is_selected = option.state & QStyle.State_Selected
        is_hover = option.state & QStyle.State_MouseOver

        if is_selected:
            bg = T["card_selected"]
            border = T["accent"]
            border_width = 1.5
        elif is_hover:
            bg = T["card_hover"]
            border = T["card_border_hover"]
            border_width = 1
        else:
            bg = T["card"]
            border = T["card_border"]
            border_width = 0.5

        # Card shape
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), CARD_RADIUS, CARD_RADIUS)

        # Subtle gradient on card background
        grad = QLinearGradient(r.x(), r.y(), r.x(), r.y() + r.height())
        grad.setColorAt(0, bg)
        darker = QColor(bg)
        darker.setAlpha(max(0, bg.alpha() - 8))
        grad.setColorAt(1, darker)

        painter.setPen(QPen(border, border_width))
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

        # Glow effect on selected
        if is_selected:
            glow = QPainterPath()
            glow.addRoundedRect(QRectF(r).adjusted(-1, -1, 1, 1), CARD_RADIUS + 1, CARD_RADIUS + 1)
            glow_color = QColor(T["accent"])
            glow_color.setAlpha(25)
            painter.setPen(QPen(glow_color, 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(glow)

        # Data
        name = index.data(ResultModel.NameRole) or ""
        fpath = index.data(ResultModel.PathRole) or ""
        ext = index.data(ResultModel.ExtRole) or ""
        size = index.data(ResultModel.SizeRole) or 0
        modified = index.data(ResultModel.ModifiedRole) or 0
        is_dir = index.data(ResultModel.IsDirRole) or 0

        left_x = r.x() + 18
        content_top = r.y() + 14

        # ── Extension badge (left side) ──
        ext_label = "FOLDER" if is_dir else EXT_LABELS.get(ext, ext.replace(".", "").upper()[:5])
        if ext_label:
            badge_font = QFont("Segoe UI", 7, QFont.Bold)
            bfm = QFontMetrics(badge_font)
            bw = max(bfm.horizontalAdvance(ext_label) + 14, 38)
            bh = 22
            bx = left_x
            by = r.y() + (r.height() - bh) // 2

            if is_dir:
                badge_bg = T["badge_orange_bg"]
                badge_text = T["badge_orange_text"]
            elif ext in (".pdf", ".docx", ".doc", ".rtf"):
                badge_bg = T["badge_bg"]
                badge_text = T["badge_text"]
            elif ext in (".xlsx", ".xls", ".csv"):
                badge_bg = T["badge_green_bg"]
                badge_text = T["badge_green_text"]
            elif ext in (".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs", ".go", ".rs"):
                badge_bg = T["badge_blue_bg"]
                badge_text = T["badge_blue_text"]
            else:
                badge_bg = T["badge_bg"]
                badge_text = T["badge_text"]

            badge_path = QPainterPath()
            badge_path.addRoundedRect(bx, by, bw, bh, 6, 6)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(badge_bg))
            painter.drawPath(badge_path)

            painter.setFont(badge_font)
            painter.setPen(QPen(badge_text))
            painter.drawText(QRect(int(bx), int(by), int(bw), int(bh)), Qt.AlignCenter, ext_label)

            text_left = int(bx + bw + 14)
        else:
            text_left = left_x + 8

        # ── File name ──
        name_font = QFont("Segoe UI", 11)
        name_font.setWeight(QFont.DemiBold)
        painter.setFont(name_font)
        painter.setPen(QPen(T["text"]))
        name_rect = QRect(text_left, int(content_top), r.width() - (text_left - r.x()) - 170, 22)
        fm = QFontMetrics(name_font)
        elided_name = fm.elidedText(name, Qt.ElideRight, name_rect.width())
        painter.drawText(name_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_name)

        # ── Path ──
        dir_path = os.path.dirname(fpath)
        path_font = QFont("Segoe UI", 8)
        painter.setFont(path_font)
        painter.setPen(QPen(T["text_muted"]))
        path_rect = QRect(text_left, int(content_top + 24), r.width() - (text_left - r.x()) - 170, 18)
        pfm = QFontMetrics(path_font)
        elided_path = pfm.elidedText(dir_path, Qt.ElideMiddle, path_rect.width())
        painter.drawText(path_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_path)

        # ── Right side: Size ──
        right_x = r.x() + r.width() - 155

        sz_text = fmt_size(size)
        if sz_text and not is_dir:
            size_font = QFont("Segoe UI", 9, QFont.Medium)
            painter.setFont(size_font)
            painter.setPen(QPen(T["text_sec"]))
            size_rect = QRect(right_x, int(content_top), 140, 20)
            painter.drawText(size_rect, Qt.AlignRight | Qt.AlignVCenter, sz_text)

        # ── Right side: Time ──
        tm_text = fmt_time(modified)
        if tm_text:
            time_font = QFont("Segoe UI", 8)
            painter.setFont(time_font)
            painter.setPen(QPen(T["text_muted"]))
            time_rect = QRect(right_x, int(content_top + 24), 140, 18)
            painter.drawText(time_rect, Qt.AlignRight | Qt.AlignVCenter, tm_text)

        painter.restore()


# ══════════════════════════════════════════════════════════════
#  ANIMATED GLOW WIDGET
# ══════════════════════════════════════════════════════════════

class GlowWidget(QWidget):
    """Subtle animated background glow."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def _tick(self):
        self._phase = (self._phase + 1) % 360
        self.update()

    def paintEvent(self, event):
        if not self.parent():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        import math
        cx = self.width() * 0.5 + math.sin(math.radians(self._phase)) * 60
        cy = self.height() * 0.3 + math.cos(math.radians(self._phase * 0.7)) * 30

        grad = QRadialGradient(cx, cy, self.width() * 0.5)
        grad.setColorAt(0, QColor(120, 80, 255, 12))
        grad.setColorAt(0.5, QColor(200, 80, 255, 6))
        grad.setColorAt(1, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawRect(self.rect())
        painter.end()


# ══════════════════════════════════════════════════════════════
#  INDEXER THREAD
# ══════════════════════════════════════════════════════════════

class IndexerThread(QThread):
    progress = Signal(int)
    status = Signal(str)
    finished_indexing = Signal()

    def __init__(self, db, reindex=True):
        super().__init__()
        self.db = db
        self.reindex = reindex
        from database import FileIndexer
        self.indexer = FileIndexer(
            db,
            progress_callback=lambda c: self.progress.emit(c),
            status_callback=lambda m: self.status.emit(m)
        )

    def run(self):
        self.indexer.start(reindex=self.reindex)
        if self.indexer._thread:
            self.indexer._thread.join()
        self.finished_indexing.emit()

    def stop(self):
        self.indexer.stop()


# ══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════

class QuickFindWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_dark = True
        self.T = THEMES["dark"]
        self._indexer_thread = None
        self._file_watcher = None

        from database import FileDatabase
        self.db = FileDatabase()

        self.setWindowTitle("QuickFind")
        self.setMinimumSize(720, 520)
        self.resize(900, 700)

        ico = os.path.join(SCRIPT_DIR, "quickfind.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        self._build_ui()
        self._apply_theme()
        self._apply_win_effects()
        self._start_indexing()
        self._start_watcher()

    def _get_theme(self):
        return self.T

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Background glow ──
        self._glow = GlowWidget(central)
        self._glow.setGeometry(0, 0, 900, 700)

        # ── Header ──
        self.header = QWidget()
        self.header.setFixedHeight(76)
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(28, 0, 24, 0)

        # Logo with gradient text effect
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(14)

        self.logo_icon = QLabel()
        self.logo_icon.setFixedSize(42, 42)

        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(1)

        self.title_label = QLabel("QuickFind")
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))

        self.subtitle_label = QLabel("Search everything, instantly")
        self.subtitle_label.setFont(QFont("Segoe UI", 9))

        title_layout.addStretch()
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        title_layout.addStretch()

        logo_layout.addWidget(self.logo_icon)
        logo_layout.addWidget(title_widget)

        h_layout.addWidget(logo_container)
        h_layout.addStretch()

        # Supported formats indicator
        self.formats_label = QLabel("PDF  DOCX  XLSX  PPTX  EPUB  +35")
        self.formats_label.setFont(QFont("Segoe UI", 7, QFont.Medium))

        h_layout.addWidget(self.formats_label)
        h_layout.addSpacing(16)

        # Theme toggle
        self.theme_btn = QPushButton()
        self.theme_btn.setFixedSize(42, 42)
        self.theme_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.theme_btn.clicked.connect(self._toggle_theme)

        # Reindex button
        self.reindex_btn = QPushButton("Reindex")
        self.reindex_btn.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        self.reindex_btn.setFixedHeight(42)
        self.reindex_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.reindex_btn.clicked.connect(self._reindex)

        h_layout.addWidget(self.theme_btn)
        h_layout.addSpacing(8)
        h_layout.addWidget(self.reindex_btn)

        layout.addWidget(self.header)

        # ── Divider with gradient ──
        self.divider = QFrame()
        self.divider.setFixedHeight(1)
        layout.addWidget(self.divider)

        # ── Search Bar ──
        search_container = QWidget()
        sc_layout = QHBoxLayout(search_container)
        sc_layout.setContentsMargins(28, 20, 28, 8)

        self.search_wrapper = QWidget()
        self.search_wrapper.setFixedHeight(56)
        sw_layout = QHBoxLayout(self.search_wrapper)
        sw_layout.setContentsMargins(20, 0, 20, 0)
        sw_layout.setSpacing(12)

        self.search_icon = QLabel()
        self.search_icon.setFixedWidth(24)
        self.search_icon.setFont(QFont("Segoe UI", 16))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files, contents, documents...")
        self.search_input.setFont(QFont("Segoe UI", 14))
        self.search_input.setFrame(False)
        self.search_input.returnPressed.connect(self._do_search)

        self.shortcut_hint = QLabel("Enter  |  Ctrl+O folder  |  Esc clear")
        self.shortcut_hint.setFont(QFont("Segoe UI", 8))

        sw_layout.addWidget(self.search_icon)
        sw_layout.addWidget(self.search_input)
        sw_layout.addWidget(self.shortcut_hint)

        sc_layout.addWidget(self.search_wrapper)
        layout.addWidget(search_container)

        # ── Stats bar ──
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(34, 2, 34, 6)

        self.result_count_label = QLabel("")
        self.result_count_label.setFont(QFont("Segoe UI", 9, QFont.Medium))
        self.search_time_label = QLabel("")
        self.search_time_label.setFont(QFont("Segoe UI", 9))

        stats_layout.addWidget(self.result_count_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.search_time_label)
        layout.addWidget(stats_widget)

        # ── Results List ──
        self.model = ResultModel()
        self.delegate = ResultDelegate(self._get_theme)

        self.list_view = QListView()
        self.list_view.setModel(self.model)
        self.list_view.setItemDelegate(self.delegate)
        self.list_view.setVerticalScrollMode(QListView.ScrollPerPixel)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_view.setSelectionMode(QListView.SingleSelection)
        self.list_view.setMouseTracking(True)
        self.list_view.setFrameShape(QListView.NoFrame)
        self.list_view.doubleClicked.connect(self._on_double_click)
        self.list_view.setUniformItemSizes(True)

        layout.addWidget(self.list_view)

        # ── Empty State ──
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(8)

        self.empty_icon = QLabel()
        self.empty_icon.setFont(QFont("Segoe UI", 48))
        self.empty_icon.setAlignment(Qt.AlignCenter)

        self.empty_title = QLabel("Search your files")
        self.empty_title.setFont(QFont("Segoe UI", 18, QFont.DemiBold))
        self.empty_title.setAlignment(Qt.AlignCenter)

        self.empty_sub = QLabel("Type a file name, extension, or search inside documents\nSupports PDF, DOCX, XLSX, PPTX, EPUB, RTF and 35+ text formats")
        self.empty_sub.setFont(QFont("Segoe UI", 10))
        self.empty_sub.setAlignment(Qt.AlignCenter)

        # Format badges
        formats_row = QWidget()
        fr_layout = QHBoxLayout(formats_row)
        fr_layout.setAlignment(Qt.AlignCenter)
        fr_layout.setSpacing(6)
        self._format_badges = []
        for fmt in ["PDF", "DOCX", "XLSX", "PPTX", "EPUB", "RTF", "PY", "JS", "+"]:
            badge = QLabel(fmt)
            badge.setFont(QFont("Segoe UI", 8, QFont.Bold))
            badge.setFixedHeight(26)
            badge.setMinimumWidth(42)
            badge.setAlignment(Qt.AlignCenter)
            fr_layout.addWidget(badge)
            self._format_badges.append(badge)

        empty_layout.addWidget(self.empty_icon)
        empty_layout.addSpacing(6)
        empty_layout.addWidget(self.empty_title)
        empty_layout.addWidget(self.empty_sub)
        empty_layout.addSpacing(12)
        empty_layout.addWidget(formats_row)

        layout.addWidget(self.empty_widget)

        # ── Status Bar ──
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont("Segoe UI", 9))
        self.status_bar.setFixedHeight(34)
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Starting...")
        self.idx_count_label = QLabel("")
        from database import DB_DIR
        self.db_path_label = QLabel(f"Index: {DB_DIR}")
        self.db_path_label.setFont(QFont("Segoe UI", 8))
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.db_path_label)
        self.status_bar.addPermanentWidget(self.idx_count_label)

        # Initial state
        self.list_view.hide()
        self.empty_widget.show()
        self.search_input.setFocus()

        # Shortcuts
        from PySide6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("Return"), self, self._open_selected)
        QShortcut(QKeySequence("Ctrl+O"), self, self._open_in_folder)
        QShortcut(QKeySequence("Escape"), self, self._clear_search)
        QShortcut(QKeySequence("Ctrl+R"), self, self._reindex)
        QShortcut(QKeySequence("Ctrl+L"), self, self._focus_search)
        QShortcut(QKeySequence("Ctrl+D"), self, self._toggle_theme)

    # ─── Theme ────────────────────────────────────────────

    def _apply_theme(self):
        T = self.T
        is_dark = self.is_dark

        bg = T["bg"].name()
        surface = T["surface"].name()
        surface_el = T["surface_elevated"].name()
        accent = T["accent"].name()
        accent_sec = T["accent_secondary"].name()
        accent_hover = T["accent_hover"].name()
        text = T["text"].name()
        text_sec = T["text_sec"].name()
        text_muted = T["text_muted"].name()
        divider = T["divider"].name()
        search_bg = T["search_bg"].name()
        search_border = T["search_border"].name()
        search_focus = T["search_focus"].name()
        scrollbar = T["scrollbar"].name()
        scrollbar_hover = T["scrollbar_hover"].name()
        badge_bg = T["badge_bg"].name()
        badge_text = T["badge_text"].name()

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {bg};
            }}

            #header {{
                background-color: {surface};
            }}

            #divider {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {divider}, stop:0.3 {accent}, stop:0.7 {accent_sec}, stop:1 {divider});
            }}

            #search_wrapper {{
                background-color: {search_bg};
                border: 1.5px solid {search_border};
                border-radius: 16px;
            }}
            #search_wrapper:focus-within {{
                border: 2px solid {search_focus};
            }}

            QLineEdit {{
                background: transparent;
                color: {text};
                border: none;
                padding: 10px 4px;
                selection-background-color: {accent};
            }}
            QLineEdit::placeholder {{
                color: {text_muted};
            }}

            QListView {{
                background-color: {bg};
                border: none;
                outline: none;
            }}
            QListView::item {{
                border: none;
                padding: 0px;
            }}
            QListView::item:selected, QListView::item:hover {{
                background: transparent;
            }}

            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 8px 2px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {scrollbar};
                min-height: 40px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {scrollbar_hover};
                width: 8px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}

            QStatusBar {{
                background-color: {surface};
                color: {text_muted};
                border-top: 1px solid {divider};
            }}

            #theme_btn {{
                background-color: {badge_bg};
                border: 1.5px solid {search_border};
                border-radius: 12px;
                font-size: 18px;
            }}
            #theme_btn:hover {{
                background-color: {surface_el};
                border-color: {accent};
            }}

            #reindex_btn {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent}, stop:1 {accent_sec});
                color: white;
                border: none;
                border-radius: 12px;
                padding: 0 22px;
                font-weight: 600;
            }}
            #reindex_btn:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent_hover}, stop:1 {accent_sec});
            }}

            QLabel {{
                color: {text};
                background: transparent;
            }}
            #subtitle {{
                color: {text_muted};
            }}
            #title_label {{
                color: {text};
            }}
            #formats_label {{
                color: {text_muted};
                padding: 4px 10px;
                background: {badge_bg};
                border-radius: 8px;
            }}
            #shortcut_hint {{
                color: {text_muted};
            }}
            #result_count {{
                color: {accent};
            }}
            #search_time {{
                color: {text_muted};
            }}
            #empty_icon {{
                color: {accent};
            }}
            #empty_title {{
                color: {text};
            }}
            #empty_sub {{
                color: {text_muted};
            }}
            #status_label {{
                color: {text_muted};
            }}
            #idx_count {{
                color: {text_muted};
            }}
            #db_path {{
                color: {text_muted};
                padding-right: 12px;
            }}
        """)

        # Object names
        self.header.setObjectName("header")
        self.divider.setObjectName("divider")
        self.search_wrapper.setObjectName("search_wrapper")
        self.theme_btn.setObjectName("theme_btn")
        self.reindex_btn.setObjectName("reindex_btn")
        self.title_label.setObjectName("title_label")
        self.subtitle_label.setObjectName("subtitle")
        self.formats_label.setObjectName("formats_label")
        self.shortcut_hint.setObjectName("shortcut_hint")
        self.result_count_label.setObjectName("result_count")
        self.search_time_label.setObjectName("search_time")
        self.empty_icon.setObjectName("empty_icon")
        self.empty_title.setObjectName("empty_title")
        self.empty_sub.setObjectName("empty_sub")
        self.status_label.setObjectName("status_label")
        self.idx_count_label.setObjectName("idx_count")
        self.db_path_label.setObjectName("db_path")

        # Dynamic content
        self.theme_btn.setText("☀" if is_dark else "🌙")
        self.search_icon.setText("🔍")
        self.empty_icon.setText("⚡")
        self.logo_icon.setText("⚡")
        self.logo_icon.setFont(QFont("Segoe UI Emoji", 22))
        self.logo_icon.setAlignment(Qt.AlignCenter)

        # Format badges styling
        for badge in self._format_badges:
            badge.setStyleSheet(f"""
                background-color: {badge_bg};
                color: {badge_text};
                border-radius: 6px;
                padding: 2px 8px;
            """)

        self.list_view.viewport().update()

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        self.T = THEMES["dark" if self.is_dark else "light"]
        self._apply_theme()
        self._apply_win_effects()

    def _apply_win_effects(self):
        try:
            hwnd = int(self.winId())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1 if self.is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value), ctypes.sizeof(value)
            )
            # Mica/acrylic effect on Windows 11
            DWMWA_SYSTEMBACKDROP_TYPE = 38
            backdrop = ctypes.c_int(2)  # Mica
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_SYSTEMBACKDROP_TYPE,
                ctypes.byref(backdrop), ctypes.sizeof(backdrop)
            )
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_glow'):
            self._glow.setGeometry(0, 0, self.width(), self.height())

    # ─── Search ───────────────────────────────────────────

    def _do_search(self):
        q = self.search_input.text().strip()
        if not q:
            self.model.clear()
            self.list_view.hide()
            self.empty_widget.show()
            self.empty_icon.setText("⚡")
            self.empty_title.setText("Search your files")
            self.empty_sub.setText("Type a file name, extension, or search inside documents\nSupports PDF, DOCX, XLSX, PPTX, EPUB, RTF and 35+ text formats")
            self.result_count_label.setText("")
            self.search_time_label.setText("")
            return

        t0 = time.perf_counter()
        results = self.db.search(q, limit=200)
        ms = (time.perf_counter() - t0) * 1000

        if results:
            self.model.set_results(results)
            self.empty_widget.hide()
            self.list_view.show()
            self.list_view.setCurrentIndex(self.model.index(0))
        else:
            self.model.clear()
            self.list_view.hide()
            self.empty_widget.show()
            self.empty_icon.setText("🔍")
            self.empty_title.setText("No results found")
            self.empty_sub.setText("Try a different search term")

        self.result_count_label.setText(f"{len(results)} results")
        self.search_time_label.setText(f"⚡ {ms:.1f} ms")

    # ─── Actions ──────────────────────────────────────────

    def _open_selected(self):
        idx = self.list_view.currentIndex()
        if idx.isValid():
            path = self.model.get_path(idx.row())
            if path:
                self._open_file(path)

    def _open_file(self, path):
        try:
            if os.path.exists(path):
                os.startfile(path)
            else:
                self.status_label.setText(f"Not found: {os.path.basename(path)}")
        except Exception as e:
            self.status_label.setText(f"Error: {e}")

    def _on_double_click(self, index):
        path = self.model.get_path(index.row())
        if path:
            self._open_file(path)

    def _open_in_folder(self):
        idx = self.list_view.currentIndex()
        if idx.isValid():
            path = self.model.get_path(idx.row())
            if path:
                try:
                    if os.path.exists(path):
                        subprocess.Popen(["explorer", "/select,", path])
                    elif os.path.exists(os.path.dirname(path)):
                        os.startfile(os.path.dirname(path))
                except Exception:
                    pass

    def _clear_search(self):
        self.search_input.clear()
        self.search_input.setFocus()
        self.model.clear()
        self.list_view.hide()
        self.empty_widget.show()
        self.result_count_label.setText("")
        self.search_time_label.setText("")

    def _focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    # ─── Indexing ─────────────────────────────────────────

    def _start_indexing(self):
        n = self.db.get_file_count()
        if n > 0:
            self.status_label.setText(f"Ready — {n:,} files indexed")
            self.idx_count_label.setText(f"  {n:,} files")
            lt = self.db.get_meta("last_index_time")
            if lt:
                try:
                    if (datetime.now() - datetime.fromisoformat(lt)).total_seconds() > 7200:
                        QTimer.singleShot(3000, lambda: self._run_indexer(False))
                except Exception:
                    pass
        else:
            self.status_label.setText("First indexing starting...")
            QTimer.singleShot(500, lambda: self._run_indexer(True))

    def _run_indexer(self, reindex):
        if self._indexer_thread and self._indexer_thread.isRunning():
            return
        self._indexer_thread = IndexerThread(self.db, reindex)
        self._indexer_thread.progress.connect(self._on_idx_progress)
        self._indexer_thread.status.connect(self._on_idx_status)
        self._indexer_thread.finished_indexing.connect(self._on_idx_done)
        self._indexer_thread.start()

    def _reindex(self):
        if self._indexer_thread and self._indexer_thread.isRunning():
            self._indexer_thread.stop()
            self.status_label.setText("Indexing stopped")
            self.reindex_btn.setText("Reindex")
            return
        self.reindex_btn.setText("Stop")
        self._run_indexer(True)

    def _on_idx_progress(self, count):
        self.idx_count_label.setText(f"  {count:,} files")

    def _on_idx_status(self, msg):
        self.status_label.setText(msg)
        if "Ready" in msg:
            self.reindex_btn.setText("Reindex")

    def _on_idx_done(self):
        self.reindex_btn.setText("Reindex")
        self._start_watcher()

    # ─── File Watcher ─────────────────────────────────────

    def _start_watcher(self):
        if self._file_watcher and self._file_watcher.is_running():
            return
        from database import FileWatcher
        self._file_watcher = FileWatcher(
            self.db,
            status_callback=lambda msg: QTimer.singleShot(0, lambda: self.status_label.setText(msg))
        )
        self._file_watcher.start()

    def _stop_watcher(self):
        if self._file_watcher:
            self._file_watcher.stop()

    # ─── Cleanup ──────────────────────────────────────────

    def closeEvent(self, event):
        self._stop_watcher()
        if self._indexer_thread and self._indexer_thread.isRunning():
            self._indexer_thread.stop()
            self._indexer_thread.wait(3000)
        self.db.close()
        event.accept()


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════

def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = QuickFindWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
