"""
QuickFind — Ultra-Fast Desktop File Search
PySide6 · Material Design 3 · FTS5 · 3-Phase Indexing
25 Features: Tabs, Drag&Drop, Regex, Bookmarks, Command Palette, Global Hotkey, etc.
"""

import sys, os, subprocess, time, ctypes, json, re, shutil
from datetime import datetime
from functools import partial

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("dgknk.QuickFind.1")
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QListView, QPushButton, QStatusBar,
    QStyledItemDelegate, QStyle, QFrame,
    QDialog, QRadioButton, QButtonGroup, QMessageBox,
    QProgressBar, QSlider, QScrollArea, QStackedWidget,
    QSizePolicy, QComboBox, QCheckBox, QTabWidget,
    QMenu, QFileDialog, QTextEdit, QSystemTrayIcon
)
from PySide6.QtCore import (
    Qt, QSize, QRect, QThread, Signal, QModelIndex, QObject,
    QAbstractListModel, QTimer, QRectF, QPointF, QMimeData, QUrl,
    QSortFilterProxyModel
)
from PySide6.QtGui import (
    QColor, QPainter, QFont, QFontMetrics, QPen, QBrush,
    QIcon, QPainterPath, QPixmap, QCursor,
    QShortcut, QKeySequence, QAction
)

import sys as _sys
if getattr(_sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(_sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, SCRIPT_DIR)

FONT = "Segoe UI"
FONT_MONO = "Consolas"

THEMES = {
    "light": {
        "bg": "#fcf8f9", "surface": "#fcf8f9", "sc": "#f0edef", "scl": "#f6f3f4",
        "sch": "#eae7ea", "white": "#ffffff", "primary": "#0054d6", "pc": "#dae1ff",
        "opc": "#0049bb", "on_primary": "#ffffff", "secondary": "#5f5f5f", "sec_c": "#e4e2e6",
        "on_s": "#323235", "on_sv": "#5f5f61", "outline": "#7b7a7d", "ov": "#b3b1b4",
        "divider": "#e4e2e5", "error": "#9f403d", "sb": "#b3b1b4", "sb_h": "#7b7a7d",
        "card_hover": "#f6f3f4", "card_sel": "#dae1ff",
    },
    "dark": {
        "bg": "#111318", "surface": "#111318", "sc": "#1d1f25", "scl": "#191b21",
        "sch": "#272a30", "white": "#2a2d33", "primary": "#a8c8ff", "pc": "#003068",
        "opc": "#d6e3ff", "on_primary": "#002552", "secondary": "#c6c6ca", "sec_c": "#444548",
        "on_s": "#e3e2e6", "on_sv": "#c4c6cf", "outline": "#8e9099", "ov": "#44464f",
        "divider": "#44464f", "error": "#ffb4ab", "sb": "#44464f", "sb_h": "#8e9099",
        "card_hover": "#272a30", "card_sel": "#003068",
    },
    "turquoise": {
        "bg": "#f0fafa", "surface": "#f0fafa", "sc": "#e0f0f0", "scl": "#e8f5f5",
        "sch": "#d4ebeb", "white": "#ffffff", "primary": "#00897b", "pc": "#b2dfdb",
        "opc": "#00695c", "on_primary": "#ffffff", "secondary": "#5f6368", "sec_c": "#e0e0e0",
        "on_s": "#263238", "on_sv": "#546e7a", "outline": "#78909c", "ov": "#b0bec5",
        "divider": "#cfd8dc", "error": "#c62828", "sb": "#b0bec5", "sb_h": "#78909c",
        "card_hover": "#e0f2f1", "card_sel": "#b2dfdb",
    },
    "purple": {
        "bg": "#faf5ff", "surface": "#faf5ff", "sc": "#f3e5f5", "scl": "#f5eef8",
        "sch": "#e8d5f0", "white": "#ffffff", "primary": "#7b1fa2", "pc": "#e1bee7",
        "opc": "#6a1b9a", "on_primary": "#ffffff", "secondary": "#5f6368", "sec_c": "#e0e0e0",
        "on_s": "#311b40", "on_sv": "#6d5080", "outline": "#9575cd", "ov": "#ce93d8",
        "divider": "#e1bee7", "error": "#c62828", "sb": "#ce93d8", "sb_h": "#9575cd",
        "card_hover": "#f3e5f5", "card_sel": "#e1bee7",
    },
}

def _darken(hex_color, amount=30):
    c = hex_color.lstrip('#')
    r, g, b = int(c[:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return f"#{max(0,r-amount):02x}{max(0,g-amount):02x}{max(0,b-amount):02x}"

EXT_ICONS = {
    ".pdf": "PDF", ".docx": "DOC", ".doc": "DOC", ".rtf": "RTF", ".txt": "TXT", ".md": "MD",
    ".epub": "EPB", ".xlsx": "XLS", ".xls": "XLS", ".csv": "CSV", ".pptx": "PPT", ".ppt": "PPT",
    ".py": "PY", ".js": "JS", ".ts": "TS", ".html": "HTM", ".css": "CSS",
    ".java": "JAV", ".cpp": "C++", ".c": "C", ".cs": "C#", ".go": "GO", ".rs": "RS",
    ".json": "JSN", ".xml": "XML", ".jpg": "JPG", ".jpeg": "JPG", ".png": "PNG", ".gif": "GIF",
    ".svg": "SVG", ".mp4": "MP4", ".mp3": "MP3", ".zip": "ZIP", ".rar": "RAR",
    ".exe": "EXE", ".sql": "SQL",
}

EXT_COLORS = {
    ".pdf": "#E53935", ".docx": "#1565C0", ".doc": "#1565C0", ".rtf": "#5C6BC0",
    ".txt": "#607D8B", ".md": "#455A64", ".epub": "#6D4C41",
    ".xlsx": "#2E7D32", ".xls": "#2E7D32", ".csv": "#43A047", ".pptx": "#D84315", ".ppt": "#D84315",
    ".py": "#FFB300", ".js": "#F9A825", ".ts": "#0277BD", ".html": "#E65100", ".css": "#7B1FA2",
    ".java": "#D32F2F", ".cpp": "#1565C0", ".c": "#0D47A1", ".cs": "#4A148C",
    ".go": "#00ACC1", ".rs": "#BF360C", ".json": "#546E7A", ".xml": "#EF6C00",
    ".jpg": "#AD1457", ".jpeg": "#AD1457", ".png": "#6A1B9A", ".gif": "#00695C", ".svg": "#E65100",
    ".mp4": "#C62828", ".mp3": "#6A1B9A", ".zip": "#4E342E", ".rar": "#4E342E",
    ".exe": "#37474F", ".sql": "#0277BD",
}

TYPE_NAMES = {
    ".pdf": "PDF Document", ".docx": "Word Document", ".xlsx": "Excel Spreadsheet",
    ".pptx": "PowerPoint", ".txt": "Plain Text", ".md": "Markdown", ".csv": "CSV Data",
    ".py": "Python Script", ".js": "JavaScript", ".ts": "TypeScript",
    ".html": "HTML Document", ".css": "Stylesheet", ".json": "JSON Data",
    ".jpg": "JPEG Image", ".png": "PNG Image", ".svg": "SVG Vector",
    ".mp4": "MP4 Video", ".mp3": "MP3 Audio", ".zip": "ZIP Archive",
    ".exe": "Executable", ".rtf": "Rich Text", ".epub": "E-Book",
}

_LANG = {}
TRANSLATIONS = {
    "English": {
        "search": "Search", "index_status": "Index Status", "settings": "Settings",
        "duplicates": "Duplicates", "disk_usage": "Disk Usage", "statistics": "Statistics",
        "desktop_search": "Desktop Search",
        "search_placeholder": "Search files... (regex: size:>10MB modified:today ext:pdf hash: supported)",
        "all": "All", "documents": "Documents", "images": "Images", "code": "Code",
        "archives": "Archives", "pdfs": "PDFs",
        "relevance": "Relevance", "name": "Name", "size": "Size", "newest": "Newest",
        "ready_to_search": "Ready to Search",
        "type_query": "Type to search \u2014 results appear as you type",
        "no_results": "No Results", "try_different": "Try different terms or operators",
        "results": "results", "select_file": "Select a file",
        "no_preview": "No preview for",
        "open_file": "Open File", "show_folder": "Show in Folder", "copy_path": "Copy Path",
        "index_title": "Index Status", "index_desc": "Monitor your search database and manage indexing.",
        "rebuild_index": "Rebuild Index", "current_progress": "Current Progress",
        "db_stats": "Database Stats", "db_size": "Database Size",
        "last_indexed": "Last Indexed", "search_latency": "Search Latency",
        "content_depth": "Content Indexing Depth", "save_reindex": "Save & Reindex",
        "file_type_support": "File Type Support",
        "settings_title": "Settings", "settings_desc": "Customize QuickFind appearance and behavior.",
        "appearance": "APPEARANCE", "theme": "Theme", "font_size": "Font Size",
        "search_behavior": "SEARCH BEHAVIOR", "max_results": "Max Results",
        "open_single_click": "Open file on single click", "indexing": "INDEXING",
        "auto_reindex": "Auto-reindex when files change",
        "index_hidden": "Index hidden files", "language": "LANGUAGE", "lang_label": "Language",
        "save_settings": "Save Settings", "initializing": "Initializing...",
        "ready": "Ready", "files_indexed": "files indexed",
        "first_indexing": "First indexing starting...",
        "indexing_status": "Indexing...", "indexing_stopped": "Indexing stopped",
        "phase1": "Phase 1: Scanning metadata", "phase2": "Phase 2: Indexing content",
        "phase3": "Phase 3: Computing hashes",
        "find_duplicates": "Find Duplicates", "min_file_size": "Min file size",
        "favorites": "Favorites", "recent_files": "Recent Files",
        "pin": "Pin to Top", "bookmark": "Bookmark",
        "search_history": "Search History", "clear_history": "Clear History",
        "new_tab": "New Tab", "find_similar": "Find Similar",
        "files": "FILES", "speed": "SPEED", "duration": "DURATION",
    },
    "Turkish": {
        "search": "Ara", "index_status": "Dizin Durumu", "settings": "Ayarlar",
        "duplicates": "Kopyalar", "disk_usage": "Disk Kullanimi", "statistics": "Istatistikler",
        "desktop_search": "Masaustu Arama",
        "search_placeholder": "Dosya ara... (regex: size:>10MB modified:today ext:pdf hash: desteklenir)",
        "all": "Tumu", "documents": "Belgeler", "images": "Gorseller", "code": "Kod",
        "archives": "Arsivler", "pdfs": "PDF'ler",
        "relevance": "Ilgi", "name": "Ad", "size": "Boyut", "newest": "En Yeni",
        "ready_to_search": "Aramaya Hazir",
        "type_query": "Yazmaya baslayin \u2014 sonuclar aninda gorunur",
        "no_results": "Sonuc Yok", "try_different": "Farkli terimler deneyin",
        "results": "sonuc", "select_file": "Dosya secin",
        "no_preview": "On izleme yok:",
        "open_file": "Dosyayi Ac", "show_folder": "Klasorde Goster", "copy_path": "Yolu Kopyala",
        "index_title": "Dizin Durumu", "index_desc": "Arama veritabaninizi yonetin.",
        "rebuild_index": "Yeniden Dizinle", "current_progress": "Mevcut Ilerleme",
        "db_stats": "Veritabani Istatistikleri", "db_size": "Veritabani Boyutu",
        "last_indexed": "Son Dizinleme", "search_latency": "Arama Gecikmesi",
        "content_depth": "Icerik Derinligi", "save_reindex": "Kaydet ve Yeniden Dizinle",
        "file_type_support": "Dosya Turu Destegi",
        "settings_title": "Ayarlar", "settings_desc": "QuickFind gorunumunu ozellestirin.",
        "appearance": "GORUNUM", "theme": "Tema", "font_size": "Yazi Boyutu",
        "search_behavior": "ARAMA DAVRANISI", "max_results": "Maks Sonuc",
        "open_single_click": "Tek tikla dosya ac", "indexing": "DIZINLEME",
        "auto_reindex": "Dosya degistiginde otomatik dizinle",
        "index_hidden": "Gizli dosyalari dizinle", "language": "DIL", "lang_label": "Dil",
        "save_settings": "Ayarlari Kaydet", "initializing": "Baslatiliyor...",
        "ready": "Hazir", "files_indexed": "dosya dizinlendi",
        "first_indexing": "Ilk dizinleme basliyor...",
        "indexing_status": "Dizinleniyor...", "indexing_stopped": "Dizinleme durduruldu",
        "phase1": "Faz 1: Metadata taraniyor", "phase2": "Faz 2: Icerik dizinleniyor",
        "phase3": "Faz 3: Hash hesaplaniyor",
        "find_duplicates": "Kopya Bul", "min_file_size": "Min dosya boyutu",
        "favorites": "Favoriler", "recent_files": "Son Dosyalar",
        "pin": "Uste Sabitle", "bookmark": "Favori",
        "search_history": "Arama Gecmisi", "clear_history": "Gecmisi Temizle",
        "new_tab": "Yeni Sekme", "find_similar": "Benzerlerini Bul",
        "files": "DOSYA", "speed": "HIZ", "duration": "SURE",
    },
    "German": {
        "search": "Suche", "index_status": "Indexstatus", "settings": "Einstellungen",
        "duplicates": "Duplikate", "disk_usage": "Speichernutzung", "statistics": "Statistiken",
        "desktop_search": "Desktop-Suche",
        "search_placeholder": "Dateien suchen... (regex: size:>10MB modified:today ext:pdf hash: unterstuetzt)",
        "all": "Alle", "documents": "Dokumente", "images": "Bilder", "code": "Code",
        "archives": "Archive", "pdfs": "PDFs",
        "relevance": "Relevanz", "name": "Name", "size": "Groesse", "newest": "Neueste",
        "ready_to_search": "Bereit zur Suche", "type_query": "Tippen Sie zum Suchen",
        "no_results": "Keine Ergebnisse", "try_different": "Versuchen Sie andere Begriffe",
        "results": "Ergebnisse", "select_file": "Datei auswaehlen",
        "no_preview": "Keine Vorschau fuer",
        "open_file": "Datei oeffnen", "show_folder": "Im Ordner anzeigen", "copy_path": "Pfad kopieren",
        "index_title": "Indexstatus", "index_desc": "Suchdatenbank ueberwachen und Indizierung verwalten.",
        "rebuild_index": "Index neu erstellen", "current_progress": "Aktueller Fortschritt",
        "db_stats": "Datenbankstatistiken", "db_size": "Datenbankgroesse",
        "last_indexed": "Zuletzt indiziert", "search_latency": "Suchlatenz",
        "content_depth": "Inhaltsindizierungstiefe", "save_reindex": "Speichern & Neu indizieren",
        "file_type_support": "Dateityp-Unterstuetzung",
        "settings_title": "Einstellungen", "settings_desc": "QuickFind anpassen.",
        "appearance": "ERSCHEINUNGSBILD", "theme": "Design", "font_size": "Schriftgroesse",
        "search_behavior": "SUCHVERHALTEN", "max_results": "Max. Ergebnisse",
        "open_single_click": "Datei mit Einzelklick oeffnen", "indexing": "INDIZIERUNG",
        "auto_reindex": "Bei Dateimaenderungen automatisch neu indizieren",
        "index_hidden": "Versteckte Dateien indizieren", "language": "SPRACHE", "lang_label": "Sprache",
        "save_settings": "Einstellungen speichern", "initializing": "Initialisierung...",
        "ready": "Bereit", "files_indexed": "Dateien indiziert",
        "first_indexing": "Erste Indizierung startet...",
        "indexing_status": "Indizierung...", "indexing_stopped": "Indizierung gestoppt",
        "phase1": "Phase 1: Metadaten scannen", "phase2": "Phase 2: Inhalte indizieren",
        "phase3": "Phase 3: Hashes berechnen",
        "find_duplicates": "Duplikate finden", "min_file_size": "Min. Dateigroesse",
        "favorites": "Favoriten", "recent_files": "Zuletzt verwendet",
        "pin": "Oben anheften", "bookmark": "Lesezeichen",
        "search_history": "Suchverlauf", "clear_history": "Verlauf loeschen",
        "new_tab": "Neuer Tab", "find_similar": "Aehnliche finden",
        "files": "DATEIEN", "speed": "GESCHW.", "duration": "DAUER",
    },
    "French": {
        "search": "Recherche", "index_status": "Etat de l'index", "settings": "Parametres",
        "duplicates": "Doublons", "disk_usage": "Utilisation disque", "statistics": "Statistiques",
        "desktop_search": "Recherche Bureau",
        "search_placeholder": "Rechercher des fichiers... (regex: size:>10MB modified:today ext:pdf hash: pris en charge)",
        "all": "Tout", "documents": "Documents", "images": "Images", "code": "Code",
        "archives": "Archives", "pdfs": "PDFs",
        "relevance": "Pertinence", "name": "Nom", "size": "Taille", "newest": "Recent",
        "ready_to_search": "Pret a chercher", "type_query": "Tapez pour chercher",
        "no_results": "Aucun resultat", "try_different": "Essayez d'autres termes",
        "results": "resultats", "select_file": "Selectionner un fichier",
        "no_preview": "Pas d'apercu pour",
        "open_file": "Ouvrir", "show_folder": "Afficher dans le dossier", "copy_path": "Copier le chemin",
        "index_title": "Etat de l'index", "index_desc": "Surveillez votre base de recherche.",
        "rebuild_index": "Reconstruire l'index", "current_progress": "Progres actuel",
        "db_stats": "Stats de la base", "db_size": "Taille de la base",
        "last_indexed": "Derniere indexation", "search_latency": "Latence de recherche",
        "content_depth": "Profondeur d'indexation", "save_reindex": "Enregistrer et Reindexer",
        "file_type_support": "Types de fichiers",
        "settings_title": "Parametres", "settings_desc": "Personnaliser QuickFind.",
        "appearance": "APPARENCE", "theme": "Theme", "font_size": "Taille de police",
        "search_behavior": "COMPORTEMENT DE RECHERCHE", "max_results": "Max resultats",
        "open_single_click": "Ouvrir en un clic", "indexing": "INDEXATION",
        "auto_reindex": "Reindexer automatiquement lors de modifications",
        "index_hidden": "Indexer les fichiers caches", "language": "LANGUE", "lang_label": "Langue",
        "save_settings": "Enregistrer", "initializing": "Initialisation...",
        "ready": "Pret", "files_indexed": "fichiers indexes",
        "first_indexing": "Premiere indexation...",
        "indexing_status": "Indexation...", "indexing_stopped": "Indexation arretee",
        "phase1": "Phase 1: Scan des metadonnees", "phase2": "Phase 2: Indexation du contenu",
        "phase3": "Phase 3: Calcul des hashes",
        "find_duplicates": "Trouver les doublons", "min_file_size": "Taille min",
        "favorites": "Favoris", "recent_files": "Fichiers recents",
        "pin": "Epingler", "bookmark": "Favori",
        "search_history": "Historique", "clear_history": "Effacer l'historique",
        "new_tab": "Nouvel onglet", "find_similar": "Trouver similaires",
        "files": "FICHIERS", "speed": "VITESSE", "duration": "DUREE",
    },
    "Spanish": {
        "search": "Buscar", "index_status": "Estado del indice", "settings": "Ajustes",
        "duplicates": "Duplicados", "disk_usage": "Uso de disco", "statistics": "Estadisticas",
        "desktop_search": "Busqueda de escritorio",
        "search_placeholder": "Buscar archivos... (regex: size:>10MB modified:today ext:pdf hash: soportado)",
        "all": "Todo", "documents": "Documentos", "images": "Imagenes", "code": "Codigo",
        "archives": "Archivos", "pdfs": "PDFs",
        "relevance": "Relevancia", "name": "Nombre", "size": "Tamano", "newest": "Reciente",
        "ready_to_search": "Listo para buscar", "type_query": "Escriba para buscar",
        "no_results": "Sin resultados", "try_different": "Pruebe otros terminos",
        "results": "resultados", "select_file": "Seleccionar archivo",
        "no_preview": "Sin vista previa para",
        "open_file": "Abrir", "show_folder": "Mostrar en carpeta", "copy_path": "Copiar ruta",
        "index_title": "Estado del indice", "index_desc": "Administre su base de busqueda.",
        "rebuild_index": "Reconstruir indice", "current_progress": "Progreso actual",
        "db_stats": "Stats de base de datos", "db_size": "Tamano de base",
        "last_indexed": "Ultima indexacion", "search_latency": "Latencia",
        "content_depth": "Profundidad de indexacion", "save_reindex": "Guardar y Reindexar",
        "settings_title": "Ajustes", "settings_desc": "Personalizar QuickFind.",
        "appearance": "APARIENCIA", "theme": "Tema", "font_size": "Tamano de fuente",
        "search_behavior": "COMPORTAMIENTO", "max_results": "Max resultados",
        "save_settings": "Guardar", "initializing": "Inicializando...",
        "ready": "Listo", "files_indexed": "archivos indexados",
        "phase1": "Fase 1: Escaneando metadatos", "phase2": "Fase 2: Indexando contenido",
        "phase3": "Fase 3: Calculando hashes",
        "find_duplicates": "Buscar duplicados", "files": "ARCHIVOS", "speed": "VELOC.", "duration": "DURACION",
    },
    "Portuguese": {
        "search": "Pesquisar", "index_status": "Estado do indice", "settings": "Configuracoes",
        "duplicates": "Duplicados", "disk_usage": "Uso de disco", "statistics": "Estatisticas",
        "desktop_search": "Pesquisa Desktop",
        "search_placeholder": "Pesquisar arquivos... (regex: size:>10MB modified:today ext:pdf hash: suportado)",
        "all": "Tudo", "documents": "Documentos", "images": "Imagens", "code": "Codigo",
        "ready_to_search": "Pronto para pesquisar", "type_query": "Digite para pesquisar",
        "no_results": "Sem resultados", "results": "resultados",
        "open_file": "Abrir", "show_folder": "Mostrar na pasta", "copy_path": "Copiar caminho",
        "settings_title": "Configuracoes", "save_settings": "Salvar",
        "ready": "Pronto", "files_indexed": "arquivos indexados",
        "find_duplicates": "Buscar duplicados", "files": "ARQUIVOS",
    },
    "Italian": {
        "search": "Cerca", "index_status": "Stato indice", "settings": "Impostazioni",
        "duplicates": "Duplicati", "disk_usage": "Uso disco", "statistics": "Statistiche",
        "desktop_search": "Ricerca Desktop",
        "search_placeholder": "Cerca file... (regex: size:>10MB modified:today ext:pdf hash: supportato)",
        "all": "Tutto", "documents": "Documenti", "images": "Immagini", "code": "Codice",
        "ready_to_search": "Pronto per cercare", "type_query": "Digita per cercare",
        "no_results": "Nessun risultato", "results": "risultati",
        "open_file": "Apri", "show_folder": "Mostra nella cartella", "copy_path": "Copia percorso",
        "settings_title": "Impostazioni", "save_settings": "Salva",
        "ready": "Pronto", "files_indexed": "file indicizzati",
        "find_duplicates": "Trova duplicati", "files": "FILE",
    },
    "Japanese": {
        "search": "\u691C\u7D22", "index_status": "\u30A4\u30F3\u30C7\u30C3\u30AF\u30B9\u72B6\u614B", "settings": "\u8A2D\u5B9A",
        "duplicates": "\u91CD\u8907", "disk_usage": "\u30C7\u30A3\u30B9\u30AF\u4F7F\u7528\u91CF", "statistics": "\u7D71\u8A08",
        "desktop_search": "\u30C7\u30B9\u30AF\u30C8\u30C3\u30D7\u691C\u7D22",
        "all": "\u3059\u3079\u3066", "documents": "\u30C9\u30AD\u30E5\u30E1\u30F3\u30C8", "images": "\u753B\u50CF", "code": "\u30B3\u30FC\u30C9",
        "ready_to_search": "\u691C\u7D22\u6E96\u5099\u5B8C\u4E86", "no_results": "\u7D50\u679C\u306A\u3057", "results": "\u4EF6",
        "open_file": "\u958B\u304F", "show_folder": "\u30D5\u30A9\u30EB\u30C0\u3067\u8868\u793A", "copy_path": "\u30D1\u30B9\u3092\u30B3\u30D4\u30FC",
        "settings_title": "\u8A2D\u5B9A", "save_settings": "\u4FDD\u5B58",
        "ready": "\u6E96\u5099\u5B8C\u4E86", "files_indexed": "\u30D5\u30A1\u30A4\u30EB\u30A4\u30F3\u30C7\u30C3\u30AF\u30B9\u6E08\u307F",
        "find_duplicates": "\u91CD\u8907\u3092\u691C\u7D22", "files": "\u30D5\u30A1\u30A4\u30EB",
    },
    "Chinese": {
        "search": "\u641C\u7D22", "index_status": "\u7D22\u5F15\u72B6\u6001", "settings": "\u8BBE\u7F6E",
        "duplicates": "\u91CD\u590D", "disk_usage": "\u78C1\u76D8\u4F7F\u7528", "statistics": "\u7EDF\u8BA1",
        "desktop_search": "\u684C\u9762\u641C\u7D22",
        "all": "\u5168\u90E8", "documents": "\u6587\u6863", "images": "\u56FE\u7247", "code": "\u4EE3\u7801",
        "ready_to_search": "\u51C6\u5907\u641C\u7D22", "no_results": "\u65E0\u7ED3\u679C", "results": "\u4E2A\u7ED3\u679C",
        "open_file": "\u6253\u5F00", "show_folder": "\u5728\u6587\u4EF6\u5939\u4E2D\u663E\u793A", "copy_path": "\u590D\u5236\u8DEF\u5F84",
        "settings_title": "\u8BBE\u7F6E", "save_settings": "\u4FDD\u5B58",
        "ready": "\u5C31\u7EEA", "files_indexed": "\u6587\u4EF6\u5DF2\u7D22\u5F15",
        "find_duplicates": "\u67E5\u627E\u91CD\u590D", "files": "\u6587\u4EF6",
    },
    "Korean": {
        "search": "\uAC80\uC0C9", "index_status": "\uC778\uB371\uC2A4 \uC0C1\uD0DC", "settings": "\uC124\uC815",
        "duplicates": "\uC911\uBCF5", "disk_usage": "\uB514\uC2A4\uD06C \uC0AC\uC6A9\uB7C9", "statistics": "\uD1B5\uACC4",
        "desktop_search": "\uB370\uC2A4\uD06C\uD1B1 \uAC80\uC0C9",
        "all": "\uC804\uCCB4", "documents": "\uBB38\uC11C", "images": "\uC774\uBBF8\uC9C0", "code": "\uCF54\uB4DC",
        "ready_to_search": "\uAC80\uC0C9 \uC900\uBE44", "no_results": "\uACB0\uACFC \uC5C6\uC74C", "results": "\uAC74",
        "open_file": "\uC5F4\uAE30", "show_folder": "\uD3F4\uB354\uC5D0\uC11C \uBCF4\uAE30", "copy_path": "\uACBD\uB85C \uBCF5\uC0AC",
        "settings_title": "\uC124\uC815", "save_settings": "\uC800\uC7A5",
        "ready": "\uC900\uBE44", "files_indexed": "\uD30C\uC77C \uC778\uB371\uC2A4\uB428",
        "find_duplicates": "\uC911\uBCF5 \uCC3E\uAE30", "files": "\uD30C\uC77C",
    },
    "Russian": {
        "search": "\u041F\u043E\u0438\u0441\u043A", "index_status": "\u0421\u043E\u0441\u0442\u043E\u044F\u043D\u0438\u0435 \u0438\u043D\u0434\u0435\u043A\u0441\u0430", "settings": "\u041D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438",
        "duplicates": "\u0414\u0443\u0431\u043B\u0438\u043A\u0430\u0442\u044B", "disk_usage": "\u0418\u0441\u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u043D\u0438\u0435 \u0434\u0438\u0441\u043A\u0430", "statistics": "\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043A\u0430",
        "desktop_search": "\u041F\u043E\u0438\u0441\u043A \u043D\u0430 \u0440\u0430\u0431\u043E\u0447\u0435\u043C \u0441\u0442\u043E\u043B\u0435",
        "all": "\u0412\u0441\u0435", "documents": "\u0414\u043E\u043A\u0443\u043C\u0435\u043D\u0442\u044B", "images": "\u0418\u0437\u043E\u0431\u0440\u0430\u0436\u0435\u043D\u0438\u044F", "code": "\u041A\u043E\u0434",
        "ready_to_search": "\u0413\u043E\u0442\u043E\u0432 \u043A \u043F\u043E\u0438\u0441\u043A\u0443", "no_results": "\u041D\u0435\u0442 \u0440\u0435\u0437\u0443\u043B\u044C\u0442\u0430\u0442\u043E\u0432", "results": "\u0440\u0435\u0437\u0443\u043B\u044C\u0442\u0430\u0442\u043E\u0432",
        "open_file": "\u041E\u0442\u043A\u0440\u044B\u0442\u044C", "show_folder": "\u041F\u043E\u043A\u0430\u0437\u0430\u0442\u044C \u0432 \u043F\u0430\u043F\u043A\u0435", "copy_path": "\u041A\u043E\u043F\u0438\u0440\u043E\u0432\u0430\u0442\u044C \u043F\u0443\u0442\u044C",
        "settings_title": "\u041D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438", "save_settings": "\u0421\u043E\u0445\u0440\u0430\u043D\u0438\u0442\u044C",
        "ready": "\u0413\u043E\u0442\u043E\u0432", "files_indexed": "\u0444\u0430\u0439\u043B\u043E\u0432 \u043F\u0440\u043E\u0438\u043D\u0434\u0435\u043A\u0441\u0438\u0440\u043E\u0432\u0430\u043D\u043E",
        "find_duplicates": "\u041D\u0430\u0439\u0442\u0438 \u0434\u0443\u0431\u043B\u0438\u043A\u0430\u0442\u044B", "files": "\u0424\u0410\u0419\u041B\u042B",
    },
    "Arabic": {
        "search": "\u0628\u062D\u062B", "index_status": "\u062D\u0627\u0644\u0629 \u0627\u0644\u0641\u0647\u0631\u0633", "settings": "\u0627\u0644\u0625\u0639\u062F\u0627\u062F\u0627\u062A",
        "duplicates": "\u0645\u0643\u0631\u0631\u0627\u062A", "disk_usage": "\u0627\u0633\u062A\u062E\u062F\u0627\u0645 \u0627\u0644\u0642\u0631\u0635", "statistics": "\u0625\u062D\u0635\u0627\u0626\u064A\u0627\u062A",
        "desktop_search": "\u0628\u062D\u062B \u0633\u0637\u062D \u0627\u0644\u0645\u0643\u062A\u0628",
        "all": "\u0627\u0644\u0643\u0644", "documents": "\u0645\u0633\u062A\u0646\u062F\u0627\u062A", "images": "\u0635\u0648\u0631", "code": "\u0643\u0648\u062F",
        "ready_to_search": "\u062C\u0627\u0647\u0632 \u0644\u0644\u0628\u062D\u062B", "no_results": "\u0644\u0627 \u0646\u062A\u0627\u0626\u062C", "results": "\u0646\u062A\u0627\u0626\u062C",
        "open_file": "\u0641\u062A\u062D", "show_folder": "\u0639\u0631\u0636 \u0641\u064A \u0627\u0644\u0645\u062C\u0644\u062F", "copy_path": "\u0646\u0633\u062E \u0627\u0644\u0645\u0633\u0627\u0631",
        "settings_title": "\u0627\u0644\u0625\u0639\u062F\u0627\u062F\u0627\u062A", "save_settings": "\u062D\u0641\u0638",
        "ready": "\u062C\u0627\u0647\u0632", "files_indexed": "\u0645\u0644\u0641 \u0645\u0641\u0647\u0631\u0633",
        "find_duplicates": "\u0628\u062D\u062B \u0639\u0646 \u0627\u0644\u0645\u0643\u0631\u0631\u0627\u062A", "files": "\u0645\u0644\u0641\u0627\u062A",
    },
}

def set_language(lang):
    global _LANG
    _LANG = TRANSLATIONS.get(lang, TRANSLATIONS["English"])
def tr(key):
    return _LANG.get(key, TRANSLATIONS["English"].get(key, key))
set_language("English")

def fmt_size(s):
    if not s: return ""
    for u in ("B", "KB", "MB", "GB", "TB"):
        if s < 1024: return f"{s:.0f} {u}" if u == "B" else f"{s:.1f} {u}"
        s /= 1024
    return f"{s:.1f} PB"

def fmt_time(ts):
    if not ts: return ""
    try:
        dt = datetime.fromtimestamp(ts)
        d = (datetime.now() - dt).days
        if d == 0: return f"Today {dt:%H:%M}"
        if d == 1: return "Yesterday"
        if d < 7: return f"{d}d ago"
        if d < 30: return f"{d//7}w ago"
        if d < 365: return f"{d//30}mo ago"
        return f"{dt:%d.%m.%Y}"
    except Exception:
        return ""

SETTINGS_PATH = os.path.join(SCRIPT_DIR, "QuickFind_Index", "settings.json")
def load_settings():
    d = {"theme": "dark", "font_size": 13, "show_hidden": False, "auto_index": True,
         "max_results": 200, "open_on_single_click": False, "language": "English",
         "minimize_to_tray": True, "global_hotkey": "Win+Alt+F"}
    try:
        with open(SETTINGS_PATH, "r") as f: d.update(json.load(f))
    except Exception: pass
    return d
def save_settings(s):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w") as f: json.dump(s, f, indent=2)
def detect_system_theme():
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        v, _ = winreg.QueryValueEx(k, "AppsUseLightTheme"); winreg.CloseKey(k)
        return "dark" if v == 0 else "light"
    except Exception: return "light"

# ── Data Model ──
class ResultModel(QAbstractListModel):
    NameRole=Qt.UserRole+1; PathRole=Qt.UserRole+2; ExtRole=Qt.UserRole+3
    SizeRole=Qt.UserRole+4; ModifiedRole=Qt.UserRole+5; IsDirRole=Qt.UserRole+6
    def __init__(self): super().__init__(); self._data=[]
    def rowCount(self, p=QModelIndex()): return len(self._data)
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row()>=len(self._data): return None
        r=self._data[index.row()]
        if role==self.NameRole: return r[0]
        if role==self.PathRole: return r[1]
        if role==self.ExtRole: return r[2]
        if role==self.SizeRole: return r[3]
        if role==self.ModifiedRole: return r[4]
        if role==self.IsDirRole: return r[5] if len(r)>5 else 0
        if role==Qt.DisplayRole: return r[0]
        return None
    def flags(self, index):
        f=super().flags(index)
        return f|Qt.ItemIsDragEnabled if index.isValid() else f
    def mimeData(self, indexes):
        m=QMimeData(); urls=[QUrl.fromLocalFile(self.data(i, self.PathRole)) for i in indexes if self.data(i, self.PathRole) and os.path.exists(self.data(i, self.PathRole))]
        if urls: m.setUrls(urls)
        return m
    def mimeTypes(self): return ["text/uri-list"]
    def set_results(self, results): self.beginResetModel(); self._data=results; self.endResetModel()
    def clear(self): self.beginResetModel(); self._data=[]; self.endResetModel()
    def get_path(self, index): return self._data[index][1] if 0<=index<len(self._data) else None

class ResultFilterProxy(QSortFilterProxyModel):
    def __init__(self, p=None): super().__init__(p); self._f=""
    def set_sub_filter(self, t): self._f=t.lower(); self.invalidateFilter()
    def filterAcceptsRow(self, row, parent):
        if not self._f: return True
        m=self.sourceModel(); i=m.index(row,0,parent)
        n=(m.data(i, ResultModel.NameRole) or "").lower()
        p=(m.data(i, ResultModel.PathRole) or "").lower()
        return self._f in n or self._f in p

CARD_H=72; CARD_GAP=2; CARD_R=12
class ResultDelegate(QStyledItemDelegate):
    def __init__(self, tg, p=None): super().__init__(p); self._theme=tg
    def sizeHint(self, o, i): return QSize(o.rect.width(), CARD_H+CARD_GAP)
    def paint(self, painter, option, index):
        t=self._theme(); painter.save(); painter.setRenderHint(QPainter.Antialiasing)
        r=QRectF(option.rect).adjusted(6,CARD_GAP,-6,0)
        sel=bool(option.state&QStyle.State_Selected); hov=bool(option.state&QStyle.State_MouseOver)
        if sel: bg,border,bw=QColor(t["card_sel"]),QColor(t["primary"]),1.0
        elif hov: bg,border,bw=QColor(t["card_hover"]),QColor(t["ov"]),0.5
        else: bg,border,bw=QColor(t["white"]),QColor(t["ov"]),0; border.setAlpha(40)
        card=QPainterPath(); card.addRoundedRect(r,CARD_R,CARD_R)
        painter.setPen(QPen(border,bw) if bw>0 else Qt.NoPen); painter.setBrush(QBrush(bg)); painter.drawPath(card)
        name=index.data(ResultModel.NameRole) or ""; fpath=index.data(ResultModel.PathRole) or ""
        ext=index.data(ResultModel.ExtRole) or ""; size=index.data(ResultModel.SizeRole) or 0
        modified=index.data(ResultModel.ModifiedRole) or 0; is_dir=index.data(ResultModel.IsDirRole) or 0
        isz=42; ix=r.x()+14; iy=r.y()+(r.height()-isz)/2; ir=QRectF(ix,iy,isz,isz)
        ip=QPainterPath(); ip.addRoundedRect(ir,10,10); painter.setPen(Qt.NoPen)
        ec=EXT_COLORS.get(ext)
        if ec: bc=QColor(ec); bc.setAlpha(25); painter.setBrush(QBrush(bc))
        else: painter.setBrush(QBrush(QColor(t["pc"])))
        painter.drawPath(ip)
        el=EXT_ICONS.get(ext,"DIR" if is_dir else ext.replace(".","").upper()[:3] if ext else "?")
        painter.setFont(QFont(FONT_MONO,8,QFont.Bold)); painter.setPen(QPen(QColor(ec) if ec else QColor(t["opc"])))
        painter.drawText(ir,Qt.AlignCenter,el)
        tx=ix+isz+12; mw=r.width()-(tx-r.x())-100
        painter.setFont(QFont(FONT,11,QFont.DemiBold)); painter.setPen(QPen(QColor(t["on_s"])))
        en=QFontMetrics(QFont(FONT,11,QFont.DemiBold)).elidedText(name,Qt.ElideRight,int(mw))
        painter.drawText(QRectF(tx,r.y()+14,mw,22),Qt.AlignLeft|Qt.AlignVCenter,en)
        painter.setFont(QFont(FONT,8)); painter.setPen(QPen(QColor(t["on_sv"])))
        dp=os.path.dirname(fpath).replace("\\"," / "); parts=dp.split(" / ")
        if len(parts)>4: dp=parts[0]+" / ... / "+" / ".join(parts[-2:])
        ep=QFontMetrics(QFont(FONT,8)).elidedText(dp,Qt.ElideMiddle,int(mw))
        painter.drawText(QRectF(tx,r.y()+38,mw,18),Qt.AlignLeft|Qt.AlignVCenter,ep)
        rx=r.x()+r.width()-90; sz=fmt_size(size)
        if sz and not is_dir:
            painter.setFont(QFont(FONT,9)); painter.setPen(QPen(QColor(t["on_sv"])))
            painter.drawText(QRectF(rx,r.y()+14,80,20),Qt.AlignRight|Qt.AlignVCenter,sz)
        tm=fmt_time(modified)
        if tm:
            painter.setFont(QFont(FONT,8)); painter.setPen(QPen(QColor(t["outline"])))
            painter.drawText(QRectF(rx,r.y()+38,80,18),Qt.AlignRight|Qt.AlignVCenter,tm)
        painter.restore()

class IndexerThread(QThread):
    progress=Signal(int); status=Signal(str); finished_indexing=Signal(); phase_changed=Signal(int,str)
    def __init__(self, db, reindex=True):
        super().__init__(); self.db=db; self.reindex=reindex
        from database import FileIndexer
        self.indexer=FileIndexer(db, progress_callback=lambda c:self.progress.emit(c),
            status_callback=lambda m:self.status.emit(m), phase_callback=lambda p,s:self.phase_changed.emit(p,s))
    def run(self):
        self.indexer.start(reindex=self.reindex)
        if self.indexer._thread: self.indexer._thread.join()
        self.finished_indexing.emit()
    def stop(self): self.indexer.stop()

class Sidebar(QWidget):
    page_changed=Signal(int)
    def __init__(self, p=None):
        super().__init__(p); self.setFixedWidth(180); self._buttons=[]; self._build()
    def _build(self):
        l=QVBoxLayout(self); l.setContentsMargins(12,16,12,16); l.setSpacing(4)
        t=QLabel("QuickFind"); t.setFont(QFont(FONT,14,QFont.ExtraBold)); l.addWidget(t)
        s=QLabel("Desktop Search"); s.setFont(QFont(FONT,8)); s.setObjectName("sidebar_sub"); l.addWidget(s)
        l.addSpacing(20)
        pages=[("\U0001F50D  Search",0),("\U0001F4CA  Index Status",1),("\U0001F4CB  Duplicates",2),
               ("\U0001F4C1  Disk Usage",3),("\U0001F4C8  Statistics",4),("\u2699\uFE0F  Settings",5)]
        for label,idx in pages:
            btn=QPushButton(label); btn.setFont(QFont(FONT,10,QFont.Medium)); btn.setFixedHeight(38)
            btn.setCursor(QCursor(Qt.PointingHandCursor)); btn.setCheckable(True)
            if idx==0: btn.setChecked(True)
            btn.clicked.connect(lambda c,i=idx:self._on_click(i)); l.addWidget(btn); self._buttons.append(btn)
        l.addStretch()
        v=QLabel("v2.0.0"); v.setFont(QFont(FONT,8)); v.setObjectName("sidebar_sub"); v.setAlignment(Qt.AlignCenter); l.addWidget(v)
    def _on_click(self, idx):
        for i,b in enumerate(self._buttons): b.setChecked(i==idx)
        self.page_changed.emit(idx)

# ── SearchTab ──
class SearchTab(QWidget):
    def __init__(self, db, tg, ud=None, p=None):
        super().__init__(p); self.db=db; self._theme=tg; self.ud=ud
        self._active_filter=None; self._active_sort="relevance"; self._filter_map={}
        self.max_results=200; self._current_path=""; self._build()
    def _build(self):
        layout=QHBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        left=QWidget(); ll=QVBoxLayout(left); ll.setContentsMargins(24,16,12,0); ll.setSpacing(6)
        self.search_input=QLineEdit(); self.search_input.setPlaceholderText(tr("search_placeholder"))
        self.search_input.setFont(QFont(FONT,13)); self.search_input.setFixedHeight(48)
        self.search_input.setObjectName("search_input"); self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self._do_search)
        self._search_timer=QTimer(); self._search_timer.setSingleShot(True); self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._do_search)
        self.search_input.textChanged.connect(self._on_text_changed)
        ll.addWidget(self.search_input)
        self.sub_filter=QLineEdit(); self.sub_filter.setPlaceholderText("Filter results... (Ctrl+F)")
        self.sub_filter.setFont(QFont(FONT,10)); self.sub_filter.setFixedHeight(32)
        self.sub_filter.setObjectName("sub_filter"); self.sub_filter.setVisible(False)
        self.sub_filter.textChanged.connect(self._on_sub_filter); ll.addWidget(self.sub_filter)
        fr=QWidget(); fr_l=QHBoxLayout(fr); fr_l.setContentsMargins(0,2,0,0); fr_l.setSpacing(5)
        self._filter_buttons={}
        FILTERS={"All":None,"Documents":[".pdf",".docx",".doc",".rtf",".txt",".md",".epub",".rst"],
            "Images":[".jpg",".jpeg",".png",".gif",".svg",".webp",".bmp"],
            "Code":[".py",".js",".ts",".jsx",".tsx",".html",".css",".java",".cpp",".c",".cs",".go",".rs",".rb",".php"],
            "Archives":[".zip",".rar",".7z",".tar",".gz",".exe",".msi"],"PDFs":[".pdf"]}
        self._filter_map=FILTERS
        for label in FILTERS:
            btn=QPushButton(label); btn.setFont(QFont(FONT,9)); btn.setFixedHeight(28)
            btn.setCursor(QCursor(Qt.PointingHandCursor)); btn.setCheckable(True)
            if label=="All": btn.setChecked(True)
            btn.clicked.connect(lambda c,l=label:self._set_filter(l)); fr_l.addWidget(btn); self._filter_buttons[label]=btn
        fr_l.addStretch()
        self._sort_buttons={}
        for label,key in [("Relevance","relevance"),("Name","name_asc"),("Size","size_desc"),("Newest","date_new")]:
            btn=QPushButton(label); btn.setFont(QFont(FONT,8)); btn.setFixedHeight(28)
            btn.setCursor(QCursor(Qt.PointingHandCursor)); btn.setCheckable(True)
            if key=="relevance": btn.setChecked(True)
            btn.clicked.connect(lambda c,k=key:self._set_sort(k)); fr_l.addWidget(btn); self._sort_buttons[key]=btn
        ll.addWidget(fr)
        stats=QWidget(); sl=QHBoxLayout(stats); sl.setContentsMargins(2,0,2,0)
        self.result_count=QLabel(""); self.result_count.setFont(QFont(FONT,9,QFont.Bold)); self.result_count.setObjectName("result_count")
        self.search_time=QLabel(""); self.search_time.setFont(QFont(FONT,9)); self.search_time.setObjectName("search_time")
        self.active_filters_label=QLabel(""); self.active_filters_label.setFont(QFont(FONT,8)); self.active_filters_label.setObjectName("search_time")
        sl.addWidget(self.result_count); sl.addSpacing(8); sl.addWidget(self.active_filters_label); sl.addStretch(); sl.addWidget(self.search_time)
        ll.addWidget(stats)
        self.model=ResultModel(); self.proxy=ResultFilterProxy(); self.proxy.setSourceModel(self.model)
        self.delegate=ResultDelegate(self._theme)
        self.list_view=QListView(); self.list_view.setModel(self.proxy); self.list_view.setItemDelegate(self.delegate)
        self.list_view.setVerticalScrollMode(QListView.ScrollPerPixel); self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_view.setSelectionMode(QListView.ExtendedSelection); self.list_view.setMouseTracking(True)
        self.list_view.setFrameShape(QListView.NoFrame); self.list_view.setUniformItemSizes(True)
        self.list_view.setDragEnabled(True); self.list_view.setDragDropMode(QListView.DragOnly)
        self.list_view.doubleClicked.connect(self._on_double_click)
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu); self.list_view.customContextMenuRequested.connect(self._ctx_menu)
        sm=self.list_view.selectionModel()
        if sm: sm.currentChanged.connect(self._on_sel)
        ll.addWidget(self.list_view)
        self.empty=QWidget(); el=QVBoxLayout(self.empty); el.setAlignment(Qt.AlignCenter)
        ei=QLabel("\U0001F50D"); ei.setFont(QFont(FONT,48)); ei.setAlignment(Qt.AlignCenter); el.addWidget(ei); el.addSpacing(8)
        self.empty_title=QLabel(tr("ready_to_search")); self.empty_title.setFont(QFont(FONT,20,QFont.Bold)); self.empty_title.setAlignment(Qt.AlignCenter)
        self.empty_sub=QLabel(tr("type_query")); self.empty_sub.setFont(QFont(FONT,10)); self.empty_sub.setAlignment(Qt.AlignCenter); self.empty_sub.setObjectName("empty_sub")
        el.addWidget(self.empty_title); el.addSpacing(4); el.addWidget(self.empty_sub)
        hints=QLabel("Ctrl+L Focus \u00B7 Ctrl+F Filter \u00B7 Ctrl+P Commands \u00B7 Ctrl+T Tab \u00B7 Ctrl+H History")
        hints.setFont(QFont(FONT_MONO,8)); hints.setAlignment(Qt.AlignCenter); hints.setObjectName("empty_sub")
        el.addSpacing(16); el.addWidget(hints)
        ll.addWidget(self.empty); self.list_view.hide(); self.empty.show()
        layout.addWidget(left,1)
        self.detail=QWidget(); self.detail.setFixedWidth(280); self.detail.setObjectName("detail_pane")
        dl=QVBoxLayout(self.detail); dl.setContentsMargins(16,20,16,16); dl.setSpacing(10)
        self.preview_frame=QWidget(); self.preview_frame.setMinimumHeight(140); self.preview_frame.setMaximumHeight(220); self.preview_frame.setObjectName("preview_frame")
        pfl=QVBoxLayout(self.preview_frame); pfl.setContentsMargins(10,8,10,8); pfl.setSpacing(4)
        self.preview_icon=QLabel(""); self.preview_icon.setFont(QFont(FONT_MONO,28,QFont.Bold)); self.preview_icon.setAlignment(Qt.AlignCenter); self.preview_icon.setObjectName("preview_icon"); self.preview_icon.setFixedHeight(50)
        pfl.addWidget(self.preview_icon)
        self.preview_scroll=QScrollArea(); self.preview_scroll.setWidgetResizable(True); self.preview_scroll.setFrameShape(QFrame.NoFrame)
        self.preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.preview_scroll.setStyleSheet("background:transparent;border:none;")
        self.preview_text=QLabel("No preview"); self.preview_text.setFont(QFont(FONT,8)); self.preview_text.setAlignment(Qt.AlignCenter)
        self.preview_text.setObjectName("preview_text"); self.preview_text.setWordWrap(True); self.preview_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.preview_text.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.preview_scroll.setWidget(self.preview_text); pfl.addWidget(self.preview_scroll,1); dl.addWidget(self.preview_frame)
        self.d_name=QLabel(tr("select_file")); self.d_name.setFont(QFont(FONT,12,QFont.Bold)); self.d_name.setWordWrap(True); dl.addWidget(self.d_name)
        self.d_type=QLabel(""); self.d_type.setFont(QFont(FONT,9,QFont.Medium)); self.d_type.setObjectName("d_type"); dl.addWidget(self.d_type)
        dl.addSpacing(4)
        self.d_size=self._irow(dl,"SIZE"); self.d_modified=self._irow(dl,"MODIFIED"); self.d_ext=self._irow(dl,"EXTENSION")
        self.d_hash=self._irow(dl,"HASH",True); self.d_path=self._irow(dl,"PATH",True)
        dl.addSpacing(8)
        self.open_btn=QPushButton(tr("open_file")); self.open_btn.setObjectName("open_btn"); self.open_btn.setFont(QFont(FONT,10,QFont.DemiBold))
        self.open_btn.setFixedHeight(40); self.open_btn.setCursor(QCursor(Qt.PointingHandCursor)); self.open_btn.clicked.connect(self._open_file); dl.addWidget(self.open_btn)
        self.folder_btn=QPushButton(tr("show_folder")); self.folder_btn.setObjectName("folder_btn"); self.folder_btn.setFont(QFont(FONT,10,QFont.DemiBold))
        self.folder_btn.setFixedHeight(40); self.folder_btn.setCursor(QCursor(Qt.PointingHandCursor)); self.folder_btn.clicked.connect(self._open_folder); dl.addWidget(self.folder_btn)
        br=QHBoxLayout()
        self.copy_btn=QPushButton(tr("copy_path")); self.copy_btn.setObjectName("copy_btn"); self.copy_btn.setFont(QFont(FONT,9)); self.copy_btn.setFixedHeight(32)
        self.copy_btn.setCursor(QCursor(Qt.PointingHandCursor)); self.copy_btn.clicked.connect(self._copy_path); br.addWidget(self.copy_btn)
        self.bm_btn=QPushButton("\u2606"); self.bm_btn.setObjectName("copy_btn"); self.bm_btn.setFont(QFont(FONT,14)); self.bm_btn.setFixedSize(32,32)
        self.bm_btn.setCursor(QCursor(Qt.PointingHandCursor)); self.bm_btn.clicked.connect(self._toggle_bm); br.addWidget(self.bm_btn)
        dl.addLayout(br)
        self.sim_btn=QPushButton(tr("find_similar")); self.sim_btn.setObjectName("copy_btn"); self.sim_btn.setFont(QFont(FONT,9))
        self.sim_btn.setFixedHeight(28); self.sim_btn.setCursor(QCursor(Qt.PointingHandCursor)); self.sim_btn.clicked.connect(self._find_similar); dl.addWidget(self.sim_btn)
        self.hash_search_btn=QPushButton("\U0001F50D Search by Hash"); self.hash_search_btn.setObjectName("copy_btn"); self.hash_search_btn.setFont(QFont(FONT,9))
        self.hash_search_btn.setFixedHeight(28); self.hash_search_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.hash_search_btn.setToolTip("Find all files with the same content hash")
        self.hash_search_btn.clicked.connect(self._search_by_hash); dl.addWidget(self.hash_search_btn)
        dl.addStretch(); layout.addWidget(self.detail)
    def _irow(self, parent, label, mono=False):
        row=QWidget(); rl=QHBoxLayout(row); rl.setContentsMargins(0,2,0,2)
        lbl=QLabel(label); lbl.setFont(QFont(FONT,8,QFont.Bold)); lbl.setFixedWidth(75); lbl.setObjectName("info_label")
        val=QLabel("\u2014"); val.setFont(QFont(FONT_MONO if mono else FONT,9)); val.setWordWrap(True)
        rl.addWidget(lbl); rl.addWidget(val,1); parent.addWidget(row); return val
    def _on_text_changed(self, t):
        self._search_timer.stop()
        if t.strip() or self._active_filter: self._search_timer.start()
        else: self.model.clear(); self.list_view.hide(); self.empty.show(); self.result_count.setText(""); self.search_time.setText(""); self.active_filters_label.setText("")
    def _do_search(self):
        self._search_timer.stop(); q=self.search_input.text().strip()
        if not q and not self._active_filter:
            self.model.clear(); self.list_view.hide(); self.empty.show(); self.result_count.setText(""); self.search_time.setText(""); return
        from quickfind.search_parser import parse_query
        sq=parse_query(q); t0=time.perf_counter()
        results=self.db.search(" ".join(sq.fts_terms), limit=self.max_results, ext_filter=sq.ext_filter or self._active_filter,
            sort=self._active_sort, min_size=sq.min_size, max_size=sq.max_size, date_from=sq.date_from, date_to=sq.date_to,
            folder_filter=sq.folder_filter, regex_pattern=sq.regex_pattern.pattern if sq.regex_pattern else None, content_filter=sq.content_filter)
        ms=(time.perf_counter()-t0)*1000
        if self.ud:
            pp=self.ud.pinned.get_paths()
            if pp: pinned=[r for r in results if r[1] in pp]; others=[r for r in results if r[1] not in pp]; results=pinned+others
        if results: self.model.set_results(results); self.empty.hide(); self.list_view.show(); self.list_view.setCurrentIndex(self.proxy.index(0,0))
        else: self.model.clear(); self.list_view.hide(); self.empty.show(); self.empty_title.setText(tr("no_results")); self.empty_sub.setText(tr("try_different"))
        self.result_count.setText(f"{len(results)} {tr('results')}"); self.search_time.setText(f"{ms:.1f} ms"); self.active_filters_label.setText(sq.to_display_string())
        if self.ud and q: self.ud.history.add(q)
    def _on_sub_filter(self, t): self.proxy.set_sub_filter(t)
    def _set_filter(self, label):
        for n,b in self._filter_buttons.items(): b.setChecked(n==label)
        self._active_filter=self._filter_map.get(label)
        if self.search_input.text().strip() or self._active_filter: self._do_search()
    def _set_sort(self, key):
        for k,b in self._sort_buttons.items(): b.setChecked(k==key)
        self._active_sort=key
        if self.search_input.text().strip() or self._active_filter: self._do_search()
    def _on_sel(self, current, prev):
        if not current.isValid(): return
        src=self.proxy.mapToSource(current)
        name=src.data(ResultModel.NameRole) or ""; path=src.data(ResultModel.PathRole) or ""
        ext=src.data(ResultModel.ExtRole) or ""; size=src.data(ResultModel.SizeRole) or 0
        modified=src.data(ResultModel.ModifiedRole) or 0; self._current_path=path
        self.d_name.setText(name); self.d_type.setText(TYPE_NAMES.get(ext, ext.upper().replace(".","")+" File" if ext else "File"))
        self.d_size.setText(fmt_size(size)); self.d_ext.setText(ext or "\u2014"); self.d_path.setText(os.path.dirname(path))
        try:
            h=self.db.get_file_hash(path); self.d_hash.setText(h[:16]+"\u2026" if h and len(h)>16 else (h or "\u2014")); self.d_hash.setToolTip(h if h else "")
        except: self.d_hash.setText("\u2014")
        if self.ud: self.bm_btn.setText("\u2605" if self.ud.bookmarks.is_bookmarked(path) else "\u2606")
        el=EXT_ICONS.get(ext, ext.replace(".","").upper()[:3] if ext else "?")
        self.preview_icon.show(); self.preview_icon.setFixedHeight(50); self.preview_icon.setText(el)
        IMG={".jpg",".jpeg",".png",".gif",".bmp",".webp",".svg"}; TXT={".txt",".md",".py",".js",".ts",".html",".css",".json",".xml",".yaml",".yml",".csv",".sql",".sh",".bat",".java",".cpp",".c",".cs",".go",".rs",".rb",".php",".jsx",".tsx",".vue",".toml"}
        RICH={".pdf",".docx",".xlsx",".pptx",".rtf",".epub"}; pok=False
        if ext in IMG and os.path.exists(path):
            try:
                px=QPixmap(path)
                if not px.isNull(): px=px.scaled(240,180,Qt.KeepAspectRatio,Qt.SmoothTransformation); self.preview_icon.setPixmap(px); self.preview_icon.setFixedHeight(px.height()); self.preview_text.setText(""); pok=True
            except: pass
        if not pok and os.path.exists(path) and (size is None or size<2_000_000):
            if ext in TXT:
                try:
                    with open(path,"r",encoding="utf-8",errors="ignore") as f: preview=f.read(1000)
                    if preview.strip(): self.preview_icon.hide(); self.preview_icon.setFixedHeight(0); self.preview_text.setText(preview[:600]); self.preview_text.setFont(QFont(FONT_MONO,7)); self.preview_text.setAlignment(Qt.AlignLeft|Qt.AlignTop); pok=True
                except: pass
            elif ext in RICH:
                try:
                    from database import RICH_READERS; reader=RICH_READERS.get(ext)
                    if reader:
                        content=reader(path)
                        if content and content.strip(): self.preview_icon.hide(); self.preview_icon.setFixedHeight(0); self.preview_text.setText(content[:600]); self.preview_text.setFont(QFont(FONT,8)); self.preview_text.setAlignment(Qt.AlignLeft|Qt.AlignTop); pok=True
                except: pass
        if not pok: self.preview_text.setText(tr("no_preview")+(f" {ext.upper().replace('.','')}" if ext else "")); self.preview_text.setFont(QFont(FONT,8)); self.preview_text.setAlignment(Qt.AlignCenter)
        if modified:
            try: self.d_modified.setText(datetime.fromtimestamp(modified).strftime("%b %d, %Y  %H:%M"))
            except: self.d_modified.setText("\u2014")
    def _sel_paths(self):
        return [self.proxy.mapToSource(i).data(ResultModel.PathRole) for i in self.list_view.selectionModel().selectedIndexes() if self.proxy.mapToSource(i).data(ResultModel.PathRole)]
    def _on_double_click(self, idx):
        p=self.proxy.mapToSource(idx).data(ResultModel.PathRole)
        if p: self._open_path(p)
    def _open_path(self, p):
        if p and os.path.exists(p):
            try: os.startfile(p)
            except: pass
            if self.ud: self.ud.recent.add(p)
    def _open_file(self):
        if self._current_path: self._open_path(self._current_path)
    def _open_folder(self):
        if self._current_path:
            try:
                if os.path.exists(self._current_path): subprocess.Popen(["explorer","/select,",self._current_path])
                elif os.path.exists(os.path.dirname(self._current_path)): os.startfile(os.path.dirname(self._current_path))
            except: pass
    def _copy_path(self):
        pp=self._sel_paths()
        if pp: QApplication.clipboard().setText("\n".join(pp))
    def _toggle_bm(self):
        if self.ud and self._current_path: self.ud.bookmarks.toggle(self._current_path); self.bm_btn.setText("\u2605" if self.ud.bookmarks.is_bookmarked(self._current_path) else "\u2606")
    def _find_similar(self):
        if self._current_path:
            results=self.db.find_similar(os.path.basename(self._current_path),limit=50)
            if results: self.model.set_results(results); self.empty.hide(); self.list_view.show(); self.result_count.setText(f"{len(results)} similar")
    def _search_by_hash(self):
        """Find all files with the same hash as the selected file."""
        if not self._current_path: return
        h=self.db.get_file_hash(self._current_path)
        if not h or h=="-":
            # Hash not computed yet — compute now
            from database import FileIndexer
            try:
                sz=os.path.getsize(self._current_path)
                h=FileIndexer.compute_file_hash(self._current_path, sz)
                if h: self.db.upsert_file(os.path.basename(self._current_path), os.path.dirname(self._current_path),
                    os.path.splitext(self._current_path)[1].lower(), sz, os.path.getmtime(self._current_path),
                    os.path.basename(os.path.dirname(self._current_path)), "", h)
            except: pass
        if not h or h=="-": return
        self.search_input.setText(f"hash:{h}"); self._do_search()
    def _ctx_menu(self, pos):
        pp=self._sel_paths()
        if not pp: return
        m=QMenu(self); m.addAction("Open",self._open_file); m.addAction("Show in Folder",self._open_folder); m.addSeparator()
        m.addAction("Copy Path(s)",self._copy_path); m.addSeparator()
        if self.ud and len(pp)==1:
            ib=self.ud.bookmarks.is_bookmarked(pp[0]); m.addAction("\u2605 Remove Bookmark" if ib else "\u2606 Bookmark",self._toggle_bm)
            ip=self.ud.pinned.is_pinned(pp[0]); m.addAction("Unpin" if ip else "Pin to Top",lambda:(self.ud.pinned.toggle(pp[0]),self._do_search()))
        if len(pp)==2:
            m.addSeparator(); m.addAction("Compare Files",lambda:self._compare(pp[0],pp[1]))
        m.addSeparator(); em=m.addMenu("Export Results"); em.addAction("CSV",lambda:self._export("csv")); em.addAction("TXT",lambda:self._export("txt"))
        m.exec(self.list_view.viewport().mapToGlobal(pos))
    def _compare(self, p1, p2):
        from quickfind.file_compare import compare_files, get_diff_stats
        d=compare_files(p1,p2); s=get_diff_stats(d)
        QMessageBox.information(self,"Compare",f"{os.path.basename(p1)} vs {os.path.basename(p2)}\n\nAdded: {s['added']}\nRemoved: {s['removed']}\nChanged: {s['changed']}\nSame: {s['same']}")
    def _export(self, fmt):
        if not self.model._data: return
        from quickfind.export import export_to_csv, export_to_txt
        fs={"csv":"CSV (*.csv)","txt":"Text (*.txt)"}; p,_=QFileDialog.getSaveFileName(self,"Export","",fs.get(fmt,""))
        if p: {"csv":export_to_csv,"txt":export_to_txt}[fmt](self.model._data,p)
    def toggle_sub_filter(self):
        self.sub_filter.setVisible(not self.sub_filter.isVisible())
        if self.sub_filter.isVisible(): self.sub_filter.setFocus()
        else: self.sub_filter.clear()

class SearchPage(QWidget):
    def __init__(self, db, tg, ud=None, p=None):
        super().__init__(p); self.db=db; self._theme=tg; self.ud=ud; self.max_results=200; self._build()
    def _build(self):
        l=QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(0)
        self.tabs=QTabWidget(); self.tabs.setTabsClosable(True); self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        ab=QPushButton("+"); ab.setFixedSize(28,28); ab.setFont(QFont(FONT,12,QFont.Bold)); ab.setCursor(QCursor(Qt.PointingHandCursor)); ab.clicked.connect(self._add_tab)
        self.tabs.setCornerWidget(ab,Qt.TopRightCorner); self._add_tab(); l.addWidget(self.tabs)
    def _add_tab(self):
        if self.tabs.count()>=8: return
        t=SearchTab(self.db,self._theme,self.ud); t.max_results=self.max_results
        self.tabs.addTab(t,f"Search {self.tabs.count()+1}"); self.tabs.setCurrentWidget(t)
    def _close_tab(self, i):
        if self.tabs.count()>1: self.tabs.removeTab(i)
    @property
    def current_tab(self): return self.tabs.currentWidget()
    @property
    def search_input(self):
        t=self.current_tab; return t.search_input if t else None
    @property
    def detail(self):
        t=self.current_tab; return t.detail if t else None
    @property
    def preview_frame(self):
        t=self.current_tab; return t.preview_frame if t else None

class IndexStatusPage(QWidget):
    reindex_requested=Signal()
    def __init__(self, db, tg, p=None):
        super().__init__(p); self.db=db; self._theme=tg; self._build()
    def _build(self):
        sc=QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame)
        c=QWidget(); ml=QVBoxLayout(c); ml.setContentsMargins(32,24,32,24); ml.setSpacing(20)
        hdr=QHBoxLayout()
        self.title_label=QLabel(tr("index_title")); self.title_label.setFont(QFont(FONT,24,QFont.ExtraBold)); hdr.addWidget(self.title_label); hdr.addStretch()
        self.rebuild_btn=QPushButton(tr("rebuild_index")); self.rebuild_btn.setObjectName("primary_btn"); self.rebuild_btn.setFont(QFont(FONT,10,QFont.Bold))
        self.rebuild_btn.setFixedHeight(40); self.rebuild_btn.setCursor(QCursor(Qt.PointingHandCursor)); self.rebuild_btn.clicked.connect(self.reindex_requested.emit); hdr.addWidget(self.rebuild_btn)
        ml.addLayout(hdr)
        pc=QFrame(); pc.setFrameShape(QFrame.StyledPanel); pc.setObjectName("card"); pcl=QVBoxLayout(pc); pcl.setContentsMargins(20,16,20,16); pcl.setSpacing(10)
        ph=QHBoxLayout(); self.progress_title=QLabel(tr("current_progress")); self.progress_title.setFont(QFont(FONT,14,QFont.Bold))
        self.phase_label=QLabel(""); self.phase_label.setFont(QFont(FONT,9)); self.phase_label.setObjectName("page_desc")
        self.progress_badge=QLabel("READY"); self.progress_badge.setFont(QFont(FONT,8,QFont.Bold)); self.progress_badge.setObjectName("progress_badge")
        ph.addWidget(self.progress_title); ph.addSpacing(8); ph.addWidget(self.phase_label); ph.addStretch(); ph.addWidget(self.progress_badge); pcl.addLayout(ph)
        self.progress_bar=QProgressBar(); self.progress_bar.setFixedHeight(10); self.progress_bar.setTextVisible(False); self.progress_bar.setValue(100); pcl.addWidget(self.progress_bar)
        self.progress_detail=QLabel(""); self.progress_detail.setFont(QFont(FONT,9)); self.progress_detail.setObjectName("page_desc"); pcl.addWidget(self.progress_detail)
        sr=QHBoxLayout(); sr.setSpacing(10)
        self.stat_speed=self._sbox(sr,"SPEED","\u2014"); self.stat_time=self._sbox(sr,"DURATION","\u2014"); self.stat_queue=self._sbox(sr,"FILES","0"); pcl.addLayout(sr)
        ml.addWidget(pc)
        dc=QFrame(); dc.setFrameShape(QFrame.StyledPanel); dc.setObjectName("card"); dcl=QVBoxLayout(dc); dcl.setContentsMargins(20,16,20,16); dcl.setSpacing(10)
        self.db_stats_title=QLabel(tr("db_stats")); self.db_stats_title.setFont(QFont(FONT,14,QFont.Bold)); dcl.addWidget(self.db_stats_title)
        self.db_size_val=self._drow(dcl,tr("db_size"),"\u2014"); self.db_created_val=self._drow(dcl,tr("last_indexed"),"\u2014"); self.db_latency_val=self._drow(dcl,tr("search_latency"),"< 1ms")
        ml.addWidget(dc)
        self.depth_title=QLabel(tr("content_depth")); self.depth_title.setFont(QFont(FONT,16,QFont.Bold)); ml.addWidget(self.depth_title)
        from database import PRESETS, get_preset_name
        cur=get_preset_name(); self._preset_group=QButtonGroup(self); self._preset_radios={}
        for k in ["minimal","standard","deep","maximum"]:
            p=PRESETS[k]; rb=QRadioButton(f"{k.capitalize()} \u2014 {p['label']}")
            if k==cur: rb.setChecked(True)
            self._preset_group.addButton(rb); self._preset_radios[k]=rb; ml.addWidget(rb)
        self.save_preset_btn=QPushButton(tr("save_reindex")); self.save_preset_btn.setObjectName("primary_btn"); self.save_preset_btn.setFont(QFont(FONT,10,QFont.Bold))
        self.save_preset_btn.setFixedHeight(38); self.save_preset_btn.setFixedWidth(180); self.save_preset_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_preset_btn.clicked.connect(self._save_preset); ml.addWidget(self.save_preset_btn)
        ml.addStretch(); sc.setWidget(c); self._scroll=sc; self._content=c
        outer=QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(sc)
    def _sbox(self, pl, label, value):
        w=QFrame(); w.setFrameShape(QFrame.StyledPanel); w.setObjectName("stat_box"); l=QVBoxLayout(w); l.setContentsMargins(12,8,12,8); l.setSpacing(2)
        lb=QLabel(label); lb.setFont(QFont(FONT,7,QFont.Bold)); lb.setObjectName("stat_label")
        v=QLabel(value); v.setFont(QFont(FONT,16,QFont.Black)); v.setObjectName("stat_value")
        l.addWidget(lb); l.addWidget(v); pl.addWidget(w); return v
    def _drow(self, pl, label, value):
        r=QWidget(); rl=QHBoxLayout(r); rl.setContentsMargins(0,4,0,4)
        lb=QLabel(label); lb.setFont(QFont(FONT,10)); lb.setObjectName("page_desc")
        v=QLabel(value); v.setFont(QFont(FONT,11,QFont.Bold)); rl.addWidget(lb); rl.addStretch(); rl.addWidget(v); pl.addWidget(r); return v
    def refresh(self):
        n=self.db.get_file_count(); ds=self.db.get_db_size_mb(); li=self.db.get_meta("last_index_time"); dur=self.db.get_meta("index_duration")
        self.stat_queue.setText(f"{n:,}"); self.db_size_val.setText(f"{ds:.0f} MB"); self.stat_time.setText(f"{dur}s" if dur else "\u2014")
        if li:
            try: self.db_created_val.setText(datetime.fromisoformat(li).strftime("%b %d, %H:%M"))
            except: pass
    def _save_preset(self):
        from database import get_preset_name, set_preset_name
        for k,rb in self._preset_radios.items():
            if rb.isChecked() and k!=get_preset_name(): set_preset_name(k); break
        self.reindex_requested.emit()
    def apply_theme(self, t):
        from PySide6.QtGui import QPalette
        bg = QColor(t["bg"])
        for w in [self._scroll, self._content]:
            pal = w.palette(); pal.setColor(QPalette.Window, bg); w.setPalette(pal); w.setAutoFillBackground(True)
        if self._scroll.viewport():
            vp = self._scroll.viewport().palette(); vp.setColor(QPalette.Window, bg)
            self._scroll.viewport().setPalette(vp); self._scroll.viewport().setAutoFillBackground(True)
        self._scroll.setStyleSheet("border: none;")
    def retranslate(self): self.title_label.setText(tr("index_title")); self.rebuild_btn.setText(tr("rebuild_index"))

class DuplicatesPage(QWidget):
    def __init__(self, db, tg, p=None):
        super().__init__(p); self.db=db; self._theme=tg; self._build()
    def _build(self):
        l=QVBoxLayout(self); l.setContentsMargins(32,24,32,24); l.setSpacing(16)
        h=QHBoxLayout(); t=QLabel(tr("find_duplicates")); t.setFont(QFont(FONT,24,QFont.ExtraBold)); h.addWidget(t); h.addStretch()
        self.scan_btn=QPushButton(tr("find_duplicates")); self.scan_btn.setObjectName("primary_btn"); self.scan_btn.setFont(QFont(FONT,10,QFont.Bold))
        self.scan_btn.setFixedHeight(40); self.scan_btn.setCursor(QCursor(Qt.PointingHandCursor)); self.scan_btn.clicked.connect(self._find); h.addWidget(self.scan_btn); l.addLayout(h)
        f=QHBoxLayout(); f.addWidget(QLabel(tr("min_file_size")+":"))
        self.ms_combo=QComboBox(); self.ms_combo.addItems(["Any","1 KB","100 KB","1 MB","10 MB","100 MB"]); self.ms_combo.setCurrentIndex(2); self.ms_combo.setFixedWidth(130); f.addWidget(self.ms_combo)
        f.addStretch(); self.result_info=QLabel(""); self.result_info.setFont(QFont(FONT,10,QFont.DemiBold)); f.addWidget(self.result_info); l.addLayout(f)
        self.model=ResultModel(); self.delegate=ResultDelegate(self._theme)
        self.lv=QListView(); self.lv.setModel(self.model); self.lv.setItemDelegate(self.delegate)
        self.lv.setVerticalScrollMode(QListView.ScrollPerPixel); self.lv.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lv.setMouseTracking(True); self.lv.setFrameShape(QListView.NoFrame); self.lv.setUniformItemSizes(True)
        self.lv.doubleClicked.connect(lambda i:os.startfile(os.path.dirname(self.model.get_path(i.row()))) if self.model.get_path(i.row()) and os.path.exists(self.model.get_path(i.row())) else None)
        l.addWidget(self.lv,1)
    def _find(self):
        sizes=[1,1024,102400,1048576,10485760,104857600]; ms=sizes[self.ms_combo.currentIndex()]
        rows=self.db.find_duplicates(limit=1000,min_size=ms); results=[(r[1],r[2],r[3],r[4],r[5],0,0) for r in rows]; self.model.set_results(results)
        hs=set(r[0] for r in rows); self.result_info.setText(f"{len(results)} duplicates in {len(hs)} groups" if results else "No duplicates found")
    def apply_theme(self, t):
        from PySide6.QtGui import QPalette
        pal = self.palette(); pal.setColor(QPalette.Window, QColor(t["bg"])); self.setPalette(pal); self.setAutoFillBackground(True)

class DiskUsagePage(QWidget):
    def __init__(self, db, tg, p=None):
        super().__init__(p); self.db=db; self._theme=tg; self._data=[]; self._build()
    def _build(self):
        l=QVBoxLayout(self); l.setContentsMargins(32,24,32,24); l.setSpacing(16)
        h=QHBoxLayout(); t=QLabel(tr("disk_usage")); t.setFont(QFont(FONT,24,QFont.ExtraBold)); h.addWidget(t); h.addStretch()
        self.btn=QPushButton("Analyze"); self.btn.setObjectName("primary_btn"); self.btn.setFont(QFont(FONT,10,QFont.Bold))
        self.btn.setFixedHeight(40); self.btn.setCursor(QCursor(Qt.PointingHandCursor)); self.btn.clicked.connect(self._analyze); h.addWidget(self.btn); l.addLayout(h)
        self.info=QLabel("Click Analyze to scan folder sizes."); self.info.setFont(QFont(FONT,11)); self.info.setObjectName("page_desc"); l.addWidget(self.info)
        self.chart=QWidget(); self.chart.setMinimumHeight(400); l.addWidget(self.chart,1)
    def _analyze(self):
        from quickfind.folder_analyzer import FolderAnalyzer
        self._data=FolderAnalyzer(self.db).get_top_folders(30); self.info.setText(f"Top {len(self._data)} folders by size"); self.update()
    def paintEvent(self, e):
        super().paintEvent(e)
        if not self._data: return
        t=self._theme(); p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        cr=self.chart.geometry(); x=cr.x()+10; y=cr.y()+10; w=cr.width()-20; bh=22; gap=4
        mx=max(d["total_size"] for d in self._data) if self._data else 1
        for i,d in enumerate(self._data[:25]):
            if y+bh>cr.bottom(): break
            ratio=d["total_size"]/mx if mx>0 else 0; bw=int(w*0.5*ratio)
            p.setPen(Qt.NoPen); c=QColor(t["primary"]); c.setAlpha(180); p.setBrush(QBrush(c)); p.drawRoundedRect(QRectF(x,y,bw,bh),4,4)
            p.setPen(QPen(QColor(t["on_s"]))); p.setFont(QFont(FONT,8))
            folder=d["path"]; parts=folder.split("\\")
            if len(parts)>3: folder=parts[0]+"\\...\\"+parts[-1]
            p.drawText(QRectF(x+bw+8,y,w-bw-8,bh),Qt.AlignLeft|Qt.AlignVCenter,f"{folder} ({fmt_size(d['total_size'])}, {d['file_count']:,})")
            y+=bh+gap
        p.end()
    def apply_theme(self, t):
        from PySide6.QtGui import QPalette
        pal = self.palette(); pal.setColor(QPalette.Window, QColor(t["bg"])); self.setPalette(pal); self.setAutoFillBackground(True)

class StatisticsPage(QWidget):
    def __init__(self, db, tg, p=None):
        super().__init__(p); self.db=db; self._theme=tg; self._build()
    def _build(self):
        l=QVBoxLayout(self); l.setContentsMargins(32,24,32,24); l.setSpacing(16)
        t=QLabel(tr("statistics")); t.setFont(QFont(FONT,24,QFont.ExtraBold)); l.addWidget(t)
        self.btn=QPushButton("Refresh"); self.btn.setObjectName("primary_btn"); self.btn.setFont(QFont(FONT,10,QFont.Bold))
        self.btn.setFixedHeight(36); self.btn.setFixedWidth(120); self.btn.setCursor(QCursor(Qt.PointingHandCursor)); self.btn.clicked.connect(self._refresh); l.addWidget(self.btn)
        self.txt=QTextEdit(); self.txt.setReadOnly(True); self.txt.setFont(QFont(FONT_MONO,10)); l.addWidget(self.txt,1)
    def _refresh(self):
        from quickfind.folder_analyzer import FolderAnalyzer
        fa=FolderAnalyzer(self.db); es=fa.get_extension_stats(); sd=fa.get_size_distribution(); tl=fa.get_timeline(14)
        lines=[f"Total: {self.db.get_file_count():,} files | DB: {self.db.get_db_size_mb():.0f} MB\n","=== FILE TYPES ===\n"]
        for e in es[:20]: lines.append(f"  {e['extension'] or '(none)':>10}  {e['file_count']:>8,} files  {fmt_size(e['total_size']):>10}")
        lines.append("\n\n=== SIZE DISTRIBUTION ===\n")
        mx=max(sd.values()) if sd else 1
        for lb,cnt in sd.items(): bar="\u2588"*min(40,cnt//max(1,mx//40)); lines.append(f"  {lb:>12}  {cnt:>8,}  {bar}")
        lines.append("\n\n=== RECENT ACTIVITY ===\n")
        if tl:
            tmx=max(d["count"] for d in tl) if tl else 1
            for d in tl: bar="\u2588"*min(40,d["count"]//max(1,tmx//40)); lines.append(f"  {d['date']}  {d['count']:>6,}  {bar}")
        self.txt.setPlainText("\n".join(lines))
    def apply_theme(self, t):
        from PySide6.QtGui import QPalette
        pal = self.palette(); pal.setColor(QPalette.Window, QColor(t["bg"])); self.setPalette(pal); self.setAutoFillBackground(True)

class SettingsPage(QWidget):
    theme_changed=Signal(str); settings_changed=Signal(dict)
    def __init__(self, settings, p=None):
        super().__init__(p); self.settings=settings; self._section_labels=[]; self._cards=[]; self._build()
    def _card(self, ml, title):
        c=QFrame(); c.setFrameShape(QFrame.StyledPanel); c.setObjectName("settings_card"); self._cards.append(c)
        cl=QVBoxLayout(c); cl.setContentsMargins(20,16,20,16); cl.setSpacing(12)
        lb=QLabel(title.upper()); lb.setFont(QFont(FONT,9,QFont.Bold)); lb.setObjectName("card_section_title"); self._section_labels.append(lb); cl.addWidget(lb); ml.addWidget(c); return cl
    def _srow(self, pl, label, w):
        r=QWidget(); r.setObjectName("setting_row"); rl=QHBoxLayout(r); rl.setContentsMargins(0,4,0,4)
        lb=QLabel(label); lb.setFont(QFont(FONT,11,QFont.DemiBold)); rl.addWidget(lb); rl.addStretch(); rl.addWidget(w); pl.addWidget(r); return lb
    def _build(self):
        sc=QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame)
        c=QWidget(); c.setObjectName("settings_content"); ml=QVBoxLayout(c); ml.setContentsMargins(32,24,32,24); ml.setSpacing(16)
        self.title_label=QLabel(tr("settings_title")); self.title_label.setFont(QFont(FONT,24,QFont.ExtraBold)); ml.addWidget(self.title_label)
        self.desc_label=QLabel(tr("settings_desc")); self.desc_label.setFont(QFont(FONT,11)); ml.addWidget(self.desc_label); ml.addSpacing(4)
        cl=self._card(ml,"APPEARANCE")
        self.theme_combo=QComboBox(); self.theme_combo.addItems(["Light","Dark","Turquoise","Purple","System"])
        ct=self.settings.get("theme","dark"); self.theme_combo.setCurrentText(ct.capitalize()); self.theme_combo.setFont(QFont(FONT,10))
        self.theme_combo.setFixedWidth(160); self.theme_combo.setFixedHeight(34)
        self.theme_combo.currentTextChanged.connect(lambda t:self.theme_changed.emit(detect_system_theme() if t.lower()=="system" else t.lower()))
        self._srow(cl,tr("theme"),self.theme_combo)
        fw=QWidget(); fwl=QHBoxLayout(fw); fwl.setContentsMargins(0,0,0,0); fwl.setSpacing(8)
        self.font_slider=QSlider(Qt.Horizontal); self.font_slider.setRange(10,18); self.font_slider.setValue(self.settings.get("font_size",13)); self.font_slider.setFixedWidth(140)
        self.font_val=QLabel(str(self.font_slider.value())); self.font_val.setFont(QFont(FONT,12,QFont.Bold)); self.font_val.setFixedWidth(28)
        self.font_slider.valueChanged.connect(lambda v:self.font_val.setText(str(v))); fwl.addWidget(self.font_slider); fwl.addWidget(self.font_val)
        self._srow(cl,tr("font_size"),fw)
        cl2=self._card(ml,"SEARCH BEHAVIOR")
        self.mr_combo=QComboBox(); self.mr_combo.addItems(["50","100","200","500","1000"]); self.mr_combo.setCurrentText(str(self.settings.get("max_results",200)))
        self.mr_combo.setFont(QFont(FONT,10)); self.mr_combo.setFixedWidth(160); self.mr_combo.setFixedHeight(34); self._srow(cl2,tr("max_results"),self.mr_combo)
        self.sc_cb=QCheckBox(tr("open_single_click")); self.sc_cb.setFont(QFont(FONT,11)); self.sc_cb.setChecked(self.settings.get("open_on_single_click",False)); cl2.addWidget(self.sc_cb)
        cl3=self._card(ml,"INDEXING")
        self.ai_cb=QCheckBox(tr("auto_reindex")); self.ai_cb.setFont(QFont(FONT,11)); self.ai_cb.setChecked(self.settings.get("auto_index",True)); cl3.addWidget(self.ai_cb)
        self.sh_cb=QCheckBox(tr("index_hidden")); self.sh_cb.setFont(QFont(FONT,11)); self.sh_cb.setChecked(self.settings.get("show_hidden",False)); cl3.addWidget(self.sh_cb)
        self.mt_cb=QCheckBox("Minimize to tray on close"); self.mt_cb.setFont(QFont(FONT,11)); self.mt_cb.setChecked(self.settings.get("minimize_to_tray",True)); cl3.addWidget(self.mt_cb)
        cl4=self._card(ml,"LANGUAGE")
        self.lang_combo=QComboBox(); self.lang_combo.addItems(["English","Turkish","German","French","Spanish","Portuguese","Italian","Japanese","Chinese","Korean","Russian","Arabic"]); self.lang_combo.setCurrentText(self.settings.get("language","English"))
        self.lang_combo.setFont(QFont(FONT,10)); self.lang_combo.setFixedWidth(160); self.lang_combo.setFixedHeight(34); self._srow(cl4,tr("lang_label"),self.lang_combo)
        ml.addSpacing(8)
        self.save_btn=QPushButton(tr("save_settings")); self.save_btn.setFont(QFont(FONT,11,QFont.Bold)); self.save_btn.setFixedHeight(44); self.save_btn.setFixedWidth(200)
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor)); self.save_btn.setObjectName("save_settings_btn"); self.save_btn.clicked.connect(self._save); ml.addWidget(self.save_btn)
        ml.addStretch(); sc.setWidget(c); self._scroll=sc; self._content=c
        outer=QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(sc)
    def apply_theme(self, t):
        from PySide6.QtGui import QPalette
        bg = QColor(t["bg"])
        for w in [self._scroll, self._content]:
            pal = w.palette(); pal.setColor(QPalette.Window, bg); w.setPalette(pal); w.setAutoFillBackground(True)
        if self._scroll.viewport():
            vp = self._scroll.viewport().palette(); vp.setColor(QPalette.Window, bg)
            self._scroll.viewport().setPalette(vp); self._scroll.viewport().setAutoFillBackground(True)
        self._scroll.setStyleSheet("border: none;")
    def retranslate(self): self.title_label.setText(tr("settings_title")); self.save_btn.setText(tr("save_settings"))
    def _save(self):
        th=self.theme_combo.currentText().lower()
        if th=="system": th=detect_system_theme()
        self.settings.update({"theme":th,"font_size":self.font_slider.value(),"max_results":int(self.mr_combo.currentText()),
            "open_on_single_click":self.sc_cb.isChecked(),"auto_index":self.ai_cb.isChecked(),"show_hidden":self.sh_cb.isChecked(),
            "minimize_to_tray":self.mt_cb.isChecked(),"language":self.lang_combo.currentText()})
        save_settings(self.settings); self.settings_changed.emit(self.settings)

# ── Main Window ──
class QuickFindWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings=load_settings(); set_language(self.settings.get("language","English"))
        tn=self.settings.get("theme","dark")
        if tn=="system": tn=detect_system_theme()
        self.is_dark=tn=="dark"; self.T=THEMES.get(tn,THEMES["dark"])
        self._indexer_thread=None; self._file_watcher=None; self._tray=None
        from database import FileDatabase, DB_DIR
        self.db=FileDatabase()
        from quickfind.user_data import UserDataManager
        self.ud=UserDataManager(DB_DIR)
        self.setWindowTitle("QuickFind"); self.setMinimumSize(900,600); self.resize(1100,740)
        ico=os.path.join(SCRIPT_DIR,"quickfind.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))
        self._build_ui(); self._apply_theme(); self._apply_win_effects(); self._start_indexing(); self._start_watcher(); self._setup_tray(); self._setup_hotkey()
    def _get_theme(self): return self.T
    def _build_ui(self):
        central=QWidget(); self.setCentralWidget(central); root=QHBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.sidebar=Sidebar(); self.sidebar.page_changed.connect(self._switch_page); root.addWidget(self.sidebar)
        ma=QWidget(); ml=QVBoxLayout(ma); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)
        self.header=QWidget(); self.header.setFixedHeight(44); self.header.setObjectName("header")
        hl=QHBoxLayout(self.header); hl.setContentsMargins(20,0,16,0)
        self.page_title=QLabel("Search"); self.page_title.setFont(QFont(FONT,10,QFont.DemiBold)); self.page_title.setObjectName("page_title")
        self.status_hint=QLabel(""); self.status_hint.setFont(QFont(FONT,9)); self.status_hint.setObjectName("status_hint")
        hl.addWidget(self.page_title); hl.addSpacing(16); hl.addWidget(self.status_hint); hl.addStretch(); ml.addWidget(self.header)
        self.stack=QStackedWidget()
        self.search_page=SearchPage(self.db,self._get_theme,self.ud)
        self.index_page=IndexStatusPage(self.db,self._get_theme)
        self.duplicates_page=DuplicatesPage(self.db,self._get_theme)
        self.disk_usage_page=DiskUsagePage(self.db,self._get_theme)
        self.stats_page=StatisticsPage(self.db,self._get_theme)
        self.settings_page=SettingsPage(self.settings)
        self.index_page.reindex_requested.connect(self._reindex)
        self.settings_page.theme_changed.connect(self._on_theme_change)
        self.settings_page.settings_changed.connect(self._on_settings_change)
        for w in [self.search_page,self.index_page,self.duplicates_page,self.disk_usage_page,self.stats_page,self.settings_page]: self.stack.addWidget(w)
        ml.addWidget(self.stack)
        self.status_bar=QStatusBar(); self.status_bar.setFont(QFont(FONT,9)); self.status_bar.setFixedHeight(28); self.setStatusBar(self.status_bar)
        self.status_label=QLabel(tr("initializing")); self.idx_count_label=QLabel(""); self.phase_indicator=QLabel(""); self.phase_indicator.setFont(QFont(FONT,8))
        self.status_bar.addWidget(self.status_label,1); self.status_bar.addPermanentWidget(self.phase_indicator); self.status_bar.addPermanentWidget(self.idx_count_label)
        root.addWidget(ma,1)
        QShortcut(QKeySequence("Escape"),self,self._clear_search); QShortcut(QKeySequence("Ctrl+R"),self,self._reindex)
        QShortcut(QKeySequence("Ctrl+L"),self,self._focus_search); QShortcut(QKeySequence("Ctrl+F"),self,self._toggle_sub_filter)
        QShortcut(QKeySequence("Ctrl+T"),self,lambda:self.search_page._add_tab())
        QShortcut(QKeySequence("Ctrl+W"),self,lambda:self.search_page._close_tab(self.search_page.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+P"),self,self._show_command_palette); QShortcut(QKeySequence("Ctrl+H"),self,self._show_history)
        for i in range(6): QShortcut(QKeySequence(f"Ctrl+{i+1}"),self,lambda idx=i:self._switch_page(idx))
    def _switch_page(self, idx):
        if idx<self.stack.count():
            self.stack.setCurrentIndex(idx); titles=[tr("search"),tr("index_status"),tr("duplicates"),tr("disk_usage"),tr("statistics"),tr("settings")]
            self.page_title.setText(titles[idx] if idx<len(titles) else "")
            if idx==1: self.index_page.refresh()
            for i,b in enumerate(self.sidebar._buttons): b.setChecked(i==idx)
    def _apply_theme(self):
        t=self.T
        self.setStyleSheet(f"""
            QMainWindow{{background:{t["bg"]};}}
            Sidebar{{background:{t["scl"]};border-right:1px solid {t["divider"]};}}
            Sidebar QLabel{{color:{t["on_s"]};background:transparent;}}
            Sidebar #sidebar_sub{{color:{t["on_sv"]};}}
            Sidebar QPushButton{{background:transparent;color:{t["on_sv"]};border:none;border-radius:8px;padding:4px 12px;text-align:left;}}
            Sidebar QPushButton:checked{{background:{t["white"]};color:{t["primary"]};font-weight:700;}}
            Sidebar QPushButton:hover:!checked{{background:{t["sch"]};}}
            #header{{background:{t["bg"]};border-bottom:1px solid {t["divider"]};}}
            #page_title{{color:{t["primary"]};background:transparent;}}
            #status_hint{{color:{t["on_sv"]};background:transparent;}}
            #search_input{{background:{t["sch"]};color:{t["on_s"]};border:2px solid transparent;border-radius:14px;padding:6px 20px;}}
            #search_input:focus{{border-color:{t["primary"]};}}
            #sub_filter{{background:{t["sch"]};color:{t["on_s"]};border:1px solid {t["ov"]};border-radius:8px;padding:4px 12px;}}
            QPushButton[checkable="true"]{{background:{t["white"]};color:{t["on_sv"]};border:1px solid {t["ov"]};border-radius:14px;padding:2px 12px;}}
            QPushButton[checkable="true"]:checked{{background:{t["primary"]};color:{t["on_primary"]};border-color:{t["primary"]};}}
            QPushButton[checkable="true"]:hover:!checked{{background:{t["card_hover"]};}}
            QListView{{background:transparent;border:none;outline:none;}}
            QListView::item{{border:none;padding:0;}}
            QListView::item:selected,QListView::item:hover{{background:transparent;}}
            #detail_pane{{background:{t["scl"]};border-left:1px solid {t["divider"]};}}
            #preview_frame{{background:{t["sch"]};border-radius:12px;}}
            #preview_icon{{color:{t["on_sv"]};background:transparent;}}
            #preview_text{{color:{t["on_sv"]};background:transparent;}}
            #d_type{{color:{t["primary"]};}}
            #info_label{{color:{t["on_sv"]};}}
            #open_btn{{background:{t["primary"]};color:{t["on_primary"]};border:none;border-radius:10px;}}
            #open_btn:hover{{background:{_darken(t["primary"],15)};}}
            #folder_btn{{background:{t["sec_c"]};color:{t["on_s"]};border:none;border-radius:10px;}}
            #folder_btn:hover{{background:{_darken(t["sec_c"],15)};}}
            #copy_btn{{background:transparent;color:{t["primary"]};border:none;}}
            #copy_btn:hover{{background:{t["pc"]};border-radius:8px;}}
            #primary_btn{{background:{t["primary"]};color:{t["on_primary"]};border:none;border-radius:10px;padding:4px 20px;}}
            #primary_btn:hover{{background:{_darken(t["primary"])};}}
            #card{{background:{t["white"]};border:1px solid {t["divider"]};border-radius:14px;}}
            #stat_box{{background:{t["scl"]};border-radius:8px;}}
            #stat_label{{color:{t["on_sv"]};background:transparent;}}
            #stat_value{{color:{t["primary"]};background:transparent;}}
            #progress_badge{{background:{t["pc"]};color:{t["opc"]};border-radius:10px;padding:3px 10px;}}
            QProgressBar{{background:{t["pc"]};border:none;border-radius:5px;}}
            QProgressBar::chunk{{background:{t["primary"]};border-radius:5px;}}
            #page_desc{{color:{t["on_sv"]};background:transparent;}}
            #result_count{{color:{t["primary"]};background:transparent;}}
            #search_time{{color:{t["on_sv"]};background:transparent;}}
            #empty_sub{{color:{t["on_sv"]};}}
            QRadioButton{{color:{t["on_s"]};spacing:8px;padding:8px 12px;background:{t["sc"]};border:1px solid {t["ov"]};border-radius:10px;}}
            QRadioButton:checked{{border-color:{t["primary"]};background:{t["pc"]};}}
            QRadioButton::indicator{{width:14px;height:14px;border-radius:7px;border:2px solid {t["ov"]};background:transparent;}}
            QRadioButton::indicator:checked{{border-color:{t["primary"]};background:{t["primary"]};}}
            QLabel{{color:{t["on_s"]};background:transparent;}}
            QScrollArea{{background:{t["bg"]};border:none;}}
            QScrollBar:vertical{{background:transparent;width:6px;margin:4px 1px;border:none;}}
            QScrollBar::handle:vertical{{background:{t["sb"]};min-height:30px;border-radius:3px;}}
            QScrollBar::handle:vertical:hover{{background:{t["sb_h"]};}}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
            QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{{background:transparent;}}
            QStatusBar{{background:{t["bg"]};color:{t["on_sv"]};border-top:1px solid {t["divider"]};}}
            QComboBox{{background:{t["white"]};color:{t["on_s"]};border:1px solid {t["ov"]};border-radius:8px;padding:4px 10px;}}
            QComboBox::drop-down{{border:none;}}
            QComboBox QAbstractItemView{{background:{t["white"]};color:{t["on_s"]};selection-background-color:{t["pc"]};border:1px solid {t["ov"]};}}
            QCheckBox{{color:{t["on_s"]};spacing:8px;}}
            QCheckBox::indicator{{width:18px;height:18px;border:2px solid {t["ov"]};border-radius:4px;background:transparent;}}
            QCheckBox::indicator:checked{{background:{t["primary"]};border-color:{t["primary"]};}}
            QSlider::groove:horizontal{{background:{t["pc"]};height:6px;border-radius:3px;}}
            QSlider::handle:horizontal{{background:{t["primary"]};width:18px;height:18px;margin:-6px 0;border-radius:9px;border:3px solid {t["white"]};}}
            QTabWidget::pane{{border:none;}}
            QTabBar::tab{{background:{t["sc"]};color:{t["on_sv"]};border:none;padding:6px 16px;border-radius:8px 8px 0 0;margin-right:2px;}}
            QTabBar::tab:selected{{background:{t["bg"]};color:{t["primary"]};font-weight:bold;}}
            QTabBar::tab:hover:!selected{{background:{t["sch"]};}}
            QTextEdit{{background:{t["white"]};color:{t["on_s"]};border:1px solid {t["divider"]};border-radius:8px;padding:8px;}}
            QFrame#settings_card{{background:{t["white"]};border:1px solid {t["divider"]};border-radius:14px;}}
            QLabel#card_section_title{{color:{t["primary"]};background:transparent;}}
            QPushButton#save_settings_btn{{background:{t["primary"]};color:{t["on_primary"]};border:none;border-radius:12px;}}
            QPushButton#save_settings_btn:hover{{background:{_darken(t["primary"])};}}
        """)
        # Apply theme to individual pages (scroll areas need palette override)
        for page in [self.index_page, self.duplicates_page, self.disk_usage_page, self.stats_page, self.settings_page]:
            page.apply_theme(t)
    def _on_theme_change(self, tn):
        self.is_dark=tn=="dark"; self.T=THEMES.get(tn,THEMES["dark"]); self._apply_theme(); self._apply_win_effects()
    def _on_settings_change(self, s):
        self.settings=s; set_language(s.get("language","English")); self.search_page.max_results=s.get("max_results",200)
        # Update sidebar labels
        icons=["\U0001F50D","\U0001F4CA","\U0001F4CB","\U0001F4C1","\U0001F4C8","\u2699\uFE0F"]
        pages=[tr("search"),tr("index_status"),tr("duplicates"),tr("disk_usage"),tr("statistics"),tr("settings")]
        for i,btn in enumerate(self.sidebar._buttons):
            if i<len(pages): btn.setText(f"{icons[i]}  {pages[i]}")
        # Update page titles
        titles=[tr("search"),tr("index_status"),tr("duplicates"),tr("disk_usage"),tr("statistics"),tr("settings")]
        ci=self.stack.currentIndex()
        if ci<len(titles): self.page_title.setText(titles[ci])
        self.index_page.retranslate(); self.settings_page.retranslate()
    def _apply_win_effects(self):
        try:
            hwnd=int(self.winId()); v=ctypes.c_int(1 if self.is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd,20,ctypes.byref(v),4)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd,38,ctypes.byref(ctypes.c_int(2)),4)
        except: pass
    def _clear_search(self):
        t=self.search_page.current_tab
        if t: t.search_input.clear(); t.search_input.setFocus(); t.model.clear(); t.list_view.hide(); t.empty.show()
    def _focus_search(self):
        self._switch_page(0); t=self.search_page.current_tab
        if t: t.search_input.setFocus(); t.search_input.selectAll()
    def _toggle_sub_filter(self):
        t=self.search_page.current_tab
        if t: t.toggle_sub_filter()
    def _show_command_palette(self):
        from quickfind.command_palette import CommandPalette, Command
        cmds=[Command("Search","Focus search","Ctrl+L","nav",self._focus_search),
              Command("Reindex","Rebuild index","Ctrl+R","index",self._reindex),
              Command("New Tab","Open search tab","Ctrl+T","nav",lambda:self.search_page._add_tab()),
              Command("Duplicates","Find duplicates","Ctrl+3","nav",lambda:self._switch_page(2)),
              Command("Disk Usage","Analyze disk","Ctrl+4","nav",lambda:self._switch_page(3)),
              Command("Statistics","View stats","Ctrl+5","nav",lambda:self._switch_page(4)),
              Command("Settings","Open settings","Ctrl+6","nav",lambda:self._switch_page(5)),
              Command("Toggle Theme","Light/Dark","","ui",lambda:self._on_theme_change("light" if self.is_dark else "dark"))]
        CommandPalette(self,cmds).exec()
    def _show_history(self):
        recent=self.ud.history.get_recent(20)
        if not recent: return
        t=self.search_page.current_tab
        if not t: return
        m=QMenu(self)
        for q in recent: m.addAction(q,lambda query=q:(t.search_input.setText(query),t._do_search()))
        m.addSeparator(); m.addAction(tr("clear_history"),self.ud.history.clear); m.exec(QCursor.pos())
    def _start_indexing(self):
        n=self.db.get_file_count()
        if n>0:
            self.status_label.setText(f"{tr('ready')} \u2014 {n:,} {tr('files_indexed')}"); self.idx_count_label.setText(f"[{n:,}]")
            from database import FileWatcher as FW
            if FW.is_watcher_active(self.db): self.status_label.setText(f"{tr('ready')} \u2014 {n:,} {tr('files_indexed')} (watcher active)"); return
            lt=self.db.get_meta("last_index_time")
            if lt:
                try:
                    if (datetime.now()-datetime.fromisoformat(lt)).total_seconds()>7200: QTimer.singleShot(3000,lambda:self._run_indexer(False))
                except: pass
        else: self.status_label.setText(tr("first_indexing")); QTimer.singleShot(500,lambda:self._run_indexer(True))
    def _run_indexer(self, reindex):
        if self._indexer_thread and self._indexer_thread.isRunning(): return
        self._indexer_thread=IndexerThread(self.db,reindex)
        self._indexer_thread.progress.connect(self._on_idx_progress); self._indexer_thread.status.connect(self._on_idx_status)
        self._indexer_thread.finished_indexing.connect(self._on_idx_done); self._indexer_thread.phase_changed.connect(self._on_phase_change)
        self._indexer_thread.start()
    def _reindex(self):
        if self._indexer_thread and self._indexer_thread.isRunning(): self._indexer_thread.stop(); self.status_label.setText(tr("indexing_stopped")); return
        self._run_indexer(True)
    def _on_idx_progress(self, c): self.idx_count_label.setText(f"[{c:,}]"); self.status_hint.setText(f"{tr('indexing_status')} {c:,}"); self.index_page.stat_queue.setText(f"{c:,}")
    def _on_idx_status(self, m):
        self.status_label.setText(m); self.index_page.progress_detail.setText(m)
        if "Ready" in m or "Hazir" in m: self.status_hint.setText(""); self.index_page.progress_badge.setText("READY"); self.index_page.refresh()
    def _on_phase_change(self, phase, status):
        pn={1:tr("phase1"),2:tr("phase2"),3:tr("phase3")}.get(phase,f"Phase {phase}")
        if status=="starting": self.phase_indicator.setText(f"\u25CF {pn}"); self.index_page.phase_label.setText(pn); self.index_page.progress_badge.setText(f"PHASE {phase}"); self.index_page.progress_bar.setValue({1:0,2:33,3:66}.get(phase,0))
        elif status=="done" and phase==3: self.phase_indicator.setText(""); self.index_page.progress_bar.setValue(100)
    def _on_idx_done(self): self.index_page.progress_badge.setText("COMPLETE"); self.index_page.progress_bar.setValue(100); self.index_page.refresh(); self._start_watcher(); self.phase_indicator.setText("")
    def _start_watcher(self):
        if self._file_watcher and self._file_watcher.is_running(): return
        from database import FileWatcher
        self._file_watcher=FileWatcher(self.db,status_callback=lambda m:QTimer.singleShot(0,lambda:self.status_label.setText(m))); self._file_watcher.start()
    def _setup_tray(self):
        ico=os.path.join(SCRIPT_DIR,"quickfind.ico"); icon=QIcon(ico) if os.path.exists(ico) else QIcon()
        self._tray=QSystemTrayIcon(icon,self); self._tray.setToolTip("QuickFind")
        m=QMenu(); m.addAction("Show",self.show); m.addAction("Search",self._focus_search); m.addSeparator(); m.addAction("Quit",self._quit)
        self._tray.setContextMenu(m); self._tray.activated.connect(lambda r:self.show() if r==QSystemTrayIcon.DoubleClick else None); self._tray.show()
    def _setup_hotkey(self):
        try:
            from quickfind.hotkeys import GlobalHotkey
            self._hotkey=GlobalHotkey(self.settings.get("global_hotkey","Win+Alt+F"),lambda:QTimer.singleShot(0,self._toggle_vis)); self._hotkey.register()
        except: self._hotkey=None
    def _toggle_vis(self):
        if self.isVisible() and not self.isMinimized(): self.hide()
        else: self.show(); self.raise_(); self.activateWindow(); self._focus_search()
    def _quit(self):
        if self._file_watcher: self._file_watcher.stop()
        if self._indexer_thread and self._indexer_thread.isRunning(): self._indexer_thread.stop(); self._indexer_thread.wait(3000)
        if self._hotkey:
            try: self._hotkey.unregister()
            except: pass
        self.db.close()
        if self._tray: self._tray.hide()
        QApplication.quit()
    def closeEvent(self, e):
        if self.settings.get("minimize_to_tray",True) and self._tray: e.ignore(); self.hide(); self._tray.showMessage("QuickFind","Running in tray",QSystemTrayIcon.Information,2000)
        else: self._quit(); e.accept()

def main():
    app=QApplication(sys.argv); app.setStyle("Fusion"); app.setQuitOnLastWindowClosed(False)
    ico=os.path.join(SCRIPT_DIR,"quickfind.ico")
    if os.path.exists(ico): app.setWindowIcon(QIcon(ico))
    w=QuickFindWindow(); w.show(); sys.exit(app.exec())

if __name__=="__main__":
    main()
