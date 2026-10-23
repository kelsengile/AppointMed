"""Patient records."""

from __future__ import annotations

from datetime import date

from backend.core.database import Row

from .base_repository import BaseRepository

_SCOPE = "(p.doctor_id = %s OR EXISTS (SELECT 1 FROM appointments a WHERE a.patient_id = p.id AND a.doctor_id = %s))"


class PatientRepository(BaseRepository):
    """Queries for patients. 'Scope' means patients linked to one doctor."""

    table = "patients"
    columns = ("full_name", "birthdate", "sex", "contact_number", "email", "address", "condition_summary", "doctor_id")

    def search(self, doctor_id: int, term: str | None = None, limit: int = 300) -> list[Row]:
        """Patients of one doctor, with their number of examinations, filtered by name/contact/email."""
        sql = (
            "SELECT p.*, (SELECT COUNT(*) FROM examinations e WHERE e.patient_id = p.id) AS visit_count "
            f"FROM patients p WHERE {_SCOPE}"
        )
        params: list = [doctor_id, doctor_id]
        if term:
            sql += " AND (p.full_name LIKE %s OR p.contact_number LIKE %s OR p.email LIKE %s)"
            params += [f"%{term}%"] * 3
        sql += " ORDER BY p.full_name LIMIT %s"
        params.append(limit)
        return self._db.fetch_all(sql, params)

    def get_scoped(self, patient_id: int, doctor_id: int) -> Row | None:
        """One patient, but only if linked to this doctor."""
        return self._db.fetch_one(
            f"SELECT p.* FROM patients p WHERE p.id = %s AND {_SCOPE}", (patient_id, doctor_id, doctor_id)
        )

    def find_match(self, full_name: str, birthdate: date | None) -> Row | None:
        """An existing patient with the same name and birthdate (NULL-safe comparison)."""
        return self._db.fetch_one(
            "SELECT * FROM patients WHERE LOWER(full_name) = LOWER(%s) AND birthdate <=> %s LIMIT 1", (full_name, birthdate)
        )

    def has_history(self, patient_id: int) -> bool:
        """True when the patient has any appointment on record."""
        row = self._db.fetch_one("SELECT COUNT(*) AS n FROM appointments WHERE patient_id = %s", (patient_id,))
        return bool(row and row["n"])