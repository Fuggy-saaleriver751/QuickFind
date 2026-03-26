"""
QuickFind — Ultra-Fast File Search
PySide6 · Material Design 3 · FTS5 Content Search
Supports: PDF, DOCX, XLSX, PPTX, RTF, EPUB + 35 plain-text formats
"""

import sys, os, subprocess, time, ctypes, json
from datetime import datetime

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("dgknk.QuickFind.1")

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QListView, QPushButton, QStatusBar,
    QStyledItemDelegate, QStyle, QFrame, QGraphicsDropShadowEffect,
    QDialog, QRadioButton, QButtonGroup, QMessageBox, QSplitter,
    QProgressBar, QSlider, QScrollArea, QGridLayout, QStackedWidget,
    QSizePolicy, QComboBox, QCheckBox
)
from PySide6.QtCore import (
    Qt, QSize, QRect, QThread, Signal, QModelIndex, QObject,
    QAbstractListModel, QTimer, QRectF, QPointF
)
from PySide6.QtGui import (
    QColor, QPainter, QFont, QFontMetrics, QPen, QBrush,
    QIcon, QPainterPath, QLinearGradient, QPixmap, QCursor,
    QRadialGradient, QShortcut, QKeySequence
)

import sys as _sys
if getattr(_sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(_sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

FONT = "Segoe UI"
FONT_MONO = "Consolas"

# ══════════════════════════════════════════════════════════════
#  THEMES
# ══════════════════════════════════════════════════════════════

THEMES = {
    "light": {
        "bg":         "#fcf8f9",  "surface":    "#fcf8f9",
        "sc":         "#f0edef",  "scl":        "#f6f3f4",
        "sch":        "#eae7ea",  "white":      "#ffffff",
        "primary":    "#0054d6",  "pc":         "#dae1ff",
        "opc":        "#0049bb",  "on_primary": "#ffffff",
        "secondary":  "#5f5f5f",  "sec_c":      "#e4e2e6",
        "on_s":       "#323235",  "on_sv":      "#5f5f61",
        "outline":    "#7b7a7d",  "ov":         "#b3b1b4",
        "divider":    "#e4e2e5",  "error":      "#9f403d",
        "sb":         "#b3b1b4",  "sb_h":       "#7b7a7d",
        "card_hover": "#f6f3f4",  "card_sel":   "#dae1ff",
    },
    "dark": {
        "bg":         "#111318",  "surface":    "#111318",
        "sc":         "#1d1f25",  "scl":        "#191b21",
        "sch":        "#272a30",  "white":      "#2a2d33",
        "primary":    "#a8c8ff",  "pc":         "#003068",
        "opc":        "#d6e3ff",  "on_primary": "#002552",
        "secondary":  "#c6c6ca",  "sec_c":      "#444548",
        "on_s":       "#e3e2e6",  "on_sv":      "#c4c6cf",
        "outline":    "#8e9099",  "ov":         "#44464f",
        "divider":    "#44464f",  "error":      "#ffb4ab",
        "sb":         "#44464f",  "sb_h":       "#8e9099",
        "card_hover": "#272a30",  "card_sel":   "#003068",
    },
    "turquoise": {
        "bg": "#f0fafa", "surface": "#f0fafa",
        "sc": "#e0f0f0", "scl": "#e8f5f5",
        "sch": "#d4ebeb", "white": "#ffffff",
        "primary": "#00897b", "pc": "#b2dfdb",
        "opc": "#00695c", "on_primary": "#ffffff",
        "secondary": "#5f6368", "sec_c": "#e0e0e0",
        "on_s": "#263238", "on_sv": "#546e7a",
        "outline": "#78909c", "ov": "#b0bec5",
        "divider": "#cfd8dc", "error": "#c62828",
        "sb": "#b0bec5", "sb_h": "#78909c",
        "card_hover": "#e0f2f1", "card_sel": "#b2dfdb",
    },
    "purple": {
        "bg": "#faf5ff", "surface": "#faf5ff",
        "sc": "#f3e5f5", "scl": "#f5eef8",
        "sch": "#e8d5f0", "white": "#ffffff",
        "primary": "#7b1fa2", "pc": "#e1bee7",
        "opc": "#6a1b9a", "on_primary": "#ffffff",
        "secondary": "#5f6368", "sec_c": "#e0e0e0",
        "on_s": "#311b40", "on_sv": "#6d5080",
        "outline": "#9575cd", "ov": "#ce93d8",
        "divider": "#e1bee7", "error": "#c62828",
        "sb": "#ce93d8", "sb_h": "#9575cd",
        "card_hover": "#f3e5f5", "card_sel": "#e1bee7",
    },
}

def T(theme, key):
    return theme[key]

def _darken(hex_color, amount=30):
    """Darken a hex color by reducing RGB values."""
    c = hex_color.lstrip('#')
    r, g, b = int(c[:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    r = max(0, r - amount)
    g = max(0, g - amount)
    b = max(0, b - amount)
    return f"#{r:02x}{g:02x}{b:02x}"


EXT_ICONS = {
    ".pdf": "PDF", ".docx": "DOC", ".doc": "DOC", ".rtf": "RTF",
    ".txt": "TXT", ".md": "MD", ".epub": "EPB",
    ".xlsx": "XLS", ".xls": "XLS", ".csv": "CSV",
    ".pptx": "PPT", ".ppt": "PPT",
    ".py": "PY", ".js": "JS", ".ts": "TS", ".html": "HTM", ".css": "CSS",
    ".java": "JAV", ".cpp": "C++", ".c": "C", ".cs": "C#",
    ".go": "GO", ".rs": "RS", ".json": "JSN", ".xml": "XML",
    ".jpg": "JPG", ".jpeg": "JPG", ".png": "PNG", ".gif": "GIF", ".svg": "SVG",
    ".mp4": "MP4", ".mp3": "MP3", ".zip": "ZIP", ".rar": "RAR",
    ".exe": "EXE", ".sql": "SQL",
}

EXT_CATEGORY = {
    "doc":   {".pdf", ".docx", ".doc", ".rtf", ".txt", ".md", ".epub", ".rst"},
    "data":  {".xlsx", ".xls", ".csv", ".json", ".xml", ".yaml", ".yml", ".toml", ".sql"},
    "code":  {".py", ".pyw", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".java", ".cpp",
              ".c", ".cs", ".go", ".rs", ".rb", ".php", ".sh", ".bat", ".ps1"},
    "media": {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".mp4", ".mp3", ".wav"},
    "arch":  {".zip", ".rar", ".7z", ".tar", ".gz", ".exe", ".msi"},
}

TYPE_NAMES = {
    ".pdf": "Portable Document Format", ".docx": "Word Document",
    ".xlsx": "Excel Spreadsheet", ".pptx": "PowerPoint Presentation",
    ".txt": "Plain Text", ".md": "Markdown", ".csv": "Comma-Separated Values",
    ".py": "Python Script", ".js": "JavaScript", ".ts": "TypeScript",
    ".html": "HTML Document", ".css": "Stylesheet", ".json": "JSON Data",
    ".jpg": "JPEG Image", ".png": "PNG Image", ".svg": "SVG Vector",
    ".mp4": "MP4 Video", ".mp3": "MP3 Audio", ".zip": "ZIP Archive",
    ".exe": "Executable", ".rtf": "Rich Text", ".epub": "E-Book",
}


# ══════════════════════════════════════════════════════════════
#  TRANSLATIONS
# ══════════════════════════════════════════════════════════════

TRANSLATIONS = {
    "English": {
        "search": "Search", "index_status": "Index Status", "settings": "Settings",
        "desktop_search": "Desktop Search",
        "search_placeholder": "Search for files, code, or documents...",
        "all": "All", "documents": "Documents", "images": "Images",
        "code": "Code", "archives": "Archives", "pdfs": "PDFs",
        "relevance": "Relevance", "name": "Name", "size": "Size", "newest": "Newest",
        "ready_to_search": "Ready to Search",
        "type_query": "Type a query and press Enter",
        "no_results": "No Results", "try_different": "Try a different search term",
        "results": "results", "select_file": "Select a file",
        "no_preview": "No preview available for",
        "open_file": "Open File", "show_folder": "Show in Folder",
        "copy_path": "Copy File Path",
        "index_title": "Index Status",
        "index_desc": "Monitor your search database and manage file indexing.",
        "rebuild_index": "Rebuild Index", "current_progress": "Current Progress",
        "db_stats": "Database Stats", "db_size": "Database Size",
        "last_indexed": "Last Indexed", "search_latency": "Search Latency",
        "speed": "SPEED", "duration": "DURATION", "files": "FILES",
        "content_depth": "Content Indexing Depth",
        "save_reindex": "Save & Reindex",
        "file_type_support": "File Type Support",
        "settings_title": "Settings",
        "settings_desc": "Customize QuickFind appearance and behavior.",
        "appearance": "APPEARANCE", "theme": "Theme", "font_size": "Font Size",
        "search_behavior": "SEARCH BEHAVIOR", "max_results": "Max Results",
        "open_single_click": "Open file on single click",
        "indexing": "INDEXING",
        "auto_reindex": "Auto-reindex when files change (file watcher)",
        "index_hidden": "Index hidden files and folders",
        "language": "LANGUAGE", "lang_label": "Language",
        "save_settings": "Save Settings",
        "initializing": "Initializing...",
        "ready": "Ready", "files_indexed": "files indexed",
        "first_indexing": "First indexing starting...",
        "indexing_status": "Indexing...", "indexing_stopped": "Indexing stopped",
    },
    "Turkish": {
        "search": "Ara", "index_status": "Dizin Durumu", "settings": "Ayarlar",
        "desktop_search": "Masaustu Arama",
        "search_placeholder": "Dosya, kod veya belge ara...",
        "all": "Tumunu", "documents": "Belgeler", "images": "Gorseller",
        "code": "Kod", "archives": "Arsivler", "pdfs": "PDF'ler",
        "relevance": "Ilgi", "name": "Ad", "size": "Boyut", "newest": "En Yeni",
        "ready_to_search": "Aramaya Hazir",
        "type_query": "Sorgu yazin ve Enter'a basin",
        "no_results": "Sonuc Yok", "try_different": "Farkli bir arama deneyin",
        "results": "sonuc", "select_file": "Dosya secin",
        "no_preview": "On izleme yok:",
        "open_file": "Dosyayi Ac", "show_folder": "Klasorde Goster",
        "copy_path": "Yolu Kopyala",
        "index_title": "Dizin Durumu",
        "index_desc": "Arama veritabaninizi izleyin ve dizinlemeyi yonetin.",
        "rebuild_index": "Yeniden Dizinle", "current_progress": "Mevcut Ilerleme",
        "db_stats": "Veritabani Istatistikleri", "db_size": "Veritabani Boyutu",
        "last_indexed": "Son Dizinleme", "search_latency": "Arama Gecikmesi",
        "speed": "HIZ", "duration": "SURE", "files": "DOSYA",
        "content_depth": "Icerik Dizinleme Derinligi",
        "save_reindex": "Kaydet ve Yeniden Dizinle",
        "file_type_support": "Dosya Turu Destegi",
        "settings_title": "Ayarlar",
        "settings_desc": "QuickFind gorunumunu ve davranisini ozellestirin.",
        "appearance": "GORUNUM", "theme": "Tema", "font_size": "Yazi Boyutu",
        "search_behavior": "ARAMA DAVRANISI", "max_results": "Maks Sonuc",
        "open_single_click": "Tek tikla dosya ac",
        "indexing": "DIZINLEME",
        "auto_reindex": "Dosya degistiginde otomatik yeniden dizinle",
        "index_hidden": "Gizli dosya ve klasorleri dizinle",
        "language": "DIL", "lang_label": "Dil",
        "save_settings": "Ayarlari Kaydet",
        "initializing": "Baslatiliyor...",
        "ready": "Hazir", "files_indexed": "dosya dizinlendi",
        "first_indexing": "Ilk dizinleme basliyor...",
        "indexing_status": "Dizinleniyor...", "indexing_stopped": "Dizinleme durduruldu",
    },
    "German": {
        "search": "Suche", "index_status": "Indexstatus", "settings": "Einstellungen",
        "desktop_search": "Desktop-Suche",
        "search_placeholder": "Dateien, Code oder Dokumente suchen...",
        "all": "Alle", "documents": "Dokumente", "images": "Bilder",
        "code": "Code", "archives": "Archive", "pdfs": "PDFs",
        "relevance": "Relevanz", "name": "Name", "size": "Groesse", "newest": "Neueste",
        "ready_to_search": "Bereit zur Suche",
        "type_query": "Suchbegriff eingeben und Enter druecken",
        "no_results": "Keine Ergebnisse", "try_different": "Versuchen Sie einen anderen Suchbegriff",
        "results": "Ergebnisse", "select_file": "Datei auswaehlen",
        "no_preview": "Keine Vorschau verfuegbar fuer",
        "open_file": "Datei oeffnen", "show_folder": "Im Ordner anzeigen",
        "copy_path": "Dateipfad kopieren",
        "index_title": "Indexstatus",
        "index_desc": "Ueberwachen Sie Ihre Suchdatenbank und verwalten Sie die Dateiindizierung.",
        "rebuild_index": "Index neu erstellen", "current_progress": "Aktueller Fortschritt",
        "db_stats": "Datenbankstatistiken", "db_size": "Datenbankgroesse",
        "last_indexed": "Zuletzt indiziert", "search_latency": "Suchlatenz",
        "speed": "GESCHW.", "duration": "DAUER", "files": "DATEIEN",
        "content_depth": "Inhaltsindizierungstiefe",
        "save_reindex": "Speichern & Neu indizieren",
        "file_type_support": "Dateitypunterstuetzung",
        "settings_title": "Einstellungen",
        "settings_desc": "QuickFind-Erscheinungsbild und -Verhalten anpassen.",
        "appearance": "ERSCHEINUNGSBILD", "theme": "Design", "font_size": "Schriftgroesse",
        "search_behavior": "SUCHVERHALTEN", "max_results": "Max. Ergebnisse",
        "open_single_click": "Datei mit Einzelklick oeffnen",
        "indexing": "INDIZIERUNG",
        "auto_reindex": "Automatisch neu indizieren bei Dateimaenderungen",
        "index_hidden": "Versteckte Dateien und Ordner indizieren",
        "language": "SPRACHE", "lang_label": "Sprache",
        "save_settings": "Einstellungen speichern",
        "initializing": "Initialisierung...",
        "ready": "Bereit", "files_indexed": "Dateien indiziert",
        "first_indexing": "Erste Indizierung startet...",
        "indexing_status": "Indizierung...", "indexing_stopped": "Indizierung gestoppt",
    },
    "French": {
        "search": "Recherche", "index_status": "Etat de l'index", "settings": "Parametres",
        "desktop_search": "Recherche Bureau",
        "search_placeholder": "Rechercher des fichiers, du code ou des documents...",
        "all": "Tout", "documents": "Documents", "images": "Images",
        "code": "Code", "archives": "Archives", "pdfs": "PDFs",
        "relevance": "Pertinence", "name": "Nom", "size": "Taille", "newest": "Recent",
        "ready_to_search": "Pret a chercher",
        "type_query": "Saisissez une requete et appuyez sur Entree",
        "no_results": "Aucun resultat", "try_different": "Essayez un autre terme de recherche",
        "results": "resultats", "select_file": "Selectionnez un fichier",
        "no_preview": "Aucun apercu disponible pour",
        "open_file": "Ouvrir le fichier", "show_folder": "Afficher dans le dossier",
        "copy_path": "Copier le chemin",
        "index_title": "Etat de l'index",
        "index_desc": "Surveillez votre base de donnees et gerez l'indexation des fichiers.",
        "rebuild_index": "Reconstruire l'index", "current_progress": "Progression actuelle",
        "db_stats": "Statistiques de la base", "db_size": "Taille de la base",
        "last_indexed": "Derniere indexation", "search_latency": "Latence de recherche",
        "speed": "VITESSE", "duration": "DUREE", "files": "FICHIERS",
        "content_depth": "Profondeur d'indexation du contenu",
        "save_reindex": "Enregistrer et Reindexer",
        "file_type_support": "Types de fichiers pris en charge",
        "settings_title": "Parametres",
        "settings_desc": "Personnalisez l'apparence et le comportement de QuickFind.",
        "appearance": "APPARENCE", "theme": "Theme", "font_size": "Taille de police",
        "search_behavior": "COMPORTEMENT DE RECHERCHE", "max_results": "Resultats max",
        "open_single_click": "Ouvrir le fichier en un clic",
        "indexing": "INDEXATION",
        "auto_reindex": "Reindexer automatiquement lors de modifications",
        "index_hidden": "Indexer les fichiers et dossiers caches",
        "language": "LANGUE", "lang_label": "Langue",
        "save_settings": "Enregistrer les parametres",
        "initializing": "Initialisation...",
        "ready": "Pret", "files_indexed": "fichiers indexes",
        "first_indexing": "Premiere indexation en cours...",
        "indexing_status": "Indexation...", "indexing_stopped": "Indexation arretee",
    },
    "Spanish": {
        "search": "Buscar", "index_status": "Estado del indice", "settings": "Configuracion",
        "desktop_search": "Busqueda de escritorio",
        "search_placeholder": "Buscar archivos, codigo o documentos...",
        "all": "Todo", "documents": "Documentos", "images": "Imagenes",
        "code": "Codigo", "archives": "Archivos", "pdfs": "PDFs",
        "relevance": "Relevancia", "name": "Nombre", "size": "Tamano", "newest": "Reciente",
        "ready_to_search": "Listo para buscar",
        "type_query": "Escriba una consulta y presione Enter",
        "no_results": "Sin resultados", "try_different": "Intente con otro termino de busqueda",
        "results": "resultados", "select_file": "Seleccione un archivo",
        "no_preview": "Vista previa no disponible para",
        "open_file": "Abrir archivo", "show_folder": "Mostrar en carpeta",
        "copy_path": "Copiar ruta",
        "index_title": "Estado del indice",
        "index_desc": "Supervise su base de datos de busqueda y gestione la indexacion.",
        "rebuild_index": "Reconstruir indice", "current_progress": "Progreso actual",
        "db_stats": "Estadisticas de la base", "db_size": "Tamano de la base",
        "last_indexed": "Ultima indexacion", "search_latency": "Latencia de busqueda",
        "speed": "VELOCIDAD", "duration": "DURACION", "files": "ARCHIVOS",
        "content_depth": "Profundidad de indexacion de contenido",
        "save_reindex": "Guardar y Reindexar",
        "file_type_support": "Tipos de archivo compatibles",
        "settings_title": "Configuracion",
        "settings_desc": "Personalice la apariencia y el comportamiento de QuickFind.",
        "appearance": "APARIENCIA", "theme": "Tema", "font_size": "Tamano de fuente",
        "search_behavior": "COMPORTAMIENTO DE BUSQUEDA", "max_results": "Resultados max",
        "open_single_click": "Abrir archivo con un solo clic",
        "indexing": "INDEXACION",
        "auto_reindex": "Reindexar automaticamente al cambiar archivos",
        "index_hidden": "Indexar archivos y carpetas ocultos",
        "language": "IDIOMA", "lang_label": "Idioma",
        "save_settings": "Guardar configuracion",
        "initializing": "Inicializando...",
        "ready": "Listo", "files_indexed": "archivos indexados",
        "first_indexing": "Primera indexacion iniciando...",
        "indexing_status": "Indexando...", "indexing_stopped": "Indexacion detenida",
    },
    "Portuguese": {
        "search": "Pesquisar", "index_status": "Estado do indice", "settings": "Configuracoes",
        "desktop_search": "Pesquisa de area de trabalho",
        "search_placeholder": "Pesquisar arquivos, codigo ou documentos...",
        "all": "Todos", "documents": "Documentos", "images": "Imagens",
        "code": "Codigo", "archives": "Arquivos", "pdfs": "PDFs",
        "relevance": "Relevancia", "name": "Nome", "size": "Tamanho", "newest": "Recente",
        "ready_to_search": "Pronto para pesquisar",
        "type_query": "Digite uma consulta e pressione Enter",
        "no_results": "Sem resultados", "try_different": "Tente um termo de pesquisa diferente",
        "results": "resultados", "select_file": "Selecione um arquivo",
        "no_preview": "Visualizacao nao disponivel para",
        "open_file": "Abrir arquivo", "show_folder": "Mostrar na pasta",
        "copy_path": "Copiar caminho",
        "index_title": "Estado do indice",
        "index_desc": "Monitore seu banco de dados de pesquisa e gerencie a indexacao.",
        "rebuild_index": "Reconstruir indice", "current_progress": "Progresso atual",
        "db_stats": "Estatisticas do banco", "db_size": "Tamanho do banco",
        "last_indexed": "Ultima indexacao", "search_latency": "Latencia de pesquisa",
        "speed": "VELOCIDADE", "duration": "DURACAO", "files": "ARQUIVOS",
        "content_depth": "Profundidade de indexacao de conteudo",
        "save_reindex": "Salvar e Reindexar",
        "file_type_support": "Tipos de arquivo suportados",
        "settings_title": "Configuracoes",
        "settings_desc": "Personalize a aparencia e o comportamento do QuickFind.",
        "appearance": "APARENCIA", "theme": "Tema", "font_size": "Tamanho da fonte",
        "search_behavior": "COMPORTAMENTO DE PESQUISA", "max_results": "Resultados max",
        "open_single_click": "Abrir arquivo com um clique",
        "indexing": "INDEXACAO",
        "auto_reindex": "Reindexar automaticamente ao alterar arquivos",
        "index_hidden": "Indexar arquivos e pastas ocultos",
        "language": "IDIOMA", "lang_label": "Idioma",
        "save_settings": "Salvar configuracoes",
        "initializing": "Inicializando...",
        "ready": "Pronto", "files_indexed": "arquivos indexados",
        "first_indexing": "Primeira indexacao iniciando...",
        "indexing_status": "Indexando...", "indexing_stopped": "Indexacao interrompida",
    },
    "Italian": {
        "search": "Cerca", "index_status": "Stato dell'indice", "settings": "Impostazioni",
        "desktop_search": "Ricerca desktop",
        "search_placeholder": "Cerca file, codice o documenti...",
        "all": "Tutto", "documents": "Documenti", "images": "Immagini",
        "code": "Codice", "archives": "Archivi", "pdfs": "PDF",
        "relevance": "Rilevanza", "name": "Nome", "size": "Dimensione", "newest": "Recente",
        "ready_to_search": "Pronto per cercare",
        "type_query": "Digita una query e premi Invio",
        "no_results": "Nessun risultato", "try_different": "Prova un termine di ricerca diverso",
        "results": "risultati", "select_file": "Seleziona un file",
        "no_preview": "Anteprima non disponibile per",
        "open_file": "Apri file", "show_folder": "Mostra nella cartella",
        "copy_path": "Copia percorso",
        "index_title": "Stato dell'indice",
        "index_desc": "Monitora il database di ricerca e gestisci l'indicizzazione dei file.",
        "rebuild_index": "Ricostruisci indice", "current_progress": "Progresso attuale",
        "db_stats": "Statistiche del database", "db_size": "Dimensione del database",
        "last_indexed": "Ultima indicizzazione", "search_latency": "Latenza di ricerca",
        "speed": "VELOCITA", "duration": "DURATA", "files": "FILE",
        "content_depth": "Profondita di indicizzazione del contenuto",
        "save_reindex": "Salva e Reindicizza",
        "file_type_support": "Tipi di file supportati",
        "settings_title": "Impostazioni",
        "settings_desc": "Personalizza l'aspetto e il comportamento di QuickFind.",
        "appearance": "ASPETTO", "theme": "Tema", "font_size": "Dimensione carattere",
        "search_behavior": "COMPORTAMENTO DI RICERCA", "max_results": "Risultati max",
        "open_single_click": "Apri file con un solo clic",
        "indexing": "INDICIZZAZIONE",
        "auto_reindex": "Reindicizza automaticamente quando i file cambiano",
        "index_hidden": "Indicizza file e cartelle nascosti",
        "language": "LINGUA", "lang_label": "Lingua",
        "save_settings": "Salva impostazioni",
        "initializing": "Inizializzazione...",
        "ready": "Pronto", "files_indexed": "file indicizzati",
        "first_indexing": "Prima indicizzazione in corso...",
        "indexing_status": "Indicizzazione...", "indexing_stopped": "Indicizzazione interrotta",
    },
    "Japanese": {
        "search": "検索", "index_status": "インデックス状態", "settings": "設定",
        "desktop_search": "デスクトップ検索",
        "search_placeholder": "ファイル、コード、ドキュメントを検索...",
        "all": "すべて", "documents": "ドキュメント", "images": "画像",
        "code": "コード", "archives": "アーカイブ", "pdfs": "PDF",
        "relevance": "関連性", "name": "名前", "size": "サイズ", "newest": "最新",
        "ready_to_search": "検索の準備完了",
        "type_query": "クエリを入力してEnterを押してください",
        "no_results": "結果なし", "try_different": "別の検索語をお試しください",
        "results": "件の結果", "select_file": "ファイルを選択",
        "no_preview": "プレビューできません:",
        "open_file": "ファイルを開く", "show_folder": "フォルダに表示",
        "copy_path": "パスをコピー",
        "index_title": "インデックス状態",
        "index_desc": "検索データベースを監視し、ファイルのインデックスを管理します。",
        "rebuild_index": "インデックスを再構築", "current_progress": "現在の進捗",
        "db_stats": "データベース統計", "db_size": "データベースサイズ",
        "last_indexed": "最終インデックス", "search_latency": "検索レイテンシ",
        "speed": "速度", "duration": "所要時間", "files": "ファイル数",
        "content_depth": "コンテンツインデックスの深さ",
        "save_reindex": "保存して再インデックス",
        "file_type_support": "対応ファイル形式",
        "settings_title": "設定",
        "settings_desc": "QuickFindの外観と動作をカスタマイズします。",
        "appearance": "外観", "theme": "テーマ", "font_size": "フォントサイズ",
        "search_behavior": "検索動作", "max_results": "最大結果数",
        "open_single_click": "シングルクリックでファイルを開く",
        "indexing": "インデックス",
        "auto_reindex": "ファイル変更時に自動再インデックス",
        "index_hidden": "隠しファイルとフォルダをインデックス",
        "language": "言語", "lang_label": "言語",
        "save_settings": "設定を保存",
        "initializing": "初期化中...",
        "ready": "準備完了", "files_indexed": "ファイルがインデックス済み",
        "first_indexing": "初回インデックスを開始...",
        "indexing_status": "インデックス中...", "indexing_stopped": "インデックス停止",
    },
    "Chinese": {
        "search": "搜索", "index_status": "索引状态", "settings": "设置",
        "desktop_search": "桌面搜索",
        "search_placeholder": "搜索文件、代码或文档...",
        "all": "全部", "documents": "文档", "images": "图片",
        "code": "代码", "archives": "归档", "pdfs": "PDF",
        "relevance": "相关性", "name": "名称", "size": "大小", "newest": "最新",
        "ready_to_search": "准备搜索",
        "type_query": "输入查询并按回车",
        "no_results": "无结果", "try_different": "请尝试其他搜索词",
        "results": "个结果", "select_file": "选择文件",
        "no_preview": "无法预览:",
        "open_file": "打开文件", "show_folder": "在文件夹中显示",
        "copy_path": "复制路径",
        "index_title": "索引状态",
        "index_desc": "监控搜索数据库并管理文件索引。",
        "rebuild_index": "重建索引", "current_progress": "当前进度",
        "db_stats": "数据库统计", "db_size": "数据库大小",
        "last_indexed": "上次索引", "search_latency": "搜索延迟",
        "speed": "速度", "duration": "耗时", "files": "文件数",
        "content_depth": "内容索引深度",
        "save_reindex": "保存并重新索引",
        "file_type_support": "支持的文件类型",
        "settings_title": "设置",
        "settings_desc": "自定义QuickFind的外观和行为。",
        "appearance": "外观", "theme": "主题", "font_size": "字体大小",
        "search_behavior": "搜索行为", "max_results": "最大结果数",
        "open_single_click": "单击打开文件",
        "indexing": "索引",
        "auto_reindex": "文件更改时自动重新索引",
        "index_hidden": "索引隐藏文件和文件夹",
        "language": "语言", "lang_label": "语言",
        "save_settings": "保存设置",
        "initializing": "初始化中...",
        "ready": "就绪", "files_indexed": "个文件已索引",
        "first_indexing": "首次索引开始...",
        "indexing_status": "索引中...", "indexing_stopped": "索引已停止",
    },
    "Korean": {
        "search": "검색", "index_status": "인덱스 상태", "settings": "설정",
        "desktop_search": "데스크톱 검색",
        "search_placeholder": "파일, 코드 또는 문서 검색...",
        "all": "전체", "documents": "문서", "images": "이미지",
        "code": "코드", "archives": "아카이브", "pdfs": "PDF",
        "relevance": "관련성", "name": "이름", "size": "크기", "newest": "최신",
        "ready_to_search": "검색 준비 완료",
        "type_query": "검색어를 입력하고 Enter를 누르세요",
        "no_results": "결과 없음", "try_different": "다른 검색어를 시도하세요",
        "results": "개 결과", "select_file": "파일 선택",
        "no_preview": "미리보기 불가:",
        "open_file": "파일 열기", "show_folder": "폴더에서 보기",
        "copy_path": "경로 복사",
        "index_title": "인덱스 상태",
        "index_desc": "검색 데이터베이스를 모니터링하고 파일 인덱싱을 관리합니다.",
        "rebuild_index": "인덱스 재구축", "current_progress": "현재 진행 상황",
        "db_stats": "데이터베이스 통계", "db_size": "데이터베이스 크기",
        "last_indexed": "마지막 인덱싱", "search_latency": "검색 지연",
        "speed": "속도", "duration": "소요 시간", "files": "파일 수",
        "content_depth": "콘텐츠 인덱싱 깊이",
        "save_reindex": "저장 후 재인덱싱",
        "file_type_support": "지원 파일 형식",
        "settings_title": "설정",
        "settings_desc": "QuickFind의 외관과 동작을 사용자 정의합니다.",
        "appearance": "외관", "theme": "테마", "font_size": "글꼴 크기",
        "search_behavior": "검색 동작", "max_results": "최대 결과 수",
        "open_single_click": "한 번 클릭으로 파일 열기",
        "indexing": "인덱싱",
        "auto_reindex": "파일 변경 시 자동 재인덱싱",
        "index_hidden": "숨긴 파일 및 폴더 인덱싱",
        "language": "언어", "lang_label": "언어",
        "save_settings": "설정 저장",
        "initializing": "초기화 중...",
        "ready": "준비 완료", "files_indexed": "개 파일 인덱싱됨",
        "first_indexing": "첫 인덱싱 시작...",
        "indexing_status": "인덱싱 중...", "indexing_stopped": "인덱싱 중지됨",
    },
    "Russian": {
        "search": "Поиск", "index_status": "Состояние индекса", "settings": "Настройки",
        "desktop_search": "Поиск на рабочем столе",
        "search_placeholder": "Поиск файлов, кода или документов...",
        "all": "Все", "documents": "Документы", "images": "Изображения",
        "code": "Код", "archives": "Архивы", "pdfs": "PDF",
        "relevance": "Релевантность", "name": "Имя", "size": "Размер", "newest": "Новые",
        "ready_to_search": "Готов к поиску",
        "type_query": "Введите запрос и нажмите Enter",
        "no_results": "Нет результатов", "try_different": "Попробуйте другой поисковый запрос",
        "results": "результатов", "select_file": "Выберите файл",
        "no_preview": "Предварительный просмотр недоступен для",
        "open_file": "Открыть файл", "show_folder": "Показать в папке",
        "copy_path": "Копировать путь",
        "index_title": "Состояние индекса",
        "index_desc": "Мониторинг базы данных поиска и управление индексацией файлов.",
        "rebuild_index": "Перестроить индекс", "current_progress": "Текущий прогресс",
        "db_stats": "Статистика базы данных", "db_size": "Размер базы данных",
        "last_indexed": "Последняя индексация", "search_latency": "Задержка поиска",
        "speed": "СКОРОСТЬ", "duration": "ДЛИТЕЛЬНОСТЬ", "files": "ФАЙЛЫ",
        "content_depth": "Глубина индексации содержимого",
        "save_reindex": "Сохранить и переиндексировать",
        "file_type_support": "Поддержка типов файлов",
        "settings_title": "Настройки",
        "settings_desc": "Настройте внешний вид и поведение QuickFind.",
        "appearance": "ВНЕШНИЙ ВИД", "theme": "Тема", "font_size": "Размер шрифта",
        "search_behavior": "ПОВЕДЕНИЕ ПОИСКА", "max_results": "Макс. результатов",
        "open_single_click": "Открывать файл одним кликом",
        "indexing": "ИНДЕКСАЦИЯ",
        "auto_reindex": "Автоматическая переиндексация при изменении файлов",
        "index_hidden": "Индексировать скрытые файлы и папки",
        "language": "ЯЗЫК", "lang_label": "Язык",
        "save_settings": "Сохранить настройки",
        "initializing": "Инициализация...",
        "ready": "Готово", "files_indexed": "файлов проиндексировано",
        "first_indexing": "Первая индексация начинается...",
        "indexing_status": "Индексация...", "indexing_stopped": "Индексация остановлена",
    },
    "Arabic": {
        "search": "بحث", "index_status": "حالة الفهرس", "settings": "الإعدادات",
        "desktop_search": "بحث سطح المكتب",
        "search_placeholder": "البحث عن ملفات أو أكواد أو مستندات...",
        "all": "الكل", "documents": "المستندات", "images": "الصور",
        "code": "الأكواد", "archives": "الأرشيف", "pdfs": "PDF",
        "relevance": "الصلة", "name": "الاسم", "size": "الحجم", "newest": "الأحدث",
        "ready_to_search": "جاهز للبحث",
        "type_query": "اكتب استعلامًا واضغط Enter",
        "no_results": "لا توجد نتائج", "try_different": "جرّب مصطلح بحث مختلف",
        "results": "نتائج", "select_file": "اختر ملفًا",
        "no_preview": "المعاينة غير متاحة لـ",
        "open_file": "فتح الملف", "show_folder": "عرض في المجلد",
        "copy_path": "نسخ المسار",
        "index_title": "حالة الفهرس",
        "index_desc": "راقب قاعدة بيانات البحث وأدر فهرسة الملفات.",
        "rebuild_index": "إعادة بناء الفهرس", "current_progress": "التقدم الحالي",
        "db_stats": "إحصائيات قاعدة البيانات", "db_size": "حجم قاعدة البيانات",
        "last_indexed": "آخر فهرسة", "search_latency": "زمن استجابة البحث",
        "speed": "السرعة", "duration": "المدة", "files": "الملفات",
        "content_depth": "عمق فهرسة المحتوى",
        "save_reindex": "حفظ وإعادة الفهرسة",
        "file_type_support": "أنواع الملفات المدعومة",
        "settings_title": "الإعدادات",
        "settings_desc": "تخصيص مظهر وسلوك QuickFind.",
        "appearance": "المظهر", "theme": "السمة", "font_size": "حجم الخط",
        "search_behavior": "سلوك البحث", "max_results": "الحد الأقصى للنتائج",
        "open_single_click": "فتح الملف بنقرة واحدة",
        "indexing": "الفهرسة",
        "auto_reindex": "إعادة الفهرسة تلقائيًا عند تغيير الملفات",
        "index_hidden": "فهرسة الملفات والمجلدات المخفية",
        "language": "اللغة", "lang_label": "اللغة",
        "save_settings": "حفظ الإعدادات",
        "initializing": "جارٍ التهيئة...",
        "ready": "جاهز", "files_indexed": "ملفات مفهرسة",
        "first_indexing": "بدء الفهرسة الأولى...",
        "indexing_status": "جارٍ الفهرسة...", "indexing_stopped": "تم إيقاف الفهرسة",
    },
}

_current_lang = "English"

def tr(key):
    return TRANSLATIONS.get(_current_lang, TRANSLATIONS["English"]).get(key, key)

def set_language(lang):
    global _current_lang
    _current_lang = lang


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
        if d < 7:  return f"{d}d ago"
        if d < 30: return f"{d // 7}w ago"
        if d < 365: return f"{d // 30}mo ago"
        return f"{dt:%d.%m.%Y}"
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════
#  SETTINGS PERSISTENCE
# ══════════════════════════════════════════════════════════════

SETTINGS_PATH = os.path.join(SCRIPT_DIR, "QuickFind_Index", "settings.json")

def load_settings():
    defaults = {
        "theme": "light",
        "font_size": 13,
        "show_hidden": False,
        "auto_index": True,
        "auto_index_interval": 2,
        "max_results": 200,
        "open_on_single_click": False,
        "language": "English",
    }
    try:
        with open(SETTINGS_PATH, "r") as f:
            saved = json.load(f)
            defaults.update(saved)
    except Exception:
        pass
    return defaults

def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


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
#  DELEGATE — Material Card
# ══════════════════════════════════════════════════════════════

CARD_H = 72
CARD_GAP = 2
CARD_R = 12

class ResultDelegate(QStyledItemDelegate):
    def __init__(self, theme_getter, parent=None):
        super().__init__(parent)
        self._theme = theme_getter

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), CARD_H + CARD_GAP)

    def paint(self, painter, option, index):
        t = self._theme()
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        r = QRectF(option.rect).adjusted(6, CARD_GAP, -6, 0)
        sel = bool(option.state & QStyle.State_Selected)
        hov = bool(option.state & QStyle.State_MouseOver)

        if sel:
            bg, border, bw = QColor(t["card_sel"]), QColor(t["primary"]), 1.0
        elif hov:
            bg, border, bw = QColor(t["card_hover"]), QColor(t["ov"]), 0.5
        else:
            bg, border, bw = QColor(t["white"]), QColor(t["ov"]), 0
            border.setAlpha(40)

        card = QPainterPath()
        card.addRoundedRect(r, CARD_R, CARD_R)
        painter.setPen(QPen(border, bw) if bw > 0 else Qt.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawPath(card)

        name = index.data(ResultModel.NameRole) or ""
        fpath = index.data(ResultModel.PathRole) or ""
        ext = index.data(ResultModel.ExtRole) or ""
        size = index.data(ResultModel.SizeRole) or 0
        modified = index.data(ResultModel.ModifiedRole) or 0
        is_dir = index.data(ResultModel.IsDirRole) or 0

        # Icon box
        isz = 42
        ix = r.x() + 14
        iy = r.y() + (r.height() - isz) / 2
        ir = QRectF(ix, iy, isz, isz)
        ip = QPainterPath()
        ip.addRoundedRect(ir, 10, 10)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(t["pc"])))
        painter.drawPath(ip)

        el = EXT_ICONS.get(ext, "DIR" if is_dir else ext.replace(".", "").upper()[:3])
        painter.setFont(QFont(FONT_MONO, 8, QFont.Bold))
        painter.setPen(QPen(QColor(t["opc"])))
        painter.drawText(ir, Qt.AlignCenter, el)

        tx = ix + isz + 12
        max_w = r.width() - (tx - r.x()) - 100

        # Name
        painter.setFont(QFont(FONT, 11, QFont.DemiBold))
        painter.setPen(QPen(QColor(t["on_s"])))
        en = QFontMetrics(QFont(FONT, 11, QFont.DemiBold)).elidedText(name, Qt.ElideRight, int(max_w))
        painter.drawText(QRectF(tx, r.y() + 14, max_w, 22), Qt.AlignLeft | Qt.AlignVCenter, en)

        # Path
        painter.setFont(QFont(FONT, 8))
        painter.setPen(QPen(QColor(t["on_sv"])))
        dp = os.path.dirname(fpath).replace("\\", " / ")
        parts = dp.split(" / ")
        if len(parts) > 4:
            dp = parts[0] + " / ... / " + " / ".join(parts[-2:])
        ep = QFontMetrics(QFont(FONT, 8)).elidedText(dp, Qt.ElideMiddle, int(max_w))
        painter.drawText(QRectF(tx, r.y() + 38, max_w, 18), Qt.AlignLeft | Qt.AlignVCenter, ep)

        # Size + time
        rx = r.x() + r.width() - 90
        sz = fmt_size(size)
        if sz and not is_dir:
            painter.setFont(QFont(FONT, 9))
            painter.setPen(QPen(QColor(t["on_sv"])))
            painter.drawText(QRectF(rx, r.y() + 14, 80, 20), Qt.AlignRight | Qt.AlignVCenter, sz)

        tm = fmt_time(modified)
        if tm:
            painter.setFont(QFont(FONT, 8))
            painter.setPen(QPen(QColor(t["outline"])))
            painter.drawText(QRectF(rx, r.y() + 38, 80, 18), Qt.AlignRight | Qt.AlignVCenter, tm)

        painter.restore()


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
#  SIDEBAR
# ══════════════════════════════════════════════════════════════

class Sidebar(QWidget):
    page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(180)
        self._buttons = []
        self._active = 0
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        # Logo
        title = QLabel("QuickFind")
        title.setFont(QFont(FONT, 14, QFont.ExtraBold))
        layout.addWidget(title)

        sub = QLabel("Desktop Search")
        sub.setFont(QFont(FONT, 8))
        sub.setObjectName("sidebar_sub")
        layout.addWidget(sub)
        layout.addSpacing(20)

        pages = [("Search", 0), ("Index Status", 1), ("Settings", 2)]
        for label, idx in pages:
            btn = QPushButton(label)
            btn.setFont(QFont(FONT, 10, QFont.Medium))
            btn.setFixedHeight(38)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, i=idx: self._on_click(i))
            layout.addWidget(btn)
            self._buttons.append(btn)

        layout.addStretch()

    def _on_click(self, idx):
        self._active = idx
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == idx)
        self.page_changed.emit(idx)


# ══════════════════════════════════════════════════════════════
#  PAGE: SEARCH
# ══════════════════════════════════════════════════════════════

class SearchPage(QWidget):
    def __init__(self, db, theme_getter, parent=None):
        super().__init__(parent)
        self.db = db
        self._theme = theme_getter
        self._active_filter = None
        self._active_sort = "relevance"
        self._filter_map = {}
        self.max_results = 200
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left: search + results
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(24, 16, 12, 0)
        ll.setSpacing(6)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for files, code, or documents...")
        self.search_input.setFont(QFont(FONT, 13))
        self.search_input.setFixedHeight(48)
        self.search_input.setObjectName("search_input")
        self.search_input.returnPressed.connect(self._do_search)
        ll.addWidget(self.search_input)

        # Filters
        fr = QWidget()
        fr_l = QHBoxLayout(fr)
        fr_l.setContentsMargins(0, 2, 0, 0)
        fr_l.setSpacing(5)

        self._filter_buttons = {}
        FILTERS = {
            "All":       None,
            "Documents": [".pdf", ".docx", ".doc", ".rtf", ".txt", ".md", ".epub", ".rst"],
            "Images":    [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp"],
            "Code":      [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".java",
                          ".cpp", ".c", ".cs", ".go", ".rs", ".rb", ".php"],
            "Archives":  [".zip", ".rar", ".7z", ".tar", ".gz", ".exe", ".msi"],
            "PDFs":      [".pdf"],
        }
        self._filter_map = FILTERS

        for label in FILTERS:
            btn = QPushButton(label)
            btn.setFont(QFont(FONT, 9))
            btn.setFixedHeight(28)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setCheckable(True)
            if label == "All": btn.setChecked(True)
            btn.clicked.connect(lambda c, l=label: self._set_filter(l))
            fr_l.addWidget(btn)
            self._filter_buttons[label] = btn
        fr_l.addStretch()

        # Sort
        self._sort_buttons = {}
        SORTS = {"Relevance": "relevance", "Name": "name_asc", "Size": "size_desc", "Newest": "date_new"}
        for label, key in SORTS.items():
            btn = QPushButton(label)
            btn.setFont(QFont(FONT, 8))
            btn.setFixedHeight(28)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setCheckable(True)
            if key == "relevance": btn.setChecked(True)
            btn.clicked.connect(lambda c, k=key: self._set_sort(k))
            fr_l.addWidget(btn)
            self._sort_buttons[key] = btn

        ll.addWidget(fr)

        # Stats
        stats = QWidget()
        sl = QHBoxLayout(stats)
        sl.setContentsMargins(2, 0, 2, 0)
        self.result_count = QLabel("")
        self.result_count.setFont(QFont(FONT, 9, QFont.Bold))
        self.result_count.setObjectName("result_count")
        self.search_time = QLabel("")
        self.search_time.setFont(QFont(FONT, 9))
        self.search_time.setObjectName("search_time")
        sl.addWidget(self.result_count)
        sl.addStretch()
        sl.addWidget(self.search_time)
        ll.addWidget(stats)

        # Results
        self.model = ResultModel()
        self.delegate = ResultDelegate(self._theme)
        self.list_view = QListView()
        self.list_view.setModel(self.model)
        self.list_view.setItemDelegate(self.delegate)
        self.list_view.setVerticalScrollMode(QListView.ScrollPerPixel)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_view.setSelectionMode(QListView.SingleSelection)
        self.list_view.setMouseTracking(True)
        self.list_view.setFrameShape(QListView.NoFrame)
        self.list_view.setUniformItemSizes(True)
        self.list_view.doubleClicked.connect(self._on_double_click)
        self.list_view.selectionModel().currentChanged.connect(self._on_sel)
        ll.addWidget(self.list_view)

        # Empty state
        self.empty = QWidget()
        el = QVBoxLayout(self.empty)
        el.setAlignment(Qt.AlignCenter)
        self.empty_title = QLabel("Ready to Search")
        self.empty_title.setFont(QFont(FONT, 20, QFont.Bold))
        self.empty_title.setAlignment(Qt.AlignCenter)
        self.empty_sub = QLabel("Type a query and press Enter")
        self.empty_sub.setFont(QFont(FONT, 10))
        self.empty_sub.setAlignment(Qt.AlignCenter)
        self.empty_sub.setObjectName("empty_sub")
        el.addWidget(self.empty_title)
        el.addWidget(self.empty_sub)
        ll.addWidget(self.empty)
        self.list_view.hide()
        self.empty.show()

        layout.addWidget(left, 1)

        # Right: detail pane
        self.detail = QWidget()
        self.detail.setFixedWidth(280)
        self.detail.setObjectName("detail_pane")
        dl = QVBoxLayout(self.detail)
        dl.setContentsMargins(16, 20, 16, 16)
        dl.setSpacing(10)

        # Preview area
        self.preview_frame = QWidget()
        self.preview_frame.setMinimumHeight(140)
        self.preview_frame.setMaximumHeight(220)
        self.preview_frame.setObjectName("preview_frame")
        pfl = QVBoxLayout(self.preview_frame)
        pfl.setContentsMargins(10, 8, 10, 8)
        pfl.setSpacing(4)

        self.preview_icon = QLabel("")
        self.preview_icon.setFont(QFont(FONT_MONO, 28, QFont.Bold))
        self.preview_icon.setAlignment(Qt.AlignCenter)
        self.preview_icon.setObjectName("preview_icon")
        self.preview_icon.setFixedHeight(50)
        pfl.addWidget(self.preview_icon)

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setFrameShape(QFrame.NoFrame)
        self.preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.preview_scroll.setStyleSheet("background: transparent; border: none;")

        self.preview_text = QLabel("No preview available")
        self.preview_text.setFont(QFont(FONT, 8))
        self.preview_text.setAlignment(Qt.AlignCenter)
        self.preview_text.setObjectName("preview_text")
        self.preview_text.setWordWrap(True)
        self.preview_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.preview_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.preview_scroll.setWidget(self.preview_text)
        pfl.addWidget(self.preview_scroll, 1)
        dl.addWidget(self.preview_frame)

        # File name
        self.d_name = QLabel("Select a file")
        self.d_name.setFont(QFont(FONT, 12, QFont.Bold))
        self.d_name.setWordWrap(True)
        dl.addWidget(self.d_name)

        self.d_type = QLabel("")
        self.d_type.setFont(QFont(FONT, 9, QFont.Medium))
        self.d_type.setObjectName("d_type")
        dl.addWidget(self.d_type)

        dl.addSpacing(4)

        # Info rows
        self.d_size = self._info_row(dl, "SIZE")
        self.d_modified = self._info_row(dl, "MODIFIED")
        self.d_ext = self._info_row(dl, "EXTENSION")
        self.d_path = self._info_row(dl, "PATH", mono=True)

        dl.addSpacing(8)

        # Buttons
        self.open_btn = QPushButton("Open File")
        self.open_btn.setObjectName("open_btn")
        self.open_btn.setFont(QFont(FONT, 10, QFont.DemiBold))
        self.open_btn.setFixedHeight(40)
        self.open_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.open_btn.clicked.connect(self._open_file)
        dl.addWidget(self.open_btn)

        self.folder_btn = QPushButton("Show in Folder")
        self.folder_btn.setObjectName("folder_btn")
        self.folder_btn.setFont(QFont(FONT, 10, QFont.DemiBold))
        self.folder_btn.setFixedHeight(40)
        self.folder_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.folder_btn.clicked.connect(self._open_folder)
        dl.addWidget(self.folder_btn)

        self.copy_btn = QPushButton("Copy File Path")
        self.copy_btn.setObjectName("copy_btn")
        self.copy_btn.setFont(QFont(FONT, 9))
        self.copy_btn.setFixedHeight(32)
        self.copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.copy_btn.clicked.connect(self._copy_path)
        dl.addWidget(self.copy_btn)

        dl.addStretch()

        layout.addWidget(self.detail)
        self._current_path = ""

    def _info_row(self, parent, label, mono=False):
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 2, 0, 2)
        lbl = QLabel(label)
        lbl.setFont(QFont(FONT, 8, QFont.Bold))
        lbl.setFixedWidth(75)
        lbl.setObjectName("info_label")
        val = QLabel("—")
        val.setFont(QFont(FONT_MONO if mono else FONT, 9))
        val.setWordWrap(True)
        rl.addWidget(lbl)
        rl.addWidget(val, 1)
        parent.addWidget(row)
        return val

    def _set_filter(self, label):
        for n, b in self._filter_buttons.items():
            b.setChecked(n == label)
        self._active_filter = self._filter_map.get(label)
        if self.search_input.text().strip() or self._active_filter:
            self._do_search()

    def _set_sort(self, key):
        for k, b in self._sort_buttons.items():
            b.setChecked(k == key)
        self._active_sort = key
        if self.search_input.text().strip() or self._active_filter:
            self._do_search()

    def _do_search(self):
        q = self.search_input.text().strip()
        if not q and not self._active_filter:
            self.model.clear()
            self.list_view.hide()
            self.empty.show()
            self.result_count.setText("")
            self.search_time.setText("")
            return

        t0 = time.perf_counter()
        results = self.db.search(q, limit=self.max_results, ext_filter=self._active_filter, sort=self._active_sort)
        ms = (time.perf_counter() - t0) * 1000

        if results:
            self.model.set_results(results)
            self.empty.hide()
            self.list_view.show()
            self.list_view.setCurrentIndex(self.model.index(0))
        else:
            self.model.clear()
            self.list_view.hide()
            self.empty.show()
            self.empty_title.setText("No Results")
            self.empty_sub.setText("Try a different search term")

        self.result_count.setText(f"{len(results)} results")
        self.search_time.setText(f"{ms:.1f} ms")

    def _on_sel(self, current, previous):
        if not current.isValid():
            return
        name = current.data(ResultModel.NameRole) or ""
        path = current.data(ResultModel.PathRole) or ""
        ext = current.data(ResultModel.ExtRole) or ""
        size = current.data(ResultModel.SizeRole) or 0
        modified = current.data(ResultModel.ModifiedRole) or 0
        self._current_path = path

        self.d_name.setText(name)
        self.d_type.setText(TYPE_NAMES.get(ext, ext.upper().replace(".", "") + " File" if ext else "File"))
        self.d_size.setText(fmt_size(size))
        self.d_ext.setText(ext or "—")
        self.d_path.setText(os.path.dirname(path))
        el = EXT_ICONS.get(ext, ext.replace(".", "").upper()[:3] if ext else "?")

        # Reset preview
        self.preview_icon.show()
        self.preview_icon.setFixedHeight(50)
        self.preview_icon.setText(el)

        # Content preview
        TEXT_EXTS = {".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json", ".xml",
                     ".yaml", ".yml", ".csv", ".sql", ".sh", ".bat", ".ps1", ".ini", ".cfg",
                     ".log", ".java", ".cpp", ".c", ".cs", ".go", ".rs", ".rb", ".php",
                     ".jsx", ".tsx", ".vue", ".toml", ".conf", ".rst", ".tex"}
        RICH_EXTS = {".pdf", ".docx", ".xlsx", ".pptx", ".rtf", ".epub"}

        preview_ok = False
        if os.path.exists(path) and (size is None or size < 2_000_000):
            if ext in TEXT_EXTS:
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        preview = f.read(1000)
                    if preview.strip():
                        self.preview_icon.hide()
                        self.preview_icon.setFixedHeight(0)
                        self.preview_text.setText(preview[:600])
                        self.preview_text.setFont(QFont(FONT_MONO, 7))
                        self.preview_text.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                        preview_ok = True
                except Exception:
                    pass
            elif ext in RICH_EXTS:
                try:
                    from database import RICH_READERS
                    reader = RICH_READERS.get(ext)
                    if reader:
                        content = reader(path)
                        if content and len(content.strip()) > 0:
                            self.preview_icon.hide()
                            self.preview_icon.setFixedHeight(0)
                            self.preview_text.setText(content[:600])
                            self.preview_text.setFont(QFont(FONT, 8))
                            self.preview_text.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                            self.preview_text.setWordWrap(True)
                            preview_ok = True
                except Exception as e:
                    self.preview_text.setText(f"Preview error: {e}")
                    self.preview_text.setAlignment(Qt.AlignCenter)

        if not preview_ok:
            self.preview_text.setText(tr("no_preview") + f" {ext.upper().replace('.', '')}" if ext else "")
            self.preview_text.setFont(QFont(FONT, 8))
            self.preview_text.setAlignment(Qt.AlignCenter)

        if modified:
            try:
                dt = datetime.fromtimestamp(modified)
                self.d_modified.setText(dt.strftime("%b %d, %Y  %H:%M"))
            except Exception:
                self.d_modified.setText("—")

    def _on_double_click(self, index):
        path = self.model.get_path(index.row())
        if path:
            try:
                os.startfile(path)
            except Exception:
                pass

    def _open_file(self):
        if self._current_path and os.path.exists(self._current_path):
            os.startfile(self._current_path)

    def _open_folder(self):
        if self._current_path:
            try:
                if os.path.exists(self._current_path):
                    subprocess.Popen(["explorer", "/select,", self._current_path])
                elif os.path.exists(os.path.dirname(self._current_path)):
                    os.startfile(os.path.dirname(self._current_path))
            except Exception:
                pass

    def _copy_path(self):
        if self._current_path:
            QApplication.clipboard().setText(self._current_path)


# ══════════════════════════════════════════════════════════════
#  PAGE: INDEX STATUS
# ══════════════════════════════════════════════════════════════

class IndexStatusPage(QWidget):
    reindex_requested = Signal()

    def __init__(self, db, theme_getter, parent=None):
        super().__init__(parent)
        self.db = db
        self._theme = theme_getter
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        ml = QVBoxLayout(content)
        ml.setContentsMargins(32, 24, 32, 24)
        ml.setSpacing(20)

        # Header
        hdr = QWidget()
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(0, 0, 0, 0)

        tw = QWidget()
        tl = QVBoxLayout(tw)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(4)
        self.title_label = QLabel("Index Status")
        self.title_label.setFont(QFont(FONT, 24, QFont.ExtraBold))
        self.desc_label = QLabel("Monitor your search database and manage file indexing.")
        self.desc_label.setFont(QFont(FONT, 11))
        self.desc_label.setObjectName("page_desc")
        tl.addWidget(self.title_label)
        tl.addWidget(self.desc_label)
        hl.addWidget(tw, 1)

        self.rebuild_btn = QPushButton("Rebuild Index")
        self.rebuild_btn.setObjectName("primary_btn")
        self.rebuild_btn.setFont(QFont(FONT, 10, QFont.Bold))
        self.rebuild_btn.setFixedHeight(40)
        self.rebuild_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.rebuild_btn.clicked.connect(self.reindex_requested.emit)
        hl.addWidget(self.rebuild_btn)
        ml.addWidget(hdr)

        # Progress + Stats row
        row1 = QWidget()
        r1l = QHBoxLayout(row1)
        r1l.setContentsMargins(0, 0, 0, 0)
        r1l.setSpacing(16)

        # Progress card
        prog_card = QFrame()
        prog_card.setFrameShape(QFrame.StyledPanel)
        prog_card.setObjectName("card")
        pcl = QVBoxLayout(prog_card)
        pcl.setContentsMargins(20, 16, 20, 16)
        pcl.setSpacing(10)

        ph = QWidget()
        phl = QHBoxLayout(ph)
        phl.setContentsMargins(0, 0, 0, 0)
        self.progress_title = QLabel("Current Progress")
        self.progress_title.setFont(QFont(FONT, 14, QFont.Bold))
        pl = self.progress_title
        self.progress_badge = QLabel("READY")
        self.progress_badge.setFont(QFont(FONT, 8, QFont.Bold))
        self.progress_badge.setObjectName("progress_badge")
        phl.addWidget(pl)
        phl.addStretch()
        phl.addWidget(self.progress_badge)
        pcl.addWidget(ph)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(100)
        pcl.addWidget(self.progress_bar)

        self.progress_detail = QLabel("")
        self.progress_detail.setFont(QFont(FONT, 9))
        self.progress_detail.setObjectName("page_desc")
        pcl.addWidget(self.progress_detail)

        # Stat boxes
        stat_row = QWidget()
        srl = QHBoxLayout(stat_row)
        srl.setContentsMargins(0, 4, 0, 0)
        srl.setSpacing(10)

        self.stat_speed = self._stat_box(srl, "SPEED", "—")
        self.stat_time = self._stat_box(srl, "DURATION", "—")
        self.stat_queue = self._stat_box(srl, "FILES", "0")
        pcl.addWidget(stat_row)

        r1l.addWidget(prog_card, 2)

        # DB Stats card
        db_card = QFrame()
        db_card.setFrameShape(QFrame.StyledPanel)
        db_card.setObjectName("card")
        dcl = QVBoxLayout(db_card)
        dcl.setContentsMargins(20, 16, 20, 16)
        dcl.setSpacing(10)

        self.db_stats_title = QLabel("Database Stats")
        self.db_stats_title.setFont(QFont(FONT, 14, QFont.Bold))
        dbl = self.db_stats_title
        dcl.addWidget(dbl)

        self.db_size_val = self._db_row(dcl, "Database Size", "—")
        self.db_created_val = self._db_row(dcl, "Last Indexed", "—")
        self.db_latency_val = self._db_row(dcl, "Search Latency", "< 1ms")

        r1l.addWidget(db_card, 1)
        ml.addWidget(row1)

        # Content depth presets
        self.depth_title = QLabel("Content Indexing Depth")
        self.depth_title.setFont(QFont(FONT, 16, QFont.Bold))
        depth_lbl = self.depth_title
        ml.addWidget(depth_lbl)

        from database import PRESETS, get_preset_name
        current = get_preset_name()
        self._preset_group = QButtonGroup(self)
        self._preset_radios = {}

        for key in ["minimal", "standard", "deep", "maximum"]:
            p = PRESETS[key]
            rb = QRadioButton(f"{key.capitalize()}  —  {p['label']}")
            if key == current: rb.setChecked(True)
            self._preset_group.addButton(rb)
            self._preset_radios[key] = rb
            ml.addWidget(rb)

        self.save_preset_btn = QPushButton("Save & Reindex")
        save_preset_btn = self.save_preset_btn
        save_preset_btn.setObjectName("primary_btn")
        save_preset_btn.setFont(QFont(FONT, 10, QFont.Bold))
        save_preset_btn.setFixedHeight(38)
        save_preset_btn.setFixedWidth(180)
        save_preset_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_preset_btn.clicked.connect(self._save_preset)
        ml.addWidget(save_preset_btn)

        # File types
        self.ft_title = QLabel("File Type Support")
        self.ft_title.setFont(QFont(FONT, 16, QFont.Bold))
        ft = self.ft_title
        ml.addWidget(ft)

        ftr = QWidget()
        ftl = QHBoxLayout(ftr)
        ftl.setContentsMargins(0, 0, 0, 0)
        ftl.setSpacing(10)
        for name, exts in [("Documents", "PDF, DOCX, TXT"), ("Data", "XLSX, CSV, JSON"),
                           ("Code", "PY, JS, HTML, CPP"), ("Images", "JPG, PNG (Meta)")]:
            c = QFrame()
            c.setFrameShape(QFrame.StyledPanel)
            c.setObjectName("type_chip")
            cl = QVBoxLayout(c)
            cl.setContentsMargins(14, 8, 14, 8)
            cl.setSpacing(2)
            cn = QLabel(name)
            cn.setFont(QFont(FONT, 10, QFont.Bold))
            ce = QLabel(exts)
            ce.setFont(QFont(FONT, 8))
            ce.setObjectName("page_desc")
            cl.addWidget(cn)
            cl.addWidget(ce)
            ftl.addWidget(c)
        ftl.addStretch()
        ml.addWidget(ftr)

        ml.addStretch()
        scroll.setWidget(content)
        self._scroll = scroll
        self._content = content

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def apply_theme(self, t):
        bg = t["bg"]
        white = t["white"]
        primary = t["primary"]
        on_primary = t["on_primary"]
        on_s = t["on_s"]
        on_sv = t["on_sv"]
        ov = t["ov"]
        pc = t["pc"]
        scl = t["scl"]
        divider = t["divider"]

        self.setStyleSheet(f"""
            QLabel {{ color: {on_s}; background: transparent; }}
            QFrame#card {{
                background: {white};
                border: 1px solid {divider};
                border-radius: 14px;
            }}
            QFrame#stat_box {{
                background: {scl};
                border-radius: 8px;
            }}
            QLabel#stat_label {{ color: {on_sv}; background: transparent; }}
            QLabel#stat_value {{ color: {primary}; background: transparent; }}
            QLabel#page_desc {{ color: {on_sv}; background: transparent; }}
            QLabel#progress_badge {{
                background: {pc};
                color: {primary};
                border-radius: 10px;
                padding: 3px 10px;
            }}
            QProgressBar {{
                background: {pc}; border: none; border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background: {primary}; border-radius: 5px;
            }}
            QPushButton#primary_btn {{
                background: {primary};
                color: {on_primary};
                border: none;
                border-radius: 10px;
                padding: 4px 20px;
            }}
            QPushButton#primary_btn:hover {{ background: {_darken(primary)}; }}
            QPushButton#primary_btn:pressed {{ background: {_darken(_darken(primary))}; padding-top: 6px; }}
            QFrame#type_chip {{
                background: {white};
                border: 1px solid {divider};
                border-radius: 10px;
            }}
            QRadioButton {{
                color: {on_s}; spacing: 8px; padding: 8px 12px;
                background: {white}; border: 1px solid {ov}; border-radius: 10px;
            }}
            QRadioButton:checked {{ border-color: {primary}; background: {pc}; }}
            QRadioButton::indicator {{
                width: 14px; height: 14px; border-radius: 7px;
                border: 2px solid {ov}; background: transparent;
            }}
            QRadioButton::indicator:checked {{ border-color: {primary}; background: {primary}; }}
            QScrollArea {{ background: {bg}; border: none; }}
        """)
        from PySide6.QtGui import QPalette
        pal_s = self._scroll.palette()
        pal_s.setColor(QPalette.Window, QColor(bg))
        self._scroll.setPalette(pal_s)
        self._scroll.setAutoFillBackground(True)
        self._scroll.setStyleSheet("border: none;")
        if self._scroll.viewport():
            pal_v = self._scroll.viewport().palette()
            pal_v.setColor(QPalette.Window, QColor(bg))
            self._scroll.viewport().setPalette(pal_v)
            self._scroll.viewport().setAutoFillBackground(True)
        from PySide6.QtGui import QPalette
        pal = self._content.palette()
        pal.setColor(QPalette.Window, QColor(bg))
        self._content.setPalette(pal)
        self._content.setAutoFillBackground(True)

    def _stat_box(self, parent_layout, label, value):
        w = QFrame()
        w.setFrameShape(QFrame.StyledPanel)
        w.setObjectName("stat_box")
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 8, 12, 8)
        l.setSpacing(2)
        lbl = QLabel(label)
        lbl.setFont(QFont(FONT, 7, QFont.Bold))
        lbl.setObjectName("stat_label")
        val = QLabel(value)
        val.setFont(QFont(FONT, 16, QFont.Black))
        val.setObjectName("stat_value")
        l.addWidget(lbl)
        l.addWidget(val)
        parent_layout.addWidget(w)
        return val

    def _db_row(self, parent_layout, label, value):
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 4, 0, 4)
        lbl = QLabel(label)
        lbl.setFont(QFont(FONT, 10))
        lbl.setObjectName("page_desc")
        val = QLabel(value)
        val.setFont(QFont(FONT, 11, QFont.Bold))
        rl.addWidget(lbl)
        rl.addStretch()
        rl.addWidget(val)
        parent_layout.addWidget(row)
        return val

    def refresh(self):
        count = self.db.get_file_count()
        db_size = self.db.get_db_size_mb()
        last_index = self.db.get_meta("last_index_time")
        duration = self.db.get_meta("index_duration")

        self.stat_queue.setText(f"{count:,}")
        self.db_size_val.setText(f"{db_size:.0f} MB")
        self.stat_time.setText(f"{duration}s" if duration else "—")

        if last_index:
            try:
                dt = datetime.fromisoformat(last_index)
                self.db_created_val.setText(dt.strftime("%b %d, %H:%M"))
            except Exception:
                pass

    def _save_preset(self):
        from database import get_preset_name, set_preset_name
        for key, rb in self._preset_radios.items():
            if rb.isChecked():
                if key != get_preset_name():
                    set_preset_name(key)
                break
        self.reindex_requested.emit()

    def retranslate(self):
        self.title_label.setText(tr("index_title"))
        self.desc_label.setText(tr("index_desc"))
        self.rebuild_btn.setText(tr("rebuild_index"))
        self.progress_title.setText(tr("current_progress"))
        self.db_stats_title.setText(tr("db_stats"))
        self.depth_title.setText(tr("content_depth"))
        self.ft_title.setText(tr("file_type_support"))
        self.save_preset_btn.setText(tr("save_reindex"))


# ══════════════════════════════════════════════════════════════
#  PAGE: SETTINGS
# ══════════════════════════════════════════════════════════════

class SettingsPage(QWidget):
    theme_changed = Signal(str)
    settings_changed = Signal(dict)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._section_labels = []
        self._cards = []
        self._build()

    def _card(self, ml, title):
        """Create a styled card container and return its layout."""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setObjectName("settings_card")
        self._cards.append(card)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(12)
        lbl = QLabel(title.upper())
        lbl.setFont(QFont(FONT, 9, QFont.Bold))
        lbl.setObjectName("card_section_title")
        self._section_labels.append(lbl)
        cl.addWidget(lbl)
        ml.addWidget(card)
        return cl

    def _setting_row(self, parent_layout, label_text, right_widget):
        row = QWidget()
        row.setObjectName("setting_row")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 4, 0, 4)
        lbl = QLabel(label_text)
        lbl.setFont(QFont(FONT, 11, QFont.DemiBold))
        rl.addWidget(lbl)
        rl.addStretch()
        rl.addWidget(right_widget)
        parent_layout.addWidget(row)
        return lbl

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setObjectName("settings_content")
        ml = QVBoxLayout(content)
        ml.setContentsMargins(32, 24, 32, 24)
        ml.setSpacing(16)

        self.title_label = QLabel("Settings")
        self.title_label.setFont(QFont(FONT, 24, QFont.ExtraBold))
        ml.addWidget(self.title_label)
        self.desc_label = QLabel("Customize QuickFind appearance and behavior.")
        self.desc_label.setFont(QFont(FONT, 11))
        ml.addWidget(self.desc_label)
        ml.addSpacing(4)

        # ── Appearance Card ──
        cl = self._card(ml, "APPEARANCE")

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Turquoise", "Purple"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "light").capitalize())
        self.theme_combo.setFont(QFont(FONT, 10))
        self.theme_combo.setFixedWidth(160)
        self.theme_combo.setFixedHeight(34)
        self.theme_combo.currentTextChanged.connect(lambda t: self.theme_changed.emit(t.lower()))
        self.theme_label = self._setting_row(cl, "Theme", self.theme_combo)

        font_w = QWidget()
        fwl = QHBoxLayout(font_w)
        fwl.setContentsMargins(0, 0, 0, 0)
        fwl.setSpacing(8)
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(10, 18)
        self.font_slider.setValue(self.settings.get("font_size", 13))
        self.font_slider.setFixedWidth(140)
        self.font_val = QLabel(str(self.font_slider.value()))
        self.font_val.setFont(QFont(FONT, 12, QFont.Bold))
        self.font_val.setFixedWidth(28)
        self.font_slider.valueChanged.connect(lambda v: self.font_val.setText(str(v)))
        fwl.addWidget(self.font_slider)
        fwl.addWidget(self.font_val)
        self.font_size_label = self._setting_row(cl, "Font Size", font_w)

        # ── Search Behavior Card ──
        cl2 = self._card(ml, "SEARCH BEHAVIOR")

        self.max_results_combo = QComboBox()
        self.max_results_combo.addItems(["50", "100", "200", "500", "1000"])
        self.max_results_combo.setCurrentText(str(self.settings.get("max_results", 200)))
        self.max_results_combo.setFont(QFont(FONT, 10))
        self.max_results_combo.setFixedWidth(160)
        self.max_results_combo.setFixedHeight(34)
        self.max_results_label = self._setting_row(cl2, "Max Results", self.max_results_combo)

        self.single_click = QCheckBox("Open file on single click")
        self.single_click.setFont(QFont(FONT, 11))
        self.single_click.setChecked(self.settings.get("open_on_single_click", False))
        cl2.addWidget(self.single_click)

        # ── Indexing Card ──
        cl3 = self._card(ml, "INDEXING")

        self.auto_index = QCheckBox("Auto-reindex when files change (file watcher)")
        self.auto_index.setFont(QFont(FONT, 11))
        self.auto_index.setChecked(self.settings.get("auto_index", True))
        cl3.addWidget(self.auto_index)

        self.show_hidden = QCheckBox("Index hidden files and folders")
        self.show_hidden.setFont(QFont(FONT, 11))
        self.show_hidden.setChecked(self.settings.get("show_hidden", False))
        cl3.addWidget(self.show_hidden)

        # ── Language Card ──
        cl4 = self._card(ml, "LANGUAGE")

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Turkish", "German", "French", "Spanish",
                                   "Portuguese", "Italian", "Japanese", "Chinese",
                                   "Korean", "Russian", "Arabic"])
        self.lang_combo.setCurrentText(self.settings.get("language", "English"))
        self.lang_combo.setFont(QFont(FONT, 10))
        self.lang_combo.setFixedWidth(160)
        self.lang_combo.setFixedHeight(34)
        self.lang_label = self._setting_row(cl4, "Language", self.lang_combo)

        ml.addSpacing(8)

        # Save button
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setFont(QFont(FONT, 11, QFont.Bold))
        self.save_btn.setFixedHeight(44)
        self.save_btn.setFixedWidth(200)
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_btn.setObjectName("save_settings_btn")
        self.save_btn.clicked.connect(self._save)
        ml.addWidget(self.save_btn)

        ml.addStretch()
        scroll.setWidget(content)
        self._scroll = scroll
        self._content = content

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def apply_theme(self, t):
        """Directly apply theme colors to all widgets."""
        bg = t["bg"]
        white = t["white"]
        primary = t["primary"]
        on_primary = t["on_primary"]
        on_s = t["on_s"]
        on_sv = t["on_sv"]
        ov = t["ov"]
        pc = t["pc"]
        divider = t["divider"]
        sch = t["sch"]
        dark_primary = _darken(primary) if '_darken' in dir() else primary

        ss = f"""
            QWidget#settings_content {{ background: {bg}; }}
            QLabel {{ color: {on_s}; background: transparent; }}
            QFrame#settings_card {{
                background: {white};
                border: 1px solid {divider};
                border-radius: 14px;
            }}
            QLabel#card_section_title {{
                color: {primary};
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 2px;
                background: transparent;
            }}
            QWidget#setting_row {{ background: transparent; }}

            QComboBox {{
                background: {sch};
                color: {on_s};
                border: 1px solid {ov};
                border-radius: 8px;
                padding: 6px 12px;
            }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox QAbstractItemView {{
                background: {white};
                color: {on_s};
                selection-background-color: {pc};
                border: 1px solid {ov};
                border-radius: 6px;
            }}

            QCheckBox {{ color: {on_s}; spacing: 10px; background: transparent; }}
            QCheckBox::indicator {{
                width: 20px; height: 20px;
                border: 2px solid {ov};
                border-radius: 5px;
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: {primary};
                border-color: {primary};
            }}

            QSlider::groove:horizontal {{
                background: {pc};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {primary};
                width: 20px; height: 20px;
                margin: -7px 0;
                border-radius: 10px;
                border: 3px solid {white};
            }}

            QPushButton#save_settings_btn {{
                background: {primary};
                color: {on_primary};
                border: none;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton#save_settings_btn:hover {{
                background: {_darken(primary)};
            }}
            QPushButton#save_settings_btn:pressed {{
                background: {_darken(_darken(primary))};
                padding-top: 3px;
            }}

            QScrollArea {{ background: {bg}; border: none; }}
        """
        self.setStyleSheet(ss)
        from PySide6.QtGui import QPalette
        pal_s = self._scroll.palette()
        pal_s.setColor(QPalette.Window, QColor(bg))
        self._scroll.setPalette(pal_s)
        self._scroll.setAutoFillBackground(True)
        self._scroll.setStyleSheet("border: none;")
        if self._scroll.viewport():
            pal_v = self._scroll.viewport().palette()
            pal_v.setColor(QPalette.Window, QColor(bg))
            self._scroll.viewport().setPalette(pal_v)
            self._scroll.viewport().setAutoFillBackground(True)
        from PySide6.QtGui import QPalette
        pal = self._content.palette()
        pal.setColor(QPalette.Window, QColor(bg))
        self._content.setPalette(pal)
        self._content.setAutoFillBackground(True)

    def _section(self, layout, title):
        pass  # Not used anymore — kept for compat
        layout.addWidget(lbl)
        if hasattr(self, '_section_labels'):
            self._section_labels.append((lbl, title))

    def retranslate(self):
        self.title_label.setText(tr("settings_title"))
        self.desc_label.setText(tr("settings_desc"))
        self.theme_label.setText(tr("theme"))
        self.font_size_label.setText(tr("font_size"))
        self.max_results_label.setText(tr("max_results"))
        self.lang_label.setText(tr("lang_label"))
        self.save_btn.setText(tr("save_settings"))
        self.single_click.setText(tr("open_single_click"))
        self.auto_index.setText(tr("auto_reindex"))
        self.show_hidden.setText(tr("index_hidden"))
        # Section labels
        section_keys = ["appearance", "search_behavior", "indexing", "language"]
        for i, (lbl, _) in enumerate(self._section_labels):
            if i < len(section_keys):
                lbl.setText(tr(section_keys[i]))

    def _save(self):
        self.settings["theme"] = self.theme_combo.currentText().lower()
        self.settings["font_size"] = self.font_slider.value()
        self.settings["max_results"] = int(self.max_results_combo.currentText())
        self.settings["open_on_single_click"] = self.single_click.isChecked()
        self.settings["auto_index"] = self.auto_index.isChecked()
        self.settings["show_hidden"] = self.show_hidden.isChecked()
        self.settings["language"] = self.lang_combo.currentText()
        save_settings(self.settings)
        self.settings_changed.emit(self.settings)


# ══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════

class QuickFindWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        set_language(self.settings.get("language", "English"))
        theme_name = self.settings.get("theme", "light")
        self.is_dark = theme_name == "dark"
        self.T = THEMES.get(theme_name, THEMES["light"])
        self._indexer_thread = None
        self._file_watcher = None

        from database import FileDatabase
        self.db = FileDatabase()

        self.setWindowTitle("QuickFind")
        self.setMinimumSize(900, 600)
        self.resize(1100, 740)

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
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._switch_page)
        root.addWidget(self.sidebar)

        # Main area
        main_area = QWidget()
        ml = QVBoxLayout(main_area)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        # Header bar
        self.header = QWidget()
        self.header.setFixedHeight(44)
        self.header.setObjectName("header")
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(20, 0, 16, 0)

        self.page_title = QLabel("Search")
        self.page_title.setFont(QFont(FONT, 10, QFont.DemiBold))
        self.page_title.setObjectName("page_title")

        self.status_hint = QLabel("")
        self.status_hint.setFont(QFont(FONT, 9))
        self.status_hint.setObjectName("status_hint")

        hl.addWidget(self.page_title)
        hl.addSpacing(16)
        hl.addWidget(self.status_hint)
        hl.addStretch()
        ml.addWidget(self.header)

        # Stacked pages
        self.stack = QStackedWidget()

        self.search_page = SearchPage(self.db, self._get_theme)
        self.index_page = IndexStatusPage(self.db, self._get_theme)
        self.settings_page = SettingsPage(self.settings)

        self.index_page.reindex_requested.connect(self._reindex)
        self.settings_page.theme_changed.connect(self._on_theme_change)
        self.settings_page.settings_changed.connect(self._on_settings_change)

        self.stack.addWidget(self.search_page)
        self.stack.addWidget(self.index_page)
        self.stack.addWidget(self.settings_page)
        ml.addWidget(self.stack)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont(FONT, 9))
        self.status_bar.setFixedHeight(28)
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Initializing...")
        self.idx_count_label = QLabel("")
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.idx_count_label)

        root.addWidget(main_area, 1)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+O"), self, self.search_page._open_folder)
        QShortcut(QKeySequence("Escape"), self, self._clear_search)
        QShortcut(QKeySequence("Ctrl+R"), self, self._reindex)
        QShortcut(QKeySequence("Ctrl+L"), self, self._focus_search)
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self._switch_page(0))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self._switch_page(1))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self._switch_page(2))

    def _switch_page(self, idx):
        self.stack.setCurrentIndex(idx)
        titles = ["Search", "Index Status", "Settings"]
        self.page_title.setText(titles[idx])
        if idx == 1:
            self.index_page.refresh()
        # Update sidebar
        for i, btn in enumerate(self.sidebar._buttons):
            btn.setChecked(i == idx)

    # ─── Theme ────────────────────────────────────────────

    def _apply_theme(self):
        t = self.T
        self.setStyleSheet(f"""
            QMainWindow {{ background: {t["bg"]}; }}

            /* Sidebar */
            Sidebar {{
                background: {t["scl"]};
                border-right: 1px solid {t["divider"]};
            }}
            Sidebar QLabel {{ color: {t["on_s"]}; background: transparent; }}
            Sidebar #sidebar_sub {{ color: {t["on_sv"]}; }}
            Sidebar QPushButton {{
                background: transparent;
                color: {t["on_sv"]};
                border: none;
                border-radius: 8px;
                padding: 4px 12px;
                text-align: left;
            }}
            Sidebar QPushButton:checked {{
                background: {t["white"]};
                color: {t["primary"]};
                font-weight: 700;
            }}
            Sidebar QPushButton:hover:!checked {{
                background: {t["sch"]};
            }}

            /* Header */
            #header {{
                background: {t["bg"]};
                border-bottom: 1px solid {t["divider"]};
            }}
            #page_title {{ color: {t["primary"]}; background: transparent; }}
            #status_hint {{ color: {t["on_sv"]}; background: transparent; }}

            /* Search */
            #search_input {{
                background: {t["sch"]};
                color: {t["on_s"]};
                border: 2px solid transparent;
                border-radius: 14px;
                padding: 6px 20px;
            }}
            #search_input:focus {{
                border-color: {t["primary"]};
            }}
            #search_input::placeholder {{ color: {t["on_sv"]}; }}

            /* Filter/sort chips */
            QPushButton[checkable="true"] {{
                background: {t["white"]};
                color: {t["on_sv"]};
                border: 1px solid {t["ov"]};
                border-radius: 14px;
                padding: 2px 12px;
            }}
            QPushButton[checkable="true"]:checked {{
                background: {t["primary"]};
                color: {t["on_primary"]};
                border-color: {t["primary"]};
            }}
            QPushButton[checkable="true"]:hover:!checked {{
                background: {t["card_hover"]};
            }}

            /* Results */
            QListView {{ background: transparent; border: none; outline: none; }}
            QListView::item {{ border: none; padding: 0; }}
            QListView::item:selected, QListView::item:hover {{ background: transparent; }}

            /* Detail pane */
            #detail_pane {{
                background: {t["scl"]};
                border-left: 1px solid {t["divider"]};
            }}
            #preview_frame {{
                background: {t["sch"]};
                border-radius: 12px;
            }}
            #preview_icon {{ color: {t["on_sv"]}; background: transparent; }}
            #preview_text {{ color: {t["on_sv"]}; background: transparent; }}
            #d_type {{ color: {t["primary"]}; }}
            #info_label {{ color: {t["on_sv"]}; }}
            #open_btn {{
                background: {t["primary"]};
                color: {t["on_primary"]};
                border: none;
                border-radius: 10px;
            }}
            #open_btn:pressed {{ background: {_darken(t["primary"], 35)}; padding-top: 6px; padding-bottom: 2px; }}
            #folder_btn {{
                background: {t["sec_c"]};
                color: {t["on_s"]};
                border: none;
                border-radius: 10px;
            }}
            #folder_btn:pressed {{ background: {_darken(t["sec_c"], 30)}; padding-top: 6px; padding-bottom: 2px; }}
            #primary_btn:pressed {{ background: {_darken(t["primary"], 35)}; padding-top: 6px; padding-bottom: 2px; }}
            Sidebar QPushButton:pressed {{ background: {_darken(t["sch"], 20)}; }}
            QPushButton[checkable="true"]:pressed {{ background: {_darken(t["white"], 20)}; }}
            #copy_btn {{
                background: transparent;
                color: {t["primary"]};
                border: none;
            }}

            /* Index/Settings pages */
            #card {{
                background: {t["white"]};
                border-radius: 12px;
            }}
            #stat_box {{
                background: {t["scl"]};
                border-radius: 8px;
            }}
            #stat_label {{ color: {t["on_sv"]}; background: transparent; }}
            #stat_value {{ color: {t["primary"]}; background: transparent; }}
            #progress_badge {{
                background: {t["pc"]};
                color: {t["opc"]};
                border-radius: 10px;
                padding: 3px 10px;
            }}
            QProgressBar {{
                background: {t["pc"]};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background: {t["primary"]};
                border-radius: 5px;
            }}
            #primary_btn {{
                background: {t["primary"]};
                color: {t["on_primary"]};
                border: none;
                border-radius: 10px;
                padding: 4px 20px;
            }}
            #type_chip {{
                background: {t["white"]};
                border: 1px solid {t["divider"]};
                border-radius: 10px;
            }}
            #page_desc {{ color: {t["on_sv"]}; background: transparent; }}
            #result_count {{ color: {t["primary"]}; background: transparent; }}
            #search_time {{ color: {t["on_sv"]}; background: transparent; }}
            #empty_sub {{ color: {t["on_sv"]}; }}

            QRadioButton {{
                color: {t["on_s"]};
                spacing: 8px;
                padding: 8px 12px;
                background: {t["sc"]};
                border: 1px solid {t["ov"]};
                border-radius: 10px;
            }}
            QRadioButton:checked {{
                border-color: {t["primary"]};
                background: {t["pc"]};
            }}
            QRadioButton::indicator {{
                width: 14px; height: 14px;
                border-radius: 7px;
                border: 2px solid {t["ov"]};
                background: transparent;
            }}
            QRadioButton::indicator:checked {{
                border-color: {t["primary"]};
                background: {t["primary"]};
            }}

            QLabel {{ color: {t["on_s"]}; background: transparent; }}

            QScrollArea {{ background: {t["bg"]}; border: none; }}
            QScrollBar:vertical {{
                background: transparent; width: 6px; margin: 4px 1px; border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {t["sb"]}; min-height: 30px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {t["sb_h"]}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

            QStatusBar {{
                background: {t["bg"]};
                color: {t["on_sv"]};
                border-top: 1px solid {t["divider"]};
            }}

            QComboBox {{
                background: {t["white"]};
                color: {t["on_s"]};
                border: 1px solid {t["ov"]};
                border-radius: 8px;
                padding: 4px 10px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background: {t["white"]};
                color: {t["on_s"]};
                selection-background-color: {t["pc"]};
                border: 1px solid {t["ov"]};
            }}

            QCheckBox {{ color: {t["on_s"]}; spacing: 8px; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 2px solid {t["ov"]};
                border-radius: 4px;
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: {t["primary"]};
                border-color: {t["primary"]};
            }}

            QSlider::groove:horizontal {{
                background: {t["pc"]};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {t["primary"]};
                width: 18px; height: 18px;
                margin: -6px 0;
                border-radius: 9px;
                border: 3px solid {t["white"]};
            }}

            #section_sep {{ color: {t["divider"]}; }}
            #section_title {{ color: {t["on_sv"]}; background: transparent; }}

        """)

        # Apply theme to each page directly
        self.index_page.apply_theme(t)
        self.settings_page.apply_theme(t)

        # Detail pane
        self.search_page.detail.setStyleSheet(f"""
            background: {t['scl']};
            border-left: 1px solid {t['divider']};
        """)
        pf = self.search_page.preview_frame
        pf.setStyleSheet(f"background: {t['sch']}; border-radius: 12px;")

        self.search_page.list_view.viewport().update()

    def _on_theme_change(self, theme_name):
        self.is_dark = theme_name == "dark"
        self.T = THEMES.get(theme_name, THEMES["light"])
        self._apply_theme()
        self._apply_win_effects()

    def _on_settings_change(self, settings):
        self.settings = settings
        # Apply font size
        font = QFont(FONT, settings.get("font_size", 13))
        QApplication.instance().setFont(font)
        # Apply language
        lang = settings.get("language", "English")
        set_language(lang)
        self._apply_translations()
        # Apply max_results
        self.search_page.max_results = settings.get("max_results", 200)

    def _apply_translations(self):
        # Sidebar
        pages = [tr("search"), tr("index_status"), tr("settings")]
        for i, btn in enumerate(self.sidebar._buttons):
            btn.setText(pages[i])
        # Sidebar subtitle
        self.sidebar.findChild(QLabel, "sidebar_sub").setText(tr("desktop_search"))
        # Search page
        self.search_page.search_input.setPlaceholderText(tr("search_placeholder"))
        self.search_page.empty_title.setText(tr("ready_to_search"))
        self.search_page.empty_sub.setText(tr("type_query"))
        self.search_page.d_name.setText(tr("select_file"))
        self.search_page.open_btn.setText(tr("open_file"))
        self.search_page.folder_btn.setText(tr("show_folder"))
        self.search_page.copy_btn.setText(tr("copy_path"))
        # Index page
        self.index_page.retranslate()
        # Settings page
        self.settings_page.retranslate()
        # Header
        titles = [tr("search"), tr("index_status"), tr("settings")]
        self.page_title.setText(titles[self.stack.currentIndex()])

    def _apply_win_effects(self):
        try:
            hwnd = int(self.winId())
            v = ctypes.c_int(1 if self.is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(v), 4)
            bd = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 38, ctypes.byref(bd), 4)
        except Exception:
            pass

    # ─── Actions ──────────────────────────────────────────

    def _clear_search(self):
        self.search_page.search_input.clear()
        self.search_page.search_input.setFocus()
        self.search_page.model.clear()
        self.search_page.list_view.hide()
        self.search_page.empty.show()
        self.search_page.empty_title.setText("Ready to Search")
        self.search_page.empty_sub.setText("Type a query and press Enter")

    def _focus_search(self):
        self._switch_page(0)
        self.search_page.search_input.setFocus()
        self.search_page.search_input.selectAll()

    # ─── Indexing ─────────────────────────────────────────

    def _start_indexing(self):
        n = self.db.get_file_count()
        if n > 0:
            self.status_label.setText(f"Ready — {n:,} files indexed")
            self.idx_count_label.setText(f"[{n:,}]")
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
            return
        self._run_indexer(True)

    def _on_idx_progress(self, count):
        self.idx_count_label.setText(f"[{count:,}]")
        self.status_hint.setText(f"Indexing... {count:,} files")
        self.index_page.stat_queue.setText(f"{count:,}")
        self.index_page.progress_badge.setText("INDEXING")

    def _on_idx_status(self, msg):
        self.status_label.setText(msg)
        self.index_page.progress_detail.setText(msg)
        if "Ready" in msg:
            self.status_hint.setText("")
            self.index_page.progress_badge.setText("READY")
            self.index_page.refresh()

    def _on_idx_done(self):
        self.index_page.progress_badge.setText("COMPLETE")
        self.index_page.progress_bar.setValue(100)
        self.index_page.refresh()
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

    ico = os.path.join(SCRIPT_DIR, "quickfind.ico")
    if os.path.exists(ico):
        app.setWindowIcon(QIcon(ico))

    window = QuickFindWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
