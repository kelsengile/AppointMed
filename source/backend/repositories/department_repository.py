"""Clinical departments shown on the public front page and managed by the admin."""

from __future__ import annotations

from backend.core.database import Row

from .base_repository import BaseRepository


class DepartmentRepository(BaseRepository):
    """Queries for the departments table."""

    table = "departments"
    columns = ("name", "description", "icon", "is_featured", "is_active", "sort_order")

    def _list(self, where: str) -> list[Row]:
        rows = self._db.fetch_all(
            f"""
            SELECT d.id, d.name, d.description, d.icon, d.is_featured, d.is_active, d.sort_order,
                   (SELECT COUNT(*) FROM users u
                    WHERE u.role = 'doctor' AND u.is_active = 1 AND u.specialization = d.name) AS doctor_count
            FROM departments d
            {where}
            ORDER BY d.is_featured DESC, d.sort_order, d.name
            """
        )
        for row in rows:
            row["is_featured"] = bool(row["is_featured"])
            row["is_active"] = bool(row["is_active"])
            row["doctor_count"] = int(row["doctor_count"])
        return rows

    def list_active(self) -> list[Row]:
        """Active departments (featured first) with the number of active doctors in each.

        A doctor belongs to a department when their specialization equals the department name.
        """
        return self._list("WHERE d.is_active = 1")

    def list_all(self) -> list[Row]:
        """Every department, including hidden ones (admin screen)."""
        return self._list("")

    def find_by_name(self, name: str) -> Row | None:
        """The department with this name (the stored spelling), or None."""
        return self._db.fetch_one("SELECT id, name FROM departments WHERE name = %s LIMIT 1", (name,))

    def doctors_in(self, name: str) -> int:
        """Doctors (active or not) whose specialization is this department."""
        row = self._db.fetch_one("SELECT COUNT(*) AS n FROM users WHERE role = 'doctor' AND specialization = %s", (name,))
        return int(row["n"]) if row else 0

    def rename_specialization(self, old: str, new: str) -> int:
        """Keep doctors attached to a department when it is renamed."""
        return self._db.update("UPDATE users SET specialization = %s WHERE role = 'doctor' AND specialization = %s", (new, old))