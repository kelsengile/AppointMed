from fastapi import APIRouter

from backend.schemas.server import ServerConnectRequest, ServerStatus
from backend.services.server_service import ServerService

router = APIRouter(prefix="/server", tags=["server"])


@router.get("/status", response_model=ServerStatus)
def get_status() -> ServerStatus:
    return ServerService().status()


@router.post("/connect", response_model=ServerStatus)
def connect(request: ServerConnectRequest) -> ServerStatus:
    return ServerService().connect(request)


@router.post("/disconnect", response_model=ServerStatus)
def disconnect() -> ServerStatus:
    return ServerService().disconnect()