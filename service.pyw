"""
QuickFind Background Service
Sistem tepsisinde çalışır, dosya değişikliklerini sürekli izler.
Windows açılışında otomatik başlar.
"""

import sys, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer, Signal, QObject
import subprocess, ctypes

from database import FileDatabase, FileIndexer, FileWatcher, DB_DIR


class WatcherSignals(QObject):
    """Thread-safe sinyaller"""
    status_changed = Signal(str)


class QuickFindService:
    def __init__(self, app: QApplication):
        self.app = app
        self.db = FileDatabase()
        self.watcher = None
        self.signals = WatcherSignals()
        self.indexer_thread = None

        # Tray icon
        ico_path = os.path.join(SCRIPT_DIR, "quickfind.ico")
        self.icon = QIcon(ico_path) if os.path.exists(ico_path) else QIcon()

        self.tray = QSystemTrayIcon(self.icon, parent=None)
        self.tray.setToolTip("QuickFind — Dosya indeksleme aktif")
        self.tray.activated.connect(self._on_tray_activated)

        # Context menu
        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #1A1A2E;
                color: #F0F0F8;
                border: 1px solid #2E2E50;
                border-radius: 8px;
                padding: 4px;
                font-family: 'Segoe UI';
                font-size: 11px;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2A1F5E;
            }
            QMenu::separator {
                height: 1px;
                background: #2E2E50;
                margin: 4px 8px;
            }
        """)

        # Menü öğeleri
        open_action = QAction("⚡  QuickFind Aç", self.menu)
        open_action.triggered.connect(self._open_quickfind)

        self.status_action = QAction("", self.menu)
        self.status_action.setEnabled(False)
        self._update_status_text()

        reindex_action = QAction("↻   Yeniden İndeksle", self.menu)
        reindex_action.triggered.connect(self._reindex)

        startup_action = QAction("🔄  Başlangıçta Çalıştır", self.menu)
        startup_action.setCheckable(True)
        startup_action.setChecked(self._is_in_startup())
        startup_action.triggered.connect(self._toggle_startup)

        sep1 = self.menu.addSeparator()
        quit_action = QAction("✕   Çıkış", self.menu)
        quit_action.triggered.connect(self._quit)

        self.menu.addAction(open_action)
        self.menu.addSeparator()
        self.menu.addAction(self.status_action)
        self.menu.addAction(reindex_action)
        self.menu.addSeparator()
        self.menu.addAction(startup_action)
        self.menu.addSeparator()
        self.menu.addAction(quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.show()

        # Sinyaller
        self.signals.status_changed.connect(self._on_status_changed)

        # Watcher başlat
        self._start_watcher()

        # İlk indeksleme gerekli mi kontrol et
        if self.db.get_file_count() == 0:
            self._reindex()

        # Periyodik durum güncelleme (her 30 sn)
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_text)
        self.status_timer.start(30000)

    def _start_watcher(self):
        if self.watcher and self.watcher.is_running():
            return
        self.watcher = FileWatcher(
            self.db,
            status_callback=lambda msg: self.signals.status_changed.emit(msg)
        )
        self.watcher.start()
        self.tray.setToolTip("QuickFind — Dosya izleme aktif ✓")

    def _stop_watcher(self):
        if self.watcher:
            self.watcher.stop()

    def _on_status_changed(self, msg):
        self.tray.setToolTip(f"QuickFind — {msg}")

    def _update_status_text(self):
        count = self.db.get_file_count()
        db_size = self.db.get_db_size_mb()
        watcher_status = "✓ İzleme aktif" if (self.watcher and self.watcher.is_running()) else "⏸ İzleme durdu"
        self.status_action.setText(f"📊  {count:,} dosya  •  {db_size:.0f} MB  •  {watcher_status}")

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._open_quickfind()

    def _open_quickfind(self):
        """Ana QuickFind uygulamasını aç"""
        pyw_path = os.path.join(SCRIPT_DIR, "QuickFind.pyw")
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = "pythonw"
        try:
            subprocess.Popen([pythonw, pyw_path], cwd=SCRIPT_DIR)
        except Exception:
            try:
                subprocess.Popen(["pyw", pyw_path], cwd=SCRIPT_DIR)
            except Exception:
                pass

    def _reindex(self):
        """Arka planda tam yeniden indeksleme"""
        import threading

        def run():
            indexer = FileIndexer(
                self.db,
                progress_callback=lambda c: self.signals.status_changed.emit(f"İndeksleniyor... {c:,} dosya"),
                status_callback=lambda m: self.signals.status_changed.emit(m)
            )
            indexer.start(reindex=True)
            if indexer._thread:
                indexer._thread.join()
            self._update_status_text()
            self.tray.showMessage(
                "QuickFind",
                f"İndeksleme tamamlandı! {self.db.get_file_count():,} dosya",
                QSystemTrayIcon.Information,
                3000
            )

        t = threading.Thread(target=run, daemon=True)
        t.start()

    # ─── Windows Startup ──────────────────────────────────

    STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    STARTUP_NAME = "QuickFind"

    def _get_startup_command(self):
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = r"C:\Users\dgknk\AppData\Local\Programs\Python\Python313\pythonw.exe"
        service_path = os.path.join(SCRIPT_DIR, "service.pyw")
        return f'"{pythonw}" "{service_path}"'

    def _is_in_startup(self):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.STARTUP_KEY, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, self.STARTUP_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False

    def _toggle_startup(self, checked):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
            if checked:
                winreg.SetValueEx(key, self.STARTUP_NAME, 0, winreg.REG_SZ, self._get_startup_command())
                self.tray.showMessage("QuickFind", "Windows başlangıcına eklendi", QSystemTrayIcon.Information, 2000)
            else:
                try:
                    winreg.DeleteValue(key, self.STARTUP_NAME)
                    self.tray.showMessage("QuickFind", "Başlangıçtan kaldırıldı", QSystemTrayIcon.Information, 2000)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self.tray.showMessage("QuickFind", f"Hata: {e}", QSystemTrayIcon.Warning, 3000)

    # ─── Quit ─────────────────────────────────────────────

    def _quit(self):
        self._stop_watcher()
        self.db.close()
        self.tray.hide()
        self.app.quit()


def is_already_running():
    """Başka bir QuickFind service instance çalışıyor mu kontrol et"""
    import ctypes
    # Mutex oluştur — zaten varsa sahipliğini almaya çalış
    mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "QuickFindServiceMutex_v2")
    last_err = ctypes.windll.kernel32.GetLastError()
    if last_err == 183:  # ERROR_ALREADY_EXISTS
        # Gerçekten çalışan bir process var mı kontrol et
        try:
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/FO", "CSV"],
                capture_output=True, text=True, timeout=5
            )
            # Kendi PID'imiz hariç kaç pythonw var?
            lines = [l for l in result.stdout.strip().split("\n") if "pythonw" in l.lower()]
            if len(lines) > 1:
                # Birden fazla pythonw var, muhtemelen biri zaten servis
                return True
        except Exception:
            pass
        # Emin olamadık, çalışmaya devam et
        return False
    # Mutex bize ait, tek instance'ız
    # Mutex'i global'de tut ki GC silmesin
    is_already_running._mutex = mutex
    return False


def main():
    if is_already_running():
        sys.exit(0)

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Tray'de kalmaya devam et
    app.setStyle("Fusion")

    service = QuickFindService(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
