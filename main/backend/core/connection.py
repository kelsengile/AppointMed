"""MySQL connection handling. Repositories get their connections from here."""
import os
import threading
from dataclasses import dataclass

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection

from backend.exceptions.app_exceptions import ServerConnectionError, ServerNotConnectedError

ConnectionType = MySQLConnectionAbstract | PooledMySQLConnection

@dataclass(frozen=True)
class ServerConfig:
    """Details used to reach the MySQL server. Kept in memory only."""

    host: str
    port: int
    user: str
    password: str
    database: str


class DatabaseManager:
    """Holds the active server connection details chosen on the login screen."""

    def __init__(self) -> None:
        self._config: ServerConfig | None = None
        self._lock = threading.Lock()

    @property
    def config(self) -> ServerConfig | None:
        return self._config

    @property
    def is_connected(self) -> bool:
        return self._config is not None

    def connect(self, host: str, port: int, user: str, password: str) -> ServerConfig:
        """Test the details against MySQL and remember them if they work."""
        config = ServerConfig(
            host=host,
            port=port,
            user=user,
            password=password,
            database=os.getenv("DB_NAME", "appointmed"),
        )
        self._open(config).close()  # raises ServerConnectionError on failure
        with self._lock:
            self._config = config
        return config

    def disconnect(self) -> None:
        with self._lock:
            self._config = None

    def get_connection(self) -> ConnectionType:
        """Open a new connection using the saved details."""
        config = self._config
        if config is None:
            raise ServerNotConnectedError()
        return self._open(config)

    @staticmethod
    def _open(config: ServerConfig) -> ConnectionType:
        try:
            return mysql.connector.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                database=config.database,
                connection_timeout=5,
            )
        except mysql.connector.Error as error:
            raise ServerConnectionError(_describe(error, config)) from error


def _describe(error: mysql.connector.Error, config: ServerConfig) -> str:
    """Turn a MySQL error into a short message that does not leak internals."""
    if error.errno == 1045:
        return "Access denied. Check the server username and password."
    if error.errno == 1049:
        return f"Database '{config.database}' was not found. Load schema.sql first."
    if error.errno in (2002, 2003, 2005, 2013):
        return f"Cannot reach the MySQL server at {config.host}:{config.port}."
    return "Could not connect to the MySQL server."


# One shared instance used by the whole backend.
database = DatabaseManager()