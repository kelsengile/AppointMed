"""Business logic for connecting the backend to a MySQL server."""
from backend.core.connection import database
from backend.schemas.server import ServerConnectRequest, ServerStatus


class ServerService:
    def connect(self, request: ServerConnectRequest) -> ServerStatus:
        database.connect(
            host=request.host,
            port=request.port,
            user=request.user,
            password=request.password,
        )
        return self.status()

    def disconnect(self) -> ServerStatus:
        database.disconnect()
        return self.status()

    def status(self) -> ServerStatus:
        config = database.config
        if config is None:
            return ServerStatus(connected=False)
        return ServerStatus(
            connected=True,
            host=config.host,
            port=config.port,
            user=config.user,
            database=config.database,
        )