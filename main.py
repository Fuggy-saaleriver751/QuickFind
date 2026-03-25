"""
QuickFind — Ultra-Fast File Search
PySide6 · Neon Glassmorphism · Dark/Light · FTS5 Content Search
Supports: PDF, DOCX, XLSX, PPTX, RTF, EPUB + 35 plain-text formats
"""

import sys, os, subprocess, time, ctypes, math
from datetime import datetime

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("dgknk.QuickFind.1")

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QListView, QPushButton, QStatusBar,
    QStyledItemDelegate, QStyle, QFrame, QGraphicsDropShadowEffect,
    QDialog, QRadioButton, QButtonGroup, QMessageBox
)
from PySide6.QtCore import (
    Qt, QSize, QRect, QThread, Signal, QModelIndex,
    QAbstractListModel, QTimer, QRectF, QPointF
)
from PySide6.QtGui import (
    QColor, QPainter, QFont, QFontMetrics, QPen, QBrush,
    QIcon, QPainterPath, QLinearGradient, QPixmap, QCursor,
    QRadialGradient, QShortcut, QKeySequence
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════
#  THEMES — Cyberpunk / Tech palette
# ══════════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        "bg":               QColor(6, 6, 12),
        "surface":          QColor(10, 10, 20),
        "surface_elevated": QColor(16, 16, 30),
        "card":             QColor(12, 12, 24),
        "card_hover":       QColor(18, 16, 36),
        "card_selected":    QColor(24, 16, 56),
        "card_border":      QColor(30, 28, 56),
        "card_border_hover": QColor(100, 60, 220, 120),
        "search_bg":        QColor(8, 8, 18),
        "search_border":    QColor(40, 36, 72),
        "search_focus":     QColor(100, 60, 255),
        "accent":           QColor(100, 60, 255),
        "accent2":          QColor(0, 210, 255),
        "accent3":          QColor(255, 40, 150),
        "accent_hover":     QColor(130, 90, 255),
        "text":             QColor(230, 230, 242),
        "text_sec":         QColor(140, 140, 175),
        "text_muted":       QColor(65, 62, 95),
        "badge_purple_bg":  QColor(25, 16, 55),
        "badge_purple_text": QColor(160, 130, 255),
        "badge_cyan_bg":    QColor(8, 30, 38),
        "badge_cyan_text":  QColor(0, 210, 255),
        "badge_green_bg":   QColor(8, 32, 18),
        "badge_green_text": QColor(0, 230, 118),
        "badge_pink_bg":    QColor(35, 10, 28),
        "badge_pink_text":  QColor(255, 80, 180),
        "badge_orange_bg":  QColor(35, 22, 8),
        "badge_orange_text": QColor(255, 160, 40),
        "divider":          QColor(20, 18, 38),
        "scrollbar":        QColor(28, 26, 50),
        "scrollbar_hover":  QColor(50, 44, 85),
        "green":            QColor(0, 230, 118),
        "yellow":           QColor(255, 200, 40),
        "red":              QColor(255, 60, 80),
        "blue":             QColor(0, 150, 255),
        "grid_line":        QColor(20, 18, 40),
        "glow1":            QColor(100, 60, 255, 30),
        "glow2":            QColor(0, 210, 255, 18),
        "glow3":            QColor(255, 40, 150, 12),
    },
    "light": {
        "bg":               QColor(245, 244, 252),
        "surface":          QColor(255, 255, 255),
        "surface_elevated": QColor(255, 255, 255),
        "card":             QColor(255, 255, 255),
        "card_hover":       QColor(248, 246, 255),
        "card_selected":    QColor(238, 232, 255),
        "card_border":      QColor(220, 216, 238),
        "card_border_hover": QColor(130, 90, 220, 150),
        "search_bg":        QColor(255, 255, 255),
        "search_border":    QColor(200, 196, 225),
        "search_focus":     QColor(90, 50, 210),
        "accent":           QColor(90, 50, 210),
        "accent2":          QColor(0, 160, 210),
        "accent3":          QColor(210, 30, 120),
        "accent_hover":     QColor(110, 70, 230),
        "text":             QColor(20, 18, 42),
        "text_sec":         QColor(70, 65, 100),
        "text_muted":       QColor(135, 130, 165),
        "badge_purple_bg":  QColor(240, 236, 255),
        "badge_purple_text": QColor(90, 50, 210),
        "badge_cyan_bg":    QColor(228, 246, 255),
        "badge_cyan_text":  QColor(0, 120, 170),
        "badge_green_bg":   QColor(228, 250, 238),
        "badge_green_text": QColor(0, 140, 65),
        "badge_pink_bg":    QColor(255, 232, 244),
        "badge_pink_text":  QColor(190, 25, 105),
        "badge_orange_bg":  QColor(255, 242, 225),
        "badge_orange_text": QColor(190, 110, 0),
        "divider":          QColor(228, 224, 242),
        "scrollbar":        QColor(210, 206, 228),
        "scrollbar_hover":  QColor(185, 180, 210),
        "green":            QColor(0, 150, 65),
        "yellow":           QColor(190, 140, 0),
        "red":              QColor(200, 35, 45),
        "blue":             QColor(0, 100, 210),
        "grid_line":        QColor(245, 244, 252, 0),
        "glow1":            QColor(90, 50, 210, 8),
        "glow2":            QColor(0, 160, 210, 5),
        "glow3":            QColor(210, 30, 120, 4),
    }
}

EXT_LABELS = {
    ".pdf": "PDF", ".docx": "DOCX", ".doc": "DOC", ".xlsx": "XLSX",
    ".xls": "XLS", ".pptx": "PPTX", ".ppt": "PPT", ".csv": "CSV",
    ".py": "PY", ".js": "JS", ".ts": "TS", ".html": "HTML",
    ".css": "CSS", ".java": "JAVA", ".cpp": "C++", ".c": "C",
    ".cs": "C#", ".go": "GO", ".rs": "RUST", ".json": "JSON",
    ".xml": "XML", ".yaml": "YML", ".md": "MD", ".txt": "TXT",
    ".jpg": "JPG", ".png": "PNG", ".gif": "GIF", ".svg": "SVG",
    ".mp4": "MP4", ".mp3": "MP3", ".zip": "ZIP", ".rar": "RAR",
    ".exe": "EXE", ".sql": "SQL", ".rtf": "RTF", ".epub": "EPUB",
    ".bat": "BAT", ".sh": "SH", ".ps1": "PS1", ".ini": "INI",
    ".log": "LOG", ".cfg": "CFG", ".toml": "TOML",
}

# Badge color mapping by category
EXT_BADGE_CATEGORY = {
    "doc":   {".pdf", ".docx", ".doc", ".rtf", ".txt", ".md", ".epub", ".rst"},
    "data":  {".xlsx", ".xls", ".csv", ".json", ".xml", ".yaml", ".yml", ".toml", ".sql", ".db"},
    "code":  {".py", ".pyw", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".java", ".cpp",
              ".c", ".cs", ".go", ".rs", ".rb", ".php", ".kt", ".scala", ".vue", ".svelte",
              ".scss", ".less", ".sh", ".bash", ".bat", ".cmd", ".ps1"},
    "media": {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".mp4", ".avi", ".mkv",
              ".mov", ".mp3", ".wav", ".flac"},
    "arch":  {".zip", ".rar", ".7z", ".tar", ".gz", ".exe", ".msi"},
}


def _get_badge_colors(ext, is_dir, T):
    if is_dir:
        return T["badge_orange_bg"], T["badge_orange_text"]
    for cat, exts in EXT_BADGE_CATEGORY.items():
        if ext in exts:
            if cat == "doc":
                return T["badge_purple_bg"], T["badge_purple_text"]
            if cat == "data":
                return T["badge_green_bg"], T["badge_green_text"]
            if cat == "code":
                return T["badge_cyan_bg"], T["badge_cyan_text"]
            if cat == "media":
                return T["badge_pink_bg"], T["badge_pink_text"]
            if cat == "arch":
                return T["badge_orange_bg"], T["badge_orange_text"]
    return T["badge_purple_bg"], T["badge_purple_text"]


def fmt_size(s):
    if not s:
        return ""
    for u in ("B", "KB", "MB", "GB", "TB"):
        if s < 1024:
            return f"{s:.0f}{u}" if u == "B" else f"{s:.1f}{u}"
        s /= 1024
    return f"{s:.1f}PB"


def fmt_time(ts):
    if not ts:
        return ""
    try:
        dt = datetime.fromtimestamp(ts)
        d = (datetime.now() - dt).days
        if d == 0:   return f"Today {dt:%H:%M}"
        if d == 1:   return "Yesterday"
        if d < 7:    return f"{d}d ago"
        if d < 30:   return f"{d//7}w ago"
        if d < 365:  return f"{d//30}mo ago"
        return f"{dt:%d.%m.%Y}"
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════
#  DATA MODEL
# ══════════════════════════════════════════════════════════════

class ResultModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    PathRole = Qt.UserRole + 2
    ExtRole  = Qt.UserRole + 3
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
#  DELEGATE — Cyberpunk card rendering
# ══════════════════════════════════════════════════════════════

CARD_H = 68
CARD_GAP = 2
CARD_R = 12

class ResultDelegate(QStyledItemDelegate):
    def __init__(self, theme_getter, parent=None):
        super().__init__(parent)
        self._theme = theme_getter

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), CARD_H + CARD_GAP)

    def paint(self, painter, option, index):
        T = self._theme()
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        r = QRectF(option.rect).adjusted(12, CARD_GAP, -12, 0)

        sel = bool(option.state & QStyle.State_Selected)
        hov = bool(option.state & QStyle.State_MouseOver)

        # ── Card background ──
        if sel:
            bg, border, bw = T["card_selected"], T["accent"], 1.5
        elif hov:
            bg, border, bw = T["card_hover"], T["card_border_hover"], 1.0
        else:
            bg, border, bw = T["card"], T["card_border"], 0.5

        card = QPainterPath()
        card.addRoundedRect(r, CARD_R, CARD_R)

        # Fill with subtle gradient
        grad = QLinearGradient(r.topLeft(), r.bottomRight())
        grad.setColorAt(0, bg)
        bg2 = QColor(bg)
        bg2.setRed(min(255, bg.red() + 4))
        bg2.setBlue(min(255, bg.blue() + 6))
        grad.setColorAt(1, bg2)

        painter.setPen(QPen(border, bw))
        painter.setBrush(QBrush(grad))
        painter.drawPath(card)

        # Neon glow on selected
        if sel:
            for i, alpha in enumerate([18, 10, 5]):
                glow_c = QColor(T["accent"])
                glow_c.setAlpha(alpha)
                painter.setPen(QPen(glow_c, 2 + i * 2))
                painter.setBrush(Qt.NoBrush)
                gp = QPainterPath()
                gp.addRoundedRect(r.adjusted(-i, -i, i, i), CARD_R + i, CARD_R + i)
                painter.drawPath(gp)

        # Left accent bar on selected
        if sel:
            bar = QPainterPath()
            bar.addRoundedRect(r.x() + 1, r.y() + 10, 3, r.height() - 20, 1.5, 1.5)
            painter.setPen(Qt.NoPen)
            bar_grad = QLinearGradient(0, r.y() + 10, 0, r.y() + r.height() - 10)
            bar_grad.setColorAt(0, T["accent"])
            bar_grad.setColorAt(1, T["accent2"])
            painter.setBrush(QBrush(bar_grad))
            painter.drawPath(bar)

        # Data
        name = index.data(ResultModel.NameRole) or ""
        fpath = index.data(ResultModel.PathRole) or ""
        ext = index.data(ResultModel.ExtRole) or ""
        size = index.data(ResultModel.SizeRole) or 0
        modified = index.data(ResultModel.ModifiedRole) or 0
        is_dir = index.data(ResultModel.IsDirRole) or 0

        lx = r.x() + 16

        # ── Extension badge ──
        ext_label = "DIR" if is_dir else EXT_LABELS.get(ext, ext.replace(".", "").upper()[:4])
        badge_bg, badge_text = _get_badge_colors(ext, is_dir, T)

        if ext_label:
            bf = QFont("Consolas", 7, QFont.Bold)
            bfm = QFontMetrics(bf)
            bw_px = max(bfm.horizontalAdvance(ext_label) + 12, 36)
            bh_px = 20
            bx = lx
            by = r.y() + (r.height() - bh_px) / 2

            bp = QPainterPath()
            bp.addRoundedRect(bx, by, bw_px, bh_px, 4, 4)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(badge_bg))
            painter.drawPath(bp)

            painter.setFont(bf)
            painter.setPen(QPen(badge_text))
            painter.drawText(QRectF(bx, by, bw_px, bh_px), Qt.AlignCenter, ext_label)

            tx = bx + bw_px + 14
        else:
            tx = lx + 8

        # ── Name (Segoe UI Semibold) ──
        nf = QFont("Segoe UI", 11, QFont.DemiBold)
        painter.setFont(nf)
        painter.setPen(QPen(T["text"]))
        max_w = r.width() - (tx - r.x()) - 140
        nr = QRectF(tx, r.y() + 13, max_w, 22)
        en = QFontMetrics(nf).elidedText(name, Qt.ElideRight, int(max_w))
        painter.drawText(nr, Qt.AlignLeft | Qt.AlignVCenter, en)

        # ── Path (monospace for tech feel) ──
        pf = QFont("Consolas", 8)
        painter.setFont(pf)
        painter.setPen(QPen(T["text_muted"]))
        dp = os.path.dirname(fpath)
        pr = QRectF(tx, r.y() + 37, max_w, 18)
        ep = QFontMetrics(pf).elidedText(dp, Qt.ElideMiddle, int(max_w))
        painter.drawText(pr, Qt.AlignLeft | Qt.AlignVCenter, ep)

        # ── Right: size with monospace ──
        rx = r.x() + r.width() - 130
        sz = fmt_size(size)
        if sz and not is_dir:
            sf = QFont("Consolas", 9, QFont.Medium)
            painter.setFont(sf)
            painter.setPen(QPen(T["text_sec"]))
            painter.drawText(QRectF(rx, r.y() + 14, 120, 20), Qt.AlignRight | Qt.AlignVCenter, sz)

        # ── Right: time ──
        tm = fmt_time(modified)
        if tm:
            tf = QFont("Consolas", 8)
            painter.setFont(tf)
            painter.setPen(QPen(T["text_muted"]))
            painter.drawText(QRectF(rx, r.y() + 36, 120, 18), Qt.AlignRight | Qt.AlignVCenter, tm)

        painter.restore()


# ══════════════════════════════════════════════════════════════
#  TECH BACKGROUND — Grid + floating orbs
# ══════════════════════════════════════════════════════════════

class TechBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tick = 0
        self._theme_colors = THEMES["dark"]
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(40)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_theme(self, T):
        self._theme_colors = T
        self.update()

    def _animate(self):
        self._tick += 1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        T = self._theme_colors

        # ── Subtle grid lines (hidden in light theme via alpha 0) ──
        grid_c = T["grid_line"]
        if grid_c.alpha() > 0:
            p.setPen(QPen(grid_c, 0.5))
            spacing = 48
            for x in range(0, w, spacing):
                p.drawLine(x, 0, x, h)
            for y in range(0, h, spacing):
                p.drawLine(0, y, w, y)

        # ── Floating orbs ──
        t = self._tick * 0.02
        orbs = [
            (0.3 + math.sin(t * 0.7) * 0.15, 0.25 + math.cos(t * 0.5) * 0.1, w * 0.35, T["glow1"]),
            (0.7 + math.sin(t * 0.5 + 2) * 0.12, 0.6 + math.cos(t * 0.8 + 1) * 0.15, w * 0.28, T["glow2"]),
            (0.5 + math.cos(t * 0.6 + 4) * 0.2, 0.8 + math.sin(t * 0.4 + 3) * 0.1, w * 0.22, T["glow3"]),
        ]
        for ox, oy, radius, color in orbs:
            cx, cy = ox * w, oy * h
            grad = QRadialGradient(cx, cy, radius)
            grad.setColorAt(0, color)
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(grad))
            p.drawEllipse(QPointF(cx, cy), radius, radius)

        # ── Scan line effect ──
        scan_y = (self._tick * 2) % (h + 60) - 30
        scan_grad = QLinearGradient(0, scan_y - 30, 0, scan_y + 30)
        scan_grad.setColorAt(0, QColor(0, 0, 0, 0))
        scan_grad.setColorAt(0.5, QColor(100, 60, 255, 8))
        scan_grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(scan_grad))
        p.drawRect(0, int(scan_y - 30), w, 60)

        p.end()


# ══════════════════════════════════════════════════════════════
#  NEON SEARCH BAR
# ══════════════════════════════════════════════════════════════

class NeonSearchBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._focused = False
        self._glow_alpha = 0
        self._theme_colors = THEMES["dark"]
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_glow)
        self._timer.start(30)

    def set_focused(self, focused):
        self._focused = focused
        self.update()

    def set_theme(self, T):
        self._theme_colors = T
        self.update()

    def _animate_glow(self):
        target = 255 if self._focused else 0
        diff = target - self._glow_alpha
        if abs(diff) > 2:
            self._glow_alpha += diff * 0.15
            self.update()
        elif self._glow_alpha != target:
            self._glow_alpha = target
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(4, 4, -4, -4)

        T = self._theme_colors

        # Glow when focused
        if self._glow_alpha > 5:
            alpha_ratio = self._glow_alpha / 255.0
            for i in range(3):
                gc = QColor(T["accent"])
                gc.setAlpha(int(12 * alpha_ratio * (3 - i)))
                gp = QPainterPath()
                gp.addRoundedRect(r.adjusted(-i * 3, -i * 3, i * 3, i * 3), 18 + i, 18 + i)
                p.setPen(QPen(gc, 2))
                p.setBrush(Qt.NoBrush)
                p.drawPath(gp)

        # Main bar
        bar = QPainterPath()
        bar.addRoundedRect(r, 16, 16)
        p.setPen(QPen(T["search_focus"] if self._focused else T["search_border"], 1.5))
        p.setBrush(QBrush(T["search_bg"]))
        p.drawPath(bar)

        # Gradient top border accent
        if self._glow_alpha > 5:
            alpha_ratio = self._glow_alpha / 255.0
            accent_grad = QLinearGradient(r.x(), r.y(), r.x() + r.width(), r.y())
            c1 = QColor(T["accent"])
            c1.setAlpha(int(150 * alpha_ratio))
            c2 = QColor(T["accent2"])
            c2.setAlpha(int(100 * alpha_ratio))
            c3 = QColor(T["accent3"])
            c3.setAlpha(int(80 * alpha_ratio))
            accent_grad.setColorAt(0, c1)
            accent_grad.setColorAt(0.5, c2)
            accent_grad.setColorAt(1, c3)
            p.setPen(QPen(QBrush(accent_grad), 2))
            p.setBrush(Qt.NoBrush)
            # Only top arc
            top_path = QPainterPath()
            top_path.moveTo(r.x() + 16, r.y())
            top_path.lineTo(r.x() + r.width() - 16, r.y())
            p.drawPath(top_path)

        p.end()


# ══════════════════════════════════════════════════════════════
#  INDEXER THREAD
# ══════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ══════════════════════════════════════════════════════════════

class SettingsDialog(QDialog):
    def __init__(self, parent=None, is_dark=True):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(420, 380)
        self.setModal(True)

        from database import PRESETS, get_preset_name

        current = get_preset_name()
        T = THEMES["dark" if is_dark else "light"]

        bg = T["bg"].name()
        surface = T["surface_elevated"].name()
        text = T["text"].name()
        text_m = T["text_muted"].name()
        accent = T["accent"].name()
        accent2 = T["accent2"].name()
        border = T["card_border"].name()
        badge_bg = T["badge_purple_bg"].name()

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg};
                color: {text};
            }}
            QLabel {{
                color: {text};
                background: transparent;
            }}
            #section_title {{
                color: {accent};
                font-family: Consolas;
                font-size: 11px;
                font-weight: bold;
            }}
            #warning_label {{
                color: {text_m};
                font-family: Consolas;
                font-size: 8px;
            }}
            QRadioButton {{
                color: {text};
                font-family: Consolas;
                font-size: 10px;
                spacing: 8px;
                padding: 8px 12px;
                background: {surface};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QRadioButton:checked {{
                border-color: {accent};
                background: {badge_bg};
            }}
            QRadioButton::indicator {{
                width: 14px;
                height: 14px;
                border-radius: 7px;
                border: 2px solid {text_m};
                background: transparent;
            }}
            QRadioButton::indicator:checked {{
                border-color: {accent};
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.4,
                    fx:0.5, fy:0.5, stop:0 {accent}, stop:1 {accent2});
            }}
            #save_btn {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent}, stop:1 {accent2});
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-family: Consolas;
                font-size: 11px;
                font-weight: bold;
            }}
            #save_btn:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent2}, stop:1 {accent});
            }}
            #cancel_btn {{
                background: {surface};
                color: {text_m};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 10px 24px;
                font-family: Consolas;
                font-size: 11px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel("CONTENT INDEXING DEPTH")
        title.setObjectName("section_title")
        layout.addWidget(title)

        warning = QLabel("// higher depth = better search accuracy, but larger database\n// changing this requires a full reindex")
        warning.setObjectName("warning_label")
        layout.addWidget(warning)
        layout.addSpacing(4)

        self._group = QButtonGroup(self)
        self._radios = {}

        preset_order = ["minimal", "standard", "deep", "maximum"]
        for key in preset_order:
            p = PRESETS[key]
            txt = f"{key.upper()}  —  {p['label']}"
            if key == "minimal":
                txt += "  [default]"
            rb = QRadioButton(txt)
            if key == current:
                rb.setChecked(True)
            self._group.addButton(rb)
            self._radios[key] = rb
            layout.addWidget(rb)

        layout.addStretch()

        # Buttons
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()

        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("SAVE & REINDEX")
        save_btn.setObjectName("save_btn")
        save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addSpacing(8)
        btn_layout.addWidget(save_btn)
        layout.addWidget(btn_row)

        self._selected_preset = current

    def _save(self):
        for key, rb in self._radios.items():
            if rb.isChecked():
                self._selected_preset = key
                break
        self.accept()

    def get_selected_preset(self):
        return self._selected_preset


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
        self._theme_colors = self.T
        self._indexer_thread = None
        self._file_watcher = None

        from database import FileDatabase
        self.db = FileDatabase()

        self.setWindowTitle("QuickFind")
        self.setMinimumSize(750, 540)
        self.resize(920, 720)

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

        # ── Tech background ──
        self._bg = TechBackground(central)
        self._bg.setGeometry(0, 0, 920, 720)

        # ── Header ──
        self.header = QWidget()
        self.header.setFixedHeight(72)
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(28, 0, 22, 0)

        # Logo
        self.logo = QLabel("⚡")
        self.logo.setFont(QFont("Segoe UI Emoji", 24))
        self.logo.setFixedSize(44, 44)
        self.logo.setAlignment(Qt.AlignCenter)

        # Title
        tw = QWidget()
        tl = QVBoxLayout(tw)
        tl.setContentsMargins(12, 0, 0, 0)
        tl.setSpacing(0)
        self.title_label = QLabel("QUICKFIND")
        self.title_label.setFont(QFont("Consolas", 20, QFont.Bold))
        self.subtitle_label = QLabel("// ultra-fast file search engine")
        self.subtitle_label.setFont(QFont("Consolas", 8))
        tl.addStretch()
        tl.addWidget(self.title_label)
        tl.addWidget(self.subtitle_label)
        tl.addStretch()

        hl.addWidget(self.logo)
        hl.addWidget(tw)
        hl.addStretch()

        # Format indicator
        self.formats_label = QLabel("40+ FORMATS")
        self.formats_label.setFont(QFont("Consolas", 7, QFont.Bold))
        self.formats_label.setFixedHeight(26)

        hl.addWidget(self.formats_label)
        hl.addSpacing(10)

        # Theme toggle
        self.theme_btn = QPushButton("☀")
        self.theme_btn.setFont(QFont("Segoe UI Emoji", 15))
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.theme_btn.clicked.connect(self._toggle_theme)

        # Reindex
        self.reindex_btn = QPushButton("⟳  REINDEX")
        self.reindex_btn.setFont(QFont("Consolas", 9, QFont.Bold))
        self.reindex_btn.setFixedHeight(40)
        self.reindex_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.reindex_btn.clicked.connect(self._reindex)

        # Settings button
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFont(QFont("Segoe UI Emoji", 15))
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.settings_btn.clicked.connect(self._open_settings)

        hl.addWidget(self.settings_btn)
        hl.addSpacing(6)
        hl.addWidget(self.theme_btn)
        hl.addSpacing(8)
        hl.addWidget(self.reindex_btn)
        layout.addWidget(self.header)

        # ── Gradient divider ──
        self.divider = QFrame()
        self.divider.setFixedHeight(2)
        layout.addWidget(self.divider)

        # ── Search area ──
        search_area = QWidget()
        sa_layout = QVBoxLayout(search_area)
        sa_layout.setContentsMargins(28, 18, 28, 6)
        sa_layout.setSpacing(6)

        # Neon search bar
        self.search_neon = NeonSearchBar(central)
        self.search_neon.setFixedHeight(64)
        search_inner = QHBoxLayout(self.search_neon)
        search_inner.setContentsMargins(24, 4, 24, 4)
        search_inner.setSpacing(12)

        self.search_prefix = QLabel("›")
        self.search_prefix.setFont(QFont("Consolas", 22, QFont.Bold))
        self.search_prefix.setFixedWidth(20)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("search files, contents, documents...")
        self.search_input.setFont(QFont("Consolas", 14))
        self.search_input.setFrame(False)
        self.search_input.returnPressed.connect(self._do_search)
        self.search_input.focusInEvent = self._on_search_focus_in
        self.search_input.focusOutEvent = self._on_search_focus_out
        self._original_focus_in = QLineEdit.focusInEvent
        self._original_focus_out = QLineEdit.focusOutEvent

        self.shortcut_label = QLabel("ENTER")
        self.shortcut_label.setFont(QFont("Consolas", 7, QFont.Bold))
        self.shortcut_label.setFixedHeight(22)

        search_inner.addWidget(self.search_prefix)
        search_inner.addWidget(self.search_input)
        search_inner.addWidget(self.shortcut_label)

        sa_layout.addWidget(self.search_neon)

        # ── Filter chips ──
        filter_row = QWidget()
        fr_layout = QHBoxLayout(filter_row)
        fr_layout.setContentsMargins(4, 4, 4, 0)
        fr_layout.setSpacing(5)

        self._active_filter = None
        self._filter_buttons = {}

        FILTERS = {
            "ALL":     None,
            "DOCS":    [".pdf", ".docx", ".doc", ".rtf", ".txt", ".md", ".epub", ".rst"],
            "SHEETS":  [".xlsx", ".xls", ".csv"],
            "SLIDES":  [".pptx", ".ppt"],
            "CODE":    [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".java",
                        ".cpp", ".c", ".cs", ".go", ".rs", ".rb", ".php", ".kt"],
            "DATA":    [".json", ".xml", ".yaml", ".yml", ".toml", ".sql", ".ini", ".cfg"],
            "MEDIA":   [".jpg", ".jpeg", ".png", ".gif", ".svg", ".mp4", ".mp3", ".wav"],
            "ARCHIVE": [".zip", ".rar", ".7z", ".tar", ".gz", ".exe", ".msi"],
        }
        self._filter_map = FILTERS

        for label in FILTERS:
            btn = QPushButton(label)
            btn.setFont(QFont("Consolas", 8, QFont.Bold))
            btn.setFixedHeight(26)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setCheckable(True)
            if label == "ALL":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, l=label: self._set_filter(l))
            fr_layout.addWidget(btn)
            self._filter_buttons[label] = btn

        fr_layout.addStretch()

        # Sort buttons
        sep = QLabel("|")
        sep.setFont(QFont("Consolas", 10))
        sep.setFixedWidth(12)
        fr_layout.addWidget(sep)

        self._active_sort = "relevance"
        self._sort_buttons = {}

        SORTS = {
            "▼ REL":   "relevance",
            "▼ NAME":  "name_asc",
            "▼ SIZE":  "size_desc",
            "▼ NEW":   "date_new",
            "▼ OLD":   "date_old",
        }
        self._sort_label_map = SORTS

        for label, key in SORTS.items():
            btn = QPushButton(label)
            btn.setFont(QFont("Consolas", 7, QFont.Bold))
            btn.setFixedHeight(26)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setCheckable(True)
            if key == "relevance":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, k=key: self._set_sort(k))
            fr_layout.addWidget(btn)
            self._sort_buttons[key] = btn

        sa_layout.addWidget(filter_row)

        # Stats row
        stats = QWidget()
        stats_l = QHBoxLayout(stats)
        stats_l.setContentsMargins(6, 0, 6, 0)
        self.result_count_label = QLabel("")
        self.result_count_label.setFont(QFont("Consolas", 9, QFont.Medium))
        self.search_time_label = QLabel("")
        self.search_time_label.setFont(QFont("Consolas", 9))
        stats_l.addWidget(self.result_count_label)
        stats_l.addStretch()
        stats_l.addWidget(self.search_time_label)
        sa_layout.addWidget(stats)

        layout.addWidget(search_area)

        # ── Results list ──
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

        # ── Empty state ──
        self.empty_widget = QWidget()
        el = QVBoxLayout(self.empty_widget)
        el.setAlignment(Qt.AlignCenter)
        el.setSpacing(6)

        self.empty_icon = QLabel("⚡")
        self.empty_icon.setFont(QFont("Segoe UI Emoji", 44))
        self.empty_icon.setAlignment(Qt.AlignCenter)

        self.empty_title = QLabel("READY TO SEARCH")
        self.empty_title.setFont(QFont("Consolas", 18, QFont.Bold))
        self.empty_title.setAlignment(Qt.AlignCenter)

        self.empty_sub = QLabel("// type a query and press ENTER\n// searches file names + document contents")
        self.empty_sub.setFont(QFont("Consolas", 9))
        self.empty_sub.setAlignment(Qt.AlignCenter)

        # Format chips
        chips_row = QWidget()
        cr_layout = QHBoxLayout(chips_row)
        cr_layout.setAlignment(Qt.AlignCenter)
        cr_layout.setSpacing(5)
        self._chips = []
        for fmt in ["PDF", "DOCX", "XLSX", "PPTX", "EPUB", "RTF", "PY", "JS", "SQL", "+30"]:
            chip = QLabel(fmt)
            chip.setFont(QFont("Consolas", 7, QFont.Bold))
            chip.setFixedHeight(24)
            chip.setMinimumWidth(38)
            chip.setAlignment(Qt.AlignCenter)
            cr_layout.addWidget(chip)
            self._chips.append(chip)

        el.addWidget(self.empty_icon)
        el.addSpacing(4)
        el.addWidget(self.empty_title)
        el.addWidget(self.empty_sub)
        el.addSpacing(14)
        el.addWidget(chips_row)
        layout.addWidget(self.empty_widget)

        # ── Status bar ──
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont("Consolas", 8))
        self.status_bar.setFixedHeight(30)
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("// initializing...")
        self.idx_count_label = QLabel("")
        from database import DB_DIR
        self.db_path_label = QLabel(f"IDX: {DB_DIR}")
        self.db_path_label.setFont(QFont("Consolas", 7))
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.db_path_label)
        self.status_bar.addPermanentWidget(self.idx_count_label)

        self.list_view.hide()
        self.empty_widget.show()
        self.search_input.setFocus()

        # Shortcuts — NO Return shortcut (it conflicts with search input)
        QShortcut(QKeySequence("Ctrl+O"), self, self._open_in_folder)
        QShortcut(QKeySequence("Escape"), self, self._clear_search)
        QShortcut(QKeySequence("Ctrl+R"), self, self._reindex)
        QShortcut(QKeySequence("Ctrl+L"), self, self._focus_search)
        QShortcut(QKeySequence("Ctrl+D"), self, self._toggle_theme)

    def _on_search_focus_in(self, event):
        self.search_neon.set_focused(True)
        self._original_focus_in(self.search_input, event)

    def _on_search_focus_out(self, event):
        self.search_neon.set_focused(False)
        self._original_focus_out(self.search_input, event)

    # ─── Theme ────────────────────────────────────────────

    def _apply_theme(self):
        T = self.T
        self._theme_colors = T
        dk = self.is_dark

        bg = T["bg"].name()
        surface = T["surface"].name()
        accent = T["accent"].name()
        accent2 = T["accent2"].name()
        accent3 = T["accent3"].name()
        accent_h = T["accent_hover"].name()
        text = T["text"].name()
        text_sec = T["text_sec"].name()
        text_m = T["text_muted"].name()
        divider = T["divider"].name()
        sb = T["scrollbar"].name()
        sb_h = T["scrollbar_hover"].name()
        s_border = T["search_border"].name()
        badge_p_bg = T["badge_purple_bg"].name()
        badge_p_t = T["badge_purple_text"].name()
        badge_c_bg = T["badge_cyan_bg"].name()
        badge_c_t = T["badge_cyan_text"].name()

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {bg}; }}

            #header {{ background: transparent; }}

            #divider {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.15 {accent}, stop:0.5 {accent2}, stop:0.85 {accent3}, stop:1 transparent);
            }}

            QLineEdit {{
                background: transparent;
                color: {text};
                border: none;
                padding: 8px 0px;
                selection-background-color: {accent};
                selection-color: white;
            }}
            QLineEdit::placeholder {{ color: {text_m}; }}

            #search_neon {{
                background: transparent;
                border: none;
            }}

            QListView {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListView::item {{ border: none; padding: 0px; }}
            QListView::item:selected, QListView::item:hover {{ background: transparent; }}

            QScrollBar:vertical {{
                background: transparent;
                width: 5px;
                margin: 10px 1px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {sb};
                min-height: 40px;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {sb_h};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

            QStatusBar {{
                background-color: {surface};
                color: {text_m};
                border-top: 1px solid {divider};
            }}

            #settings_btn {{
                background: {badge_p_bg};
                border: 1px solid {s_border};
                border-radius: 10px;
            }}
            #settings_btn:hover {{
                border-color: {accent};
            }}

            #theme_btn {{
                background: {badge_p_bg};
                border: 1px solid {s_border};
                border-radius: 10px;
            }}
            #theme_btn:hover {{
                border-color: {accent};
            }}

            #reindex_btn {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent}, stop:1 {accent2});
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 20px;
            }}
            #reindex_btn:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent_h}, stop:1 {accent2});
            }}

            QPushButton[checkable="true"] {{
                background: {badge_p_bg};
                color: {text_m};
                border: 1px solid transparent;
                border-radius: 6px;
                padding: 2px 10px;
                font-family: Consolas;
            }}
            QPushButton[checkable="true"]:checked {{
                background: {accent};
                color: white;
                border-color: {accent};
            }}
            QPushButton[checkable="true"]:hover {{
                border-color: {accent};
                color: {text};
            }}

            #formats_label {{
                color: {accent2};
                background: {badge_c_bg};
                border: 1px solid {badge_c_bg};
                border-radius: 6px;
                padding: 3px 10px;
            }}

            QLabel {{ color: {text}; background: transparent; }}
            #title_label {{ color: {text}; }}
            #subtitle {{ color: {text_m}; }}
            #search_prefix {{ color: {accent}; }}
            #shortcut_label {{
                color: {badge_c_t};
                background: {badge_c_bg};
                border-radius: 4px;
                padding: 2px 8px;
            }}
            #result_count {{ color: {accent}; }}
            #search_time {{ color: {text_m}; }}
            #empty_icon {{ color: {accent}; }}
            #empty_title {{ color: {text}; }}
            #empty_sub {{ color: {text_m}; }}
            #status_label {{ color: {text_m}; }}
            #idx_count {{ color: {text_m}; }}
            #db_path {{ color: {text_m}; padding-right: 12px; }}
        """)

        # Set object names
        for w, n in [
            (self.header, "header"), (self.divider, "divider"),
            (self.settings_btn, "settings_btn"),
            (self.theme_btn, "theme_btn"), (self.reindex_btn, "reindex_btn"),
            (self.title_label, "title_label"), (self.subtitle_label, "subtitle"),
            (self.formats_label, "formats_label"), (self.search_prefix, "search_prefix"),
            (self.search_neon, "search_neon"),
            (self.shortcut_label, "shortcut_label"),
            (self.result_count_label, "result_count"), (self.search_time_label, "search_time"),
            (self.empty_icon, "empty_icon"), (self.empty_title, "empty_title"),
            (self.empty_sub, "empty_sub"), (self.status_label, "status_label"),
            (self.idx_count_label, "idx_count"), (self.db_path_label, "db_path"),
        ]:
            w.setObjectName(n)

        self.theme_btn.setText("☀" if dk else "🌙")

        # Update child widget themes
        self.search_neon.set_theme(T)
        self._bg.set_theme(T)

        # Chip styling
        for i, chip in enumerate(self._chips):
            if i < 3:
                cbg, ct = badge_p_bg, badge_p_t
            elif i < 6:
                cbg, ct = badge_c_bg, badge_c_t
            else:
                cbg, ct = T["badge_green_bg"].name(), T["badge_green_text"].name()
            chip.setStyleSheet(f"background:{cbg}; color:{ct}; border-radius:5px; padding:2px 6px;")

        self.list_view.viewport().update()

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        self.T = THEMES["dark" if self.is_dark else "light"]
        self._theme_colors = self.T
        self._apply_theme()
        self._apply_win_effects()

    def _apply_win_effects(self):
        try:
            hwnd = int(self.winId())
            v = ctypes.c_int(1 if self.is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(v), 4)
            bd = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 38, ctypes.byref(bd), 4)
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_bg'):
            self._bg.setGeometry(0, 0, self.width(), self.height())

    # ─── Search ───────────────────────────────────────────

    def _set_filter(self, label):
        for name, btn in self._filter_buttons.items():
            btn.setChecked(name == label)
        self._active_filter = self._filter_map.get(label)
        if self.search_input.text().strip() or self._active_filter:
            self._do_search()

    def _set_sort(self, key):
        for k, btn in self._sort_buttons.items():
            btn.setChecked(k == key)
        self._active_sort = key
        if self.search_input.text().strip() or self._active_filter:
            self._do_search()

    def _do_search(self):
        q = self.search_input.text().strip()
        if not q and not self._active_filter:
            self._show_empty("⚡", "READY TO SEARCH",
                             "// type a query and press ENTER\n// searches file names + document contents\n// use ext:pdf or filter chips to filter by type")
            return

        t0 = time.perf_counter()
        results = self.db.search(q, limit=200, ext_filter=self._active_filter, sort=self._active_sort)
        ms = (time.perf_counter() - t0) * 1000

        if results:
            self.model.set_results(results)
            self.empty_widget.hide()
            self.list_view.show()
            self.list_view.setCurrentIndex(self.model.index(0))
        else:
            self._show_empty("🔍", "NO RESULTS", "// try a different search term")

        self.result_count_label.setText(f"[{len(results)} results]")
        self.search_time_label.setText(f"⚡ {ms:.1f}ms")

    def _show_empty(self, icon, title, sub):
        self.model.clear()
        self.list_view.hide()
        self.empty_widget.show()
        self.empty_icon.setText(icon)
        self.empty_title.setText(title)
        self.empty_sub.setText(sub)
        self.result_count_label.setText("")
        self.search_time_label.setText("")

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
                self.status_label.setText(f"// not found: {os.path.basename(path)}")
        except Exception as e:
            self.status_label.setText(f"// error: {e}")

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
        self._show_empty("⚡", "READY TO SEARCH",
                         "// type a query and press ENTER\n// searches file names + document contents")

    def _focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    # ─── Indexing ─────────────────────────────────────────

    def _start_indexing(self):
        n = self.db.get_file_count()
        if n > 0:
            self.status_label.setText(f"// ready — {n:,} files indexed")
            self.idx_count_label.setText(f"  [{n:,}]")
            lt = self.db.get_meta("last_index_time")
            if lt:
                try:
                    if (datetime.now() - datetime.fromisoformat(lt)).total_seconds() > 7200:
                        QTimer.singleShot(3000, lambda: self._run_indexer(False))
                except Exception:
                    pass
        else:
            self.status_label.setText("// first indexing starting...")
            QTimer.singleShot(500, lambda: self._run_indexer(True))

    def _run_indexer(self, reindex):
        if self._indexer_thread and self._indexer_thread.isRunning():
            return
        self._indexer_thread = IndexerThread(self.db, reindex)
        self._indexer_thread.progress.connect(self._on_idx_progress)
        self._indexer_thread.status.connect(self._on_idx_status)
        self._indexer_thread.finished_indexing.connect(self._on_idx_done)
        self._indexer_thread.start()

    def _open_settings(self):
        dlg = SettingsDialog(self, self.is_dark)
        if dlg.exec() == QDialog.Accepted:
            new_preset = dlg.get_selected_preset()
            from database import get_preset_name, set_preset_name
            if new_preset != get_preset_name():
                set_preset_name(new_preset)
                self.status_label.setText(f"// preset changed to {new_preset} — reindexing...")
                self._run_indexer(True)

    def _reindex(self):
        if self._indexer_thread and self._indexer_thread.isRunning():
            self._indexer_thread.stop()
            self.status_label.setText("// indexing stopped")
            self.reindex_btn.setText("⟳  REINDEX")
            return
        self.reindex_btn.setText("■  STOP")
        self._run_indexer(True)

    def _on_idx_progress(self, count):
        self.idx_count_label.setText(f"  [{count:,}]")

    def _on_idx_status(self, msg):
        self.status_label.setText(f"// {msg}")
        if "Ready" in msg:
            self.reindex_btn.setText("⟳  REINDEX")

    def _on_idx_done(self):
        self.reindex_btn.setText("⟳  REINDEX")
        self._start_watcher()

    # ─── File Watcher ─────────────────────────────────────

    def _start_watcher(self):
        if self._file_watcher and self._file_watcher.is_running():
            return
        from database import FileWatcher
        self._file_watcher = FileWatcher(
            self.db,
            status_callback=lambda msg: QTimer.singleShot(0, lambda: self.status_label.setText(f"// {msg}"))
        )
        self._file_watcher.start()

    def _stop_watcher(self):
        if self._file_watcher:
            self._file_watcher.stop()

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

    # Set app icon for taskbar
    ico = os.path.join(SCRIPT_DIR, "quickfind.ico")
    if os.path.exists(ico):
        app.setWindowIcon(QIcon(ico))

    window = QuickFindWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
