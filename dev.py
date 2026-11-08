#!/usr/bin/env python3
"""AppointMed developer console.

One file to set up and run the whole project from a terminal menu:
  * checks your tools (Git, Python, Node.js, npm, MySQL)
  * creates the virtual environment and installs the backend and frontend packages
  * writes source/.env (database password, random JWT secret)
  * creates the database and the limited app account, loads the schema and sample data
  * starts the backend and the frontend, each in its own terminal window
  * health check, browser shortcuts, frontend build, and update-from-GitHub

Run it from anywhere:
    python dev.py            (Windows: py dev.py)       -> opens the menu
    python dev.py start                                 -> starts backend + frontend
    python dev.py setup | check | install | env | db | reset-db
                  backend | frontend | health | open | build | sync

It only uses Python's standard library, so it works before anything is installed.
"""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

# ---------------------------------------------------------------- paths and constants
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
FRONTEND = SOURCE / "frontend"
DB_DIR = SOURCE / "database"
VENV = SOURCE / ".venv"
ENV_FILE = SOURCE / ".env"
ENV_EXAMPLE = SOURCE / ".env.example"

IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"
VENV_BIN = VENV / ("Scripts" if IS_WINDOWS else "bin")
VENV_PYTHON = VENV_BIN / ("python.exe" if IS_WINDOWS else "python")
UVICORN = "uvicorn.exe" if IS_WINDOWS else "uvicorn"

BACKEND_PORT = 8000
FRONTEND_PORT = 5173
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"

MIN_PYTHON = (3, 11)
MIN_NODE = 20
# Loaded in this order. seed.sql only runs on an empty database; the others are safe to repeat.
SQL_FILES = ("schema.sql", "seed.sql", "landing_update.sql")
CHARSET = "--default-character-set=utf8mb4"

DEFAULT_ENV = """APP_ENV=development
DB_HOST=localhost
DB_PORT=3306
DB_NAME=appointmed
DB_USER=appointmed_user
DB_PASSWORD=change_this_password
JWT_SECRET=change_this_secret
JWT_EXPIRE_MINUTES=480
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=no-reply@appointmed.example
SMTP_TLS=true
"""

# ---------------------------------------------------------------- terminal output
if IS_WINDOWS:
    os.system("")  # switches on ANSI colour codes in Windows 10+ consoles
USE_COLOR = sys.stdout.isatty()


def paint(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t: str) -> str: return paint(t, "32")
def red(t: str) -> str: return paint(t, "31")
def yellow(t: str) -> str: return paint(t, "33")
def cyan(t: str) -> str: return paint(t, "36")
def bold(t: str) -> str: return paint(t, "1")
def dim(t: str) -> str: return paint(t, "2")


def heading(title: str) -> None:
    print("\n" + bold(cyan(f"== {title} ==")))


def ok(message: str) -> None:
    print(f"  {green('[ OK ]')} {message}")


def warn(message: str) -> None:
    print(f"  {yellow('[WARN]')} {message}")


def fail(message: str) -> None:
    print(f"  {red('[FAIL]')} {message}")


def info(message: str) -> None:
    print(f"  {dim('[ .. ]')} {message}")


def confirm(question: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    answer = input(f"  {question} [{hint}] ").strip().lower()
    return default if not answer else answer in ("y", "yes")


def clear_screen() -> None:
    os.system("cls" if IS_WINDOWS else "clear")


# ---------------------------------------------------------------- small helpers
def run_live(cmd: list, cwd: Path) -> bool:
    """Run a command with its output shown live. True when it exits with code 0."""
    parts = [str(c) for c in cmd]
    print(dim("  $ " + " ".join(parts)))
    try:
        return subprocess.call(parts, cwd=str(cwd)) == 0
    except OSError as exc:
        fail(f"Could not run {parts[0]}: {exc}")
        return False


def tool_version(cmd: list) -> str | None:
    """First line of '<tool> --version', or None when the tool is not installed."""
    exe = shutil.which(cmd[0])
    if not exe:
        return None
    try:
        result = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    lines = (result.stdout or result.stderr).strip().splitlines()
    return lines[0] if lines else "installed"


def port_open(port: int) -> bool:
    """True when something accepts connections on the port (IPv4 or IPv6 localhost)."""
    for host in ("127.0.0.1", "::1"):
        try:
            with socket.create_connection((host, port), timeout=0.4):
                return True
        except OSError:
            continue
    return False


def wait_for_port(port: int, seconds: int = 25) -> bool:
    end = time.time() + seconds
    while time.time() < end:
        if port_open(port):
            return True
        time.sleep(0.5)
    return False


def fetch_json(url: str):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:  # offline, refused, or not JSON: all mean "no answer"
        return None


def read_env() -> dict:
    """source/.env as a dictionary (comments and blank lines ignored)."""
    values: dict = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()
    return values


def set_env_value(lines: list, key: str, value: str) -> None:
    """Replace KEY=... in the list of lines, or append it when it is missing."""
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for index, line in enumerate(lines):
        if pattern.match(line):
            lines[index] = f"{key}={value}"
            return
    lines.append(f"{key}={value}")


def sql_fingerprint() -> str:
    digest = hashlib.sha256()
    for name in SQL_FILES:
        path = DB_DIR / name
        if path.exists():
            digest.update(path.read_bytes())
    return digest.hexdigest()


# ---------------------------------------------------------------- 1. prerequisites
def check_prerequisites() -> bool:
    heading("Prerequisites")
    good = True
    version = ".".join(str(n) for n in sys.version_info[:3])
    if sys.version_info >= MIN_PYTHON:
        ok(f"Python {version}")
    else:
        fail(f"Python {version} is too old. Run this file with Python 3.11 or newer (for example: py -3.12 dev.py).")
        good = False
    for name, cmd in (
        ("Git", ["git", "--version"]),
        ("Node.js", ["node", "--version"]),
        ("npm", ["npm", "--version"]),
        ("MySQL client", ["mysql", "--version"]),
    ):
        found = tool_version(cmd)
        if found is None:
            fail(f"{name} was not found on your PATH. See the Prerequisites table in CONTRIBUTING.md.")
            good = False
        elif name == "Node.js":
            match = re.search(r"(\d+)", found)
            if match and int(match.group(1)) < MIN_NODE:
                fail(f"{found} is too old (Node.js {MIN_NODE} or newer is needed).")
                good = False
            else:
                ok(f"Node.js {found}")
        else:
            ok(f"{name}: {found}")
    if not (SOURCE / "main.py").exists():
        fail("source/main.py was not found. Keep dev.py in the project root, next to the source folder.")
        good = False
    return good


# ---------------------------------------------------------------- 2. dependencies
def install_backend() -> bool:
    heading("Backend dependencies")
    if sys.version_info < MIN_PYTHON:
        fail("Run this file with Python 3.11 or newer so the virtual environment uses it.")
        return False
    if not VENV_PYTHON.exists():
        info("Creating the virtual environment at source/.venv")
        if not run_live([sys.executable, "-m", "venv", VENV], SOURCE):
            fail("Could not create the virtual environment. On Debian/Ubuntu install it with: sudo apt install python3-venv")
            return False
    info("Installing the packages in requirements.txt")
    if not run_live([VENV_PYTHON, "-m", "pip", "install", "-r", "requirements.txt"], SOURCE):
        fail("pip could not install the packages. Read the error above.")
        return False
    ok("Backend packages are installed.")
    return True


def install_frontend() -> bool:
    heading("Frontend dependencies")
    npm = shutil.which("npm")
    if not npm:
        fail("npm was not found. Install Node.js 20 or newer.")
        return False
    if not run_live([npm, "install"], FRONTEND):
        fail("npm install failed. Read the error above.")
        return False
    ok("Frontend packages are installed.")
    return True


def install_all() -> bool:
    results = [install_backend(), install_frontend()]
    return all(results)


# ---------------------------------------------------------------- 3. source/.env
def ask_db_password() -> str:
    while True:
        value = getpass.getpass("  Database password for the app account (Enter = generate a random one): ")
        if not value:
            ok("Generated a random password. It is saved in source/.env.")
            return secrets.token_urlsafe(18)
        if re.search(r"[\s'\"#\\$]", value):
            warn("Do not use spaces, quotes, #, $ or backslashes (they break the .env file). Try again.")
            continue
        return value


def configure_env() -> bool:
    heading("Configure source/.env")
    if ENV_FILE.exists() and not confirm("source/.env already exists. Replace it?", default=False):
        info("Keeping the existing file.")
        return True
    template = ENV_EXAMPLE.read_text(encoding="utf-8") if ENV_EXAMPLE.exists() else DEFAULT_ENV
    lines = template.splitlines()
    set_env_value(lines, "DB_PASSWORD", ask_db_password())
    set_env_value(lines, "JWT_SECRET", secrets.token_hex(32))
    if confirm("Send real emails through SMTP? (No = emails are printed in the backend console)", default=False):
        info("Fill in the SMTP_* values in source/.env yourself, then restart the backend.")
    else:
        for key in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
            set_env_value(lines, key, "")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok("Wrote source/.env (it is gitignored: never commit it).")
    return True


# ---------------------------------------------------------------- 4. database
_NAME = re.compile(r"^[A-Za-z0-9_]{1,64}$")
_HOST = re.compile(r"^[A-Za-z0-9.\-]+$")


def db_settings() -> dict | None:
    """Connection values from source/.env, checked so they are safe to place in SQL."""
    env = read_env()
    cfg = {
        "host": env.get("DB_HOST") or "localhost",
        "port": env.get("DB_PORT") or "3306",
        "name": env.get("DB_NAME") or "appointmed",
        "user": env.get("DB_USER") or "appointmed_user",
        "password": env.get("DB_PASSWORD", ""),
    }
    if not (_NAME.match(cfg["name"]) and _NAME.match(cfg["user"])):
        fail("DB_NAME and DB_USER may only contain letters, digits and underscores.")
        return None
    if not _HOST.match(cfg["host"]) or not cfg["port"].isdigit():
        fail("DB_HOST or DB_PORT in source/.env is not valid.")
        return None
    if not cfg["password"] or cfg["password"] == "change_this_password":
        fail("DB_PASSWORD in source/.env is still the placeholder. Run 'Configure source/.env' first.")
        return None
    return cfg


def sql_text(value: str) -> str:
    """Escapes a value for a single-quoted MySQL string."""
    return value.replace("\\", "\\\\").replace("'", "''")


def mysql_step(label: str, cfg: dict, root_password: str, args: list | None = None,
               sql: str | None = None, path: Path | None = None, quiet: bool = False):
    """Runs the mysql client as root. The SQL goes in through stdin (no shell, so PowerShell works too)."""
    env = os.environ.copy()
    env.pop("MYSQL_PWD", None)
    if root_password:
        env["MYSQL_PWD"] = root_password  # keeps the password off the command line
    cmd = [shutil.which("mysql") or "mysql", "-h", cfg["host"], "-P", cfg["port"], "-u", "root", *(args or [])]
    kwargs: dict = {"capture_output": True, "env": env}
    if sql is not None:
        kwargs["input"] = sql.encode("utf-8")
    elif path is not None:
        kwargs["input"] = path.read_bytes()
    else:
        kwargs["stdin"] = subprocess.DEVNULL
    try:
        result = subprocess.run(cmd, **kwargs)
    except OSError as exc:
        fail(f"{label}: could not run mysql ({exc})")
        return None
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        fail(f"{label} failed.")
        for line in message.splitlines()[-6:]:
            print("         " + line)
        if "Access denied" in message:
            info("Check the MySQL root password you typed.")
        return None
    if not quiet:
        ok(label)
    return result


def setup_database(reset: bool = False) -> bool:
    heading("Reset database" if reset else "Set up database")
    if not shutil.which("mysql"):
        fail("The mysql client was not found on your PATH. Install MySQL 8 and open a new terminal.")
        return False
    if not ENV_FILE.exists():
        warn("source/.env does not exist yet, so it is created first.")
        if not configure_env():
            return False
    cfg = db_settings()
    if cfg is None:
        return False
    needed = ("schema.sql", "seed.sql") if reset else SQL_FILES
    missing = [name for name in needed if not (DB_DIR / name).exists()]
    if missing:
        fail("Missing file(s) in source/database: " + ", ".join(missing))
        return False
    if reset and input(f"  Type RESET to delete the database '{cfg['name']}' and all its data: ").strip() != "RESET":
        info("Cancelled. Nothing was changed.")
        return False

    root_password = getpass.getpass("  MySQL root password (hidden; press Enter if root has no password): ")
    name, user, password = cfg["name"], cfg["user"], sql_text(cfg["password"])
    create = (
        (f"DROP DATABASE IF EXISTS `{name}`;\n" if reset else "")
        + f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n"
        f"CREATE USER IF NOT EXISTS '{user}'@'localhost' IDENTIFIED BY '{password}';\n"
        f"ALTER USER '{user}'@'localhost' IDENTIFIED BY '{password}';\n"
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{name}`.* TO '{user}'@'localhost';\n"
        "FLUSH PRIVILEGES;\n"
    )
    if mysql_step("Create the database and the app account", cfg, root_password, sql=create) is None:
        return False
    if mysql_step("Load schema.sql (tables)", cfg, root_password, args=[CHARSET, name], path=DB_DIR / "schema.sql") is None:
        return False

    counted = mysql_step("Check for existing data", cfg, root_password,
                         args=["-N", "-B", name, "-e", "SELECT COUNT(*) FROM users"], quiet=True)
    if counted is None:
        return False
    existing = int(counted.stdout.decode("utf-8", "replace").strip() or 0)
    if existing == 0:
        if reset:
            info("Reset loads schema.sql and seed.sql only, so landing_update.sql was skipped.")
        elif mysql_step("Load landing_update.sql (departments and extra doctors)", cfg, root_password,
                    args=[CHARSET, name], path=DB_DIR / "landing_update.sql") is None:
            return False
    ok(f"Database '{name}' is ready. Sample logins are listed in CONTRIBUTING.md (Step 5).")
    return True


# ---------------------------------------------------------------- terminals and servers
def launch(title: str, workdir: Path, parts: list) -> bool:
    """Runs a command in a NEW terminal window that stays open. Works on Windows, macOS and Linux."""
    parts = [str(p) for p in parts]
    if IS_WINDOWS:
        manual = f'cd /d "{workdir}" && {subprocess.list2cmdline(parts)}'
    else:
        manual = f"cd {shlex.quote(str(workdir))} && " + " ".join(shlex.quote(p) for p in parts)
    try:
        if IS_WINDOWS:
            # start opens a new console; cmd /k keeps it open so errors stay readable.
            subprocess.Popen(f'start "{title}" cmd /k "{subprocess.list2cmdline(parts)}"', shell=True, cwd=str(workdir))
            return True
        if IS_MAC:
            line = manual.replace("\\", "\\\\").replace('"', '\\"')
            script = f'tell application "Terminal"\nactivate\ndo script "{line}"\nend tell'
            subprocess.Popen(["osascript", "-e", script])
            return True
        if launch_linux(title, manual):
            return True
    except OSError as exc:
        fail(f"Could not open a terminal window: {exc}")
    fail("No supported terminal was found. Open a new terminal yourself and run:")
    print("         " + manual)
    return False


def launch_linux(title: str, manual: str) -> bool:
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    script = f"{manual}; echo; echo 'Stopped. Press Enter to close this window.'; read _"
    options = (
        ("gnome-terminal", ["gnome-terminal", "--title", title, "--", "bash", "-c", script]),
        ("konsole", ["konsole", "-p", f"tabtitle={title}", "-e", "bash", "-c", script]),
        ("xfce4-terminal", ["xfce4-terminal", "--title", title, "-x", "bash", "-c", script]),
        ("kitty", ["kitty", "--title", title, "bash", "-c", script]),
        ("alacritty", ["alacritty", "-t", title, "-e", "bash", "-c", script]),
        ("x-terminal-emulator", ["x-terminal-emulator", "-e", "bash", "-c", script]),
        ("xterm", ["xterm", "-T", title, "-e", "bash", "-c", script]),
    )
    for exe, cmd in options:
        if shutil.which(exe):
            subprocess.Popen(cmd)
            return True
    return False


def start_backend() -> bool:
    heading("Backend (FastAPI)")
    if port_open(BACKEND_PORT):
        ok(f"Already running on port {BACKEND_PORT}.")
        return True
    problems = []
    if not (VENV_BIN / UVICORN).exists():
        problems.append("Backend packages are not installed. Use 'Install / update dependencies'.")
    if not ENV_FILE.exists():
        problems.append("source/.env is missing. Use 'Configure source/.env'.")
    if problems:
        for problem in problems:
            fail(problem)
        return False
    if not launch("AppointMed Backend", SOURCE, [VENV_PYTHON, "-m", "uvicorn", "main:app", "--reload"]):
        return False
    info("Waiting for the backend to answer...")
    if wait_for_port(BACKEND_PORT):
        ok(f"Backend is up: {BACKEND_URL}  (API docs: {BACKEND_URL}/docs)")
        return True
    warn("The backend did not answer yet. Read its terminal window for errors.")
    return False


def start_frontend() -> bool:
    heading("Frontend (Vite)")
    if port_open(FRONTEND_PORT):
        ok(f"Already running on port {FRONTEND_PORT}.")
        return True
    npm = shutil.which("npm")
    if not npm:
        fail("npm was not found. Install Node.js 20 or newer.")
        return False
    if not (FRONTEND / "node_modules" / "vite").exists():
        fail("Frontend packages are not installed. Use 'Install / update dependencies'.")
        return False
    if not launch("AppointMed Frontend", FRONTEND, [npm, "run", "dev"]):
        return False
    info("Waiting for the frontend to answer...")
    if wait_for_port(FRONTEND_PORT):
        ok(f"Frontend is up: {FRONTEND_URL}")
        return True
    warn("The frontend did not answer yet. Read its terminal window for errors.")
    return False


def start_everything() -> bool:
    results = [start_backend(), start_frontend()]
    if all(results):
        health_check()
        webbrowser.open(FRONTEND_URL)
        ok("Opened the web app in your browser. Close the two terminal windows (or press Ctrl+C in them) to stop.")
    return all(results)


# ---------------------------------------------------------------- tools
def health_check() -> bool:
    heading("Health check")
    api = fetch_json(BACKEND_URL + "/api/health")
    if not api:
        fail(f"The backend is not answering at {BACKEND_URL}. Start it first.")
        return False
    ok(f"API online ({api.get('app')} {api.get('version')}, {api.get('environment')})")
    good = True
    db = fetch_json(BACKEND_URL + "/api/health/db")
    if db and db.get("connected"):
        ok(f"Database connected ({db.get('database')})")
    else:
        fail("Database not connected. Check that MySQL is running and the DB_* values in source/.env.")
        good = False
    if port_open(FRONTEND_PORT):
        ok(f"Frontend running at {FRONTEND_URL}")
    else:
        warn("Frontend is not running.")
    return good


def open_browser() -> bool:
    heading("Open in browser")
    targets = (("Web app", FRONTEND_URL), ("Backend status page", BACKEND_URL), ("API docs", BACKEND_URL + "/docs"))
    for index, (label, url) in enumerate(targets, 1):
        print(f"  {index}) {label}  {dim(url)}")
    pick = input("  Open which one? [1] ").strip() or "1"
    if pick.isdigit() and 1 <= int(pick) <= len(targets):
        webbrowser.open(targets[int(pick) - 1][1])
        return True
    warn("Choose 1, 2 or 3.")
    return False


def build_frontend() -> bool:
    heading("Build frontend (TypeScript check)")
    npm = shutil.which("npm")
    if not npm:
        fail("npm was not found.")
        return False
    if not (FRONTEND / "node_modules").exists():
        fail("Frontend packages are not installed. Use 'Install / update dependencies'.")
        return False
    if run_live([npm, "run", "build"], FRONTEND):
        ok("The build finished with no errors.")
        return True
    fail("The build failed. Fix the errors listed above.")
    return False


def sync_after_pull() -> bool:
    heading("Update from GitHub")
    git = shutil.which("git")
    if not git:
        fail("Git was not found on your PATH.")
        return False
    before = sql_fingerprint()
    if not run_live([git, "pull", "--ff-only"], ROOT):
        fail("git pull failed. Commit or stash your changes, or resolve the conflict, then try again.")
        return False
    good = install_all()
    if sql_fingerprint() != before:
        warn("The database SQL files changed. Use 'Reset database' so your database matches the team's.")
    info("If source/.env.example gained new variables, add them to your own source/.env and restart the backend.")
    return good


def first_time_setup() -> bool:
    heading("First-time setup")
    steps = (
        ("Check prerequisites", check_prerequisites),
        ("Install dependencies", install_all),
        ("Configure source/.env", configure_env),
        ("Set up database", setup_database),
    )
    for name, step in steps:
        if not step():
            fail(f"Stopped at: {name}. Fix the problem above, then run First-time setup again (finished steps are safe to repeat).")
            return False
    ok("Setup complete.")
    if confirm("Start the project now?", default=True):
        start_everything()
    return True


# ---------------------------------------------------------------- menu
def mark(flag: bool) -> str:
    return green("[x]") if flag else red("[ ]")


def show_status() -> None:
    print(bold("Project status"))
    print(f"  {mark(VENV_PYTHON.exists())} Python virtual environment (source/.venv)")
    print(f"  {mark((VENV_BIN / UVICORN).exists())} Backend packages installed")
    print(f"  {mark((FRONTEND / 'node_modules' / 'vite').exists())} Frontend packages installed")
    print(f"  {mark(ENV_FILE.exists())} source/.env present")
    backend_up = port_open(BACKEND_PORT)
    print(f"  {mark(backend_up)} Backend running (port {BACKEND_PORT})")
    if backend_up:
        db = fetch_json(BACKEND_URL + "/api/health/db")
        print(f"  {mark(bool(db and db.get('connected')))} Database connected")
    else:
        print(f"  {dim('[-] Database connection (start the backend to check)')}")
    print(f"  {mark(port_open(FRONTEND_PORT))} Frontend running (port {FRONTEND_PORT})")


MENU = [
    ("f", "First-time setup (steps 1 to 4 in order)", first_time_setup),
    ("1", "Check prerequisites", check_prerequisites),
    ("2", "Install / update dependencies (backend + frontend)", install_all),
    ("3", "Configure source/.env", configure_env),
    ("4", "Set up database (create, schema, sample data)", setup_database),
    ("5", "Reset database (deletes all data)", lambda: setup_database(True)),
    ("6", "Start backend in a new terminal", start_backend),
    ("7", "Start frontend in a new terminal", start_frontend),
    ("8", "Start everything and open the browser", start_everything),
    ("9", "Health check", health_check),
    ("10", "Open in browser", open_browser),
    ("11", "Build frontend (TypeScript check)", build_frontend),
    ("12", "Update from GitHub (git pull + install)", sync_after_pull),
    ("q", "Quit", None),
]

COMMANDS = {
    "setup": first_time_setup, "check": check_prerequisites, "install": install_all, "env": configure_env,
    "db": setup_database, "reset-db": lambda: setup_database(True), "backend": start_backend,
    "frontend": start_frontend, "start": start_everything, "health": health_check, "open": open_browser,
    "build": build_frontend, "sync": sync_after_pull,
}


def menu_loop() -> int:
    while True:
        clear_screen()
        print(bold(cyan("AppointMed developer console")))
        print(dim(f"Project folder: {ROOT}\n"))
        show_status()
        print("\n" + bold("Menu"))
        for key, label, _ in MENU:
            print(f"  {bold(key.rjust(2))}  {label}")
        choice = input("\nChoose an option: ").strip().lower()
        if choice in ("q", "quit", "exit", "0"):
            return 0    
        action = next((fn for key, _, fn in MENU if key == choice and fn), None)
        if action is None:
            continue
        try:
            action()
        except KeyboardInterrupt:
            print("\n  Cancelled.")
        input("\nPress Enter to return to the menu...")


def main(argv: list) -> int:
    if len(argv) > 1:
        action = COMMANDS.get(argv[1].lower())
        if action is None:
            print("Unknown command. Use one of: " + ", ".join(COMMANDS) + ", or no command for the menu.")
            return 2
        return 0 if action() else 1
    return menu_loop()


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except (KeyboardInterrupt, EOFError):
        print("\nBye.")
        sys.exit(130)