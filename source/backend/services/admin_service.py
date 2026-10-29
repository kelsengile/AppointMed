"""Admin operations: users, schedules, rooms, clinic settings, and audit logs."""

from __future__ import annotations

from typing import Any

from backend.core.database import Database, Executor, Row, database
from backend.core.exceptions import ConflictError, DuplicateEntryError, NotFoundError, PermissionDeniedError, ValidationFailedError
from backend.core.security import hash_password
from backend.core.utils import blank_to_none, to_money
from backend.models.domain import User
from backend.repositories.system_repository import AuditRepository, RoomRepository, SettingsRepository
from backend.repositories.user_repository import ScheduleRepository, UserRepository
from backend.schemas.api import ScheduleBlock, UserCreate, UserUpdate

_BOOL_VALUES = {"true", "false"}


class AdminService:
    """Management features that only administrators can reach."""

    def __init__(self, db: Database = database) -> None:
        self._db = db

    # ------------------------------------------------------------ users
    @staticmethod
    def _assignment(users: UserRepository, role: str, doctor_id: int | None) -> int | None:
        """Nurses must support an active doctor; other roles never have one."""
        if role != "nurse":
            return None
        if doctor_id is None:
            raise ValidationFailedError("Choose the doctor this nurse supports.")
        doctor = users.get(doctor_id)
        if doctor is None or doctor["role"] != "doctor" or not doctor["is_active"]:
            raise ValidationFailedError("The chosen doctor is not available.")
        return doctor_id

    def list_users(self, role: str | None, term: str | None) -> list[Row]:
        return UserRepository(self._db).list_users(role, blank_to_none(term))

    def create_user(self, admin: User, data: UserCreate) -> Row:
        with self._db.transaction() as tx:
            users = UserRepository(tx)
            assigned = self._assignment(users, data.role, data.assigned_doctor_id)
            try:
                new_id = users.create(
                    {
                        "username": data.username, "password_hash": hash_password(data.password), "full_name": data.full_name,
                        "role": data.role, "email": blank_to_none(data.email),
                        "specialization": blank_to_none(data.specialization) if data.role == "doctor" else None,
                        "assigned_doctor_id": assigned, "is_active": 1,
                    }
                )
            except DuplicateEntryError as exc:
                raise ConflictError("That username is already taken.") from exc
            AuditRepository(tx).record(admin.id, "CREATE_USER", "users", new_id, f"Created {data.role} account {data.username}")
        return UserRepository(self._db).get_detail(new_id)  # type: ignore[return-value]

    def update_user(self, admin: User, user_id: int, data: UserUpdate) -> Row:
        with self._db.transaction() as tx:
            users = UserRepository(tx)
            row = users.get(user_id)
            if row is None:
                raise NotFoundError("User not found.")
            users.update(
                user_id,
                {
                    "full_name": data.full_name, "email": blank_to_none(data.email),
                    "specialization": blank_to_none(data.specialization) if row["role"] == "doctor" else None,
                    "assigned_doctor_id": self._assignment(users, row["role"], data.assigned_doctor_id),
                },
            )
            AuditRepository(tx).record(admin.id, "UPDATE_USER", "users", user_id, f"Edited account {row['username']}")
        return UserRepository(self._db).get_detail(user_id)  # type: ignore[return-value]

    def set_active(self, admin: User, user_id: int, active: bool) -> Row:
        """Deactivate instead of deleting, so history stays intact. Admins cannot lock themselves out."""
        with self._db.transaction() as tx:
            users = UserRepository(tx)
            row = users.get(user_id)
            if row is None:
                raise NotFoundError("User not found.")
            if user_id == admin.id and not active:
                raise PermissionDeniedError("You cannot deactivate your own account.")
            users.update(user_id, {"is_active": 1 if active else 0})
            AuditRepository(tx).record(
                admin.id, "ACTIVATE_USER" if active else "DEACTIVATE_USER", "users", user_id, f"Account {row['username']}"
            )
        return UserRepository(self._db).get_detail(user_id)  # type: ignore[return-value]

    def reset_password(self, admin: User, user_id: int, new_password: str) -> None:
        with self._db.transaction() as tx:
            users = UserRepository(tx)
            row = users.get(user_id)
            if row is None:
                raise NotFoundError("User not found.")
            users.set_password(user_id, hash_password(new_password))
            AuditRepository(tx).record(admin.id, "RESET_PASSWORD", "users", user_id, f"Reset password for {row['username']}")

    # ------------------------------------------------------------ schedules
    def get_schedule(self, doctor_id: int) -> list[Row]:
        self._require_doctor(UserRepository(self._db), doctor_id)
        return ScheduleRepository(self._db).blocks_for_doctor(doctor_id)

    @staticmethod
    def _require_doctor(users: UserRepository, doctor_id: int) -> Row:
        row = users.get(doctor_id)
        if row is None or row["role"] != "doctor":
            raise NotFoundError("Doctor not found.")
        return row

    def replace_schedule(self, admin: User, doctor_id: int, blocks: list[ScheduleBlock]) -> list[Row]:
        """Validate (end after start, no overlaps) and replace a doctor's weekly schedule."""
        for block in blocks:
            if block.end_time <= block.start_time:
                raise ValidationFailedError("Each block must end after it starts.")
            minutes = (block.end_time.hour * 60 + block.end_time.minute) - (block.start_time.hour * 60 + block.start_time.minute)
            if minutes < block.slot_minutes:
                raise ValidationFailedError("A block must be at least one slot long.")
        ordered = sorted(blocks, key=lambda b: (b.weekday, b.start_time))
        for first, second in zip(ordered, ordered[1:]):
            if first.weekday == second.weekday and second.start_time < first.end_time:
                raise ValidationFailedError("Schedule blocks on the same day cannot overlap.")
        with self._db.transaction() as tx:
            self._require_doctor(UserRepository(tx), doctor_id)
            ScheduleRepository(tx).replace(
                doctor_id,
                [{"weekday": b.weekday, "start_time": b.start_time, "end_time": b.end_time, "slot_minutes": b.slot_minutes} for b in ordered],
            )
            AuditRepository(tx).record(admin.id, "UPDATE_SCHEDULE", "users", doctor_id, f"{len(ordered)} schedule blocks saved")
        return ScheduleRepository(self._db).blocks_for_doctor(doctor_id)

    def doctors(self) -> list[Row]:
        return UserRepository(self._db).active_doctors()

    # ------------------------------------------------------------ rooms
    def list_rooms(self) -> list[Row]:
        return RoomRepository(self._db).list_with_occupant()

    def create_room(self, admin: User, name: str, status: str) -> list[Row]:
        with self._db.transaction() as tx:
            try:
                new_id = RoomRepository(tx).create({"room_name": name, "status": status, "updated_by": admin.id})
            except DuplicateEntryError as exc:
                raise ConflictError("A room with that name already exists.") from exc
            AuditRepository(tx).record(admin.id, "CREATE_ROOM", "rooms", new_id, name)
        return self.list_rooms()

    def update_room(self, admin: User, room_id: int, name: str, status: str) -> list[Row]:
        with self._db.transaction() as tx:
            rooms = RoomRepository(tx)
            if rooms.get(room_id) is None:
                raise NotFoundError("Room not found.")
            try:
                rooms.update(room_id, {"room_name": name, "status": status, "updated_by": admin.id})
            except DuplicateEntryError as exc:
                raise ConflictError("A room with that name already exists.") from exc
            AuditRepository(tx).record(admin.id, "UPDATE_ROOM", "rooms", room_id, f"{name} ({status})")
        return self.list_rooms()

    def delete_room(self, admin: User, room_id: int) -> list[Row]:
        with self._db.transaction() as tx:
            rooms = RoomRepository(tx)
            room = rooms.get(room_id)
            if room is None:
                raise NotFoundError("Room not found.")
            if rooms.in_use(room_id):
                raise ConflictError("This room appears in appointment history. Set it to Maintenance instead of deleting it.")
            rooms.delete(room_id)
            AuditRepository(tx).record(admin.id, "DELETE_ROOM", "rooms", room_id, room["room_name"])
        return self.list_rooms()

    # ------------------------------------------------------------ settings
    @staticmethod
    def _validate_setting(key: str, value: str) -> str:
        """Check one setting value and return its cleaned form."""
        value = value.strip()
        if key in ("clinic_name", "clinic_address"):
            if not value or len(value) > (100 if key == "clinic_name" else 255):
                raise ValidationFailedError(f"{key.replace('_', ' ').title()} is required and must be short enough.")
            return value
        if key == "consultation_fee":
            try:
                fee = to_money(value)
            except Exception as exc:
                raise ValidationFailedError("The consultation fee must be a number.") from exc
            if fee < 0 or fee > 1_000_000:
                raise ValidationFailedError("The consultation fee must be between 0 and 1,000,000.")
            return str(fee)
        if key in ("default_slot_minutes", "booking_window_days"):
            low, high = (5, 120) if key == "default_slot_minutes" else (1, 365)
            # isascii() stops characters such as "²" that pass isdigit() but crash int().
            if not (value.isascii() and value.isdigit()) or not low <= int(value) <= high:
                raise ValidationFailedError(f"{key.replace('_', ' ').title()} must be a whole number from {low} to {high}.")
            return str(int(value))
        if key == "online_booking_enabled":
            if value.lower() not in _BOOL_VALUES:
                raise ValidationFailedError("Online booking must be true or false.")
            return value.lower()
        raise ValidationFailedError(f"Unknown setting: {key}")

    def list_settings(self) -> list[Row]:
        return SettingsRepository(self._db).all_rows()

    def update_settings(self, admin: User, values: dict[str, str]) -> list[Row]:
        """Validate everything first, then save all values together."""
        cleaned = {key: self._validate_setting(key, value) for key, value in values.items()}
        with self._db.transaction() as tx:
            settings = SettingsRepository(tx)
            for key, value in cleaned.items():
                settings.upsert(key, value, admin.id)
                AuditRepository(tx).record(admin.id, "UPDATE_SETTING", "clinic_settings", None, f"Changed {key} to {value}"[:255])
        return self.list_settings()

    # ------------------------------------------------------------ audit
    def audit(self, term: str | None, action: str | None, limit: int, offset: int) -> dict[str, Any]:
        return AuditRepository(self._db).search(blank_to_none(term), blank_to_none(action), limit, offset)


__all__ = ["AdminService", "Executor"]