"""
QuickFind — Ultra-Hızlı Dosya Arama
PySide6 · Glassmorphism · Dark/Light · FTS5 Content Search
"""

import sys, os, subprocess, time, ctypes
from datetime import datetime

# Windows'ta uygulamanın "Python" yerine "QuickFind" olarak görünmesini sağla
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("dgknk.QuickFind.1")
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QListView, QPushButton, QStatusBar,
    QStyledItemDelegate, QStyle
)
from PySide6.QtCore import (
    Qt, QSize, QRect, QThread, Signal, QModelIndex,
    QAbstractListModel, QPoint, QTimer, QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import (
    QColor, QPainter, QFont, QFontMetrics, QPen, QBrush,
    QIcon, QPainterPath, QLinearGradient, QPixmap, QPalette, QCursor
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════
#  THEMES
# ══════════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        "bg":             QColor(11, 11, 20),
        "surface":        QColor(22, 22, 42),
        "card":           QColor(26, 26, 48),
        "card_hover":     QColor(32, 32, 58),
        "card_selected":  QColor(42, 31, 94),
        "card_border":    QColor(46, 46, 80),
        "search_bg":      QColor(18, 18, 34),
        "search_border":  QColor(58, 58, 106),
        "search_focus":   QColor(124, 92, 255),
        "accent":         QColor(124, 92, 255),
        "accent_hover":   QColor(155, 127, 255),
        "accent_glow":    QColor(124, 92, 255, 30),
        "text":           QColor(240, 240, 248),
        "text_sec":       QColor(160, 160, 192),
        "text_muted":     QColor(96, 96, 128),
        "badge_bg":       QColor(32, 24, 72),
        "badge_text":     QColor(160, 143, 255),
        "divider":        QColor(30, 30, 48),
        "scrollbar":      QColor(42, 42, 74),
        "scrollbar_hover": QColor(74, 74, 122),
        "green":          QColor(74, 222, 128),
        "yellow":         QColor(251, 191, 36),
        "red":            QColor(248, 113, 113),
        "blue":           QColor(96, 165, 250),
    },
    "light": {
        "bg":             QColor(240, 240, 248),
        "surface":        QColor(255, 255, 255),
        "card":           QColor(255, 255, 255),
        "card_hover":     QColor(245, 245, 255),
        "card_selected":  QColor(232, 224, 255),
        "card_border":    QColor(208, 208, 224),
        "search_bg":      QColor(255, 255, 255),
        "search_border":  QColor(200, 200, 224),
        "search_focus":   QColor(108, 76, 224),
        "accent":         QColor(108, 76, 224),
        "accent_hover":   QColor(124, 92, 255),
        "accent_glow":    QColor(108, 76, 224, 20),
        "text":           QColor(26, 26, 46),
        "text_sec":       QColor(90, 90, 122),
        "text_muted":     QColor(144, 144, 170),
        "badge_bg":       QColor(237, 232, 248),
        "badge_text":     QColor(108, 76, 224),
        "divider":        QColor(224, 224, 236),
        "scrollbar":      QColor(208, 208, 224),
        "scrollbar_hover": QColor(176, 176, 208),
        "green":          QColor(22, 163, 74),
        "yellow":         QColor(202, 138, 4),
        "red":            QColor(220, 38, 38),
        "blue":           QColor(37, 99, 235),
    }
}

EXT_ICONS = {
    ".pdf": ("📄", "red"),    ".doc": ("📝", "blue"),   ".docx": ("📝", "blue"),
    ".xls": ("📊", "green"),  ".xlsx": ("📊", "green"), ".csv": ("📊", "green"),
    ".ppt": ("📊", "yellow"), ".pptx": ("📊", "yellow"),
    ".txt": ("📃", "text_muted"), ".md": ("📃", "text_muted"),
    ".py": ("🐍", "yellow"),  ".js": ("⚡", "yellow"),  ".ts": ("⚡", "blue"),
    ".html": ("🌐", "red"),   ".css": ("🎨", "blue"),
    ".java": ("☕", "red"),    ".cpp": ("⚙️", "blue"),   ".c": ("⚙️", "blue"),
    ".cs": ("⚙️", "accent"),  ".go": ("⚙️", "blue"),    ".rs": ("🦀", "red"),
    ".json": ("📋", "yellow"), ".xml": ("📋", "red"),    ".yaml": ("📋", "red"),
    ".jpg": ("🖼️", "green"),  ".jpeg": ("🖼️", "green"), ".png": ("🖼️", "green"),
    ".gif": ("🖼️", "yellow"), ".svg": ("🖼️", "yellow"), ".webp": ("🖼️", "green"),
    ".mp4": ("🎬", "red"),    ".avi": ("🎬", "red"),    ".mkv": ("🎬", "red"),
    ".mov": ("🎬", "red"),    ".mp3": ("🎵", "accent"), ".wav": ("🎵", "accent"),
    ".flac": ("🎵", "accent"),
    ".zip": ("📦", "yellow"), ".rar": ("📦", "yellow"), ".7z": ("📦", "yellow"),
    ".tar": ("📦", "yellow"), ".gz": ("📦", "yellow"),
    ".exe": ("⚡", "red"),    ".msi": ("⚡", "red"),    ".bat": ("⚡", "green"),
    ".ps1": ("⚡", "blue"),   ".sh": ("⚡", "green"),
    ".sql": ("🗃️", "blue"),   ".db": ("🗃️", "blue"),
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
        if d == 0: return f"Bugün {dt:%H:%M}"
        if d == 1: return f"Dün {dt:%H:%M}"
        if d < 7:  return f"{d} gün önce"
        if d < 30: return f"{d // 7} hafta önce"
        if d < 365: return f"{d // 30} ay önce"
        return f"{dt:%d.%m.%Y}"
    except:
        return ""


# ══════════════════════════════════════════════════════════════
#  DATA MODEL
# ══════════════════════════════════════════════════════════════

class ResultModel(QAbstractListModel):
    """Arama sonuçları için sıfır-kopya veri modeli"""

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
        if role == self.NameRole:    return row[0]
        if role == self.PathRole:    return row[1]
        if role == self.ExtRole:     return row[2]
        if role == self.SizeRole:    return row[3]
        if role == self.ModifiedRole: return row[4]
        if role == self.IsDirRole:   return row[5]
        if role == Qt.DisplayRole:   return row[0]
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
#  DELEGATE — Her satırı QPainter ile çizer (widget yok!)
# ══════════════════════════════════════════════════════════════

CARD_HEIGHT = 64
CARD_MARGIN = 4
CARD_RADIUS = 10

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

        # Kart alanı
        r = option.rect.adjusted(6, CARD_MARGIN // 2, -6, -(CARD_MARGIN // 2))

        # Durum renkleri
        is_selected = option.state & QStyle.State_Selected
        is_hover = option.state & QStyle.State_MouseOver

        if is_selected:
            bg = T["card_selected"]
            border = T["accent"]
        elif is_hover:
            bg = T["card_hover"]
            border = T["card_border"]
        else:
            bg = T["card"]
            border = T["card_border"]

        # Kart çiz
        path = QPainterPath()
        path.addRoundedRect(r.x(), r.y(), r.width(), r.height(), CARD_RADIUS, CARD_RADIUS)

        painter.setPen(QPen(border, 1))
        painter.setBrush(QBrush(bg))
        painter.drawPath(path)

        # Veri
        name = index.data(ResultModel.NameRole) or ""
        fpath = index.data(ResultModel.PathRole) or ""
        ext = index.data(ResultModel.ExtRole) or ""
        size = index.data(ResultModel.SizeRole) or 0
        modified = index.data(ResultModel.ModifiedRole) or 0
        is_dir = index.data(ResultModel.IsDirRole) or 0

        # Icon
        if is_dir:
            icon_text, icon_color_key = "📁", "yellow"
        else:
            icon_text, icon_color_key = EXT_ICONS.get(ext, ("📄", "text_muted"))

        icon_font = QFont("Segoe UI Emoji", 16)
        painter.setFont(icon_font)
        painter.setPen(QPen(T.get(icon_color_key, T["text_muted"])))
        icon_rect = QRect(r.x() + 14, r.y(), 36, r.height())
        painter.drawText(icon_rect, Qt.AlignCenter, icon_text)

        # Ad
        name_font = QFont("Segoe UI", 11)
        name_font.setWeight(QFont.DemiBold)
        painter.setFont(name_font)
        painter.setPen(QPen(T["text"]))
        name_rect = QRect(r.x() + 54, r.y() + 10, r.width() - 230, 22)
        fm = QFontMetrics(name_font)
        elided_name = fm.elidedText(name, Qt.ElideRight, name_rect.width())
        painter.drawText(name_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_name)

        # Yol
        dir_path = os.path.dirname(fpath)
        path_font = QFont("Segoe UI", 9)
        painter.setFont(path_font)
        painter.setPen(QPen(T["text_muted"]))
        path_rect = QRect(r.x() + 54, r.y() + 32, r.width() - 230, 20)
        pfm = QFontMetrics(path_font)
        elided_path = pfm.elidedText(dir_path, Qt.ElideMiddle, path_rect.width())
        painter.drawText(path_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_path)

        # Sağ: Boyut badge
        sz_text = fmt_size(size)
        right_x = r.x() + r.width() - 160
        if sz_text:
            badge_font = QFont("Segoe UI", 8)
            badge_font.setWeight(QFont.Medium)
            bfm = QFontMetrics(badge_font)
            bw = bfm.horizontalAdvance(sz_text) + 16
            bh = 20
            bx = right_x + 140 - bw
            by = r.y() + 10

            badge_path = QPainterPath()
            badge_path.addRoundedRect(bx, by, bw, bh, 5, 5)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(T["badge_bg"]))
            painter.drawPath(badge_path)

            painter.setFont(badge_font)
            painter.setPen(QPen(T["badge_text"]))
            painter.drawText(QRect(bx, by, bw, bh), Qt.AlignCenter, sz_text)

        # Sağ: Tarih
        tm_text = fmt_time(modified)
        if tm_text:
            time_font = QFont("Segoe UI", 8)
            painter.setFont(time_font)
            painter.setPen(QPen(T["text_muted"]))
            time_rect = QRect(right_x, r.y() + 34, 140, 18)
            painter.drawText(time_rect, Qt.AlignRight | Qt.AlignVCenter, tm_text)

        painter.restore()


# ══════════════════════════════════════════════════════════════
#  INDEXER THREAD (Qt thread-safe)
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
        # Bekle bitene kadar
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

        # DB
        from database import FileDatabase
        self.db = FileDatabase()

        self.setWindowTitle("QuickFind")
        self.setMinimumSize(660, 480)
        self.resize(820, 660)

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

        # ── Header ──────────────────────────────────
        self.header = QWidget()
        self.header.setFixedHeight(68)
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(24, 0, 20, 0)

        # Logo
        self.logo = QLabel("⚡")
        self.logo.setFont(QFont("Segoe UI Emoji", 24))

        # Başlık
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(10, 0, 0, 0)
        title_layout.setSpacing(0)
        self.title_label = QLabel("QuickFind")
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.subtitle_label = QLabel("Ultra-hızlı dosya arama")
        self.subtitle_label.setFont(QFont("Segoe UI", 9))
        title_layout.addStretch()
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        title_layout.addStretch()

        h_layout.addWidget(self.logo)
        h_layout.addWidget(title_widget)
        h_layout.addStretch()

        # Theme toggle
        self.theme_btn = QPushButton("☀️")
        self.theme_btn.setFont(QFont("Segoe UI Emoji", 14))
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.theme_btn.clicked.connect(self._toggle_theme)

        # Reindex button
        self.reindex_btn = QPushButton("↻  Yeniden İndeksle")
        self.reindex_btn.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        self.reindex_btn.setFixedHeight(40)
        self.reindex_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.reindex_btn.clicked.connect(self._reindex)

        h_layout.addWidget(self.theme_btn)
        h_layout.addSpacing(8)
        h_layout.addWidget(self.reindex_btn)

        layout.addWidget(self.header)

        # ── Divider ─────────────────────────────────
        self.divider = QWidget()
        self.divider.setFixedHeight(1)
        layout.addWidget(self.divider)

        # ── Search Bar ──────────────────────────────
        search_container = QWidget()
        sc_layout = QHBoxLayout(search_container)
        sc_layout.setContentsMargins(24, 16, 24, 8)

        self.search_wrapper = QWidget()
        sw_layout = QHBoxLayout(self.search_wrapper)
        sw_layout.setContentsMargins(16, 0, 16, 0)
        sw_layout.setSpacing(8)

        self.search_icon = QLabel("🔍")
        self.search_icon.setFont(QFont("Segoe UI Emoji", 15))
        self.search_icon.setFixedWidth(30)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Dosya veya içerik ara... (Enter ile ara)")
        self.search_input.setFont(QFont("Segoe UI", 14))
        self.search_input.setFrame(False)
        self.search_input.returnPressed.connect(self._do_search)

        self.shortcut_hint = QLabel("↵ Ara   Ctrl+O Klasör   Esc Temizle")
        self.shortcut_hint.setFont(QFont("Segoe UI", 8))

        sw_layout.addWidget(self.search_icon)
        sw_layout.addWidget(self.search_input)
        sw_layout.addWidget(self.shortcut_hint)

        sc_layout.addWidget(self.search_wrapper)
        layout.addWidget(search_container)

        # ── Stats ───────────────────────────────────
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(30, 0, 30, 4)

        self.result_count_label = QLabel("")
        self.result_count_label.setFont(QFont("Segoe UI", 10))
        self.search_time_label = QLabel("")
        self.search_time_label.setFont(QFont("Segoe UI", 10))

        stats_layout.addWidget(self.result_count_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.search_time_label)
        layout.addWidget(stats_widget)

        # ── Results List ────────────────────────────
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

        # ── Empty State ─────────────────────────────
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)

        self.empty_icon = QLabel("⚡")
        self.empty_icon.setFont(QFont("Segoe UI Emoji", 40))
        self.empty_icon.setAlignment(Qt.AlignCenter)

        self.empty_title = QLabel("Dosya aramaya başla")
        self.empty_title.setFont(QFont("Segoe UI", 16, QFont.DemiBold))
        self.empty_title.setAlignment(Qt.AlignCenter)

        self.empty_sub = QLabel("Dosya adı, uzantı veya dosya içeriği yazıp Enter'a basın")
        self.empty_sub.setFont(QFont("Segoe UI", 11))
        self.empty_sub.setAlignment(Qt.AlignCenter)

        empty_layout.addWidget(self.empty_icon)
        empty_layout.addSpacing(10)
        empty_layout.addWidget(self.empty_title)
        empty_layout.addSpacing(4)
        empty_layout.addWidget(self.empty_sub)

        layout.addWidget(self.empty_widget)

        # ── Status Bar ──────────────────────────────
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont("Segoe UI", 10))
        self.status_bar.setFixedHeight(32)
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Başlatılıyor...")
        self.idx_count_label = QLabel("")
        from database import DB_DIR
        self.db_path_label = QLabel(f"📂 İndeks: {DB_DIR}")
        self.db_path_label.setFont(QFont("Segoe UI", 9))
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.db_path_label)
        self.status_bar.addPermanentWidget(self.idx_count_label)

        # Başlangıçta list gizli
        self.list_view.hide()
        self.empty_widget.show()

        # Focus
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
        card = T["card"].name()
        accent = T["accent"].name()
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

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {bg};
            }}

            /* Header */
            #header {{
                background-color: {surface};
            }}

            /* Divider */
            #divider {{
                background-color: {divider};
            }}

            /* Search wrapper */
            #search_wrapper {{
                background-color: {search_bg};
                border: 1px solid {search_border};
                border-radius: 14px;
            }}
            #search_wrapper:focus-within {{
                border: 2px solid {search_focus};
            }}

            QLineEdit {{
                background: transparent;
                color: {text};
                border: none;
                padding: 8px 4px;
                selection-background-color: {accent};
            }}
            QLineEdit::placeholder {{
                color: {text_muted};
            }}

            /* List view */
            QListView {{
                background-color: {bg};
                border: none;
                outline: none;
            }}
            QListView::item {{
                border: none;
                padding: 0px;
            }}
            QListView::item:selected {{
                background: transparent;
            }}
            QListView::item:hover {{
                background: transparent;
            }}

            /* Scrollbar */
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 4px 2px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {scrollbar};
                min-height: 30px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {scrollbar_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}

            /* Status bar */
            QStatusBar {{
                background-color: {surface};
                color: {text_muted};
                border-top: 1px solid {divider};
            }}

            /* Buttons */
            #theme_btn {{
                background-color: {badge_bg};
                border: 1px solid {search_border};
                border-radius: 10px;
                color: {text};
            }}
            #theme_btn:hover {{
                background-color: {card};
                border-color: {accent};
            }}

            #reindex_btn {{
                background-color: {accent};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 18px;
                font-weight: 600;
            }}
            #reindex_btn:hover {{
                background-color: {accent_hover};
            }}

            /* Labels */
            QLabel {{
                color: {text};
                background: transparent;
            }}
            #subtitle {{
                color: {text_muted};
            }}
            #title_label {{
                color: {accent};
            }}
            #shortcut_hint {{
                color: {text_muted};
            }}
            #result_count {{
                color: {text_sec};
            }}
            #search_time {{
                color: {text_muted};
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

        # Object names ayarla
        self.header.setObjectName("header")
        self.divider.setObjectName("divider")
        self.search_wrapper.setObjectName("search_wrapper")
        self.theme_btn.setObjectName("theme_btn")
        self.reindex_btn.setObjectName("reindex_btn")
        self.title_label.setObjectName("title_label")
        self.subtitle_label.setObjectName("subtitle")
        self.shortcut_hint.setObjectName("shortcut_hint")
        self.result_count_label.setObjectName("result_count")
        self.search_time_label.setObjectName("search_time")
        self.empty_sub.setObjectName("empty_sub")
        self.status_label.setObjectName("status_label")
        self.idx_count_label.setObjectName("idx_count")
        self.db_path_label.setObjectName("db_path")

        self.theme_btn.setText("🌙" if is_dark else "☀️")

        # Delegate'i güncelle
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
        except:
            pass

    # ─── Search ───────────────────────────────────────────

    def _do_search(self):
        q = self.search_input.text().strip()
        if not q:
            self.model.clear()
            self.list_view.hide()
            self.empty_widget.show()
            self.empty_icon.setText("⚡")
            self.empty_title.setText("Dosya aramaya başla")
            self.empty_sub.setText("Dosya adı, uzantı veya dosya içeriği yazıp Enter'a basın")
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
            self.empty_title.setText("Sonuç bulunamadı")
            self.empty_sub.setText("Farklı bir arama terimi deneyin")

        self.result_count_label.setText(f"{len(results)} sonuç bulundu")
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
                self.status_label.setText(f"Bulunamadı: {os.path.basename(path)}")
        except Exception as e:
            self.status_label.setText(f"Hata: {e}")

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
                except:
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
            self.status_label.setText(f"Hazır — {n:,} dosya indeksli")
            self.idx_count_label.setText(f"📂 {n:,}")
            lt = self.db.get_meta("last_index_time")
            if lt:
                try:
                    if (datetime.now() - datetime.fromisoformat(lt)).total_seconds() > 7200:
                        QTimer.singleShot(3000, lambda: self._run_indexer(False))
                except:
                    pass
        else:
            self.status_label.setText("İlk indeksleme başlıyor...")
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
            self.status_label.setText("İndeksleme durduruldu")
            self.reindex_btn.setText("↻  Yeniden İndeksle")
            return
        self.reindex_btn.setText("⏹  Durdur")
        self._run_indexer(True)

    def _on_idx_progress(self, count):
        self.idx_count_label.setText(f"📂 {count:,}")

    def _on_idx_status(self, msg):
        self.status_label.setText(msg)
        if "Hazır" in msg:
            self.reindex_btn.setText("↻  Yeniden İndeksle")

    def _on_idx_done(self):
        self.reindex_btn.setText("↻  Yeniden İndeksle")
        # İndeksleme bitince watcher'ı yeniden başlat
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
    # Windows DPI awareness
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = QuickFindWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
