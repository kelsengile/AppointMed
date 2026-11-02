"""Administrator endpoints for the Database page. Mounted under /api/admin/database."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from backend.core.security import require_feature
from backend.models.domain import User
from backend.schemas.database import RowValues, SqlRequest
from backend.services.database_service import DatabaseService

router = APIRouter(prefix="/database", tags=["admin-database"])
service = DatabaseService()


@router.get("/tables")
def tables(user: User = Depends(require_feature("database"))) -> list:
    return service.tables()


@router.get("/tables/{table}")
def table_page(
    table: str, q: str | None = None, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0),
    user: User = Depends(require_feature("database")),
) -> dict:
    return service.table(table, q, limit, offset)


@router.post("/tables/{table}/rows", status_code=201)
def insert_row(table: str, body: RowValues, user: User = Depends(require_feature("database"))) -> dict:
    return service.insert_row(user, table, body.values)


@router.put("/tables/{table}/rows/{key}")
def update_row(table: str, key: str, body: RowValues, user: User = Depends(require_feature("database"))) -> dict:
    return service.update_row(user, table, key, body.values)


@router.delete("/tables/{table}/rows/{key}")
def delete_row(table: str, key: str, user: User = Depends(require_feature("database"))) -> dict:
    return service.delete_row(user, table, key)


@router.post("/query")
def run_query(body: SqlRequest, user: User = Depends(require_feature("database"))) -> dict:
    return service.run_sql(user, body.sql)


@router.get("/backup")
def backup(user: User = Depends(require_feature("database"))) -> Response:
    """Structure and current data of every table, as a downloadable .sql file."""
    filename, content = service.backup(user)
    return Response(
        content=content.encode("utf-8"),
        media_type="application/sql",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )