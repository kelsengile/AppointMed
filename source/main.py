"""AppointMed backend entry point.

Run from the `source` folder:
    uvicorn main:app --reload

Then open http://127.0.0.1:8000 (status page) or http://127.0.0.1:8000/docs (API docs).
"""

import os
from datetime import datetime, timezone
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from mysql.connector import Error as MySQLError

APP_NAME = "AppointMed"
APP_VERSION = "0.1.0"

load_dotenv(Path(__file__).resolve().parent / ".env")


class Settings:
    """Reads configuration from environment variables (loaded from .env)."""

    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", "3306"))
        self.db_name = os.getenv("DB_NAME", "appointmed")
        self.db_user = os.getenv("DB_USER", "appointmed_user")
        self.db_password = os.getenv("DB_PASSWORD", "")
        origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        self.cors_origins = [o.strip() for o in origins.split(",") if o.strip()]


class Database:
    """Thin wrapper around MySQL Connector/Python."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def connect(self):
        return mysql.connector.connect(
            host=self._settings.db_host,
            port=self._settings.db_port,
            database=self._settings.db_name,
            user=self._settings.db_user,
            password=self._settings.db_password,
            connection_timeout=3,
        )

    def is_reachable(self) -> bool:
        """True if the app can connect and run a trivial query."""
        try:
            connection = self.connect()
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            finally:
                connection.close()
            return True
        except MySQLError:
            return False


settings = Settings()
database = Database(settings)

app = FastAPI(title=f"{APP_NAME} API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    """Confirms the backend is running."""
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "environment": settings.app_env,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/health/db")
def health_db() -> dict:
    """Confirms the backend can reach MySQL. Never returns error details."""
    return {"connected": database.is_reachable(), "database": settings.db_name}


STATUS_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AppointMed</title>
  <style>
    :root { --bg:#f6f8f8; --fg:#12302f; --muted:#5b6f6e; --card:#ffffff; --line:#d5e0df; --ok:#0f7b6c; --bad:#b3402f; }
    @media (prefers-color-scheme: dark) {
      :root { --bg:#0e1a1a; --fg:#e4f0ef; --muted:#93aaa8; --card:#152524; --line:#27403e; --ok:#4cc3b0; --bad:#ec8a77; }
    }
    * { box-sizing: border-box; }
    body { margin:0; min-height:100vh; display:grid; place-items:center; padding:24px;
           background:var(--bg); color:var(--fg); font-family:system-ui, -apple-system, "Segoe UI", sans-serif; }
    main { width:100%; max-width:30rem; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:28px; }
    h1 { margin:0 0 4px; font-size:1.5rem; }
    p { margin:0 0 20px; color:var(--muted); line-height:1.5; }
    ul { list-style:none; margin:0 0 20px; padding:0; }
    li { display:flex; justify-content:space-between; padding:10px 0; border-top:1px solid var(--line); }
    .ok { color:var(--ok); font-weight:600; } .bad { color:var(--bad); font-weight:600; }
    a { color:var(--ok); }
  </style>
</head>
<body>
  <main>
    <h1>AppointMed is running</h1>
    <p>The backend responded. This page is a placeholder for the public booking website.</p>
    <ul>
      <li><span>API</span><span id="api" class="bad">Checking...</span></li>
      <li><span>Database</span><span id="db" class="bad">Checking...</span></li>
    </ul>
    <a href="/docs">Open API docs</a>
  </main>
  <script>
    function show(id, ok, yes, no) {
      var el = document.getElementById(id);
      el.textContent = ok ? yes : no;
      el.className = ok ? "ok" : "bad";
    }
    fetch("/api/health").then(function (r) { return r.json(); })
      .then(function (d) { show("api", d.status === "ok", "Online", "Problem"); })
      .catch(function () { show("api", false, "", "Offline"); });
    fetch("/api/health/db").then(function (r) { return r.json(); })
      .then(function (d) { show("db", d.connected, "Connected", "Not connected. Check source/.env and that MySQL is running."); })
      .catch(function () { show("db", false, "", "Unknown"); });
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def status_page() -> str:
    return STATUS_PAGE
