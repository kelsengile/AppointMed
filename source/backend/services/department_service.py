"""Departments: the public list for the front page, and admin management (text, icon, order)."""

from __future__ import annotations

import base64
import binascii
import re
from datetime import datetime

from backend.core.database import Database, Row, database
from backend.core.exceptions import ConflictError, DuplicateEntryError, NotFoundError, ValidationFailedError
from backend.models.domain import User
from backend.repositories.department_repository import DepartmentRepository
from backend.repositories.site_repository import SiteContentRepository
from backend.repositories.system_repository import AuditRepository
from backend.schemas.api import DepartmentIn
from backend.services.auth_service import _detect_mime

_MAX_ICON_BYTES = 150_000


def _icon_key(department_id: int) -> str:
    return f"dept_icon_{department_id}"  # icons are stored in site_content (it holds large text)


class DepartmentService:
    """Public reads, and admin-only changes."""

    def __init__(self, db: Database = database) -> None:
        self._db = db

    # ------------------------------------------------------------ public
    def list_public(self) -> list[Row]:
        return DepartmentRepository(self._db).list_active()

    def icon(self, department_id: int) -> tuple[bytes, str]:
        value = SiteContentRepository(self._db).get_value(_icon_key(department_id))
        match = re.match(r"^data:(image/[a-z]+);base64,(.+)$", value or "", re.DOTALL)
        if not match:
            raise NotFoundError("No icon has been set.")
        return base64.b64decode(match.group(2)), match.group(1)

    # ------------------------------------------------------------ admin
    def list_admin(self) -> list[Row]:
        return DepartmentRepository(self._db).list_all()

    @staticmethod
    def _columns(data: DepartmentIn) -> dict:
        return {
            "name": data.name,
            "description": data.description,
            "is_featured": 1 if data.is_featured else 0,
            "is_active": 1 if data.is_active else 0,
            "sort_order": data.sort_order,
        }

    def create(self, admin: User, data: DepartmentIn) -> list[Row]:
        with self._db.transaction() as tx:
            try:
                new_id = DepartmentRepository(tx).create(self._columns(data))
            except DuplicateEntryError as exc:
                raise ConflictError("A department with that name already exists.") from exc
            AuditRepository(tx).record(admin.id, "CREATE_DEPARTMENT", "departments", new_id, data.name)
        return self.list_admin()

    def update(self, admin: User, department_id: int, data: DepartmentIn) -> list[Row]:
        with self._db.transaction() as tx:
            departments = DepartmentRepository(tx)
            old = departments.get(department_id)
            if old is None:
                raise NotFoundError("Department not found.")
            try:
                departments.update(department_id, self._columns(data))
            except DuplicateEntryError as exc:
                raise ConflictError("A department with that name already exists.") from exc
            if old["name"] != data.name:
                departments.rename_specialization(old["name"], data.name)  # doctors follow the rename
            AuditRepository(tx).record(admin.id, "UPDATE_DEPARTMENT", "departments", department_id, data.name)
        return self.list_admin()

    def delete(self, admin: User, department_id: int) -> list[Row]:
        with self._db.transaction() as tx:
            departments = DepartmentRepository(tx)
            row = departments.get(department_id)
            if row is None:
                raise NotFoundError("Department not found.")
            count = departments.doctors_in(row["name"])
            if count:
                raise ConflictError(f"{count} doctor(s) still use this department. Change their specialization on the Users page first.")
            departments.delete(department_id)
            SiteContentRepository(tx).remove(_icon_key(department_id))
            AuditRepository(tx).record(admin.id, "DELETE_DEPARTMENT", "departments", department_id, row["name"])
        return self.list_admin()

    def set_icon(self, admin: User, department_id: int, image: str) -> list[Row]:
        match = re.match(r"^data:image/(?:png|jpeg|jpg|webp);base64,(.+)$", image, re.DOTALL)
        if not match:
            raise ValidationFailedError("Upload a PNG, JPEG or WebP image.")
        try:
            raw = base64.b64decode(match.group(1), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValidationFailedError("The image could not be read.") from exc
        if len(raw) > _MAX_ICON_BYTES:
            raise ValidationFailedError("The icon is too large. Choose a smaller one.")
        mime = _detect_mime(raw)
        if mime is None:
            raise ValidationFailedError("Upload a PNG, JPEG or WebP image.")
        with self._db.transaction() as tx:
            departments = DepartmentRepository(tx)
            if departments.get(department_id) is None:
                raise NotFoundError("Department not found.")
            SiteContentRepository(tx).upsert(_icon_key(department_id), f"data:{mime};base64,{base64.b64encode(raw).decode()}", admin.id)
            version = int(datetime.now().timestamp())
            departments.update(department_id, {"icon": f"/api/public/department-icon/{department_id}?v={version}"})
            AuditRepository(tx).record(admin.id, "UPDATE_DEPARTMENT_ICON", "departments", department_id, "Changed the icon")
        return self.list_admin()

    def remove_icon(self, admin: User, department_id: int) -> list[Row]:
        with self._db.transaction() as tx:
            departments = DepartmentRepository(tx)
            if departments.get(department_id) is None:
                raise NotFoundError("Department not found.")
            SiteContentRepository(tx).remove(_icon_key(department_id))
            departments.update(department_id, {"icon": None})
            AuditRepository(tx).record(admin.id, "REMOVE_DEPARTMENT_ICON", "departments", department_id, "Removed the icon")
        return self.list_admin()