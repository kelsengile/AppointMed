"""Editable website content: texts, links, and the logo and hero pictures."""

from __future__ import annotations

from backend.core.database import Row

from .base_repository import BaseRepository

IMAGE_KEYS = ("logo_image", "hero_image")


class SiteContentRepository(BaseRepository):
    """Key/value rows. Pictures are stored as data URLs in the same table."""

    table = "site_content"
    columns = ("content_key", "content_value", "updated_by")

    def texts(self) -> dict[str, str]:
        rows = self._db.fetch_all(
            "SELECT content_key, content_value FROM site_content "
            "WHERE content_key NOT IN (%s, %s) AND LEFT(content_key, 10) <> 'dept_icon_'",
            IMAGE_KEYS,
        )
        return {r["content_key"]: r["content_value"] for r in rows}

    def image_keys(self) -> set[str]:
        rows = self._db.fetch_all("SELECT content_key FROM site_content WHERE content_key IN (%s, %s)", IMAGE_KEYS)
        return {r["content_key"] for r in rows}

    def get_value(self, key: str) -> str | None:
        row = self._db.fetch_one("SELECT content_value FROM site_content WHERE content_key = %s", (key,))
        return row["content_value"] if row else None

    def version(self) -> str:
        """Changes whenever anything is saved or removed (used to refresh the browser's cached pictures)."""
        row: Row | None = self._db.fetch_one(
            "SELECT COUNT(*) AS n, COALESCE(UNIX_TIMESTAMP(MAX(updated_at)), 0) AS v FROM site_content"
        )
        return f"{int(row['n'])}-{int(row['v'])}" if row else "0"

    def upsert(self, key: str, value: str, user_id: int | None) -> None:
        self._db.execute(
            "INSERT INTO site_content (content_key, content_value, updated_by) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE content_value = VALUES(content_value), updated_by = VALUES(updated_by)",
            (key, value, user_id),
        )

    def remove(self, key: str) -> None:
        self._db.update("DELETE FROM site_content WHERE content_key = %s", (key,))