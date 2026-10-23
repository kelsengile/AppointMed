"""AppointMed backend entry point.

Run from the `source` folder:
    uvicorn main:app --reload

Then open http://127.0.0.1:8000 (status page) or http://127.0.0.1:8000/docs (API docs).
"""

import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.core.config import APP_NAME, APP_VERSION, settings
from backend.core.database import database
from backend.core.exceptions import register_exception_handlers
from backend.routes.admin_routes import router as admin_router
from backend.routes.auth_routes import router as auth_router
from backend.routes.public_routes import router as public_router
from backend.routes.staff_routes import router as staff_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title=f"{APP_NAME} API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(auth_router)
app.include_router(public_router)
app.include_router(staff_router)
app.include_router(admin_router)


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
    <p>The backend responded. The web app runs at http://localhost:5173 during development.</p>
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