"""Analyze folder sizes and file statistics from the database."""


class FolderAnalyzer:
    """Provides folder size analysis and file statistics."""

    def __init__(self, db) -> None:
        """Initialize with a FileDatabase instance."""
        self._db = db

    def get_top_folders(self, limit: int = 50) -> list[dict]:
        """Return top folders by total size.

        Returns list of {path, total_size, file_count} sorted by size desc.
        """
        sql = (
            "SELECT d.path, SUM(f.size), COUNT(*) "
            "FROM files f JOIN dirs d ON d.id = f.dir_id "
            "GROUP BY d.path "
            "ORDER BY SUM(f.size) DESC "
            "LIMIT ?"
        )
        try:
            cursor = self._db.conn.execute(sql, (limit,))
            return [
                {"path": row[0], "total_size": row[1] or 0, "file_count": row[2]}
                for row in cursor.fetchall()
            ]
        except Exception:
            return []

    def get_extension_stats(self) -> list[dict]:
        """Return file statistics grouped by extension.

        Returns list of {extension, total_size, file_count} sorted by count desc.
        """
        sql = (
            "SELECT extension, SUM(size), COUNT(*) "
            "FROM files "
            "GROUP BY extension "
            "ORDER BY COUNT(*) DESC "
            "LIMIT 30"
        )
        try:
            cursor = self._db.conn.execute(sql)
            return [
                {"extension": row[0] or "", "total_size": row[1] or 0, "file_count": row[2]}
                for row in cursor.fetchall()
            ]
        except Exception:
            return []

    def get_size_distribution(self) -> dict:
        """Return file count distribution by size ranges.

        Returns {range_label: count}.
        """
        ranges = [
            ("< 1 KB", 0, 1024),
            ("1-10 KB", 1024, 10 * 1024),
            ("10-100 KB", 10 * 1024, 100 * 1024),
            ("100 KB - 1 MB", 100 * 1024, 1024 * 1024),
            ("1-10 MB", 1024 * 1024, 10 * 1024 * 1024),
            ("10-100 MB", 10 * 1024 * 1024, 100 * 1024 * 1024),
            ("100 MB - 1 GB", 100 * 1024 * 1024, 1024 * 1024 * 1024),
            ("> 1 GB", 1024 * 1024 * 1024, None),
        ]

        distribution = {}
        try:
            for label, low, high in ranges:
                if high is not None:
                    sql = "SELECT COUNT(*) FROM files WHERE size >= ? AND size < ?"
                    cursor = self._db.conn.execute(sql, (low, high))
                else:
                    sql = "SELECT COUNT(*) FROM files WHERE size >= ?"
                    cursor = self._db.conn.execute(sql, (low,))
                distribution[label] = cursor.fetchone()[0]
        except Exception:
            return {}

        return distribution

    def get_timeline(self, days: int = 30) -> list[dict]:
        """Return file modification counts per day for the last N days.

        Returns list of {date, count}.
        """
        import time

        cutoff = int(time.time()) - (days * 86400)
        sql = (
            "SELECT date(modified, 'unixepoch') AS d, COUNT(*) "
            "FROM files "
            "WHERE modified >= ? "
            "GROUP BY d "
            "ORDER BY d ASC"
        )
        try:
            cursor = self._db.conn.execute(sql, (cutoff,))
            return [
                {"date": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]
        except Exception:
            return []
