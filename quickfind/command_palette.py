"""A VS Code-style command palette widget for PySide6."""

from dataclasses import dataclass, field

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

DEFAULT_THEME = {
    "bg": "#1e1e1e",
    "input_bg": "#2d2d2d",
    "input_fg": "#cccccc",
    "input_border": "#3c3c3c",
    "item_bg": "#1e1e1e",
    "item_fg": "#cccccc",
    "item_hover": "#2a2d2e",
    "item_selected": "#094771",
    "shortcut_fg": "#888888",
    "category_fg": "#569cd6",
    "border": "#454545",
    "overlay": "rgba(0, 0, 0, 150)",
}


@dataclass
class Command:
    """Represents a command in the palette."""

    name: str
    description: str = ""
    shortcut: str = ""
    callback: callable = field(default=None, repr=False)
    category: str = ""


def _fuzzy_match(query: str, text: str) -> bool:
    """Check if all characters of query appear in text in order (case-insensitive)."""
    query = query.lower()
    text = text.lower()
    qi = 0
    for ch in text:
        if qi < len(query) and ch == query[qi]:
            qi += 1
    return qi == len(query)


class CommandPalette(QDialog):
    """A VS Code-style command palette dialog."""

    def __init__(self, parent: QWidget | None, commands: list[Command],
                 theme: dict | None = None) -> None:
        super().__init__(parent)
        self._commands = commands
        self._theme = {**DEFAULT_THEME, **(theme or {})}
        self._filtered: list[Command] = list(commands)

        self._setup_window()
        self._setup_ui()
        self._apply_styles()
        self._populate_list()

    def _setup_window(self) -> None:
        """Configure dialog window properties."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
            | Qt.WindowType.Popup
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(500)
        self.setMinimumHeight(100)
        self.setMaximumHeight(400)

        # Center on parent or screen
        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - 500) // 2
            y = parent_geo.y() + parent_geo.height() // 5
            self.move(x, y)

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container widget for rounded corners
        self._container = QWidget(self)
        self._container.setObjectName("palette_container")
        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(1, 1, 1, 1)
        container_layout.setSpacing(0)

        # Search input
        self._input = QLineEdit(self._container)
        self._input.setPlaceholderText("Type a command...")
        self._input.setObjectName("palette_input")
        self._input.textChanged.connect(self._on_filter)
        container_layout.addWidget(self._input)

        # Command list
        self._list = QListWidget(self._container)
        self._list.setObjectName("palette_list")
        self._list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._list.itemActivated.connect(self._on_activate)
        container_layout.addWidget(self._list)

        layout.addWidget(self._container)
        self._input.setFocus()

    def _apply_styles(self) -> None:
        """Apply dark theme styles."""
        t = self._theme
        self._container.setStyleSheet(f"""
            QWidget#palette_container {{
                background-color: {t['bg']};
                border: 1px solid {t['border']};
                border-radius: 8px;
            }}
        """)
        self._input.setStyleSheet(f"""
            QLineEdit#palette_input {{
                background-color: {t['input_bg']};
                color: {t['input_fg']};
                border: 1px solid {t['input_border']};
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                margin: 8px 8px 4px 8px;
            }}
        """)
        self._list.setStyleSheet(f"""
            QListWidget#palette_list {{
                background-color: {t['item_bg']};
                border: none;
                outline: none;
                padding: 4px;
            }}
            QListWidget#palette_list::item {{
                background-color: {t['item_bg']};
                color: {t['item_fg']};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QListWidget#palette_list::item:hover {{
                background-color: {t['item_hover']};
            }}
            QListWidget#palette_list::item:selected {{
                background-color: {t['item_selected']};
            }}
        """)

    def _create_item_widget(self, cmd: Command) -> QWidget:
        """Create a widget for a command list item."""
        t = self._theme
        widget = QWidget()
        h_layout = QHBoxLayout(widget)
        h_layout.setContentsMargins(4, 2, 4, 2)

        # Category + name
        left = QLabel()
        if cmd.category:
            left.setText(
                f'<span style="color:{t["category_fg"]}">{cmd.category}: </span>'
                f'<span style="color:{t["item_fg"]}">{cmd.name}</span>'
            )
        else:
            left.setText(f'<span style="color:{t["item_fg"]}">{cmd.name}</span>')
        left.setFont(QFont("Segoe UI", 10))
        h_layout.addWidget(left)

        h_layout.addStretch()

        # Shortcut
        if cmd.shortcut:
            shortcut_label = QLabel(cmd.shortcut)
            shortcut_label.setStyleSheet(
                f"color: {t['shortcut_fg']}; font-size: 11px;"
            )
            shortcut_label.setFont(QFont("Consolas", 9))
            h_layout.addWidget(shortcut_label)

        return widget

    def _populate_list(self) -> None:
        """Fill the list widget with filtered commands."""
        self._list.clear()
        for cmd in self._filtered:
            item = QListWidgetItem(self._list)
            widget = self._create_item_widget(cmd)
            item.setSizeHint(widget.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, widget)
            item.setData(Qt.ItemDataRole.UserRole, cmd)

        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _on_filter(self, text: str) -> None:
        """Filter commands based on fuzzy matching."""
        query = text.strip()
        if not query:
            self._filtered = list(self._commands)
        else:
            self._filtered = [
                cmd for cmd in self._commands if _fuzzy_match(query, cmd.name)
            ]
        self._populate_list()

    def _on_activate(self, item: QListWidgetItem) -> None:
        """Execute the selected command."""
        cmd = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
        if cmd and cmd.callback:
            try:
                cmd.callback()
            except Exception:
                pass

    def keyPressEvent(self, event) -> None:
        """Handle keyboard navigation."""
        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.reject()
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            current = self._list.currentItem()
            if current:
                self._on_activate(current)
        elif key == Qt.Key.Key_Down:
            row = self._list.currentRow()
            if row < self._list.count() - 1:
                self._list.setCurrentRow(row + 1)
        elif key == Qt.Key.Key_Up:
            row = self._list.currentRow()
            if row > 0:
                self._list.setCurrentRow(row - 1)
        else:
            super().keyPressEvent(event)
