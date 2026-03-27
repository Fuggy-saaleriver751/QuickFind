"""Generate and cache thumbnails for image and PDF files."""

import hashlib
import os
import shutil
from threading import Lock

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
PDF_EXTENSIONS = {".pdf"}


class ThumbnailCache:
    """Thread-safe thumbnail generator with disk caching."""

    def __init__(self, cache_dir: str) -> None:
        self._cache_dir = cache_dir
        self._lock = Lock()
        os.makedirs(cache_dir, exist_ok=True)

    def _cache_key(self, path: str, mtime: float) -> str:
        """Generate cache key: first 16 chars of sha256(path + mtime) + .png."""
        raw = f"{path}{mtime}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16] + ".png"

    def _cache_path(self, key: str) -> str:
        return os.path.join(self._cache_dir, key)

    def get_thumbnail(self, path: str, size: int = 200) -> QPixmap | None:
        """Return a cached or newly generated thumbnail QPixmap, or None on failure."""
        try:
            if not os.path.isfile(path):
                return None

            mtime = os.path.getmtime(path)
            key = self._cache_key(path, mtime)
            cached = self._cache_path(key)

            # Check cache first (read is safe without lock)
            if os.path.isfile(cached):
                px = QPixmap(cached)
                if not px.isNull():
                    return px

            # Generate under lock
            with self._lock:
                # Double-check after acquiring lock
                if os.path.isfile(cached):
                    px = QPixmap(cached)
                    if not px.isNull():
                        return px

                ext = os.path.splitext(path)[1].lower()
                pixmap = None

                if ext in IMAGE_EXTENSIONS:
                    pixmap = self._generate_image_thumbnail(path, size)
                elif ext in PDF_EXTENSIONS:
                    pixmap = self._generate_pdf_thumbnail(path, size)

                if pixmap is not None and not pixmap.isNull():
                    pixmap.save(cached, "PNG")
                    return pixmap

            return None
        except Exception:
            return None

    def _generate_image_thumbnail(self, path: str, size: int) -> QPixmap | None:
        """Load an image and scale it to a thumbnail."""
        try:
            px = QPixmap(path)
            if px.isNull():
                return None
            return px.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
        except Exception:
            return None

    def _generate_pdf_thumbnail(self, path: str, size: int) -> QPixmap | None:
        """Render page 0 of a PDF to a thumbnail using PyMuPDF (fitz)."""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(path)
            if doc.page_count == 0:
                doc.close()
                return None

            page = doc.load_page(0)
            # Render at 2x resolution then scale down for quality
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            doc.close()

            # Convert fitz pixmap to QImage then QPixmap
            img = QImage(pix.samples, pix.width, pix.height,
                         pix.stride, QImage.Format.Format_RGB888)
            px = QPixmap.fromImage(img)
            if px.isNull():
                return None
            return px.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
        except Exception:
            return None

    def clear_cache(self) -> None:
        """Delete all cached thumbnails."""
        with self._lock:
            try:
                shutil.rmtree(self._cache_dir, ignore_errors=True)
                os.makedirs(self._cache_dir, exist_ok=True)
            except Exception:
                pass

    def get_cache_size_mb(self) -> float:
        """Return total size of cached thumbnails in megabytes."""
        try:
            total = 0
            for entry in os.scandir(self._cache_dir):
                if entry.is_file():
                    total += entry.stat().st_size
            return total / (1024 * 1024)
        except Exception:
            return 0.0
