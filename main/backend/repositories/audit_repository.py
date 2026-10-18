"""All SQL for the audit_logs table (append-only)."""
from backend.core.connection import database


class AuditRepository:
    def add(
        self,
        user_id: int | None,
        action: str,
        entity: str | None = None,
        entity_id: int | None = None,
        details: str | None = None,
    ) -> None:
        connection = database.get_connection()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO audit_logs (user_id, action, entity, entity_id, details) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (user_id, action, entity, entity_id, details),
                )
                connection.commit()
            finally:
                cursor.close()
        finally:
            connection.close()