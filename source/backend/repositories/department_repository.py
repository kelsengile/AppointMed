"""Clinical departments shown on the public front page."""

from __future__ import annotations

from backend.core.database import Row

from .base_repository import BaseRepository


class DepartmentRepository(BaseRepository):
    """Queries for the departments table."""

    table = "departments"
    columns = ("name", "description", "icon", "is_featured", "is_active", "sort_order")

    def list_active(self) -> list[Row]:
        """Active departments (featured first) with the number of active doctors in each.

        A doctor belongs to a department when their specialization equals the department name.
        """
        rows = self._db.fetch_all(
            """
            SELECT d.id, d.name, d.description, d.icon, d.is_featured,
                   (SELECT COUNT(*) FROM users u
                    WHERE u.role = 'doctor' AND u.is_active = 1 AND u.specialization = d.name) AS doctor_count
            FROM departments d
            WHERE d.is_active = 1
            ORDER BY d.is_featured DESC, d.sort_order, d.name
            """
        )
        for row in rows:
            row["is_featured"] = bool(row["is_featured"])
            row["doctor_count"] = int(row["doctor_count"])
        return rows