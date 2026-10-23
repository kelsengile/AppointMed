"""Patient record management (add, edit, delete, search, history)."""

from __future__ import annotations

from backend.core.database import Database, Row, database
from backend.core.exceptions import ConflictError, NotFoundError
from backend.core.utils import blank_to_none
from backend.models.domain import User
from backend.repositories.patient_repository import PatientRepository
from backend.repositories.system_repository import AuditRepository
from backend.schemas.api import PatientIn


class PatientService:
    """Patients are scoped to the user's doctor."""

    def __init__(self, db: Database = database) -> None:
        self._db = db
        self._patients = PatientRepository(db)

    @staticmethod
    def _columns(data: PatientIn) -> dict:
        return {
            "full_name": data.full_name,
            "birthdate": data.birthdate,
            "sex": data.sex,
            "contact_number": blank_to_none(data.contact_number),
            "email": blank_to_none(data.email),
            "address": blank_to_none(data.address),
            "condition_summary": blank_to_none(data.condition_summary),
        }

    def search(self, user: User, term: str | None) -> list[Row]:
        return self._patients.search(user.scope_doctor_id, blank_to_none(term))

    def _load(self, user: User, patient_id: int) -> Row:
        row = self._patients.get_scoped(patient_id, user.scope_doctor_id)
        if row is None:
            raise NotFoundError("Patient not found.")
        return row

    def ensure_access(self, user: User, patient_id: int) -> None:
        """Raise NotFoundError when the patient is outside the user's scope."""
        self._load(user, patient_id)

    def create(self, user: User, data: PatientIn) -> Row:
        doctor_id = user.scope_doctor_id
        existing = self._patients.find_match(data.full_name, data.birthdate)
        if existing:
            raise ConflictError("A patient with this name and birthdate already exists.")
        new_id = self._patients.create({**self._columns(data), "doctor_id": doctor_id})
        AuditRepository(self._db).record(user.id, "CREATE_PATIENT", "patients", new_id, "Added a patient record")
        return self._patients.search(doctor_id, data.full_name)[0] if False else self._load(user, new_id)

    def update(self, user: User, patient_id: int, data: PatientIn) -> Row:
        self._load(user, patient_id)
        self._patients.update(patient_id, self._columns(data))
        AuditRepository(self._db).record(user.id, "UPDATE_PATIENT", "patients", patient_id, "Edited a patient record")
        return self._load(user, patient_id)

    def delete(self, user: User, patient_id: int) -> None:
        """Only patients without any appointment can be removed, to protect clinical history."""
        self._load(user, patient_id)
        if self._patients.has_history(patient_id):
            raise ConflictError("This patient has appointments on record, so the record cannot be deleted.")
        self._patients.delete(patient_id)
        AuditRepository(self._db).record(user.id, "DELETE_PATIENT", "patients", patient_id, "Deleted a patient record")
        